#!/usr/bin/env python3
"""
Process beleidsdomein data to calculate totals per policy domain per year.
This aggregates investment data across all municipalities.
"""

import pandas as pd
import json
from pathlib import Path

def process_beleidsdomein_totals():
    """Process the beleidsdomein CSV and calculate totals per year per policy domain."""
    
    # Load the CSV
    csv_path = Path(__file__).parent.parent / 'data' / 'investeringsuitgave per beleidsdomein.csv'
    
    print(f"Loading {csv_path}...")
    
    # Read the header rows to understand structure
    # Row 0: Type rapport
    # Row 1: Boekjaar (years)
    # Row 2: BV_domein (main policy domains)
    # Row 3: BV_subdomein (policy subdomains)
    # Row 4: Grondgebied;Bestuur;Uitgave per inwoner;...
    
    # Read header rows
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = [f.readline().strip() for _ in range(5)]
    
    # Parse the year row (row 1)
    years_raw = lines[1].split(';')[2:]  # Skip first 2 columns
    
    # Parse the BV_subdomein row (row 3)
    subdomeinen_raw = lines[3].split(';')[2:]  # Skip first 2 columns
    
    # Create a mapping of column index to (year, subdomein)
    column_mapping = {}
    for idx, (year_str, subdomein_str) in enumerate(zip(years_raw, subdomeinen_raw)):
        try:
            year = int(year_str.strip())
            subdomein = subdomein_str.strip()
            if year and subdomein:
                column_mapping[idx] = {
                    'year': year,
                    'subdomein': subdomein
                }
        except (ValueError, AttributeError):
            # Skip invalid entries
            pass
    
    print(f"Found {len(column_mapping)} data columns spanning years {min(m['year'] for m in column_mapping.values())} to {max(m['year'] for m in column_mapping.values())}")
    
    # Now process the actual data
    data_df = pd.read_csv(csv_path, sep=';', encoding='utf-8', skiprows=4)
    
    # Initialize result structure: {year: {subdomein: total}}
    totals = {}
    
    # Iterate through all data rows
    for _, row in data_df.iterrows():
        municipality = row.iloc[0]  # Grondgebied
        
        # Skip if this is a total/aggregate row (we want individual municipalities only)
        if pd.isna(municipality) or municipality in ['Total', 'Totaal', '']:
            continue
            
        # Process each column with investment data
        for col_idx, mapping in column_mapping.items():
            # col_idx is relative to data columns (after Grondgebied, Bestuur)
            # In the dataframe, add 2 to get the actual column index
            actual_col_idx = col_idx + 2
            if actual_col_idx < len(row):
                value = row.iloc[actual_col_idx]
                
                # Try to convert to float
                try:
                    if pd.notna(value) and value != '':
                        # Replace comma with dot for decimal separator
                        value_str = str(value).replace(',', '.')
                        amount = float(value_str)
                        
                        year = mapping['year']
                        subdomein = mapping['subdomein']
                        
                        # Initialize year if needed
                        if year not in totals:
                            totals[year] = {}
                        
                        # Initialize subdomein if needed
                        if subdomein not in totals[year]:
                            totals[year][subdomein] = 0.0
                        
                        # Add to total
                        totals[year][subdomein] += amount
                        
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    pass
    
    # Convert to a more useful structure: {subdomein: {year: total}}
    by_subdomein = {}
    for year, subdomeinen in totals.items():
        for subdomein, total in subdomeinen.items():
            if subdomein not in by_subdomein:
                by_subdomein[subdomein] = {}
            by_subdomein[subdomein][year] = round(total, 2)
    
    # Sort years in each subdomein
    for subdomein in by_subdomein:
        by_subdomein[subdomein] = dict(sorted(by_subdomein[subdomein].items()))
    
    # Save to JSON
    output_path = Path(__file__).parent.parent / 'longread_output' / 'beleidsdomein_totals.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(by_subdomein, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved totals to {output_path}")
    print(f"   Found {len(by_subdomein)} policy subdomains")
    print(f"   Years covered: {sorted(set(year for subdomeinen in by_subdomein.values() for year in subdomeinen.keys()))}")
    
    # Print a sample
    sample_subdomein = list(by_subdomein.keys())[0]
    print(f"\n   Sample - {sample_subdomein}:")
    for year, total in list(by_subdomein[sample_subdomein].items())[:5]:
        print(f"      {year}: €{total:,.2f}")

if __name__ == '__main__':
    process_beleidsdomein_totals()
