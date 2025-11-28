#!/usr/bin/env python3
"""
Script om opgesplitst_grouped.json data te koppelen aan municipalities.geojson.
Voegt gedetailleerde uitsplitsing toe aan elke gemeente.
"""

import json
from collections import defaultdict


def normalize_municipality_name(name: str) -> str:
    """
    Normaliseer gemeentenaam voor matching.
    Verwijdert 'Gemeente en OCMW' prefix en maakt lowercase.
    """
    name = name.strip()
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name.lower()


def load_opgesplitst_data(filepath: str) -> dict:
    """
    Laad opgesplitst_grouped.json en organiseer per gemeente.
    
    Returns:
        Dict met genormaliseerde gemeentenamen als keys en dict met rekeningen als values
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Organiseer data per gemeente
    municipality_data = defaultdict(lambda: {
        'rekeningen': [],
        'totaal': 0.0,
        'boekjaar': data['boekjaar'],
        'type_rapport': data['type_rapport']
    })
    
    for rekening_code, rekening_data in data['rekeningen'].items():
        gemeenten = rekening_data.get('gemeenten', {})
        
        for gemeente_naam, bedrag in gemeenten.items():
            normalized_name = normalize_municipality_name(gemeente_naam)
            
            # Voeg rekening toe aan gemeente
            municipality_data[normalized_name]['rekeningen'].append({
                'code': rekening_code,
                'naam': rekening_data['alg_rekening'],
                'bedrag': bedrag,
                'categorie': rekening_data['categorie'],
                'niveau_1': rekening_data['niveaus']['niveau_1'],
                'niveau_2': rekening_data['niveaus']['niveau_2'],
                'niveau_3': rekening_data['niveaus']['niveau_3'],
                'niveau_diepte': rekening_data['niveau_diepte']
            })
            
            # Tel op voor totaal
            municipality_data[normalized_name]['totaal'] += bedrag
    
    # Rond totalen af
    for gemeente in municipality_data.values():
        gemeente['totaal'] = round(gemeente['totaal'], 2)
        # Sorteer rekeningen op bedrag (hoogste eerst)
        gemeente['rekeningen'].sort(key=lambda x: abs(x['bedrag']), reverse=True)
    
    return dict(municipality_data)


def enrich_geojson(geojson_path: str, opgesplitst_data: dict, output_path: str):
    """
    Voeg opgesplitste data toe aan GeoJSON.
    """
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    matched = 0
    not_matched = 0
    
    for feature in geojson['features']:
        municipality = feature['properties']['municipality']
        normalized_name = normalize_municipality_name(municipality)
        
        if normalized_name in opgesplitst_data:
            # Voeg de opgesplitste data toe
            gemeente_data = opgesplitst_data[normalized_name]
            
            # Voeg samenvattende statistieken toe
            feature['properties']['detail_2024'] = {
                'totaal_details': gemeente_data['totaal'],
                'aantal_rekeningen': len(gemeente_data['rekeningen']),
                'boekjaar': gemeente_data['boekjaar'],
                'type_rapport': gemeente_data['type_rapport'],
                'verschil_met_totaal': round(
                    gemeente_data['totaal'] - feature['properties']['2024'], 
                    2
                )
            }
            
            # Voeg top 10 grootste rekeningen toe voor compactheid
            feature['properties']['detail_2024']['top_rekeningen'] = [
                {
                    'code': r['code'],
                    'naam': r['naam'],
                    'bedrag': r['bedrag'],
                    'categorie': r['categorie']
                }
                for r in gemeente_data['rekeningen'][:10]
            ]
            
            # Optioneel: voeg volledige lijst toe (kan groot zijn)
            # feature['properties']['detail_2024']['alle_rekeningen'] = gemeente_data['rekeningen']
            
            matched += 1
        else:
            not_matched += 1
            feature['properties']['detail_2024'] = None
    
    # Bewaar verrijkte GeoJSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Verrijkte GeoJSON opgeslagen: {output_path}")
    print(f"  Matched: {matched} gemeenten")
    print(f"  Not matched: {not_matched} gemeenten")


def create_separate_detail_file(opgesplitst_data: dict, output_path: str):
    """
    Maak een apart bestand met alle details (voor als GeoJSON te groot wordt).
    """
    # Converteer terug naar originele gemeentenamen voor leesbaarheid
    output_data = {
        'boekjaar': 2024,
        'type_rapport': 'Jaarrekening',
        'gemeenten': {}
    }
    
    for normalized_name, data in opgesplitst_data.items():
        # Gebruik title case voor weergave
        display_name = normalized_name.title()
        output_data['gemeenten'][display_name] = data
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Detail bestand opgeslagen: {output_path}")


def main():
    print("=" * 80)
    print("DATA KOPPELING: opgesplitst_grouped.json → municipalities.geojson")
    print("=" * 80)
    print()
    
    # Bestanden
    opgesplitst_file = "data/opgesplitst_grouped.json"
    geojson_file = "longread_output/municipalities.geojson"
    output_geojson = "longread_output/municipalities_enriched.geojson"
    output_details = "longread_output/municipality_details_2024.json"
    
    # Laad opgesplitste data
    print("Laden van opgesplitst_grouped.json...")
    opgesplitst_data = load_opgesplitst_data(opgesplitst_file)
    print(f"  → {len(opgesplitst_data)} gemeenten gevonden")
    
    # Statistieken
    total_rekeningen = sum(len(d['rekeningen']) for d in opgesplitst_data.values())
    avg_rekeningen = total_rekeningen / len(opgesplitst_data)
    print(f"  → {total_rekeningen} totale rekeningen")
    print(f"  → {avg_rekeningen:.1f} rekeningen per gemeente (gemiddeld)")
    print()
    
    # Verrijk GeoJSON
    print("Verrijken van GeoJSON met details...")
    enrich_geojson(geojson_file, opgesplitst_data, output_geojson)
    print()
    
    # Maak apart detail bestand
    print("Maken van apart detail bestand...")
    create_separate_detail_file(opgesplitst_data, output_details)
    print()
    
    print("=" * 80)
    print("✓ KOPPELING VOLTOOID")
    print("=" * 80)
    print()
    print("Bestanden aangemaakt:")
    print(f"  1. {output_geojson}")
    print(f"     → GeoJSON met top 10 rekeningen per gemeente")
    print(f"  2. {output_details}")
    print(f"     → Volledig detail bestand met alle rekeningen")
    print()
    print("Let op: Er zijn systematische verschillen tussen detail som en totaal.")
    print("Zie scripts/verification_report.json voor details.")


if __name__ == "__main__":
    main()
