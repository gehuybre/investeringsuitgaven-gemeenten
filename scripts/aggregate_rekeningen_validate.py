"""
Script om rekeningen data te aggregeren en valideren tegen beleidsveld totalen.
"""

import pandas as pd
import json
from pathlib import Path


def aggregate_rekeningen_and_validate():
    """
    Aggregeer rekeningen per provincie per meerjarenplan en valideer tegen beleidsveld totalen.
    """
    
    print("Laden van data...")
    
    # Laad rekeningen data
    rek_df = pd.read_csv('data/provinciebesturen/provincie_investeringen_per_rekening_cleaned.csv')
    
    # Laad beleidsveld data voor vergelijking
    bel_df = pd.read_csv('data/provinciebesturen/provincie_investeringen_per_beleidsveld_cleaned.csv')
    
    # Bereken totalen per provincie per meerjarenplan van rekeningen
    print("\n=== Berekenen rekeningen totalen ===")
    
    rek_totals = {}
    rek_detailed = {}
    
    for provincie in rek_df['provincie'].unique():
        prov_naam = provincie.replace('Provincie ', '')
        rek_totals[prov_naam] = {}
        rek_detailed[prov_naam] = {}
        
        for mjp in ['2014-2019', '2020-2025', '2026-2031']:
            # Filter data
            data = rek_df[
                (rek_df['provincie'] == provincie) & 
                (rek_df['meerjarenplan'] == mjp)
            ]
            
            # Bereken totaal per jaar, dan som over jaren
            yearly_totals = data.groupby('boekjaar')['bedrag'].sum()
            totaal = yearly_totals.sum()
            rek_totals[prov_naam][mjp] = round(totaal, 2)
            
            # Groepeer per rekening (over alle jaren)
            rek_yearly = data.groupby(['rekening', 'boekjaar'])['bedrag'].sum().groupby('rekening').sum()
            rek_detailed[prov_naam][mjp] = {
                'totaal': round(totaal, 2),
                'per_rekening': {
                    rek: round(bedrag, 2) 
                    for rek, bedrag in rek_yearly.sort_values(ascending=False).items() 
                    if bedrag > 0
                }
            }
            
            print(f"{prov_naam} {mjp}: €{totaal:.2f}")
    
    # Bereken totalen van beleidsveld data voor vergelijking
    print("\n=== Berekenen beleidsveld totalen ===")
    
    bel_totals = {}
    provincies_cols = [
        'Provincie Antwerpen',
        'Provincie Limburg',
        'Provincie Oost-Vlaanderen',
        'Provincie Vlaams-Brabant',
        'Provincie West-Vlaanderen'
    ]
    
    for provincie in provincies_cols:
        prov_naam = provincie.replace('Provincie ', '')
        bel_totals[prov_naam] = {}
        
        for mjp in ['2014-2019', '2020-2025', '2026-2031']:
            data = bel_df[bel_df['meerjarenplan'] == mjp]
            # Bereken totaal per jaar, dan som over jaren
            yearly_totals = data.groupby('boekjaar')[provincie].sum()
            totaal = yearly_totals.sum()
            bel_totals[prov_naam][mjp] = round(totaal, 2)
            
            print(f"{prov_naam} {mjp}: €{totaal:.2f}")
    
    # Vergelijk beide totalen
    print("\n=== VALIDATIE: Vergelijking Rekeningen vs Beleidsveld ===")
    print(f"{'Provincie':<20} {'Periode':<12} {'Rekeningen':<15} {'Beleidsveld':<15} {'Verschil':<15} {'Match'}")
    print("-" * 90)
    
    all_match = True
    mismatches = []
    
    for prov in sorted(rek_totals.keys()):
        for mjp in ['2014-2019', '2020-2025', '2026-2031']:
            rek_val = rek_totals[prov][mjp]
            bel_val = bel_totals[prov][mjp]
            verschil = abs(rek_val - bel_val)
            
            # Tolerantie van 0.01 voor afrondingsfouten
            match = verschil < 0.01
            match_str = "✓" if match else "✗"
            
            if not match and (rek_val > 0 or bel_val > 0):
                all_match = False
                mismatches.append({
                    'provincie': prov,
                    'periode': mjp,
                    'rekeningen': rek_val,
                    'beleidsveld': bel_val,
                    'verschil': verschil
                })
            
            print(f"{prov:<20} {mjp:<12} €{rek_val:<14.2f} €{bel_val:<14.2f} €{verschil:<14.2f} {match_str}")
    
    print("-" * 90)
    
    if all_match:
        print("\n✓ VALIDATIE GESLAAGD: Alle totalen komen overeen!")
    else:
        print(f"\n✗ VALIDATIE MISLUKT: {len(mismatches)} verschillen gevonden")
        print("\nDetails van verschillen:")
        for m in mismatches:
            print(f"  {m['provincie']} {m['periode']}: verschil €{m['verschil']:.2f}")
    
    # Sla rekeningen data op
    print("\n=== Opslaan output bestanden ===")
    
    output_totals = 'longread_output/provincie_rekeningen_totals.json'
    with open(output_totals, 'w', encoding='utf-8') as f:
        json.dump(rek_totals, f, indent=2, ensure_ascii=False)
    print(f"✓ {output_totals}")
    
    output_detailed = 'longread_output/provincie_rekeningen_detailed.json'
    with open(output_detailed, 'w', encoding='utf-8') as f:
        json.dump(rek_detailed, f, indent=2, ensure_ascii=False)
    print(f"✓ {output_detailed}")
    
    # Sla validatie report op
    validation_report = {
        'all_match': all_match,
        'mismatches': mismatches,
        'summary': {
            'total_comparisons': len(rek_totals) * 3,
            'matches': len(rek_totals) * 3 - len(mismatches),
            'mismatches': len(mismatches)
        }
    }
    
    output_validation = 'longread_output/provincie_validation.json'
    with open(output_validation, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2, ensure_ascii=False)
    print(f"✓ {output_validation}")
    
    return rek_totals, rek_detailed, validation_report


if __name__ == '__main__':
    totals, detailed, validation = aggregate_rekeningen_and_validate()
    print("\n✓ Script voltooid!")
