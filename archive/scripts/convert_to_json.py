#!/usr/bin/env python3
"""
Converteer PowerBI CSV export naar JSON.

Belangrijke structuur:
- Records MET 'Alg. rekening' = DETAIL records (concrete waarden)
- Records ZONDER 'Alg. rekening' = TOTAAL/AGGREGATIE records (sommen van children)
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any


def parse_value(value: str) -> float | None:
    """Converteer string waarde naar float, handle lege strings en komma als decimaal."""
    if not value or value.strip() == '':
        return None
    # Vervang komma door punt voor decimalen
    value = value.strip().replace(',', '.')
    try:
        return float(value)
    except ValueError:
        return None


def build_hierarchy(row: List[str], headers: List[str]) -> Dict[str, Any]:
    """Bouw een hiërarchisch object met duidelijk onderscheid tussen detail en totaal records."""
    
    # Basis metadata
    hierarchy = {
        'type_rapport': row[0],
        'boekjaar': int(row[1]) if row[1] else None,
    }
    
    # Verzamel alle ingevulde niveaus
    niveaus = []
    niveau_dict = {}
    for i in range(1, 9):
        niveau_value = row[i + 1]  # +1 want Type en Boekjaar zijn 0,1
        if niveau_value:
            niveaus.append(niveau_value)
            niveau_dict[f'niveau_{i}'] = niveau_value
    
    hierarchy['niveaus'] = niveau_dict
    hierarchy['niveau_diepte'] = len(niveaus)
    
    # Algemene rekening bepaalt of dit detail of totaal is
    # MAAR: "Total" in Alg. rekening is ook een totaal, geen detail!
    alg_rekening = row[10] if len(row) > 10 else None
    
    if alg_rekening and alg_rekening != 'Total':
        # DIT IS EEN DETAIL RECORD - heeft concrete REK code
        hierarchy['record_type'] = 'detail'
        hierarchy['alg_rekening'] = alg_rekening
        hierarchy['alg_rekening_code'] = alg_rekening.split(' ')[0] if ' ' in alg_rekening else alg_rekening
        hierarchy['categorie'] = niveaus[-1] if niveaus else None
        path_parts = niveaus + [alg_rekening]
    else:
        # DIT IS EEN TOTAAL/AGGREGATIE RECORD - som van onderliggende records
        hierarchy['record_type'] = 'totaal'
        if alg_rekening == 'Total':
            hierarchy['totaal_van'] = niveaus[-1] if niveaus else 'Overall Total'
            hierarchy['totaal_niveau'] = 'subtotaal'
            path_parts = niveaus + ['[Subtotaal]']
        else:
            hierarchy['totaal_van'] = niveaus[-1] if niveaus else 'Overall Total'
            hierarchy['totaal_niveau'] = 'hoofdtotaal'
            path_parts = niveaus
    
    # Maak een path voor navigatie
    hierarchy['path'] = ' > '.join(path_parts) if path_parts else 'Root'
    
    # Parse gemeenten waarden
    gemeenten = {}
    for i in range(11, len(headers) - 1):  # Van na 'Alg. rekening' tot voor 'Total'
        if i < len(row):
            gemeente_naam = headers[i]
            waarde = parse_value(row[i])
            if waarde is not None and waarde != 0:  # Filter nulls en nullen
                gemeenten[gemeente_naam] = waarde
    
    hierarchy['gemeenten'] = gemeenten
    hierarchy['gemeenten_count'] = len(gemeenten)
    
    # Parse totaal kolom
    hierarchy['total'] = parse_value(row[-1]) if len(row) > 11 else None
    
    return hierarchy


def convert_csv_to_json(input_file: Path, output_file: Path):
    """Converteer de CSV naar hiërarchisch JSON met detail/totaal onderscheid."""
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)
        
        data = []
        detail_count = 0
        totaal_count = 0
        
        for row in reader:
            if len(row) < 11:  # Skip incomplete rows
                continue
            
            entry = build_hierarchy(row, headers)
            data.append(entry)
            
            if entry['record_type'] == 'detail':
                detail_count += 1
            else:
                totaal_count += 1
    
    # Schrijf naar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Hiërarchisch JSON: {len(data)} records → {output_file.name}")
    print(f"  ├─ {detail_count} detail records (met Alg. rekening = concrete waarden)")
    print(f"  └─ {totaal_count} totaal records (zonder Alg. rekening = aggregaties)")


def create_normalized_json(input_file: Path, output_file: Path):
    """
    Maak een genormaliseerde versie: lange format met één rij per gemeente/categorie.
    ALLEEN detail records (met Alg. rekening), want totalen kunnen berekend worden.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader)
        
        normalized = []
        
        for row in reader:
            if len(row) < 11:
                continue
            
            # Check of dit een detail record is (heeft REK code, niet "Total")
            alg_rekening = row[10] if len(row) > 10 else None
            if not alg_rekening or alg_rekening == 'Total':
                # Skip totaal records in normalized format
                continue
            
            # Verzamel niveau info
            niveaus = []
            niveau_dict = {}
            for i in range(1, 9):
                niveau_value = row[i + 1]
                if niveau_value:
                    niveaus.append(niveau_value)
                    niveau_dict[f'niveau_{i}'] = niveau_value
            
            path = ' > '.join(niveaus + [alg_rekening]) if niveaus else alg_rekening
            
            # Maak een entry voor elke gemeente met waarde
            for i in range(11, len(headers) - 1):
                if i >= len(row):
                    continue
                    
                gemeente_naam = headers[i]
                waarde = parse_value(row[i])
                
                if waarde is not None and waarde != 0:  # Skip nulls en nullen
                    entry = {
                        'gemeente': gemeente_naam,
                        'waarde': waarde,
                        'alg_rekening': alg_rekening,
                        'alg_rekening_code': alg_rekening.split(' ')[0] if ' ' in alg_rekening else alg_rekening,
                        'categorie': niveaus[-1] if niveaus else None,
                        'niveau_diepte': len(niveaus),
                        'path': path,
                        **niveau_dict,
                        'boekjaar': int(row[1]) if row[1] else None,
                        'type_rapport': row[0]
                    }
                    normalized.append(entry)
    
    # Schrijf naar JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Normalized JSON: {len(normalized)} records → {output_file.name}")
    print(f"  (Alleen detail records; totalen weggelaten)")


if __name__ == '__main__':
    # Definieer paden
    data_dir = Path(__file__).parent.parent / 'data'
    input_csv = data_dir / 'opgesplitst.csv'
    
    print("=" * 60)
    print("CSV → JSON Conversie")
    print("=" * 60)
    print()
    
    # Hiërarchische versie (alle records, inclusief totalen)
    hierarchical_json = data_dir / 'opgesplitst.json'
    convert_csv_to_json(input_csv, hierarchical_json)
    print()
    
    # Genormaliseerde versie (alleen detail records, lange format)
    normalized_json = data_dir / 'opgesplitst_normalized.json'
    create_normalized_json(input_csv, normalized_json)
    print()
    
    print("=" * 60)
    print("✓ Conversie compleet!")
    print("=" * 60)
