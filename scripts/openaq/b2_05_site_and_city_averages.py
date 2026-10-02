# BATCH 2 (17 cities added 2026-10-02, Gina): a copy of the original step with only the city list, inputs/outputs and
# summary file names changed, so the original 16 cities' files are not touched. Same dates, rules and decisions (OA-D1 to OA-D7).
# Step 5 · OpenAQ · daily site averages and city averages (reference, low-cost, overall), with a full audit trail.
#
# Per sensor-day, in this order (Decisions OA-D3, OA-D5, OA-D6, OA-D7):
#   1. Valid day: at least 18 of 24 hours observed (OA-D3). Otherwise excluded.
#   2. Negative daily values set to 0 µg/m³ (OA-D5); the original value is kept in the audit.
#   3. Low-cost sensor-days flagged by OpenAQ (an hour above 1,000 µg/m³ still in the daily value) are excluded (OA-D7).
#      Flagged reference sensor-days are kept (the flagged negative hour is already left out by OpenAQ).
#   4. Low-cost outlier rule (OA-D6), using only sensor-days still included after 1-3:
#        reference average = mean of the city's included reference sensor-days that day
#        other low-cost median = median of the city's other included low-cost sensor-days that day
#        excluded if > 1,000; or if > 100 and:
#          reference + >= 3 other low-cost:  > 5x reference average AND > 5x other low-cost median   (rule "ref+peer")
#          reference, < 3 other low-cost:    > 5x reference average                                  (rule "ref")
#          no reference, >= 3 other low-cost: > 5x other low-cost median                             (rule "peer")
#          neither: only the 1,000 ceiling                                                           (rule "ceiling")
# Then (OA-D3):
#   5. Site-day = mean of the site's included sensor-days (a site = same type, same city, within 50 m; Step 3).
#   6. City-day, per type: mean, min and max across that type's site-days; number of sites; site and sensor IDs.
#      Overall: mean = mean of the reference mean and the low-cost mean (each type 50%); on days with only one type,
#      overall = that type. Min / max / sites = across all site-days of both types.
# Every date of the study period gets a row per city, including days with no data.
# The summary file is coverage only (days with data, first/last day, sites used), no whole-period averages (Gina, 2026-09-27).
# Run from the repo root: python3 scripts/openaq/05_site_and_city_averages.py   (local files only; no API calls)
import csv, datetime, glob, os, statistics
from collections import defaultdict

START, END = datetime.date(2016, 3, 6), datetime.date(2026, 9, 25)
MIN_HOURS, CEILING, FLOOR_TEST, RATIO, MIN_PEERS = 18, 1000.0, 100.0, 5.0, 3
IN = "data/processed/openaq/step04_daily"
OUT = "data/processed/openaq/step05_averages"
os.makedirs(f"{OUT}/audit", exist_ok=True)
CITIES = ['visalia', 'seattle', 'bismarck', 'mcallen', 'minot', 'pittsburgh', 'elcentro', 'indianapolis', 'medford', 'boise', 'lancaster', 'bend', 'sanjose', 'saltlakecity', 'helena', 'logan', 'yakima']
DATES = [(START + datetime.timedelta(d)).isoformat() for d in range((END - START).days + 1)]
fmt = lambda x: "" if x is None else round(x, 4)

summary = []
for city in CITIES:
    fn = f"{IN}/openaq_pm25_{city}_daily_sensors.csv"
    rows = list(csv.DictReader(open(fn))) if os.path.exists(fn) else []
    # 1-3
    for r in rows:
        raw = r["pm25_mean_ugm3"]
        r["value_raw"] = None if raw in ("", "None") else float(raw)
        r["pm25_used"] = None if r["value_raw"] is None else max(r["value_raw"], 0.0)
        r["negative_set_to_zero"] = int(r["value_raw"] is not None and r["value_raw"] < 0)
        r["included"], r["exclusion_reason"], r["rule"], r["ref_avg"], r["peer_median"], r["n_peers"] = 1, "", "", None, None, None
        if r["valid_day"] != "1":
            r["included"], r["exclusion_reason"] = 0, f"fewer than {MIN_HOURS} hours observed"
        elif r["pm25_used"] is None:
            r["included"], r["exclusion_reason"] = 0, "no value"
        elif r["sensor_class"] == "low-cost" and r["has_flags"] == "True":
            r["included"], r["exclusion_reason"] = 0, "low-cost day flagged by OpenAQ (hour above 1,000 µg/m³ in daily value)"
    # 4
    by_day = defaultdict(list)
    for r in rows:
        if r["included"]: by_day[r["date_local"]].append(r)
    for d, L in by_day.items():
        refs = [r["pm25_used"] for r in L if r["sensor_class"] == "reference"]
        ref_avg = statistics.mean(refs) if refs else None
        lows = [r for r in L if r["sensor_class"] == "low-cost"]
        for r in lows:
            peers = [x["pm25_used"] for x in lows if x is not r]
            pm = statistics.median(peers) if len(peers) >= MIN_PEERS else None
            v = r["pm25_used"]
            r["ref_avg"], r["peer_median"], r["n_peers"] = ref_avg, pm, len(peers)
            r["rule"] = "ref+peer" if ref_avg is not None and pm is not None else "ref" if ref_avg is not None else "peer" if pm is not None else "ceiling"
            out = v > CEILING
            if not out and v > FLOOR_TEST:
                if r["rule"] == "ref+peer": out = v > RATIO * ref_avg and v > RATIO * pm
                elif r["rule"] == "ref": out = v > RATIO * ref_avg
                elif r["rule"] == "peer": out = v > RATIO * pm
            if out:
                r["included"], r["exclusion_reason"] = 0, ("above 1,000 µg/m³" if v > CEILING else f"low-cost outlier, rule {r['rule']}")
    # 5 site-days
    site_day = defaultdict(list)
    for r in rows:
        if r["included"]: site_day[(r["site_id"], r["date_local"])].append(r)
    site_rows = []
    by_date = defaultdict(list)
    for (sid, d), L in sorted(site_day.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        m = statistics.mean(r["pm25_used"] for r in L)
        rec = dict(city_slug=city, date_local=d, site_id=sid, sensor_class=L[0]["sensor_class"], site_mean_ugm3=round(m, 4),
                   n_sensors=len(L), sensor_ids="; ".join(sorted((r["sensor_id"] for r in L), key=int)))
        site_rows.append(rec); by_date[d].append(rec)
    # 6 city-days
    city_rows = []
    for d in DATES:
        S = by_date.get(d, [])
        row = {"date": d}
        means = {}
        for cls, key in (("reference", "ref"), ("low-cost", "lowcost")):
            T = [s for s in S if s["sensor_class"] == cls]
            vals = [s["site_mean_ugm3"] for s in T]
            means[key] = statistics.mean(vals) if vals else None
            row.update({f"{key}_mean": fmt(means[key]), f"{key}_min": fmt(min(vals)) if vals else "", f"{key}_max": fmt(max(vals)) if vals else "",
                        f"{key}_n_sites": len(T), f"{key}_site_ids": "; ".join(s["site_id"] for s in T),
                        f"{key}_sensor_ids": "; ".join(s["sensor_ids"] for s in T)})
        present = [m for m in means.values() if m is not None]
        vals = [s["site_mean_ugm3"] for s in S]
        row.update({"all_mean": fmt(statistics.mean(present)) if present else "",
                    "all_mean_basis": "mean of reference and low-cost means" if len(present) == 2 else ("reference only" if means["ref"] is not None else "low-cost only") if present else "",
                    "all_min": fmt(min(vals)) if vals else "", "all_max": fmt(max(vals)) if vals else "", "all_n_sites": len(S)})
        city_rows.append(row)
    # write
    with open(f"{OUT}/pm25_{city}_daily.csv", "w", newline="", encoding="utf-8") as f:
        cols = ["date"] + [f"{k}_{c}" for k in ("ref", "lowcost") for c in ("mean", "min", "max", "n_sites", "site_ids", "sensor_ids")] + ["all_mean", "all_mean_basis", "all_min", "all_max", "all_n_sites"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(city_rows)
    with open(f"{OUT}/audit/site_daily_{city}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["city_slug", "date_local", "site_id", "sensor_class", "site_mean_ugm3", "n_sensors", "sensor_ids"]); w.writeheader(); w.writerows(site_rows)
    acols = ["city_slug", "date_local", "site_id", "sensor_id", "sensor_class", "value_raw", "pm25_used", "negative_set_to_zero", "hours_observed",
             "has_flags", "included", "exclusion_reason", "rule", "ref_avg", "peer_median", "n_peers"]
    with open(f"{OUT}/audit/sensor_day_audit_{city}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=acols, extrasaction="ignore"); w.writeheader()
        for r in sorted(rows, key=lambda r: (r["date_local"], r["site_id"], int(r["sensor_id"]))):
            w.writerow({**r, "ref_avg": fmt(r["ref_avg"]), "peer_median": fmt(r["peer_median"]), "n_peers": "" if r["n_peers"] is None else r["n_peers"]})
    # summary per city and type
    reasons = defaultdict(int)
    for r in rows: reasons[r["exclusion_reason"] or "included"] += 1
    for key, label in (("ref", "reference"), ("lowcost", "low-cost"), ("all", "overall")):
        v = [float(r[f"{key}_mean"]) for r in city_rows if r[f"{key}_mean"] != ""]
        days = [r["date"] for r in city_rows if r[f"{key}_mean"] != ""]
        summary.append(dict(city_slug=city, average=label, days_with_data=len(v), share_of_study_days=round(len(v) / len(DATES), 4),
            first_day=days[0] if days else "", last_day=days[-1] if days else "",
            sites_used=len({s for r in city_rows for s in (r.get(f"{key}_site_ids", "") or "").split("; ") if s}) if key != "all" else len({s["site_id"] for s in site_rows})))
    print(f"{city}: sensor-days {len(rows)} | " + ", ".join(f"{k}: {n}" for k, n in sorted(reasons.items(), key=lambda kv: -kv[1])), flush=True)

with open(f"{OUT}/pm25_city_coverage_summary_b2.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0])); w.writeheader(); w.writerows(summary)
print("DONE")
