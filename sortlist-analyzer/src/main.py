import logging
import duckdb
import argparse
from data_loading import load_config, load_data
from pagerank_analysis import calculate_pagerank, calculate_advanced_metrics
from report_generation import generate_excel_report
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import numpy as np
from math import pi # Added for radar chart

warnings.filterwarnings("ignore", category=UserWarning, module="xlsxwriter.worksheet")

def main():
    parser = argparse.ArgumentParser(description="Analyzes PageRank and generates an Excel report for sortlist.com")
    parser.add_argument('--config', required=True, help='Path to the YAML configuration file')
    args = parser.parse_args()

    # Initialize logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    # Load configuration
    config = load_config(args.config)

    # Resolve data_dir to be relative to the directory containing the 'config' directory.
    # This makes 'data_dir: data/' in config.yaml refer to 'sortlist-analyzer/data/'
    # when the script is run from the workspace root.
    config_file_path = args.config  # e.g., "sortlist-analyzer/config/config.yaml"
    config_directory = os.path.dirname(config_file_path)  # e.g., "sortlist-analyzer/config"
    project_directory_containing_config = os.path.dirname(config_directory)  # e.g., "sortlist-analyzer"
    
    # config['data_dir'] is 'data/' from the yaml file by default.
    # Prepend the project_directory_containing_config to make the path correct relative to CWD.
    resolved_data_dir = os.path.join(project_directory_containing_config, config['data_dir'])
    config['data_dir'] = resolved_data_dir # Now, e.g., 'sortlist-analyzer/data/'

    # DuckDB connection
    con = duckdb.connect(database=':memory:')
    logging.info("Connected to DuckDB")

    # Load data
    if not load_data(con, config):
        logging.error("Failed to load data")
        return

    # --- Load and prepare external backlink data ---
    backlinks_csv_path_config = config.get('backlinks_csv_path', 'data/backlinks_www.sortlist.com.csv')
    if not os.path.isabs(backlinks_csv_path_config):
        backlinks_file_path = os.path.join(project_directory_containing_config, backlinks_csv_path_config)
    else:
        backlinks_file_path = backlinks_csv_path_config
    
    try:
        logging.info(f"Loading backlinks file: {backlinks_file_path}")
        # Read the file with error handling for parsing issues
        backlinks_df = pd.read_csv(backlinks_file_path, sep=';', on_bad_lines='skip')
        logging.info(f"{len(backlinks_df)} backlinks rows loaded from {backlinks_file_path}.")

        if 'TargetURL' not in backlinks_df.columns:
            logging.error(f"Column 'TargetURL' not found in {backlinks_file_path}. External backlinks analysis will be skipped.")
            # Create an empty table so the rest of the SQL doesn't break
            con.execute("CREATE OR REPLACE TABLE external_backlinks_summary (url VARCHAR, external_backlinks_count INTEGER DEFAULT 0)")
            # Create an empty DataFrame for external_backlinks_count to avoid errors if the file is missing
            df_external_backlinks_count = pd.DataFrame(columns=['url', 'external_backlinks_count'])

        else:
            backlinks_df['TargetURL'] = backlinks_df['TargetURL'].astype(str).str.strip()
            # Filter out invalid or empty URLs that might result from string conversion
            backlinks_df = backlinks_df[backlinks_df['TargetURL'].str.lower() != 'nan']
            backlinks_df = backlinks_df[backlinks_df['TargetURL'] != '']
            
            external_links_counts = backlinks_df.groupby('TargetURL').size().reset_index(name='external_backlinks_count')
            external_links_counts = external_links_counts.rename(columns={'TargetURL': 'url'})
            df_external_backlinks_count = external_links_counts
            logging.info(f"{len(df_external_backlinks_count)} unique URLs with external backlinks found.")
            
            con.register('df_external_backlinks_count_temp', df_external_backlinks_count) # Use a temporary name
            con.execute("CREATE OR REPLACE TABLE external_backlinks_summary AS SELECT * FROM df_external_backlinks_count_temp")
            logging.info("Table 'external_backlinks_summary' created in DuckDB.")
            con.unregister('df_external_backlinks_count_temp') # Clean up

    except FileNotFoundError:
        logging.warning(f"Backlinks file {backlinks_file_path} not found. External backlinks analysis will be skipped.")
        con.execute("CREATE OR REPLACE TABLE external_backlinks_summary (url VARCHAR, external_backlinks_count INTEGER DEFAULT 0)")
        df_external_backlinks_count = pd.DataFrame(columns=['url', 'external_backlinks_count'])
    except pd.errors.EmptyDataError:
        logging.warning(f"Backlinks file {backlinks_file_path} is empty. External backlinks analysis will be skipped.")
        con.execute("CREATE OR REPLACE TABLE external_backlinks_summary (url VARCHAR, external_backlinks_count INTEGER DEFAULT 0)")
        df_external_backlinks_count = pd.DataFrame(columns=['url', 'external_backlinks_count'])
    except Exception as e:
        logging.error(f"Error loading or processing backlinks ({backlinks_file_path}): {e}. External backlinks analysis will be skipped.")
        con.execute("CREATE OR REPLACE TABLE external_backlinks_summary (url VARCHAR, external_backlinks_count INTEGER DEFAULT 0)")
        df_external_backlinks_count = pd.DataFrame(columns=['url', 'external_backlinks_count'])

    # Calculate PageRank
    pr_df, prw_df = calculate_pagerank(con)
    if pr_df.empty or prw_df.empty:
        logging.error("Failed to calculate PageRank")
        return

    # Fusion des données pour analyse avancée
    try:
        logging.info("Début de la fusion des données pour analyse avancée")
        con.execute("DROP TABLE IF EXISTS pr_df")
        con.execute("DROP TABLE IF EXISTS prw_df")
        con.register("pr_df", pr_df)
        con.register("prw_df", prw_df)
        # Ajout du nombre de hits (logs) par URL
        con.execute('''
            CREATE OR REPLACE TABLE hits_per_url AS
            SELECT event_url as url, COUNT(*) as hits
            FROM logs_events
            GROUP BY event_url;
        ''')
        con.execute('''
            CREATE OR REPLACE TABLE merged_data AS
            WITH ranked_data AS (
                SELECT 
                    p.url,
                    p.content_type,
                    p.http_code,
                    p.status,
                    p.indexability,
                    p.incoming_links,
                    p.outgoing_links,
                    p.crawl_depth,
                    p.word_count,
                    c.category as category,
                    c.label as label,
                    c.country as country,
                    c.location as location,
                    COALESCE(t.clicks, 0) as clicks,
                    COALESCE(t.impressions, 0) as impressions,
                    COALESCE(t.ctr, 0) as ctr,
                    COALESCE(t.avg_position, 0) as avg_position,
                    COALESCE(pr.PageRank, 0) as PageRank,
                    COALESCE(prw.Weighted_PageRank, 0) as Weighted_PageRank,
                    COALESCE(h.hits, 0) as hits,
                    COALESCE(el.external_backlinks_count, 0) as external_backlinks_count,
                    ROW_NUMBER() OVER (PARTITION BY p.url ORDER BY COALESCE(pr.PageRank, 0) DESC) as rn
                FROM pages p
                LEFT JOIN categorized c ON p.url = c.url
                LEFT JOIN traffic t ON p.url = t.url
                LEFT JOIN pr_df pr ON p.url = pr.url
                LEFT JOIN prw_df prw ON p.url = prw.url
                LEFT JOIN hits_per_url h ON p.url = h.url
                LEFT JOIN external_backlinks_summary el ON p.url = el.url
            )
            SELECT * FROM ranked_data WHERE rn = 1;
        ''')
        df = con.execute('''
            SELECT 
                url, content_type, category, label, location, country,
                clicks, impressions, ctr, avg_position, PageRank, Weighted_PageRank, incoming_links, outgoing_links, crawl_depth, word_count, hits,
                external_backlinks_count
            FROM merged_data;
        ''').df()
        logging.info(f"{len(df)} pages fusionnées pour analyse avancée")
    except Exception as e:
        logging.error(f"Erreur lors de la fusion des données : {e}")
        return

    # Calcul des métriques avancées
    df = calculate_advanced_metrics(df)
    if df is None:
        logging.error("Failed to calculate advanced metrics")
        return

    # --- Load and integrate PageSpeed data from CSV ---
    pagespeed_csv_path_config = config.get('pagespeed_output_csv', 'data/pagespeed_results.csv')
    df_pagespeed_raw = None  # For the Excel tab
    pagespeed_loaded = False
    try:
        project_root_main = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.isabs(pagespeed_csv_path_config):
            pagespeed_csv_path = os.path.join(project_root_main, pagespeed_csv_path_config)
        else:
            pagespeed_csv_path = pagespeed_csv_path_config

        if os.path.exists(pagespeed_csv_path):
            logging.info(f"Loading PageSpeed data from: {pagespeed_csv_path}")
            df_pagespeed_raw = pd.read_csv(pagespeed_csv_path, sep=',') # Use comma as separator
            logging.info(f"{len(df_pagespeed_raw)} PageSpeed rows loaded.")

            if not df_pagespeed_raw.empty:
                # Copy for processing without affecting the original for Excel
                df_ps_processed = df_pagespeed_raw.copy()
                df_ps_processed.columns = [col.lower().strip() for col in df_ps_processed.columns]

                required_ps_cols = ['url', 'mobile_performance_score', 'desktop_performance_score']
                if all(col in df_ps_processed.columns for col in required_ps_cols):
                    # Calculate combined score
                    # Convert to numeric, handling errors (which become NaN)
                    df_ps_processed['mobile_performance_score'] = pd.to_numeric(df_ps_processed['mobile_performance_score'], errors='coerce')
                    df_ps_processed['desktop_performance_score'] = pd.to_numeric(df_ps_processed['desktop_performance_score'], errors='coerce')

                    # Calculate average only if both scores are valid
                    df_ps_processed['combined_performance_score'] = df_ps_processed[['mobile_performance_score', 'desktop_performance_score']].mean(axis=1, skipna=False)
                    
                    # Select and deduplicate for merging
                    df_to_merge = df_ps_processed[['url', 'combined_performance_score']].dropna(subset=['url']).drop_duplicates(subset=['url'], keep='first')

                    # Merge with the main DataFrame
                    df = pd.merge(df, df_to_merge, on='url', how='left')
                    logging.info("Combined PageSpeed score (sample-based) merged with the main DataFrame.")
                    pagespeed_loaded = True # Mark as loaded and merged
                else:
                    logging.warning(f"Required PageSpeed columns ({required_ps_cols}) not found after normalization. PageSpeed integration skipped.")
                    df_pagespeed_raw = None # No valid data for Excel either
            else:
                 logging.info(f"PageSpeed file {pagespeed_csv_path} is empty.")
                 df_pagespeed_raw = None # Empty file
        else:
            logging.warning(f"PageSpeed file {pagespeed_csv_path} not found. PageSpeed analysis skipped.")

    except pd.errors.EmptyDataError:
        logging.warning(f"PageSpeed file {pagespeed_csv_path} is empty. PageSpeed analysis skipped.")
        df_pagespeed_raw = None
    except Exception as e:
        logging.error(f"Error loading/processing PageSpeed file {pagespeed_csv_path}: {e}")
        df_pagespeed_raw = None

    # --- Prepare DataFrames for new tabs ---
    # Correlation PR/Traffic and PR/Hits, Weighted PR, etc.
    correlation_list = [
        'PageRank vs Traffic (clicks)',
        'PageRank vs Hits (logs)',
        'Weighted_PageRank vs Traffic (clicks)',
        'Weighted_PageRank vs Hits (logs)',
        'PageRank vs Weighted_PageRank',
        'PageRank vs Nombre de mots',
        'Weighted_PageRank vs Nombre de mots',
        'Traffic (clicks) vs Nombre de mots',
        'Crawl profondeur vs PageRank',
        'Crawl profondeur vs Weighted_PageRank',
        'Crawl profondeur vs Traffic (clicks)',
        'Crawl profondeur vs Nombre de mots',
        'PageRank vs Backlinks Externes',
        'Weighted_PageRank vs Backlinks Externes',
        'Traffic (clicks) vs Backlinks Externes',
        'Hits (logs) vs Backlinks Externes'
    ]
    values_list = [
        df['PageRank'].corr(df['clicks']),
        df['PageRank'].corr(df['hits']),
        df['Weighted_PageRank'].corr(df['clicks']),
        df['Weighted_PageRank'].corr(df['hits']),
        df['PageRank'].corr(df['Weighted_PageRank']),
        df['PageRank'].corr(df['word_count']),
        df['Weighted_PageRank'].corr(df['word_count']),
        df['clicks'].corr(df['word_count']),
        df['crawl_depth'].corr(df['PageRank']),
        df['crawl_depth'].corr(df['Weighted_PageRank']),
        df['crawl_depth'].corr(df['clicks']),
        df['crawl_depth'].corr(df['word_count']),
        df['PageRank'].corr(df['external_backlinks_count']) if 'external_backlinks_count' in df else None,
        df['Weighted_PageRank'].corr(df['external_backlinks_count']) if 'external_backlinks_count' in df else None,
        df['clicks'].corr(df['external_backlinks_count']) if 'external_backlinks_count' in df else None,
        df['hits'].corr(df['external_backlinks_count']) if 'external_backlinks_count' in df else None
    ]

    # Add PageSpeed correlations if data is available
    if pagespeed_loaded and 'combined_performance_score' in df.columns:
        correlation_list.extend([
            'PageRank vs Combined PageSpeed Score (Sample)',
            'Traffic (clicks) vs Combined PageSpeed Score (Sample)',
            'Backlinks Externes vs Combined PageSpeed Score (Sample)'
        ])
        values_list.extend([
            df['PageRank'].corr(df['combined_performance_score']) if 'PageRank' in df else None,
            df['clicks'].corr(df['combined_performance_score']) if 'clicks' in df else None,
            df['external_backlinks_count'].corr(df['combined_performance_score']) if 'external_backlinks_count' in df else None
        ])

    correlation_df = pd.DataFrame({'Correlation': correlation_list, 'Value': values_list})
    correlation_df.dropna(subset=['Value'], inplace=True) # Remove rows where correlation could not be calculated

    # Stats by Label
    label_agg_dict = {
        'PageRank': ['mean', 'min', 'max', 'median'],
        'clicks': ['mean', 'min', 'max', 'median'],
        'hits': ['mean', 'min', 'max', 'median'],
        'word_count': ['mean', 'min', 'max', 'median'],
        'crawl_depth': ['mean', 'min', 'max', 'median']
    }
    if 'external_backlinks_count' in df.columns:
        label_agg_dict['external_backlinks_count'] = ['sum', 'mean', 'median']
    label_stats = df.groupby('label').agg(label_agg_dict).reset_index()
    label_stats.columns = ['_'.join([str(i) for i in col if i]) for col in label_stats.columns.values]

    # Stats by Category
    # Define the base aggregation dictionary
    cat_agg_config = {
        'PageRank_mean': pd.NamedAgg(column='PageRank', aggfunc='mean'),
        'PageRank_min': pd.NamedAgg(column='PageRank', aggfunc='min'),
        'PageRank_max': pd.NamedAgg(column='PageRank', aggfunc='max'),
        'PageRank_median': pd.NamedAgg(column='PageRank', aggfunc='median'),
        'clicks_mean': pd.NamedAgg(column='clicks', aggfunc='mean'),
        'clicks_min': pd.NamedAgg(column='clicks', aggfunc='min'),
        'clicks_max': pd.NamedAgg(column='clicks', aggfunc='max'),
        'clicks_median': pd.NamedAgg(column='clicks', aggfunc='median'),
        'hits_mean': pd.NamedAgg(column='hits', aggfunc='mean'),
        'hits_min': pd.NamedAgg(column='hits', aggfunc='min'),
        'hits_max': pd.NamedAgg(column='hits', aggfunc='max'),
        'hits_median': pd.NamedAgg(column='hits', aggfunc='median'),
        'word_count_mean': pd.NamedAgg(column='word_count', aggfunc='mean'),
        'word_count_min': pd.NamedAgg(column='word_count', aggfunc='min'),
        'word_count_max': pd.NamedAgg(column='word_count', aggfunc='max'),
        'word_count_median': pd.NamedAgg(column='word_count', aggfunc='median'),
        'crawl_depth_mean': pd.NamedAgg(column='crawl_depth', aggfunc='mean'),
        'crawl_depth_min': pd.NamedAgg(column='crawl_depth', aggfunc='min'),
        'crawl_depth_max': pd.NamedAgg(column='crawl_depth', aggfunc='max'),
        'crawl_depth_median': pd.NamedAgg(column='crawl_depth', aggfunc='median'),
    }
    # Conditionally add aggregations for external backlinks
    if 'external_backlinks_count' in df.columns:
        cat_agg_config.update({
            'external_backlinks_count_sum': pd.NamedAgg(column='external_backlinks_count', aggfunc='sum'),
            'external_backlinks_count_mean': pd.NamedAgg(column='external_backlinks_count', aggfunc='mean'),
            'external_backlinks_count_median': pd.NamedAgg(column='external_backlinks_count', aggfunc='median')
        })
    
    # Conditionally add aggregation for combined PageSpeed score
    if pagespeed_loaded and 'combined_performance_score' in df.columns:
        cat_agg_config['avg_combined_pagespeed_score_sample'] = pd.NamedAgg(column='combined_performance_score', aggfunc='mean')

    # Perform aggregation
    cat_stats = df.groupby('category').agg(**cat_agg_config).reset_index()
    # No need to rename columns here, it's done via NamedAgg keys

    # Stats by Location (New)
    if 'location' in df.columns and df['location'].notna().any():
        loc_agg_dict = {
            'PageRank': ['mean', 'min', 'max', 'median'],
            'clicks': ['mean', 'min', 'max', 'median'],
            'hits': ['mean', 'min', 'max', 'median'],
            'word_count': ['mean', 'min', 'max', 'median'],
            'crawl_depth': ['mean', 'min', 'max', 'median']
        }
        if 'external_backlinks_count' in df.columns:
            loc_agg_dict['external_backlinks_count'] = ['sum', 'mean', 'median']
        
        # Replace empty or NaN values in 'location' to avoid groupby errors
        df_loc_cleaned = df.copy()
        df_loc_cleaned['location'] = df_loc_cleaned['location'].fillna('Unknown').replace('', 'Unknown')

        loc_stats = df_loc_cleaned.groupby('location').agg(loc_agg_dict).reset_index()
        loc_stats.columns = ['_'.join([str(i) for i in col if i]) for col in loc_stats.columns.values]
        logging.info("Location statistics generated.")
    else:
        loc_stats = pd.DataFrame() 
        logging.warning("Column 'location' not found, empty, or entirely NaN. loc_stats will not be generated.")
        # Ensure loc_stats has at least a 'location' column to avoid errors if used later
        if not ('location' in loc_stats.columns or 'location_' in loc_stats.columns): # Handle case where it's empty and columns haven't been flattened
             loc_stats['location'] = None

    # TOP 50 Traffic
    top50_traffic = df.sort_values('clicks', ascending=False).head(50)
    # FLOP 50 Traffic
    flop50_traffic = df.sort_values('clicks', ascending=True).head(50)

    # --- Orphan page detection ---
    try:
        # Get all page URLs
        all_pages = set(df['url'])
        # Get all link destinations
        edges_dst = con.execute('SELECT DISTINCT dst FROM edges').df()['dst']
        linked_pages = set(edges_dst)
        orphan_pages = df[df['url'].apply(lambda x: x not in linked_pages)]
        logging.info(f"{len(orphan_pages)} orphan pages detected")
    except Exception as e:
        logging.error(f"Error detecting orphan pages: {e}")
        orphan_pages = pd.DataFrame()

    # --- Advanced SEO: Zombie pages ---
    zombies = df[(df['PageRank'] < 0.0001) & (df['clicks'] < 10) & (df['hits'] < 10) & (df['url'].apply(lambda x: x not in orphan_pages['url'].values))]
    # --- Advanced SEO: Deep pages ---
    deep_pages = df[df['crawl_depth'] > 3]
    # --- Advanced SEO: Opportunities ---
    pr_median = df['PageRank'].median()
    wpr_median = df['Weighted_PageRank'].median()
    clicks_median = df['clicks'].median() # Added for prioritization
    opportunities = df[((df['PageRank'] > pr_median) | (df['Weighted_PageRank'] > wpr_median)) & (df['clicks'] < 10)]
    # --- Advanced SEO: High CTR, Low Impressions ---
    highctr_lowimp = df[(df['ctr'] > 0.1) & (df['impressions'] < 100)]

    # --- Prioritize SEO segments ---
    if not zombies.empty:
        zombies = zombies.copy() # To avoid SettingWithCopyWarning
        zombies['Priority'] = zombies['crawl_depth'].apply(lambda x: 'High' if x > 2 else ('Medium' if x > 1 else 'Low'))
    
    if not opportunities.empty:
        opportunities = opportunities.copy()
        def prioritize_opportunities(row):
            if (row['PageRank'] > 1.5 * pr_median or row['Weighted_PageRank'] > 1.5 * wpr_median) and row['word_count'] > 500:
                return 'High'
            elif (row['PageRank'] > pr_median or row['Weighted_PageRank'] > wpr_median) and row['word_count'] > 250:
                return 'Medium'
            return 'Low'
        opportunities['Priority'] = opportunities.apply(prioritize_opportunities, axis=1)

    if not deep_pages.empty:
        deep_pages = deep_pages.copy()
        def prioritize_deep_pages(row):
            if row['PageRank'] > pr_median or row['clicks'] > clicks_median:
                return 'High'
            elif row['PageRank'] > 0.5 * pr_median or row['clicks'] > 0.5 * clicks_median:
                return 'Medium'
            return 'Low'
        deep_pages['Priority'] = deep_pages.apply(prioritize_deep_pages, axis=1)
        # Ensure Priority column is last for readability
        cols = [col for col in deep_pages.columns if col != 'Priority'] + ['Priority']
        deep_pages = deep_pages[cols]

    # --- Generate Excel report ---
    cross_metrics = {
        'Correlation': correlation_df,
        'Top50Traffic': top50_traffic,
        'Flop50Traffic': flop50_traffic,
        'OrphanPages': orphan_pages,
        'Zombies': zombies,
        'DeepPages': deep_pages,
        'Opportunities': opportunities,
        'HighCTR_LowImpressions': highctr_lowimp
    }

    # Add raw PageSpeed data (read from CSV) to cross_metrics for a new Excel tab
    if df_pagespeed_raw is not None and not df_pagespeed_raw.empty:
        cross_metrics['PageSpeed_Raw_Sample'] = df_pagespeed_raw
        logging.info("Raw PageSpeed data (sample) added for Excel report.")

    search_engine_analysis = {}
    output_file_config = config.get('output_excel', 'reports/pr_analysis.xlsx')
    if not os.path.isabs(output_file_config):
        output_file = os.path.join(project_directory_containing_config, output_file_config)
    else:
        output_file = output_file_config

    # Ensure the output directory for the Excel report exists
    output_dir = os.path.dirname(output_file)
    if output_dir: # Create directory only if output_dir is not empty (i.e., not saving in CWD)
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Ensured output directory exists: {output_dir}")

    if not generate_excel_report(df, cat_stats, label_stats, loc_stats, prw_df, cross_metrics, output_file, search_engine_analysis):
        logging.error("Failed to generate Excel report")
        return

    # --- Generate actionable SEO charts ---
    charts_dir_config = 'reports/charts' # This is relative to the project_directory_containing_config by default
    charts_dir = os.path.join(project_directory_containing_config, charts_dir_config)
    os.makedirs(charts_dir, exist_ok=True)

    # Ensure df['category'] doesn't have too many unique values for scatter plot legends
    # or consider grouping small categories into 'Other'
    if 'category' in df.columns:
        top_n_categories = 10 # Number of categories to display individually
        if df['category'].nunique() > top_n_categories:
            top_categories_list = df['category'].value_counts().nlargest(top_n_categories).index
            df['category_plot'] = df['category'].apply(lambda x: x if x in top_categories_list else 'Other')
        else:
            df['category_plot'] = df['category']
    else: # Fallback if 'category' column doesn't exist
        df['category_plot'] = 'N/A'

    # 1. Correlation heatmap (keep, rounded to 2 decimal places)
    try:
        cols_for_corr = ['PageRank','Weighted_PageRank','clicks','hits','crawl_depth','word_count']
        if 'external_backlinks_count' in df.columns:
            cols_for_corr.append('external_backlinks_count')
        if pagespeed_loaded and 'combined_performance_score' in df.columns:
             cols_for_corr.append('combined_performance_score')
        
        cols_for_corr = [col for col in cols_for_corr if col in df.columns]

        if len(cols_for_corr) > 1: 
            corr_matrix = df[cols_for_corr].corr().round(2)
            # Create figure and axes
            fig, ax = plt.subplots(figsize=(max(8, len(cols_for_corr)), max(6, int(len(cols_for_corr)*0.8)))) 
            mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
            # Plot on specified axes
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', mask=mask, center=0, square=True, linewidths=.5, cbar_kws={"shrink": .8}, ax=ax)
            plt.title('Heatmap of Main Correlations') 

            # Modify tick labels to remove unnecessary ones
            xticklabels = ax.get_xticklabels()
            yticklabels = ax.get_yticklabels()
            if len(xticklabels) > 0:
                xticklabels[-1].set_text('') # Remove last X label
                ax.set_xticklabels(xticklabels, rotation=45, ha="right")
            if len(yticklabels) > 0:
                yticklabels[0].set_text('')  # Remove first Y label
                ax.set_yticklabels(yticklabels, rotation=0)

            # plt.xticks(rotation=45, ha="right") # Handled by set_xticklabels
            # plt.yticks(rotation=0) # Handled by set_yticklabels
            plt.tight_layout() 
            plt.savefig(f'{charts_dir}/Correlation_heatmap.png')
            plt.close(fig) # Close the figure
        else:
            logging.warning("Not enough columns available to generate the correlation heatmap.") 
            
    except Exception as e:
        logging.error(f"Error plotting Correlation heatmap: {e}")

    # 2. Barplot of page count by depth (replaces boxplot)
    try:
        depth_counts = df['crawl_depth'].value_counts().sort_index()
        plt.figure(figsize=(8,5))
        sns.barplot(x=depth_counts.index, y=depth_counts.values)
        plt.title('Page Count by Crawl Depth')
        plt.xlabel('Crawl Depth')
        plt.ylabel('Number of Pages')
        plt.tight_layout()
        plt.savefig(f'{charts_dir}/DeepPages_barplot.png')
        plt.close()
    except Exception as e:
        logging.error(f"Error plotting Page Count by Crawl Depth: {e}")

    # 3. Weighted_PageRank histogram (long tail)
    # try:
    #     plt.figure(figsize=(8,4))
    #     sns.histplot(df['Weighted_PageRank'], bins=50, kde=True)
    #     plt.title('Weighted PageRank Distribution')
    #     plt.xlabel('Weighted_PageRank')
    #     plt.ylabel('Number of pages')
    #     plt.tight_layout()
    #     plt.savefig(f'{charts_dir}/WeightedPR_distribution.png')
    #     plt.close()
    # except Exception as e:
    #     logging.error(f"Error plotting WeightedPR: {e}")

    # 4. Barplot of traffic by label (top 10)
    try:
        top_labels = df.groupby('label')['clicks'].sum().sort_values(ascending=False).head(10)
        plt.figure(figsize=(10,5))
        sns.barplot(x=top_labels.index, y=top_labels.values)
        plt.title('Top 10 Labels by Traffic (clicks)')
        plt.ylabel('Total Clicks')
        plt.xlabel('Label')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{charts_dir}/Top10_Label_Traffic.png')
        plt.close()
    except Exception as e:
        logging.error(f"Error plotting Top 10 Labels by Traffic: {e}")

    # 5. Barplot of traffic by category (top 10)
    try:
        top_cats = df.groupby('category')['clicks'].sum().sort_values(ascending=False).head(10)
        plt.figure(figsize=(10,5))
        sns.barplot(x=top_cats.index, y=top_cats.values)
        plt.title('Top 10 Categories by Traffic (clicks)')
        plt.ylabel('Total Clicks')
        plt.xlabel('Category')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{charts_dir}/Top10_Category_Traffic.png')
        plt.close()
    except Exception as e:
        logging.error(f"Error plotting Top 10 Categories by Traffic: {e}")

    # 6. Countplot of opportunities by category
    try:
        if not opportunities.empty:
            opp_cat = opportunities['category'].value_counts().head(10)
            plt.figure(figsize=(10,5))
            sns.barplot(x=opp_cat.index, y=opp_cat.values)
            plt.title('Opportunities: Page Count by Category (Top 10)')
            plt.ylabel('Number of Pages')
            plt.xlabel('Category')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f'{charts_dir}/Opportunities_count_Category.png')
            plt.close()
    except Exception as e:
        logging.error(f"Error plotting Opportunities count by Category: {e}")

    # 7. Countplot of zombies by category
    try:
        if not zombies.empty:
            zom_cat = zombies['category'].value_counts().head(10)
            plt.figure(figsize=(10,5))
            sns.barplot(x=zom_cat.index, y=zom_cat.values)
            plt.title('Zombies: Page Count by Category (Top 10)')
            plt.ylabel('Number of Pages')
            plt.xlabel('Category')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f'{charts_dir}/Zombies_count_Category.png')
            plt.close()
    except Exception as e:
        logging.error(f"Error plotting Zombies count by Category: {e}")

    # 8. Countplot of HighCTR_LowImpressions by category
    try:
        if not highctr_lowimp.empty:
            hcli_cat = highctr_lowimp['category'].value_counts().head(10)
            plt.figure(figsize=(10,5))
            sns.barplot(x=hcli_cat.index, y=hcli_cat.values)
            plt.title('High CTR & Low Impressions: Page Count by Category (Top 10)')
            plt.ylabel('Number of Pages')
            plt.xlabel('Category')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f'{charts_dir}/HighCTR_LowImpressions_count_Category.png')
            plt.close()
    except Exception as e:
        logging.error(f"Error plotting High CTR Low Impressions count by Category: {e}")

    # --- New Scatter Plots ---
    # 9. PageRank vs Clicks by Category
    try:
        plt.figure(figsize=(12, 7))
        if not df.empty and 'PageRank' in df.columns and 'clicks' in df.columns and 'category_plot' in df.columns:
            sns.scatterplot(data=df, x='PageRank', y='clicks', hue='category_plot', alpha=0.6, s=50)
            plt.title('PageRank vs Clicks (colored by Category)')
            plt.xlabel('PageRank')
            plt.ylabel('Number of Clicks')
            plt.xscale('log') 
            plt.yscale('log') 
            plt.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout(rect=[0,0,0.85,1]) 
            plt.savefig(f'{charts_dir}/PageRank_vs_Clicks_by_Category.png')
            plt.close()
        else:
            logging.warning("Insufficient data for PageRank vs Clicks scatter plot.")
    except Exception as e:
        logging.error(f"Error plotting PageRank vs Clicks: {e}")

    # 10. Word Count vs Clicks by Category
    try:
        plt.figure(figsize=(12, 7))
        if not df.empty and 'word_count' in df.columns and 'clicks' in df.columns and 'category_plot' in df.columns:
            plot_data = df[(df['word_count'] > 0) & (df['clicks'] > 0)]
            if not plot_data.empty:
                sns.scatterplot(data=plot_data, x='word_count', y='clicks', hue='category_plot', alpha=0.6, s=50)
                plt.title('Word Count vs Clicks (colored by Category)')
                plt.xlabel('Word Count (log scale)')
                plt.ylabel('Number of Clicks (log scale)')
                plt.xscale('log')
                plt.yscale('log')
                plt.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
                plt.tight_layout(rect=[0,0,0.85,1]) 
                plt.savefig(f'{charts_dir}/WordCount_vs_Clicks_by_Category.png')
                plt.close()
            else:
                logging.warning("Filtered data insufficient (word_count > 0, clicks > 0) for Word Count vs Clicks scatter plot.")
        else:
            logging.warning("Insufficient data for Word Count vs Clicks scatter plot.")
    except Exception as e:
        logging.error(f"Error plotting Word Count vs Clicks: {e}")

    # --- New Bar Plots by Location ---
    # 11. Top 15 Locations by Traffic (clicks)
    try:
        if 'location' in df.columns and 'clicks' in df.columns:
            top_locations = df.groupby('location')['clicks'].sum().sort_values(ascending=False).head(15)
            if not top_locations.empty:
                plt.figure(figsize=(12, 7))
                sns.barplot(x=top_locations.index, y=top_locations.values, palette="viridis")
                plt.title('Top 15 Locations by Traffic (clicks)')
                plt.xlabel('Location')
                plt.ylabel('Total Clicks')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(f'{charts_dir}/Top15_Location_Traffic.png')
                plt.close()
            else:
                logging.warning("Insufficient or empty location data for Top 15 Locations chart.")
        else:
            logging.warning("'location' or 'clicks' columns missing for Top 15 Locations chart.")
    except Exception as e:
        logging.error(f"Error generating Top 15 Locations by Traffic chart: {e}")

    # 12. Top 15 Countries by Traffic (clicks)
    try:
        if 'country' in df.columns and 'clicks' in df.columns:
            top_countries = df.groupby('country')['clicks'].sum().sort_values(ascending=False).head(15)
            if not top_countries.empty:
                plt.figure(figsize=(12, 7))
                sns.barplot(x=top_countries.index, y=top_countries.values, palette="mako")
                plt.title('Top 15 Countries by Traffic (clicks)')
                plt.xlabel('Country')
                plt.ylabel('Total Clicks')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(f'{charts_dir}/Top15_Country_Traffic.png')
                plt.close()
            else:
                logging.warning("Insufficient or empty country data for Top 15 Countries chart.")
        else:
            logging.warning("'country' or 'clicks' columns missing for Top 15 Countries chart.")
    except Exception as e:
        logging.error(f"Error generating Top 15 Countries by Traffic chart: {e}")

    # --- New PageSpeed Radar Charts by Category ---
    try:
        if pagespeed_loaded and df_pagespeed_raw is not None and not df_pagespeed_raw.empty:
            logging.info("Preparing data for PageSpeed radar charts...")
            
            # Use a copy to avoid modifying the original used for Excel
            df_ps_radar = df_pagespeed_raw.copy()
            df_ps_radar.columns = [col.lower().strip() for col in df_ps_radar.columns]
            
            # Filter out 'Other' and 'Blog Category' before any processing
            category_col_name = 'category' # Assuming this is the column name in the CSV
            categories_to_remove = ['Other', 'Blog Category']
            if category_col_name in df_ps_radar.columns:
                initial_rows = len(df_ps_radar)
                df_ps_radar = df_ps_radar[~df_ps_radar[category_col_name].isin(categories_to_remove)]
                rows_removed = initial_rows - len(df_ps_radar)
                if rows_removed > 0:
                    logging.info(f"Filtered out {rows_removed} rows for categories {categories_to_remove} for radar charts.")
                else:
                    logging.info(f"Categories {categories_to_remove} not found or already excluded for radar charts.")
            else:
                logging.warning(f"Column '{category_col_name}' not found in PageSpeed data, cannot filter categories for radar charts.")

            # Metrics to visualize (check they exist after normalization)
            metrics_radar = ['lcp', 'tbt', 'cls', 'fcp', 'speed_index']
            # Check if speed_index exists, otherwise remove it too
            base_mobile_cols = [f'mobile_{m}' for m in metrics_radar]
            base_desktop_cols = [f'desktop_{m}' for m in metrics_radar]
            if 'mobile_speed_index' not in df_ps_radar.columns or 'desktop_speed_index' not in df_ps_radar.columns:
                metrics_radar = ['lcp', 'tbt', 'cls', 'fcp'] # Fallback without speed index
            
            mobile_cols = [f'mobile_{m}' for m in metrics_radar]
            desktop_cols = [f'desktop_{m}' for m in metrics_radar]
            category_col = 'category'
            
            cols_to_check = mobile_cols + desktop_cols + [category_col]
            if not all(col in df_ps_radar.columns for col in cols_to_check):
                logging.warning(f"Missing PageSpeed columns for radar charts. Expected: {cols_to_check}. Found: {list(df_ps_radar.columns)}")
            else:
                # Convert to numeric
                for col in mobile_cols + desktop_cols:
                     df_ps_radar[col] = pd.to_numeric(df_ps_radar[col], errors='coerce')
                df_ps_radar = df_ps_radar.dropna(subset=mobile_cols + desktop_cols + [category_col])

                if not df_ps_radar.empty:
                    # Min-Max normalization (0-1) and inversion for "lower is better"
                    # Note: score is no longer included
                    metrics_lower_is_better = ['lcp', 'tbt', 'cls', 'fcp', 'speed_index']
                    df_scaled = df_ps_radar[[category_col]].copy()

                    for metric in metrics_radar:
                        for platform in ['mobile', 'desktop']:
                            col_name = f'{platform}_{metric}'
                            min_val = df_ps_radar[col_name].min()
                            max_val = df_ps_radar[col_name].max()
                            scaled_col_name = f'{col_name}_scaled'
                            
                            if max_val == min_val: # Avoid division by zero
                                df_scaled[scaled_col_name] = 0.5 # Neutral value
                            else:
                                df_scaled[scaled_col_name] = (df_ps_radar[col_name] - min_val) / (max_val - min_val)
                            
                            # Invert for "lower is better" metrics
                            if metric in metrics_lower_is_better:
                                df_scaled[scaled_col_name] = 1 - df_scaled[scaled_col_name]
                    
                    # Aggregate by category (average of normalized scores)
                    radar_data = df_scaled.groupby(category_col).mean().reset_index()
                    
                    # Limit the number of categories for readability
                    max_categories_on_radar = 8
                    if len(radar_data) > max_categories_on_radar:
                         # Select categories with the most URLs in the original sample
                         top_categories = df_ps_radar[category_col].value_counts().nlargest(max_categories_on_radar).index
                         radar_data = radar_data[radar_data[category_col].isin(top_categories)]
                         logging.info(f"Radar charts limited to {max_categories_on_radar} main categories.")

                    if not radar_data.empty:
                        # Prepare for plotting
                        labels = metrics_radar
                        num_vars = len(labels)
                        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist() + [0] # Close the circle
                        labels_upper = [l.upper() for l in labels] # Axis labels

                        # Use a more distinct palette
                        colors = plt.cm.get_cmap('tab10', max_categories_on_radar)

                        # --- Mobile Plot ---
                        fig_mob, ax_mob = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True)) # Slightly increased size
                        ax_mob.set_theta_offset(pi / 2)
                        ax_mob.set_theta_direction(-1)
                        plt.xticks(angles[:-1], labels_upper)
                        ax_mob.set_yticks(np.linspace(0, 1, 5)) 
                        ax_mob.set_yticklabels([f"{i*100:.0f}" for i in np.linspace(0, 1, 5)]) 
                        ax_mob.set_ylim(0, 1)

                        for i, row in radar_data.iterrows():
                            category = row[category_col]
                            values = row[[f'mobile_{m}_scaled' for m in metrics_radar]].values.flatten().tolist()
                            values += values[:1] 
                            ax_mob.plot(angles, values, color=colors(i), linewidth=2.5, linestyle='solid', label=category) # More visible line
                            ax_mob.fill(angles, values, color=colors(i), alpha=0.35) # Slightly increased alpha
                        
                        plt.title('Mobile PageSpeed Performance by Category (Normalized Sample)', size=14, y=1.1) # Translated
                        # Place legend outside
                        ax_mob.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
                        # plt.tight_layout() # Warning: tight_layout can interact poorly with bbox_to_anchor
                        plt.subplots_adjust(right=0.75) # Adjust space for legend
                        plt.savefig(f'{charts_dir}/Radar_PageSpeed_Mobile_ByCategory.png', bbox_inches='tight') # bbox_inches can help
                        plt.close(fig_mob)
                        logging.info("Mobile radar chart saved.") # Translated

                        # --- Desktop Plot ---
                        fig_desk, ax_desk = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
                        ax_desk.set_theta_offset(pi / 2)
                        ax_desk.set_theta_direction(-1)
                        plt.xticks(angles[:-1], labels_upper)
                        ax_desk.set_yticks(np.linspace(0, 1, 5))
                        ax_desk.set_yticklabels([f"{i*100:.0f}" for i in np.linspace(0, 1, 5)])
                        ax_desk.set_ylim(0, 1)

                        for i, row in radar_data.iterrows():
                            category = row[category_col]
                            values = row[[f'desktop_{m}_scaled' for m in metrics_radar]].values.flatten().tolist()
                            values += values[:1]
                            ax_desk.plot(angles, values, color=colors(i), linewidth=2.5, linestyle='solid', label=category)
                            ax_desk.fill(angles, values, color=colors(i), alpha=0.35)
                        
                        plt.title('Desktop PageSpeed Performance by Category (Normalized Sample)', size=14, y=1.1) # Translated
                        # Place legend outside
                        ax_desk.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
                        # plt.tight_layout()
                        plt.subplots_adjust(right=0.75)
                        plt.savefig(f'{charts_dir}/Radar_PageSpeed_Desktop_ByCategory.png', bbox_inches='tight')
                        plt.close(fig_desk)
                        logging.info("Desktop radar chart saved.") # Translated
                    else:
                         logging.info("No aggregated data for radar charts after filtering/limiting.") # Translated
                else:
                    logging.warning("Not enough valid PageSpeed data after cleaning to generate radar charts.") # Translated
            # End of column check
        else:
            logging.info("PageSpeed data not loaded or empty, radar charts will not be generated.") # Translated
            
    except Exception as e:
        logging.error(f"Error generating PageSpeed radar charts: {e}", exc_info=True) # Translated

    logging.info("Analysis pipeline completed successfully!") # Translated

if __name__ == '__main__':
    main() 