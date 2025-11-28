#!/usr/bin/env python3
"""
Script to clean the code-rekeningen.csv file.
Extracts the hierarchical account structure with codes and descriptions.
"""

import csv
import re



def clean_csv(input_path, output_path):
    """Clean the code-rekeningen CSV file."""
    # Use csv.reader to handle proper CSV parsing
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        lines = list(reader)
    
    # Skip header lines and empty lines
    data_rows = []
    skip_patterns = [
        'Algemene rekeningen',
        'Rubriek (schema T2)',
        'EXPLOITATIE',
        'INVESTERINGEN',
        'FINANCIERING',
        'BUDGETTAIRE RESULTATEN',
        'FACTURERING TUSSEN',
        'TUSSENKOMST IN DE'
    ]
    
    for row in lines:
        # Skip lines that are just empty columns
        if not any(cell.strip() for cell in row):
            continue
        
        # Skip header/section title lines
        row_text = ';'.join(row)
        if any(pattern in row_text for pattern in skip_patterns):
            continue
        
        # Count leading empty columns for hierarchy level
        level = 0
        for cell in row:
            if cell == '':
                level += 1
            else:
                break
        
        # Find code and description
        code = ''
        description = ''
        voetnoot = ''
        
        # Look for code starting from first non-empty cell
        found_content = False
        for i in range(level, len(row)):
            if row[i].strip():
                if not found_content:
                    # First non-empty cell is the code (or section header)
                    code = row[i].strip()
                    found_content = True
                elif not description:
                    # Second non-empty cell is the description
                    description = row[i].strip()
                elif not voetnoot and row[i].strip().startswith('['):
                    # Footnote reference
                    voetnoot = row[i].strip()
                    break
        
        # Only add rows that have a description
        if description:
            data_rows.append({
                'niveau': level,
                'code': code,
                'omschrijving': description,
                'voetnoot': voetnoot
            })
    
    # Write cleaned CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['niveau', 'code', 'omschrijving', 'voetnoot'])
        writer.writeheader()
        writer.writerows(data_rows)
    
    print(f"Cleaned {len(data_rows)} rows")
    print(f"Output written to: {output_path}")

if __name__ == '__main__':
    input_file = 'data/code-rekeningen.csv'
    output_file = 'data/code-rekeningen-clean.csv'
    clean_csv(input_file, output_file)
