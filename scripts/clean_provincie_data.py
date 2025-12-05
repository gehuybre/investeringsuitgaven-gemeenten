"""
Script om provinciale investeringsdata te verwerken van Excel naar CSV.

Verwerkt drie meerjarenplannen:
- 2014-2019 (jaren 2014-2019)
- 2020-2025 (jaren 2020-2025, gefilterd uit 2020-2027 plan)
- 2026-2031 (jaren 2026-2031)
"""

import pandas as pd
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def clean_provincie_beleidsveld_data():
    """
    Verwerk het 'provincie per beleidsveld.xlsx' bestand.
    
    Structuur:
    - Kolom 'Bestuur' = 'Meerjarenplan'
    - Kolom 'Unnamed: 1' = Rapportjaar (2014, 2020, 2026 of 'Total')
    - Kolom 'Unnamed: 2' = Boekjaar (2014-2031 of 'Total')
    - Kolom 'Unnamed: 3' = BV_domein
    - Kolom 'Unnamed: 4' = BV_subdomein
    - Kolom 'Unnamed: 5' = Beleidsveld
    - Kolommen 6-10 = Provincies (Antwerpen, Limburg, Oost-Vlaanderen, Vlaams-Brabant, West-Vlaanderen)
    """
    
    print("Laden van provincie per beleidsveld data...")
    
    # Lees Excel bestand
    df = pd.read_excel(
        'data/provinciebesturen/provincie per beleidsveld.xlsx',
        sheet_name='Export'
    )
    
    # Filter alleen meerjarenplan rows
    df = df[df['Bestuur'] == 'Meerjarenplan'].copy()
    
    # Hernoem kolommen voor duidelijkheid
    df.rename(columns={
        'Unnamed: 1': 'rapportjaar',
        'Unnamed: 2': 'boekjaar',
        'Unnamed: 3': 'bv_domein',
        'Unnamed: 4': 'bv_subdomein',
        'Unnamed: 5': 'beleidsveld'
    }, inplace=True)
    
    # Verwijder de 'Bestuur' kolom (bevat alleen 'Meerjarenplan')
    df.drop(columns=['Bestuur'], inplace=True)
    
    # Filter totaalrijen (rapportjaar en boekjaar beide != 'Total')
    df = df[
        (df['rapportjaar'] != 'Total') & 
        (df['boekjaar'] != 'Total') &
        (pd.notna(df['boekjaar']))
    ].copy()
    
    # Converteer jaren naar integers
    df['rapportjaar'] = pd.to_numeric(df['rapportjaar'], errors='coerce')
    df['boekjaar'] = pd.to_numeric(df['boekjaar'], errors='coerce')
    
    # Filter per meerjarenplan en sla op
    print("\nVerwerken meerjarenplannen...")
    
    # 1. MJP 2014-2019 (rapportjaar = 2014, boekjaar 2014-2019)
    mjp_2014_2019 = df[
        (df['rapportjaar'] == 2014) &
        (df['boekjaar'] >= 2014) &
        (df['boekjaar'] <= 2019)
    ].copy()
    mjp_2014_2019['meerjarenplan'] = '2014-2019'
    print(f"  MJP 2014-2019: {len(mjp_2014_2019)} rijen")
    
    # 2. MJP 2020-2025 (rapportjaar = 2020, boekjaar 2020-2025)
    mjp_2020_2025 = df[
        (df['rapportjaar'] == 2020) &
        (df['boekjaar'] >= 2020) &
        (df['boekjaar'] <= 2025)
    ].copy()
    mjp_2020_2025['meerjarenplan'] = '2020-2025'
    print(f"  MJP 2020-2025: {len(mjp_2020_2025)} rijen")
    
    # 3. MJP 2026-2031 (rapportjaar = 2026, boekjaar 2026-2031)
    mjp_2026_2031 = df[
        (df['rapportjaar'] == 2026) &
        (df['boekjaar'] >= 2026) &
        (df['boekjaar'] <= 2031)
    ].copy()
    mjp_2026_2031['meerjarenplan'] = '2026-2031'
    print(f"  MJP 2026-2031: {len(mjp_2026_2031)} rijen")
    
    # Combineer alle meerjarenplannen
    df_clean = pd.concat([mjp_2014_2019, mjp_2020_2025, mjp_2026_2031], ignore_index=True)
    
    # Herorden kolommen
    provincie_cols = [
        'Provincie Antwerpen',
        'Provincie Limburg', 
        'Provincie Oost-Vlaanderen',
        'Provincie Vlaams-Brabant',
        'Provincie West-Vlaanderen'
    ]
    
    cols_order = [
        'meerjarenplan',
        'rapportjaar',
        'boekjaar',
        'bv_domein',
        'bv_subdomein',
        'beleidsveld'
    ] + provincie_cols
    
    # Selecteer alleen bestaande kolommen (skip 'Total' kolom)
    existing_cols = [col for col in cols_order if col in df_clean.columns]
    df_clean = df_clean[existing_cols]
    
    # Converteer provinciale waarden naar numeriek
    for col in provincie_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    # Sla op als CSV
    output_path = 'data/provinciebesturen/provincie_investeringen_per_beleidsveld_cleaned.csv'
    df_clean.to_csv(output_path, index=False)
    print(f"\n✓ Cleaned data opgeslagen: {output_path}")
    print(f"  Totaal aantal rijen: {len(df_clean)}")
    print(f"\nVoorbeeld data:")
    print(df_clean.head(10))
    
    # Toon samenvattende statistieken
    print("\n=== Samenvattende statistieken ===")
    print(f"\nMeerjarenplannen:")
    print(df_clean['meerjarenplan'].value_counts().sort_index())
    print(f"\nBoekjaren per meerjarenplan:")
    for mjp in df_clean['meerjarenplan'].unique():
        jaren = sorted(df_clean[df_clean['meerjarenplan'] == mjp]['boekjaar'].unique())
        print(f"  {mjp}: {jaren}")
    
    return df_clean


if __name__ == '__main__':
    df = clean_provincie_beleidsveld_data()
    print("\n✓ Script voltooid!")
