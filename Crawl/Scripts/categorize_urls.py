#!/usr/bin/env python3

import argparse
from urllib.parse import urlparse
import csv
import time
from datetime import datetime, timedelta

# Mapping custom pour villes/pays sans code pays
CITY_COUNTRY_MAP = {
    'singapore': 'SG',
    'dubai': 'AE',
    'abu': 'AE',
    'abu dhabi': 'AE',
    'melbourne': 'AU',
    'cape': 'ZA',
    'dublin': 'IE',
    'barcelona': 'ES',
    'paris': 'FR',
    'berlin': 'DE',
    'amsterdam': 'NL'
}

def extract_location_country(segment):
    """Extrait la location et le pays d'un segment d'URL"""
    parts = segment.split('-')
    if len(parts) > 1:
        # Le dernier élément est le code pays
        country = parts[-1].upper()
        # Tous les autres éléments forment la location
        location = ' '.join(p.title() for p in parts[:-1])
        return location, country
    
    # Si pas de tiret, vérifier si c'est une ville connue
    location = segment.title()
    country = CITY_COUNTRY_MAP.get(segment.lower(), '')
    return location, country

def categorize(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    segments = [s for s in path.split('/') if s]

    if not segments:
        return 'HomePage', 'HomePage'

    first = segments[0]

    # Agency prioritaire
    if first == 'agency' and len(segments) >= 2:
        return 'Agency', ''

    # Project
    if first == 'project':
        return 'Project', 'Project'
    
    # Blog
    if first == 'blog':
        if len(segments) == 1:
            return 'Blog', 'Blog Root'
        elif len(segments) >= 2 and segments[1] == 'category':
            label = ' > '.join(s.replace('-', ' ').title() for s in segments[2:])
            return 'Blog Category', label
        else:
            return 'Blog', 'Blog Article'

    # Datahub
    if first == 'datahub':
        if len(segments) >= 2 and segments[1] == 'reports_categories':
            return 'Datahub', 'Datahub Landing'
        elif len(segments) >= 2 and segments[1] == 'reports':
            return 'Datahub', 'Datahub'

    # Landing Location
    if first == 'l' and len(segments) >= 2:
        return 'Landing Location', ''

    # Landing avec /i/ ou /s/ (ex: /i/3d-design/paris-fr, /s/social-media-optimization/abu-dhabi-ae)
    if first in ['i', 's'] and len(segments) >= 3:
        service = segments[1].replace('-', ' ').title()
        return 'Landing', service

    # Service Landing avec location (ex: /3d-design/cape-town-za, /design/singapore)
    if len(segments) == 2:
        service = segments[0].replace('-', ' ').title()
        # Vérifier si le deuxième segment est une ville connue ou contient un code pays
        if segments[1].lower() in CITY_COUNTRY_MAP or '-' in segments[1]:
            return 'Landing', service

    # Service Landing global (ex: /digital-marketing, /photography)
    if len(segments) == 1:
        return 'Service Landing', segments[0].replace('-', ' ').title()

    # Service Landing avec sous-catégorie (ex: /advertising-production)
    if len(segments) == 1 and '-' in segments[0]:
        return 'Service Landing', segments[0].replace('-', ' ').title()

    # Event pages
    if first == 'event':
        return 'Event', ' '.join(segments[1:]).replace('-', ' ').title()

    return 'Other', ' '.join(segments).replace('-', ' ').title()

def main():
    parser = argparse.ArgumentParser(description='Categorize URLs by path pattern')
    parser.add_argument('-i', '--input', required=True, help='Input CSV file path')
    parser.add_argument('-o', '--output', required=True, help='Output CSV file path')
    args = parser.parse_args()

    print("\nStarting URL categorization...")
    start_time = time.time()
    processed = 0

    with open(args.input, newline='', encoding='utf-8-sig') as infile, \
         open(args.output, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)
        writer.writerow(['Adresse', 'Category', 'Label', 'Location', 'Country', 'Pagination'])
        
        for row in reader:
            url = row.get('Adresse', '').strip()
            if not url:
                continue
                
            parsed = urlparse(url)
            category, label = categorize(url)
            segs = [s for s in parsed.path.strip('/').split('/') if s]
            
            # Si HomePage, label vide
            if category == 'HomePage':
                label = ''
            # Si Landing Location, label vide
            if category == 'Landing Location':
                label = ''
            
            location = ''
            country = ''

            # Gestion des locations pour les pages de type Landing et Landing Location
            if category in ['Landing', 'Landing Location']:
                # Pour les URLs avec /i/ ou /s/, le dernier segment contient la location
                if segs[0] in ['i', 's'] and len(segs) >= 3:
                    location, country = extract_location_country(segs[-1])
                # Pour les autres URLs, chercher le segment avec un tiret ou une ville connue
                else:
                    for seg in reversed(segs):
                        if '-' in seg or seg.lower() in CITY_COUNTRY_MAP:
                            location, country = extract_location_country(seg)
                            break

            # Pour les autres types de pages, pas de location ni de country
            if category in ['Service Landing', 'HomePage', 'Blog', 'Blog Category', 'Blog Article', 'Datahub', 'Project', 'Event']:
                location = 'Global'
                country = ''

            pagination = 'Yes' if parsed.query and 'page=' in parsed.query else 'No'

            writer.writerow([url, category, label, location, country, pagination])
            processed += 1
            
            if category == 'Other':
                print(f"⚠️ Non catégorisé clairement : {url}")
            if processed % 100 == 0:
                elapsed = time.time() - start_time
                print(f"\nProgress: {processed} URLs processed - {elapsed:.1f}s elapsed")
                print("=" * 80)

    print(f'\nDone: wrote categorized URLs to {args.output}')

if __name__ == '__main__':
    main() 