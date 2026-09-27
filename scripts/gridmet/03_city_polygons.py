"""
Step 3 · gridMET · Write one zipped city-limits shapefile per city for ClimateEngine upload.
Input : data/raw/gridmet/tiger_places/tl_2025_<FIPS>_place.zip (not modified)
Output: data/processed/gridmet/step03_city_polygons/<city>_citylimits.zip   (9 files)
        data/processed/gridmet/step03_city_polygons/step03_summary.csv
Decision D3: shapes used as-is, except San Francisco keeps only its main piece
(drops the Farallon Islands piece ~31 km offshore).
Run from repo root:  python3 scripts/gridmet/03_city_polygons.py
"""
import os, zipfile, tempfile
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPolygon

RAW = "data/raw/gridmet/tiger_places"
OUT = "data/processed/gridmet/step03_city_polygons"
os.makedirs(OUT, exist_ok=True)

CITIES = {  # city key -> (state FIPS, Census NAME); Fairbanks excluded (no gridMET in AK)
    "bakersfield": ("06", "Bakersfield"), "fresno": ("06", "Fresno"),
    "losangeles": ("06", "Los Angeles"), "sanfrancisco": ("06", "San Francisco"),
    "eugene": ("41", "Eugene"), "brownsville": ("48", "Brownsville"),
    "detroit": ("26", "Detroit"), "pittsburgh": ("42", "Pittsburgh"),
    "boston": ("25", "Boston"),
}
KEEP_MAIN_PIECE_ONLY = {"sanfrancisco"}   # Decision D3

summary = []
for city, (fips, name) in CITIES.items():
    gdf = gpd.read_file(f"zip://{RAW}/tl_2025_{fips}_place.zip")
    c = gdf[(gdf["NAME"] == name) & (gdf["NAMELSAD"] == f"{name} city")].copy()
    assert len(c) == 1, f"{name}: expected 1 match, got {len(c)}"
    area_before = c.to_crs(5070).area.iloc[0] / 1e6
    g = c.geometry.iloc[0]
    n_before = len(g.geoms) if isinstance(g, MultiPolygon) else 1

    if city in KEEP_MAIN_PIECE_ONLY and isinstance(g, MultiPolygon):
        pieces_m = list(c.to_crs(5070).geometry.iloc[0].geoms)
        biggest = max(range(len(pieces_m)), key=lambda i: pieces_m[i].area)
        c = c.set_geometry([list(g.geoms)[biggest]], crs=c.crs)

    c = c[["GEOID", "NAME", "NAMELSAD", "ALAND", "AWATER", "geometry"]].to_crs(4326)  # WGS84
    g2 = c.geometry.iloc[0]
    n_after = len(g2.geoms) if isinstance(g2, MultiPolygon) else 1
    area_after = c.to_crs(5070).area.iloc[0] / 1e6

    with tempfile.TemporaryDirectory() as tmp:
        base = f"{city}_citylimits"
        c.to_file(os.path.join(tmp, f"{base}.shp"))
        with zipfile.ZipFile(os.path.join(OUT, f"{base}.zip"), "w", zipfile.ZIP_DEFLATED) as z:
            for ext in ["shp", "shx", "dbf", "prj", "cpg"]:
                z.write(os.path.join(tmp, f"{base}.{ext}"), f"{base}.{ext}")

    summary.append({"city": city, "geoid": c["GEOID"].iloc[0], "pieces_before": n_before,
                    "pieces_after": n_after, "area_before_km2": round(area_before, 2),
                    "area_after_km2": round(area_after, 2),
                    "removed_km2": round(area_before - area_after, 2)})

s = pd.DataFrame(summary)
s.to_csv(f"{OUT}/step03_summary.csv", index=False)
print(s.to_string(index=False))
