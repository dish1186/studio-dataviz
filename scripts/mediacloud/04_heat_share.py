# Media Cloud Step 4 · heat share: heat stories as a share of all stories mentioning the city.
#
# No new queries. Uses the denominator already downloaded in Media Cloud Step 2 (city_stories: stories mentioning
# "<city>" in the same state collection and dates), from data/processed/mediacloud-attention/mediacloud_attention_<city>.csv.
# Adds two columns to each data/processed/heat-media/heat_media_<city>.csv (Gina, 2026-09-27):
#   city_stories = stories that day mentioning "<city>" (copied from Step 2)
#   heat_share   = stories / city_stories (numerator = Step 3's heat stories); blank when city_stories is 0
# Existing columns unchanged. Checks: same dates as Step 2; city_stories >= heat stories every day.
# Run from the repo root: python3 scripts/mediacloud/04_heat_share.py   (local files only)
import csv, sys
H = "data/processed/heat-media"; A = "data/processed/mediacloud-attention"
Q = list(csv.DictReader(open(f"{H}/queries.csv")))
for q in Q:
    slug = q["csv"].replace("heat_media_", "").replace(".csv", "")
    den = {r["date"]: int(r["city_stories"]) for r in csv.DictReader(open(f"{A}/mediacloud_attention_{slug}.csv"))}
    fn = f"{H}/{q['csv']}"; rows = list(csv.DictReader(open(fn)))
    if set(den) != {r["date"] for r in rows}: sys.exit(f"STOP: {slug}: dates differ from Step 2")
    for r in rows:
        c = den[r["date"]]; s = int(r["stories"])
        if c < s: sys.exit(f"STOP: {slug} {r['date']}: city_stories {c} < heat stories {s}")
        r["city_stories"] = c; r["heat_share"] = "" if c == 0 else s / c
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "stories", "total_stories_in_collection", "ratio", "city_stories", "heat_share"]); w.writeheader(); w.writerows(rows)
    tc = sum(den.values()); q["total_city_stories"] = tc; q["heat_share_overall"] = round(int(q["total_stories"]) / tc, 5) if tc else ""
    print(f"{q['city']:14} heat {int(q['total_stories']):6} / city {tc:9} = {100*q['heat_share_overall']:.2f}%")
with open(f"{H}/queries.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(Q[0])); w.writeheader(); w.writerows(Q)
print("DONE")
