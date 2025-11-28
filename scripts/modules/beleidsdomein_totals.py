"""
Generator voor beleidsdomein totals over alle jaren.
"""

import pandas as pd
from pathlib import Path
from .utils import parse_value


def generate_beleidsdomein_totals(csv_path: str | Path) -> dict:
    """
    Process beleidsdomein CSV en bereken totals per jaar per beleidsdomein.
    
    Aggregeert investeringsdata over alle gemeenten heen.
    
    Args:
        csv_path: Pad naar 'investeringsuitgave per beleidsdomein.csv'
        
    Returns:
        Dict met structuur {subdomein: {year: total}}
    """
    # Read header rows to understand structure
    # Row 0: (empty or type)
    # Row 1: Boekjaar (years) - contains years like 2014, 2015, etc. repeated for each subdomain
    # Row 2: BV_domein (main policy domains)
    # Row 3: BV_subdomein (policy subdomains) - this is what we aggregate on
    # Row 4: Grondgebied;Bestuur;Uitgave per inwoner;...
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = [f.readline().strip() for _ in range(5)]
    
    # Parse headers - skip first 2 columns (Grondgebied, Bestuur)
    years_raw = lines[1].split(';')[2:]
    subdomeinen_raw = lines[3].split(';')[2:]
    
    # Create a mapping of column index to (year, subdomein)
    column_mapping = {}
    for idx, (year_str, subdomein_str) in enumerate(zip(years_raw, subdomeinen_raw)):
        year_str = year_str.strip()
        subdomein_str = subdomein_str.strip()
        
        # Parse year
        try:
            year = int(year_str)
        except (ValueError, AttributeError):
            continue
        
        # Skip if no subdomein
        if not subdomein_str:
            continue
        
        column_mapping[idx] = {
            'year': year,
            'subdomein': subdomein_str
        }
    
    # Process the actual data - skip first 4 header rows
    data_df = pd.read_csv(csv_path, sep=';', encoding='utf-8', skiprows=4)
    
    # Initialize result structure: {subdomein: {year: total}}
    totals_by_subdomein = {}
    processed_municipalities = set()
    
    # Iterate through all data rows
    for _, row in data_df.iterrows():
        municipality = row.iloc[0]
        
        # Skip if this is a total/aggregate row or empty
        if pd.isna(municipality) or municipality in ['Total', 'Totaal', ''] or not municipality.strip():
            continue
        
        # Normalize municipality name to avoid counting duplicates
        normalized_name = municipality.strip().lower()
        if normalized_name in processed_municipalities:
            continue
        processed_municipalities.add(normalized_name)
        
        # Process each column with investment data
        for col_idx, mapping in column_mapping.items():
            actual_col_idx = col_idx + 2  # Adjust for Grondgebied, Bestuur columns
            
            if actual_col_idx < len(row):
                import math
                value = parse_value(str(row.iloc[actual_col_idx]))
                
                # Skip if value is None, NaN, inf, or 0
                if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))) or value == 0:
                    continue
                
                year = mapping['year']
                subdomein = mapping['subdomein']
                
                # Initialize subdomein dict if needed
                if subdomein not in totals_by_subdomein:
                    totals_by_subdomein[subdomein] = {}
                
                # Initialize year in subdomein if needed
                if year not in totals_by_subdomein[subdomein]:
                    totals_by_subdomein[subdomein][year] = 0.0
                
                # Add value to total
                totals_by_subdomein[subdomein][year] += value
    
    # Clean up and format the result
    result = {}
    import math
    
    for subdomein, year_data in totals_by_subdomein.items():
        result[subdomein] = {}
        for year, total in sorted(year_data.items()):
            # Check for NaN/inf and replace with 0
            if math.isnan(total) or math.isinf(total):
                result[subdomein][year] = 0.0
            else:
                result[subdomein][year] = round(total, 2)
    
    return result
