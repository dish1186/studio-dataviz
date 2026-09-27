"""
Step 1b · METAR · Phoenix: convert UTC timestamps to local time.
Arizona observes MST (UTC-7) all year, with no daylight saving; IEM's
timezone menu has no America/Phoenix, so PHX was downloaded in UTC (log D5).
local = UTC - 7 hours, fixed. Original UTC time kept as valid_utc.
No rows dropped; all other columns unchanged.

Run from the repo root:  python3 scripts/metar/01b_phoenix_utc_to_local.py
"""
import os
import pandas as pd

RAW = "data/raw/metar/metar_phoenix_raw_utc.csv"
OUT_DIR = "data/processed/metar/step01b_phoenix_local"
OUT = f"{OUT_DIR}/metar_phoenix_local.csv"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(RAW, dtype=str, keep_default_na=False)
utc = pd.to_datetime(df["valid"], format="%Y-%m-%d %H:%M")
local = utc - pd.Timedelta(hours=7)

df.insert(2, "valid_utc", df["valid"])
df["valid"] = local.dt.strftime("%Y-%m-%d %H:%M")
df.to_csv(OUT, index=False)

print(f"rows in {len(df)} -> rows out {len(df)}")
print("first:", df[["valid_utc", "valid"]].iloc[0].tolist())
print("last: ", df[["valid_utc", "valid"]].iloc[-1].tolist())
assert (utc - local == pd.Timedelta(hours=7)).all()
