# BATCH 2 (17 cities added 2026-10-02, Gina): a copy of the original step with only the city list, inputs/outputs and
# summary file names changed, so the original 16 cities' files are not touched. Same dates, rules and decisions (OA-D1 to OA-D7).
# Step 1 · OpenAQ · read-only inventory of PM2.5 sensors near each city. No measurements are downloaded.
#
# For each of the 16 cities:
#   1. City center = city hall. 9 cities reuse Dish's coordinates (data/processed/metar/metar_station_distances.csv);
#      6 others are geocoded from their city hall address with the US Census Geocoder. Warren's city hall address
#      (1 City Square) is not in the Census Geocoder, so its coordinates come from Gina (Google Maps place pin).
#   2. Ask OpenAQ for every location with a PM2.5 sensor within 25 km of the center (25 km is the API's maximum radius).
#   3. For each location, ask OpenAQ for its sensors, to get each PM2.5 sensor's own first/last measurement dates.
# Raw API responses are saved exactly as received in data/raw/openaq/json/. The flattened tables go to
# data/processed/openaq/step01_inventory/. Assigning sensors to cities (city limits + nearest-city fallback) is Step 2.
#
# Run from the repo root with the key in the environment:
#   OPENAQ_API_KEY=... python3 scripts/openaq/01_sensor_inventory.py
import csv, json, math, os, subprocess, sys, time, urllib.parse

KEY = os.environ["OPENAQ_API_KEY"]
RADIUS_M = 25000
STUDY_START, STUDY_END = "2016-01-01", "2026-09-25"      # end date matches Dish's Decision D1
RAW = "data/raw/openaq/json"
OUT = "data/processed/openaq/step01_inventory_b2"
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)

CITIES = [  # slug, city, state, city hall address (addresses supplied by Claude, checked by the Census Geocoder)
    ("visalia", "Visalia", "CA", "220 N Santa Fe St, Visalia, CA 93292"),
    ("seattle", "Seattle", "WA", "600 4th Ave, Seattle, WA 98104"),
    ("bismarck", "Bismarck", "ND", "221 N 5th St, Bismarck, ND 58501"),
    ("mcallen", "McAllen", "TX", "1300 Houston Ave, McAllen, TX 78501"),
    ("minot", "Minot", "ND", "10 3rd Ave SW, Minot, ND 58701"),
    ("pittsburgh", "Pittsburgh", "PA", "414 Grant St, Pittsburgh, PA 15219"),
    ("elcentro", "El Centro", "CA", "1275 W Main St, El Centro, CA 92243"),
    ("indianapolis", "Indianapolis", "IN", "200 E Washington St, Indianapolis, IN 46204"),
    ("medford", "Medford", "OR", "411 W 8th St, Medford, OR 97501"),
    ("boise", "Boise City", "ID", "150 N Capitol Blvd, Boise, ID 83702"),
    ("lancaster", "Lancaster", "PA", "120 N Duke St, Lancaster, PA 17602"),
    ("bend", "Bend", "OR", "710 NW Wall St, Bend, OR 97703"),
    ("sanjose", "San Jose", "CA", "200 E Santa Clara St, San Jose, CA 95113"),
    ("saltlakecity", "Salt Lake City", "UT", "451 S State St, Salt Lake City, UT 84111"),
    ("helena", "Helena", "MT", "316 N Park Ave, Helena, MT 59623"),
    ("logan", "Logan", "UT", "290 N 100 W, Logan, UT 84321"),
    ("yakima", "Yakima", "WA", "129 N 2nd St, Yakima, WA 98901"),
]  # None = use Dish's city hall coordinates

# Coordinates supplied by Gina where the Census Geocoder has no match (Google Maps place pin, !3d/!4d values in the URL)
MANUAL = {}

def get(url, headers=()):
    """GET with curl (Python's urllib fails the SSL check on this Mac). Retries on rate limit / errors."""
    for attempt in range(6):
        cmd = ["curl", "-s", "-m", "120", "-w", "\n%{http_code}", url] + [a for h in headers for a in ("-H", h)]
        out = subprocess.run(cmd, capture_output=True, text=True).stdout
        body, _, code = out.rpartition("\n")
        if code == "200":
            time.sleep(1.1)                    # stay under OpenAQ's 60 requests/minute
            return json.loads(body)
        print(f"  HTTP {code}, retry {attempt + 1}", flush=True)
        time.sleep(30 if code == "429" else 5)
    if "/sensors" in url:                      # batch 2: one location's sensor list returned HTTP 500 every time (2026-10-02)
        raise RuntimeError(f"HTTP {code}")
    sys.exit(f"STOP: {url} failed 6 times (last HTTP {code}). Nothing written for this city.")

def km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))

def overlaps(first, last):
    return bool(first and last and first[:10] <= STUDY_END and last[:10] >= STUDY_START)

OAQ = ("X-API-Key: " + KEY,)
dish = {r["city"]: r for r in csv.DictReader(open("data/processed/metar/metar_station_distances.csv"))}

# 1. City centers
centers = {}
for slug, city, st, addr in CITIES:
    if slug in MANUAL:
        lat_m, lon_m, src_m = MANUAL[slug]
        centers[slug] = (lat_m, lon_m, addr, src_m)
    elif addr is None:
        d = dish[slug]
        centers[slug] = (float(d["city_hall_lat"]), float(d["city_hall_lon"]), d["city_hall"], "Dish, METAR Step 8b")
    else:
        g = get("https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?"
                + urllib.parse.urlencode(dict(address=addr, benchmark="Public_AR_Current", format="json")))
        json.dump(g, open(f"{RAW}/geocode_{slug}.json", "w"), indent=1)
        m = g["result"]["addressMatches"]
        if not m:
            sys.exit(f"STOP: Census Geocoder found no match for {addr}")
        centers[slug] = (m[0]["coordinates"]["y"], m[0]["coordinates"]["x"], addr, "US Census Geocoder: " + m[0]["matchedAddress"])
    print(slug, centers[slug], flush=True)

# 2-3. Locations and sensors
cities_rows, inv = [], []
for slug, city, st, _ in CITIES:
    lat, lon, addr, src = centers[slug]
    pages, page = [], 1
    while True:
        r = get("https://api.openaq.org/v3/locations?" + urllib.parse.urlencode(dict(
            coordinates=f"{lat},{lon}", radius=RADIUS_M, parameters_id=2, limit=1000, page=page)), OAQ)
        pages.append(r)
        if len(r.get("results", [])) < 1000: break
        page += 1
    json.dump(pages, open(f"{RAW}/locations_{slug}.json", "w"), indent=1)
    locs = [l for p in pages for l in p["results"]]
    # Check the search worked as intended (e.g. latitude/longitude order): every location must be within the radius.
    far = [l["id"] for l in locs if km(lat, lon, l["coordinates"]["latitude"], l["coordinates"]["longitude"]) > RADIUS_M / 1000 + 0.5]
    if far:
        sys.exit(f"STOP: {slug}: {len(far)} locations returned outside {RADIUS_M/1000} km (first: {far[:5]}). Check the coordinates parameter.")
    sens_raw = []
    for l in locs:
        try:
            s = get(f"https://api.openaq.org/v3/locations/{l['id']}/sensors", OAQ); src_dates = "sensor"
        except RuntimeError as e:
            # Batch 2 fallback: use the location's own first/last dates for its sensors, and say so in dates_source.
            s = {"results": [], "error": str(e)}; src_dates = f"location record (sensors endpoint failed: {e})"
            print(f"  location {l['id']} sensors endpoint failed ({e}); using location-level dates", flush=True)
        sens_raw.append({"location_id": l["id"], "response": s})
        spans = {x["id"]: x for x in s.get("results", [])}
        for sn in l.get("sensors", []):
            if sn["parameter"]["name"] != "pm25": continue
            x = spans.get(sn["id"], {})
            first = (x.get("datetimeFirst") or {}).get("utc"); last = (x.get("datetimeLast") or {}).get("utc")
            if not x:
                first = (l.get("datetimeFirst") or {}).get("utc"); last = (l.get("datetimeLast") or {}).get("utc")
            llat, llon = l["coordinates"]["latitude"], l["coordinates"]["longitude"]
            inv.append(dict(
                city_slug=slug, location_id=l["id"], location_name=l.get("name"), locality=l.get("locality"),
                sensor_id=sn["id"], parameter=sn["parameter"]["name"], units=sn["parameter"].get("units"),
                provider=(l.get("provider") or {}).get("name"), owner=(l.get("owner") or {}).get("name"),
                sensor_class="reference" if l.get("isMonitor") else "low-cost", is_mobile=l.get("isMobile"),
                instrument="; ".join(i.get("name", "") for i in l.get("instruments", [])),
                lat=llat, lon=llon, distance_km_to_center=round(km(lat, lon, llat, llon), 2),
                first_measurement_utc=first, last_measurement_utc=last,
                overlaps_study_period=overlaps(first, last), timezone=l.get("timezone"),
                dates_source=src_dates if not x else "sensor"))
    with open(f"{RAW}/location_sensors_{slug}.jsonl", "w") as f:
        for s in sens_raw: f.write(json.dumps(s) + "\n")
    n = [r for r in inv if r["city_slug"] == slug]
    cities_rows.append(dict(city_slug=slug, city=city, state=st, center_address=addr, center_lat=lat, center_lon=lon,
        center_source=src, search_radius_km=RADIUS_M / 1000, n_locations_found=len(locs), n_pm25_sensors_found=len(n),
        n_reference=sum(r["sensor_class"] == "reference" for r in n), n_lowcost=sum(r["sensor_class"] == "low-cost" for r in n),
        n_overlapping_study_period=sum(r["overlaps_study_period"] for r in n)))
    print(slug, cities_rows[-1]["n_locations_found"], "locations,", len(n), "PM2.5 sensors", flush=True)

# Sensors that fall inside more than one city's 25 km circle (input to Step 2's assignment)
by_sensor = {}
for r in inv: by_sensor.setdefault(r["sensor_id"], []).append(r["city_slug"])
for r in inv:
    r["also_within_25km_of"] = "; ".join(c for c in by_sensor[r["sensor_id"]] if c != r["city_slug"])

for name, rows in (("openaq_cities.csv", cities_rows), ("openaq_sensors_inventory.csv", inv)):
    with open(f"{OUT}/{name}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("DONE:", len(inv), "city-sensor rows,", len(by_sensor), "distinct sensors", flush=True)
