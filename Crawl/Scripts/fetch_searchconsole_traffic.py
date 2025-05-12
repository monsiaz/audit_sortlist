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
INPUT_CSV_DEFAULT = '/Volumes/T7/sortlist/Crawl/interne_html-sortlist.csv'
# Fichiers de sortie fixes dans /Volumes/T7/sortlist
OUTPUT_CSV_DEFAULT = '/Volumes/T7/sortlist/searchconsole_traffic.csv'
LOG_FILE_DEFAULT = '/Volumes/T7/sortlist/fetch_searchconsole_traffic.log'

# ------------ ARGPARSE ------------
parser = argparse.ArgumentParser(description='Fetch Search Console traffic for URLs in CSV.')
parser.add_argument('--input', '-i', default=INPUT_CSV_DEFAULT,
                    help=f"Chemin vers le CSV d'input (défaut: {INPUT_CSV_DEFAULT})")
parser.add_argument('--output', '-o', default=OUTPUT_CSV_DEFAULT,
                    help=f"Chemin du CSV de sortie (défaut: {OUTPUT_CSV_DEFAULT})")
parser.add_argument('--log', '-l', default=LOG_FILE_DEFAULT,
                    help=f"Chemin du fichier de log (défaut: {LOG_FILE_DEFAULT})")
args = parser.parse_args()
INPUT_CSV = args.input
OUTPUT_CSV = args.output
LOG_FILE = args.log

# ------------ CRÉATION DES RÉPERTOIRES SI NÉCESSAIRE ------------
for path in [LOG_FILE, OUTPUT_CSV]:
    dirpath = os.path.dirname(path)
    if dirpath and not os.path.exists(dirpath):
        try:
            os.makedirs(dirpath, exist_ok=True)
        except Exception as e:
            print(f"Impossible de créer le dossier '{dirpath}': {e}")
            sys.exit(1)

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
    if not os.path.exists(path):
        logging.error(f"Fichier d'entrée non trouvé: {path}")
        sys.exit(1)
    urls = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            logging.error(f"Fichier CSV vide: {path}")
            sys.exit(1)
        # Nettoyage du header
        cleaned = [h.strip().replace('"', '').lstrip('\ufeff') for h in header]
        logging.info(f"En-têtes CSV nettoyées : {cleaned}")
        if 'Adresse' in cleaned:
            idx = cleaned.index('Adresse')
        elif 'URL' in cleaned:
            idx = cleaned.index('URL')
        else:
            logging.error("Aucune colonne 'Adresse' ou 'URL' trouvée dans l'en-tête CSV.")
            sys.exit(1)
        for row in reader:
            if len(row) > idx and row[idx].strip():
                urls.append(row[idx].strip().strip('"'))
    return urls


def load_processed_urls(path):
    processed = set()
    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                u = row.get('URL')
                if u:
                    processed.add(u.strip())
    logging.info(f"URLs déjà traitées : {len(processed)}")
    return processed


def init_output(path):
    if not os.path.exists(path):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Clicks', 'Impressions', 'CTR', 'Average Position'])
            f.flush()


def fetch_metrics(url):
    req = {
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
    resp = service.searchanalytics().query(siteUrl=SITE_URL, body=req).execute()
    rows = resp.get('rows', [])
    if not rows:
        return 0, 0, 0.0, 0.0
    d = rows[0]
    return d.get('clicks', 0), d.get('impressions', 0), d.get('ctr', 0), d.get('position', 0)

# ------------ BOUCLE PRINCIPALE ------------
def main():
    logging.info(f"Entrée: {INPUT_CSV} | Sortie: {OUTPUT_CSV}")
    urls = load_input_urls(INPUT_CSV)
    total = len(urls)
    if total == 0:
        logging.error("Aucune URL trouvée dans le fichier d'entrée.")
        sys.exit(1)
    init_output(OUTPUT_CSV)
    processed = load_processed_urls(OUTPUT_CSV)
    to_process = [u for u in urls if u not in processed]
    logging.info(f"Total URLs: {total}, déjà traitées: {len(processed)}, reste: {len(to_process)}")
    start = time.time()
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        for i, url in enumerate(to_process, start=1):
            try:
                num = len(processed) + i
                logging.info(f"({num}/{total}) Fetching: {url}")
                c, imp, ctr, pos = fetch_metrics(url)
                writer.writerow([url, c, imp, f"{ctr:.4f}", f"{pos:.2f}"])
                out.flush()
                logging.info(f"Écrit: {url}")
            except Exception as e:
                logging.error(f"Erreur sur {url}: {e}")
                sys.exit(1)
    logging.info("Terminé pour toutes les URLs.")

if __name__ == '__main__':
    main()
