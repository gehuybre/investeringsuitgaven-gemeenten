"""
Verwerk totaal provincies CSV en genereer correcte totalen voor de grafiek.
"""
import pandas as pd
import json
from pathlib import Path

def process_totaal_provincies():
    """Lees het CSV en bereken totalen per meerjarenplan."""
    
    # Lees CSV met juiste delimiter
    df = pd.read_csv(
        'data/provinciebesturen/totaal provincies.csv',
        sep=';',
        decimal=','
    )
    
    print("Kolommen:", df.columns.tolist())
    print("\nEerste rijen:")
    print(df.head())
    
    # De structuur is:
    # Rij 0: Type rapport (Meerjarenplan)
    # Rij 1: Rapportjaar (2014, 2014, ..., 2020, ..., 2026, ...)
    # Rij 2: Boekjaar (2014, 2015, 2016, ...)
    # Rij 3: Niveau 2 (I.1 Investeringsuitgaven)
    # Rij 4: Grondgebied (Uitgave per inwoner)
    # Rij 5+: Provincies met waarden per jaar
    
    # Skip eerste 4 rijen en gebruik rij 4 als header
    df = pd.read_csv(
        'data/provinciebesturen/totaal provincies.csv',
        sep=';',
        decimal=',',
        skiprows=4
    )
    
    # Hernoem eerste kolom
    df.rename(columns={df.columns[0]: 'Provincie'}, inplace=True)
    
    print("\nNa processing:")
    print(df.head())
    print("\nKolommen:", df.columns.tolist())
    
    # Definieer de meerjarenplan periodes op basis van boekjaren
    # 2014-2019: kolommen 0-5 (indices 1-6)
    # 2020-2025: kolommen 6-11 (indices 7-12)
    # 2026-2031: kolommen 14-19 (indices 15-20)
    
    results = {}
    
    for idx, row in df.iterrows():
        provincie = row['Provincie']
        
        # Skip lege rijen
        if pd.isna(provincie) or provincie.strip() == '':
            continue
            
        # Parse provincie naam
        if provincie.startswith('Provincie '):
            provincie_naam = provincie.replace('Provincie ', '')
        else:
            provincie_naam = provincie
        
        # Bereken totalen per meerjarenplan
        # Let op: kolom indices zijn verschoven door de Provincie kolom
        totaal_2014_2019 = 0
        totaal_2020_2025 = 0
        totaal_2026_2031 = 0
        
        # 2014-2019: kolommen 1-6 (na Provincie kolom)
        for i in range(1, 7):
            if i < len(row):
                val = row.iloc[i]
                if pd.notna(val) and val != '':
                    try:
                        totaal_2014_2019 += float(val)
                    except:
                        pass
        
        # 2020-2025: kolommen 7-12
        for i in range(7, 13):
            if i < len(row):
                val = row.iloc[i]
                if pd.notna(val) and val != '':
                    try:
                        totaal_2020_2025 += float(val)
                    except:
                        pass
        
        # 2026-2031: kolommen 15-20
        for i in range(15, 21):
            if i < len(row):
                val = row.iloc[i]
                if pd.notna(val) and val != '':
                    try:
                        totaal_2026_2031 += float(val)
                    except:
                        pass
        
        results[provincie_naam] = {
            '2014-2019': round(totaal_2014_2019, 2),
            '2020-2025': round(totaal_2020_2025, 2),
            '2026-2031': round(totaal_2026_2031, 2)
        }
    
    print("\nResultaten:")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # Sla op
    output_file = 'longread_output/provincie_totals.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Opgeslagen: {output_file}")
    
    return results

if __name__ == '__main__':
    process_totaal_provincies()
