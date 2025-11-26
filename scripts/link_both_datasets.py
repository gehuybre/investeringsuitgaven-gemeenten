#!/usr/bin/env python3
"""
Script om zowel detail (uitgavenposten) als beleidsdomein data te koppelen aan geojson.
Vervangt/update municipalities_enriched.geojson met beide datasets.
"""

import json


def normalize_municipality_name(name: str) -> str:
    """Normaliseer gemeentenaam voor matching."""
    name = name.strip()
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name.lower()


def load_beleidsdomein_data(filepath: str) -> dict:
    """Laad beleidsdomein_2024_processed.json."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_detail_data(filepath: str) -> dict:
    """Laad detail_alle_2024_processed.json en converteer naar dict per gemeente."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {}
    if 'gemeenten' in data:
        for gemeente, info in data['gemeenten'].items():
            normalized = normalize_municipality_name(gemeente)
            result[normalized] = info
    
    return result


def enrich_geojson_with_both(geojson_path: str, detail_data: dict, beleidsdomein_data: dict, output_path: str):
    """Voeg zowel detail als beleidsdomein data toe aan GeoJSON."""
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    matched_detail = 0
    matched_beleidsdomein = 0
    total_features = len(geojson['features'])
    
    for feature in geojson['features']:
        municipality = feature['properties']['municipality']
        normalized_name = normalize_municipality_name(municipality)
        totaal_2024 = feature['properties'].get('2024', 0)
        
        # Add detail data (uitgavenposten)
        if normalized_name in detail_data:
            gemeente_detail = detail_data[normalized_name]
            totaal_details = sum(r['bedrag'] for r in gemeente_detail.get('rekeningen', []))
            
            feature['properties']['detail_2024'] = {
                'totaal_details': round(totaal_details, 2),
                'aantal_rekeningen': len(gemeente_detail.get('rekeningen', [])),
                'verschil_met_totaal': round(totaal_details - totaal_2024, 2),
                'top_rekeningen': [
                    {
                        'code': r['code'],
                        'naam': r['naam'],
                        'bedrag': r['bedrag']
                    }
                    for r in sorted(gemeente_detail.get('rekeningen', []), 
                                   key=lambda x: abs(x['bedrag']), 
                                   reverse=True)[:10]
                ]
            }
            matched_detail += 1
        else:
            feature['properties']['detail_2024'] = None
        
        # Add beleidsdomein data
        if normalized_name in beleidsdomein_data:
            gemeente_beleidsdomein = beleidsdomein_data[normalized_name]
            totaal_beleidsdomein = gemeente_beleidsdomein.get('totaal', 0)
            
            feature['properties']['beleidsdomein_2024'] = {
                'totaal_beleidsdomein': round(totaal_beleidsdomein, 2),
                'aantal_beleidsvelden': gemeente_beleidsdomein.get('aantal_beleidsvelden', 0),
                'verschil_met_totaal': round(totaal_beleidsdomein - totaal_2024, 2),
                'top_beleidsvelden': [
                    {
                        'code': b['code'],
                        'naam': b['naam'],
                        'volledig': b['volledig'],
                        'bedrag': b['bedrag']
                    }
                    for b in gemeente_beleidsdomein.get('beleidsvelden', [])[:10]
                ]
            }
            matched_beleidsdomein += 1
        else:
            feature['properties']['beleidsdomein_2024'] = None
    
    # Save enriched GeoJSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Verrijkte GeoJSON opgeslagen: {output_path}")
    print(f"  Totaal gemeenten: {total_features}")
    print(f"  Matched detail (uitgavenposten): {matched_detail}")
    print(f"  Matched beleidsdomein: {matched_beleidsdomein}")


def analyze_discrepancies(geojson_path: str):
    """Analyseer de afwijkingen tussen de drie datasets."""
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    print("\n" + "=" * 100)
    print("AFWIJKINGEN ANALYSE")
    print("=" * 100)
    
    large_discrepancies = []
    
    for feature in geojson['features']:
        props = feature['properties']
        municipality = props['municipality']
        totaal = props.get('2024', 0)
        
        detail_2024 = props.get('detail_2024')
        beleidsdomein_2024 = props.get('beleidsdomein_2024')
        
        if detail_2024 and beleidsdomein_2024:
            diff_detail = detail_2024.get('verschil_met_totaal', 0)
            diff_beleidsdomein = beleidsdomein_2024.get('verschil_met_totaal', 0)
            diff_between = beleidsdomein_2024['totaal_beleidsdomein'] - detail_2024['totaal_details']
            
            # Check for large discrepancies (> 10 euro)
            if abs(diff_between) > 10:
                large_discrepancies.append({
                    'municipality': municipality,
                    'totaal': totaal,
                    'detail': detail_2024['totaal_details'],
                    'beleidsdomein': beleidsdomein_2024['totaal_beleidsdomein'],
                    'diff_detail_totaal': diff_detail,
                    'diff_beleidsdomein_totaal': diff_beleidsdomein,
                    'diff_between_methods': diff_between
                })
    
    if large_discrepancies:
        print(f"\nGemeenten met verschil > €10 tussen Detail en Beleidsdomein:")
        print("-" * 100)
        print(f"{'Gemeente':<25} {'Totaal':>10} {'Detail':>10} {'Beleidsdom':>12} {'Δ Methods':>12}")
        print("-" * 100)
        
        for item in sorted(large_discrepancies, key=lambda x: abs(x['diff_between_methods']), reverse=True)[:15]:
            print(f"{item['municipality']:<25} "
                  f"€{item['totaal']:>9.2f} "
                  f"€{item['detail']:>9.2f} "
                  f"€{item['beleidsdomein']:>11.2f} "
                  f"€{item['diff_between_methods']:>11.2f}")
    else:
        print("\n✓ Geen significante afwijkingen gevonden (alles < €10 verschil)")
    
    # Summary statistics
    print("\n" + "=" * 100)
    print("SAMENVATTING")
    print("=" * 100)
    
    all_diffs = []
    for feature in geojson['features']:
        props = feature['properties']
        detail = props.get('detail_2024')
        beleidsdomein = props.get('beleidsdomein_2024')
        
        if detail and beleidsdomein:
            diff = beleidsdomein['totaal_beleidsdomein'] - detail['totaal_details']
            all_diffs.append(abs(diff))
    
    if all_diffs:
        avg_diff = sum(all_diffs) / len(all_diffs)
        max_diff = max(all_diffs)
        within_1_euro = sum(1 for d in all_diffs if d < 1.0)
        within_10_euro = sum(1 for d in all_diffs if d < 10.0)
        
        print(f"Gemiddeld verschil: €{avg_diff:.2f}")
        print(f"Maximaal verschil: €{max_diff:.2f}")
        print(f"Binnen €1: {within_1_euro}/{len(all_diffs)} ({within_1_euro/len(all_diffs)*100:.1f}%)")
        print(f"Binnen €10: {within_10_euro}/{len(all_diffs)} ({within_10_euro/len(all_diffs)*100:.1f}%)")


def main():
    print("=" * 100)
    print("DATA KOPPELING: Detail + Beleidsdomein → GeoJSON")
    print("=" * 100)
    print()
    
    # File paths
    detail_json = 'data/detail_alle_2024_processed.json'
    beleidsdomein_json = 'data/beleidsdomein_2024_processed.json'
    geojson_input = 'longread_output/municipalities.geojson'
    geojson_output = 'longread_output/municipalities_enriched.geojson'
    
    # Load data
    print("Laden van data...")
    detail_data = load_detail_data(detail_json)
    beleidsdomein_data = load_beleidsdomein_data(beleidsdomein_json)
    print(f"  ✓ Detail data: {len(detail_data)} gemeenten")
    print(f"  ✓ Beleidsdomein data: {len(beleidsdomein_data)} gemeenten")
    print()
    
    # Enrich GeoJSON
    print("Verrijken van GeoJSON...")
    enrich_geojson_with_both(geojson_input, detail_data, beleidsdomein_data, geojson_output)
    
    # Analyze discrepancies
    analyze_discrepancies(geojson_output)
    
    print("\n" + "=" * 100)
    print("✓ KOPPELING VOLTOOID")
    print("=" * 100)


if __name__ == '__main__':
    main()
