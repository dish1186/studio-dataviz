"""
Step 5b · METAR · Remove "wet" hours (water, not haze).
Decisions approved by Dish (see log, Step 5a/5b):
 1-2. Remove if any report in the hour has a water phenomenon at the airport:
      FG, BR, RA, DZ, SN, SG, IC, PL, GR, GS, UP (any intensity/descriptor,
      e.g. FZFG, BCFG, TSRA, FZRA, BLSN).
 3.   Also remove vicinity fog (VCFG).
 4-5. Keep TS/VCTS without precip, HZ, FU, DU, SA, SS, SQ, FC.
 6.   Remove if the hour's highest RH >= 90%.
 7.   Keep hours with blank RH; flag them rh_missing = 1.

Run from the repo root:  python3 scripts/metar/05b_remove_water.py
"""
import glob, os
import pandas as pd

IN = "data/processed/metar/step04_daytime"
OUT = "data/processed/metar/step05_dry"
os.makedirs(OUT, exist_ok=True)

WET = {"FG", "BR", "RA", "DZ", "SN", "SG", "IC", "PL", "GR", "GS", "UP"}
VICINITY_WET = {"FG"}
DESCRIPTORS = {"MI", "PR", "BC", "DR", "BL", "SH", "TS", "FZ"}
RH_LIMIT = 90

def wet_codes(codes):
    """Return the tokens in this hour's codes that make it 'wet' (empty = dry)."""
    hits = []
    for tok in codes.split():
        t = tok.lstrip("+-")
        vicinity = t.startswith("VC")
        if vicinity:
            t = t[2:]
        core = {t[i:i+2] for i in range(0, len(t), 2)} - DESCRIPTORS
        if core & (VICINITY_WET if vicinity else WET):
            hits.append(tok)
    return " ".join(sorted(hits))

summary = []
for path in sorted(glob.glob(f"{IN}/metar_*_daytime.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_daytime.csv", "")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    wet_tok = df["wx_any_in_hour"].map(wet_codes)
    relh_max = pd.to_numeric(df["relh_max_in_hour"].replace("", None), errors="coerce")
    is_wet_code = wet_tok != ""
    is_humid = relh_max >= RH_LIMIT                 # blank RH -> False (kept)
    drop = is_wet_code | is_humid

    reason = pd.Series("", index=df.index)
    reason[is_wet_code] = "wet code: " + wet_tok[is_wet_code]
    reason[is_humid & ~is_wet_code] = "RH >= 90"
    reason[is_humid & is_wet_code] += " + RH >= 90"

    kept = df[~drop].copy()
    kept["rh_missing"] = relh_max[~drop].isna().astype(int)
    kept.to_csv(f"{OUT}/metar_{city}_dry.csv", index=False)
    df[drop].assign(removed_reason=reason[drop]).to_csv(
        f"{OUT}/metar_{city}_removed.csv", index=False)

    for station in sorted(df["station"].unique()):
        s = df["station"] == station
        summary.append({
            "city": city, "station": station,
            "hours_in": int(s.sum()),
            "removed_code_only": int((s & is_wet_code & ~is_humid).sum()),
            "removed_rh_only": int((s & is_humid & ~is_wet_code).sum()),
            "removed_both": int((s & is_wet_code & is_humid).sum()),
            "hours_out": int((s & ~drop).sum()),
            "kept_with_rh_missing": int((s & ~drop & relh_max.isna()).sum()),
        })

summ = pd.DataFrame(summary)
summ["pct_removed"] = (100 * (summ.hours_in - summ.hours_out) / summ.hours_in).round(1)
summ.to_csv(f"{OUT}/step05_summary.csv", index=False)
print(summ.to_string(index=False))
t = summ.drop(columns=["city", "station", "pct_removed"]).sum()
print(f"\nTOTAL in {t.hours_in} | removed {t.hours_in - t.hours_out} | out {t.hours_out}")
assert t.hours_in == t.hours_out + t.removed_code_only + t.removed_rh_only + t.removed_both
