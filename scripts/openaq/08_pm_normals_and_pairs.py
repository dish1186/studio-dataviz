# Step 8 · OpenAQ · PM2.5 normal, ratio-to-normal and city pairs for the PM2.5 experiment (docs/experiment-design-pm25.md).
# PM2.5 only; no Reddit data is read. Pairs are fixed here, before any event-week Reddit file is opened.
#
# Input (read only): data/processed/openaq/step07_screening/city_screening.csv and weekly_all.csv (reference monitors).
# Per city (the 10 that passed checks 1 and 3):
#   Event week     = Step 7's worst valid non-fireworks week.
#   PM2.5 normal   = median of the weekly averages of the event's calendar month (a week belongs to the month of its
#                    Thursday), 2019-2025, excluding the event week. Only valid weeks (>= 5 of 7 days) count; fireworks
#                    weeks and weeks above 35.5 are kept, since the normal describes what residents are used to
#                    (Claude's choices, flagged).
#   Ratio          = event-week average / PM2.5 normal.
#   Shifting-normal check (design doc confounds; definitions Claude's choices, flagged):
#     polluted normal week = a normal week with at least one day >= 35.5 (the "harmful day" line);
#     flag = more than half of the normal weeks are polluted. Also reported: weeks averaging >= 15 (WHO 2021 24-hour
#     guideline) and, as a sensitivity only, the normal and ratio without the polluted weeks.
#   Dropped cities (Dish, 2026-10-03) stay in pm_normals.csv with the reason, but are left out of the pairs:
#     Yakima: event week has fewer than 100 kept Reddit posts + comments (check 2, Reddit activity).
# Pairs (every pair of the 10 cities, A = the city with the higher event-week PM2.5):
#   crossed = A had worse air but a smaller ratio.
#   matched = event-week PM2.5 within 5% of each other (relative to the higher one) and different ratios
#             (Claude's choice for the "pair tolerance" open decision, flagged).
#   No headline pairs (Dish, 2026-10-03; replaces Bakersfield-Indianapolis / Bakersfield-Seattle). All pairs are reported.
#   featured_by_rule (only for presentation examples): the matched pair with the biggest ratio gap and the crossed pair
#   with the biggest air gap.
# Output: data/processed/openaq/step08_pm_normals/pm_normals.csv, pairs.csv
# Run from the repo root: python3 scripts/openaq/08_pm_normals_and_pairs.py   (local files only)
import csv, itertools, os, statistics

IN = "data/processed/openaq/step07_screening"
OUT = "data/processed/openaq/step08_pm_normals"
CITIES = ["bakersfield", "fairbanks", "fresno", "yakima", "detroit", "seattle", "indianapolis", "eugene", "pittsburgh", "sanjose"]
YEARS, MIN_DAYS, MATCH_TOL = range(2019, 2026), 5, 0.05
DROPPED = {"yakima": "check 2: event week under 100 Reddit posts + comments"}
os.makedirs(OUT, exist_ok=True)

S = {r["city"]: r for r in csv.DictReader(open(f"{IN}/city_screening.csv", encoding="utf-8")) if r["source"] == "reference"}
W = [r for r in csv.DictReader(open(f"{IN}/weekly_all.csv", encoding="utf-8")) if r["source"] == "reference"]

norms = []
for c in CITIES:
    s = S[c]; ev, month = s["worst_week_start"], s["worst_week_month"]
    m = int(month[5:])
    base = [r for r in W if r["city"] == c and r["week_start"] != ev and int(r["month"][5:]) == m
            and int(r["month"][:4]) in YEARS and int(r["n_days"]) >= MIN_DAYS]
    vals = [float(r["week_avg"]) for r in base]
    a, n = float(s["worst_week_avg"]), statistics.median(vals)
    polluted = [float(r["max_day"]) >= 35.5 for r in base]
    clean = [v for v, bad in zip(vals, polluted) if not bad]
    n_clean = statistics.median(clean) if clean else None
    norms.append(dict(city=c, city_name=s["city_name"], event_week_start=ev, event_week_end=s["worst_week_end"], event_month=m,
                      event_week_pm25=a, pm25_normal=round(n, 3), normal_weeks=len(vals),
                      normal_weeks_above_35_5=sum(v > 35.5 for v in vals), ratio_to_normal=round(a / n, 2),
                      median_days_ge_35_5_2019_2025=s["median_days_ge_35_5_2019_2025"],
                      normal_weeks_with_day_ge_35_5=sum(polluted), normal_weeks_avg_ge_15=sum(v >= 15 for v in vals),
                      shifting_normal_flag=int(sum(polluted) > len(vals) / 2),
                      sens_normal_without_polluted_weeks=round(n_clean, 3) if n_clean else "",
                      sens_ratio_without_polluted_weeks=round(a / n_clean, 2) if n_clean else "",
                      dropped=DROPPED.get(c, "")))
by = {r["city"]: r for r in norms}

pairs = []
for x, y in itertools.combinations([c for c in CITIES if c not in DROPPED], 2):
    A, B = sorted((by[x], by[y]), key=lambda r: -r["event_week_pm25"])
    gap = (A["event_week_pm25"] - B["event_week_pm25"]) / A["event_week_pm25"]
    crossed = A["ratio_to_normal"] < B["ratio_to_normal"]
    matched = gap <= MATCH_TOL and A["ratio_to_normal"] != B["ratio_to_normal"]
    if not (crossed or matched):
        continue
    pairs.append(dict(type="matched" if matched else "crossed", featured_by_rule=0,
                      worse_air_city=A["city"], other_city=B["city"],
                      pm25_worse=A["event_week_pm25"], pm25_other=B["event_week_pm25"], pm25_gap_pct=round(100 * gap, 1),
                      ratio_worse=A["ratio_to_normal"], ratio_other=B["ratio_to_normal"],
                      ratio_gap=round(max(A["ratio_to_normal"], B["ratio_to_normal"]) / min(A["ratio_to_normal"], B["ratio_to_normal"]), 2),
                      median_days_worse=A["median_days_ge_35_5_2019_2025"], median_days_other=B["median_days_ge_35_5_2019_2025"],
                      pos_predicts=f"{(B if B['ratio_to_normal'] > A['ratio_to_normal'] else A)['city']} reacts more",
                      neg_predicts=f"{A['city']} reacts more" if gap > MATCH_TOL else "about the same"))
for t, k in (("matched", "ratio_gap"), ("crossed", "pm25_gap_pct")):
    max((p for p in pairs if p["type"] == t), key=lambda p: p[k])["featured_by_rule"] = 1
pairs.sort(key=lambda p: (p["type"] != "matched", -(p["ratio_gap"] if p["type"] == "matched" else p["pm25_gap_pct"])))

for fn, rows in (("pm_normals.csv", sorted(norms, key=lambda r: -r["ratio_to_normal"])), ("pairs.csv", pairs)):
    with open(f"{OUT}/{fn}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

for r in sorted(norms, key=lambda r: -r["ratio_to_normal"]):
    print(f"{r['city']:13s} event {r['event_week_pm25']:7.2f}  normal {r['pm25_normal']:6.2f} ({r['normal_weeks']} wks)  ratio {r['ratio_to_normal']:5.1f}x"
          f"  | polluted wks {r['normal_weeks_with_day_ge_35_5']}/{r['normal_weeks']}, avg>=15 {r['normal_weeks_avg_ge_15']}"
          f"{'  FLAG' if r['shifting_normal_flag'] else ''}  | without polluted: normal {r['sens_normal_without_polluted_weeks']} ratio {r['sens_ratio_without_polluted_weeks']}x")
for p in pairs:
    print(f"{'*' if p['featured_by_rule'] else ' '} {p['type']:8s} {p['worse_air_city']} ({p['pm25_worse']}, {p['ratio_worse']}x) vs "
          f"{p['other_city']} ({p['pm25_other']}, {p['ratio_other']}x)")
print("DONE")
