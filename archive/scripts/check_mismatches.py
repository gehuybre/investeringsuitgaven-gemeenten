import pandas as pd
import geopandas as gpd

DATA_CSV = 'data/data.csv'
GIS_GPKG = 'data/gisco/LAU_RG_01M_2024_4326.gpkg'

def check_mismatches():
    print("Reading CSV...")
    df = pd.read_csv(DATA_CSV, sep=';', decimal=',')
    # Clean names
    csv_names = set(df['Grondgebied'].str.strip().str.lower())
    
    print("Reading GIS...")
    gdf = gpd.read_file(GIS_GPKG)
    if 'CNTR_CODE' in gdf.columns:
        gdf = gdf[gdf['CNTR_CODE'] == 'BE']
    
    gis_names = set(gdf['LAU_NAME'].str.strip().str.lower())
    
    # Find differences
    missing_in_gis = csv_names - gis_names
    missing_in_csv = gis_names - csv_names
    
    print(f"CSV entries: {len(csv_names)}")
    print(f"GIS entries: {len(gis_names)}")
    print(f"Missing in GIS (present in CSV): {len(missing_in_gis)}")
    print(sorted(list(missing_in_gis)))
    print(f"Missing in CSV (present in GIS): {len(missing_in_csv)}")
    print(sorted(list(missing_in_csv)))

if __name__ == "__main__":
    check_mismatches()

