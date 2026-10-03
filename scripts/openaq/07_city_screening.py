# Step 7 · OpenAQ · screen the 13 PM2.5-experiment candidate cities and report the numbers for the chronic/acute cutoffs
# (docs/experiment-design-pm25.md, "How do we pick the cities?" checks 1 and 3, and "How do we group the cities?").
# No baselines, ratios or Reddit here. Nothing is chosen: no cutoffs, no data source. It only reports.
#
# Input (read only): data/processed/openaq/step05_averages/pm25_<city>_daily.csv, so Step 5's rules carry over:
#   sensor-day valid with >= 18 of 24 hours (OA-D3), negatives set to 0 (OA-D5), flagged low-cost days out (OA-D7),
#   low-cost outlier rule (OA-D6), site = same-type sensors within 50 m (Step 3), local calendar days (OpenAQ /days).
#   City daily value per source = Step 5's ref_mean / lowcost_mean = mean of that source's reporting sites (>= 1 site).
#   "Monitor" = site (approved by Dish, 2026-10-02).
# Reference and low-cost are kept completely separate (never mixed).
#
# Per city x source:
#   Check 1 coverage: % of days 2019-01-01 -> END with a city daily value. Pass = >= 75%.
#     END = last date with any PM2.5 value in any candidate city's file (the same END for every city and source).
#   Grouping measure: for each year 2019-2025, days with daily PM2.5 >= 35.5 ug/m3 (unrounded; approved by Dish),
#     that year's coverage, and the median of the 7 yearly counts. Years below 75% coverage are flagged, not dropped.
#   Check 3 real harm: Monday-Sunday weeks overlapping 2019-01-01 -> END; week average = mean of the available daily
#     values; valid week = >= 5 of 7 days with data. Days outside 2019-01-01 -> END count as missing.
#     Fireworks rule (Dish, 2026-10-02): a week whose calendar dates include Jul 4, Jul 5, Dec 31 or Jan 1 can't be the
#     event week. Worst valid non-fireworks week reported; every invalid non-fireworks week and every fireworks week
#     whose average beats it is listed (not dropped silently). Month = the month holding most of the week's days
#     (= the month of the week's Thursday). Pass = worst valid non-fireworks week average > 35.5.
#   Low-cost only: relative humidity is not in the OpenAQ pull and there are no PurpleAir sensors, so no EPA/Barkjohn
#     correction is applied (values are uncorrected). Agreement with reference on days both have a value
#     (2019-01-01 -> END): n days, Pearson r, median of (low-cost - reference).
#
# Output: data/processed/openaq/step07_screening/
#   city_screening.csv    one row per city x source
#   grouping_by_year.csv  one row per city x source x year (2019-2025)
#   weekly_all.csv        every Monday-Sunday week per city x source (average, days with data, valid), for auditing
#   screening_summary.md  plain-language summary, pass/fail tables, sorted median-days list, Claude's choices
# Run from the repo root: python3 scripts/openaq/07_city_screening.py   (local files only; no API calls)
import csv, datetime, os, statistics

IN = "data/processed/openaq/step05_averages"
OUT = "data/processed/openaq/step07_screening"
START = datetime.date(2019, 1, 1)
GROUP_YEARS = list(range(2019, 2026))
HARM, MIN_COVERAGE, MIN_WEEK_DAYS = 35.5, 75.0, 5
FIREWORKS = {(7, 4), (7, 5), (12, 31), (1, 1)}
# slug, name, ALA State of the Air 2026 rank (candidate list only; not used in any calculation)
CITIES = [("fairbanks", "Fairbanks AK", 1), ("eugene", "Eugene OR", 2), ("bakersfield", "Bakersfield CA", 3),
          ("fresno", "Fresno CA", 6), ("losangeles", "Los Angeles CA", 7), ("seattle", "Seattle WA", 8),
          ("detroit", "Detroit MI", 11), ("pittsburgh", "Pittsburgh PA", 13), ("indianapolis", "Indianapolis IN", 15),
          ("phoenix", "Phoenix AZ", 18), ("sanjose", "San Jose CA", 21), ("saltlakecity", "Salt Lake City UT", 22),
          ("yakima", "Yakima WA", 25)]
SOURCES = [("reference", "ref"), ("low-cost", "lowcost")]
os.makedirs(OUT, exist_ok=True)
D = datetime.date.fromisoformat
r1 = lambda x, n=2: "" if x is None else round(x, n)

# Read Step 5 city-daily files
raw = {}
for slug, _, _ in CITIES:
    raw[slug] = list(csv.DictReader(open(f"{IN}/pm25_{slug}_daily.csv", encoding="utf-8")))
END = max(D(r["date"]) for rows in raw.values() for r in rows if r["ref_mean"] or r["lowcost_mean"])
WINDOW = [START + datetime.timedelta(i) for i in range((END - START).days + 1)]
print(f"Window: {START} -> {END} ({len(WINDOW)} days)", flush=True)

def daily_series(slug, key):
    vals, nsites, sites = {}, {}, set()
    for r in raw[slug]:
        d = D(r["date"])
        if START <= d <= END and r[f"{key}_mean"] != "":
            vals[d] = float(r[f"{key}_mean"]); nsites[d] = int(r[f"{key}_n_sites"])
            sites.update(s for s in r[f"{key}_site_ids"].split("; ") if s)
    return vals, nsites, sites

def weeks(vals):
    out, mon = [], START - datetime.timedelta(START.weekday())
    while mon <= END:
        days = [mon + datetime.timedelta(i) for i in range(7)]
        v = [vals[d] for d in days if d in vals]
        thu = days[3]
        fw = [d.isoformat() for d in days if (d.month, d.day) in FIREWORKS]
        out.append(dict(week_start=mon, week_end=days[-1], n_days=len(v), avg=statistics.mean(v) if v else None,
                        max_day=max(v) if v else None, valid=len(v) >= MIN_WEEK_DAYS,
                        month=f"{thu.year}-{thu.month:02d}", fireworks="; ".join(fw)))
        mon += datetime.timedelta(7)
    return out

screen, by_year, week_rows = [], [], []
series = {}
for slug, name, rank in CITIES:
    for src, key in SOURCES:
        vals, nsites, sites = daily_series(slug, key)
        series[(slug, src)] = vals
        cov = 100 * len(vals) / len(WINDOW)
        one_site = sum(1 for n in nsites.values() if n == 1)
        # Grouping measure by year
        counts, low_years = [], []
        for y in GROUP_YEARS:
            ydays = [d for d in WINDOW if d.year == y]
            yv = [vals[d] for d in ydays if d in vals]
            ycov = 100 * len(yv) / len(ydays)
            n_harm = sum(v >= HARM for v in yv)
            counts.append(n_harm)
            if ycov < MIN_COVERAGE: low_years.append(str(y))
            by_year.append(dict(city=slug, city_name=name, source=src, year=y, days_in_year=len(ydays),
                                days_with_data=len(yv), coverage_pct=round(ycov, 2), coverage_below_75=int(ycov < MIN_COVERAGE),
                                days_ge_35_5=n_harm))
        # Weeks
        W = weeks(vals)
        for w in W:
            week_rows.append(dict(city=slug, source=src, week_start=w["week_start"], week_end=w["week_end"], month=w["month"],
                                  n_days=w["n_days"], valid=int(w["valid"]), week_avg=r1(w["avg"]), max_day=r1(w["max_day"]),
                                  fireworks_dates=w["fireworks"]))
        valid = [w for w in W if w["valid"]]
        eligible = [w for w in valid if not w["fireworks"]]
        worst = max(eligible, key=lambda w: w["avg"]) if eligible else None
        beats = lambda w: w["avg"] is not None and (worst is None or w["avg"] > worst["avg"])
        higher = sorted((w for w in W if not w["valid"] and not w["fireworks"] and beats(w)), key=lambda w: -w["avg"])
        fw_higher = sorted((w for w in W if w["fireworks"] and beats(w)), key=lambda w: -w["avg"])
        # Low-cost agreement with reference
        agree = {}
        if src == "low-cost":
            ref = series[(slug, "reference")]
            both = sorted(d for d in vals if d in ref)
            x, y = [ref[d] for d in both], [vals[d] for d in both]
            r = statistics.correlation(x, y) if len(both) >= 3 and len(set(x)) > 1 and len(set(y)) > 1 else None
            agree = dict(agree_n_days=len(both), agree_pearson_r=r1(r, 3),
                         agree_median_diff_lowcost_minus_ref=r1(statistics.median(b - a for a, b in zip(x, y))) if both else "",
                         agree_first_day=both[0] if both else "", agree_last_day=both[-1] if both else "")
        screen.append(dict(
            city=slug, city_name=name, ala_rank=rank, source=src,
            n_sites=len(sites), site_ids="; ".join(sorted(sites)),
            window_start=START, window_end=END, days_in_window=len(WINDOW), days_with_data=len(vals),
            coverage_pct=round(cov, 2), check1_pass=int(cov >= MIN_COVERAGE),
            first_day=min(vals) if vals else "", last_day=max(vals) if vals else "",
            days_one_site=one_site, days_one_site_pct=round(100 * one_site / len(vals), 2) if vals else "",
            **{f"days_ge_35_5_{y}": c for y, c in zip(GROUP_YEARS, counts)},
            median_days_ge_35_5_2019_2025=statistics.median(counts), years_below_75pct="; ".join(low_years),
            n_weeks=len(W), n_valid_weeks=len(valid), n_invalid_weeks=len(W) - len(valid),
            worst_week_start=worst["week_start"] if worst else "", worst_week_end=worst["week_end"] if worst else "",
            worst_week_month=worst["month"] if worst else "", worst_week_avg=r1(worst["avg"]) if worst else "",
            worst_week_n_days=worst["n_days"] if worst else "", worst_week_max_day=r1(worst["max_day"]) if worst else "",
            n_fireworks_weeks_higher=len(fw_higher),
            fireworks_weeks_higher="; ".join(f"{w['week_start']} avg {w['avg']:.2f} ({w['n_days']}/7 days; {w['fireworks']})" for w in fw_higher),
            check3_pass=int(worst is not None and worst["avg"] > HARM),
            n_invalid_weeks_higher=len(higher),
            invalid_weeks_higher="; ".join(f"{w['week_start']} avg {w['avg']:.2f} ({w['n_days']}/7 days)" for w in higher),
            rh_available="no" if src == "low-cost" else "",
            correction="none (no RH in OpenAQ pull; no PurpleAir sensors)" if src == "low-cost" else "",
            **(agree or dict(agree_n_days="", agree_pearson_r="", agree_median_diff_lowcost_minus_ref="",
                             agree_first_day="", agree_last_day=""))))

def write(fn, rows):
    with open(f"{OUT}/{fn}", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
write("city_screening.csv", screen)
write("grouping_by_year.csv", by_year)
write("weekly_all.csv", week_rows)

# ---- Summary (markdown) ----
S = {(s["city"], s["source"]): s for s in screen}
pf = lambda b: "PASS" if b else "fail"
L = [f"# PM2.5 experiment · Step 1 screening (OpenAQ Step 7)", "",
     f"Generated by `scripts/openaq/07_city_screening.py` on {datetime.date.today()}. "
     f"Input: `{IN}/pm25_<city>_daily.csv`. Window: {START} → {END} ({len(WINDOW)} days). "
     "Reference and low-cost are reported separately and never mixed. Nothing is chosen here: no cutoffs, no data source.", ""]
ref = [S[(c, "reference")] for c, _, _ in CITIES]
p1 = [s["city_name"] for s in ref if s["check1_pass"]]; p3 = [s["city_name"] for s in ref if s["check3_pass"]]
both = [s["city_name"] for s in ref if s["check1_pass"] and s["check3_pass"]]
L += ["## In plain language", "",
      f"- **Reference monitors:** {len(p1)} of 13 cities have PM2.5 on at least 75% of days (check 1). "
      f"{len(p3)} of 13 had a worst week averaging above 35.5 µg/m³ (check 3). **{len(both)} pass both.**",
      f"- Fail check 1 (reference): {', '.join(s['city_name'] + f' ({s['coverage_pct']}%)' for s in ref if not s['check1_pass']) or 'none'}.",
      f"- Fail check 3 (reference): {', '.join(s['city_name'] + f' ({s['worst_week_avg']})' for s in ref if not s['check3_pass']) or 'none'}.",
      "- **Low-cost sensors are uncorrected.** OpenAQ's pull has no relative humidity, and none of these sensors are PurpleAir "
      "(they are Clarity, AirGradient and CMU), so the EPA/Barkjohn correction can't be applied. Under the design doc, "
      "low-cost can't serve as a fallback until this is resolved. Low-cost numbers below are for information only.",
      "- Check 2 (Reddit activity) is not part of this step.", ""]
L += ["## Checks 1 and 3 · reference monitors", "",
      "| City | ALA | Sites | Coverage | Check 1 | Days with 1 site | Worst valid week | Month | Avg (µg/m³) | Days | Check 3 | Fireworks weeks higher (skipped) | Invalid weeks higher |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for s in ref:
    L.append(f"| {s['city_name']} | {s['ala_rank']} | {s['n_sites']} | {s['coverage_pct']}% | {pf(s['check1_pass'])} | "
             f"{s['days_one_site']} ({s['days_one_site_pct']}%) | {s['worst_week_start']} → {s['worst_week_end']} | {s['worst_week_month']} | "
             f"{s['worst_week_avg']} | {s['worst_week_n_days']}/7 | {pf(s['check3_pass'])} | {s['n_fireworks_weeks_higher']} | {s['n_invalid_weeks_higher']} |")
lc = [S[(c, "low-cost")] for c, _, _ in CITIES]
L += ["", "## Checks 1 and 3 · low-cost sensors (uncorrected)", "",
      "| City | Sites | Coverage | Check 1 | First day | Worst valid week | Avg (µg/m³) | Check 3 | Overlap days with ref | r | Median diff (low-cost − ref) |",
      "|---|---|---|---|---|---|---|---|---|---|---|"]
for s in lc:
    L.append(f"| {s['city_name']} | {s['n_sites']} | {s['coverage_pct']}% | {pf(s['check1_pass'])} | {s['first_day'] or '–'} | "
             f"{(str(s['worst_week_start']) + ' → ' + str(s['worst_week_end'])) if s['worst_week_start'] else '–'} | {s['worst_week_avg'] or '–'} | "
             f"{pf(s['check3_pass'])} | {s['agree_n_days']} | {s['agree_pearson_r'] if s['agree_pearson_r'] != '' else '–'} | "
             f"{s['agree_median_diff_lowcost_minus_ref'] if s['agree_median_diff_lowcost_minus_ref'] != '' else '–'} |")
for src, label in SOURCES:
    rows = sorted((S[(c, src)] for c, _, _ in CITIES), key=lambda s: -s["median_days_ge_35_5_2019_2025"])
    L += ["", f"## Grouping measure · {src}: median days per year with daily PM2.5 ≥ 35.5, 2019–2025 (sorted)", "",
          "`*` = that year's coverage is below 75%.", "",
          "| City | Median | " + " | ".join(map(str, GROUP_YEARS)) + " |", "|---|---|" + "---|" * len(GROUP_YEARS)]
    for s in rows:
        yr = {b["year"]: b for b in by_year if b["city"] == s["city"] and b["source"] == src}
        L.append(f"| {s['city_name']} | **{s['median_days_ge_35_5_2019_2025']}** | " +
                 " | ".join(f"{yr[y]['days_ge_35_5']}{'*' if yr[y]['coverage_below_75'] else ''}" for y in GROUP_YEARS) + " |")
L += ["", "## Invalid weeks (fewer than 5 of 7 days) whose average beats the worst valid week", ""]
any_h = False
for s in screen:
    if s["n_invalid_weeks_higher"]:
        any_h = True
        L.append(f"- **{s['city_name']} · {s['source']}** (worst valid week {s['worst_week_avg'] or 'none'}): {s['invalid_weeks_higher']}")
if not any_h: L.append("- None.")
L += ["", "## Fireworks weeks (Jul 4–5, Dec 31–Jan 1) skipped as event weeks, whose average beats the worst eligible week", ""]
any_f = False
for s in screen:
    if s["n_fireworks_weeks_higher"]:
        any_f = True
        L.append(f"- **{s['city_name']} · {s['source']}** (worst eligible week {s['worst_week_avg'] or 'none'}): {s['fireworks_weeks_higher']}")
if not any_f: L.append("- None.")
L += ["", "Every week, valid or not, fireworks or not, is in `weekly_all.csv`.", "",
      "## Defaults and choices", "",
      "**Team decisions carried over from Step 5 (Gina):** sensor-day valid with ≥ 18 of 24 hours (OA-D3); negatives set to 0 (OA-D5); "
      "flagged low-cost days removed (OA-D7); low-cost outlier rule (OA-D6); site = same-type sensors within 50 m (Step 3); "
      "city daily value = mean of the reporting sites, at least 1 (OA-D3).", "",
      "**Claude's choices, approved by Dish (2026-10-02):**",
      "- Start from Step 5 (`pm25_<city>_daily.csv`) rather than raw.",
      "- A \"monitor\" is a site (sensors within 50 m already averaged).",
      "- A harmful day is daily PM2.5 ≥ 35.5 µg/m³, on the unrounded value (Step 6 truncates to 1 decimal first; not done here).",
      "- Low-cost reported uncorrected (no RH available).",
      f"- One end date for every city and source: {END}, the last day with any PM2.5 value in any candidate's file.",
      "- Weeks are every Monday–Sunday week overlapping the window; days before 2019-01-01 or after the end date count as missing "
      "(so the first and last weeks can't use data from outside the window).",
      "- Years below 75% coverage are flagged but still count toward the median. Missing days count as not harmful. "
      "No second median without low-coverage years: those are the big smoke years (2020–21), so dropping them would "
      "understate chronic cities (Bakersfield 12 → 6). Their counts are likely undercounts (limitation).",
      "- Fireworks weeks are identified by the week's calendar dates, whether or not those days have data.", "",
      "**Rule set by Dish (2026-10-02):** a week containing Jul 4–5 or Dec 31–Jan 1 can't be the event week (fireworks smoke "
      "is short and man-made, and Reddit talk that week is about fireworks). Applied to every city; such weeks are listed above.",
      "- Agreement uses Pearson r on daily values, over overlapping days in the window only. It inherits OA-D6, which compares "
      "low-cost readings above 100 µg/m³ with reference, so low-cost isn't fully independent of reference before this check.",
      "- Check 3 pass is strictly > 35.5 (as in the design doc); the day count is ≥ 35.5 (approved above).", ""]
open(f"{OUT}/screening_summary.md", "w", encoding="utf-8").write("\n".join(L))

for s in screen:
    print(f"{s['city']:13s} {s['source']:9s} sites {s['n_sites']:3d} cov {s['coverage_pct']:6.2f}% c1 {pf(s['check1_pass'])} | "
          f"median >=35.5 {s['median_days_ge_35_5_2019_2025']:5} | worst {s['worst_week_start']} {s['worst_week_avg']} c3 {pf(s['check3_pass'])}"
          f"{' | fireworks weeks skipped ' + str(s['n_fireworks_weeks_higher']) if s['n_fireworks_weeks_higher'] else ''}{' | higher invalid ' + str(s['n_invalid_weeks_higher']) if s['n_invalid_weeks_higher'] else ''}", flush=True)
print("DONE")
