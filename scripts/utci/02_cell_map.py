"""UTCI Step 2a: state-by-state map of the PROPOSED UTCI cells, gridMET city-limits polygons
and METAR airports (12 cities, D10). Read-only on all inputs.
For each state: one locator panel (whole state), then one zoomed panel per city.
Cell shares and duplicates come from Step 2 (data/processed/utci/step02_cell_weights/cell_weights.csv).
Output: docs/figures/utci_cells_map.png (+ .pdf)
Set UTCI_MAP_OUT=<dir> to write the figure somewhere else (used only for test runs)."""
import os, math, itertools
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, xarray as xr
from shapely.geometry import box
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/"data/raw/utci/cds_timeseries"
POLY = ROOT/"data/processed/gridmet/step03_city_polygons"
TIGER_AK = ROOT/"data/raw/gridmet/tiger_places/tl_2025_02_place.zip"
DIST = ROOT/"data/processed/metar/metar_station_distances.csv"
AUDIT = ROOT/"data/processed/gridmet/step02_boundary_audit/airport_in_city.csv"
STATES = ROOT/"data/raw/basemap/ne_50m_admin_1_states_provinces.geojson"   # Natural Earth, outlines only
WEIGHTS = ROOT/"data/processed/utci/step02_cell_weights/cell_weights.csv"   # Step 2 (D11)
alt = os.environ.get("UTCI_MAP_OUT")
FIG = Path(alt) if alt else ROOT/"docs/figures"; FIG.mkdir(parents=True, exist_ok=True)

# D10 order (LA, Phoenix, San Diego, Detroit, Bakersfield, San Francisco, Fresno, Boston, Eugene,
# Fairbanks, Brownsville, Ann Arbor), grouped by state in order of each state's first city
LAYOUT = [("CA", "California", [("losangeles","Los Angeles"),("sandiego","San Diego"),("bakersfield","Bakersfield"),
                                 ("sanfrancisco","San Francisco"),("fresno","Fresno")]),
          ("AZ", "Arizona", [("phoenix","Phoenix")]),
          ("MI", "Michigan", [("detroit","Detroit"),("annarbor","Ann Arbor")]),
          ("MA", "Massachusetts", [("boston","Boston")]),
          ("OR", "Oregon", [("eugene","Eugene")]),
          ("AK", "Alaska", [("fairbanks","Fairbanks")]),
          ("TX", "Texas", [("brownsville","Brownsville")])]
ROWS = [[0], [1, 2, 3], [4, 5, 6]]   # which states share a figure row

INK, MUTED, FILL, EDGE = "#1f2328", "#6b7280", "#dbe4f0", "#5b7aa6"
IN_C, OUT_C, HALL = "#1f5fbf", "#c2410c", "#1f2328"
CELL_C, GRID_C, STATE_C = "#d97706", "#b8c0cc", "#9aa4b2"

H = 0.125   # half a 0.25° cell
stations = pd.read_csv(DIST)
audit = pd.read_csv(AUDIT).set_index(["city","station"])
weights = pd.read_csv(WEIGHTS, keep_default_na=False)
states = gpd.read_file(STATES); states = states[states.iso_a2 == "US"]

def city_limits(city):
    if city == "fairbanks":   # not in the gridMET set (AK not covered); GEOID 0224230 from TIGER
        ak = gpd.read_file(TIGER_AK); return ak[ak.GEOID == "0224230"].to_crs(4326).union_all()
    return gpd.read_file(POLY/f"{city}_citylimits.zip").to_crs(4326).union_all()

def km_proj(lon0, lat0):
    """Local equirectangular projection in km around (lon0, lat0), same as the airport map."""
    k = math.cos(math.radians(lat0))
    return lambda lon, lat: ((np.asarray(lon)-lon0)*111.32*k, (np.asarray(lat)-lat0)*110.57)

def draw_geom(ax, geom, P, **kw):
    polys = getattr(geom, "geoms", [geom])
    for pg in polys:
        if pg.geom_type != "Polygon": continue
        x, y = P(*pg.exterior.xy); ax.fill(x, y, **kw)
        for r in pg.interiors:
            xi, yi = P(*r.xy); ax.fill(xi, yi, fc="white", ec=kw.get("ec", "none"), lw=kw.get("lw", 0.5), zorder=kw.get("zorder", 1))

def outline(ax, geom, P, **kw):
    for pg in getattr(geom, "geoms", [geom]):
        if pg.geom_type != "Polygon": continue
        x, y = P(*pg.exterior.xy); ax.plot(x, y, **kw)

EA = "EPSG:6933"   # equal-area CRS for km² shares
def area_km2(g): return gpd.GeoSeries([g], crs=4326).to_crs(EA).area.iloc[0]/1e6

# ---- per-city numbers, taken from Step 2 ----
info = {}
for _, _, cities in LAYOUT:
    for city, _ in cities:
        ds = xr.open_dataset(RAW/f"utci_{city}_1991-2026.nc", engine="netcdf4")
        pts = [(round(float(a),2), round(float(b),2)) for a in ds.latitude.values for b in ds.longitude.values]; ds.close()
        w = weights[weights.city == city]
        cand = [(float(a), float(b)) for a, b in zip(w.lat, w.lon)]
        dup_of = {}
        for a, b, d in zip(w.lat, w.lon, w.duplicate_of):
            for part in [x for x in str(d).split("; ") if x]:
                la_, lo_ = map(float, part.split(",")); dup_of.setdefault((float(a), float(b)), []).append((la_, lo_))
        st = stations[stations.city == city]
        hlat, hlon = float(st.city_hall_lat.iloc[0]), float(st.city_hall_lon.iloc[0])
        hall = [(float(a), float(b)) for a, b, h in zip(w.lat, w.lon, w.is_city_hall_cell) if str(h) == "True"][0]
        info[city] = dict(g=city_limits(city), hall=hall, hall_xy=(hlon,hlat), pts=pts, cand=cand, dup_of=dup_of, st=st)
tab = weights.assign(pct_of_city=weights.weight*100)

# ---- figure ----
ncols = 7
fig, axes = plt.subplots(len(ROWS), ncols, figsize=(ncols*3.4, len(ROWS)*3.9))
for ax in axes.ravel(): ax.axis("off")

def locator(ax, code, name, cities):
    shp = states[states.postal == code].union_all()
    if code == "AK": shp = shp.intersection(box(-170, 50, -129, 72))   # mainland view (skip far Aleutians)
    x0, y0, x1, y1 = shp.bounds
    P = km_proj((x0+x1)/2, (y0+y1)/2)
    draw_geom(ax, shp, P, fc="#f3f4f6", ec=STATE_C, lw=0.7, zorder=1)
    for city, label in cities:
        I = info[city]
        for (a, b) in I["cand"]:
            xs, ys = P([b-H, b+H, b+H, b-H], [a-H, a-H, a+H, a+H]); ax.fill(xs, ys, fc=CELL_C, ec=CELL_C, lw=0.4, alpha=0.6, zorder=2)
        hx, hy = P(*I["hall_xy"]); ax.plot(hx, hy, marker="*", ms=9, color=HALL, mec="white", mew=0.8, zorder=4)
        ax.annotate(label, (hx, hy), xytext=(5, 3), textcoords="offset points", fontsize=8, color=INK, zorder=5)
    ax.set_aspect("equal"); ax.axis("on"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#d0d7de")
    ax.set_title(name, fontsize=12, color=INK, loc="left", fontweight="bold")

def city_panel(ax, code, city, label):
    I = info[city]; g = I["g"]; hlon, hlat = I["hall_xy"]
    P = km_proj(hlon, hlat)
    lat_c = [a for a,_ in I["cand"]]; lon_c = [b for _,b in I["cand"]]
    ext = (min(lon_c)-H-0.06, min(lat_c)-H-0.06, max(lon_c)+H+0.06, max(lat_c)+H+0.06)
    # coastline / state edge for context
    shp = states[states.postal == code].union_all().intersection(box(ext[0]-.5, ext[1]-.5, ext[2]+.5, ext[3]+.5))
    outline(ax, shp, P, color=STATE_C, lw=0.8, zorder=1)
    # full downloaded grid (thin), candidate cells shaded by share of the city
    for (a, b) in I["pts"]:
        xs, ys = P([b-H, b+H, b+H, b-H, b-H], [a-H, a-H, a+H, a+H, a-H]); ax.plot(xs, ys, color=GRID_C, lw=0.6, zorder=2)
    t = tab[tab.city == city].set_index(["lat","lon"])
    for (a, b) in I["cand"]:
        pct = t.loc[(a,b), "pct_of_city"]
        xs, ys = P([b-H, b+H, b+H, b-H], [a-H, a-H, a+H, a+H])
        ax.fill(xs, ys, fc=CELL_C, alpha=0.10 + 0.5*min(pct, 100)/100, ec="none", zorder=2)
        cx, cy = P(b, a)
        ax.text(cx, cy + 9, f"{pct:.0f}%", ha="center", va="center", fontsize=8, color="#7c2d12", fontweight="bold", zorder=6)
    # duplicate pairs (identical cells): dashed link between the two centres with "=" at the midpoint
    done = set()
    for c1, others in I["dup_of"].items():
        for c2 in others:
            if (c2, c1) in done or not ({c1, c2} & set(I["cand"])): continue
            done.add((c1, c2))
            x1_, y1_ = P(c1[1], c1[0]); x2_, y2_ = P(c2[1], c2[0])
            ax.plot([x1_, x2_], [y1_, y2_], ls=(0, (3, 2)), lw=1.4, color="#7c2d12", zorder=6)
            ax.text((x1_+x2_)/2, (y1_+y2_)/2, "=", ha="center", va="center", fontsize=10, fontweight="bold",
                    color="#7c2d12", zorder=6, bbox=dict(fc="white", ec="#7c2d12", lw=0.6, boxstyle="circle,pad=0.15"))
    a, b = I["hall"]
    xs, ys = P([b-H, b+H, b+H, b-H, b-H], [a-H, a-H, a+H, a+H, a-H]); ax.plot(xs, ys, color="#7c2d12", lw=2.0, zorder=3)
    # gridMET city limits
    draw_geom(ax, g, P, fc=FILL, ec=EDGE, lw=0.8, alpha=0.9, zorder=3)
    # airports + city hall
    ax.plot(0, 0, marker="*", ms=12, color=HALL, mec="white", mew=1, zorder=7)
    for _, s in I["st"].iterrows():
        x, y = P(s.station_lon, s.station_lat)
        inside = bool(audit.loc[(city, s.station), "in_city_limits"]) if (city, s.station) in audit.index else False
        ax.plot(x, y, marker="o" if inside else "^", ms=9, color=IN_C if inside else OUT_C, mec="white", mew=1.2, zorder=7)
        ax.annotate(s.station, (x, y), xytext=(5, -3), textcoords="offset points", fontsize=7.5, color=INK, va="top", zorder=8,
                    bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.8))
    x0, y0 = P(ext[0], ext[1]); x1, y1 = P(ext[2], ext[3])
    ax.set_xlim(float(x0), float(x1)); ax.set_ylim(float(y0), float(y1)); ax.set_aspect("equal")
    bar = 10 if (x1-x0) < 120 else 20; bx, by = x0 + (x1-x0)*0.05, y0 + (y1-y0)*0.05
    ax.plot([bx, bx+bar], [by, by], color=INK, lw=2, solid_capstyle="butt", zorder=8)
    ax.text(bx+bar/2, by+(y1-y0)*0.02, f"{bar} km", ha="center", va="bottom", fontsize=7.5, color=INK, zorder=8)
    ax.axis("on"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#d0d7de")
    ax.set_title(label, fontsize=11, color=INK, loc="left", fontweight="bold")

for r, idxs in enumerate(ROWS):
    c = 0
    for i in idxs:
        code, name, cities = LAYOUT[i]
        locator(axes[r, c], code, name, cities); c += 1
        for city, label in cities:
            city_panel(axes[r, c], code, city, label); c += 1

# legend in the last free cell of row 0
lg = axes[0, ncols-1]; lg.axis("off")
items = [("patch", FILL, EDGE, "City limits (TIGER/Line 2025)\nused for gridMET"),
         ("cell", CELL_C, None, "UTCI cell used (0.25°, ~28 km)\nshade and % = weight (share of city)"),
         ("hall", "#7c2d12", None, "Cell containing city hall"),
         ("grid", GRID_C, None, "Downloaded UTCI box (other cells)"),
         ("o", IN_C, None, "METAR airport, inside city limits"),
         ("^", OUT_C, None, "METAR airport, outside city limits"),
         ("*", HALL, None, "City hall")]
for k, (kind, c1, c2, txt) in enumerate(items):
    y = 0.93 - k*0.13
    if kind == "patch": lg.add_patch(plt.Rectangle((0.02, y-0.04), 0.12, 0.08, fc=c1, ec=c2, transform=lg.transAxes))
    elif kind == "cell": lg.add_patch(plt.Rectangle((0.02, y-0.04), 0.12, 0.08, fc=c1, alpha=0.45, ec="none", transform=lg.transAxes))
    elif kind in ("hall", "grid"): lg.add_patch(plt.Rectangle((0.02, y-0.04), 0.12, 0.08, fc="none", ec=c1, lw=2 if kind=="hall" else 0.8, transform=lg.transAxes))
    else: lg.plot([0.08], [y], marker=kind, ms=10 if kind != "*" else 12, color=c1, mec="white", transform=lg.transAxes)
    lg.text(0.18, y, txt, transform=lg.transAxes, va="center", fontsize=8, color=INK)
lg.text(0.02, 0.02, '"=" link: the two cells hold identical values\n(regridding artefact, Step 1). Each city panel\nhas its own scale.',
        transform=lg.transAxes, fontsize=7, color=MUTED, va="bottom")

fig.suptitle("UTCI cells (felt heat, D11 area-weighted) over gridMET city limits (actual temperature) and METAR airports (visibility)",
             fontsize=15, color=INK, x=0.01, ha="left", y=0.995)
fig.text(0.01, 0.967, "UTCI for a city = area-weighted average of every ERA5-HEAT 0.25° cell touching city limits (D11). "
         "Sources: Copernicus ERA5-HEAT time series v1.1; U.S. Census TIGER/Line 2025 Places; IEM ASOS metadata; "
         "Natural Earth 1:50m state outlines.", fontsize=8.5, color=MUTED, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.955))
fig.savefig(FIG/"utci_cells_map.png", dpi=200); fig.savefig(FIG/"utci_cells_map.pdf")
print("saved", FIG/"utci_cells_map.png", "|", len(tab), "cells from Step 2")
