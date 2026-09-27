"""
Step 2 · gridMET · Audit city-limits boundaries (READ-ONLY, changes no data).
Input : data/raw/gridmet/tiger_places/tl_2025_<FIPS>_place.zip  (Census TIGER/Line 2025)
        data/processed/metar/metar_station_distances.csv          (airport coordinates)
Output: data/processed/gridmet/step02_boundary_audit/boundary_audit.csv   (1 row per city)
        data/processed/gridmet/step02_boundary_audit/boundary_parts.csv   (1 row per polygon piece)
        data/processed/gridmet/step02_boundary_audit/airport_in_city.csv  (1 row per airport)
Areas/distances use equal-area projections: EPSG:5070 (CONUS Albers), EPSG:3338 (Alaska Albers).
Run from repo root:  python3 scripts/gridmet/02_boundary_audit.py
"""
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

RAW = "data/raw/gridmet/tiger_places"
OUT = "data/processed/gridmet/step02_boundary_audit"
os.makedirs(OUT, exist_ok=True)

# city key -> (state FIPS, Census NAME). Fairbanks: airport check only (no gridMET in AK).
CITIES = {
    "bakersfield":  ("06", "Bakersfield"),
    "fresno":       ("06", "Fresno"),
    "losangeles":   ("06", "Los Angeles"),
    "sanfrancisco": ("06", "San Francisco"),
    "eugene":       ("41", "Eugene"),
    "brownsville":  ("48", "Brownsville"),
    "detroit":      ("26", "Detroit"),
    "pittsburgh":   ("42", "Pittsburgh"),
    "boston":       ("25", "Boston"),
    "fairbanks":    ("02", "Fairbanks"),
}
GRIDMET_DEG = 1 / 24  # gridMET cell size (~4 km)

def load_city(fips, name):
    gdf = gpd.read_file(f"zip://{RAW}/tl_2025_{fips}_place.zip")
    hit = gdf[(gdf["NAME"] == name) & (gdf["NAMELSAD"] == f"{name} city")]
    assert len(hit) == 1, f"{name}: expected 1 match, got {len(hit)}"
    return hit

def cells_inside(geom_ll):
    """Approx. count of gridMET cell CENTRES inside the boundary (rough size check only)."""
    minx, miny, maxx, maxy = geom_ll.bounds
    xs = np.arange(np.floor(minx / GRIDMET_DEG), np.ceil(maxx / GRIDMET_DEG)) * GRIDMET_DEG + GRIDMET_DEG / 2
    ys = np.arange(np.floor(miny / GRIDMET_DEG), np.ceil(maxy / GRIDMET_DEG)) * GRIDMET_DEG + GRIDMET_DEG / 2
    pts = gpd.GeoSeries([Point(x, y) for x in xs for y in ys], crs=4269)
    return int(pts.within(geom_ll).sum())

rows, parts_rows, air_rows = [], [], []
stations = pd.read_csv("data/processed/metar/metar_station_distances.csv")

for city, (fips, name) in CITIES.items():
    c = load_city(fips, name)
    epsg = 3338 if fips == "02" else 5070
    geom_ll = c.geometry.iloc[0]
    geom_m = c.to_crs(epsg).geometry.iloc[0]
    pieces = list(geom_m.geoms) if geom_m.geom_type == "MultiPolygon" else [geom_m]
    pieces.sort(key=lambda p: p.area, reverse=True)
    main = pieces[0]
    for i, p in enumerate(pieces):
        parts_rows.append({"city": city, "part": i, "area_km2": p.area / 1e6,
                           "dist_from_main_km": p.distance(main) / 1e3})
    rows.append({
        "city": city, "geoid": c["GEOID"].iloc[0], "namelsad": c["NAMELSAD"].iloc[0],
        "aland_km2": c["ALAND"].iloc[0] / 1e6,          # Census land area
        "awater_km2": c["AWATER"].iloc[0] / 1e6,        # Census water area
        "water_share_pct": 100 * c["AWATER"].iloc[0] / (c["ALAND"].iloc[0] + c["AWATER"].iloc[0]),
        "n_parts": len(pieces),
        "farthest_part_km": max(p.distance(main) for p in pieces) / 1e3,
        "gridmet_cells_approx": None if fips == "02" else cells_inside(geom_ll),
    })
    # Airport check: all airports for this city (in-city status + km outside the boundary)
    for _, s in stations[stations["city"] == city].iterrows():
        pt = gpd.GeoSeries([Point(s.station_lon, s.station_lat)], crs=4326).to_crs(epsg).iloc[0]
        inside = geom_m.contains(pt)
        air_rows.append({"city": city, "station": s.station, "in_city_limits": inside,
                         "km_outside_boundary": 0.0 if inside else pt.distance(geom_m) / 1e3,
                         "handoff_note": s.in_city_limits_note})

pd.DataFrame(rows).to_csv(f"{OUT}/boundary_audit.csv", index=False)
pd.DataFrame(parts_rows).to_csv(f"{OUT}/boundary_parts.csv", index=False)
pd.DataFrame(air_rows).to_csv(f"{OUT}/airport_in_city.csv", index=False)
print(pd.DataFrame(rows).round(2).to_string(index=False))
print(pd.DataFrame(air_rows).round(2).to_string(index=False))
