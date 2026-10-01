"""Small-multiples map: city-limits polygons (gridMET, TIGER/Line 2025 Places)
+ METAR airports + city hall, one panel per study city.
Read-only on inputs. Output: docs/figures/airport_city_map.png (+ .pdf)."""
import csv, math
from pathlib import Path
import shapefile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as MPath
from matplotlib.patches import PathPatch

ROOT = Path(__file__).resolve().parents[2]
POLY = ROOT / "data/processed/gridmet/step03_city_polygons"
TIGER_AK = ROOT / "data/raw/gridmet/tiger_places/tl_2025_02_place.zip"
DIST = ROOT / "data/processed/metar/metar_station_distances.csv"
AUDIT = ROOT / "data/processed/gridmet/step02_boundary_audit/airport_in_city.csv"
OUT = ROOT / "docs/figures"; OUT.mkdir(parents=True, exist_ok=True)

ORDER = [("fairbanks","Fairbanks, AK"),("eugene","Eugene, OR"),("springfield","Springfield, OR"),
 ("sanfrancisco","San Francisco, CA"),("fresno","Fresno, CA"),("delano","Delano, CA"),
 ("bakersfield","Bakersfield, CA"),("losangeles","Los Angeles, CA"),("sandiego","San Diego, CA"),
 ("phoenix","Phoenix, AZ"),("brownsville","Brownsville, TX"),("raymondville","Raymondville, TX"),
 ("detroit","Detroit, MI"),("warren","Warren, MI"),("annarbor","Ann Arbor, MI"),
 ("pittsburgh","Pittsburgh, PA"),("boston","Boston, MA")]

INK, MUTED, FILL, EDGE = "#1f2328", "#6b7280", "#dbe4f0", "#5b7aa6"
IN_C, OUT_C, HALL = "#1f5fbf", "#c2410c", "#1f2328"

stations = {}
for r in csv.DictReader(open(DIST)):
    stations.setdefault(r["city"], []).append(r)
audit = {(r["city"], r["station"]): r for r in csv.DictReader(open(AUDIT))}

def rings(city):
    if city == "fairbanks":  # no gridMET polygon (AK not covered); taken from TIGER for reference
        sf = shapefile.Reader(str(TIGER_AK))
        idx = [i for i, rec in enumerate(sf.records()) if rec["GEOID"] == "0224230"][0]
        shp = sf.shape(idx)
    else:
        shp = shapefile.Reader(str(POLY / f"{city}_citylimits.zip")).shape(0)
    pts, parts = shp.points, list(shp.parts) + [len(shp.points)]
    return [pts[parts[i]:parts[i+1]] for i in range(len(parts)-1)]

fig, axes = plt.subplots(4, 5, figsize=(20, 16.5))
axes = axes.ravel()
for ax, (city, label) in zip(axes, ORDER):
    rs = rings(city); st = stations[city]
    lat0 = float(st[0]["city_hall_lat"]); lon0 = float(st[0]["city_hall_lon"])
    k = math.cos(math.radians(lat0))
    P = lambda lon, lat: ((lon-lon0)*111.32*k, (lat-lat0)*110.57)
    verts, codes = [], []
    for ring in rs:
        xy = [P(*p) for p in ring]
        verts += xy + [xy[0]]; codes += [MPath.MOVETO] + [MPath.LINETO]*(len(xy)-1) + [MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), fc=FILL, ec=EDGE, lw=0.8, zorder=1))
    xs = [v[0] for v in verts]; ys = [v[1] for v in verts]
    ax.plot(0, 0, marker="*", ms=13, color=HALL, mec="white", mew=1, zorder=4)
    for s in st:
        x, y = P(float(s["station_lon"]), float(s["station_lat"]))
        xs.append(x); ys.append(y)
        a = audit.get((city, s["station"]))
        inside = a and a["in_city_limits"] == "True"
        c = IN_C if inside else OUT_C
        ax.plot([0, x], [0, y], ls=(0,(2,2)), lw=0.9, color=MUTED, zorder=2)
        ax.plot(x, y, marker="o" if inside else "^", ms=10, color=c, mec="white", mew=1.5, zorder=5)
        note = "inside city limits" if inside else f"{float(a['km_outside_boundary']):.1f} km outside"
        ax.annotate(f"{s['station']}\n{note}\n{s['distance_km']} km to city hall",
                    (x, y), xytext=(7, -4), textcoords="offset points", fontsize=8,
                    color=INK, va="top", zorder=6,
                    bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
    # square extent with padding
    cx, cy = (max(xs)+min(xs))/2, (max(ys)+min(ys))/2
    half = max(max(xs)-min(xs), max(ys)-min(ys))/2*1.25 + 1.5
    ax.set_xlim(cx-half, cx+half); ax.set_ylim(cy-half, cy+half); ax.set_aspect("equal")
    # scale bar
    nice = [1,2,5,10,20,50]; bar = [n for n in nice if n <= half*0.6][-1]
    bx, by = cx-half*0.92, cy-half*0.9
    ax.plot([bx, bx+bar], [by, by], color=INK, lw=2, solid_capstyle="butt")
    ax.text(bx+bar/2, by+half*0.03, f"{bar} km", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#d0d7de")
    codes_ = " + ".join(s["station"] for s in st)
    ax.set_title(f"{label}", fontsize=12, color=INK, loc="left", fontweight="bold")
    ax.text(0.02, 0.98, f"METAR: {codes_}" + ("\nboundary shown for reference;\nno gridMET temp in Alaska" if city=="fairbanks" else ""),
            transform=ax.transAxes, fontsize=8, color=MUTED, va="top")

# legend panel
for ax in axes[len(ORDER):]: ax.axis("off")
lg = axes[len(ORDER)]
lg.add_patch(plt.Rectangle((0.05,0.78),0.12,0.08, fc=FILL, ec=EDGE, transform=lg.transAxes))
lg.text(0.22,0.82,"City limits (TIGER/Line 2025 Places)\nused for gridMET actual temp",transform=lg.transAxes,va="center",fontsize=9.5,color=INK)
lg.plot([0.11],[0.64],marker="o",ms=10,color=IN_C,mec="white",transform=lg.transAxes)
lg.text(0.22,0.64,"METAR airport, inside city limits",transform=lg.transAxes,va="center",fontsize=9.5,color=INK)
lg.plot([0.11],[0.50],marker="^",ms=10,color=OUT_C,mec="white",transform=lg.transAxes)
lg.text(0.22,0.50,"METAR airport, outside city limits",transform=lg.transAxes,va="center",fontsize=9.5,color=INK)
lg.plot([0.11],[0.36],marker="*",ms=13,color=HALL,mec="white",transform=lg.transAxes)
lg.text(0.22,0.36,"City hall (distance reference)",transform=lg.transAxes,va="center",fontsize=9.5,color=INK)
lg.text(0.05,0.18,"Each panel has its own scale.\nSpringfield uses Eugene's EUG.\nDetroit and Pittsburgh average two airports.",
        transform=lg.transAxes,va="center",fontsize=8.5,color=MUTED)

fig.suptitle("Where the data comes from: city limits (actual temperature) and airport stations (visibility)",
             fontsize=16, color=INK, x=0.01, ha="left", y=0.995)
fig.text(0.01, 0.968, "Sources: U.S. Census TIGER/Line 2025 Places; Iowa Environmental Mesonet ASOS station metadata; "
         "distances from scripts/metar/08b_station_distances.py and scripts/gridmet/02_boundary_audit.py.",
         fontsize=9, color=MUTED, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(OUT/"airport_city_map.png", dpi=200); fig.savefig(OUT/"airport_city_map.pdf")
print("saved")
