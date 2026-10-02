"""Build data.json for City Heat Thresholds v2 (V13): 7 cities, three layers.
Layer 1 "Heat · AC searches": the 5 original cities use Google Trends Step 12 (heat_surge.csv) as published.
  Eugene and Bakersfield: their January-February searches are 0 in most weeks, so Step 12's ratio (week / that year's
  Jan-Feb level) is undefined. Equivalent rule on the index itself: target = halfway between the Jan-Feb median and the
  median of the hottest 10% of weeks; the surge point is where a running median of searches (sorted by weekly high,
  window 10% of weeks, odd, >= 7) first reaches it. With a non-zero winter level this is the same target as Step 12's
  (1 + hot ratio) / 2. "Starts looking": Step 11's hockey stick, fitted to log2(1 + index) because log2(0) is undefined.
Layer 2 "Heat · ER visits": the same halfway rule on DAILY heat-related ER visits (per 100,000 ER visits, HHS region)
  against the DAILY high: floor = Jan-Feb median, hot level = median of the hottest 10% of days, running-median window
  10% of days. Region: Boston 1, Detroit 5, Eugene 10, Phoenix / San Diego / San Francisco / Bakersfield 9 (shared).
Layer 3 "Air · purifier searches": weekly Google Trends "air purifier", 2022-2026, each week placed by its WORST day of
  PM2.5 (OpenAQ city mean, >= 4 days). (A halfway rule on weekly mean PM2.5 was tried first and rejected: purifier searches
  follow the season, so it put "surges" below normal air.) A week has a purifier spike when searches are above the city's
  75th percentile of weeks (if that is 0, any searches). Share of spike weeks in four EPA-based bands of the worst day:
  good < 12, moderate 12-35.4, unhealthy for sensitive groups 35.5-55.4, unhealthy 55.5+. Reaction point = the lower edge of
  the first band (>= 2 weeks) where more than half of weeks spike. Weeks 2026-03-22 to 2026-06-28 left out (national surge).
  All years together only: per-period counts of bad-air weeks are too small.
All layers: periods all = 2022-2026, before2026 = 2022-2025, 2026 = Jan-Sep 2026; 1,000 recomputations on 4-week (weekly)
or 28-day (daily) blocks; 5th-95th percentile, as in Step 12. Typical summer high = mean Jun-Aug daily high 1991-2020.
Run from the repo root: python3 viz/city-heat-thresholds/build.py"""
import csv, datetime as dt, json, math, random, statistics as st, collections as C
CITIES = {"boston": ("Boston", "BOS", "boston_manch_trends_aircon_5yr.csv", "Region 1"),
          "sanfrancisco": ("San Francisco", "SF", "sanfran_metro_trends_aircon_5yr.csv", "Region 9"),
          "phoenix": ("Phoenix", "PHX", "phoenix_trends_aircon_5yr.csv", "Region 9"),
          "detroit": ("Detroit", "DET", "detroit_trends_aircon_5yr.csv", "Region 5"),
          "sandiego": ("San Diego", "SD", "sandiego_trends_aircon_5yr.csv", "Region 9"),
          "eugene": ("Eugene", "EUG", "eugene_aircon_5yr.csv", "Region 10"),
          "bakersfield": ("Bakersfield", "BAK", "bakersfield_aircon_5yr.csv", "Region 9")}
PER = {"all": range(2022, 2027), "pre": range(2022, 2026), "y26": range(2026, 2027)}
N_BOOT, SEED = 1000, 20260929
rng = random.Random(SEED)

def tmax(c):
    out = {}
    for f in (f"data/raw/gridmet/climateengine/gridmet_tmax_{c}_1991-2020.csv", f"data/raw/gridmet/climateengine/gridmet_tmax_{c}_2016-2026.csv"):
        for r in list(csv.reader(open(f, encoding="utf-8-sig")))[1:]:
            if len(r) > 1 and r[1] not in ("", "NaN"): out[r[0].strip('"')] = float(r[1])
    return out
def trends(path):
    return [(w, 0 if v == "<1" else int(v)) for w, v in list(csv.reader(open(path)))[3:] if w]
def curve_cross(pts, floor, hot):
    """pts = [(x, y)]; running median of y over x-sorted points; first x where it reaches (floor + hot) / 2."""
    if hot <= floor: return None
    target = (floor + hot) / 2; pts = sorted(pts); w = max(7, round(0.10 * len(pts)) | 1)
    cur = [(st.median(x for x, _ in pts[i:i + w]), st.median(y for _, y in pts[i:i + w])) for i in range(len(pts) - w + 1)]
    if not cur: return None
    if cur[0][1] >= target: return cur[0][0]
    for (x1, y1), (x2, y2) in zip(cur, cur[1:]):
        if y1 < target <= y2: return x1 + (target - y1) / (y2 - y1) * (x2 - x1)
    return None
def heat_rule(rows):
    """rows = [(date, x, y)] for all months of the period; floor = Jan-Feb median y (pooled over the period's years);
    hot = median y of the hottest 10% (by x) of all rows in the period."""
    win = [y for d, x, y in rows if d[5:7] in ("01", "02")]
    if not win: return None
    pts = [(x, y) for d, x, y in rows]; k = max(4, round(0.10 * len(pts)))
    hot = st.median(y for _, y in sorted(pts)[-k:])
    return curve_cross(pts, st.median(win), hot)
def air_rule(rows):
    pts = sorted((x, y) for d, x, y in rows); n = len(pts)
    if n < 20: return None
    floor = st.median(y for _, y in pts[: n // 2]); k = max(4, round(0.10 * n))
    return curve_cross(pts, floor, st.median(y for _, y in pts[-k:]))
def hockey(rows):
    pts = [(x, math.log2(1 + y)) for d, x, y in rows]; best = None
    for t0 in range(30, 101):
        xs = [max(0.0, x - t0) for x, _ in pts]; ys = [y for _, y in pts]; mx, my = st.mean(xs), st.mean(ys)
        sxx = sum((a - mx) ** 2 for a in xs)
        if sxx == 0: continue
        b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sxx; a0 = my - b * mx
        sse = sum((c - a0 - b * a) ** 2 for a, c in zip(xs, ys))
        if b > 0 and (best is None or sse < best[1]): best = (t0, sse)
    return best[0] if best else None
def boot(rows, rule, block):
    blocks = [rows[i:i + block] for i in range(0, len(rows), block)]; v = []
    for _ in range(N_BOOT):
        r = rule([q for _ in blocks for q in rng.choice(blocks)])
        if r is not None: v.append(r)
    if len(v) < 0.5 * N_BOOT: return None, N_BOOT - len(v)
    v.sort(); return [round(v[int(.05 * len(v))], 1), round(v[int(.95 * len(v)) - 1], 1)], N_BOOT - len(v)
def summarise(rows_by_per, rule, block, extra=None):
    out = {}
    for p, rows in rows_by_per.items():
        s = rule(rows); ci, miss = boot(rows, rule, block) if s is not None else (None, None)
        out[p] = {"s": None if s is None else round(s, 1), "ci": ci, "boot_missing": miss, "n": len(rows)}
        if extra: out[p]["st"] = extra(rows)
    return out

ER = C.defaultdict(dict)
for r in csv.DictReader(open("data/processed/cdc-tracking/daily_hri_ed_rate_by_hhs_region.csv")):
    if r["suppressed"] == "0": ER[r["hhs_region"]][r["date"]] = float(r["hri_ed_per_100k_ed_visits"])
S12 = {(r["city"], r["period"]): r for r in csv.DictReader(open("data/processed/google-trends/heat-threshold/heat_surge.csv"))}
PMAP = {"all": "all", "pre": "before2026", "y26": "2026"}
OUT = {}
for c, (name, ab, acf, reg) in CITIES.items():
    T = tmax(c)
    summer = st.mean(v for d, v in T.items() if "1991" <= d[:4] <= "2020" and d[5:7] in ("06", "07", "08"))
    wk = []
    for w, v in trends(f"data/raw/google-trends/heat-search-weekly/{acf}"):
        s0 = dt.date.fromisoformat(w); ds = [T.get((s0 + dt.timedelta(i)).isoformat()) for i in range(7)]
        if all(x is not None for x in ds) and 2022 <= s0.year <= 2026: wk.append((w, st.mean(ds), v))
    o = {"n": name, "a": ab, "region": reg, "sum": round(summer, 1)}
    if c in ("eugene", "bakersfield"):
        o["search"] = summarise({p: [r for r in wk if int(r[0][:4]) in y] for p, y in PER.items()}, heat_rule, 4, hockey)
        o["search_method"] = "index (winter level 0)"
    else:
        o["search"] = {p: {"s": float(S12[(c, PMAP[p])]["surge_F"]), "ci": [float(S12[(c, PMAP[p])]["surge_ci90_low_F"]), float(S12[(c, PMAP[p])]["surge_ci90_high_F"])],
                           "st": float(S12[(c, PMAP[p])]["starts_looking_F"]), "n": int(S12[(c, PMAP[p])]["n_weeks"])} for p in PER}
        o["search_method"] = "Step 12 (as published)"
        o["search_check_index_method"] = {p: heat_rule([r for r in wk if int(r[0][:4]) in y]) for p, y in PER.items()}
    er = [(d, T[d], v) for d, v in sorted(ER[reg].items()) if d in T and "2022" <= d[:4] <= "2026"]
    o["er"] = summarise({p: [r for r in er if int(r[0][:4]) in y] for p, y in PER.items()}, heat_rule, 28)
    pm = {r["date"]: float(r["all_mean"]) for r in csv.DictReader(open(f"data/processed/openaq/step05_averages/pm25_{c}_daily.csv")) if r["all_mean"]}
    aw = []
    for w, v in trends(f"data/raw/google-trends/air-search-weekly/{c}_purifier_5yr.csv"):
        if "2026-03-22" <= w <= "2026-06-28": continue
        s0 = dt.date.fromisoformat(w); ds = [pm[k] for k in ((s0 + dt.timedelta(i)).isoformat() for i in range(7)) if k in pm]
        if len(ds) >= 4 and 2022 <= s0.year <= 2026: aw.append((w, max(ds), v))
    vals = sorted(v for *_, v in aw); p75 = vals[int(.75 * (len(vals) - 1))]
    spike = (lambda v: v > 0) if p75 == 0 else (lambda v: v > p75)
    bands, react = [], None
    for lo, hi in ((0, 12), (12, 35.5), (35.5, 55.5), (55.5, 10000)):
        L = [v for _, m, v in aw if lo <= m < hi]; k = sum(spike(v) for v in L)
        bands.append({"lo": lo, "hi": hi, "n": len(L), "k": k})
        if react is None and len(L) >= 2 and k / len(L) > 0.5: react = lo
    o["air"] = {"bands": bands, "react": react, "spike_above": p75, "n": len(aw)}
    o["typ_pm"] = round(st.median(st.median([pm[k] for k in pm if "2022" <= k[:4] <= "2026"]) for _ in [0]), 1)
    o["worst_pm_week"] = round(max(m for _, m, _ in aw), 1)
    OUT[c] = o
    print(name, "| search", {p: (v["s"], v.get("ci"), v.get("st")) for p, v in o["search"].items()}, "| check", o.get("search_check_index_method"),
          "\n   ER", {p: (v["s"], v["ci"], v["n"]) for p, v in o["er"].items()}, "\n   air", o["air"], "typ", o["typ_pm"], "worst wk", o["worst_pm_week"], "summer", o["sum"])
json.dump(OUT, open("viz/city-heat-thresholds/data.json", "w"), separators=(",", ":"))
