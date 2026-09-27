"""UTCI Step 1: read-only check of raw CDS time-series NetCDF files.
Nothing in data/raw/ is modified. Writes three CSVs to data/processed/utci/step01_raw_check/:
  raw_check.csv  one row per file (fingerprint, grid, time continuity)
  raw_cells.csv  one row per grid cell (empty / implausible counts, min/mean/max °C)
  raw_extra.csv  location check, duplicate cells, empty hours by year, agreement where boxes overlap."""
import hashlib, pathlib, math, itertools
import numpy as np, pandas as pd, xarray as xr

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/utci/cds_timeseries"
OUT = ROOT / "data/processed/utci/step01_raw_check"; OUT.mkdir(parents=True, exist_ok=True)

# Requested boxes, N/S/W/E (from the plan; D9: overlapping cells + 1-cell margin)
BOX = {"annarbor":(42.50,42.00,-84.00,-83.50), "bakersfield":(35.75,35.00,-119.50,-118.50),
 "boston":(42.75,42.00,-71.50,-70.50), "brownsville":(26.50,25.50,-98.00,-97.00),
 "delano":(36.00,35.50,-119.50,-119.00), "detroit":(42.75,42.00,-83.50,-82.75),
 "eugene":(44.50,43.75,-123.50,-122.75), "fairbanks":(65.25,64.50,-148.00,-147.25),
 "fresno":(37.25,36.50,-120.25,-119.50), "losangeles":(34.50,33.50,-119.00,-118.00),
 "phoenix":(34.25,33.00,-112.50,-111.75), "pittsburgh":(40.75,40.00,-80.25,-79.50),
 "raymondville":(26.75,26.25,-98.00,-97.50), "sandiego":(33.25,32.25,-117.50,-116.75),
 "sanfrancisco":(38.25,37.50,-122.75,-122.00), "springfield":(44.25,43.75,-123.25,-122.75),
 "warren":(42.75,42.25,-83.25,-82.75)}
START, END = pd.Timestamp("1991-01-01 00:00"), pd.Timestamp("2026-06-13 23:00")  # latest offered by CDS on 2026-09-27
PLAUSIBLE_K = (183.15, 333.15)   # -90 to +60 °C; flag only (Claude's choice)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""): h.update(chunk)
    return h.hexdigest()

files, cells = [], []
for p in sorted(RAW.glob("utci_*_1991-2026.nc")):
    city = p.name.split("_")[1]
    ds = xr.open_dataset(p, engine="netcdf4")
    t = pd.DatetimeIndex(ds["valid_time"].values)
    lat, lon = ds["latitude"].values, ds["longitude"].values
    N, S, W, E = BOX[city]
    u = ds["utci"]
    expected = pd.date_range(START, END, freq="h")
    files.append(dict(
        city=city, file=p.name, bytes=p.stat().st_size, sha256=sha256(p),
        units=u.attrs.get("units"), n_lat=len(lat), n_lon=len(lon),
        grid_on_quarter_degree=bool(np.allclose(lat*4, np.round(lat*4)) and np.allclose(lon*4, np.round(lon*4))),
        box_matches=bool(np.isclose(lat.max(),N) and np.isclose(lat.min(),S) and np.isclose(lon.min(),W) and np.isclose(lon.max(),E)),
        first_utc=t.min(), last_utc=t.max(), n_hours=len(t), n_expected=len(expected),
        n_missing_hours=len(expected.difference(t)), n_duplicate_hours=int(t.duplicated().sum()),
        sorted=bool(t.is_monotonic_increasing), n_outside_period=int(((t<START)|(t>END)).sum())))
    for la in lat:
        for lo in lon:
            v = u.sel(latitude=la, longitude=lo).values
            ok = v[~np.isnan(v)]
            cells.append(dict(city=city, lat=la, lon=lo, n_values=v.size, n_empty=int(np.isnan(v).sum()),
                n_implausible=int(((ok<PLAUSIBLE_K[0])|(ok>PLAUSIBLE_K[1])).sum()),
                min_c=round(float(ok.min())-273.15,2) if ok.size else None,
                mean_c=round(float(ok.mean())-273.15,2) if ok.size else None,
                max_c=round(float(ok.max())-273.15,2) if ok.size else None))
    ds.close()

# ---- Extra checks (added after the first 10 files; read-only) ----
import geopandas as gpd
from shapely.geometry import box as cellbox
hall = pd.read_csv(ROOT/"data/processed/metar/metar_station_distances.csv").drop_duplicates("city").set_index("city")
def city_limits(city):
    if city == "fairbanks":   # no Step-3 zip for Fairbanks; take GEOID 0224230 from the AK TIGER file
        ak = gpd.read_file(ROOT/"data/raw/gridmet/tiger_places/tl_2025_02_place.zip")
        return ak[ak.GEOID == "0224230"].to_crs(4326).union_all()
    return gpd.read_file(ROOT/f"data/processed/gridmet/step03_city_polygons/{city}_citylimits.zip").to_crs(4326).union_all()

extra, opened = [], {}
for p in sorted(RAW.glob("utci_*_1991-2026.nc")):
    city = p.name.split("_")[1]
    ds = xr.open_dataset(p, engine="netcdf4"); opened[city] = ds
    lat, lon = ds["latitude"].values, ds["longitude"].values
    t = pd.DatetimeIndex(ds["valid_time"].values)
    have = {(round(a, 2), round(b, 2)) for a in lat for b in lon}
    # Location: city-hall cell = nearest 0.25° centre; city cells = every 0.25° cell (centre ± 0.125°) touching city limits
    hlat, hlon = hall.loc[city, "city_hall_lat"], hall.loc[city, "city_hall_lon"]
    hc = (round(hlat*4)/4, round(hlon*4)/4)
    g = city_limits(city); x0, y0, x1, y1 = g.bounds
    need = [(a/4, b/4) for a in range(math.floor((y0-.125)*4), math.ceil((y1+.125)*4)+1)
                       for b in range(math.floor((x0-.125)*4), math.ceil((x1+.125)*4)+1)
            if g.intersects(cellbox(b/4-.125, a/4-.125, b/4+.125, a/4+.125))]
    missing = [c for c in need if (round(c[0], 2), round(c[1], 2)) not in have]
    # Hottest 3 UTC days in the city-hall cell (sanity check against known heat events)
    hs = ds["utci"].sel(latitude=hc[0], longitude=hc[1]).to_series() - 273.15
    top = hs.resample("D").max().nlargest(3)
    # Duplicate cells: pairs with identical values in > 50% of hours
    flat = ds["utci"].values.reshape(len(t), -1); pts = [(a, b) for a in lat for b in lon]
    dups = []
    for i, j in itertools.combinations(range(len(pts)), 2):
        share = float(np.mean(flat[:, i] == flat[:, j]))
        if share > 0.5: dups.append(f"{pts[i][0]:.2f},{pts[i][1]:.2f}={pts[j][0]:.2f},{pts[j][1]:.2f} ({share:.5f})")
    # Empty hours: hours with an empty value in any cell, by UTC year
    e = np.isnan(flat).any(axis=1)
    by_year = pd.Series(t[e].year).value_counts().sort_index().to_dict()
    extra.append(dict(city=city, city_hall=f"{hlat:.4f},{hlon:.4f}", hall_cell=f"{hc[0]:.2f},{hc[1]:.2f}",
        hall_cell_in_file=hc in have, n_city_cells=len(need), n_city_cells_missing=len(missing),
        hottest_utc_days_hall_cell="; ".join(f"{d.date()} {v:.1f}C" for d, v in top.items()),
        duplicate_cells="; ".join(dups) if dups else "none",
        hours_with_empty_cell=int(e.sum()), empty_hours_by_year=str(by_year) if by_year else "none", overlap_with=""))
# Agreement where two cities' boxes share cells
for a, b in itertools.combinations(sorted(opened), 2):
    A, B = opened[a], opened[b]
    la, lo = np.intersect1d(A.latitude, B.latitude), np.intersect1d(A.longitude, B.longitude)
    if len(la) and len(lo):
        same = np.array_equal(A.utci.sel(latitude=la, longitude=lo).values, B.utci.sel(latitude=la, longitude=lo).values, equal_nan=True)
        for r in extra:
            if r["city"] in (a, b):
                r["overlap_with"] += f"{b if r['city']==a else a}: {len(la)*len(lo)} cells, identical={same}; "
for ds in opened.values(): ds.close()
pd.DataFrame(extra).to_csv(OUT/"raw_extra.csv", index=False)

pd.DataFrame(files).to_csv(OUT/"raw_check.csv", index=False)
pd.DataFrame(cells).to_csv(OUT/"raw_cells.csv", index=False)
print(pd.DataFrame(files).T.to_string()); print(pd.DataFrame(cells).to_string(index=False))
