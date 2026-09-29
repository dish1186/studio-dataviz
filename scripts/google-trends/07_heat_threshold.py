# Google Trends Step 11 · heat threshold per city: the temperature at which "air conditioner" searches start to climb.
#
# For "Find Your Threshold" (heat only, first version). Five cities: Boston, San Francisco, Phoenix, Detroit, San Diego.
# Inputs (not modified):
#   weekly searches  data/raw/google-trends/heat-search-weekly/<city>_trends_aircon_5yr.csv   (2021-09-26 to 2026-09-27)
#   monthly searches data/raw/google-trends/heat-search/<metro>-heat-search.csv, "air conditioner" column (2016-01 to 2026-09)
#   daily highs      data/raw/gridmet/climateengine/gridmet_tmax_<city>_2016-2026.csv and _1991-2020.csv (deg F)
#
# 1. Weekly high = mean of the 7 daily highs in the Trends week (Sunday-Saturday); weeks without all 7 days are dropped.
# 2. Usual level: searches in the same year's January-February weeks (median). ratio = week's searches / usual level.
#    Per year, because 2026 sits higher all year (Step 10). Weeks before 2022 have no January-February of their own and
#    are dropped.
# 3. Method B (headline) - tipping point: fit a "hockey stick" to log2(ratio) against weekly high:
#    flat below T*, rising in a straight line above it. T* (1 deg F steps, least squares, same candidate range for every
#    period) = the tipping temperature. Fitted for three periods: all (2022-2026), before 2026 (2022-2025), 2026 alone
#    (Jan-Sep). Uncertainty: refit 1,000 times on the weeks resampled in 4-week blocks (keeps neighbouring weeks together;
#    works for one year too); 5th-95th percentile. Shift = 2026 minus before-2026, with its own 5th-95th percentile from
#    the paired refits.
# 4. Heat, not calendar (all years): in May-September, compare weeks within the same month of the same year (both measures minus
#    their year-month mean). Spearman rho > 0 means a hotter week gets more searches than a cooler week that same month.
#    Chance test: shuffle temperatures within each year-month 1,000 times.
# 5. Method A (check) - halfway point, monthly, for 2016-2025 and for 2026 (Jan-Aug): monthly mean high vs monthly ratio (same Jan-Feb usual level);
#    medians in 2 deg F bins; T50 = temperature where the binned median first reaches halfway between the lowest and
#    highest bin (linear interpolation). Partial last month (2026-09) dropped.
# 6. Typical summer high = mean daily high for June-August 1991-2020 (for "X deg above a typical summer day").
# Run from the repo root: python3 scripts/google-trends/07_heat_threshold.py
import csv, datetime as dt, math, os, random, statistics as st
from collections import defaultdict

CITIES = {  # key: (weekly file, monthly file, gridMET name)
    "boston": ("boston_manch", "boston MA-Manchester-NH", "boston"),
    "sanfrancisco": ("sanfran_metro", "San Francisco-Oakland-San Jose CA-ca", "sanfrancisco"),
    "phoenix": ("phoenix", "phoenix-az", "phoenix"),
    "detroit": ("detroit", "detroit-mi", "detroit"),
    "sandiego": ("sandiego", "sandiego-ca", "sandiego"),
}
OUT = "data/processed/google-trends/heat-threshold"
N_BOOT, N_PERM, SEED, BLOCK = 1000, 1000, 20260929, 4
PERIODS = {"all": range(2022, 2027), "before2026": range(2022, 2026), "2026": range(2026, 2027)}
os.makedirs(OUT, exist_ok=True)
rng = random.Random(SEED)


def read_tmax(fn):
    L = open(fn, encoding="utf-8-sig").read().splitlines()[1:]
    return {dt.date.fromisoformat(a.strip('"')): float(b) for a, b in (l.split(",") for l in L if l)}


def read_weekly(fn):
    L = open(fn, encoding="utf-8").read().splitlines()
    assert L[0] == "Category: All categories" and L[2].startswith("Week,air conditioner"), fn
    return [(dt.date.fromisoformat(a), int(b)) for a, b in (l.split(",") for l in L[3:] if l)]


def hockey(pts, grid):
    """Least-squares hockey stick y = a + b*max(0, T - T*); returns (T*, a, b, sse)."""
    best = None
    for t0 in grid:
        x = [max(0.0, T - t0) for T, _ in pts]; y = [v for _, v in pts]
        mx, my = st.mean(x), st.mean(y)
        sxx = sum((xi - mx) ** 2 for xi in x)
        if sxx == 0:
            continue
        b = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / sxx
        a = my - b * mx
        sse = sum((yi - a - b * xi) ** 2 for xi, yi in zip(x, y))
        if best is None or sse < best[3]:
            best = (t0, a, b, sse)
    return best


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2
        i = j + 1
    return r


spearman = lambda a, b: st.correlation(rank(a), rank(b))
summary = []
for city, (wk, mo, gm) in CITIES.items():
    tmax = read_tmax(f"data/raw/gridmet/climateengine/gridmet_tmax_{gm}_2016-2026.csv")
    clim = read_tmax(f"data/raw/gridmet/climateengine/gridmet_tmax_{gm}_1991-2020.csv")
    weekly = read_weekly(f"data/raw/google-trends/heat-search-weekly/{wk}_trends_aircon_5yr.csv")
    usual = {y: st.median([v for d, v in weekly if d.year == y and d.month <= 2]) for y in range(2022, 2027)}
    rows = []
    for d0, v in weekly:
        days = [tmax.get(d0 + dt.timedelta(k)) for k in range(7)]
        if d0.year < 2022 or None in days:
            continue
        T = st.mean(days); r = v / usual[d0.year]
        rows.append({"week_start": d0.isoformat(), "search": v, "usual_level": usual[d0.year], "ratio": round(r, 3),
                     "weekly_high_F": round(T, 2), "year": d0.year, "month": d0.month})
    with open(f"{OUT}/weekly_search_temp_{city}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    # Method B, per period
    Ts = sorted(r["weekly_high_F"] for r in rows)
    grid = range(math.ceil(Ts[len(Ts) // 10]), math.floor(Ts[len(Ts) * 9 // 10]) + 1)
    B = {}
    for per, yrs in PERIODS.items():
        pts = [(r["weekly_high_F"], math.log2(r["ratio"])) for r in rows if r["year"] in yrs]
        blocks = [pts[i:i + BLOCK] for i in range(0, len(pts), BLOCK)]
        t0, a0, b0, _ = hockey(pts, grid)
        boot = [hockey([q for _ in blocks for q in rng.choice(blocks)], grid)[0] for _ in range(N_BOOT)]
        B[per] = {"t0": t0, "a": a0, "b": b0, "boot": boot, "n": len(pts)}
    years = sorted({r["year"] for r in rows})
    shift = sorted(x - y for x, y in zip(B["2026"]["boot"], B["before2026"]["boot"]))
    ci = lambda v: (sorted(v)[int(0.05 * N_BOOT)], sorted(v)[int(0.95 * N_BOOT) - 1])

    # Heat-not-calendar check
    warm = [r for r in rows if 5 <= r["month"] <= 9]
    grp = defaultdict(list)
    for r in warm:
        grp[(r["year"], r["month"])].append(r)
    dT, dR, groups = [], [], []
    for g in grp.values():
        mT = st.mean(r["weekly_high_F"] for r in g); mR = st.mean(math.log2(r["ratio"]) for r in g)
        dT += [r["weekly_high_F"] - mT for r in g]; dR += [math.log2(r["ratio"]) - mR for r in g]
        groups.append(len(g))
    rho = spearman(dT, dR)
    hits = 0
    for _ in range(N_PERM):
        sh, i = [], 0
        for n in groups:
            part = dT[i:i + n]; rng.shuffle(part); sh += part; i += n
        hits += spearman(sh, dR) >= rho
    p = (hits + 1) / (N_PERM + 1)

    # Method A (monthly)
    M = list(csv.DictReader(open(f"data/raw/google-trends/heat-search/{mo}-heat-search.csv", encoding="utf-8")))
    ms = {r["Time"][:7]: int(r["air conditioner"]) for r in M}
    musual = {y: st.median([ms[f"{y}-01"], ms[f"{y}-02"]]) for y in range(2016, 2027)}
    mt = defaultdict(list)
    for d, T in tmax.items():
        mt[f"{d.year}-{d.month:02d}"].append(T)
    def halfway(keep):
        mpts = [(st.mean(mt[k]), v / musual[int(k[:4])]) for k, v in ms.items()
                if k != "2026-09" and k in mt and keep(int(k[:4])) and musual[int(k[:4])] > 0]
        bins = defaultdict(list)
        for T, r in mpts:
            bins[2 * math.floor(T / 2)].append(r)
        bm = sorted((k + 1, st.median(v)) for k, v in bins.items() if len(v) >= (3 if len(mpts) > 24 else 1))
        lo, hi = min(v for _, v in bm), max(v for _, v in bm)
        half = lo + (hi - lo) / 2
        for (x1, y1), (x2, y2) in zip(bm, bm[1:]):
            if y1 < half <= y2:
                return round(x1 + (half - y1) / (y2 - y1) * (x2 - x1), 1), len(mpts)
        return "", len(mpts)
    A_pre, nA_pre = halfway(lambda y: y < 2026)
    A_26, nA_26 = halfway(lambda y: y == 2026)

    summer = st.mean(T for d, T in clim.items() if d.month in (6, 7, 8))
    for per in PERIODS:
        lo_, hi_ = ci(B[per]["boot"])
        summary.append({"city": city, "period": per, "n_weeks": B[per]["n"],
                        "B_tipping_F": B[per]["t0"], "B_ci90_low_F": lo_, "B_ci90_high_F": hi_,
                        "B_flat_ratio": round(2 ** B[per]["a"], 2), "B_doublings_per_10F": round(10 * B[per]["b"], 2),
                        "shift_2026_vs_before_F": B["2026"]["t0"] - B["before2026"]["t0"] if per == "2026" else "",
                        "shift_ci90": f"{ci(shift)[0]} to {ci(shift)[1]}" if per == "2026" else "",
                        "within_month_rho": round(rho, 3) if per == "all" else "",
                        "within_month_p": round(p, 4) if per == "all" else "",
                        "A_halfway_F": {"all": "", "before2026": A_pre, "2026": A_26}[per],
                        "A_months": {"all": "", "before2026": nA_pre, "2026": nA_26}[per],
                        "typical_summer_high_F_1991_2020": round(summer, 1),
                        "B_minus_summer_high_F": round(B[per]["t0"] - summer, 1)})
with open(f"{OUT}/heat_thresholds.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
for s in summary:
    print(s)
