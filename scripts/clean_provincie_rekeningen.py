"""
Script om provinciale rekeningen data te verwerken.
De data heeft een transposed structuur waar provincies in rijen staan en rekeningen in kolommen.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def clean_provincie_rekeningen_data():
    """
    Verwerk het 'provincie per rekening.xlsx' bestand.
    """
    
    print("Laden van provincie per rekening data...")
    
    df = pd.read_excel('data/provinciebesturen/provincie per rekening.xlsx')
    
    # De structuur is:
    # Row 0: Rapportjaar values in columns
    # Row 1: Boekjaar values in columns  
    # Row 2: Rekening codes in columns
    # Row 3: "Bestuur" label
    # Rows 4-8: Province names met data
    
    # Extract metadata rijen
    rapportjaar_row = df.iloc[0].values
    boekjaar_row = df.iloc[1].values
    rekening_row = df.iloc[2].values
    
    # Extract provincies (rijen 4-8)
    provincie_names = df.iloc[4:9, 0].values
    
    print(f"Provincies gevonden: {provincie_names}")
    
    # Verwerk de data
    all_records = []
    
    # Loop door alle kolommen (skip eerste kolom die labels bevat)
    for col_idx in range(1, len(df.columns)):
        rapportjaar = rapportjaar_row[col_idx]
        boekjaar = boekjaar_row[col_idx]
        rekening = rekening_row[col_idx]
        
        # Skip als geen geldige data
        if pd.isna(rapportjaar) or rapportjaar == 'Rapportjaar':
            continue
            
        # Converteer rapportjaar en boekjaar naar numeriek
        try:
            rapportjaar = int(float(rapportjaar))
            boekjaar = int(float(boekjaar)) if pd.notna(boekjaar) and boekjaar != 'Boekjaar' else None
        except (ValueError, TypeError):
            continue
        
        # Bepaal meerjarenplan
        if rapportjaar == 2014 and boekjaar and 2014 <= boekjaar <= 2019:
            meerjarenplan = '2014-2019'
        elif rapportjaar == 2020 and boekjaar and 2020 <= boekjaar <= 2025:
            meerjarenplan = '2020-2025'
        elif rapportjaar == 2026 and boekjaar and 2026 <= boekjaar <= 2031:
            meerjarenplan = '2026-2031'
        else:
            continue
        
        # Extract values voor elke provincie
        for prov_idx, prov_name in enumerate(provincie_names):
            value_row_idx = 4 + prov_idx
            value = df.iloc[value_row_idx, col_idx]
            
            # Converteer naar numeriek
            if pd.notna(value):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    value = None
            else:
                value = None
            
            if value is not None and value != 0:
                all_records.append({
                    'meerjarenplan': meerjarenplan,
                    'rapportjaar': rapportjaar,
                    'boekjaar': boekjaar,
                    'provincie': prov_name,
                    'rekening': str(rekening) if pd.notna(rekening) else 'Onbekend',
                    'bedrag': value
                })
    
    # Maak DataFrame
    df_clean = pd.DataFrame(all_records)
    
    # Sla op
    output_path = 'data/provinciebesturen/provincie_investeringen_per_rekening_cleaned.csv'
    df_clean.to_csv(output_path, index=False)
    
    print(f"\n✓ Cleaned data opgeslagen: {output_path}")
    print(f"  Totaal aantal records: {len(df_clean)}")
    
    # Show summary
    print(f"\n=== Samenvattende statistieken ===")
    print(f"\nMeerjarenplannen:")
    print(df_clean['meerjarenplan'].value_counts().sort_index())
    
    print(f"\nProvincies:")
    print(df_clean['provincie'].value_counts())
    
    print(f"\nAantal unieke rekeningen: {df_clean['rekening'].nunique()}")
    
    # Voorbeelden
    print(f"\n=== Voorbeelden ===")
    print(df_clean.head(10))
    
    return df_clean


if __name__ == '__main__':
    df = clean_provincie_rekeningen_data()
    print("\n✓ Script voltooid!")
