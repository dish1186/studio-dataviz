# Reddit pipeline: study files

Every city, subreddit, time zone, week and word list lives in a **study file** here.
The scripts in `scripts/reddit/` have nothing hardcoded: point them at a study file.

## Run a study

```
python3 scripts/reddit/00_download_plan.py      --study studies/NAME.json   # what to download, and file names
python3 scripts/reddit/02_clean.py              --study studies/NAME.json
python3 scripts/reddit/03_remarkability.py      --study studies/NAME.json
python3 scripts/reddit/03b_validation_sample.py --study studies/NAME.json --n 25   # optional hand check
python3 scripts/reddit/03c_validation_results.py --study studies/NAME.json --coder gina
python3 scripts/reddit/04_mood.py               --study studies/NAME.json
python3 scripts/reddit/05_language.py           --study studies/NAME.json --set wide
```

Results go to `data/processed/reddit/<study>/`, one folder per study, so studies never overwrite each other.

## The study file

```json
{
  "study": "boston_heat_2026",                     // folder name for the results
  "topic_name": "heat",                            // used in printouts and the coding guide
  "lexicon_topic": "data/lexicons/lexicon_heat_v0.csv",
  "lexicon_registers": "data/lexicons/lexicon_registers_v0.csv",
  "near_miss_cities": [],                          // cities to hunt for missed talk in (step 03b)
  "cities": {
    "Boston": {"subreddit": "boston", "timezone": "America/New_York",
               "raw": ["data/raw/reddit/arctic-shift/boston_*.jsonl"]}
  },
  "windows": [                                     // named weeks: event vs baseline
    {"name": "boston_event_2026-05-18", "city": "Boston", "type": "event",
     "start": "2026-05-18", "days": 7, "group": "May 2026 early heat"},
    {"name": "boston_base_2025-05-19",  "city": "Boston", "type": "baseline",
     "start": "2025-05-19", "group": "May 2026 early heat"}
  ],
  "periods": [                                     // or: a continuous stretch cut into bins
    {"city": "Boston", "start": "2020-01-06", "end": "2026-09-27", "bin_days": 7}
  ]
}
```
(JSON has no comments: the notes above are only for this page.)

- **type**: `event` and `baseline` windows are compared within their **group** (each event against the mean of its group's baselines). `period` bins form a series: shares and mood per bin, no comparison.
- **days** defaults to 7. **start** is a local date in the city's time zone.
- **raw** is a list of file patterns. Posts and comments can be in the same or separate files, downloads can overlap (duplicates are dropped by id), and one big download can feed many windows.
- **Any type in the word list other than include / candidate / exclude** becomes its own separate measure, never counted as topic talk (e.g. `fire` in the air list).

## Studies here

| File | Topic | What it is |
|---|---|---|
| `eugene_bakersfield.json` | air | the case study already run (same windows, same results) |
| `boston_heat_2026.json` | heat | May 18–24, 2026 (96°F vs a typical 67°F) and Jun 29–Jul 5, 2026 (101°F record), each vs the same week in 2024 and 2025 |
| `boston_smoke_2023.json` | air | Jun 5–11, 2023 (Canadian wildfire smoke) vs 2024 and 2025. **Check the week against Boston's PM2.5 before using.** |
| `boston_weekly_2020_2026.json` | heat (or air) | every week, Jan 5 2020 to Sep 26 2026, **Sunday to Saturday** to line up with the weekly heat panel (`heat_map_weekly.csv`, Google Trends Step 13). Very large; raw files may be too big for GitHub (100 MB per file). |

## Heat and air in the same study

Step 02 runs once per study. Steps 03 to 05 run once per word list: the study file's own list by default,
or another with `--lexicon`. Each word list gets its own results folder, so both can sit side by side:

```
python3 scripts/reddit/02_clean.py         --study studies/boston_weekly_2020_2026.json
python3 scripts/reddit/03_remarkability.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv
python3 scripts/reddit/03_remarkability.py --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_air_v1.csv
python3 scripts/reddit/04_mood.py          --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv
python3 scripts/reddit/04_mood.py          --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_air_v1.csv
python3 scripts/reddit/05_language.py      --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_heat_v0.csv
python3 scripts/reddit/05_language.py      --study studies/boston_weekly_2020_2026.json --lexicon data/lexicons/lexicon_air_v1.csv
```
Results: `data/processed/reddit/<study>/step03_remarkability/lexicon_heat_v0/`, `.../lexicon_air_v1/`, and the same
inside `step04_mood/`, `step05_language/`, `step03b_validation/` and `step03c_validation/`.
Pass the same `--lexicon` to 03b and 03c to check that word list.

## Word lists

- `lexicon_air_v1.csv`: frozen, checked by hand on Eugene and Bakersfield. Not checked for other cities.
- `lexicon_heat_v0.csv`: **draft, not checked.** Excludes the Miami Heat (a Celtics rival), hot food and hot takes, and winter heating. Run 03b and code a sample before reporting any heat result.
- `lexicon_registers_v0.csv`: draft. In Eugene the Institutions register was mostly misreads; read `fragments.csv` before trusting any register.
