"""
Step 4 · gridMET · Check raw ClimateEngine downloads (READ-ONLY, changes no data).
Input : data/raw/gridmet/climateengine/gridmet_tmax_<city>_{2016-2026,1991-2020}.csv
Output: data/processed/gridmet/step04_raw_check/raw_check.csv  (1 row per file)
Expected ranges: study 2016-01-01..2026-09-24 (Decision D4), baseline 1991-01-01..2020-12-31.
Run from repo root:  python3 scripts/gridmet/04_raw_check.py
"""
import glob, os, re
import pandas as pd

RAW = "data/raw/gridmet/climateengine"
OUT = "data/processed/gridmet/step04_raw_check"
os.makedirs(OUT, exist_ok=True)
EXPECT = {"2016-2026": ("2016-01-01", "2026-09-24"), "1991-2020": ("1991-01-01", "2020-12-31")}
PLAUSIBLE = (-60, 130)   # deg F; outside this = impossible for these cities
# Census GEOIDs from Step 3 (step03_summary.csv); ClimateEngine writes the region ID into the header
EXPECTED_GEOID = {
    "bakersfield": "0603526", "fresno": "0627000", "losangeles": "0644000",
    "sanfrancisco": "0667000", "eugene": "4123850", "brownsville": "4810768",
    "detroit": "2622000", "pittsburgh": "4261000", "boston": "2507000",
}

def read(path):
    with open(path, encoding="utf-8-sig") as f:
        header = f.readline().strip()
    df = pd.read_csv(path, skiprows=1, header=None, names=["date", "tmax_f"],
                     dtype={"date": str}, encoding="utf-8-sig")
    return header, df

rows, series = [], {}
for path in sorted(glob.glob(f"{RAW}/gridmet_tmax_*_*.csv")):
    city, period = re.match(r".*gridmet_tmax_(\w+?)_(\d{4}-\d{4})\.csv", path).groups()
    header, df = read(path)
    dates = pd.to_datetime(df["date"], errors="coerce")
    start, end = EXPECT[period]
    full = pd.date_range(start, end, freq="D")
    vals = pd.to_numeric(df["tmax_f"], errors="coerce")
    series[(city, period)] = pd.Series(vals.values, index=dates)
    rows.append({
        "file": os.path.basename(path), "city": city, "period": period,
        "header": header.lstrip(",").strip('"'),
        "geoid_in_header": re.search(r"at (\d+),", header).group(1),
        "geoid_matches_city": re.search(r"at (\d+),", header).group(1) == EXPECTED_GEOID[city],
        "header_dates_match": f"{start} to {end}" in header,
        "first_date": dates.min().date(), "last_date": dates.max().date(),
        "n_rows": len(df), "n_expected_days": len(full),
        "missing_days": len(full.difference(dates)),
        "extra_days_outside_range": int((~dates.isin(full)).sum()),
        "duplicate_dates": int(dates.duplicated().sum()),
        "bad_dates": int(dates.isna().sum()),
        "blank_or_nonnumeric": int(vals.isna().sum()),
        "implausible": int(((vals < PLAUSIBLE[0]) | (vals > PLAUSIBLE[1])).sum()),
        "min_f": vals.min(), "max_f": vals.max(), "mean_f": round(vals.mean(), 2),
    })

out = pd.DataFrame(rows)
# Overlap check: 2016-01-01..2020-12-31 appears in both pulls -> values should be identical
out["overlap_2016_2020_maxdiff_f"] = None
for city in out["city"].unique():
    if (city, "2016-2026") in series and (city, "1991-2020") in series:
        a, b = series[(city, "2016-2026")], series[(city, "1991-2020")]
        common = a.index.intersection(b.index)
        diff = (a[common] - b[common]).abs().max()
        out.loc[out["city"] == city, "overlap_2016_2020_maxdiff_f"] = round(float(diff), 4)

out.to_csv(f"{OUT}/raw_check.csv", index=False)
print(out.T.to_string())
