"""UTCI Step 2: area weights of each 0.25° UTCI cell within city limits (decision D11, method B).
Read-only on inputs. Output: data/processed/utci/step02_cell_weights/cell_weights.csv"""
import itertools, pathlib, numpy as np, pandas as pd, geopandas as gpd, xarray as xr
from shapely.geometry import box

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT/"data/raw/utci/cds_timeseries"
POLY = ROOT/"data/processed/gridmet/step03_city_polygons"
TIGER_AK = ROOT/"data/raw/gridmet/tiger_places/tl_2025_02_place.zip"
HALLS = ROOT/"data/processed/metar/metar_station_distances.csv"
OUT = ROOT/"data/processed/utci/step02_cell_weights"; OUT.mkdir(parents=True, exist_ok=True)
CITIES = ["losangeles","phoenix","sandiego","detroit","bakersfield","sanfrancisco",
          "fresno","boston","eugene","fairbanks","brownsville","annarbor"]   # D10 order
H, EA = 0.125, "EPSG:6933"      # half-cell; equal-area CRS for km²

def km2(g): return gpd.GeoSeries([g], crs=4326).to_crs(EA).area.iloc[0] / 1e6
def limits(city):
    if city == "fairbanks":
        ak = gpd.read_file(TIGER_AK); return ak[ak.GEOID == "0224230"].to_crs(4326).union_all()
    return gpd.read_file(POLY/f"{city}_citylimits.zip").to_crs(4326).union_all()

halls = pd.read_csv(HALLS).drop_duplicates("city").set_index("city")
rows = []
for city in CITIES:
    ds = xr.open_dataset(RAW/f"utci_{city}_1991-2026.nc", engine="netcdf4")
    pts = [(round(float(a),2), round(float(b),2)) for a in ds.latitude.values for b in ds.longitude.values]
    flat = ds.utci.values.reshape(ds.sizes["valid_time"], -1); ds.close()
    dup = {p: [] for p in pts}          # recorded only; duplicates need no special handling (see log)
    for i, j in itertools.combinations(range(len(pts)), 2):
        if np.mean(flat[:, i] == flat[:, j]) > 0.5: dup[pts[i]].append(pts[j]); dup[pts[j]].append(pts[i])
    g = limits(city); total = km2(g)
    hall = (round(halls.loc[city,"city_hall_lat"]*4)/4, round(halls.loc[city,"city_hall_lon"]*4)/4)
    for a, b in pts:
        cell = box(b-H, a-H, b+H, a+H)
        if not g.intersects(cell): continue
        ov = km2(g.intersection(cell))
        rows.append(dict(city=city, lat=a, lon=b, overlap_km2=round(ov, 3), weight=ov/total,
                         is_city_hall_cell=(a, b) == hall,
                         duplicate_of="; ".join(f"{x:.2f},{y:.2f}" for x, y in dup[(a, b)])))
w = pd.DataFrame(rows)
w["weight"] = w.groupby("city")["weight"].transform(lambda s: s / s.sum())   # exact sum = 1 per city
w.to_csv(OUT/"cell_weights.csv", index=False)
print(w.groupby("city", sort=False).agg(n_cells=("lat","size"), weight_sum=("weight","sum")).to_string())
