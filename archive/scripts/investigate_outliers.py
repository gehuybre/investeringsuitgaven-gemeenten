#!/usr/bin/env python3
"""
Onderzoek de outliers: Kaprijke en Antwerpen.
"""

import json
import csv


def normalize_municipality_name(name: str) -> str:
    """Normaliseer gemeentenaam voor matching."""
    name = name.strip()
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name.lower()


def investigate_municipality(municipality_name: str):
    """Onderzoek een specifieke gemeente."""
    print(f"\n{'=' * 80}")
    print(f"ONDERZOEK: {municipality_name.upper()}")
    print(f"{'=' * 80}\n")
    
    normalized = normalize_municipality_name(municipality_name)
    
    # 1. Check GeoJSON
    print("1. GEOJSON DATA")
    print("-" * 80)
    with open('longread_output/municipalities_enriched.geojson', 'r', encoding='utf-8') as f:
        geojson = json.load(f)
    
    geojson_feature = None
    for feature in geojson['features']:
        if normalize_municipality_name(feature['properties']['municipality']) == normalized:
            geojson_feature = feature
            break
    
    if geojson_feature:
        props = geojson_feature['properties']
        print(f"Gemeente: {props['municipality']}")
        print(f"Totaal 2024: €{props['2024']:,.2f}")
        if props.get('detail_2024'):
            detail = props['detail_2024']
            print(f"Totaal details (CSV): €{detail['totaal_details']:,.2f}")
            print(f"Verschil: €{detail['verschil_met_totaal']:,.2f}")
            print(f"Aantal rekeningen: {detail['aantal_rekeningen']}")
    else:
        print(f"⚠ Niet gevonden in GeoJSON")
    
    # 2. Check processed CSV data
    print(f"\n2. VERWERKTE CSV DATA")
    print("-" * 80)
    with open('data/detail_alle_2024_processed.json', 'r', encoding='utf-8') as f:
        csv_data = json.load(f)
    
    csv_match = None
    for csv_name, csv_info in csv_data['gemeenten'].items():
        if normalize_municipality_name(csv_name) == normalized:
            csv_match = csv_info
            print(f"Gemeente: {csv_name}")
            print(f"Totaal: €{csv_info['totaal']:,.2f}")
            print(f"Aantal rekeningen: {len(csv_info['rekeningen'])}")
            print(f"\nTop 10 rekeningen:")
            for i, rek in enumerate(csv_info['rekeningen'][:10], 1):
                print(f"  {i:2d}. {rek['code']}: €{rek['bedrag']:>12,.2f} - {rek['naam']}")
            break
    
    if not csv_match:
        print(f"⚠ Niet gevonden in verwerkte CSV data")
    
    # 3. Check raw CSV
    print(f"\n3. RUWE CSV DATA (detail-alle-2024.csv)")
    print("-" * 80)
    with open('data/detail-alle-2024.csv', 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        headers = first_line.split(';')  # CSV uses semicolon
        
        print(f"Aantal kolommen: {len(headers)}")
        print(f"Eerste kolom: '{headers[0]}'")
        print(f"Aantal rekening-kolommen: {len(headers) - 1}")
        
        # Find the row
        f.seek(0)
        reader = csv.reader(f, delimiter=';')  # Use semicolon
        header_row = next(reader)
        
        found = False
        for row in reader:
            if row and normalize_municipality_name(row[0]) == normalized:
                found = True
                print(f"\nGemeente in CSV: {row[0]}")
                
                # Count non-empty values
                non_empty = 0
                total = 0.0
                non_zero_values = []
                
                for i in range(1, len(row)):
                    value = row[i].strip()
                    if value and value != '0' and value != '0.00' and value != '0,00':
                        try:
                            # Replace comma with dot for float parsing
                            amount = float(value.replace(',', '.'))
                            if amount != 0:
                                non_empty += 1
                                total += amount
                                if len(non_zero_values) < 10:  # Keep top 10
                                    non_zero_values.append((header_row[i], amount))
                        except ValueError:
                            pass
                
                print(f"Aantal niet-lege rekeningen: {non_empty}")
                print(f"Totaal berekend: €{total:,.2f}")
                
                print(f"\nTop 10 niet-nul waarden uit ruwe CSV:")
                # Sort by amount descending
                non_zero_values.sort(key=lambda x: x[1], reverse=True)
                for i, (code, amount) in enumerate(non_zero_values[:10], 1):
                    print(f"  {i:2d}. {code}: €{amount:>12,.2f}")
                
                break
        
        if not found:
            print(f"⚠ Niet gevonden in ruwe CSV")
    
    # 4. Check original opgesplitst_grouped.json
    print(f"\n4. ORIGINELE OPGESPLITST_GROUPED.JSON")
    print("-" * 80)
    try:
        with open('data/opgesplitst_grouped.json', 'r', encoding='utf-8') as f:
            opgesplitst = json.load(f)
        
        total_from_opgesplitst = 0.0
        count = 0
        top_accounts = []
        
        # Skip metadata fields
        rekeningen = opgesplitst.get('rekeningen', opgesplitst)
        
        for account_code, account_data in rekeningen.items():
            if not isinstance(account_data, dict):
                continue
            gemeenten = account_data.get('gemeenten', {})
            for gem_name, gem_data in gemeenten.items():
                if normalize_municipality_name(gem_name) == normalized:
                    # gem_data is directly a float/number, not a dict
                    bedrag = gem_data if isinstance(gem_data, (int, float)) else gem_data.get('bedrag', 0)
                    if bedrag != 0:
                        total_from_opgesplitst += bedrag
                        count += 1
                        naam = account_data.get('alg_rekening', account_code)
                        top_accounts.append((account_code, bedrag, naam))
        
        print(f"Totaal uit opgesplitst_grouped.json: €{total_from_opgesplitst:,.2f}")
        print(f"Aantal rekeningen: {count}")
        
        if top_accounts:
            print(f"\nTop 10 rekeningen:")
            top_accounts.sort(key=lambda x: x[1], reverse=True)
            for i, (code, bedrag, naam) in enumerate(top_accounts[:10], 1):
                print(f"  {i:2d}. {code}: €{bedrag:>12,.2f} - {naam}")
    
    except FileNotFoundError:
        print("⚠ opgesplitst_grouped.json niet gevonden")
    
    # 5. Summary comparison
    print(f"\n5. SAMENVATTING")
    print("-" * 80)
    if geojson_feature and csv_match:
        geojson_total = geojson_feature['properties']['2024']
        csv_total = csv_match['totaal']
        difference = csv_total - geojson_total
        
        print(f"GeoJSON totaal:           €{geojson_total:>15,.2f}")
        print(f"CSV totaal:               €{csv_total:>15,.2f}")
        print(f"Verschil (CSV - GeoJSON): €{difference:>15,.2f}")
        print(f"Percentage:               {(difference/geojson_total*100):>15.2f}%")


def main():
    print("=" * 80)
    print("OUTLIER INVESTIGATIE")
    print("=" * 80)
    
    # Investigate both outliers
    investigate_municipality("Kaprijke")
    investigate_municipality("Antwerpen")
    
    print(f"\n{'=' * 80}")
    print("INVESTIGATIE VOLTOOID")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
