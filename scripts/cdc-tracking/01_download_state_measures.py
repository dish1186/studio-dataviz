# CDC Tracking · Step 1 · download heat-related illness measures from the CDC Environmental Public Health Tracking
# Network Data API (https://ephtracking.cdc.gov/apigateway/api/v1), using the same calls as CDC's own R package
# EPHTrackR, get_data() (https://github.com/CDCgov/EPHTrackR, R/get_data.R), without installing it.
#
# Measures (content area 35, Heat & Heat-related Illness), in download order (daily first, Gina 2026-09-30):
#   1238  Daily rates of HRI-associated ED visits per 100,000 (non-VA)   HHS regions (geographic type 13)
#   1385  Daily rates of HRI-associated ED visits per 100,000 (VA)       HHS regions
#   1237  Weekly rates of HRI-associated ED visits per 100,000 (non-VA)  HHS regions
#   438   Annual number of ED visits for HRI                             states (geographic type 1)
#   370   Annual number of heat-related deaths (May-Sep)                 states
#   431   Annual number of hospitalizations for HRI                      states (to compare with the Explorer download)
# For each measure, at its geography with no stratification (the level whose stratification list is empty):
#   1. GET  stratificationlevel/{measure}/{geo type}/0
#   2. GET  temporalItems/{measure}/{geo type}/ALL/ALL      -> all days / weeks / years
#   3. GET  geographicItems/{measure}/{geo type}/0          -> all regions or states
#   4. POST getCoreHolder/{measure}/{level id}/0/0 with the geographic and temporal filters -> the data.
#      Daily and weekly measures are requested one calendar year at a time (parentTemporal), to keep requests small.
# Every response is saved unchanged (JSON) in data/raw/cdc-tracking/measure_<id>_<name>/; nothing is edited.
# Requests go through curl: Python's urllib fails the HTTPS certificate check on this Mac (as in city-selection Step 6).
# Optional token: environment variable EPHT_API_TOKEN (never written to any file). Without one, the API throttles
# ("too many non-token requests"), so the script waits PAUSE seconds between requests, skips measures already
# downloaded, and stops cleanly on a 429 so it can simply be run again later.
# Run from the repo root: python3 scripts/cdc-tracking/01_download_state_measures.py
import json, os, subprocess, sys, time

API = "https://ephtracking.cdc.gov/apigateway/api/v1/"
MEASURES = [(1238, 13, "daily_ed_rate_hri_nonva"), (1385, 13, "daily_ed_rate_hri_va"), (1237, 13, "weekly_ed_rate_hri_nonva"),
            (438, 1, "annual_ed_visits_hri"), (370, 1, "annual_heat_deaths"), (431, 1, "annual_hospitalizations_hri")]
OUT, PAUSE = "data/raw/cdc-tracking", 12
TOKEN = os.environ.get("EPHT_API_TOKEN")


def call(path, body=None):
    url = API + path + ("?apiToken=" + TOKEN if TOKEN else "")
    cmd = ["curl", "-sS", "-m", "300", "-w", "\n%{http_code}", "-H", "Accept: application/json"]
    if body is not None:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "--data-binary", "@-"]
    r = subprocess.run(cmd + [url], input=json.dumps(body).encode() if body is not None else None, capture_output=True)
    raw, _, code = r.stdout.rpartition(b"\n")
    if r.returncode != 0 or code != b"200":
        sys.exit(f"HTTP {code.decode() or r.returncode} on {path}: {raw[:200]!r} {r.stderr[:200]!r} -- run again later; finished measures are kept.")
    time.sleep(PAUSE)
    return raw


def save(folder, name, raw):
    with open(os.path.join(folder, name), "wb") as f:
        f.write(raw)
    return json.loads(raw)


for m, gt, label in MEASURES:
    folder = os.path.join(OUT, f"measure_{m}_{label}")
    if os.path.exists(os.path.join(folder, "DONE")) or os.path.exists(os.path.join(folder, "SKIPPED")):
        print(f"measure {m}: already downloaded"); continue
    os.makedirs(folder, exist_ok=True)
    levels = save(folder, "1_stratificationlevel.json", call(f"stratificationlevel/{m}/{gt}/0"))
    level = next((l for l in levels if not l["stratificationType"]), None)
    if level is None:   # the API offers no unstratified level for this measure and geography
        open(os.path.join(folder, "SKIPPED"), "w").write("stratificationlevel returned no level without stratification\n")
        print(f"measure {m}: no unstratified level at geographic type {gt}; skipped"); continue
    temporal = save(folder, "2_temporalItems.json", call(f"temporalItems/{m}/{gt}/ALL/ALL"))
    geo = save(folder, "3_geographicItems.json", call(f"geographicItems/{m}/{gt}/0"))
    ttype = str(temporal[0]["temporalTypeId"])
    groups = {}
    for t in temporal:
        key = t.get("parentTemporal") if ttype != "1" else "all"
        groups.setdefault(key or "all", []).append(str(t["temporal"]))
    total = 0
    for key in sorted(groups):
        body = {"geographicTypeIdFilter": str(gt), "geographicItemsFilter": ",".join(str(g["id"]) for g in geo),
                "temporalTypeIdFilter": ttype, "temporalItemsFilter": ",".join(sorted(groups[key], reverse=True))}
        tag = f"4_getCoreHolder_{key}"
        json.dump({"path": f"getCoreHolder/{m}/{level['id']}/0/0", "body": body}, open(os.path.join(folder, tag + "_request.json"), "w"))
        d = save(folder, tag + ".json", call(f"getCoreHolder/{m}/{level['id']}/0/0", body))
        n = max([len(v) for k, v in d.items() if k.endswith("ableResult") and isinstance(v, list)] or [0])  # e.g. tableResult, regionPMTableResult
        total += n
        print(f"measure {m} {key}: {n} rows", flush=True)
    open(os.path.join(folder, "DONE"), "w").write(f"{total} rows\n")
    print(f"measure {m}: {len(geo)} areas, {len(temporal)} time points ({temporal[0]['temporalType']}), {total} rows")
