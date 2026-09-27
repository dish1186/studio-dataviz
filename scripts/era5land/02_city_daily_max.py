"""ERA5-Land Step 2 (Fairbanks): city-limits daily maximum 2 m air temperature in local time.
1. Weight of each 0.1° cell = its share of Fairbanks city area (TIGER/Line 2025, GEOID 0224230; D2),
   areas in the equal-area CRS EPSG:6933, as UTCI Step 2 (D11 method B).
2. Hourly city value = weighted mean of the 8 cells (no hours are missing, so no re-weighting needed;
   the UTCI < 50%-of-weight rule is kept in the code for consistency).
3. UTC -> America/Anchorage (AKST/AKDT, DST-aware); local calendar days; daily max of the hourly values.
   A day counts only if every local hour is present (UTCI Step 4 rule). K -> °F from unrounded values.
Read-only on inputs. Outputs: data/processed/era5land/step02_daily/ (cell_weights.csv, fairbanks_daily_max.csv)"""
import hashlib, io, pathlib, zipfile, numpy as np, pandas as pd, shapefile
from shapely.geometry import shape, box
from shapely.ops import transform
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAW = ROOT/"data/raw/era5land/fairbanks/era5land_t2m_fairbanks_1991-2026_8pts.zip"
RAW_SHA = "42ccef1cf2d490fb0d594706c78c56613a58f3a34c2a3461e2ba773ae21f85fd"
TIGER_AK = ROOT/"data/raw/gridmet/tiger_places/tl_2025_02_place.zip"
OUT = ROOT/"data/processed/era5land/step02_daily"; OUT.mkdir(parents=True, exist_ok=True)
H, TZ = 0.05, "America/Anchorage"

if hashlib.sha256(RAW.read_bytes()).hexdigest() != RAW_SHA: raise SystemExit("raw SHA-256 mismatch")

# 1. cell weights
z = zipfile.ZipFile(TIGER_AK); n = [x for x in z.namelist() if x.endswith(".shp")][0][:-4]
r = shapefile.Reader(shp=io.BytesIO(z.read(n+".shp")), dbf=io.BytesIO(z.read(n+".dbf")), shx=io.BytesIO(z.read(n+".shx")))
city = [shape(s.__geo_interface__) for s, rec in zip(r.shapes(), r.records()) if rec["GEOID"] == "0224230"][0]
ea = Transformer.from_crs(4269, 6933, always_xy=True).transform      # TIGER is NAD83 (EPSG:4269)
km2 = lambda g: transform(ea, g).area / 1e6
total = km2(city)

z2 = zipfile.ZipFile(RAW); d = pd.read_csv(z2.open(z2.namelist()[0]))
d["lat"], d["lon"] = d.latitude.round(2), d.longitude.round(2)
cells = sorted(set(zip(d.lat, d.lon)))
w = []
for a, b in cells:
    ov = km2(city.intersection(box(b-H, a-H, b+H, a+H)))
    w.append(dict(lat=a, lon=b, overlap_km2=round(ov, 3), weight=ov/total))
w = pd.DataFrame(w); w["weight"] = w.weight / w.weight.sum()
w.to_csv(OUT/"cell_weights.csv", index=False)
print(w.to_string(index=False), f"\ncity area {total:.2f} km2; cells touching: {(w.weight > 0).sum()}")

# 2. hourly weighted mean (K)
d = d.merge(w[["lat", "lon", "weight"]], on=["lat", "lon"])
d = d[d.weight > 0].dropna(subset=["t2m"])
d["wt"] = d.t2m * d.weight
h = d.groupby("valid_time").agg(wt=("wt", "sum"), wsum=("weight", "sum"))
h["t_k"] = np.where(h.wsum >= 0.5, h.wt / h.wsum, np.nan)

# 3. local days, daily max
t = pd.to_datetime(h.index).tz_localize("UTC").tz_convert(TZ)
h = pd.DataFrame({"local": t, "t_k": h.t_k.to_numpy()})
h["date"] = h.local.dt.strftime("%Y-%m-%d")
days = pd.date_range("1991-01-01", h.date.max(), freq="D")
start = days.tz_localize(TZ); end = (days + pd.Timedelta(days=1)).tz_localize(TZ)
exp = pd.Series(((end - start) / pd.Timedelta(hours=1)).astype(int), index=days.strftime("%Y-%m-%d"))   # 23/24/25 on DST days
g = h.dropna(subset=["t_k"]).groupby("date")
imax = g.t_k.idxmax()                                                  # first hour if tied
out = pd.DataFrame({"t_max_k": g.t_k.max(), "n_hours": g.t_k.size(),
                    "hour_of_max_local": pd.Series(h.loc[imax.to_numpy(), "local"].dt.hour.to_numpy(), index=imax.index)})
out = out.reindex(exp.index).rename_axis("date").reset_index()
out["n_hours_expected"] = exp.to_numpy()
out["n_hours"] = out.n_hours.fillna(0).astype(int)
out["valid"] = (out.n_hours == out.n_hours_expected).astype(int)
out["tmax_f"] = ((out.t_max_k - 273.15) * 9/5 + 32).round(2)
out.loc[out.valid == 0, ["tmax_f", "hour_of_max_local"]] = np.nan
out = out[["date", "tmax_f", "hour_of_max_local", "n_hours", "n_hours_expected", "valid"]]
out["hour_of_max_local"] = out.hour_of_max_local.astype("Int64")
out.to_csv(OUT/"fairbanks_daily_max.csv", index=False)
print(f"\nlocal days {len(out)} ({out.date.min()} -> {out.date.max()}), valid {out.valid.sum()}; invalid:",
      out.loc[out.valid == 0, "date"].tolist())
print("typical hour of max:", out.hour_of_max_local.mode().iloc[0],
      "| hottest:", out.loc[out.tmax_f.idxmax(), "date"], out.tmax_f.max(),
      "| coldest daily max:", out.loc[out.tmax_f.idxmin(), "date"], out.tmax_f.min())
