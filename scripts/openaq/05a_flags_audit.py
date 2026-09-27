# Step 5a · OpenAQ · read-only audit of OpenAQ data flags. Nothing is removed or changed.
#
# Step 4 found hasFlags = true on 10.6% of valid reference sensor-days. The daily data does not say what the flag is,
# so this downloads the flags themselves (GET /v3/sensors/{id}/flags, OpenAQ Docs:
# https://docs.openaq.org/api/operations/sensor_flags_get_v3_sensors__sensor_id__flags_get) for every kept sensor
# with at least one flagged day, and counts flag types and their overlap with the flagged days.
# Raw responses: data/raw/openaq/flags_json/sensor_<id>_flags.json. Summary: data/processed/openaq/step05a_flags/.
# Run from the repo root:  OPENAQ_API_KEY=... python3 scripts/openaq/05a_flags_audit.py
import collections, csv, glob, json, os, subprocess, time, urllib.parse

KEY = os.environ["OPENAQ_API_KEY"]
RAW = "data/raw/openaq/flags_json"; OUT = "data/processed/openaq/step05a_flags"
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)

def get(url):
    for attempt in range(6):
        out = subprocess.run(["curl", "-s", "-m", "120", "-w", "\n%{http_code}", "-H", "X-API-Key: " + KEY, url], capture_output=True, text=True).stdout
        body, _, code = out.rpartition("\n")
        if code == "200":
            time.sleep(1.2); return json.loads(body)
        print(f"  HTTP {code}, retry {attempt + 1}", flush=True); time.sleep(60 if code == "429" else 10)
    raise SystemExit(f"STOP: {url} failed")

days = []
for fn in glob.glob("data/processed/openaq/step04_daily/openaq_pm25_*_daily_sensors.csv"):
    days += list(csv.DictReader(open(fn)))
flagged = collections.defaultdict(list)
for d in days:
    if d["has_flags"] == "True": flagged[d["sensor_id"]].append(d)
cls = {d["sensor_id"]: (d["sensor_class"], d["city_slug"]) for d in days}
print(len(flagged), "sensors with flagged days", flush=True)

rows = []
# The flags endpoint ignores limit/page and returns every flag for the sensor in one response (checked 2026-09-27:
# sensor 2436 returned all 1,130 flags for page=1, page=2 and page=50, with limit=3). So one request per sensor,
# checked against meta.found. (The first run paged forever on sensors with >= 1000 flags and was stopped.)
for sid in sorted(flagged, key=int):
    fn = f"{RAW}/sensor_{sid}_flags.json"
    if os.path.exists(fn):
        pages = json.load(open(fn))
    else:
        r = get(f"https://api.openaq.org/v3/sensors/{sid}/flags?" + urllib.parse.urlencode(dict(limit=1000, page=1)))
        found = r["meta"].get("found")
        if isinstance(found, int) and found != len(r["results"]):
            raise SystemExit(f"STOP: sensor {sid}: meta.found {found} but {len(r['results'])} results")
        pages = [r]
        json.dump(pages, open(fn, "w"))
    for p in pages:
        for f in p["results"]:
            ft = f.get("flagType") or {}
            rows.append(dict(sensor_id=sid, sensor_class=cls[sid][0], city_slug=cls[sid][1], location_id=f.get("locationId"),
                flag_type_id=ft.get("id"), flag_label=ft.get("label"), flag_level=ft.get("level"), note=f.get("note"),
                from_local=(f.get("datetimeFrom") or {}).get("local"), to_local=(f.get("datetimeTo") or {}).get("local")))
    print(f"  sensor {sid}: {sum(len(p['results']) for p in pages)} flags", flush=True)

with open(f"{OUT}/flags_list.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["sensor_id"]); w.writeheader(); w.writerows(rows)
c = collections.Counter((r["sensor_class"], r["flag_label"], r["flag_level"], (r["note"] or "")[:80]) for r in rows)
with open(f"{OUT}/flag_types_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["sensor_class", "flag_label", "flag_level", "note_start", "n_flags"])
    for k, n in c.most_common(): w.writerow([*k, n])
print("DONE:", len(rows), "flags"); [print(" ", n, k) for k, n in c.most_common(15)]
