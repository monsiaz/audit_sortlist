#!/usr/bin/env python3

import csv
import os

def clean_value(value):
    """Nettoie une valeur en retirant les guillemets et les espaces."""
    if isinstance(value, str):
        return value.strip().strip('"')
    return value

def extract_redirects():
    input_file = '/Volumes/T7/sortlist/Crawl/Datas/liens_entrants_tous-sortlist.csv'
    output_file = '/Volumes/T7/sortlist/Crawl/Datas/redirections.csv'
    
    # Supprimer le fichier de sortie s'il existe
    if os.path.exists(output_file):
        os.remove(output_file)
    
    print("Extraction des redirections 301 et 302 (excluant le blog)...")
    count = 0
    excluded_count = 0
    
    with open(input_file, 'r', encoding='utf-8-sig') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        # Lire le CSV source
        reader = csv.DictReader(infile)
        
        # Configurer l'écrivain avec les mêmes en-têtes
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        # Filtrer les redirections
        for row in reader:
            status_code = clean_value(row['Code de statut'])
            destination = clean_value(row['Destination'])
            
            if status_code in ['301', '302']:
                if 'https://www.sortlist.com/blog' not in destination:
                    writer.writerow(row)
                    count += 1
                else:
                    excluded_count += 1
                
                if (count + excluded_count) % 1000 == 0:
                    print(f"Redirections trouvées : {count} (exclues : {excluded_count})")
    
    print(f"\nTerminé !")
    print(f"- {count} redirections ont été extraites vers {output_file}")
    print(f"- {excluded_count} redirections vers le blog ont été exclues")
    
    # Vérifier le contenu du fichier
    print("\nVérification du contenu du fichier :")
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < 3:  # Afficher les 3 premières lignes
                print(f"\nRedirection {i+1} :")
                print(f"Source : {row['Source']}")
                print(f"Destination : {row['Destination']}")
                print(f"Code de statut : {row['Code de statut']}")
            else:
                break

if __name__ == '__main__':
    extract_redirects() 