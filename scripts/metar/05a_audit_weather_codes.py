"""
Step 5a · METAR · Audit weather codes and humidity (read-only).
Counts, per city, how many daytime station-hours contain each weather code
(as written, and by phenomenon with intensity/vicinity/descriptor stripped),
and how many hours have RH >= 90% or blank RH. Removes nothing.
Uses wx_any_in_hour (all codes reported during the hour, from Step 3).

Run from the repo root:  python3 scripts/metar/05a_audit_weather_codes.py
"""
import glob, os
from collections import Counter
import pandas as pd

IN = "data/processed/metar/step04_daytime"
OUT = "data/processed/metar/step05a_wx_audit"
os.makedirs(OUT, exist_ok=True)

DESCRIPTORS = {"MI", "PR", "BC", "DR", "BL", "SH", "TS", "FZ"}
NAMES = {"RA": "rain", "DZ": "drizzle", "SN": "snow", "SG": "snow grains",
         "IC": "ice crystals", "PL": "ice pellets", "GR": "hail", "GS": "small hail",
         "UP": "unknown precip", "BR": "mist", "FG": "fog", "FU": "smoke",
         "VA": "volcanic ash", "DU": "dust", "SA": "sand", "HZ": "haze",
         "PY": "spray", "PO": "dust whirls", "SQ": "squalls", "FC": "funnel cloud",
         "SS": "sandstorm", "DS": "duststorm"}

def phenomena(token):
    """'-SHRA' -> ({'RA'}, vicinity=False); 'VCFG' -> ({'FG'}, True); 'TS' -> ({'TS'}, False)"""
    t = token.lstrip("+-")
    vicinity = t.startswith("VC")
    if vicinity:
        t = t[2:]
    chunks = [t[i:i+2] for i in range(0, len(t), 2)]
    core = {c for c in chunks if c not in DESCRIPTORS}
    if not core:                        # e.g. bare 'TS' (thunder, no precip)
        core = set(chunks)
    return core, vicinity

code_rows, phen_rows, rh_rows = [], [], []
for path in sorted(glob.glob(f"{IN}/metar_*_daytime.csv")):
    city = os.path.basename(path).replace("metar_", "").replace("_daytime.csv", "")
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    token_hours, phen_at, phen_vc = Counter(), Counter(), Counter()
    for codes in df["wx_any_in_hour"]:
        tokens = set(codes.split())
        token_hours.update(tokens)
        at, vc = set(), set()
        for tok in tokens:
            core, vicinity = phenomena(tok)
            (vc if vicinity else at).update(core)
        phen_at.update(at)
        phen_vc.update(vc - at)          # vicinity-only: not also reported at the airport

    for tok, n in token_hours.items():
        code_rows.append({"city": city, "code": tok, "hours": n})
    for p in sorted(set(phen_at) | set(phen_vc)):
        phen_rows.append({"city": city, "phenomenon": p, "name": NAMES.get(p, p),
                          "hours_at_airport": phen_at[p], "hours_vicinity_only": phen_vc[p]})

    relh = pd.to_numeric(df["relh"].replace("", None), errors="coerce")
    relh_max = pd.to_numeric(df["relh_max_in_hour"].replace("", None), errors="coerce")
    for station in sorted(df["station"].unique()):
        s = df["station"] == station
        rh_rows.append({
            "city": city, "station": station, "daytime_hours": int(s.sum()),
            "hours_any_wxcode": int((s & (df["wx_any_in_hour"] != "")).sum()),
            "rh_ge90_picked_report": int((s & (relh >= 90)).sum()),
            "rh_ge90_any_report_in_hour": int((s & (relh_max >= 90)).sum()),
            "rh_blank_picked_report": int((s & relh.isna()).sum()),
            "rh_blank_whole_hour": int((s & relh_max.isna()).sum()),
        })

codes = pd.DataFrame(code_rows).sort_values(["city", "hours"], ascending=[True, False])
phen = pd.DataFrame(phen_rows)
rh = pd.DataFrame(rh_rows)
codes.to_csv(f"{OUT}/wxcode_counts.csv", index=False)
phen.to_csv(f"{OUT}/phenomenon_counts.csv", index=False)
rh.to_csv(f"{OUT}/rh_summary.csv", index=False)

print("HOURS WITH EACH PHENOMENON AT THE AIRPORT (vicinity-only in brackets)\n")
pv = phen.pivot(index="name", columns="city", values="hours_at_airport").fillna(0).astype(int)
vc = phen.pivot(index="name", columns="city", values="hours_vicinity_only").fillna(0).astype(int)
print((pv.astype(str) + " [" + vc.astype(str) + "]").to_string())
print("\nHUMIDITY\n")
print(rh.to_string(index=False))
