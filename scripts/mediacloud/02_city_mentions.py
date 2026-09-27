# Media Cloud Step 2 · denominator: all stories mentioning each city, and the air-pollution share of them.
#
# For each of the 12 cities in Step 1, in the SAME state "State & Local" collection and dates (2016-01-01 to 2026-09-25),
# query "<city>" (the same quoted city phrase as in the Step 1 query, so every Step 1 story is also counted here)
# with /api/search/count-over-time. Then add two columns to each processed CSV (Gina, 2026-09-27):
#   city_stories = stories that day mentioning "<city>" (denominator)
#   air_share    = stories / city_stories (numerator = Step 1's air-pollution stories); blank when city_stories is 0
# Existing columns are not changed. Checks: same dates as Step 1; city_stories >= stories on every day.
# Raw responses: data/raw/mediacloud-attention/json/<slug>_city_count_over_time.json (exactly as received).
# Run from the repo root:  MEDIACLOUD_API_KEY=... python3 scripts/mediacloud/02_city_mentions.py
import csv, json, os, subprocess, sys, time, urllib.parse

KEY = os.environ["MEDIACLOUD_API_KEY"]
START, END = "2016-01-01", "2026-09-25"
RAW = "data/raw/mediacloud-attention/json"; OUT = "data/processed/mediacloud-attention"

def get(url, tries=6):
    code = ""
    for t in range(tries):
        out = subprocess.run(["curl", "-s", "-m", "300", "-w", "\n%{http_code}", "-H", "Authorization: Token " + KEY, url],
                             capture_output=True, text=True).stdout
        body, _, code = out.rpartition("\n")
        if code == "200":
            j = json.loads(body)
            if not (isinstance(j, dict) and j.get("status") == "error"):
                time.sleep(10); return j
            print(f"    error: {j.get('note')}; retry {t + 1}", flush=True)
        else:
            print(f"    HTTP {code or 'timeout'}; retry {t + 1}", flush=True)
        time.sleep(45)
    sys.exit(f"STOP: {url} failed after {tries} tries")

Q = list(csv.DictReader(open(f"{OUT}/queries.csv")))
for q in Q:
    slug = q["csv"].replace("mediacloud_attention_", "").replace(".csv", "")
    cq = f'"{q["city"]}"'
    print(f"[{q['#']}] {q['city']}: {cq} in {q['collection_id']}", flush=True)
    r = get("https://search.mediacloud.org/api/search/count-over-time?" + urllib.parse.urlencode(
        dict(q=cq, start=START, end=END, cs=q["collection_id"], platform="onlinenews-mediacloud")))
    json.dump(dict(query=cq, collection_id=int(q["collection_id"]), retrieved_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   parts=[dict(start=START, end=END, response=r)]), open(f"{RAW}/{slug}_city_count_over_time.json", "w"))
    city = {d["date"][:10]: d["count"] for d in r["count_over_time"]["counts"]}
    fn = f"{OUT}/{q['csv']}"; rows = list(csv.DictReader(open(fn)))
    if set(city) != {x["date"] for x in rows}:
        sys.exit(f"STOP: {slug}: dates differ between the air-pollution and city queries ({len(city)} vs {len(rows)})")
    for x in rows:
        c = city[x["date"]]; s = int(x["stories"])
        if c < s: sys.exit(f"STOP: {slug} {x['date']}: city_stories {c} < stories {s}")
        x["city_stories"] = c; x["air_share"] = "" if c == 0 else s / c
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "stories", "total_stories_in_collection", "ratio", "city_stories", "air_share"]); w.writeheader(); w.writerows(rows)
    q["city_query"] = cq; q["total_city_stories"] = sum(int(x["city_stories"]) for x in rows)
    q["days_city_stories_0"] = sum(1 for x in rows if int(x["city_stories"]) == 0)
    q["air_share_overall"] = round(int(q["total_stories"]) / q["total_city_stories"], 5) if q["total_city_stories"] else ""
    print(f"  city stories {q['total_city_stories']}, days with 0 {q['days_city_stories_0']}, overall air share {q['air_share_overall']}", flush=True)
with open(f"{OUT}/queries.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(Q[0])); w.writeheader(); w.writerows(Q)
print("DONE", flush=True)
