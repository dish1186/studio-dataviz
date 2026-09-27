"""
Step 2 · METAR · Throw out broken visibility readings.
For each raw city file: drop reports whose visibility is blank or exactly 0 miles.
Kept rows are copied unchanged (read and written as text).
Dropped rows are saved separately with a reason, for audit.

Run from the repo root:  python3 scripts/metar/02_drop_broken.py
"""
import glob, os
import pandas as pd

RAW = "data/raw/metar"
OUT = "data/processed/metar/step02_valid"
os.makedirs(OUT, exist_ok=True)

summary = []
for path in sorted(glob.glob(f"{RAW}/metar_*_raw.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_raw.csv", "")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)   # everything as text

    vsby = pd.to_numeric(df["vsby"].replace("", None), errors="coerce")
    is_blank = df["vsby"] == ""
    is_zero = vsby == 0                                         # exactly 0.00 only

    reason = pd.Series("", index=df.index)
    reason[is_blank] = "blank visibility"
    reason[is_zero] = "zero visibility (sensor glitch)"
    drop = is_blank | is_zero

    kept = df[~drop]
    removed = df[drop].assign(removed_reason=reason[drop])

    kept.to_csv(f"{OUT}/metar_{city}_valid.csv", index=False)
    removed.to_csv(f"{OUT}/metar_{city}_removed.csv", index=False)

    for station in sorted(df["station"].unique()):
        s = df["station"] == station
        summary.append({
            "city": city, "station": station,
            "rows_in": int(s.sum()),
            "removed_blank": int((s & is_blank).sum()),
            "removed_zero": int((s & is_zero).sum()),
            "rows_out": int((s & ~drop).sum()),
        })

summ = pd.DataFrame(summary)
summ["pct_removed"] = (100 * (summ.rows_in - summ.rows_out) / summ.rows_in).round(3)
summ.to_csv(f"{OUT}/step02_summary.csv", index=False)
print(summ.to_string(index=False))
t = summ[["rows_in", "removed_blank", "removed_zero", "rows_out"]].sum()
print(f"\nTOTAL in {t.rows_in} | blank {t.removed_blank} | zero {t.removed_zero} | out {t.rows_out}")
# Check: every row is either kept or removed
assert t.rows_in == t.rows_out + t.removed_blank + t.removed_zero
