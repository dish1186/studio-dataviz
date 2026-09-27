"""ERA5-Land Step 1 (Fairbanks actual temperature): read-only check of the raw CDS downloads.
Product: "ERA5-Land hourly time-series data from 1950 to present", variable 2m temperature (K), CSV in zip.
Checks per grid point: position on the 0.1° grid, hourly continuity, duplicates, blanks, plausible range;
and that the partial first pull matches the 8-point pull on the points they share.
Output: data/processed/era5land/step01_raw_check/raw_check.csv"""
import hashlib, pathlib, zipfile, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT/"data/raw/era5land/fairbanks"
OUT = ROOT/"data/processed/era5land/step01_raw_check"; OUT.mkdir(parents=True, exist_ok=True)
MAIN, FIRST = "era5land_t2m_fairbanks_1991-2026_8pts.zip", "era5land_t2m_fairbanks_1991-2026.zip"
PLAUSIBLE_K = (213.15, 313.15)      # -60 °C to +40 °C (-76 to 104 °F): flag only

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
    z = zipfile.ZipFile(RAW/name); d = pd.read_csv(z.open(z.namelist()[0]))
    d["lat"], d["lon"] = d.latitude.round(2), d.longitude.round(2)
    return d

rows = []
for name in (MAIN, FIRST):
    d = read(name)
    full = pd.date_range(d.valid_time.min(), d.valid_time.max(), freq="h")
    for (a, b), g in d.groupby(["lat", "lon"]):
        t = pd.to_datetime(g.valid_time)
        rows.append(dict(file=name, sha256=sha(RAW/name), lat=a, lon=b,
            off_grid=float(max((g.latitude*10 - (g.latitude*10).round()).abs().max(),
                               (g.longitude*10 - (g.longitude*10).round()).abs().max())),
            first_utc=g.valid_time.min(), last_utc=g.valid_time.max(),
            n_hours=len(g), n_expected=len(full), n_missing=len(full.difference(t)),
            n_duplicate=int(t.duplicated().sum()), n_blank=int(g.t2m.isna().sum()),
            n_implausible=int(((g.t2m < PLAUSIBLE_K[0]) | (g.t2m > PLAUSIBLE_K[1])).sum()),
            min_k=round(g.t2m.min(), 2), max_k=round(g.t2m.max(), 2)))
r = pd.DataFrame(rows)
m = read(FIRST).merge(read(MAIN), on=["valid_time", "lat", "lon"], suffixes=("_first", "_main"))
r["first_vs_main_max_abs_diff_k"] = float((m.t2m_first - m.t2m_main).abs().max())
r["first_vs_main_rows_compared"] = len(m)
r.to_csv(OUT/"raw_check.csv", index=False)
print(r.drop(columns="sha256").to_string(index=False))
