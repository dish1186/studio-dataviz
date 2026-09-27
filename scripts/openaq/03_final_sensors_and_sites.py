# Step 3 · OpenAQ · final list of sensors per city, grouped into sites. No measurements downloaded.
#
#   1. Keep sensors assigned in Step 2 as "in_city_limits", plus fallback candidates within the 10 km cap
#      (Decision OA-D3). Only sensors with data in the study period (2016-03-06 to 2026-09-25) were assigned in Step 2.
#   2. US only (Decision OA-D3). Sensors inside a study city's Census boundary are in the US by definition.
#      Fallback sensors must have OpenAQ country "US". (OpenAQ's country field is not used for in-city sensors: it is
#      wrong near borders, e.g. Brownsville's AirNow monitors are tagged MX and one Detroit sensor CA.)
#   3. Group each city's sensors into sites (Decision OA-D3): sensors of the same type within 50 m of each other are
#      one site (chained: A-B and B-C within 50 m puts A, B and C in one site). Site ID = the lowest OpenAQ location ID
#      in the group. The daily site value (Step 5) will be the mean of that site's valid sensors.
#   4. Traceability columns for every sensor: other study cities whose limits are within 10 km of it
#      (other_study_cities_nearby, with distances), and the cities whose Step 1 search circle (25 km) it fell in.
# Every Step 2 sensor gets a row in the output, kept or not, with the reason.
# Run from the repo root: python3 scripts/openaq/03_final_sensors_and_sites.py   (no API calls, no key needed)
import csv, glob, json, math, os

CAP_KM = 10.0
SITE_M = 50.0
IN = "data/processed/openaq/step02_assignment/openaq_sensors_assigned.csv"
OUT = "data/processed/openaq/step03_final"
os.makedirs(OUT, exist_ok=True)

def km(a, b):
    p = math.pi / 180
    la1, lo1, la2, lo2 = float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"])
    x = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(x))

country = {}
for fn in glob.glob("data/raw/openaq/json/locations_*.json"):
    for page in json.load(open(fn)):
        for l in page["results"]:
            country[str(l["id"])] = (l.get("country") or {}).get("code")

S = list(csv.DictReader(open(IN)))

# City limits (Step 2 copy of the Census boundaries) for the traceability distances
def gj_rings(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [ring for poly in polys for ring in poly]
def inside(lon, lat, rs):
    c = False
    for ring in rs:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c
def dist_km(lon, lat, rs):
    kx, ky = 111.195 * math.cos(math.radians(lat)), 111.195
    best = float("inf")
    for ring in rs:
        for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
            ax, ay, bx, by = (x1 - lon) * kx, (y1 - lat) * ky, (x2 - lon) * kx, (y2 - lat) * ky
            dx, dy = bx - ax, by - ay
            t = 0 if dx == dy == 0 else max(0, min(1, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(ax + t * dx, ay + t * dy))
    return best
limits = {f["properties"]["city_slug"]: gj_rings(f["geometry"]) for f in json.load(open("data/processed/openaq/step02_assignment/city_boundaries.geojson"))["features"]}
step1 = {}
for r in csv.DictReader(open("data/processed/openaq/step01_inventory/openaq_sensors_inventory.csv")):
    step1.setdefault(r["sensor_id"], []).append(r["city_slug"])
for s in S:
    s["country"] = country.get(s["location_id"], "")
    if s["assignment_rule"] == "in_city_limits":
        s["kept"], s["reason"] = True, "in city limits"
    elif s["assignment_rule"] == "fallback_candidate" and float(s["distance_km_to_assigned_limits"]) <= CAP_KM:
        s["kept"], s["reason"] = True, f"fallback within {CAP_KM:g} km of city limits"
    elif s["assignment_rule"] == "fallback_candidate":
        s["kept"], s["reason"] = False, f"fallback beyond {CAP_KM:g} km cap"
    elif s["overlaps_study_period"] != "True":
        s["kept"], s["reason"] = False, "no data in study period"
    else:
        s["kept"], s["reason"] = False, "outside every study city, not needed as fallback"
    s["us_basis"] = "inside a US city boundary" if s["assignment_rule"] == "in_city_limits" else f"OpenAQ country {s['country'] or 'blank'}"
    if s["kept"] and s["assignment_rule"] != "in_city_limits" and s["country"] != "US":
        s["kept"], s["reason"] = False, f"not in the US (OpenAQ country {s['country'] or 'blank'})"
    if not s["kept"]: s["assigned_city"] = s["assigned_city"] if s["assignment_rule"] == "fallback_candidate" else ""
    lon, lat = float(s["lon"]), float(s["lat"])
    near = []
    for c, rs in limits.items():
        if c == s["assigned_city"]: continue
        d = 0.0 if inside(lon, lat, rs) else dist_km(lon, lat, rs)
        if d <= CAP_KM: near.append((d, c))
    s["other_study_cities_nearby"] = "; ".join(f"{c} ({d:.1f} km)" for d, c in sorted(near))
    s["step01_within_25km_of"] = "; ".join(step1.get(s["sensor_id"], [])) or "(found in Step 2 extra search)"

# Sites: same city, same type, chained within 50 m
kept = [s for s in S if s["kept"]]
parent = {s["sensor_id"]: s["sensor_id"] for s in kept}
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for i, a in enumerate(kept):
    for b in kept[i + 1:]:
        if a["assigned_city"] == b["assigned_city"] and a["sensor_class"] == b["sensor_class"] and km(a, b) * 1000 <= SITE_M:
            parent[find(a["sensor_id"])] = find(b["sensor_id"])
groups = {}
for s in kept: groups.setdefault(find(s["sensor_id"]), []).append(s)
sites = []
for g in groups.values():
    site_id = "S" + str(min(int(s["location_id"]) for s in g))
    for s in g: s["site_id"] = site_id
    names = sorted({s["location_name"] or "" for s in g})
    sites.append(dict(site_id=site_id, city_slug=g[0]["assigned_city"], sensor_class=g[0]["sensor_class"],
        site_name=" / ".join(n for n in names if n) or "(no name)", n_sensors=len(g),
        sensor_ids="; ".join(sorted((s["sensor_id"] for s in g), key=int)),
        location_ids="; ".join(sorted({s["location_id"] for s in g}, key=int)),
        lat=round(sum(float(s["lat"]) for s in g) / len(g), 6), lon=round(sum(float(s["lon"]) for s in g) / len(g), 6),
        max_spread_m=round(max((km(a, b) * 1000 for a in g for b in g), default=0), 1),
        first_measurement_utc=min(s["first_measurement_utc"] for s in g), last_measurement_utc=max(s["last_measurement_utc"] for s in g),
        assignment=" / ".join(sorted({s["reason"] for s in g})),
        distance_km_to_limits=max(float(s["distance_km_to_assigned_limits"] or 0) for s in g)))
sites.sort(key=lambda r: (r["city_slug"], r["sensor_class"], r["site_id"]))

cols = ["sensor_id", "location_id", "location_name", "country", "us_basis", "provider", "sensor_class", "instrument", "lat", "lon",
        "first_measurement_utc", "last_measurement_utc", "assigned_city", "assignment_rule", "distance_km_to_assigned_limits",
        "kept", "reason", "site_id", "other_study_cities_nearby", "step01_within_25km_of"]
with open(f"{OUT}/openaq_sensors_final.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
    w.writerows(sorted(S, key=lambda s: (not s["kept"], s["assigned_city"] or "~", s["sensor_class"], s.get("site_id", ""), int(s["sensor_id"]))))
with open(f"{OUT}/openaq_sites.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(sites[0])); w.writeheader(); w.writerows(sites)
cities = sorted({s["assigned_city"] for s in S if s["assigned_city"]} | {"raymondville", "warren", "delano"})
summ = []
for c in cities:
    row = dict(city_slug=c)
    for cls in ("reference", "low-cost"):
        row[f"{cls}_sites"] = sum(1 for x in sites if x["city_slug"] == c and x["sensor_class"] == cls)
        row[f"{cls}_sensors"] = sum(1 for s in kept if s["assigned_city"] == c and s["sensor_class"] == cls)
    summ.append(row)
with open(f"{OUT}/city_site_counts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0])); w.writeheader(); w.writerows(summ)
from collections import Counter
print("reasons:", dict(Counter(s["reason"] for s in S)))
print(f"DONE: {len(kept)} sensors kept at {len(sites)} sites")
for r in summ: print(r)
