# Google Trends Step 4 · write trends_sources.csv for the air-quality search files (same approach as Step 1).
# The raw CSVs are copied unchanged (Rule 2). Geography levels follow the heat-search files (Gina, 2026-09-27):
# same 6 states, 4 metro areas and 7 cities. Settings from Gina: search terms, All categories, Web Search, downloaded 2026-09-27.
# Run from the repo root: python3 scripts/google-trends/03_air_sources_table.py
import csv, os
D = "data/raw/google-trends/air-search"
GEO = {
    "alaska-air-search.csv": ("Alaska", "US state"),
    "az-air-search.csv": ("Arizona", "US state"),
    "ca-air-search.csv": ("California", "US state"),
    "michigan-air-search.csv": ("Michigan", "US state"),
    "oregon-air-search.csv": ("Oregon", "US state"),
    "tx-air-search.csv": ("Texas", "US state"),
    "Harlingen-Weslaco-Brownsville-McAllen TX-air-search.csv": ("Harlingen-Weslaco-Brownsville-McAllen TX", "metro area"),
    "San Francisco-Oakland-San Jose CA-ca-air-search.csv": ("San Francisco-Oakland-San Jose CA", "metro area"),
    "fresno-visalia-ca-air-search.csv": ("Fresno-Visalia CA", "metro area"),
    "boston-ma-air-search.csv": ("Boston MA-Manchester NH", "metro area"),
    "bakersfield-ca-air-search.csv": ("Bakersfield, CA", "city (per Gina)"),
    "detroit-mi-air-search.csv": ("Detroit, MI", "city (per Gina)"),
    "eugene-or-air-search.csv": ("Eugene, OR", "city (per Gina)"),
    "fairbanks-ak-air-search.csv": ("Fairbanks, AK", "city (per Gina)"),
    "la-ca-air-search.csv": ("Los Angeles, CA", "city (per Gina)"),
    "phoenix-az-air-search.csv": ("Phoenix, AZ", "city (per Gina)"),
    "san diego-ca-air-search.csv": ("San Diego, CA", "city (per Gina)"),
}
rows = []
for f in sorted(os.listdir(D)):
    if not f.endswith("-air-search.csv"): continue
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
