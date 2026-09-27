"""
Step 1 · METAR · Inventory raw files (read-only).
Reads each untouched raw IEM ASOS file and records, per station:
rows, first/last timestamp, days covered, and counts of blank or
zero visibility and blank RH. Writes a summary CSV. Changes nothing.

Run from the repo root:  python3 scripts/metar/01_inventory.py
"""
import glob, os
import pandas as pd

RAW = "data/raw/metar"
OUT = "data/processed/metar/metar_inventory.csv"

rows = []
# Phoenix comes from the Step 1b local-time file (raw PHX is in UTC; log D5, Step 1b)
PHOENIX_LOCAL = "data/processed/metar/step01b_phoenix_local/metar_phoenix_local.csv"
for path in sorted(glob.glob(f"{RAW}/metar_*_raw.csv")) + [PHOENIX_LOCAL]:
    city = (os.path.basename(path).replace("metar_", "")
            .replace("_raw.csv", "").replace("_local.csv", ""))
    # Read everything as text so nothing is reinterpreted (blanks stay blank)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for station, g in df.groupby("station"):
        vsby = pd.to_numeric(g["vsby"].replace("", None), errors="coerce")
        rows.append({
            "city": city,
            "station": station,
            "rows": len(g),
            "first_obs_local": g["valid"].min(),
            "last_obs_local": g["valid"].max(),
            "days_with_data": g["valid"].str[:10].nunique(),
            "vsby_blank": int((g["vsby"] == "").sum()),
            "vsby_zero": int((vsby == 0).sum()),
            "vsby_unparseable": int((vsby.isna() & (g["vsby"] != "")).sum()),
            "relh_blank": int((g["relh"] == "").sum()),
            "rows_with_wxcode": int((g["wxcodes"] != "").sum()),
        })

inv = pd.DataFrame(rows)
inv.to_csv(OUT, index=False)
print(inv.to_string(index=False))
print(f"\nTotal rows across all files: {inv['rows'].sum()}")
