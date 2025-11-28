#!/usr/bin/env python3
"""
Script om detail-alle-2024.csv te verwerken en te vergelijken met bestaande data.
Dit CSV heeft een andere structuur: gemeenten als rijen, rekeningen als kolommen.
"""

import json
import csv
from collections import defaultdict


def normalize_municipality_name(name: str) -> str:
    """Normaliseer gemeentenaam voor matching."""
    name = name.strip()
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name.lower()


def parse_csv_to_dict(csv_path: str) -> dict:
    """
    Parse het CSV bestand naar een dictionary structuur.
    
    Returns:
        Dict met genormaliseerde gemeentenamen als keys en dict met rekeningen als values
    """
    municipality_data = defaultdict(lambda: {
        'rekeningen': [],
        'totaal': 0.0
    })
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Read header first
        header = f.readline().strip().split(';')
        
        # First column is municipality name, rest are rekeningen
        rekening_codes = header[1:]  # Skip first column
        
        for line in f:
            parts = line.strip().split(';')
            if not parts or not parts[0]:
                continue
            
            gemeente_naam = parts[0]
            normalized_name = normalize_municipality_name(gemeente_naam)
            bedragen = parts[1:]  # Skip municipality name
            
            # Loop door alle bedragen met corresponderende rekening codes
            for i, bedrag_str in enumerate(bedragen):
                if i >= len(rekening_codes):
                    break
                
                rekening_code = rekening_codes[i]
                
                # Parse bedrag
                if bedrag_str and bedrag_str.strip():
                    try:
                        # Replace comma with dot for decimal
                        bedrag = float(bedrag_str.replace(',', '.'))
                        
                        if bedrag != 0:
                            # Extract code from column name (e.g., "REK221-7 Description" -> "REK221-7")
                            code = rekening_code.split()[0] if ' ' in rekening_code else rekening_code
                            
                            municipality_data[normalized_name]['rekeningen'].append({
                                'code': code,
                                'naam': rekening_code,
                                'bedrag': bedrag
                            })
                            
                            municipality_data[normalized_name]['totaal'] += bedrag
                    except ValueError:
                        continue
    
    # Round totals and sort rekeningen
    for gemeente in municipality_data.values():
        gemeente['totaal'] = round(gemeente['totaal'], 2)
        gemeente['rekeningen'].sort(key=lambda x: abs(x['bedrag']), reverse=True)
    
    return dict(municipality_data)


def load_geojson_data(filepath: str) -> dict:
    """Laad municipalities.geojson en extraheer 2024 waarden."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    municipality_2024 = {}
    
    for feature in data['features']:
        props = feature['properties']
        municipality = props['municipality']
        value_2024 = props.get('2024')
        
        if value_2024 is not None:
            normalized_name = normalize_municipality_name(municipality)
            municipality_2024[normalized_name] = float(value_2024)
    
    return municipality_2024


def compare_data(csv_data: dict, geojson_data: dict) -> list:
    """Vergelijk CSV data met GeoJSON data."""
    results = []
    
    all_municipalities = set(csv_data.keys()) | set(geojson_data.keys())
    
    for municipality in sorted(all_municipalities):
        csv_total = csv_data.get(municipality, {}).get('totaal', 0.0)
        geojson_value = geojson_data.get(municipality, None)
        
        if geojson_value is None:
            status = "MISSING_IN_GEOJSON"
            difference = None
            match = False
        else:
            difference = csv_total - geojson_value
            # Acceptable difference < 0.01
            match = abs(difference) < 0.01
            status = "MATCH" if match else "MISMATCH"
        
        results.append({
            'municipality': municipality,
            'csv_total': round(csv_total, 2),
            'geojson_2024': round(geojson_value, 2) if geojson_value is not None else None,
            'difference': round(difference, 2) if difference is not None else None,
            'status': status,
            'match': match,
            'num_rekeningen': len(csv_data.get(municipality, {}).get('rekeningen', []))
        })
    
    return results


def print_comparison_report(results: list) -> None:
    """Print vergelijkingsrapport."""
    matches = [r for r in results if r['status'] == 'MATCH']
    mismatches = [r for r in results if r['status'] == 'MISMATCH']
    missing = [r for r in results if r['status'] == 'MISSING_IN_GEOJSON']
    
    print("=" * 80)
    print("VERGELIJKING: detail-alle-2024.csv vs municipalities.geojson")
    print("=" * 80)
    print()
    
    print(f"Totaal aantal gemeenten: {len(results)}")
    print(f"✓ Matches (verschil < €0.01): {len(matches)}")
    print(f"✗ Mismatches: {len(mismatches)}")
    print(f"? Ontbreekt in GeoJSON: {len(missing)}")
    print()
    
    if len(matches) == len([r for r in results if r['status'] != 'MISSING_IN_GEOJSON']):
        print("=" * 80)
        print("🎉 PERFECT MATCH! 🎉")
        print("=" * 80)
        print()
        print("Alle gemeenten hebben nu een perfecte match tussen CSV en GeoJSON!")
        print("De tekorten zijn opgelost!")
        print()
    elif mismatches:
        print("=" * 80)
        print("MISMATCHES (top 20):")
        print("=" * 80)
        print()
        
        mismatches.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        for result in mismatches[:20]:
            print(f"Gemeente: {result['municipality'].title()}")
            print(f"  CSV totaal:   €{result['csv_total']:>12,.2f} ({result['num_rekeningen']} rek.)")
            print(f"  GeoJSON 2024: €{result['geojson_2024']:>12,.2f}")
            print(f"  Verschil:     €{result['difference']:>12,.2f}")
            print()


def create_enriched_data(csv_data: dict, output_path: str):
    """Maak verrijkte data structuur aan."""
    output = {
        'boekjaar': 2024,
        'type_rapport': 'Jaarrekening',
        'bron': 'detail-alle-2024.csv',
        'gemeenten': {}
    }
    
    for normalized_name, data in csv_data.items():
        display_name = normalized_name.title()
        output['gemeenten'][display_name] = data
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Verrijkte data opgeslagen: {output_path}")


def main():
    print("=" * 80)
    print("NIEUWE DATABRON VERWERKEN: detail-alle-2024.csv")
    print("=" * 80)
    print()
    
    csv_file = "data/detail-alle-2024.csv"
    geojson_file = "longread_output/municipalities.geojson"
    output_json = "data/detail_alle_2024_processed.json"
    comparison_report = "scripts/comparison_csv_vs_geojson.json"
    
    # Parse CSV
    print("Verwerken van CSV...")
    csv_data = parse_csv_to_dict(csv_file)
    print(f"  → {len(csv_data)} gemeenten gevonden")
    
    # Statistieken
    total_rekeningen = sum(len(d['rekeningen']) for d in csv_data.values())
    avg_rekeningen = total_rekeningen / len(csv_data) if csv_data else 0
    print(f"  → {total_rekeningen} totale rekeningen")
    print(f"  → {avg_rekeningen:.1f} rekeningen per gemeente (gemiddeld)")
    print()
    
    # Load GeoJSON voor vergelijking
    print("Laden van GeoJSON voor vergelijking...")
    geojson_data = load_geojson_data(geojson_file)
    print(f"  → {len(geojson_data)} gemeenten in GeoJSON")
    print()
    
    # Vergelijk
    print("Vergelijken van data...")
    results = compare_data(csv_data, geojson_data)
    print()
    
    # Print rapport
    print_comparison_report(results)
    
    # Bewaar verrijkte data
    print("Opslaan van verwerkte data...")
    create_enriched_data(csv_data, output_json)
    print()
    
    # Bewaar vergelijkingsrapport
    with open(comparison_report, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ Vergelijkingsrapport opgeslagen: {comparison_report}")
    print()


if __name__ == "__main__":
    main()
