import pandas as pd
import geopandas as gpd
import os
import json
import re

# Paths
DATA_CSV = 'data/data.csv'
GIS_GPKG = 'data/gisco/LAU_RG_01M_2024_4326.gpkg'
OUTPUT_GEOJSON = 'longread_output/municipalities.geojson'
OUTPUT_AVERAGES = 'longread_output/averages.json'

# Fusion Mapping (Old Name -> New Name in CSV)
FUSION_MAPPING = {
    'borsbeek': 'antwerpen',
    'antwerpen': 'antwerpen', # Should map to itself but key is needed if we rely on keys for check? No, map() uses keys.
    'beveren': 'beveren-kruibeke-zwijndrecht', # Beveren (Sint-Niklaas) in GIS?
    'beveren (sint-niklaas)': 'beveren-kruibeke-zwijndrecht', # Specific check

    'kruibeke': 'beveren-kruibeke-zwijndrecht',
    'zwijndrecht': 'beveren-kruibeke-zwijndrecht',
    'bilzen': 'bilzen-hoeselt',
    'hoeselt': 'bilzen-hoeselt',
    'tongeren': 'tongeren-borgloon',
    'borgloon': 'tongeren-borgloon',
    'merelbeke': 'merelbeke-melle',
    'melle': 'merelbeke-melle',
    'nazareth': 'nazareth-de pinte',
    'de pinte': 'nazareth-de pinte',
    'galmaarden': 'pajottegem',
    'gooik': 'pajottegem',
    'herne': 'pajottegem',
    'tessenderlo': 'tessenderlo-ham',
    'ham': 'tessenderlo-ham',
    'tielt': 'tielt',
    'meulebeke': 'tielt',
    'lochristi': 'lochristi',
    'wachtebeke': 'lochristi',
    'lokeren': 'lokeren',
    'moerbeke': 'lokeren',
    'wingene': 'wingene',
    'ruiselede': 'wingene',
    'hasselt': 'hasselt',
    'kortessem': 'hasselt'
}

def clean_gis_name(name):
    if not isinstance(name, str):
        return ""
    # Antwerpen in GIS is "Antwerpen / Anvers"
    # But also check if specific name handling is needed
    # Just lowercasing and splitting should be enough for "Antwerpen / Anvers" -> "antwerpen"
    
    # Special case: "Aalst (Aalst) / Alost (Alost)" -> "aalst"
    # Special case: "Beveren (Sint-Niklaas) / Beveren (Saint-Nicolas)" -> "beveren (sint-niklaas)" ? 
    # No, we want to match keys in FUSION_MAPPING.
    # Let's keep parenthesis for specific matches if needed, OR strip them.
    # The mismatch check showed 'aalst (aalst) / alost (alost)' missing in CSV (which has 'aalst')
    # 'antwerpen / anvers' missing in CSV (which has 'antwerpen')
    
    # Split by slash
    name = name.split('/')[0]
    
    # Remove parenthesis ONLY if it duplicates name or is region info we don't want?
    # Actually, for 'Beveren (Sint-Niklaas)', the parens distinguish it.
    # But usually we just want the name.
    # Let's clean parens content out.
    name = re.sub(r'\(.*?\)', '', name)
    return name.strip().lower()

def get_province(gisco_id):
    # Format: BE_XXXXX
    if not isinstance(gisco_id, str):
        return None
    
    # Extract NIS code (digits)
    parts = gisco_id.split('_')
    if len(parts) < 2:
        return None
    nis = parts[1]
    
    if nis.startswith('1'):
        return 'Provincie Antwerpen'
    elif nis.startswith('3'):
        return 'Provincie West-Vlaanderen'
    elif nis.startswith('4'):
        return 'Provincie Oost-Vlaanderen'
    elif nis.startswith('7'):
        return 'Provincie Limburg'
    elif nis.startswith('23') or nis.startswith('24'):
        return 'Provincie Vlaams-Brabant'
    # 21 is Brussels, 25 is Waals-Brabant, 5/6/8/9 are Wallonia
    return None

def main():
    print("Reading CSV data...")
    df = pd.read_csv(DATA_CSV, sep=';', decimal=',')
    df.rename(columns={'Grondgebied': 'municipality'}, inplace=True)
    
    numeric_cols = [str(year) for year in range(2014, 2025)]
    for col in numeric_cols:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace('.', '').str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['match_name'] = df['municipality'].str.lower().str.strip()
    
    print("Reading GIS data...")
    gdf = gpd.read_file(GIS_GPKG)
    if 'CNTR_CODE' in gdf.columns:
        gdf = gdf[gdf['CNTR_CODE'] == 'BE']
    
    gdf['clean_name'] = gdf['LAU_NAME'].apply(clean_gis_name)
    gdf['mapped_name'] = gdf['clean_name'].map(FUSION_MAPPING).fillna(gdf['clean_name'])
    
    # Assign Province to GIS rows BEFORE dissolve
    # (Fusions are within provinces, so this is safe)
    gdf['province'] = gdf['GISCO_ID'].apply(get_province)
    
    # Dissolve
    print("Dissolving geometries for fusions...")
    csv_names = set(df['match_name'])
    gdf_filtered = gdf[gdf['mapped_name'].isin(csv_names)].copy()
    
    # We want to keep 'province' after dissolve.
    # Dissolve usually keeps the first value of the group for non-geometry columns if specified,
    # or we can aggregate. Since they are in same province, 'first' is fine.
    gdf_dissolved = gdf_filtered.dissolve(by='mapped_name', aggfunc='first')
    gdf_dissolved['match_name'] = gdf_dissolved.index
    
    # Merge with Data
    merged = gdf_dissolved.merge(df, on='match_name', how='inner')
    print(f"Merged data: {len(merged)} municipalities matched.")
    
    # Calculate Averages
    print("Calculating averages...")
    
    # 1. Flanders (simple mean)
    flanders_avg = df[numeric_cols].mean().to_dict()
    
    # 2. Provinces
    # Now we have province in 'merged' dataframe (which came from GIS -> Dissolve -> Merge)
    # So we can group by 'province' column in merged
    prov_stats = merged.groupby('province')[numeric_cols].mean().to_dict(orient='index')
    
    averages = {
        'Vlaanderen': flanders_avg,
        'Provincies': prov_stats
    }
    
    # Export GeoJSON
    keep_cols = ['municipality', 'match_name', 'province'] + numeric_cols + ['geometry']
    final_cols = [c for c in keep_cols if c in merged.columns]
    final_gdf = merged[final_cols]
    
    if not os.path.exists(os.path.dirname(OUTPUT_GEOJSON)):
        os.makedirs(os.path.dirname(OUTPUT_GEOJSON))
        
    print(f"Saving to {OUTPUT_GEOJSON}...")
    final_gdf.to_file(OUTPUT_GEOJSON, driver='GeoJSON')
    
    print(f"Saving to {OUTPUT_AVERAGES}...")
    with open(OUTPUT_AVERAGES, 'w') as f:
        json.dump(averages, f, indent=2)
        
    print("Done.")

if __name__ == "__main__":
    main()
