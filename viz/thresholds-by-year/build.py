"""Build data.json for "Thresholds by Year" (V12): Eugene and Bakersfield, heat and air, one threshold per action per year.

Method (all choices are Claude's, flagged in logs/data-log-gina.md V12, not yet approved):
1. Units. Heat: May-Sep days (ER) or Sunday-start weeks with >= 5 May-Sep days (searches, news).
   Air: all-year days or weeks with >= 4 days of PM2.5. A week's hazard = its WORST day (max), because people
   react to the bad days; ER uses the same day's hazard.
2. "Strong reaction" = the unit's value is above that city's 75th percentile for that action over all years
   (if the 75th percentile is 0, any value above 0). One fixed bar for all years, so years are comparable.
3. Each year, fit a logistic curve: P(strong reaction) = 1 / (1 + exp(-(a + b*h))), h = hazard
   (heat: degF; air: log of PM2.5 + 1, since reactions scale with multiples of PM2.5). Slightly penalised slope
   (ridge, lambda = 1 on the standardised scale) so small years with clean separation still give a finite answer.
4. Threshold = the hazard where P = 50% (h50 = -a/b): the level at which a strong reaction becomes more likely
   than not. Only reported when b > 0, the year has >= 10 units with >= 3 strong and >= 3 not-strong, and h50 lies
   no more than 10% beyond the hottest/worst unit seen that year (otherwise "not reached").
5. Second measure, every year: share of DANGEROUS units with a strong reaction vs share of safe units.
   Dangerous = felt heat >= 89.6 degF (UTCI strong heat stress; for weeks, the week's worst day) or
   PM2.5 >= 35.5 ug/m3 (EPA "unhealthy for sensitive groups"; for weeks, the week's worst day).
6. 95% range: block bootstrap within the year (7-day blocks for days, 3-week blocks for weeks), 300 resamples;
   reported when >= 70% of resamples give a valid threshold.
Run from the repo root: python3 viz/thresholds-by-year/build.py
"""
import csv, json, math, random, datetime as dt, collections as C, statistics as st

CITY = {"eugene": {"label": "Eugene", "region": "Region 10", "ac": "eugene_aircon_5yr.csv", "ice": "eugene_ice_5yr.csv",
                   "drops": "eugene_drops_5yr.csv", "pur": "eugene_purifier_5yr.csv"},
        "bakersfield": {"label": "Bakersfield", "region": "Region 9", "ac": "bakersfield_aircon_5yr.csv", "ice": "bakersfield_ice_5yr.csv",
                        "drops": "bakersfield_drops_5yr.csv", "pur": "bakersfield_purifier_5yr.csv"}}
SURGE = ("2026-03-22", "2026-06-28")  # national spring-2026 purifier surge, left out
summer = lambda d: 5 <= int(d[5:7]) <= 9

def trends(path):
    return {w: (0 if v == "<1" else int(v)) for w, v in list(csv.reader(open(path)))[3:] if w}
def mc_weekly(path):
    wk = C.defaultdict(int)
    for r in csv.DictReader(open(path)):
        x = dt.date.fromisoformat(r["date"]); wk[(x - dt.timedelta((x.weekday() + 1) % 7)).isoformat()] += int(r["stories"])
    return wk
def week_units(values, hazard, need, season, dang, line):
    out = []
    for w, y in values.items():
        s0 = dt.date.fromisoformat(w); ks = [(s0 + dt.timedelta(i)).isoformat() for i in range(7)]
        hv = [hazard[k] for k in ks if k in hazard and season(k)]
        dv = [dang[k] for k in ks if k in dang and season(k)]
        if len(hv) >= need: out.append((w, int(ks[3][:4]), max(hv), y, (max(dv) >= line) if dv else None))
    return out

def fit(units, logx):
    """penalised logistic regression by Newton steps; returns (a, b) on the original-or-log hazard scale"""
    xs = [math.log1p(u[0]) if logx else u[0] for u in units]; ys = [u[1] for u in units]
    m, s = st.mean(xs), (st.pstdev(xs) or 1)
    z = [(x - m) / s for x in xs]; a = b = 0.0; lam = 1.0
    for _ in range(50):
        ga = gb = haa = hab = hbb = 0.0
        for zi, yi in zip(z, ys):
            p = 1 / (1 + math.exp(-max(-30, min(30, a + b * zi)))); w = p * (1 - p)
            ga += yi - p; gb += (yi - p) * zi; haa += w; hab += w * zi; hbb += w * zi * zi
        gb -= lam * b; hbb += lam
        det = haa * hbb - hab * hab
        if det <= 1e-12: break
        da = (hbb * ga - hab * gb) / det; db = (haa * gb - hab * ga) / det
        a += da; b += db
        if abs(da) + abs(db) < 1e-8: break
    # back to the unstandardised scale: a + b*(x-m)/s
    return a - b * m / s, b / s

def h50(units, logx, maxh):
    if len(units) < 10: return None, None, None
    ns = sum(u[1] for u in units)
    if ns < 3 or len(units) - ns < 3: return None, None, None
    a, b = fit(units, logx)
    if b <= 0: return None, a, b
    t = -a / b; t = math.expm1(t) if logx else t
    return (t if t <= maxh * 1.10 else None), a, b

def boot(units, logx, maxh, block, reps=300, seed=1):
    rnd = random.Random(seed); n = len(units); vals = []
    for _ in range(reps):
        smp = []
        while len(smp) < n:
            i = rnd.randrange(0, max(1, n - block + 1)); smp += units[i:i + block]
        t, _, _ = h50(smp[:n], logx, maxh)
        if t is not None: vals.append(t)
    if len(vals) < 0.7 * reps: return None
    vals.sort(); return [round(vals[int(.025 * len(vals))], 1), round(vals[int(.975 * len(vals)) - 1], 1)]

def bins_for(units, edges):
    out = []
    for lo, hi in zip(edges, edges[1:]):
        L = [u for u in units if lo <= u[0] < hi]
        if L: out.append([lo, hi, len(L), round(sum(u[1] for u in L) / len(L), 3)])
    return out

def series(raw, logx, block, edges):
    """raw: list of (date_or_week, year, hazard, value). Returns per-year thresholds and pooled fit."""
    vals = sorted(r[3] for r in raw); p75 = vals[int(.75 * (len(vals) - 1))]
    strong = (lambda v: v > 0) if p75 == 0 else (lambda v: v > p75)
    by = C.defaultdict(list)
    dg = C.defaultdict(list)
    for k, y, h, v, dz in sorted(raw):
        by[y].append((h, 1 if strong(v) else 0, k))
        if dz is not None: dg[y].append((dz, 1 if strong(v) else 0))
    out = {"strong_above": p75, "n_all": len(raw), "years": {}}
    allu = [(h, s) for y in by for h, s, _ in by[y]]
    t, a, b = h50(allu, logx, max(h for h, _ in allu))
    out["all"] = {"h50": None if t is None else round(t, 1), "a": a, "b": b, "bins": bins_for(allu, edges)}
    for y, L in sorted(by.items()):
        u = [(h, s) for h, s, _ in L]; mx = max(h for h, _ in u)
        t, a, b = h50(u, logx, mx)
        out["years"][y] = {"n": len(u), "ns": sum(s for _, s in u), "max": round(mx, 1), "h50": None if t is None else round(t, 1),
                           "ci": boot(u, logx, mx, block) if t is not None else None, "a": a, "b": b, "bins": bins_for(u, edges)}
        D = [s for dz, s in dg[y] if dz]; S = [s for dz, s in dg[y] if not dz]
        out["years"][y]["dang"] = [len(D), round(sum(D) / len(D), 3) if D else None]
        out["years"][y]["safe"] = [len(S), round(sum(S) / len(S), 3) if S else None]
    return out

ER = C.defaultdict(dict)
for r in csv.DictReader(open("data/processed/cdc-tracking/daily_hri_ed_rate_by_hhs_region.csv")):
    if r["suppressed"] == "0": ER[r["hhs_region"]][r["date"]] = float(r["hri_ed_per_100k_ed_visits"])

OUT = {}
HEAT_EDGES = list(range(40, 131, 5)); AIR_EDGES = [0, 5, 9, 15, 25, 35.5, 55.5, 125.5, 1000]
for c, m in CITY.items():
    felt = {r["date"]: float(r["utci_max_f"]) for r in csv.DictReader(open(f"data/processed/utci/final/utci_{c}_daily.csv")) if r["utci_max_f"] and summer(r["date"])}
    high = {r["date"]: float(r["tmax_f"]) for r in csv.DictReader(open(f"data/processed/gridmet/final/temp_{c}_daily.csv")) if r["tmax_f"] and summer(r["date"])}
    pm = {r["date"]: float(r["all_mean"]) for r in csv.DictReader(open(f"data/processed/openaq/step05_averages/pm25_{c}_daily.csv")) if r["all_mean"]}
    OUT[c] = {"label": m["label"], "region": m["region"], "heat": {}, "air": {}}
    ac, ice = trends(f"data/raw/google-trends/heat-search-weekly/{m['ac']}"), trends(f"data/raw/google-trends/icecream-search-weekly/{m['ice']}")
    hn = mc_weekly(f"data/processed/heat-media/heat_media_{c}.csv")
    for hk, H in (("felt", felt), ("high", high)):
        er = [(d, int(d[:4]), H[d], ER[m["region"]][d], (felt[d] >= 89.6) if d in felt else None) for d in H if d in ER[m["region"]]]
        OUT[c]["heat"][hk] = {
            "er": series(er, False, 7, HEAT_EDGES),
            "ac": series(week_units(ac, H, 5, summer, felt, 89.6), False, 3, HEAT_EDGES),
            "ice": series(week_units(ice, H, 5, summer, felt, 89.6), False, 3, HEAT_EDGES),
            "news": series(week_units(hn, H, 5, summer, felt, 89.6), False, 3, HEAT_EDGES)}
    pur = {w: v for w, v in trends(f"data/raw/google-trends/air-search-weekly/{m['pur']}").items() if not (SURGE[0] <= w <= SURGE[1])}
    drops = trends(f"data/raw/google-trends/eyedrops-search/{m['drops']}")
    an = mc_weekly(f"data/processed/mediacloud-attention/mediacloud_attention_{c}.csv")
    allyear = lambda d: True
    OUT[c]["air"]["pm"] = {
        "pur": series(week_units(pur, pm, 4, allyear, pm, 35.5), True, 3, AIR_EDGES),
        "drops": series(week_units(drops, pm, 4, allyear, pm, 35.5), True, 3, AIR_EDGES),
        "news": series(week_units(an, pm, 4, allyear, pm, 35.5), True, 3, AIR_EDGES)}
json.dump(OUT, open("viz/thresholds-by-year/data.json", "w"), separators=(",", ":"))
for c in OUT:
    for hz, hd in ((k, OUT[c][k]) for k in ("heat", "air")):
        for hk, acts in hd.items():
            for ak, s in acts.items():
                yrs = {y: (v["h50"], v["dang"], v["safe"]) for y, v in s["years"].items()}
                print(c, hz, hk, ak, "strong>", s["strong_above"], "| all:", s["all"]["h50"], "|", yrs)
