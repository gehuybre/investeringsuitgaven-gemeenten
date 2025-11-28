#!/usr/bin/env python3
"""
Converteer PowerBI CSV export naar gegroepeerde JSON structuur.

Input:  data/opgesplitst.csv
Output: data/opgesplitst_grouped.json

De output bevat:
- Metadata per rekening code (1x hiërarchie info)
- Gemeenten als key-value pairs per rekening
- Geen repetitie van namen of metadata
"""

import csv
import json
from pathlib import Path


def parse_value(value: str) -> float | None:
    """Converteer CSV waarde naar float (komma -> punt voor decimalen)."""
    if not value or value.strip() == '':
        return None
    try:
        return float(value.strip().replace(',', '.'))
    except ValueError:
        return None


def convert_csv_to_grouped_json():
    """
    Converteer CSV naar gegroepeerde JSON:
    - Groepeer per rekening code
    - Metadata 1x per rekening
    - Gemeenten als object met waarden
    """
    # Paden
    data_dir = Path(__file__).parent.parent / 'data'
    input_file = data_dir / 'opgesplitst.csv'
    output_file = data_dir / 'opgesplitst_grouped.json'
    
    print("Conversie starten...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)
        
        # Vind indices
        alg_rek_idx = headers.index('Alg. rekening')
        total_idx = headers.index('Total')
        gemeente_headers = headers[alg_rek_idx + 1:total_idx]
        
        # Grouped structure
        grouped = {}
        
        for row in reader:
            # Skip records zonder rekening of met "Total" (dat zijn aggregaties)
            alg_rekening = row[alg_rek_idx] if alg_rek_idx < len(row) else None
            if not alg_rekening or alg_rekening == 'Total':
                continue
            
            # Extract rekening code (eerste deel voor spatie)
            rek_code = alg_rekening.split(' ')[0] if ' ' in alg_rekening else alg_rekening
            
            # Verzamel niveau info
            niveaus = {}
            for i in range(1, 9):
                niveau_value = row[i + 1]  # +1 want Type en Boekjaar zijn 0,1
                if niveau_value:
                    niveaus[f'niveau_{i}'] = niveau_value
            
            # Build path
            niveau_values = [v for k, v in sorted(niveaus.items())]
            path = ' > '.join(niveau_values + [alg_rekening]) if niveau_values else alg_rekening
            
            # Eerste keer deze rekening tegenkomen: sla metadata op
            if rek_code not in grouped:
                grouped[rek_code] = {
                    'alg_rekening': alg_rekening,
                    'categorie': niveau_values[-1] if niveau_values else None,
                    'niveaus': niveaus,
                    'niveau_diepte': len(niveaus),
                    'path': path,
                    'gemeenten': {}
                }
            
            # Voeg gemeente waarden toe
            for i, gemeente_naam in enumerate(gemeente_headers):
                value = parse_value(row[alg_rek_idx + 1 + i])
                if value is not None and value != 0:  # Skip nulls en nullen
                    grouped[rek_code]['gemeenten'][gemeente_naam] = value
    
    # Build output structure
    output = {
        'boekjaar': 2024,
        'type_rapport': 'Jaarrekening',
        'rekeningen': grouped,
        'metadata': {
            'rekening_count': len(grouped),
            'gemeente_count': len(gemeente_headers),
            'beschrijving': 'Investeringsuitgaven per rekening, gegroepeerd met metadata'
        }
    }
    
    # Schrijf JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # Stats
    total_gemeenten_entries = sum(len(r['gemeenten']) for r in grouped.values())
    
    print(f"✓ Conversie compleet!")
    print(f"  Input:  {input_file.name}")
    print(f"  Output: {output_file.name}")
    print(f"  ")
    print(f"  Rekeningen: {len(grouped)}")
    print(f"  Gemeenten:  {len(gemeente_headers)}")
    print(f"  Data punten: {total_gemeenten_entries}")
    print(f"  File size: {output_file.stat().st_size / 1024:.1f} KB")


if __name__ == '__main__':
    convert_csv_to_grouped_json()
