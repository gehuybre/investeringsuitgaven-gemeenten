#!/usr/bin/env python3
"""
Script om investeringsuitgave per beleidsdomein 2024.csv te verwerken.
Dit CSV heeft dezelfde structuur als detail-alle-2024.csv maar met beleidsvelden i.p.v. rekeningen.
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
        Dict met genormaliseerde gemeentenamen als keys en dict met beleidsvelden als values
    """
    municipality_data = defaultdict(lambda: {
        'beleidsvelden': [],
        'totaal': 0.0
    })
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Read first line as header
        header_line = f.readline().strip()
        headers = header_line.split(';')
        
        # Get field names (exclude Grondgebied and Bestuur)
        beleidsveld_columns = headers[2:]  # Skip first two columns
        
        for line in f:
            parts = line.strip().split(';')
            if not parts or len(parts) < 2:
                continue
            
            gemeente_naam = parts[0].strip()
            bestuur = parts[1].strip()
            
            # Skip empty rows, but KEEP "Total" rows as they contain the aggregated data
            if not gemeente_naam or not bestuur:
                continue
            
            # Only process "Total" rows which have the aggregated municipal data
            if bestuur != 'Total':
                continue
            
            normalized_name = normalize_municipality_name(gemeente_naam)
            bedragen = parts[2:]  # Skip gemeente and bestuur columns
            
            # Process each beleidsveld column
            for i, beleidsveld_naam in enumerate(beleidsveld_columns):
                if i >= len(bedragen):
                    break
                    
                bedrag_str = bedragen[i].strip()
                
                if bedrag_str:
                    try:
                        # Replace comma with dot for decimal
                        bedrag = float(bedrag_str.replace(',', '.'))
                        
                        if bedrag != 0:
                            # Extract code and description from column name
                            # e.g., "011 Algemene diensten" -> code: "011", naam: "Algemene diensten"
                            parts = beleidsveld_naam.split(maxsplit=1)
                            if len(parts) == 2:
                                code = parts[0]
                                beschrijving = parts[1]
                            else:
                                code = beleidsveld_naam
                                beschrijving = beleidsveld_naam
                            
                            municipality_data[normalized_name]['beleidsvelden'].append({
                                'code': code,
                                'naam': beschrijving,
                                'volledig': beleidsveld_naam,
                                'bedrag': bedrag
                            })
                            
                            municipality_data[normalized_name]['totaal'] += bedrag
                    except ValueError:
                        continue
    
    # Round totals and sort beleidsvelden by absolute amount
    for gemeente in municipality_data.values():
        gemeente['totaal'] = round(gemeente['totaal'], 2)
        gemeente['beleidsvelden'].sort(key=lambda x: abs(x['bedrag']), reverse=True)
        gemeente['aantal_beleidsvelden'] = len(gemeente['beleidsvelden'])
    
    return dict(municipality_data)


def load_existing_detail_data(filepath: str) -> dict:
    """Laad de bestaande detail data (uitgavenposten) voor vergelijking."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Convert to flat structure: gemeente -> totaal_details
            result = {}
            if 'gemeenten' in data:
                for gemeente, info in data['gemeenten'].items():
                    normalized = normalize_municipality_name(gemeente)
                    totaal = sum(rek['bedrag'] for rek in info.get('rekeningen', []))
                    result[normalized] = {
                        'totaal_details': round(totaal, 2),
                        'aantal_rekeningen': len(info.get('rekeningen', []))
                    }
            return result
    except FileNotFoundError:
        return {}


def load_geojson_data(filepath: str) -> dict:
    """Laad municipalities_enriched.geojson en extraheer 2024 waarden."""
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


def compare_all_data(beleidsdomein_data: dict, detail_data: dict, geojson_data: dict) -> list:
    """Vergelijk alle drie de datasets."""
    results = []
    
    all_municipalities = set(beleidsdomein_data.keys()) | set(detail_data.keys()) | set(geojson_data.keys())
    
    for municipality in sorted(all_municipalities):
        beleidsdomein_total = beleidsdomein_data.get(municipality, {}).get('totaal', 0.0)
        detail_total = detail_data.get(municipality, {}).get('totaal_details', 0.0)
        geojson_value = geojson_data.get(municipality, 0.0)
        
        # Calculate differences
        diff_beleidsdomein_geojson = beleidsdomein_total - geojson_value if geojson_value else None
        diff_detail_geojson = detail_total - geojson_value if geojson_value else None
        diff_beleidsdomein_detail = beleidsdomein_total - detail_total if detail_total else None
        
        # Determine match status (acceptable difference < 0.01)
        match_beleidsdomein = abs(diff_beleidsdomein_geojson) < 0.01 if diff_beleidsdomein_geojson is not None else False
        match_detail = abs(diff_detail_geojson) < 0.01 if diff_detail_geojson is not None else False
        match_both = abs(diff_beleidsdomein_detail) < 0.01 if diff_beleidsdomein_detail is not None else False
        
        results.append({
            'municipality': municipality,
            'geojson_2024': round(geojson_value, 2),
            'beleidsdomein_total': round(beleidsdomein_total, 2),
            'detail_total': round(detail_total, 2),
            'diff_beleidsdomein_geojson': round(diff_beleidsdomein_geojson, 2) if diff_beleidsdomein_geojson is not None else None,
            'diff_detail_geojson': round(diff_detail_geojson, 2) if diff_detail_geojson is not None else None,
            'diff_beleidsdomein_detail': round(diff_beleidsdomein_detail, 2) if diff_beleidsdomein_detail is not None else None,
            'match_beleidsdomein': match_beleidsdomein,
            'match_detail': match_detail,
            'match_both_details': match_both,
            'num_beleidsvelden': len(beleidsdomein_data.get(municipality, {}).get('beleidsvelden', [])),
            'num_rekeningen': detail_data.get(municipality, {}).get('aantal_rekeningen', 0)
        })
    
    return results


def print_comparison_report(results: list) -> None:
    """Print vergelijkingsrapport."""
    print("=" * 100)
    print("VERGELIJKING: Beleidsdomein vs Detail (Uitgavenposten) vs GeoJSON (Totaal)")
    print("=" * 100)
    print()
    
    print(f"Totaal aantal gemeenten: {len(results)}")
    print()
    
    # Statistics
    match_beleidsdomein = sum(1 for r in results if r['match_beleidsdomein'])
    match_detail = sum(1 for r in results if r['match_detail'])
    match_both = sum(1 for r in results if r['match_both_details'])
    
    print(f"✓ Beleidsdomein matcht GeoJSON totaal: {match_beleidsdomein}/{len(results)}")
    print(f"✓ Detail (uitgavenposten) matcht GeoJSON totaal: {match_detail}/{len(results)}")
    print(f"✓ Beleidsdomein matcht Detail: {match_both}/{len(results)}")
    print()
    
    # Show mismatches
    large_mismatches = [r for r in results if 
                       (r['diff_beleidsdomein_detail'] is not None and 
                        abs(r['diff_beleidsdomein_detail']) > 1.0)]
    
    if large_mismatches:
        print(f"Gemeenten met verschil > €1.00 tussen Beleidsdomein en Detail:")
        print("-" * 100)
        print(f"{'Gemeente':<30} {'GeoJSON':>12} {'Beleidsdom.':>12} {'Detail':>12} {'Δ Bel-Det':>12}")
        print("-" * 100)
        
        for r in sorted(large_mismatches, key=lambda x: abs(x['diff_beleidsdomein_detail']), reverse=True)[:20]:
            print(f"{r['municipality']:<30} "
                  f"€{r['geojson_2024']:>11.2f} "
                  f"€{r['beleidsdomein_total']:>11.2f} "
                  f"€{r['detail_total']:>11.2f} "
                  f"€{r['diff_beleidsdomein_detail']:>11.2f}")
        print()


def save_processed_data(data: dict, output_path: str) -> None:
    """Sla verwerkte data op als JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Data opgeslagen naar {output_path}")


def save_comparison_report(results: list, output_path: str) -> None:
    """Sla vergelijkingsrapport op als JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"✓ Vergelijkingsrapport opgeslagen naar {output_path}")


def main():
    # File paths
    csv_path = 'data/investeringsuitgave per beleidsdomein 2024.csv'
    detail_json_path = 'data/detail_alle_2024_processed.json'
    geojson_path = 'longread_output/municipalities_enriched.geojson'
    output_json = 'data/beleidsdomein_2024_processed.json'
    comparison_output = 'scripts/comparison_all_datasets.json'
    
    print("Verwerken van beleidsdomein CSV...")
    beleidsdomein_data = parse_csv_to_dict(csv_path)
    print(f"✓ {len(beleidsdomein_data)} gemeenten verwerkt")
    print()
    
    # Load other datasets for comparison
    print("Laden van andere datasets...")
    detail_data = load_existing_detail_data(detail_json_path)
    geojson_data = load_geojson_data(geojson_path)
    print(f"✓ Detail data: {len(detail_data)} gemeenten")
    print(f"✓ GeoJSON data: {len(geojson_data)} gemeenten")
    print()
    
    # Compare all datasets
    results = compare_all_data(beleidsdomein_data, detail_data, geojson_data)
    print_comparison_report(results)
    
    # Save processed data
    save_processed_data(beleidsdomein_data, output_json)
    save_comparison_report(results, comparison_output)
    print()
    print("Klaar!")


if __name__ == '__main__':
    main()
