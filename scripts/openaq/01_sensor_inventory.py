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
OUT = "data/processed/openaq/step01_inventory"
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)

CITIES = [  # slug, city, state, city hall address
    ("annarbor", "Ann Arbor", "MI", "301 E Huron St, Ann Arbor, MI 48104"),
    ("bakersfield", "Bakersfield", "CA", None),
    ("boston", "Boston", "MA", None),
    ("brownsville", "Brownsville", "TX", None),
    ("delano", "Delano", "CA", "1015 11th Ave, Delano, CA 93215"),
    ("detroit", "Detroit", "MI", None),
    ("eugene", "Eugene", "OR", None),
    ("fairbanks", "Fairbanks", "AK", None),
    ("fresno", "Fresno", "CA", None),
    ("losangeles", "Los Angeles", "CA", None),
    ("phoenix", "Phoenix", "AZ", "200 W Washington St, Phoenix, AZ 85003"),
    ("raymondville", "Raymondville", "TX", "142 S 7th St, Raymondville, TX 78580"),
    ("sandiego", "San Diego", "CA", "202 C St, San Diego, CA 92101"),
    ("sanfrancisco", "San Francisco", "CA", None),
    ("springfield", "Springfield", "OR", "225 5th St, Springfield, OR 97477"),
    ("warren", "Warren", "MI", "1 City Square, Warren, MI 48093"),
]  # None = use Dish's city hall coordinates

# Coordinates supplied by Gina where the Census Geocoder has no match (Google Maps place pin, !3d/!4d values in the URL)
MANUAL = {"warren": (42.5118008, -83.0249714, "Gina, Google Maps place pin (address not in Census Geocoder)")}

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
        s = get(f"https://api.openaq.org/v3/locations/{l['id']}/sensors", OAQ)
        sens_raw.append({"location_id": l["id"], "response": s})
        spans = {x["id"]: x for x in s.get("results", [])}
        for sn in l.get("sensors", []):
            if sn["parameter"]["name"] != "pm25": continue
            x = spans.get(sn["id"], {})
            first = (x.get("datetimeFirst") or {}).get("utc"); last = (x.get("datetimeLast") or {}).get("utc")
            llat, llon = l["coordinates"]["latitude"], l["coordinates"]["longitude"]
            inv.append(dict(
                city_slug=slug, location_id=l["id"], location_name=l.get("name"), locality=l.get("locality"),
                sensor_id=sn["id"], parameter=sn["parameter"]["name"], units=sn["parameter"].get("units"),
                provider=(l.get("provider") or {}).get("name"), owner=(l.get("owner") or {}).get("name"),
                sensor_class="reference" if l.get("isMonitor") else "low-cost", is_mobile=l.get("isMobile"),
                instrument="; ".join(i.get("name", "") for i in l.get("instruments", [])),
                lat=llat, lon=llon, distance_km_to_center=round(km(lat, lon, llat, llon), 2),
                first_measurement_utc=first, last_measurement_utc=last,
                overlaps_study_period=overlaps(first, last), timezone=l.get("timezone")))
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
