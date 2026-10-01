"""Tipping points Step 1: where do searches "take off" against felt heat and smoke?

For each city, fits a hinge ("hockey stick") model to monthly Google Trends
searches:   searches = a + b * max(0, x - k)
where x is felt heat (or PM2.5 / visibility) and k is the breakpoint: the level
above which searches start rising. k is found by grid search (least squares),
with a 90% bootstrap interval (1,000 resamples of months, seed 1).

Heat:  x = monthly mean of daily felt-heat max (UTCI, deg F); y = "air conditioner" + "AC".
       Also: actual temperature (gridMET tmax) as x, for thermometer vs body.
Smoke: y = "air purifier"; x = monthly worst day of PM2.5 (city daily mean,
       reference first, low-cost where no reference) and monthly worst day of
       visibility (METAR, miles; lower = hazier, so x = 10 - visibility).
Granularity check: San Francisco weekly air purifier vs weekly worst-day PM2.5.

Absolute vs relative: each city's breakpoint is also expressed as a percentile
of that city's own monthly values (2016-2026). If breakpoints in deg F differ a
lot between cities but their percentiles are similar, the trigger is relative
("hotter than normal here"), not an absolute temperature.

Run from repo root:  python3 scripts/tipping-points/01_breakpoints.py
Reads only processed files. Writes data/processed/tipping-points/step01_*.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

P = Path("data/processed")
OUT = P / "tipping-points"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(1)
N_BOOT = 1000
LAST_FULL_MONTH = "2026-08-01"  # Sept 2026 is partial in Trends

HEAT_FILES = {
    "bakersfield": "bakersfield-ca-heat-search.csv",
    "fresno": "Fresno-Visalia CA-ca-heat-search.csv",
    "brownsville": "Harlingen-Weslaco-Brownsville-McAllen TX-tx-heat-search.csv",
    "sanfrancisco": "San Francisco-Oakland-San Jose CA-ca-heat-search.csv",
    "boston": "boston MA-Manchester-NH-heat-search.csv",
    "detroit": "detroit-mi-heat-search.csv",
    "eugene": "eugene-or-heat-search.csv",
    "fairbanks": "fairbanks-ak-heat-search.csv",
    "losangeles": "losangeles-ca-heat-search.csv",
    "phoenix": "phoenix-az-heat-search.csv",
    "sandiego": "sandiego-ca-heat-search.csv",
}
AIR_FILES = {
    "bakersfield": "bakersfield-ca-air-search.csv",
    "fresno": "fresno-visalia-ca-air-search.csv",
    "brownsville": "Harlingen-Weslaco-Brownsville-McAllen TX-air-search.csv",
    "sanfrancisco": "San Francisco-Oakland-San Jose CA-ca-air-search.csv",
    "boston": "boston-ma-air-search.csv",
    "detroit": "detroit-mi-air-search.csv",
    "eugene": "eugene-or-air-search.csv",
    "fairbanks": "fairbanks-ak-air-search.csv",
    "losangeles": "la-ca-air-search.csv",
    "phoenix": "phoenix-az-air-search.csv",
    "sandiego": "san diego-ca-air-search.csv",
}


def hinge_fit(x, y, grid):
    """Least-squares hinge fit for each k in grid; returns best k, a, b, sse."""
    best = None
    for k in grid:
        h = np.maximum(0, x - k)
        X = np.column_stack([np.ones_like(x), h])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(((y - X @ coef) ** 2).sum())
        if best is None or sse < best[3]:
            best = (float(k), float(coef[0]), float(coef[1]), sse)
    return best


def analyse(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    n = len(x)
    grid = np.linspace(np.percentile(x, 5), np.percentile(x, 90), 120)
    k, a, b, sse = hinge_fit(x, y, grid)
    sst = float(((y - y.mean()) ** 2).sum())
    # straight-line comparison
    X = np.column_stack([np.ones_like(x), x])
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    sse_lin = float(((y - X @ c) ** 2).sum())
    bic = lambda s, p: n * np.log(s / n) + p * np.log(n)
    boots = []
    for _ in range(N_BOOT):
        i = RNG.integers(0, n, n)
        boots.append(hinge_fit(x[i], y[i], grid)[0])
    lo, hi = np.percentile(boots, [5, 95])
    return {
        "n": n, "k": round(k, 2), "k_lo": round(float(lo), 2), "k_hi": round(float(hi), 2),
        "a": round(a, 2), "b": round(b, 3),
        "r2_hinge": round(1 - sse / sst, 3), "r2_linear": round(1 - sse_lin / sst, 3),
        "dbic_hinge_minus_linear": round(bic(sse, 3) - bic(sse_lin, 2), 1),
        "k_percentile": round(float((x < k).mean() * 100), 1),
        "share_months_above_k": round(float((x > k).mean() * 100), 1),
        "points": [[round(float(xi), 2), round(float(yi), 2)] for xi, yi in zip(x, y)],
    }


def monthly(df, col, how):
    s = df.set_index(pd.to_datetime(df["date"]))[col]
    return getattr(s.resample("MS"), how)()


def trends(path, cols):
    t = pd.read_csv(path)
    t["Time"] = pd.to_datetime(t["Time"])
    t = t[t["Time"] <= LAST_FULL_MONTH].set_index("Time")
    return t[cols].sum(axis=1)


def pm_daily(city):
    d = pd.read_csv(P / f"openaq/step05_averages/pm25_{city}_daily.csv")
    d["pm"] = d["ref_mean"].fillna(d["lowcost_mean"])
    return d[["date", "pm"]]


rows, pts = [], {}

# ---------------- heat ----------------
for city, f in HEAT_FILES.items():
    y = trends(P / "google-trends/heat-search" / f, ["air conditioner", "AC"])
    u = pd.read_csv(P / f"utci/final/utci_{city}_daily.csv")
    u = u[u["valid"] == 1]
    tm = pd.read_csv(P / f"gridmet/final/temp_{city}_daily.csv")
    for metric, s in [
        ("felt_heat_f", monthly(u, "utci_max_f", "mean")),
        ("actual_temp_f", monthly(tm, "tmax_f", "mean")),
    ]:
        m = pd.concat([s.rename("x"), y.rename("y")], axis=1, sort=True).dropna()
        r = analyse(m["x"], m["y"])
        pts[f"heat|{metric}|{city}"] = {"points": r.pop("points"),
                                        "months": [d.strftime("%Y-%m") for d in m.index]}
        rows.append({"topic": "heat", "x_metric": metric, "search": "air conditioner + AC",
                     "city": city, **r})
    # year-adjusted sensitivity: divide searches by each year's mean
    s = monthly(u, "utci_max_f", "mean")
    ya = y / y.groupby(y.index.year).transform("mean") * y.mean()
    m = pd.concat([s.rename("x"), ya.rename("y")], axis=1).dropna()
    r = analyse(m["x"], m["y"]); r.pop("points")
    rows.append({"topic": "heat", "x_metric": "felt_heat_f (searches year-adjusted)",
                 "search": "air conditioner + AC", "city": city, **r})

# ---------------- smoke ----------------
for city, f in AIR_FILES.items():
    y = trends(P / "google-trends/air-search" / f, ["air purifier"])
    pm = pm_daily(city)
    v = pd.read_csv(P / f"metar/final/vis_{city}_daily.csv")
    v = v[v["valid_day"] == 1].copy()
    v["haze"] = 10 - v["visibility_mi"].clip(upper=10)
    for metric, s in [
        ("pm25_worst_day", monthly(pm, "pm", "max")),
        ("haze_worst_day_10_minus_vis_mi", monthly(v, "haze", "max")),
    ]:
        m = pd.concat([s.rename("x"), y.rename("y")], axis=1, sort=True).dropna()
        if len(m) < 24:
            continue
        r = analyse(m["x"], m["y"])
        pts[f"smoke|{metric}|{city}"] = {"points": r.pop("points"),
                                         "months": [d.strftime("%Y-%m") for d in m.index]}
        rows.append({"topic": "smoke", "x_metric": metric, "search": "air purifier",
                     "city": city, **r})

# ---------------- SF weekly granularity check ----------------
w = pd.read_csv(P / "google-trends/air-search-weekly/sf_air_purifier_weekly.csv")
w["week_start"] = pd.to_datetime(w["week_start"])
pm = pm_daily("sanfrancisco")
pm["date"] = pd.to_datetime(pm["date"])
# Trends weeks start Sunday
pm["week_start"] = pm["date"] - pd.to_timedelta((pm["date"].dt.dayofweek + 1) % 7, unit="D")
pw = pm.groupby("week_start")["pm"].max()
m = w.set_index("week_start")["calibrated_index"].to_frame("y").join(pw.rename("x")).dropna()
m = m[m.index < "2026-09-21"]
r = analyse(m["x"], m["y"])
pts["smoke|pm25_worst_day_weekly|sanfrancisco"] = {"points": r.pop("points"),
                                                  "months": [d.strftime("%Y-%m-%d") for d in m.index]}
rows.append({"topic": "smoke", "x_metric": "pm25_worst_day (weekly)", "search": "air purifier (weekly)",
             "city": "sanfrancisco", **r})
# same SF, monthly, same 2020+ window, for a like-for-like comparison
y = trends(P / "google-trends/air-search" / AIR_FILES["sanfrancisco"], ["air purifier"])
mm = pd.concat([monthly(pm.assign(date=pm["date"].astype(str)), "pm", "max").rename("x"),
                y.rename("y")], axis=1).dropna()
mm = mm[mm.index >= "2020-01-01"]
r = analyse(mm["x"], mm["y"]); r.pop("points")
rows.append({"topic": "smoke", "x_metric": "pm25_worst_day (monthly, 2020+)", "search": "air purifier",
             "city": "sanfrancisco", **r})

res = pd.DataFrame(rows)
res.to_csv(OUT / "step01_breakpoints.csv", index=False)
(OUT / "step01_points.json").write_text(json.dumps(pts))

pd.set_option("display.width", 200)
print(res[["topic", "x_metric", "city", "n", "k", "k_lo", "k_hi", "k_percentile",
           "r2_hinge", "r2_linear", "dbic_hinge_minus_linear"]].to_string(index=False))
for metric in ["felt_heat_f", "actual_temp_f"]:
    h = res[(res.topic == "heat") & (res.x_metric == metric) & (res.city != "fairbanks")]
    print(f"\n{metric} breakpoints, 10 cities excl. Fairbanks: "
          f"deg F range {h.k.min()}-{h.k.max()} (SD {h.k.std():.1f}); "
          f"percentile range {h.k_percentile.min()}-{h.k_percentile.max()} (SD {h.k_percentile.std():.1f})")

# ---------------- within-city "hotter than normal here" test ----------------
# Remove each city's usual month-of-year level and each year's level from the
# searches, then ask: in May-September, do months that felt hotter than the
# 1991-2020 normal for those dates have more searches than usual?
an_rows = []
for city, f in HEAT_FILES.items():
    y = trends(P / "google-trends/heat-search" / f, ["air conditioner", "AC"])
    u = pd.read_csv(P / f"utci/final/utci_{city}_daily.csv")
    u = u[u["valid"] == 1]
    m = pd.concat([monthly(u, "anomaly_f", "mean").rename("anom"),
                   monthly(u, "abnormally_high", "sum").rename("hot_days"),
                   y.rename("y")], axis=1, sort=True).dropna()
    m["resid"] = (m["y"] - m.groupby(m.index.month)["y"].transform("mean")
                  - m.groupby(m.index.year)["y"].transform("mean") + m["y"].mean())
    s = m[m.index.month.isin([5, 6, 7, 8, 9])]
    r = float(np.corrcoef(s["anom"], s["resid"])[0, 1])
    boots = []
    for _ in range(N_BOOT):
        i = RNG.integers(0, len(s), len(s))
        boots.append(np.corrcoef(s["anom"].values[i], s["resid"].values[i])[0, 1])
    lo, hi = np.nanpercentile(boots, [5, 95])
    an_rows.append({"city": city, "n_summer_months": len(s), "r_anomaly_vs_extra_searches": round(r, 2),
                    "r_lo": round(float(lo), 2), "r_hi": round(float(hi), 2)})
an = pd.DataFrame(an_rows)
an.to_csv(OUT / "step01_anomaly_test.csv", index=False)
print("\nSummer months: felt-heat anomaly vs searches above the usual seasonal level")
print(an.to_string(index=False))
