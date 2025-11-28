"""
Processors om GeoJSON te verrijken met verschillende datasets.
"""

from .utils import normalize_municipality_name


def enrich_with_detail_data(geojson: dict, detail_data: dict) -> tuple[dict, int]:
    """
    Voeg detail (rekeningen) data toe aan GeoJSON.
    
    Args:
        geojson: GeoJSON data
        detail_data: Dict met detail data per gemeente
        
    Returns:
        Tuple van (verrijkte geojson, aantal matches)
    """
    matched = 0
    
    for feature in geojson['features']:
        municipality = feature['properties']['municipality']
        normalized_name = normalize_municipality_name(municipality)
        totaal_2024 = feature['properties'].get('2024', 0)
        
        if normalized_name in detail_data:
            gemeente_detail = detail_data[normalized_name]
            totaal_details = sum(r['bedrag'] for r in gemeente_detail.get('rekeningen', []))
            
            feature['properties']['detail_2024'] = {
                'totaal_details': round(totaal_details, 2),
                'aantal_rekeningen': len(gemeente_detail.get('rekeningen', [])),
                'verschil_met_totaal': round(totaal_details - totaal_2024, 2),
                'top_rekeningen': [
                    {
                        'code': r['code'],
                        'naam': r['naam'],
                        'bedrag': r['bedrag']
                    }
                    for r in sorted(gemeente_detail.get('rekeningen', []), 
                                   key=lambda x: abs(x['bedrag']), 
                                   reverse=True)[:10]
                ]
            }
            matched += 1
        else:
            feature['properties']['detail_2024'] = None
    
    return geojson, matched


def enrich_with_beleidsdomein_data(geojson: dict, beleidsdomein_data: dict) -> tuple[dict, int]:
    """
    Voeg beleidsdomein data toe aan GeoJSON.
    
    Args:
        geojson: GeoJSON data
        beleidsdomein_data: Dict met beleidsdomein data per gemeente
        
    Returns:
        Tuple van (verrijkte geojson, aantal matches)
    """
    matched = 0
    
    for feature in geojson['features']:
        municipality = feature['properties']['municipality']
        normalized_name = normalize_municipality_name(municipality)
        totaal_2024 = feature['properties'].get('2024', 0)
        
        if normalized_name in beleidsdomein_data:
            gemeente_beleidsdomein = beleidsdomein_data[normalized_name]
            totaal_beleidsdomein = gemeente_beleidsdomein.get('totaal', 0)
            
            feature['properties']['beleidsdomein_2024'] = {
                'totaal_beleidsdomein': round(totaal_beleidsdomein, 2),
                'aantal_beleidsvelden': len(gemeente_beleidsdomein.get('beleidsvelden', [])),
                'verschil_met_totaal': round(totaal_beleidsdomein - totaal_2024, 2),
                'top_beleidsvelden': [
                    {
                        'code': b['code'],
                        'naam': b['naam'],
                        'volledig': b['volledig'],
                        'bedrag': b['bedrag']
                    }
                    for b in sorted(gemeente_beleidsdomein.get('beleidsvelden', []),
                                   key=lambda x: abs(x['bedrag']),
                                   reverse=True)[:10]
                ]
            }
            matched += 1
        else:
            feature['properties']['beleidsdomein_2024'] = None
    
    return geojson, matched
