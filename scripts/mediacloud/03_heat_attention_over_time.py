# Media Cloud Step 3 · "attention over time" for heat news (heat wave / heat advisory) mentioning each of 12 study cities.
# Same method, collections and dates as Step 1 (scripts/mediacloud/01_attention_over_time.py); only the query and folders differ.
#
# Method (Gina, 2026-09-27; heat version): for each city, in its state's "State & Local" collection, the query
#   ("heat wave" OR "heat advisory") AND "<city>"
# from 2016-01-01 to 2026-09-25, daily story counts (Media Cloud "Attention over time", /api/search/count-over-time).
# Quoted phrases and parentheses follow Media Cloud's query syntax (same form as city-selection Step 6).
# The collection's current source count is looked up at run time.
# Outputs:
#   data/raw/heat-media/json/<slug>_heat_count_over_time.json   raw API responses, exactly as received
#   data/raw/heat-media/json/<slug>_collection.json        raw collection record (source count)
#   data/processed/heat-media/heat_media_<slug>.csv  one row per day (flattened; values as returned)
#   data/processed/heat-media/queries.csv                    one row per city: query, collection, sources, totals
# CSVs in processed and JSON in raw, following Gina's rule for the air-quality files (Media Cloud Step 1).
# If the full-period request fails, the period is requested one calendar year at a time and the days joined.
# Run from the repo root:  MEDIACLOUD_API_KEY=... python3 scripts/mediacloud/03_heat_attention_over_time.py
import csv, json, os, subprocess, sys, time, urllib.parse

KEY = os.environ["MEDIACLOUD_API_KEY"]
START, END = "2016-01-01", "2026-09-25"
RAW = "data/raw/heat-media/json"; OUT = "data/processed/heat-media"
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)
CITIES = [  # rank order as listed by Gina; slug, city, state, collection id (State & Local)
    ("losangeles", "Los Angeles", "California", 38380550),
    ("phoenix", "Phoenix", "Arizona", 38381317),
    ("sandiego", "San Diego", "California", 38380550),
    ("detroit", "Detroit", "Michigan", 38381374),
    ("bakersfield", "Bakersfield", "California", 38380550),
    ("sanfrancisco", "San Francisco", "California", 38380550),
    ("fresno", "Fresno", "California", 38380550),
    ("boston", "Boston", "Massachusetts", 38381372),
    ("eugene", "Eugene", "Oregon", 38381398),
    ("fairbanks", "Fairbanks", "Alaska", 38381315),
    ("brownsville", "Brownsville", "Texas", 38381323),
    ("annarbor", "Ann Arbor", "Michigan", 38381374),
]

def get(url, tries=6):
    code = ""
    for t in range(tries):
        out = subprocess.run(["curl", "-s", "-m", "300", "-w", "\n%{http_code}", "-H", "Authorization: Token " + KEY, url],
                             capture_output=True, text=True).stdout
        body, _, code = out.rpartition("\n")
        if code == "200":
            try:
                j = json.loads(body)
                if isinstance(j, dict) and j.get("status") == "error": raise ValueError(j.get("note"))
                time.sleep(10); return j
            except ValueError as e:
                print(f"    error: {e}; retry {t + 1}", flush=True)
        else:
            print(f"    HTTP {code or 'timeout'}; retry {t + 1}", flush=True)
        time.sleep(45)
    raise RuntimeError(f"failed after {tries} tries (last HTTP {code})")

def count_over_time(q, cs, start, end):
    return get("https://search.mediacloud.org/api/search/count-over-time?" + urllib.parse.urlencode(
        dict(q=q, start=start, end=end, cs=cs, platform="onlinenews-mediacloud")))

summary = []
for n, (slug, city, state, cs) in enumerate(CITIES, 1):
    q = f'("heat wave" OR "heat advisory") AND "{city}"'
    print(f"[{n}] {city}: {q} in {cs}", flush=True)
    col = get(f"https://search.mediacloud.org/api/sources/collections/{cs}/")
    json.dump(col, open(f"{RAW}/{slug}_collection.json", "w"), indent=1)
    try:
        parts = [dict(start=START, end=END, response=count_over_time(q, cs, START, END))]
    except RuntimeError as e:
        print(f"  full period failed ({e}); requesting by year", flush=True)
        parts = []
        for y in range(int(START[:4]), int(END[:4]) + 1):
            a, b = max(f"{y}-01-01", START), min(f"{y}-12-31", END)
            parts.append(dict(start=a, end=b, response=count_over_time(q, cs, a, b)))
    json.dump(dict(query=q, collection_id=cs, retrieved_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), parts=parts),
              open(f"{RAW}/{slug}_heat_count_over_time.json", "w"))
    days = {}
    for p in parts:
        for d in p["response"]["count_over_time"]["counts"]:
            days[d["date"][:10]] = d
    rows = [dict(date=k, stories=days[k].get("count"), total_stories_in_collection=days[k].get("total_count"), ratio=days[k].get("ratio"))
            for k in sorted(days) if START <= k <= END]
    with open(f"{OUT}/heat_media_{slug}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "stories", "total_stories_in_collection", "ratio"]); w.writeheader(); w.writerows(rows)
    tot = sum(r["stories"] or 0 for r in rows)
    summary.append({"#": n, "city": city, "state": state, "query": q, "collection_id": cs, "collection_name": col.get("name"),
        "sources_in_collection": col.get("source_count"), "start": START, "end": END, "days_returned": len(rows),
        "first_day": rows[0]["date"] if rows else "", "last_day": rows[-1]["date"] if rows else "",
        "days_with_stories": sum(1 for r in rows if (r["stories"] or 0) > 0), "total_stories": tot,
        "requests": "full period" if len(parts) == 1 else "by year", "csv": f"heat_media_{slug}.csv"})
    print(f"  {len(rows)} days, {tot} stories, sources {col.get('source_count')}", flush=True)
with open(f"{OUT}/queries.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
print("DONE", flush=True)
