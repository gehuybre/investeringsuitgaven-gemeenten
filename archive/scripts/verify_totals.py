#!/usr/bin/env python3
"""
Script om te verifiëren of de som van details in opgesplitst_grouped.json
overeenkomt met het totaal in municipalities.geojson voor 2024.
"""

import json
from collections import defaultdict
from typing import Dict, List, Tuple


def normalize_municipality_name(name: str) -> str:
    """
    Normaliseer gemeentenaam voor matching.
    Verwijdert 'Gemeente en OCMW' prefix en maakt lowercase.
    """
    name = name.strip()
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name.lower()


def load_opgesplitst_data(filepath: str) -> Dict[str, float]:
    """
    Laad opgesplitst_grouped.json en som alle details per gemeente.
    
    Returns:
        Dict met genormaliseerde gemeentenamen als keys en totalen als values
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Som alle bedragen per gemeente over alle rekeningen
    municipality_totals = defaultdict(float)
    
    for rekening_code, rekening_data in data['rekeningen'].items():
        gemeenten = rekening_data.get('gemeenten', {})
        for gemeente_naam, bedrag in gemeenten.items():
            normalized_name = normalize_municipality_name(gemeente_naam)
            municipality_totals[normalized_name] += bedrag
    
    return dict(municipality_totals)


def load_geojson_data(filepath: str) -> Dict[str, float]:
    """
    Laad municipalities.geojson en extraheer 2024 waarden.
    
    Returns:
        Dict met genormaliseerde gemeentenamen als keys en 2024 waarden als values
    """
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


def compare_totals(opgesplitst_totals: Dict[str, float], 
                   geojson_totals: Dict[str, float]) -> List[Dict]:
    """
    Vergelijk de totalen tussen beide bestanden.
    
    Returns:
        List van dict met verschillen per gemeente
    """
    results = []
    
    # Alle unieke gemeentenamen
    all_municipalities = set(opgesplitst_totals.keys()) | set(geojson_totals.keys())
    
    for municipality in sorted(all_municipalities):
        detail_sum = opgesplitst_totals.get(municipality, 0.0)
        geojson_value = geojson_totals.get(municipality, None)
        
        if geojson_value is None:
            status = "MISSING_IN_GEOJSON"
            difference = None
            match = False
        else:
            difference = detail_sum - geojson_value
            # Afrondingsverschillen tot 0.01 zijn acceptabel
            match = abs(difference) < 0.01
            status = "MATCH" if match else "MISMATCH"
        
        results.append({
            'municipality': municipality,
            'detail_sum': round(detail_sum, 2),
            'geojson_2024': round(geojson_value, 2) if geojson_value is not None else None,
            'difference': round(difference, 2) if difference is not None else None,
            'status': status,
            'match': match
        })
    
    return results


def print_report(results: List[Dict]) -> None:
    """Print een leesbaar rapport van de vergelijking."""
    
    matches = [r for r in results if r['status'] == 'MATCH']
    mismatches = [r for r in results if r['status'] == 'MISMATCH']
    missing = [r for r in results if r['status'] == 'MISSING_IN_GEOJSON']
    
    print("=" * 80)
    print("VERIFICATIE RAPPORT: opgesplitst_grouped.json vs municipalities.geojson")
    print("=" * 80)
    print()
    
    print(f"Totaal aantal gemeenten: {len(results)}")
    print(f"✓ Matches (verschil < €0.01): {len(matches)}")
    print(f"✗ Mismatches: {len(mismatches)}")
    print(f"? Ontbreekt in GeoJSON: {len(missing)}")
    print()
    
    if mismatches:
        print("=" * 80)
        print("MISMATCHES (details som ≠ GeoJSON totaal):")
        print("=" * 80)
        print()
        
        # Sorteer op grootte van verschil
        mismatches.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        for result in mismatches:
            print(f"Gemeente: {result['municipality'].title()}")
            print(f"  Details som:  €{result['detail_sum']:>12,.2f}")
            print(f"  GeoJSON 2024: €{result['geojson_2024']:>12,.2f}")
            print(f"  Verschil:     €{result['difference']:>12,.2f}")
            print()
    
    if missing:
        print("=" * 80)
        print("ONTBREKEND IN GEOJSON:")
        print("=" * 80)
        print()
        
        for result in missing:
            print(f"Gemeente: {result['municipality'].title()}")
            print(f"  Details som: €{result['detail_sum']:>12,.2f}")
            print()
    
    if not mismatches and not missing:
        print("=" * 80)
        print("✓ ALLE CONTROLES GESLAAGD!")
        print("=" * 80)
        print()
        print("Alle gemeenten hebben details die correct optellen tot het GeoJSON totaal.")
        print()


def save_detailed_report(results: List[Dict], output_path: str) -> None:
    """Bewaar gedetailleerd rapport als JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Gedetailleerd rapport opgeslagen: {output_path}")


def main():
    # Bestanden
    opgesplitst_file = "data/opgesplitst_grouped.json"
    geojson_file = "longread_output/municipalities.geojson"
    report_file = "scripts/verification_report.json"
    
    print("Laden van opgesplitst_grouped.json...")
    opgesplitst_totals = load_opgesplitst_data(opgesplitst_file)
    print(f"  → {len(opgesplitst_totals)} gemeenten gevonden")
    
    print("Laden van municipalities.geojson...")
    geojson_totals = load_geojson_data(geojson_file)
    print(f"  → {len(geojson_totals)} gemeenten gevonden")
    print()
    
    print("Vergelijken van totalen...")
    results = compare_totals(opgesplitst_totals, geojson_totals)
    print()
    
    # Print rapport
    print_report(results)
    
    # Bewaar gedetailleerd rapport
    save_detailed_report(results, report_file)


if __name__ == "__main__":
    main()
