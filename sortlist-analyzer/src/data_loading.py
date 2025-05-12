import pandas as pd
import duckdb
import logging
import os
import yaml
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_data(con, config: Dict[str, Any]) -> bool:
    data_dir = config['data_dir']
    files = config['csv_files']
    try:
        # Load pages
        pages_path = os.path.join(data_dir, files['pages'])
        con.execute(f'''
            CREATE TABLE pages AS
            SELECT 
                "Adresse" as url,
                "Type de contenu" as content_type,
                "Code HTTP" as http_code,
                "Statut" as status,
                "Indexabilité" as indexability,
                "Liens entrants" as incoming_links,
                "Liens sortants" as outgoing_links,
                "Crawl profondeur" as crawl_depth,
                "Nombre de mots" as word_count
            FROM read_csv_auto('{pages_path}');
        ''')
        logging.info(f"Pages loaded from {pages_path}")

        # Load links
        edges_path = os.path.join(data_dir, files['edges'])
        con.execute(f'''
            CREATE TABLE edges AS
            SELECT 
                "Source" as src,
                "Destination" as dst,
                "Type" as link_type,
                "Position du lien" as pos
            FROM read_csv_auto('{edges_path}');
        ''')
        logging.info(f"Links loaded from {edges_path}")

        # Load categories
        cat_path = os.path.join(data_dir, files['categories'])
        con.execute(f'''
            CREATE TABLE categorized AS
            SELECT 
                Adresse as url,
                Category as category,
                Label as label,
                Country as country,
                Location as location
            FROM read_csv_auto('{cat_path}');
        ''')
        logging.info(f"Categories loaded from {cat_path}")

        # Load traffic
        traffic_path = os.path.join(data_dir, files['traffic'])
        con.execute(f'''
            CREATE TABLE traffic AS
            SELECT 
                URL as url,
                Clicks as clicks,
                Impressions as impressions,
                CTR as ctr,
                "Average Position" as avg_position
            FROM read_csv_auto('{traffic_path}');
        ''')
        logging.info(f"Traffic loaded from {traffic_path}")

        # Load engine logs
        logs_path = os.path.join(data_dir, files['logs'])
        con.execute(f'''
            CREATE TABLE logs_events AS
            SELECT 
                event_url,
                event_bot_name,
                event_datetime as event_date,
                event_status_code as event_status
            FROM read_csv_auto('{logs_path}');
        ''')
        logging.info(f"Engine logs loaded from {logs_path}")

        return True
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        return False 