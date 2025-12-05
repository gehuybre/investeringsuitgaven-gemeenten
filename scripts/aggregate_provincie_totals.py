"""
Script om totale investeringen per provincie per meerjarenplan te berekenen.

Output JSON structuur:
{
    "provincie_naam": {
        "2014-2019": totaal_bedrag,
        "2020-2025": totaal_bedrag,
        "2026-2031": totaal_bedrag
    },
    ...
}
"""

import pandas as pd
import json
from pathlib import Path


def aggregate_provincie_totals():
    """
    Bereken totale investeringen per provincie per meerjarenplan.
    """
    
    print("Laden van cleaned provinciale data...")
    
    # Lees cleaned CSV
    df = pd.read_csv('data/provinciebesturen/provincie_investeringen_per_beleidsveld_cleaned.csv')
    
    print(f"  Geladen: {len(df)} rijen")
    print(f"  Meerjarenplannen: {df['meerjarenplan'].unique()}")
    
    # Lijst van provincies
    provincies = [
        'Provincie Antwerpen',
        'Provincie Limburg',
        'Provincie Oost-Vlaanderen',
        'Provincie Vlaams-Brabant',
        'Provincie West-Vlaanderen'
    ]
    
    # Bereken totalen per provincie per meerjarenplan
    results = {}
    
    print("\n=== Berekenen van totalen ===")
    
    for provincie in provincies:
        provincie_naam = provincie.replace('Provincie ', '')
        results[provincie_naam] = {}
        
        print(f"\n{provincie_naam}:")
        
    for mjp in ['2014-2019', '2020-2025', '2026-2031']:
        # Filter data voor Total rijen (niet alle beleidsdomeinen optellen)
        mjp_data = df[
            (df['meerjarenplan'] == mjp) &
            (df['bv_domein'] == 'Total')
        ].copy()
        
        # Bereken som over alle jaren
        totaal = mjp_data[provincie].sum()
        
        results[provincie_naam][mjp] = round(totaal, 2)            print(f"  {mjp}: €{totaal:,.2f}")
    
    # Sla op als JSON
    output_path = 'longread_output/provincie_totals.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Totalen opgeslagen: {output_path}")
    
    # Bereken ook gemiddelden over alle provincies
    print("\n=== Gemiddelden over alle provincies ===")
    for mjp in ['2014-2019', '2020-2025', '2026-2031']:
        totaal_alle_provincies = sum(
            results[prov][mjp] 
            for prov in results.keys()
        )
        gemiddelde = totaal_alle_provincies / len(results)
        print(f"{mjp}:")
        print(f"  Totaal alle provincies: €{totaal_alle_provincies:,.2f}")
        print(f"  Gemiddelde per provincie: €{gemiddelde:,.2f}")
    
    return results


def create_detailed_province_data():
    """
    Maak gedetailleerde data per provincie met beleidsveld breakdown.
    """
    
    print("\n\n=== Creëren gedetailleerde provinciale data ===")
    
    # Lees cleaned CSV
    df = pd.read_csv('data/provinciebesturen/provincie_investeringen_per_beleidsveld_cleaned.csv')
    
    # Lijst van provincies
    provincies = [
        'Provincie Antwerpen',
        'Provincie Limburg',
        'Provincie Oost-Vlaanderen',
        'Provincie Vlaams-Brabant',
        'Provincie West-Vlaanderen'
    ]
    
    detailed_results = {}
    
    for provincie in provincies:
        provincie_naam = provincie.replace('Provincie ', '')
        detailed_results[provincie_naam] = {}
        
        for mjp in ['2014-2019', '2020-2025', '2026-2031']:
            # Filter data voor deze provincie en dit meerjarenplan
            mjp_data = df[df['meerjarenplan'] == mjp].copy()
            
            # Groepeer per bv_domein en bereken totaal per jaar, dan som
            beleidsdomein_totals = {}
            
            for domein in mjp_data['bv_domein'].dropna().unique():
                domein_data = mjp_data[mjp_data['bv_domein'] == domein]
                # Bereken totaal per jaar voor dit domein, dan som
                yearly_totals = domein_data.groupby('boekjaar')[provincie].sum()
                totaal = yearly_totals.sum()
                
                if totaal > 0:  # Alleen opnemen als er investeringen zijn
                    beleidsdomein_totals[str(domein)] = round(totaal, 2)
            
            # Sorteer op bedrag (hoogste eerst)
            beleidsdomein_totals = dict(
                sorted(beleidsdomein_totals.items(), 
                       key=lambda x: x[1], 
                       reverse=True)
            )
            
            # Bereken totaal
            yearly_totals = mjp_data.groupby('boekjaar')[provincie].sum()
            totaal = yearly_totals.sum()
            
            detailed_results[provincie_naam][mjp] = {
                'totaal': round(totaal, 2),
                'per_beleidsdomein': beleidsdomein_totals
            }
    
    # Sla op als JSON
    output_path = 'longread_output/provincie_detailed.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(detailed_results, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Gedetailleerde data opgeslagen: {output_path}")
    
    # Toon voorbeeld
    print("\nVoorbeeld (Antwerpen 2020-2025, top 5 beleidsdomeinen):")
    top5 = list(detailed_results['Antwerpen']['2020-2025']['per_beleidsdomein'].items())[:5]
    for domein, bedrag in top5:
        print(f"  {domein}: €{bedrag:,.2f}")
    
    return detailed_results


if __name__ == '__main__':
    totals = aggregate_provincie_totals()
    detailed = create_detailed_province_data()
    print("\n✓ Script voltooid!")
