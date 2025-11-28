#!/usr/bin/env python3
"""
Script om detail-alle-jaren.xlsx te verwerken en per gemeente de beleidsdomein data 
voor alle jaren (2014-2024) te extraheren.

Output: Een JSON bestand met de structuur:
{
  "Aalst": {
    "02 Zich verplaatsen en mobiliteit": {
      "2014": 123.45,
      "2015": 234.56,
      ...
    },
    "061 Gebiedsontwikkeling": {
      ...
    }
  },
  "Aarschot": {
    ...
  }
}
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict


def normalize_municipality_name(name: str) -> str:
    """Normaliseer gemeentenaam voor matching."""
    name = str(name).strip()
    # Remove "Gemeente en OCMW " prefix if present
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name


def main():
    # Paths
    input_file = Path("../data/detail-alle-jaren.xlsx")
    output_file = Path("../longread_output/beleidsdomein_per_gemeente.json")
    
    print(f"Reading Excel file: {input_file}")
    
    # Read Excel file
    # The structure should be similar to the CSV files we've seen
    df = pd.read_excel(input_file, sheet_name=0, header=None, skiprows=4)
    
    print(f"DataFrame shape: {df.shape}")
    print(f"First few rows:")
    print(df.head())
    
    # Parse header rows (first 4 rows)
    excel_df = pd.read_excel(input_file, sheet_name=0, nrows=4, header=None)
    print("\nHeader rows:")
    print(excel_df)
    
    # Read with proper header
    df = pd.read_excel(input_file, sheet_name=0, header=3)
    
    print(f"\nColumns: {df.columns.tolist()[:10]}")
    print(f"Total columns: {len(df.columns)}")
    
    # The structure should be:
    # Column 0: Grondgebied (municipality name)
    # Column 1: Bestuur
    # Remaining columns: year-subdomain combinations
    
    # Initialize data structure
    municipality_data = defaultdict(lambda: defaultdict(dict))
    
    # Process each row
    for idx, row in df.iterrows():
        gemeente = row.iloc[0]
        bestuur = row.iloc[1]
        
        if pd.isna(gemeente) or pd.isna(bestuur):
            continue
            
        # Normalize municipality name
        gemeente_clean = normalize_municipality_name(gemeente)
        
        # Skip if not a real municipality
        if "Total" in str(gemeente) or gemeente_clean == "":
            continue
        
        # Process each column (skip first 2)
        for col_idx in range(2, len(row)):
            col_name = df.columns[col_idx]
            value = row.iloc[col_idx]
            
            # Skip if no value
            if pd.isna(value) or value == 0:
                continue
            
            # Parse column name to extract year and subdomain
            # Expected format: "2014\nBV_subdomein_code BV_subdomein_naam"
            # or similar variations
            col_parts = str(col_name).split('\n')
            
            if len(col_parts) >= 2:
                year = col_parts[0].strip()
                subdomain = col_parts[1].strip()
                
                # Validate year
                if year.isdigit() and 2014 <= int(year) <= 2024:
                    municipality_data[gemeente_clean][subdomain][year] = float(value)
    
    # Convert to regular dict for JSON serialization
    output_data = {
        mun: {
            subdomain: dict(years)
            for subdomain, years in subdomains.items()
        }
        for mun, subdomains in municipality_data.items()
    }
    
    print(f"\nProcessed {len(output_data)} municipalities")
    
    # Print sample data
    if output_data:
        sample_mun = list(output_data.keys())[0]
        print(f"\nSample data for {sample_mun}:")
        sample_subdomains = list(output_data[sample_mun].keys())[:3]
        for subdomain in sample_subdomains:
            print(f"  {subdomain}: {output_data[sample_mun][subdomain]}")
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nOutput written to: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
