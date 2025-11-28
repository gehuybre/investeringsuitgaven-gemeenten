#!/usr/bin/env python3
"""
Genereer efficiënte export formaten voor de data.
Reduceert file size door repetitieve data te vermijden.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict


def create_table_format():
    """
    Creëer een tabel-georiënteerde structuur:
    - Schema: kolomnamen 1x
    - Data: alleen waarden als arrays
    - Reduceert repetitie van keys dramatisch
    """
    data_dir = Path(__file__).parent.parent / 'data'
    
    with open(data_dir / 'opgesplitst_normalized.json', 'r') as f:
        data = json.load(f)
    
    if not data:
        return
    
    # Schema: kolomnamen
    columns = list(data[0].keys())
    
    # Data: alleen waarden
    rows = []
    for record in data:
        row = [record[col] for col in columns]
        rows.append(row)
    
    output = {
        'schema': columns,
        'data': rows,
        'count': len(rows)
    }
    
    output_file = data_dir / 'opgesplitst_table.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    original_size = (data_dir / 'opgesplitst_normalized.json').stat().st_size
    new_size = output_file.stat().st_size
    reduction = (1 - new_size / original_size) * 100
    
    print(f"✓ Table format: {len(rows)} rows → {output_file.name}")
    print(f"  Size: {new_size/1024:.1f} KB (was {original_size/1024:.1f} KB)")
    print(f"  Reduction: {reduction:.1f}%")


def create_grouped_format():
    """
    Groepeer per rekening code, dan gemeenten als key-value.
    Vermijdt herhaling van alle niveau/categorie info.
    """
    data_dir = Path(__file__).parent.parent / 'data'
    
    with open(data_dir / 'opgesplitst_normalized.json', 'r') as f:
        data = json.load(f)
    
    # Groepeer per alg_rekening
    grouped = {}
    
    for record in data:
        rek_code = record['alg_rekening_code']
        
        if rek_code not in grouped:
            # Eerste keer: sla metadata op
            grouped[rek_code] = {
                'alg_rekening': record['alg_rekening'],
                'categorie': record['categorie'],
                'niveaus': {
                    k: v for k, v in record.items() 
                    if k.startswith('niveau_') and k != 'niveau_diepte'
                },
                'niveau_diepte': record['niveau_diepte'],
                'path': record['path'],
                'gemeenten': {}
            }
        
        # Voeg gemeente waarde toe
        grouped[rek_code]['gemeenten'][record['gemeente']] = record['waarde']
    
    output = {
        'boekjaar': data[0]['boekjaar'],
        'type_rapport': data[0]['type_rapport'],
        'rekeningen': grouped,
        'totaal_records': len(data),
        'rekening_codes': len(grouped)
    }
    
    output_file = data_dir / 'opgesplitst_grouped.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    original_size = (data_dir / 'opgesplitst_normalized.json').stat().st_size
    new_size = output_file.stat().st_size
    reduction = (1 - new_size / original_size) * 100
    
    print(f"✓ Grouped format: {len(grouped)} rekeningen → {output_file.name}")
    print(f"  Size: {new_size/1024:.1f} KB (was {original_size/1024:.1f} KB)")
    print(f"  Reduction: {reduction:.1f}%")


def create_csv_export():
    """
    Simpele CSV export - vaak de meest efficiënte voor tabulaire data.
    """
    data_dir = Path(__file__).parent.parent / 'data'
    
    with open(data_dir / 'opgesplitst_normalized.json', 'r') as f:
        data = json.load(f)
    
    if not data:
        return
    
    output_file = data_dir / 'opgesplitst_normalized.csv'
    
    # Bepaal kolommen (maar sorteer ze logisch)
    key_columns = ['gemeente', 'waarde', 'alg_rekening_code', 'alg_rekening', 'categorie']
    niveau_columns = [f'niveau_{i}' for i in range(1, 9)]
    other_columns = ['niveau_diepte', 'path', 'boekjaar', 'type_rapport']
    
    columns = key_columns + niveau_columns + other_columns
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
    
    original_size = (data_dir / 'opgesplitst_normalized.json').stat().st_size
    new_size = output_file.stat().st_size
    reduction = (1 - new_size / original_size) * 100
    
    print(f"✓ CSV export: {len(data)} rows → {output_file.name}")
    print(f"  Size: {new_size/1024:.1f} KB (was {original_size/1024:.1f} KB)")
    print(f"  Reduction: {reduction:.1f}%")


def create_parquet_export():
    """
    Parquet: kolomgeoriënteerd, gecomprimeerd, ideaal voor analytics.
    Vereist: pip install pyarrow
    """
    data_dir = Path(__file__).parent.parent / 'data'
    
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        print("⊘ Parquet format: pyarrow niet geïnstalleerd (optioneel)")
        print("  Install met: pip install pyarrow")
        return
    
    with open(data_dir / 'opgesplitst_normalized.json', 'r') as f:
        data = json.load(f)
    
    # Converteer naar PyArrow tabel
    table = pa.Table.from_pylist(data)
    
    output_file = data_dir / 'opgesplitst_normalized.parquet'
    pq.write_table(table, output_file, compression='snappy')
    
    original_size = (data_dir / 'opgesplitst_normalized.json').stat().st_size
    new_size = output_file.stat().st_size
    reduction = (1 - new_size / original_size) * 100
    
    print(f"✓ Parquet format: {len(data)} rows → {output_file.name}")
    print(f"  Size: {new_size/1024:.1f} KB (was {original_size/1024:.1f} KB)")
    print(f"  Reduction: {reduction:.1f}%")
    print(f"  (Fast, columnar, ideal voor pandas/analytics)")


if __name__ == '__main__':
    print("=" * 60)
    print("Efficiënte Export Formaten")
    print("=" * 60)
    print()
    
    create_table_format()
    print()
    
    create_grouped_format()
    print()
    
    create_csv_export()
    print()
    
    create_parquet_export()
    print()
    
    print("=" * 60)
    print("✓ Alle exports compleet!")
    print("=" * 60)
