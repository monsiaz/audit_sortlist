#!/usr/bin/env python3

import csv
import os
from collections import defaultdict

def remove_duplicates():
    input_file = '/Volumes/T7/sortlist/Crawl/Datas/redirections.csv'
    output_file = '/Volumes/T7/sortlist/Crawl/Datas/redirections_unique.csv'
    
    # Compteur pour les statistiques
    total_rows = 0
    unique_destinations = set()
    duplicates = 0
    
    # Dictionnaire pour stocker les lignes uniques
    unique_rows = {}
    
    print("Lecture du fichier et suppression des doublons...")
    
    # Lire le fichier d'entrée
    with open(input_file, 'r', encoding='utf-8-sig') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        # Parcourir toutes les lignes
        for row in reader:
            total_rows += 1
            destination = row['Destination']
            
            if destination not in unique_destinations:
                unique_destinations.add(destination)
                unique_rows[destination] = row
            else:
                duplicates += 1
            
            # Afficher la progression tous les 10000 lignes
            if total_rows % 10000 == 0:
                print(f"Lignes traitées : {total_rows}")
    
    # Écrire le fichier de sortie
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_rows.values())
    
    # Afficher les statistiques
    print("\nStatistiques :")
    print(f"Nombre total de lignes : {total_rows}")
    print(f"Nombre de destinations uniques : {len(unique_destinations)}")
    print(f"Nombre de doublons supprimés : {duplicates}")
    print(f"\nFichier sauvegardé : {output_file}")
    
    # Afficher un aperçu des résultats
    print("\nAperçu des résultats :")
    with open(output_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < 3:  # Afficher les 3 premières lignes
                print(f"\nLigne {i+1}:")
                print(f"Source : {row['Source']}")
                print(f"Destination : {row['Destination']}")
            else:
                break

if __name__ == '__main__':
    remove_duplicates() 