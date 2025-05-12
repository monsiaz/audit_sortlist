import pandas as pd
import networkx as nx
import logging
from typing import Tuple
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import numpy as np

def calculate_pagerank(con) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculates standard and weighted PageRank from DuckDB tables.
    Returns two DataFrames: pr_df (standard PageRank), prw_df (weighted PageRank).
    """
    try:
        logging.info("Starting PageRank calculation")
        # Retrieve internal URLs
        internal_urls = con.execute("""
            SELECT DISTINCT url
            FROM pages
            WHERE url LIKE 'https://www.sortlist.com/%';
        """).df()
        if len(internal_urls) == 0:
            raise ValueError("No internal URLs found")
        logging.info(f"{len(internal_urls)} internal URLs identified")
        # Retrieve incoming links
        edges_df = con.execute("""
            SELECT 
                src as src,
                dst as dst,
                pos as pos,
                COUNT(*) as link_count
            FROM edges
            WHERE src LIKE 'https://www.sortlist.com/%'
              AND dst LIKE 'https://www.sortlist.com/%'
              AND src != dst
            GROUP BY src, dst, pos;
        """).df()
        if len(edges_df) == 0:
            raise ValueError("No internal links found")
        logging.info(f"{len(edges_df)} unique internal links identified")
        # Standard PageRank
        G = nx.DiGraph()
        all_urls = set(internal_urls['url'].unique())
        for url in all_urls:
            G.add_node(url)
        for _, row in edges_df.iterrows():
            G.add_edge(row['src'], row['dst'], weight=row['link_count'])
        pr_dict = nx.pagerank(
            G,
            alpha=0.85,
            max_iter=100,
            tol=1e-6,
            nstart=None,
            weight='weight'
        )
        pr_df = pd.DataFrame(list(pr_dict.items()), columns=['url', 'PageRank'])
        logging.info(f"Standard PageRank calculated for {len(pr_df)} URLs")
        # Weighted PageRank (by link position)
        weight_map = {
            "Contenu": 1.0,
            "Header": 0.5,
            "Footer": 0.3,
            "Sidebar": 0.4,
            "Menu": 0.6
        }
        Gw = nx.DiGraph()
        for url in all_urls:
            Gw.add_node(url)
        for _, row in edges_df.iterrows():
            pos_weight = weight_map.get(row['pos'], 0.2)
            total_weight = pos_weight * row['link_count']
            Gw.add_edge(row['src'], row['dst'], weight=total_weight)
        prw_dict = nx.pagerank(
            Gw,
            alpha=0.85,
            max_iter=100,
            tol=1e-6,
            nstart=None,
            weight='weight'
        )
        prw_df = pd.DataFrame(list(prw_dict.items()), columns=['url', 'Weighted_PageRank'])
        logging.info(f"Weighted PageRank calculated for {len(prw_df)} URLs")
        return pr_df, prw_df
    except Exception as e:
        logging.error(f"Error during PageRank calculation: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

def calculate_advanced_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates advanced metrics for SEO analysis.
    """
    try:
        logging.info("Starting calculation of advanced metrics")
        numeric_columns = ['clicks', 'impressions', 'ctr', 'PageRank', 'Weighted_PageRank']
        df[numeric_columns] = df[numeric_columns].fillna(0)
        # Base metrics
        df['Traffic_Score'] = df['clicks'] * df['ctr']
        df['PR_Traffic_Ratio'] = df['PageRank'] / (df['clicks'] + 1)
        df['WPR_Traffic_Ratio'] = df['Weighted_PageRank'] / (df['clicks'] + 1)
        # SEO Score
        df['SEO_Score'] = (df['PageRank'] * 0.3 + df['Weighted_PageRank'] * 0.3 +
                          df['clicks'] * 0.2 + df['ctr'] * 0.1 + df['impressions'] * 0.1)
        df['Visibility_Score'] = (df['impressions'] * 0.4 + df['clicks'] * 0.4 + df['ctr'] * 0.2)
        # Score by content type
        if 'content_type' in df.columns:
            df['Content_Type_Score'] = df.groupby('content_type')['SEO_Score'].transform('mean')
        else:
            df['Content_Type_Score'] = 0
        # Score by country
        if 'country' in df.columns:
            df['Country_Score'] = df.groupby('country')['SEO_Score'].transform('mean')
        else:
            df['Country_Score'] = 0
        # Normalization
        scaler = MinMaxScaler()
        metrics = ['PageRank', 'Weighted_PageRank', 'clicks', 'ctr', 'Traffic_Score', 
                  'SEO_Score', 'Visibility_Score', 'Content_Type_Score', 'Country_Score']
        df[metrics] = df[metrics].fillna(0)
        for metric in metrics:
            if df[metric].nunique() > 1:
                df[f'{metric}_Normalized'] = scaler.fit_transform(df[[metric]])
            else:
                df[f'{metric}_Normalized'] = 0
        # Weighted global performance score
        weights = {
            'PageRank_Normalized': 0.15,
            'Weighted_PageRank_Normalized': 0.15,
            'clicks_Normalized': 0.15,
            'ctr_Normalized': 0.1,
            'Traffic_Score_Normalized': 0.1,
            'SEO_Score_Normalized': 0.15,
            'Visibility_Score_Normalized': 0.1,
            'Content_Type_Score_Normalized': 0.05,
            'Country_Score_Normalized': 0.05
        }
        df['Performance_Score'] = sum(df[col] * weight for col, weight in weights.items())
        # Page clustering
        features = ['PageRank_Normalized', 'Weighted_PageRank_Normalized', 
                   'clicks_Normalized', 'ctr_Normalized', 'SEO_Score_Normalized']
        df_cluster = df[features].copy().fillna(0)
        kmeans = KMeans(n_clusters=4, random_state=42)
        df['Cluster'] = kmeans.fit_predict(df_cluster)
        logging.info("Advanced metrics and clustering calculated")
        return df
    except Exception as e:
        logging.error(f"Error during calculation of advanced metrics: {str(e)}")
        return None 