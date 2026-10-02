"""Build data.json for City Heat Thresholds v2 (V13): 7 cities, three layers.
Layer 1 "Heat · AC searches": the 5 original cities use Google Trends Step 12 (heat_surge.csv) as published.
  Eugene and Bakersfield: their January-February searches are 0 in most weeks, so Step 12's ratio (week / that year's
  Jan-Feb level) is undefined. Equivalent rule on the index itself: target = halfway between the Jan-Feb median and the
  median of the hottest 10% of weeks; the surge point is where a running median of searches (sorted by weekly high,
  window 10% of weeks, odd, >= 7) first reaches it. With a non-zero winter level this is the same target as Step 12's
  (1 + hot ratio) / 2. "Starts looking": Step 11's hockey stick, fitted to log2(1 + index) because log2(0) is undefined, with Step 11's
  candidate range for the bend (10th-90th percentile of the city's 2022-2026 weekly highs). (v2 first used a fixed 30-100 F
  range, which let the bend sit below all data in 2026 Bakersfield and gave a meaningless 32 F; fixed.) A bend at either
  edge of the range is reported as no clear start point (Bakersfield: every period).
Layer 1b "Heat · ice cream searches" (added after v3): Google Trends weekly "ice cream", all 7 cities, Step 12's method
  exactly (ice cream has non-zero winter values everywhere): ratio = week / that year's Jan-Feb median; hot level = median
  ratio of the hottest 10% of weeks; surge = where a running median of the ratio (weeks sorted by weekly high, window 10%,
  odd, >= 7) reaches (1 + hot) / 2; "starts looking" = Step 11's hockey stick on log2(ratio), bend searched over the city's
  10th-90th percentile of weekly highs, edges reported as no clear start. Same periods and 4-week block bootstrap.
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
  Gauge point (v5, Gina: same structure as the AC gauge, PM2.5 on the scale, all months of the year): weeks Sep 2021-Sep 2026,
  each placed by its worst PM2.5 day. Clean-air rate = share of weeks with worst day < 12 that spike. Surge point = the lowest
  worst-day level (>= 12) at and above which at least half of weeks, and at least twice the clean-air rate, spike (>= 3 weeks
  above). 90% range: 1,000 recomputations on 4-week blocks; shown when >= 70% of recomputations find a point, otherwise the
  point is marked uncertain. (A 7-week running window was tried first and rejected: chance clusters of moderate weeks
  triggered it, e.g. Bakersfield at 12 ug/m3.)
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
ICEF = {"boston": "boston_ice_5yr.csv", "sanfrancisco": "san fran_ice_5yr.csv", "phoenix": "phoenix_ice_5yr.csv", "detroit": "detroit_ice_5yr.csv",
        "sandiego": "sandiego_ice_5yr.csv", "eugene": "eugene_ice_5yr.csv", "bakersfield": "bakersfield_ice_5yr.csv"}
def ratio_rows(rows):
    usual = {}
    for d, x, y in rows:
        if d[5:7] in ("01", "02"): usual.setdefault(d[:4], []).append(y)
    usual = {k: st.median(v) for k, v in usual.items()}
    return [(d, x, y / usual[d[:4]]) for d, x, y in rows if usual.get(d[:4], 0) > 0]
def ratio_rule(rows):
    rr = ratio_rows(rows)
    if len(rr) < 20: return None
    pts = [(x, y) for _, x, y in rr]; k = max(4, round(0.10 * len(pts)))
    return curve_cross(pts, 1.0, st.median(y for _, y in sorted(pts)[-k:]))
def ratio_hockey(rows, city):
    rr = ratio_rows(rows); best = None
    pts = [(x, math.log2(y)) for _, x, y in rr if y > 0]
    for t0 in GRID[city]:
        xs = [max(0.0, x - t0) for x, _ in pts]; ys = [y for _, y in pts]; mx, my = st.mean(xs), st.mean(ys)
        sxx = sum((a - mx) ** 2 for a in xs)
        if sxx == 0: continue
        b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sxx; a0 = my - b * mx
        sse = sum((c - a0 - b * a) ** 2 for a, c in zip(xs, ys))
        if b > 0 and (best is None or sse < best[1]): best = (t0, sse)
    if not best or best[0] in (GRID[city][0], GRID[city][-1]): return None
    return best[0]
GRID = {}  # per city: Step 11's candidate range, 10th to 90th percentile of all 2022-2026 weekly highs
def air_gauge(R, minn=3):
    R = sorted(R); clean = [sv for m, sv in R if m < 12]
    if not clean: return None, None
    base = sum(clean) / len(clean); tg = max(0.5, 2 * base)
    for i, (m, _) in enumerate(R):
        above = R[i:]
        if len(above) < minn: break
        if m >= 12 and sum(sv for _, sv in above) / len(above) >= tg: return m, base
    return None, base
def hockey(rows, city=None):
    pts = [(x, math.log2(1 + y)) for d, x, y in rows]; best = None
    for t0 in GRID[city]:
        xs = [max(0.0, x - t0) for x, _ in pts]; ys = [y for _, y in pts]; mx, my = st.mean(xs), st.mean(ys)
        sxx = sum((a - mx) ** 2 for a in xs)
        if sxx == 0: continue
        b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sxx; a0 = my - b * mx
        sse = sum((c - a0 - b * a) ** 2 for a, c in zip(xs, ys))
        if b > 0 and (best is None or sse < best[1]): best = (t0, sse)
    if not best or best[0] in (GRID[city][0], GRID[city][-1]): return None  # bend at the edge of the range = no clear start
    return best[0]
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
    Ts = sorted(x for _, x, _ in wk); GRID[c] = range(math.ceil(Ts[len(Ts) // 10]), math.floor(Ts[len(Ts) * 9 // 10]) + 1)
    iw = []
    for w, v in trends(f"data/raw/google-trends/icecream-search-weekly/{ICEF[c]}"):
        s0 = dt.date.fromisoformat(w); ds = [T.get((s0 + dt.timedelta(i)).isoformat()) for i in range(7)]
        if all(x is not None for x in ds) and 2022 <= s0.year <= 2026: iw.append((w, st.mean(ds), v))
    o["ice"] = summarise({p: [r for r in iw if int(r[0][:4]) in y] for p, y in PER.items()}, ratio_rule, 4, lambda rows, c=c: ratio_hockey(rows, c))
    if c in ("eugene", "bakersfield"):
        Ts = sorted(x for _, x, _ in wk); GRID[c] = range(math.ceil(Ts[len(Ts) // 10]), math.floor(Ts[len(Ts) * 9 // 10]) + 1)
        o["search"] = summarise({p: [r for r in wk if int(r[0][:4]) in y] for p, y in PER.items()}, heat_rule, 4, lambda rows, c=c: hockey(rows, c))
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
        if len(ds) >= 4 and w <= "2026-09-20": aw.append((w, max(ds), v))
    vals = sorted(v for *_, v in aw); p75 = vals[int(.75 * (len(vals) - 1))]
    spike = (lambda v: v > 0) if p75 == 0 else (lambda v: v > p75)
    bands, react = [], None
    for lo, hi in ((0, 12), (12, 35.5), (35.5, 55.5), (55.5, 10000)):
        L = [v for _, m, v in aw if lo <= m < hi]; k = sum(spike(v) for v in L)
        bands.append({"lo": lo, "hi": hi, "n": len(L), "k": k})
        if react is None and len(L) >= 2 and k / len(L) > 0.5: react = lo
    R = [(m, 1 if spike(v) else 0) for _, m, v in aw]
    g, base = air_gauge(R)
    blocks = [R[i:i + 4] for i in range(0, len(R), 4)]; bs = []
    for _ in range(N_BOOT):
        t, _ = air_gauge([q for _ in blocks for q in rng.choice(blocks)])
        if t is not None: bs.append(t)
    bs.sort(); valid = len(bs) / N_BOOT
    ab = [sv for m, sv in R if g is not None and m >= g]
    o["air"] = {"bands": bands, "react": react, "spike_above": p75, "n": len(aw),
                "gauge": {"s": None if g is None else round(g, 1), "ci": [round(bs[int(.05 * len(bs))], 1), round(bs[int(.95 * len(bs)) - 1], 1)] if g is not None and valid >= 0.7 else None,
                          "valid": round(valid, 2), "above": [sum(ab), len(ab)], "base": round(base, 3)}}
    o["typ_pm"] = round(st.median(st.median([pm[k] for k in pm if "2022" <= k[:4] <= "2026"]) for _ in [0]), 1)
    o["worst_pm_week"] = round(max(m for _, m, _ in aw), 1)
    OUT[c] = o
    print(name, "| ice", {p: (v["s"], v.get("ci"), v.get("st")) for p, v in o["ice"].items()}, "| search", {p: (v["s"], v.get("ci"), v.get("st")) for p, v in o["search"].items()}, "| check", o.get("search_check_index_method"),
          "\n   ER", {p: (v["s"], v["ci"], v["n"]) for p, v in o["er"].items()}, "\n   air", o["air"], "typ", o["typ_pm"], "worst wk", o["worst_pm_week"], "summer", o["sum"])
json.dump(OUT, open("viz/city-heat-thresholds/data.json", "w"), separators=(",", ":"))
