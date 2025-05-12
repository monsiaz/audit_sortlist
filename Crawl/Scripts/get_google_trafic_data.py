#!/usr/bin/env python3
"""
Script complet pour extraire le trafic via l'API Search Console sur 6 mois,
à partir d'un CSV d'URLs, avec reprise sur crash.

Pré-requis :
    python3 -m pip install --upgrade pip
    python3 -m pip install google-api-python-client google-auth google-auth-httplib2 python-dateutil

Exécution :
    chmod +x get_google_trafic_data.py
    ./get_google_trafic_data.py
"""
import os
import csv
import time
import datetime
import argparse
from dateutil.relativedelta import relativedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging
import sys

# ------------ CONFIGURATION PAR DÉFAUT ------------
KEY_FILE_LOCATION = '/Volumes/T7/sortlist/leafy-brace-242115-c73d373e2d41.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
SITE_URL = 'https://www.sortlist.com'
# Chemin par défaut du CSV d'entrée
INPUT_CSV_DEFAULT = '/Volumes/T7/sortlist/Crawl/interne_html-sortlist.csv'
OUTPUT_CSV_DEFAULT = 'searchconsole_traffic.csv'
LOG_FILE_DEFAULT = 'fetch_searchconsole_traffic.log'

# ------------ SETUP ARGPARSE ------------
parser = argparse.ArgumentParser(description='Fetch Search Console traffic for URLs in CSV.')
parser.add_argument('--input', '-i', default=INPUT_CSV_DEFAULT,
                    help=f"Chemin vers le CSV d'input (défaut: {INPUT_CSV_DEFAULT})")
parser.add_argument('--output', '-o', default=OUTPUT_CSV_DEFAULT,
                    help=f"Chemin vers le CSV de sortie (défaut: {OUTPUT_CSV_DEFAULT})")
parser.add_argument('--log', '-l', default=LOG_FILE_DEFAULT,
                    help=f"Chemin vers le fichier de log (défaut: {LOG_FILE_DEFAULT})")
args = parser.parse_args()
INPUT_CSV = args.input
OUTPUT_CSV = args.output
LOG_FILE = args.log

# ------------ SETUP LOGGING ------------
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# ------------ CALCUL DES DATES ------------
today = datetime.date.today()
six_months_ago = today - relativedelta(months=6)

# ------------ AUTHENTIFICATION ------------
logging.info("Authentification avec Google API...")
try:
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE_LOCATION,
        scopes=SCOPES
    )
    service = build('searchconsole', 'v1', credentials=credentials)
except Exception as e:
    logging.error(f"Échec de l'authentification : {e}")
    sys.exit(1)

# ------------ FONCTIONS UTILES ------------

def load_input_urls(path):
    """
    Lit le CSV d'entrée, nettoie les en-têtes et renvoie la liste des URLs.
    Utilise csv.reader pour un parsing robuste du header et des lignes.
    """
    if not os.path.exists(path):
        logging.error(f"Fichier d'entrée non trouvé: {path}")
        sys.exit(1)
    urls = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            logging.error(f"Fichier CSV vide: {path}")
            sys.exit(1)
        # Nettoyer chaque nom de colonne
        cleaned_header = [h.strip().replace('"', '').lstrip('﻿') for h in raw_header]
        logging.info(f"En-têtes CSV nettoyées : {cleaned_header}")
        # Trouver l'index de la colonne URL
        if 'Adresse' in cleaned_header:
            url_idx = cleaned_header.index('Adresse')
        elif 'URL' in cleaned_header:
            url_idx = cleaned_header.index('URL')
        else:
            logging.error("Aucune colonne 'Adresse' ou 'URL' trouvée dans l'en-tête CSV.")
            sys.exit(1)
        # Parcourir chaque ligne et extraire l'URL
        for row in reader:
            if len(row) > url_idx:
                raw_url = row[url_idx]
                if raw_url:
                    urls.append(raw_url.strip().strip('"'))
    return urls


def load_processed_urls(path):
    processed = set()
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed.add(row.get('URL', '').strip())
    return processed


def init_output(path):
    if not os.path.exists(path):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Clicks', 'Impressions', 'CTR', 'Average Position'])
            f.flush()


def fetch_metrics(url):
    request = {
        'startDate': six_months_ago.isoformat(),
        'endDate': today.isoformat(),
        'dimensions': ['page'],
        'dimensionFilterGroups': [{
            'filters': [{
                'dimension': 'page',
                'operator': 'equals',
                'expression': url
            }]
        }],
        'aggregationType': 'byPage',
        'rowLimit': 1
    }
    response = service.searchanalytics().query(
        siteUrl=SITE_URL,
        body=request
    ).execute()
    rows = response.get('rows', [])
    if not rows:
        return 0, 0, 0.0, 0.0
    data = rows[0]
    return (
        data.get('clicks', 0),
        data.get('impressions', 0),
        data.get('ctr', 0),
        data.get('position', 0)
    )

# ------------ BOUCLE PRINCIPALE ------------
def main():
    logging.info("Démarrage du script...")
    urls = load_input_urls(INPUT_CSV)
    total = len(urls)
    if total == 0:
        logging.error("Aucune URL trouvée dans le fichier d'entrée.")
        sys.exit(1)

    init_output(OUTPUT_CSV)
    processed = load_processed_urls(OUTPUT_CSV)
    to_process = [u for u in urls if u not in processed]
    count = len(processed)
    start_time = time.time()

    logging.info(f"Total URLs: {total}, déjà traitées: {count}, reste: {len(to_process)}")

    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        for idx, url in enumerate(to_process, start=1):
            try:
                processed_count = count + idx
                logging.info(f"({processed_count}/{total}) Fetching metrics for: {url}")
                t0 = time.time()
                clicks, impressions, ctr, position = fetch_metrics(url)
                writer.writerow([url, clicks, impressions, f"{ctr:.4f}", f"{position:.2f}"])
                fout.flush()
                elapsed = time.time() - t0
                avg_time = (time.time() - start_time) / processed_count
                remaining = total - processed_count
                eta = datetime.timedelta(seconds=int(avg_time * remaining))
                logging.info(f"Done in {elapsed:.2f}s, ETA remaining: {eta}")
            except Exception as e:
                logging.error(f"Erreur sur {url}: {e}")
                logging.info("Sauvegarde de l'état et arrêt du script.")
                sys.exit(1)
    logging.info("Traitement terminé pour toutes les URLs.")

if __name__ == '__main__':
    main()
