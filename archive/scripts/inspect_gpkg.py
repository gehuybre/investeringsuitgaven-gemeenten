import geopandas as gpd
gdf = gpd.read_file('data/gisco/LAU_RG_01M_2024_4326.gpkg')
print(gdf.columns)
print(gdf.head(1))

