# Step 2 · OpenAQ · assign PM2.5 sensors to cities by city limits, and list fallback options. No measurements downloaded.
#
#   1. Read the 16 city boundaries from the Census 2024 cartographic boundary file (data/raw/census/, not modified).
#   2. For cities whose limits reach past the Step 1 search net (25 km from city hall), run one extra OpenAQ search
#      over the city's bounding box, so sensors near the edges of large cities are not missed. Raw responses saved.
#   3. For every distinct sensor: which listed city's limits it is inside (if any), and its distance to each city's limits.
#   4. Assignment (Decision OA-D1): a sensor inside a city's limits belongs to that city. Fallback is decided per
#      sensor type (reference / low-cost), because the city averages will be computed per type (Decision OA-D2):
#      a city with no sensor of a type inside its limits may use sensors of that type that are outside every listed
#      city; each such sensor goes to the nearest city (by distance to limits) among the cities needing that fallback.
#   5. Fallback cap options: for each city/type needing fallback, how many sensors each cap (5/10/15/20 km beyond the
#      limits) would keep. The cap itself is chosen by Gina after this step (Decision OA-D2); nothing is dropped here.
#
# Run from the repo root:  OPENAQ_API_KEY=... python3 scripts/openaq/02_assign_sensors.py
import csv, io, json, math, os, subprocess, sys, time, urllib.parse, zipfile
import shapefile  # pyshp

KEY = os.environ["OPENAQ_API_KEY"]
STUDY_START, STUDY_END = "2016-03-06", "2026-09-25"     # Decision OA-D2 / Dish's D1
NET_KM = 25.0
CAPS_KM = (5, 10, 15, 20)
ZIP = "data/raw/census/cb_2024_us_place_500k.zip"
RAW = "data/raw/openaq/json"
IN = "data/processed/openaq/step01_inventory"
OUT = "data/processed/openaq/step02_assignment"
os.makedirs(OUT, exist_ok=True)
STATE = {"annarbor": ("Ann Arbor", "MI"), "bakersfield": ("Bakersfield", "CA"), "boston": ("Boston", "MA"),
         "brownsville": ("Brownsville", "TX"), "delano": ("Delano", "CA"), "detroit": ("Detroit", "MI"),
         "eugene": ("Eugene", "OR"), "fairbanks": ("Fairbanks", "AK"), "fresno": ("Fresno", "CA"),
         "losangeles": ("Los Angeles", "CA"), "phoenix": ("Phoenix", "AZ"), "raymondville": ("Raymondville", "TX"),
         "sandiego": ("San Diego", "CA"), "sanfrancisco": ("San Francisco", "CA"), "springfield": ("Springfield", "OR"),
         "warren": ("Warren", "MI")}

def get(url):
    """GET with curl (Python's urllib fails the SSL check on this Mac). Retries on rate limit / errors."""
    for attempt in range(6):
        out = subprocess.run(["curl", "-s", "-m", "120", "-w", "\n%{http_code}", "-H", "X-API-Key: " + KEY, url],
                             capture_output=True, text=True).stdout
        body, _, code = out.rpartition("\n")
        if code == "200":
            time.sleep(1.1)
            return json.loads(body)
        print(f"  HTTP {code}, retry {attempt + 1}", flush=True)
        time.sleep(30 if code == "429" else 5)
    sys.exit(f"STOP: {url} failed 6 times (last HTTP {code}).")

def hav_km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))

def rings(shape):
    idx = list(shape.parts) + [len(shape.points)]
    return [shape.points[idx[i]:idx[i + 1]] for i in range(len(shape.parts))]

def inside(lon, lat, rs):
    """Even-odd rule over all rings (handles holes and multi-part cities)."""
    c = False
    for ring in rs:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1):
                c = not c
    return c

def dist_to_boundary_km(lon, lat, rs):
    """Shortest distance from the point to the boundary, on a local flat projection centred on the point."""
    kx, ky = 111.195 * math.cos(math.radians(lat)), 111.195
    best = float("inf")
    for ring in rs:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            t = 0 if dx == dy == 0 else max(0, min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best

def overlaps(first, last):
    return bool(first and last and first[:10] <= STUDY_END and last[:10] >= STUDY_START)

# 1. Boundaries
z = zipfile.ZipFile(ZIP)
b = "cb_2024_us_place_500k"
rdr = shapefile.Reader(shp=io.BytesIO(z.read(b + ".shp")), shx=io.BytesIO(z.read(b + ".shx")), dbf=io.BytesIO(z.read(b + ".dbf")))
want = {v: k for k, v in STATE.items()}
bounds, feats = {}, []
for sr in rdr.iterShapeRecords():
    d = sr.record.as_dict()
    slug = want.get((d["NAME"], d["STUSPS"]))
    if slug is None or d["LSAD"] != "25": continue          # LSAD 25 = "city"
    if slug in bounds: sys.exit(f"STOP: two boundaries match {slug}")
    bounds[slug] = dict(rec=d, rings=rings(sr.shape), bbox=sr.shape.bbox)
    feats.append({"type": "Feature", "properties": {"city_slug": slug, **{k: d[k] for k in ("GEOID", "NAMELSAD", "STUSPS", "ALAND", "AWATER")}},
                  "geometry": sr.shape.__geo_interface__})
missing = set(STATE) - set(bounds)
if missing: sys.exit(f"STOP: no boundary for {missing}")
json.dump({"type": "FeatureCollection", "features": feats}, open(f"{OUT}/city_boundaries.geojson", "w"))

centers = {r["city_slug"]: (float(r["center_lat"]), float(r["center_lon"])) for r in csv.DictReader(open(f"{IN}/openaq_cities.csv"))}
inv = list(csv.DictReader(open(f"{IN}/openaq_sensors_inventory.csv")))
sensors = {}
for r in inv:
    sensors.setdefault(r["sensor_id"], {k: r[k] for k in ("sensor_id", "location_id", "location_name", "provider", "owner",
        "sensor_class", "is_mobile", "instrument", "lat", "lon", "first_measurement_utc", "last_measurement_utc", "timezone")} | {"found_by": "step01_radius"})

# 2. Extra search for cities reaching past the 25 km net
summary = []
known_locs = {r["location_id"] for r in inv}
for slug, bd in bounds.items():
    lat0, lon0 = centers[slug]
    far = max(hav_km(lat0, lon0, y, x) for ring in bd["rings"] for x, y in ring)
    extra_locs = extra_sensors = 0
    if far > NET_KM:
        minx, miny, maxx, maxy = bd["bbox"]
        pages, page = [], 1
        while True:
            r = get("https://api.openaq.org/v3/locations?" + urllib.parse.urlencode(dict(
                bbox=f"{minx},{miny},{maxx},{maxy}", parameters_id=2, limit=1000, page=page)))
            pages.append(r)
            if len(r.get("results", [])) < 1000: break
            page += 1
        json.dump(pages, open(f"{RAW}/locations_bbox_{slug}.json", "w"), indent=1)
        locs = [l for p in pages for l in p["results"]]
        bad = [l["id"] for l in locs if not (minx - 0.01 <= l["coordinates"]["longitude"] <= maxx + 0.01 and miny - 0.01 <= l["coordinates"]["latitude"] <= maxy + 0.01)]
        if bad: sys.exit(f"STOP: {slug}: bbox search returned {len(bad)} locations outside the box (first {bad[:5]}).")
        new = [l for l in locs if str(l["id"]) not in known_locs]
        with open(f"{RAW}/location_sensors_bbox_{slug}.jsonl", "w") as f:
            for l in new:
                s = get(f"https://api.openaq.org/v3/locations/{l['id']}/sensors")
                f.write(json.dumps({"location_id": l["id"], "response": s}) + "\n")
                spans = {x["id"]: x for x in s.get("results", [])}
                for sn in l.get("sensors", []):
                    if sn["parameter"]["name"] != "pm25" or str(sn["id"]) in sensors: continue
                    x = spans.get(sn["id"], {})
                    sensors[str(sn["id"])] = dict(sensor_id=str(sn["id"]), location_id=str(l["id"]), location_name=l.get("name"),
                        provider=(l.get("provider") or {}).get("name"), owner=(l.get("owner") or {}).get("name"),
                        sensor_class="reference" if l.get("isMonitor") else "low-cost", is_mobile=str(l.get("isMobile")),
                        instrument="; ".join(i.get("name", "") for i in l.get("instruments", [])),
                        lat=str(l["coordinates"]["latitude"]), lon=str(l["coordinates"]["longitude"]),
                        first_measurement_utc=(x.get("datetimeFirst") or {}).get("utc"), last_measurement_utc=(x.get("datetimeLast") or {}).get("utc"),
                        timezone=l.get("timezone"), found_by=f"step02_bbox_{slug}")
                    extra_sensors += 1
                known_locs.add(str(l["id"]))
            extra_locs = len(new)
    d = bd["rec"]
    summary.append(dict(city_slug=slug, GEOID=d["GEOID"], NAMELSAD=d["NAMELSAD"], state=d["STUSPS"], land_km2=round(d["ALAND"] / 1e6, 1),
        farthest_limit_from_center_km=round(far, 1), extra_bbox_search=far > NET_KM, extra_locations_found=extra_locs, extra_pm25_sensors_found=extra_sensors))
    print(slug, f"farthest limit {far:.1f} km", f"(+{extra_locs} locations, +{extra_sensors} sensors)" if far > NET_KM else "", flush=True)

# 3. Inside / distance for every sensor
for s in sensors.values():
    lat, lon = float(s["lat"]), float(s["lon"])
    ins = [c for c, bd in bounds.items() if inside(lon, lat, bd["rings"])]
    if len(ins) > 1: sys.exit(f"STOP: sensor {s['sensor_id']} inside two cities {ins}")
    s["inside_city"] = ins[0] if ins else ""
    s["dist"] = {}
    for c, bd in bounds.items():
        minx, miny, maxx, maxy = bd["bbox"]
        if hav_km(lat, lon, min(max(lat, miny), maxy), min(max(lon, minx), maxx)) > 40: continue   # too far to matter
        s["dist"][c] = 0.0 if c == s["inside_city"] else dist_to_boundary_km(lon, lat, bd["rings"])
    s["overlaps_study_period"] = overlaps(s["first_measurement_utc"], s["last_measurement_utc"])

# 4. Assignment
def counts_inside(city, cls):
    return sum(1 for s in sensors.values() if s["inside_city"] == city and s["sensor_class"] == cls and s["overlaps_study_period"])
need = {(c, cls) for c in STATE for cls in ("reference", "low-cost") if counts_inside(c, cls) == 0}
for s in sensors.values():
    s["assigned_city"], s["assignment_rule"], s["distance_km_to_assigned_limits"] = "", "", ""
    if s["inside_city"]:
        s["assigned_city"], s["assignment_rule"], s["distance_km_to_assigned_limits"] = s["inside_city"], "in_city_limits", 0.0
        continue
    cands = [(d, c) for c, d in s["dist"].items() if (c, s["sensor_class"]) in need and d <= max(CAPS_KM)]
    if cands and s["overlaps_study_period"]:
        d, c = min(cands)
        s["assigned_city"], s["assignment_rule"], s["distance_km_to_assigned_limits"] = c, "fallback_candidate", round(d, 2)
    else:
        s["assignment_rule"] = "unassigned"
    near = sorted((d, c) for c, d in s["dist"].items())
    s["nearest_city"], s["distance_km_to_nearest_limits"] = (near[0][1], round(near[0][0], 2)) if near else ("", "")

# 5. Outputs
cols = ["sensor_id", "location_id", "location_name", "provider", "owner", "sensor_class", "is_mobile", "instrument", "lat", "lon",
        "first_measurement_utc", "last_measurement_utc", "overlaps_study_period", "timezone", "found_by", "inside_city",
        "nearest_city", "distance_km_to_nearest_limits", "assigned_city", "assignment_rule", "distance_km_to_assigned_limits"]
with open(f"{OUT}/openaq_sensors_assigned.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
    w.writerows(sorted(sensors.values(), key=lambda s: (s["assigned_city"] or "~", s["sensor_class"], int(s["sensor_id"]))))
with open(f"{OUT}/city_boundary_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
cap_rows = []
for c in STATE:
    for cls in ("reference", "low-cost"):
        fb = sorted(float(s["distance_km_to_assigned_limits"]) for s in sensors.values()
                    if s["assigned_city"] == c and s["sensor_class"] == cls and s["assignment_rule"] == "fallback_candidate")
        cap_rows.append(dict(city_slug=c, sensor_class=cls, inside_limits_in_study=counts_inside(c, cls), needs_fallback=(c, cls) in need,
            nearest_fallback_km=fb[0] if fb else "", **{f"fallback_within_{k}km": sum(d <= k for d in fb) for k in CAPS_KM}))
with open(f"{OUT}/fallback_cap_options.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(cap_rows[0])); w.writeheader(); w.writerows(cap_rows)
n = lambda rule: sum(s["assignment_rule"] == rule for s in sensors.values())
print(f"DONE: {len(sensors)} sensors | in_city_limits {n('in_city_limits')} | fallback_candidate {n('fallback_candidate')} | unassigned {n('unassigned')}")
