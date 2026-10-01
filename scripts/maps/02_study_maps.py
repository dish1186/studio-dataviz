"""Three map spreads for the 12 study cities, written as SVG with plain Python (no extra libraries).
Read-only on all inputs. Output, in docs/figures/:
  study_cities_map.svg   US overview (Alaska inset) + each city's limits at one common scale
  air_sources_map.svg    per city: PM2.5 (OpenAQ sensors) · visibility (METAR airports) · Google Trends area · Media Cloud collection
  heat_sources_map.svg   per city: actual temperature (gridMET city limits; ERA5-Land cells for Fairbanks) ·
                         felt heat (ERA5-HEAT UTCI cells) · Google Trends area · Media Cloud collection
Shapefiles are read by the small reader below (polygon .shp + .dbf inside the zip). Projections: Albers equal-area
for the overview, local kilometres (equirectangular around the panel centre) everywhere else.
Run from the repo root: python3 scripts/maps/02_study_maps.py"""
import csv, json, math, struct, zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "data"
OUT = ROOT / "docs/figures"; OUT.mkdir(parents=True, exist_ok=True)

CITIES = [  # slug, label, state name, state postal
    ("fairbanks", "Fairbanks", "Alaska", "AK"), ("eugene", "Eugene", "Oregon", "OR"),
    ("sanfrancisco", "San Francisco", "California", "CA"), ("fresno", "Fresno", "California", "CA"),
    ("bakersfield", "Bakersfield", "California", "CA"), ("losangeles", "Los Angeles", "California", "CA"),
    ("sandiego", "San Diego", "California", "CA"), ("phoenix", "Phoenix", "Arizona", "AZ"),
    ("brownsville", "Brownsville", "Texas", "TX"), ("detroit", "Detroit", "Michigan", "MI"),
    ("annarbor", "Ann Arbor", "Michigan", "MI"), ("boston", "Boston", "Massachusetts", "MA")]

# Google Trends geography per city, as downloaded by Gina (data/raw/google-trends/*/trends_sources.csv);
# the heat and the air search terms use the same geographies. None = no Trends file.
TRENDS = {"sanfrancisco": ("dma", "San Francisco-Oakland-San Jose, CA"), "fresno": ("dma", "Fresno-Visalia, CA"),
          "brownsville": ("dma", "Harlingen-Weslaco-Brownsville-McAllen, TX"), "boston": ("dma", "Boston, MA (Manchester, NH)"),
          "bakersfield": ("city", "Bakersfield, CA"), "detroit": ("city", "Detroit, MI"), "eugene": ("city", "Eugene, OR"),
          "fairbanks": ("city", "Fairbanks, AK"), "losangeles": ("city", "Los Angeles, CA"), "phoenix": ("city", "Phoenix, AZ"),
          "sandiego": ("city", "San Diego, CA"), "annarbor": None}
NEIGHBOURS = {"California": ["Oregon", "Nevada", "Arizona"], "Oregon": ["California", "Washington", "Idaho", "Nevada"],
              "Arizona": ["California", "Nevada", "Utah", "New Mexico"], "Texas": ["New Mexico", "Oklahoma", "Louisiana"],
              "Michigan": ["Indiana", "Ohio", "Wisconsin"], "Alaska": [],
              "Massachusetts": ["New Hampshire", "Vermont", "New York", "Connecticut", "Rhode Island", "Maine"]}

INK, MUTED, RULE = "#1f2328", "#6b7280", "#d0d7de"
CITY_F, CITY_E = "#dbe4f0", "#5b7aa6"
LAND, LAND_E = "#f1f3f5", "#c9ced6"
C_PM, C_VIN, C_VOUT = "#a8324a", "#1f5fbf", "#c2410c"
C_TR, C_MC, C_ACT, C_FELT = "#17806f", "#2f5bc9", "#d9822b", "#c2410c"
FONT = "Helvetica, Arial, sans-serif"

# ---------- inputs ----------
def read_zip_shp(path):
    """Polygon shapefile inside a zip -> list of (attributes, rings)."""
    z = zipfile.ZipFile(path); names = z.namelist()
    shp = z.read([n for n in names if n.lower().endswith(".shp")][0])
    dbf = z.read([n for n in names if n.lower().endswith(".dbf")][0])
    n_rec, hlen, rlen = struct.unpack("<IHH", dbf[4:12])
    fields, o = [], 32
    while dbf[o] != 0x0D:
        fields.append((dbf[o:o + 11].split(b"\0")[0].decode(), dbf[o + 16])); o += 32
    recs = []
    for i in range(n_rec):
        b, pos, r = hlen + i * rlen + 1, 0, {}
        for name, ln in fields:
            r[name] = dbf[b + pos:b + pos + ln].decode("latin-1").strip(); pos += ln
        recs.append(r)
    shapes, o = [], 100
    while o < len(shp):
        clen = struct.unpack(">I", shp[o + 4:o + 8])[0] * 2
        c = shp[o + 8:o + 8 + clen]; o += 8 + clen
        if struct.unpack("<i", c[:4])[0] == 0: shapes.append([]); continue
        nparts, npts = struct.unpack("<ii", c[36:44])
        parts = list(struct.unpack(f"<{nparts}i", c[44:44 + 4 * nparts])) + [npts]
        p0 = 44 + 4 * nparts
        pts = [struct.unpack("<dd", c[p0 + 16 * k:p0 + 16 * k + 16]) for k in range(npts)]
        shapes.append([pts[parts[k]:parts[k + 1]] for k in range(nparts)])
    return list(zip(recs, shapes))

_CR = {}
def city_rings(slug):
    if slug not in _CR:
        if slug == "fairbanks":  # Alaska is outside gridMET; TIGER/Line 2025 place, as in scripts/maps/01
            _CR[slug] = [s for r, s in read_zip_shp(D / "raw/gridmet/tiger_places/tl_2025_02_place.zip") if r["GEOID"] == "0224230"][0]
        else:
            _CR[slug] = read_zip_shp(D / f"processed/gridmet/step03_city_polygons/{slug}_citylimits.zip")[0][1]
    return _CR[slug]

def gj_rings(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [[tuple(p[:2]) for p in ring] for poly in polys for ring in poly]

STATES = {f["properties"]["name"]: gj_rings(f["geometry"]) for f in
          json.load(open(D / "raw/basemap/ne_50m_admin_1_states_provinces.geojson"))["features"]
          if f["properties"].get("iso_a2") == "US"}
STATES["Alaska"] = [r for r in STATES["Alaska"] if all(-179.5 < p[0] < 0 for p in r)]  # drop rings across the dateline
DMAS = {f["properties"]["dma_name"]: gj_rings(f["geometry"]) for f in
        json.load(open(D / "raw/basemap/nielsen-mkt-map.json"))["features"]}
OA_BOUND = {f["properties"]["city_slug"]: gj_rings(f["geometry"]) for f in
            json.load(open(D / "processed/openaq/step02_assignment/city_boundaries.geojson"))["features"]}

HALLS, AIRPORTS = {}, {}
for r in csv.DictReader(open(D / "processed/metar/metar_station_distances.csv")):
    HALLS[r["city"]] = (float(r["city_hall_lon"]), float(r["city_hall_lat"]))
    AIRPORTS.setdefault(r["city"], []).append(r)
INSIDE = {(r["city"], r["station"]): r["in_city_limits"] == "True"
          for r in csv.DictReader(open(D / "processed/gridmet/step02_boundary_audit/airport_in_city.csv"))}
SENSORS = {}
for r in csv.DictReader(open(D / "processed/openaq/step03_final/openaq_sensors_final.csv")):
    if r["kept"] == "True": SENSORS.setdefault(r["assigned_city"], []).append(r)

def utci_cells(slug):  # cells actually used, from the final daily file: "lat,lon (w%); ..."
    row = next(csv.DictReader(open(D / f"processed/utci/final/utci_{slug}_daily.csv")))
    out = []
    for part in row["cells_used"].split(";"):
        ll, w = part.strip().split(" (")
        lat, lon = map(float, ll.split(",")); out.append((lat, lon, float(w.rstrip("%)"))))
    return out
ERA5L = [(float(r["lat"]), float(r["lon"]), float(r["weight"]) * 100)
         for r in csv.DictReader(open(D / "processed/era5land/step02_daily/cell_weights.csv"))]
MC_AIR = {r["city"]: (r["collection_name"], int(r["sources_in_collection"]))
          for r in csv.DictReader(open(D / "processed/mediacloud-attention/queries.csv"))}
MC_HEAT = {r["city"]: (r["collection_name"], int(r["sources_in_collection"]))
           for r in csv.DictReader(open(D / "processed/heat-media/queries.csv"))}

# ---------- tiny SVG plotting layer ----------
def local(lon0, lat0):
    k = math.cos(math.radians(lat0))
    return lambda lon, lat: ((lon - lon0) * 111.32 * k, (lat - lat0) * 110.57)

def albers(lon0, lat0, lat1, lat2):
    f = math.radians; n = (math.sin(f(lat1)) + math.sin(f(lat2))) / 2
    C = math.cos(f(lat1)) ** 2 + 2 * n * math.sin(f(lat1)); r0 = math.sqrt(C - 2 * n * math.sin(f(lat0))) / n
    def P(lon, lat):
        r = math.sqrt(C - 2 * n * math.sin(f(lat))) / n; th = n * f(lon - lon0)
        return (r * math.sin(th) * 6371, (r0 - r * math.cos(th)) * 6371)
    return P

def tx(x, y, s, size=11, color=INK, anchor="start", weight="normal", base="auto", lines=None):
    s = s.split("\n")
    out = [f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}" dominant-baseline="{base}" font-family="{FONT}">']
    for i, line in enumerate(s):
        out.append(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else size * 1.25:.1f}">{escape(line)}</tspan>')
    return "".join(out) + "</text>"

class Fig:
    def __init__(self, w, h):
        self.w, self.h, self.items, self.n = w, h, [], 0
    def text(self, *a, **k): self.items.append(tx(*a, **k))
    def save(self, name):
        s = f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">' \
            f'<rect width="100%" height="100%" fill="#ffffff"/>' + "".join(self.items) + "</svg>"
        (OUT / f"{name}.svg").write_text(s, encoding="utf-8")

MARK = {"o": lambda x, y, r: f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"',
        "^": lambda x, y, r: f'<path d="M{x:.1f},{y - r * 1.2:.1f} L{x + r * 1.1:.1f},{y + r * 0.8:.1f} L{x - r * 1.1:.1f},{y + r * 0.8:.1f} Z"',
        "D": lambda x, y, r: f'<path d="M{x:.1f},{y - r * 1.25:.1f} L{x + r:.1f},{y:.1f} L{x:.1f},{y + r * 1.25:.1f} L{x - r:.1f},{y:.1f} Z"',
        "*": lambda x, y, r: '<path d="' + "M" + " L".join(
            f"{x + (r if i % 2 == 0 else r * 0.42) * math.sin(i * math.pi / 5):.1f},{y - (r if i % 2 == 0 else r * 0.42) * math.cos(i * math.pi / 5):.1f}"
            for i in range(10)) + ' Z"'}

class Ax:
    """A panel in data units (km). Ops are collected, then drawn once the frame (centre, half-width) is known."""
    def __init__(self, fig, x, y, w, h, border=True):
        self.fig, self.x, self.y, self.w, self.h, self.ops, self.border = fig, x, y, w, h, [], border
        self.cx = self.cy = 0; self.half = 1; fig.n += 1; self.id = f"c{fig.n}"
    def poly(self, rings, P, fill="none", stroke="none", sw=0.8, op=1, dash=None):
        xy = [[P(*p) for p in r] for r in rings if len(r) >= 3]
        self.ops.append(("poly", xy, fill, stroke, sw, op, dash)); return [p for r in xy for p in r]
    def rect(self, P, lat, lon, half, **k):
        (x0, y0), (x1, y1) = P(lon - half, lat - half), P(lon + half, lat + half)
        return self.poly([[(lon - half, lat - half), (lon + half, lat - half), (lon + half, lat + half), (lon - half, lat + half)]], P, **k)
    def mark(self, x, y, m="o", r=4, fill=INK, stroke="white", sw=1):
        self.ops.append(("mark", x, y, m, r, fill, stroke, sw))
    def dtext(self, x, y, s, dx=0, dy=0, **k): self.ops.append(("text", x, y, s, dx, dy, k))
    def frame(self, pts, pad=1.18, minhalf=3.0, bar=True):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        self.cx, self.cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        self.half = max(max(max(xs) - min(xs), (max(ys) - min(ys)) * self.w / self.h) / 2 * pad, minhalf)
        self.bar = bar
    def px(self, x, y):
        s = self.w / (2 * self.half)
        return self.x + self.w / 2 + (x - self.cx) * s, self.y + self.h / 2 - (y - self.cy) * s
    def draw(self, title=None, sub=None):
        F = self.fig.items
        F.append(f'<clipPath id="{self.id}"><rect x="{self.x}" y="{self.y}" width="{self.w}" height="{self.h}"/></clipPath><g clip-path="url(#{self.id})">')
        for op in self.ops:
            if op[0] == "poly":
                _, xy, fill, stroke, sw, o, dash = op
                d = " ".join("M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in (self.px(*p) for p in r)) + " Z" for r in xy)
                F.append(f'<path d="{d}" fill="{fill}" fill-opacity="{o}" stroke="{stroke}" stroke-width="{sw}" fill-rule="evenodd"'
                         + (f' stroke-dasharray="{dash}"' if dash else "") + ' stroke-linejoin="round"/>')
            elif op[0] == "mark":
                _, x, y, m, r, fill, stroke, sw = op; X, Y = self.px(x, y)
                F.append(MARK[m](X, Y, r) + f' fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            else:
                _, x, y, s, dx, dy, k = op; X, Y = self.px(x, y); F.append(tx(X + dx, Y + dy, s, **k))
        if getattr(self, "bar", False):
            nice = [n for n in [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000] if n <= self.half * 0.55]
            if nice:
                b = nice[-1]; L = b * self.w / (2 * self.half); bx, by = self.x + 8, self.y + self.h - 10
                F.append(f'<path d="M{bx:.1f},{by:.1f} h{L:.1f}" stroke="{INK}" stroke-width="2"/>')
                F.append(tx(bx + L / 2, by - 4, f"{b} km", size=8.5, anchor="middle"))
        if sub:
            lines = sub.split("\n"); w = max(len(l) for l in lines) * 5.1 + 8
            F.append(f'<rect x="{self.x + 4}" y="{self.y + 4}" width="{min(w, self.w - 8):.1f}" height="{len(lines) * 10.6 + 5:.1f}" fill="white" fill-opacity="0.85"/>')
            F.append(tx(self.x + 8, self.y + 13, sub, size=8.5, color=MUTED))
        F.append("</g>")
        if self.border:
            F.append(f'<rect x="{self.x}" y="{self.y}" width="{self.w}" height="{self.h}" fill="none" stroke="{RULE}"/>')
        if title:
            F.append(tx(self.x, self.y - 5, title, size=10.5, weight="bold"))

def hall(ax, P=None, slug=None, r=6):
    x, y = (0, 0) if P is None else P(*HALLS[slug]); ax.mark(x, y, "*", r=r, fill=INK, stroke="white", sw=0.8)

def thin(v, n=250): return v[::max(1, len(v) // n)]

# ---------- panels shared by both source spreads ----------
def panel_trends(ax, slug, st):
    t = TRENDS[slug]
    if t is None:
        P = local(*HALLS[slug]); v = ax.poly(city_rings(slug), P, CITY_F, CITY_E, 0.7); hall(ax); ax.frame(thin(v) + [(0, 0)])
        return "Google Trends", "no Trends file for Ann Arbor;\nnot in the search analysis"
    kind, name = t
    if kind == "dma":
        rings = DMAS[name]; xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
        P = local((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
        for n in [st] + NEIGHBOURS.get(st, []): ax.poly(STATES[n], P, LAND, LAND_E, 0.6)
        v = ax.poly(rings, P, C_TR, C_TR, 1.2, op=0.2)
        ax.poly(city_rings(slug), P, CITY_E, CITY_E, 0.4); hall(ax, P, slug, r=5); ax.frame(v, pad=1.12)
        return "Google Trends", f"metro area (Nielsen DMA)\n{name}\noutline approximate"
    P = local(*HALLS[slug]); v = ax.poly(city_rings(slug), P, "none", C_TR, 1.3, dash="4 3"); hall(ax); ax.frame(thin(v) + [(0, 0)])
    return "Google Trends", f"Google \"city\": {name}\nGoogle does not publish its city\nareas; city limits for reference"

def panel_media(ax, slug, st, label, table):
    coll, n = table[label]
    rings = STATES[st]; xs = [p[0] for r in rings for p in r]; ys = [p[1] for r in rings for p in r]
    P = local((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2)
    for nb in NEIGHBOURS.get(st, []): ax.poly(STATES[nb], P, LAND, LAND_E, 0.6)
    v = ax.poly(rings, P, C_MC, C_MC, 1.0, op=0.16); hall(ax, P, slug, r=6); ax.frame(v, pad=1.08)
    short = coll.replace(", United States", "").replace(" -State", " State").replace(" - State", " State")
    return "Media Cloud", f"{short} collection\n{n:,} sources; city name is a\nsearch term, not a geographic filter"

def p_pm(ax, slug, st, label):
    P = local(*HALLS[slug]); ax.poly(OA_BOUND[slug], P, CITY_F, CITY_E, 0.7)
    # frame on the TIGER city limits + sensors, so outlying islands in the boundary (SF's Farallones) don't shrink the city
    pts = [(0, 0)] + thin([P(*p) for r in city_rings(slug) for p in r])
    ref = [s for s in SENSORS.get(slug, []) if s["sensor_class"] == "reference"]
    low = [s for s in SENSORS.get(slug, []) if s["sensor_class"] == "low-cost"]
    for s in low:
        x, y = P(float(s["lon"]), float(s["lat"])); pts.append((x, y)); ax.mark(x, y, "o", 2.3, "white", C_PM, 0.9)
    fb = 0
    for s in ref:
        x, y = P(float(s["lon"]), float(s["lat"])); pts.append((x, y)); out = s["assignment_rule"] != "in_city_limits"; fb += out
        ax.mark(x, y, "D" if out else "o", 4.2, C_PM, "white", 1)
    hall(ax); ax.frame(pts)
    note = f"{len(ref)} reference · {len(low)} low-cost"
    if fb: note += f"\n{fb} reference monitor outside the\nlimits (nearest-city fallback)"
    return "PM2.5 · OpenAQ sensors", note

def p_vis(ax, slug, st, label):
    P = local(*HALLS[slug]); v = ax.poly(city_rings(slug), P, CITY_F, CITY_E, 0.7); pts = [(0, 0)] + thin(v); codes = []
    for s in AIRPORTS[slug]:
        x, y = P(float(s["station_lon"]), float(s["station_lat"])); pts.append((x, y))
        inside = INSIDE.get((slug, s["station"]), False)
        ax.mark(x, y, "o" if inside else "^", 5, C_VIN if inside else C_VOUT, "white", 1.2)
        ax.dtext(x, y, s["station"], dx=7, dy=-5, size=9, weight="bold")
        codes.append(f"{s['station']}: {s['distance_km']} km from city hall")
    hall(ax); ax.frame(pts)
    return "Visibility · METAR airports", "\n".join(codes)

def p_act(ax, slug, st, label):
    P = local(*HALLS[slug]); pts = [(0, 0)]
    if slug == "fairbanks":
        for lat, lon, w in ERA5L:
            pts += ax.rect(P, lat, lon, 0.05, fill=C_ACT, stroke=C_ACT, sw=0.5, op=0.08 + 0.55 * w / 35)
            ax.dtext(*P(lon, lat), f"{w:.0f}%", size=8, anchor="middle", base="middle")
        pts += thin(ax.poly(city_rings(slug), P, "none", CITY_E, 1.0))
        sub = "ERA5-Land 0.1° cells, weighted by\nshare of city area (Alaska is\noutside gridMET)"
    else:
        pts += thin(ax.poly(city_rings(slug), P, C_ACT, C_ACT, 0.9, op=0.4))
        sub = "gridMET 4 km cells, averaged\nover the city limits (ClimateEngine)"
    hall(ax); ax.frame(pts)
    return "Actual temperature", sub

def p_felt(ax, slug, st, label):
    P = local(*HALLS[slug]); pts = [(0, 0)]
    for lat, lon, w in utci_cells(slug):
        pts += ax.rect(P, lat, lon, 0.125, fill=C_FELT, stroke=C_FELT, sw=0.6, op=0.06 + 0.45 * w / 100)
    ax.poly(city_rings(slug), P, CITY_F, CITY_E, 0.7, op=0.85)
    for lat, lon, w in utci_cells(slug):
        ax.dtext(*P(lon, lat), f"{w:.0f}%", size=8.5, anchor="middle", base="middle", weight="bold")
    hall(ax); ax.frame(pts, pad=1.06)
    return "Felt heat · UTCI", "ERA5-HEAT 0.25° cells used\n(% = share of the city's area)"

# ---------- figures ----------
def map_cities():
    fig = Fig(2000, 1560)
    fig.text(20, 40, "The 12 study cities", size=28, weight="bold")
    fig.text(20, 66, "City limits: U.S. Census TIGER/Line 2025 Places (the boundaries used for gridMET actual temperature and the UTCI cell weights). "
             "Overview: Albers equal-area; Alaska inset at its own scale. ★ = city hall.", size=13, color=MUTED)
    ax = Ax(fig, 20, 90, 1400, 860, border=False); P48 = albers(-96, 37.5, 29.5, 45.5); pts = []
    for nm, rings in STATES.items():
        if nm in ("Alaska", "Hawaii"): continue
        pts += thin(ax.poly(rings, P48, LAND, LAND_E, 0.8), 40)
    offs = {"annarbor": (-10, 18, "end"), "detroit": (10, -8, "start"), "sanfrancisco": (12, -8, "start"), "fresno": (10, -2, "start"),
            "bakersfield": (10, 8, "start"), "losangeles": (-10, 6, "end"), "sandiego": (8, 14, "start"), "eugene": (10, 4, "start")}
    for slug, label, st, pc in CITIES:
        if slug == "fairbanks": continue
        x, y = P48(*HALLS[slug]); ax.mark(x, y, "o", 6, INK, "white", 1.5)
        dx, dy, an = offs.get(slug, (10, 4, "start")); ax.dtext(x, y, label, dx=dx, dy=dy, size=16, anchor=an)
    ax.frame(pts, pad=1.02, bar=False); ax.draw()
    ak = Ax(fig, 30, 700, 330, 240); PAK = albers(-154, 50, 55, 65)
    v = ak.poly(STATES["Alaska"], PAK, LAND, LAND_E, 0.6); x, y = PAK(*HALLS["fairbanks"])
    ak.mark(x, y, "o", 6, INK, "white", 1.5); ak.dtext(x, y, "Fairbanks", dx=10, dy=5, size=16)
    ak.frame(thin(v, 400), pad=1.05, bar=False); ak.draw(sub="Alaska (own scale)")
    # common-scale panels
    ext, areas = 0, {}
    for s, *_ in CITIES:
        P = local(*HALLS[s]); a = 0
        for ring in city_rings(s):
            xy = [P(*p) for p in ring]
            a += sum(xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1] for i in range(len(xy) - 1)) / 2
            ext = max(ext, max(max(abs(x), abs(y)) for x, y in xy))
        areas[s] = abs(a)
    fig.text(20, 1000, "Every city at the same scale, centred on its city hall", size=18, weight="bold")
    fig.text(20, 1022, "Area = land + water inside the city limits.", size=13, color=MUTED)
    for k, (s, label, st, pc) in enumerate(CITIES):
        a = Ax(fig, 20 + (k % 6) * 330, 1060 + (k // 6) * 250, 310, 215); P = local(*HALLS[s])
        a.poly(city_rings(s), P, CITY_F, CITY_E, 0.9); hall(a); a.frame([(-ext, -ext), (ext, ext)], pad=1.04, bar=(k == 0))
        a.draw(title=f"{label}, {pc}", sub=f"{areas[s]:,.0f} km²")
    fig.save("study_cities_map")

def spread(name, title, sub, cols):
    PW, PH, GX, GY, TOP = 272, 230, 8, 52, 118
    blockw = 4 * PW + 3 * GX
    fig = Fig(2 * blockw + 60 + 40, TOP + 6 * (PH + GY) + 70)
    fig.text(20, 40, title, size=26, weight="bold"); fig.text(20, 66, sub[0], size=12.5, color=MUTED); fig.text(20, 84, sub[1], size=12.5, color=MUTED)
    for k, (slug, label, st, pc) in enumerate(CITIES):
        row, side = k // 2, k % 2
        bx, by = 20 + side * (blockw + 60), TOP + row * (PH + GY) + 26
        fig.text(bx, by - 26, f"{label}, {pc}", size=15, weight="bold")
        for c, fn in enumerate(cols):
            ax = Ax(fig, bx + c * (PW + GX), by, PW, PH); t, s = fn(ax, slug, st, label); ax.draw(title=t, sub=s)
    return fig

def legend(fig, items):
    x, y = 20, fig.h - 28
    for kind, fill, stroke, text in items:
        if kind == "patch": fig.items.append(f'<rect x="{x}" y="{y - 9}" width="18" height="12" fill="{fill}" fill-opacity="0.45" stroke="{stroke}"/>')
        else: fig.items.append(MARK[kind](x + 9, y - 3, 5 if kind != "*" else 7) + f' fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>')
        fig.text(x + 24, y + 1, text, size=12.5); x += 34 + len(text) * 6.6

map_cities()
air = spread("air_sources_map", "Air quality: where each measure comes from",
             ("Per city: PM2.5 (sensor) · visibility (embodied) · searches (action) · news (media). Each panel has its own scale; ★ = city hall.",
              "Sources: OpenAQ sensor metadata + Gina's city boundaries (OpenAQ Step 2) · IEM ASOS station metadata · TIGER/Line 2025 Places · "
              "Nielsen DMA outlines, community GeoJSON (simzou/nielsen-dma), approximate · Natural Earth 1:50m states · Media Cloud collections."),
             [p_pm, p_vis, lambda a, s, st, l: panel_trends(a, s, st), lambda a, s, st, l: panel_media(a, s, st, l, MC_AIR)])
legend(air, [("o", C_PM, "white", "PM2.5 reference monitor"), ("o", "white", C_PM, "PM2.5 low-cost sensor"),
             ("D", C_PM, "white", "reference monitor outside limits"), ("o", C_VIN, "white", "airport inside city limits"),
             ("^", C_VOUT, "white", "airport outside city limits"), ("patch", CITY_F, CITY_E, "city limits"),
             ("patch", C_TR, C_TR, "Trends metro area (DMA)"), ("patch", C_MC, C_MC, "Media Cloud state collection"), ("*", INK, "white", "city hall")])
air.save("air_sources_map")
heat = spread("heat_sources_map", "Heat: where each measure comes from",
              ("Per city: actual temperature (sensor) · felt heat (embodied) · searches (action) · news (media). Each panel has its own scale; ★ = city hall.",
               "Sources: gridMET via ClimateEngine + TIGER/Line 2025 Places · ERA5-Land (Fairbanks) · Copernicus ERA5-HEAT UTCI · "
               "Nielsen DMA outlines, community GeoJSON (simzou/nielsen-dma), approximate · Natural Earth 1:50m states · Media Cloud collections."),
              [p_act, p_felt, lambda a, s, st, l: panel_trends(a, s, st), lambda a, s, st, l: panel_media(a, s, st, l, MC_HEAT)])
legend(heat, [("patch", C_ACT, C_ACT, "actual temperature: area averaged"), ("patch", C_FELT, C_FELT, "felt heat: UTCI cell used (darker = more weight)"),
              ("patch", CITY_F, CITY_E, "city limits"), ("patch", C_TR, C_TR, "Trends metro area (DMA)"),
              ("patch", C_MC, C_MC, "Media Cloud state collection"), ("*", INK, "white", "city hall")])
heat.save("heat_sources_map")
print("saved study_cities_map.svg, air_sources_map.svg, heat_sources_map.svg to", OUT)
