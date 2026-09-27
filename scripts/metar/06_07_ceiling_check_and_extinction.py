"""
Steps 6 + 7 · METAR · Check the 10-mile ceiling, then convert to light extinction.
Step 6: confirm no visibility > 10 mi (stop if any; don't cap silently) and
        count hours at the 10-mi ceiling.
Step 7: visual range km = miles x 1.609344; extinction (1/km) = 3.912 / km
        (Koschmieder 1924, 2% contrast threshold; see docs/references.md, log M1).
Existing columns are unchanged; vsby_km and extinction_km are added.

Run from the repo root:  python3 scripts/metar/06_07_ceiling_check_and_extinction.py
"""
import glob, os, sys
import pandas as pd

IN = "data/processed/metar/step05_dry"
OUT = "data/processed/metar/step07_extinction"
MI_TO_KM = 1.609344
K = 3.912                     # ln(1/0.02)
CEILING_MI = 10.0

files = sorted(glob.glob(f"{IN}/metar_*_dry.csv"))

# ---- Step 6: ceiling check across ALL files before writing anything ----
over = {}
for path in files:
    v = pd.to_numeric(pd.read_csv(path, dtype=str, keep_default_na=False)["vsby"])
    if (v > CEILING_MI).any():
        over[os.path.basename(path)] = int((v > CEILING_MI).sum())
if over:
    print("STOP: visibility values above 10 mi found; nothing written.", over)
    sys.exit(1)

# ---- Step 7: convert ----
os.makedirs(OUT, exist_ok=True)
summary = []
for path in files:
    city = os.path.basename(path).replace("metar_", "").replace("_dry.csv", "")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    mi = pd.to_numeric(df["vsby"])
    df["vsby_km"] = mi * MI_TO_KM
    df["extinction_km"] = K / df["vsby_km"]
    df.to_csv(f"{OUT}/metar_{city}_extinction.csv", index=False)

    for station, g in df.groupby("station"):
        m = pd.to_numeric(g["vsby"])
        summary.append({
            "city": city, "station": station, "hours": len(g),
            "vsby_min_mi": m.min(), "vsby_max_mi": m.max(),
            "hours_at_10mi": int((m == CEILING_MI).sum()),
            "pct_at_10mi": round(100 * (m == CEILING_MI).mean(), 1),
            "ext_min": round(g["extinction_km"].min(), 4),
            "ext_max": round(g["extinction_km"].max(), 4),
            "ext_mean": round(g["extinction_km"].mean(), 4),
        })

summ = pd.DataFrame(summary)
summ.to_csv(f"{OUT}/step07_summary.csv", index=False)
print("Step 6: no values above 10 mi.\n")
print(summ.to_string(index=False))
print(f"\nTOTAL hours converted: {summ.hours.sum()}")
