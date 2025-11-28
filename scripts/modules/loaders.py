"""
Data loaders voor verschillende input formaten.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict
from .utils import normalize_municipality_name, parse_value


def load_geojson(filepath: str | Path) -> dict:
    """
    Laad een GeoJSON bestand.
    
    Args:
        filepath: Pad naar GeoJSON bestand
        
    Returns:
        Dict met GeoJSON data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_geojson(data: dict, filepath: str | Path) -> None:
    """
    Sla GeoJSON data op.
    
    Args:
        data: GeoJSON data
        filepath: Output pad
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str | Path) -> dict:
    """
    Laad een JSON bestand.
    
    Args:
        filepath: Pad naar JSON bestand
        
    Returns:
        Dict met JSON data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: dict, filepath: str | Path) -> None:
    """
    Sla JSON data op.
    
    Args:
        data: JSON data
        filepath: Output pad
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)


def load_detail_csv(csv_path: str | Path) -> dict:
    """
    Parse detail CSV bestand (gemeenten als rijen, rekeningen als kolommen).
    
    Args:
        csv_path: Pad naar CSV bestand
        
    Returns:
        Dict met genormaliseerde gemeentenamen als keys
    """
    municipality_data = {}
    processed_municipalities = set()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        rekening_codes = header[1:]  # Skip first column (municipality name)
        
        for row in reader:
            if not row or not row[0]:
                continue
            
            gemeente_naam = row[0]
            normalized_name = normalize_municipality_name(gemeente_naam)
            
            # Skip duplicate municipality entries (prefer first occurrence)
            if normalized_name in processed_municipalities:
                continue
            
            processed_municipalities.add(normalized_name)
            municipality_data[normalized_name] = {
                'rekeningen': [],
                'totaal': 0.0
            }
            
            bedragen = row[1:]
            
            for i, bedrag_str in enumerate(bedragen):
                if i >= len(rekening_codes):
                    break
                
                rekening_code = rekening_codes[i]
                bedrag = parse_value(bedrag_str)
                
                if bedrag is not None and bedrag != 0:
                    code = rekening_code.split()[0] if ' ' in rekening_code else rekening_code
                    
                    municipality_data[normalized_name]['rekeningen'].append({
                        'code': code,
                        'naam': rekening_code,
                        'bedrag': bedrag
                    })
                    municipality_data[normalized_name]['totaal'] += bedrag
    
    return municipality_data


def load_beleidsdomein_csv(csv_path: str | Path) -> dict:
    """
    Parse beleidsdomein CSV bestand.
    
    Args:
        csv_path: Pad naar CSV bestand
        
    Returns:
        Dict met genormaliseerde gemeentenamen als keys
    """
    municipality_data = {}
    processed_municipalities = set()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        beleidsveld_columns = header[2:]  # Skip Grondgebied and Bestuur
        
        for row in reader:
            if not row or len(row) < 2:
                continue
            
            gemeente_naam = row[0].strip()
            bestuur = row[1].strip()
            
            if not gemeente_naam or not bestuur:
                continue
            
            normalized_name = normalize_municipality_name(gemeente_naam)
            
            # Skip duplicate municipality entries (prefer first occurrence, often "Total")
            if normalized_name in processed_municipalities:
                continue
            
            processed_municipalities.add(normalized_name)
            municipality_data[normalized_name] = {
                'beleidsvelden': [],
                'totaal': 0.0
            }
            
            bedragen = row[2:]
            
            for i, bedrag_str in enumerate(bedragen):
                if i >= len(beleidsveld_columns):
                    break
                
                beleidsveld = beleidsveld_columns[i]
                bedrag = parse_value(bedrag_str)
                
                if bedrag is not None and bedrag != 0:
                    parts = beleidsveld.split(' ', 1)
                    code = parts[0] if parts else beleidsveld
                    naam = parts[1] if len(parts) > 1 else beleidsveld
                    
                    municipality_data[normalized_name]['beleidsvelden'].append({
                        'code': code,
                        'naam': naam,
                        'volledig': beleidsveld,
                        'bedrag': bedrag
                    })
                    municipality_data[normalized_name]['totaal'] += bedrag
    
    return municipality_data
