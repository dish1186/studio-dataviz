# METAR visibility: status and data guide (FINAL, closed 2026-09-27)

Copied from Dish's project notes (`claude/metar-pipeline-status.md`) so the whole team has it in the repo. Full record: `logs/data-log-dish.md` (Decisions D1–D8), one script per step in `scripts/metar/`, citations in `docs/references.md`. **Closing commit: `12802a3`.**

## Status: CLOSED (D8). Final files frozen.
`data/processed/metar/final/vis_<city>_daily.csv` for 17 cities, 3,920 days each (2016-01-01 → 2026-09-24). The SHA-256 of each file is in the D8 log entry. No further reruns are planned. Read the files; don't modify or regenerate them.

| City | Airport(s) | Mi to city hall | Local time | Valid days | Notes |
|---|---|---|---|---|---|
| Bakersfield CA | BFL | 4.5 | Pacific | 3,872 | |
| Fresno CA | FAT | 4.7 | Pacific | 3,846 | |
| Delano CA | DLO | 1.7 | Pacific | 3,079 | starts 2017-01-15; ends 09-23 |
| Los Angeles CA | LAX | 11.5 | Pacific | 3,851 | |
| San Diego CA | SAN | 1.7 | Pacific | 3,896 | ends 09-23 |
| San Francisco CA | SFO | 11.3 | Pacific | 3,849 | |
| Eugene OR | EUG | 7.9 | Pacific | 3,661 | |
| Springfield OR | EUG (shared) | 10.9 | Pacific | 3,661 | identical to Eugene |
| Fairbanks AK | PAFA | 5.2 | Alaska | 3,438 | |
| Phoenix AZ | PHX | 3.9 | MST, no DST | 3,915 | nearly flat row |
| Brownsville TX | BRO | 4.6 | Central | 3,823 | |
| Raymondville TX | HRL (Harlingen) | 19.2 | Central | 3,810 | |
| Detroit MI | DET + DTW | 5.8 / 16.1 | Eastern | 3,757 | two-airport mean |
| Warren MI | VLL (Troy) | 8.0 | Eastern | 3,610 | ends 09-23 |
| Ann Arbor MI | ARB | 4.0 | Eastern | 3,523 | outage from ~2026-06-17; last valid day 2026-08-05 |
| Pittsburgh PA | AGC + PIT | 7.0 / 12.9 | Eastern | 3,744 | two-airport mean |
| Boston MA | BOS | 2.5 | Eastern | 3,579 | |

Pipeline rules: drop blank and 0-mi readings · one report per airport per clock hour (haziest kept; DLO/VLL one routine report at :54–:56, D6) · daytime 8:00–17:59 local · remove wet hours (fog, mist, rain, drizzle, snow/frozen precip, vicinity fog, or hour max RH ≥ 90%) · Koschmieder extinction = 3.912 ÷ km · two-airport cities use an equal-weight mean · a day is valid with ≥ 3 dry daytime hours.

## Columns in `vis_<city>_daily.csv`
| Column | Meaning | Values |
|---|---|---|
| `date` | Local calendar day | 2016-01-01 … 2026-09-24 (every day present) |
| `visibility_mi` | Daily daytime visibility in miles, from the mean extinction. Lower = hazier; 10 = sensor cap ("10+") | 0.25–10; blank if `valid_day = 0` |
| `extinction` | Daily mean light extinction, km⁻¹. Higher = hazier; 0.243 = 10 mi | 0.243–9.72; blank if `valid_day = 0` |
| `n_hours` | Dry daytime hours used | 0–10 |
| `n_stations` | Airports contributing that day | 0–2 (2 only Detroit, Pittsburgh) |
| `valid_day` | 1 = usable (≥ 3 dry hours), 0 = no value | 0/1 |
| `point_sample` | 1 = single airport, 0 = two-airport mean | 0/1 |
| `rh_missing_hours` | Hours kept with blank humidity (less certain) | 0–10 |

**Using it:** use only `valid_day = 1` and show the other days as gaps. To aggregate, average `extinction`, then convert back: miles = (3.912 ÷ extinction) ÷ 1.609344. Never average `visibility_mi` directly. **Haze index (chosen for the viz):** `extinction ÷ 0.24308`, where 1× is a clear 10-mile day and 10× is about 1 mile.

## Weather codes left in the kept (dry) hours
HZ haze 18,213 h · FU smoke 2,734 · VCTS thunder nearby 978 · TS thunder, no rain 547 · BLDU blowing dust 49 · DU dust 6 · SQ squall 6 · "-" formatting artifact 2. All wet codes were removed (audit files: `data/processed/metar/step05_dry/metar_<city>_removed.csv`).

## Caveats (for the story and the Forensics Appendix)
1. **Ann Arbor outage:** from ~2026-06-17, visibility and RH are blank in the raw reports (June 2026: 20 valid days, July 3, Aug 1, Sep 0). Not usable for summer 2026.
2. **10-mi ceiling:** 65% (Bakersfield) to 99% (Phoenix) of dry daytime hours are at the cap, so the metric can't tell clean days from very clean ones.
3. **Phoenix** has 0 days below 5 mi (haze index max ≈ 1.8×), so its row says little about its ozone and dust. Its two heavy duststorm hours were removed because rain was reported in the same hour.
4. **Point samples, some outside the city:** HRL 19.2 mi, DTW 16.1, PIT 12.9.
5. **Removing wet hours** may drop humid pollution days, and wet cities' series tilt toward hazier weather.
6. **7 unreviewed low days** (possibly uncoded fog), not to be used as story beats without checking: Boston 2024-02-23 · Bakersfield 2020-12-17/18 · Ann Arbor 2016-07-25 · Warren 2026-07-16/17 · Delano 2024-11-11.
7. **DLO/VLL** use no specials, so short events are less likely to register there.
8. ARB, DLO, SAN, VLL end 2026-09-23 (Sep 24 blank).

## Not done, by choice (none of these change values)
- "In city limits" check for the 6 new stations (D7, deferred).
- City-hall coordinate spot-check (Dish; least certain: Warren, Raymondville).
- ASOS internal visibility algorithm citation → Forensics Appendix.
