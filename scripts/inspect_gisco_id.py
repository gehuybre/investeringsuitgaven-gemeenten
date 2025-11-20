import geopandas as gpd
gdf = gpd.read_file('data/gisco/LAU_RG_01M_2024_4326.gpkg')
be = gdf[gdf['CNTR_CODE'] == 'BE']
print(be[['LAU_NAME', 'GISCO_ID']].head(10))

