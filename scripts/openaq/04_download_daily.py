# Step 4 · OpenAQ · download daily PM2.5 for every kept sensor (Step 3), 2016-03-06 to 2026-09-25.
#
# OpenAQ's daily value = mean of the sensor's hourly values from 01:00 to 00:00 local time (OpenAQ Docs,
# Measurements: https://docs.openaq.org/resources/measurements). Endpoint: GET /v3/sensors/{id}/days with
# date_from / date_to. OpenAQ warns long ranges can time out, so each sensor is requested one calendar year at a
# time, only for the years between its first and last measurement.
#
# Raw responses: data/raw/openaq/daily_json/sensor_<id>.json.gz (gzip, exactly as received, one file per sensor).
# Flattened: data/processed/openaq/step04_daily/openaq_pm25_<city>_daily_sensors.csv (one row per sensor per local day,
# study period only; no values changed, no days removed; valid_day = hours_observed >= 18, Decision OA-D3).
# Resumable: a sensor whose raw file already exists is not downloaded again. Failed sensors are listed, not fatal.
#
# Run from the repo root:  OPENAQ_API_KEY=... python3 scripts/openaq/04_download_daily.py
import csv, gzip, json, os, subprocess, time, urllib.parse

KEY = os.environ["OPENAQ_API_KEY"]
START, END = "2016-03-06", "2026-09-25"
MIN_HOURS = 18
RAW = "data/raw/openaq/daily_json"
OUT = "data/processed/openaq/step04_daily"
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)

# Pacing (changed at Gina's request after 32 sensors, to speed up the run): a short pause between requests, plus a
# client-side budget that never exceeds OpenAQ's free-tier limits of 60 requests/minute and 2,000/hour
# (https://docs.openaq.org/using-the-api/rate-limits). Budget used: 55/minute and 1,850/hour (leaves room for the ~110 requests of the first run), counting every request.
SENT = []
def wait_for_budget():
    while True:
        now = time.time()
        while SENT and now - SENT[0] > 3600: SENT.pop(0)
        last_min = sum(1 for t in SENT if now - t <= 60)
        if last_min < 55 and len(SENT) < 1850: break
        time.sleep(1)
    SENT.append(time.time())

def get(url):
    code = ""
    for attempt in range(6):
        wait_for_budget()
        out = subprocess.run(["curl", "-s", "-m", "180", "-w", "\n%{http_code}", "-H", "X-API-Key: " + KEY, url],
                             capture_output=True, text=True).stdout
        body, _, code = out.rpartition("\n")
        if code == "200":
            time.sleep(0.3)
            return json.loads(body)
        print(f"    HTTP {code or 'timeout'}, retry {attempt + 1}", flush=True)
        time.sleep(60 if code == "429" else 10)
    raise RuntimeError(f"HTTP {code or 'timeout'} after 6 tries")

sensors = [s for s in csv.DictReader(open("data/processed/openaq/step03_final/openaq_sensors_final.csv")) if s["kept"] == "True"]
print(len(sensors), "sensors to download", flush=True)

failed, summary = [], []
for i, s in enumerate(sensors, 1):
    sid = s["sensor_id"]; fn = f"{RAW}/sensor_{sid}.json.gz"
    if not os.path.exists(fn):
        y0 = max(int(START[:4]), int(s["first_measurement_utc"][:4]))
        y1 = min(int(END[:4]), int(s["last_measurement_utc"][:4]))
        chunks = []
        try:
            for y in range(y0, y1 + 1):
                df = max(f"{y}-01-01", START); dt = min(f"{y + 1}-01-01", "2026-09-26")
                page, pages = 1, []
                while True:
                    r = get(f"https://api.openaq.org/v3/sensors/{sid}/days?" + urllib.parse.urlencode(dict(date_from=df, date_to=dt, limit=1000, page=page)))
                    pages.append(r)
                    if len(r.get("results", [])) < 1000: break
                    page += 1
                chunks.append(dict(date_from=df, date_to=dt, pages=pages))
        except RuntimeError as e:
            failed.append(dict(sensor_id=sid, city_slug=s["assigned_city"], error=str(e))); print(f"  [{i}] sensor {sid} FAILED: {e}", flush=True)
            continue
        with gzip.open(fn, "wt") as f: json.dump(dict(sensor_id=int(sid), retrieved_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), chunks=chunks), f)
    n = sum(len(p["results"]) for c in json.load(gzip.open(fn, "rt"))["chunks"] for p in c["pages"])
    print(f"  [{i}/{len(sensors)}] {s['assigned_city']} {s['sensor_class']} sensor {sid}: {n} days returned", flush=True)

# Flatten per city
by_city = {}
for s in sensors:
    fn = f"{RAW}/sensor_{s['sensor_id']}.json.gz"
    if not os.path.exists(fn): continue
    raw = json.load(gzip.open(fn, "rt"))
    days = {}
    for c in raw["chunks"]:
        for p in c["pages"]:
            for d in p["results"]:
                per = d.get("period") or {}
                frm = (per.get("datetimeFrom") or {}); to = (per.get("datetimeTo") or {})
                date = (frm.get("local") or "")[:10]
                if not (START <= date <= END): continue
                cov = d.get("coverage") or {}; sm = d.get("summary") or {}
                hrs = cov.get("observedCount")
                days[date] = dict(city_slug=s["assigned_city"], site_id=s["site_id"], sensor_id=s["sensor_id"], location_id=s["location_id"],
                    sensor_class=s["sensor_class"], date_local=date, pm25_mean_ugm3=d.get("value"),
                    pm25_min=sm.get("min"), pm25_median=sm.get("median"), pm25_max=sm.get("max"), pm25_sd=sm.get("sd"),
                    hours_observed=hrs, hours_expected=cov.get("expectedCount"), percent_complete=cov.get("percentComplete"),
                    valid_day=int(hrs is not None and hrs >= MIN_HOURS), has_flags=(d.get("flagInfo") or {}).get("hasFlags"),
                    period_from_local=frm.get("local"), period_to_local=to.get("local"), period_from_utc=frm.get("utc"), units=(d.get("parameter") or {}).get("units"))
    rows = [days[k] for k in sorted(days)]
    by_city.setdefault(s["assigned_city"], []).extend(rows)
    v = [r for r in rows if r["valid_day"]]
    summary.append(dict(sensor_id=s["sensor_id"], city_slug=s["assigned_city"], site_id=s["site_id"], sensor_class=s["sensor_class"],
        days_in_study=len(rows), valid_days=len(v), first_day=rows[0]["date_local"] if rows else "", last_day=rows[-1]["date_local"] if rows else "",
        negative_values=sum(1 for r in rows if r["pm25_mean_ugm3"] is not None and r["pm25_mean_ugm3"] < 0)))
cols = list(next(iter(by_city.values()))[0].keys())
for c, rows in by_city.items():
    with open(f"{OUT}/openaq_pm25_{c}_daily_sensors.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(sorted(rows, key=lambda r: (r["date_local"], r["site_id"], int(r["sensor_id"]))))
with open(f"{OUT}/step04_sensor_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
with open(f"{OUT}/step04_failed.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["sensor_id", "city_slug", "error"]); w.writeheader(); w.writerows(failed)
print(f"DONE: {len(summary)} sensors flattened, {sum(r['days_in_study'] for r in summary)} sensor-days, "
      f"{sum(r['valid_days'] for r in summary)} valid (>= {MIN_HOURS} h); {len(failed)} failed", flush=True)
