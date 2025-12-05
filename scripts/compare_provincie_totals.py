"""
Vergelijk totalen uit verschillende bronnen:
- Correcte totalen uit totaal provincies.csv
- Berekende totalen uit beleidsdomein data
- Berekende totalen uit rekeningen data
"""
import json
from pathlib import Path

def compare_totals():
    """Vergelijk de drie verschillende totalen."""
    
    # Laad correcte totalen
    with open('longread_output/provincie_totals.json', 'r') as f:
        correcte_totalen = json.load(f)
    
    # Laad beleidsdomein detailed (bevat totalen)
    with open('longread_output/provincie_detailed.json', 'r') as f:
        beleidsdomein_data = json.load(f)
    
    # Laad rekeningen detailed
    with open('longread_output/provincie_rekeningen_detailed.json', 'r') as f:
        rekeningen_data = json.load(f)
    
    # Maak vergelijking
    vergelijking = {}
    
    for provincie in correcte_totalen.keys():
        vergelijking[provincie] = {}
        
        for mjp in ['2014-2019', '2020-2025', '2026-2031']:
            correct_totaal = correcte_totalen[provincie][mjp]
            
            # Haal beleidsdomein totaal op
            beleidsdomein_totaal = beleidsdomein_data.get(provincie, {}).get(mjp, {}).get('totaal', 0)
            
            # Haal rekeningen totaal op
            rekeningen_totaal = rekeningen_data.get(provincie, {}).get(mjp, {}).get('totaal', 0)
            
            # Bereken afwijkingen
            afwijking_beleidsdomein = beleidsdomein_totaal - correct_totaal
            afwijking_rekeningen = rekeningen_totaal - correct_totaal
            
            # Bereken percentage afwijking
            pct_beleidsdomein = (afwijking_beleidsdomein / correct_totaal * 100) if correct_totaal > 0 else 0
            pct_rekeningen = (afwijking_rekeningen / correct_totaal * 100) if correct_totaal > 0 else 0
            
            vergelijking[provincie][mjp] = {
                'correct': round(correct_totaal, 2),
                'beleidsdomein': round(beleidsdomein_totaal, 2),
                'rekeningen': round(rekeningen_totaal, 2),
                'afwijking_beleidsdomein': round(afwijking_beleidsdomein, 2),
                'afwijking_rekeningen': round(afwijking_rekeningen, 2),
                'pct_afwijking_beleidsdomein': round(pct_beleidsdomein, 2),
                'pct_afwijking_rekeningen': round(pct_rekeningen, 2)
            }
    
    # Sla vergelijking op
    output_file = 'longread_output/provincie_comparison.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(vergelijking, f, indent=2, ensure_ascii=False)
    
    print("Vergelijking van totalen:")
    print("=" * 80)
    
    for provincie in sorted(vergelijking.keys()):
        print(f"\n{provincie}:")
        for mjp in ['2014-2019', '2020-2025', '2026-2031']:
            data = vergelijking[provincie][mjp]
            if data['correct'] > 0:
                print(f"  {mjp}:")
                print(f"    Correct:         €{data['correct']:>8.2f}")
                print(f"    Beleidsdomein:   €{data['beleidsdomein']:>8.2f} (verschil: €{data['afwijking_beleidsdomein']:>7.2f}, {data['pct_afwijking_beleidsdomein']:>6.2f}%)")
                print(f"    Rekeningen:      €{data['rekeningen']:>8.2f} (verschil: €{data['afwijking_rekeningen']:>7.2f}, {data['pct_afwijking_rekeningen']:>6.2f}%)")
    
    print(f"\n✓ Opgeslagen: {output_file}")
    
    return vergelijking

if __name__ == '__main__':
    compare_totals()
