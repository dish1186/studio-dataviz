# Google Trends Step 1 · write trends_sources.csv: one row per raw Google Trends file, with source, geography,
# date range and search settings. The raw CSVs themselves are copied unchanged (Rule 2).
# Geography and settings come from Gina (file names + chat, 2026-09-27); dates and terms are read from each file.
# Run from the repo root: python3 scripts/google-trends/01_sources_table.py
import csv, os
D = "data/raw/google-trends/heat-search"
GEO = {  # file -> (geography as selected in Google Trends, level)
    "az-heat-search.csv": ("Arizona", "US state"),
    "ca-heat-search.csv": ("California", "US state"),
    "alaska-heat-search.csv": ("Alaska", "US state"),
    "michigan-heat-search.csv": ("Michigan", "US state"),
    "or-heat-search.csv": ("Oregon", "US state"),
    "texas-heat-search.csv": ("Texas", "US state"),
    "Fresno-Visalia CA-ca-heat-search.csv": ("Fresno-Visalia CA", "metro area"),
    "Harlingen-Weslaco-Brownsville-McAllen TX-tx-heat-search.csv": ("Harlingen-Weslaco-Brownsville-McAllen TX", "metro area"),
    "San Francisco-Oakland-San Jose CA-ca-heat-search.csv": ("San Francisco-Oakland-San Jose CA", "metro area"),
    "boston MA-Manchester-NH-heat-search.csv": ("Boston MA-Manchester NH", "metro area"),   # added 2026-09-27 (Google Trends Step 2)
    "bakersfield-ca-heat-search.csv": ("Bakersfield, CA", "city (per Gina)"),
    "detroit-mi-heat-search.csv": ("Detroit, MI", "city (per Gina)"),
    "eugene-or-heat-search.csv": ("Eugene, OR", "city (per Gina)"),
    "fairbanks-ak-heat-search.csv": ("Fairbanks, AK", "city (per Gina)"),
    "losangeles-ca-heat-search.csv": ("Los Angeles, CA", "city (per Gina)"),
    "phoenix-az-heat-search.csv": ("Phoenix, AZ", "city (per Gina)"),
    "sandiego-ca-heat-search.csv": ("San Diego, CA", "city (per Gina)"),
}
rows = []
for f in sorted(os.listdir(D)):
    if not f.endswith("-heat-search.csv"): continue
    R = list(csv.reader(open(f"{D}/{f}")))
    geo, lvl = GEO[f]
    rows.append(dict(file=f, source="Google Trends (https://trends.google.com)", geography_selected=geo, geography_level=lvl,
        country="United States", first_month=R[1][0][:7], last_month=R[-1][0][:7], n_months=len(R) - 1, time_resolution="monthly",
        search_terms="; ".join(R[0][1:]), term_type="search terms (not topics)", category="All categories", search_type="Web Search",
        downloaded="2026-09-27", downloaded_by="Gina",
        values="Relative search interest 0-100, scaled within this file (100 = highest month for any of its terms); not search counts; not comparable across files",
        last_month_partial="yes: 2026-09 covers only the days up to the download date"))
assert len(rows) == len(GEO)
with open(f"{D}/trends_sources.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows), "rows")
