"""UTCI Step 3: one hourly UTCI series per city = area-weighted average of its cells (D11).
Rules (approved by Dish, D11): cells without a value in an hour are skipped and the remaining weights
re-normalized; if the cells with a value cover < 50% of the city's weight, the hour is left empty.
Read-only on inputs. Output: data/processed/utci/step03_city_hourly/utci_<city>_hourly.csv.gz (+ summary)."""
import pathlib, numpy as np, pandas as pd, xarray as xr

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT/"data/raw/utci/cds_timeseries"
W = pd.read_csv(ROOT/"data/processed/utci/step02_cell_weights/cell_weights.csv")
OUT = ROOT/"data/processed/utci/step03_city_hourly"; OUT.mkdir(parents=True, exist_ok=True)
MIN_COVER = 0.5
CITIES = list(dict.fromkeys(W.city))          # the 12 cities in D10 order

summary = []
for city in CITIES:
    w = W[W.city == city]
    ds = xr.open_dataset(RAW/f"utci_{city}_1991-2026.nc", engine="netcdf4")
    t = pd.DatetimeIndex(ds.valid_time.values)
    # hours x cells matrix of UTCI (K), columns in the order of the weights table
    U = np.stack([ds.utci.sel(latitude=a, longitude=b).values.astype("float64") for a, b in zip(w.lat, w.lon)], axis=1)
    ds.close()
    wt = w.weight.values
    have = ~np.isnan(U)
    cover = (have * wt).sum(axis=1)                              # share of city weight with a value
    num = np.nansum(U * wt, axis=1)
    utci = np.where(cover >= MIN_COVER, num / np.where(cover > 0, cover, np.nan), np.nan)
    df = pd.DataFrame({"time_utc": t.strftime("%Y-%m-%d %H:%M"), "utci_k": utci,
                       "weight_available": cover.round(4), "n_cells_used": have.sum(axis=1), "n_cells": len(wt)})
    df.to_csv(OUT/f"utci_{city}_hourly.csv.gz", index=False, float_format="%.4f")
    v = utci[~np.isnan(utci)] - 273.15
    summary.append(dict(city=city, n_cells=len(wt), n_hours=len(t),
        hours_all_cells=int((have.all(axis=1)).sum()), hours_partial_kept=int(((cover < 1 - 1e-9) & (cover >= MIN_COVER)).sum()),
        hours_empty=int(np.isnan(utci).sum()), min_c=round(v.min(), 2), mean_c=round(v.mean(), 2), max_c=round(v.max(), 2)))
s = pd.DataFrame(summary); s.to_csv(OUT/"step03_summary.csv", index=False); print(s.to_string(index=False))
