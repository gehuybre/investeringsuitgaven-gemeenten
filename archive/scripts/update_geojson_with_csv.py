#!/usr/bin/env python3
"""
Update municipalities_enriched.geojson met de nieuwe CSV data.
"""

import json


def normalize_municipality_name(name: str) -> str:
    """Normaliseer gemeentenaam voor matching."""
    name = name.strip()
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name.lower()


def main():
    print("=" * 80)
    print("UPDATE GEOJSON MET NIEUWE CSV DATA")
    print("=" * 80)
    print()
    
    # Load processed CSV data
    print("Laden van verwerkte CSV data...")
    with open('data/detail_alle_2024_processed.json', 'r', encoding='utf-8') as f:
        csv_data = json.load(f)
    
    csv_gemeenten = csv_data['gemeenten']
    print(f"  → {len(csv_gemeenten)} gemeenten in CSV")
    print()
    
    # Load current GeoJSON
    print("Laden van huidige GeoJSON...")
    with open('longread_output/municipalities_enriched.geojson', 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    features = geojson['features']
    print(f"  → {len(features)} gemeenten in GeoJSON")
    print()
    
    # Update features
    print("Updaten van features met nieuwe data...")
    updated = 0
    not_found = 0
    
    for feature in features:
        municipality = feature['properties']['municipality']
        normalized = normalize_municipality_name(municipality)
        
        # Find in CSV data (case insensitive)
        csv_match = None
        for csv_name, csv_info in csv_gemeenten.items():
            if normalize_municipality_name(csv_name) == normalized:
                csv_match = csv_info
                break
        
        if csv_match:
            # Update detail_2024
            total_2024 = feature['properties']['2024']
            
            feature['properties']['detail_2024'] = {
                'totaal_details': csv_match['totaal'],
                'aantal_rekeningen': len(csv_match['rekeningen']),
                'boekjaar': 2024,
                'type_rapport': 'Jaarrekening',
                'bron': 'detail-alle-2024.csv',
                'verschil_met_totaal': round(csv_match['totaal'] - total_2024, 2),
                'top_rekeningen': [
                    {
                        'code': r['code'],
                        'naam': r['naam'],
                        'bedrag': r['bedrag']
                    }
                    for r in csv_match['rekeningen'][:10]
                ]
            }
            updated += 1
        else:
            not_found += 1
            print(f"  ⚠ Geen match gevonden voor: {municipality}")
    
    print(f"  → {updated} gemeenten bijgewerkt")
    print(f"  → {not_found} gemeenten niet gevonden in CSV")
    print()
    
    # Save updated GeoJSON
    print("Opslaan van bijgewerkte GeoJSON...")
    with open('longread_output/municipalities_enriched.geojson', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print("✓ municipalities_enriched.geojson bijgewerkt")
    print()
    
    # Statistics
    print("=" * 80)
    print("STATISTIEKEN")
    print("=" * 80)
    
    matches = 0
    small_diff = 0
    large_diff = 0
    
    for feature in features:
        if feature['properties'].get('detail_2024'):
            diff = abs(feature['properties']['detail_2024']['verschil_met_totaal'])
            if diff < 0.01:
                matches += 1
            elif diff < 1.0:
                small_diff += 1
            else:
                large_diff += 1
    
    print(f"Perfecte matches (< €0.01):       {matches:>3} ({matches/len(features)*100:.1f}%)")
    print(f"Kleine verschillen (€0.01-€1.00): {small_diff:>3} ({small_diff/len(features)*100:.1f}%)")
    print(f"Grote verschillen (> €1.00):      {large_diff:>3} ({large_diff/len(features)*100:.1f}%)")
    print()
    print("=" * 80)
    print("✓ UPDATE VOLTOOID")
    print("=" * 80)


if __name__ == "__main__":
    main()
