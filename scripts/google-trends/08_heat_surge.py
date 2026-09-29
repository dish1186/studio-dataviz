# Google Trends Step 12 · heat "surge point" per city (headline threshold for "Find Your Threshold"), plus the
# "starts looking" mark carried over from Step 11 (method B).
#
# Input: Step 11 outputs in data/processed/google-trends/heat-threshold/ (not modified):
#   weekly_search_temp_<city>.csv  (weekly "air conditioner" ratio to that year's Jan-Feb level, and the week's mean high)
#   heat_thresholds.csv            (method B = "starts looking", method A = monthly check, typical summer high)
# Surge point, per city and period (all = 2022-2026, before2026 = 2022-2025, 2026 = Jan-Sep 2026):
#   floor     = 1 (a normal January-February week, by construction of the ratio)
#   hot level = median ratio of the hottest 10% of weeks in the period (at least 4 weeks)
#   target    = halfway between them, in plain multiples: (1 + hot level) / 2
#   curve     = weeks sorted by weekly high; running median of the ratio over a window of 10% of the weeks (odd, at
#               least 7), placed at the window's median temperature
#   surge     = the first temperature where the curve reaches the target (linear interpolation between neighbours)
# Uncertainty: 1,000 recomputations on the weeks resampled in 4-week blocks (as in Step 11); 5th-95th percentile.
# Shift = 2026 minus before-2026, with the 5th-95th percentile of paired recomputation differences.
# Run from the repo root: python3 scripts/google-trends/08_heat_surge.py
import csv, math, random, statistics as st

IN = OUT = "data/processed/google-trends/heat-threshold"
CITIES = ["boston", "sanfrancisco", "phoenix", "detroit", "sandiego"]
PERIODS = {"all": range(2022, 2027), "before2026": range(2022, 2026), "2026": range(2026, 2027)}
N_BOOT, SEED, BLOCK, HOT_SHARE = 1000, 20260929, 4, 0.10
rng = random.Random(SEED)


def surge(pts):
    """pts = [(weekly high, ratio)]; returns (surge temperature or None, hot level, target)."""
    pts = sorted(pts)
    k = max(4, round(HOT_SHARE * len(pts)))
    hot = st.median(r for _, r in pts[-k:])
    target = (1 + hot) / 2
    w = max(7, round(0.10 * len(pts)) | 1)
    curve = [(st.median(T for T, _ in pts[i:i + w]), st.median(r for _, r in pts[i:i + w])) for i in range(len(pts) - w + 1)]
    if curve[0][1] >= target:
        return curve[0][0], hot, target
    for (t1, r1), (t2, r2) in zip(curve, curve[1:]):
        if r1 < target <= r2:
            return t1 + (target - r1) / (r2 - r1) * (t2 - t1), hot, target
    return None, hot, target


B = {(r["city"], r["period"]): r for r in csv.DictReader(open(f"{IN}/heat_thresholds.csv", encoding="utf-8"))}
out = []
for city in CITIES:
    rows = list(csv.DictReader(open(f"{IN}/weekly_search_temp_{city}.csv", encoding="utf-8")))
    res = {}
    for per, yrs in PERIODS.items():
        pts = [(float(r["weekly_high_F"]), float(r["ratio"])) for r in rows if int(r["year"]) in yrs]
        s0, hot, target = surge(pts)
        blocks = [pts[i:i + BLOCK] for i in range(0, len(pts), BLOCK)]
        boot = [surge([q for _ in blocks for q in rng.choice(blocks)])[0] for _ in range(N_BOOT)]
        res[per] = (s0, hot, target, boot, len(pts))
    pair = [a - b for a, b in zip(res["2026"][3], res["before2026"][3]) if a is not None and b is not None]
    for per in PERIODS:
        s0, hot, target, boot, n = res[per]
        ok = sorted(x for x in boot if x is not None)
        b = B[(city, per)]
        summer = float(b["typical_summer_high_F_1991_2020"])
        out.append({
            "city": city, "period": per, "n_weeks": n,
            "surge_F": round(s0, 1), "surge_ci90_low_F": round(ok[int(0.05 * len(ok))], 1),
            "surge_ci90_high_F": round(ok[int(0.95 * len(ok)) - 1], 1), "surge_boot_missing": N_BOOT - len(ok),
            "hot_level_ratio": round(hot, 2), "target_ratio": round(target, 2),
            "starts_looking_F": b["B_tipping_F"], "starts_looking_ci90_low_F": b["B_ci90_low_F"],
            "starts_looking_ci90_high_F": b["B_ci90_high_F"],
            "A_halfway_F": b["A_halfway_F"],
            "typical_summer_high_F_1991_2020": summer, "surge_minus_summer_high_F": round(s0 - summer, 1),
            "surge_shift_2026_vs_before_F": round(res["2026"][0] - res["before2026"][0], 1) if per == "2026" else "",
            "surge_shift_ci90": (f"{sorted(pair)[int(0.05 * len(pair))]:.1f} to {sorted(pair)[int(0.95 * len(pair)) - 1]:.1f}"
                                 if per == "2026" else ""),
        })
with open(f"{OUT}/heat_surge.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
for o in out:
    print(o)
