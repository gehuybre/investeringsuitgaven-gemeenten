"""
Processors voor provinciale investeringsdata.
"""

import pandas as pd
from pathlib import Path


def load_provincie_data(filepath: str | Path) -> pd.DataFrame:
    """
    Laad cleaned provinciale data.
    
    Args:
        filepath: Pad naar cleaned CSV bestand
        
    Returns:
        DataFrame met provinciale data
    """
    return pd.read_csv(filepath)


def aggregate_provincie_totals(df: pd.DataFrame) -> dict:
    """
    Bereken totale investeringen (per inwoner) per provincie per meerjarenplan.
    
    De cijfers zijn "per inwoner per jaar", en we tellen alle jaren op om het
    totaal voor de hele meerjarenplanperiode te krijgen.
    
    Args:
        df: DataFrame met provinciale data
        
    Returns:
        Dict met structuur: {provincie: {meerjarenplan: totaal}}
    """
    provincies = [
        'Provincie Antwerpen',
        'Provincie Limburg',
        'Provincie Oost-Vlaanderen',
        'Provincie Vlaams-Brabant',
        'Provincie West-Vlaanderen'
    ]
    
    results = {}
    
    for provincie in provincies:
        provincie_naam = provincie.replace('Provincie ', '')
        results[provincie_naam] = {}
        
        for mjp in ['2014-2019', '2020-2025', '2026-2031']:
            # Filter data voor Total rijen (niet alle beleidsdomeinen optellen)
            mjp_data = df[
                (df['meerjarenplan'] == mjp) &
                (df['bv_domein'] == 'Total')
            ].copy()
            
            # Bereken som over alle jaren
            totaal = mjp_data[provincie].sum()
            
            results[provincie_naam][mjp] = round(totaal, 2)
    
    return results


def create_detailed_provincie_data(df: pd.DataFrame) -> dict:
    """
    Maak gedetailleerde data per provincie met beleidsveld breakdown.
    
    Args:
        df: DataFrame met provinciale data
        
    Returns:
        Dict met gedetailleerde data per provincie per meerjarenplan
    """
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
            # Filter data voor deze provincie en dit meerjarenplan (exclusief Total)
            mjp_data = df[
                (df['meerjarenplan'] == mjp) &
                (df['bv_domein'] != 'Total')
            ].copy()
            
            # Groepeer per bv_domein en bereken som over jaren
            beleidsdomein_totals = {}
            
            for domein in mjp_data['bv_domein'].dropna().unique():
                domein_data = mjp_data[mjp_data['bv_domein'] == domein]
                totaal = domein_data[provincie].sum()
                
                if totaal > 0:  # Alleen opnemen als er investeringen zijn
                    beleidsdomein_totals[str(domein)] = round(totaal, 2)
            
            # Sorteer op bedrag (hoogste eerst)
            beleidsdomein_totals = dict(
                sorted(beleidsdomein_totals.items(), 
                       key=lambda x: x[1], 
                       reverse=True)
            )
            
            # Bereken totaal van Total rijen
            total_data = df[
                (df['meerjarenplan'] == mjp) &
                (df['bv_domein'] == 'Total')
            ]
            totaal = total_data[provincie].sum()
            
            detailed_results[provincie_naam][mjp] = {
                'totaal': round(totaal, 2),
                'per_beleidsdomein': beleidsdomein_totals
            }
    
    return detailed_results


def calculate_provincie_statistics(totals: dict) -> dict:
    """
    Bereken statistieken over provinciale investeringen.
    
    Args:
        totals: Dict met totalen per provincie per meerjarenplan
        
    Returns:
        Dict met statistieken per meerjarenplan
    """
    stats = {}
    
    for mjp in ['2014-2019', '2020-2025', '2026-2031']:
        values = [prov_data[mjp] for prov_data in totals.values()]
        
        # Filter uit nullen voor statistieken
        non_zero_values = [v for v in values if v > 0]
        
        if non_zero_values:
            stats[mjp] = {
                'totaal_alle_provincies': round(sum(values), 2),
                'gemiddelde': round(sum(values) / len(totals), 2),
                'minimum': round(min(non_zero_values), 2),
                'maximum': round(max(non_zero_values), 2),
                'aantal_provincies': len(totals),
                'aantal_met_data': len(non_zero_values)
            }
        else:
            stats[mjp] = {
                'totaal_alle_provincies': 0,
                'gemiddelde': 0,
                'minimum': 0,
                'maximum': 0,
                'aantal_provincies': len(totals),
                'aantal_met_data': 0
            }
    
    return stats
