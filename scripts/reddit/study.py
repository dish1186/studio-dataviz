"""
scripts/reddit/study.py

Shared settings and helpers for the Reddit pipeline (steps 02-05).
Everything city- or period-specific lives in a study file (studies/<name>.json),
not in the scripts. See studies/README.md for the format.
"""

import bisect
import csv
import glob
import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

STD_TYPES = {"include", "candidate", "exclude"}


def load_study(path):
    cfg = json.load(open(path, encoding="utf-8"))
    name = cfg["study"]
    cities = cfg["cities"]
    windows = []
    for w in cfg.get("windows", []):
        windows.append({"name": w["name"], "city": w["city"], "type": w["type"],
                        "start": date.fromisoformat(w["start"]), "days": int(w.get("days", 7)),
                        "group": w.get("group", w["city"])})
    for p in cfg.get("periods", []):           # a continuous stretch, cut into equal bins
        d, end, step = date.fromisoformat(p["start"]), date.fromisoformat(p["end"]), int(p.get("bin_days", 7))
        while d + timedelta(days=step - 1) <= end:
            windows.append({"name": f"{p['city'].lower().replace(' ', '')}_{d.isoformat()}", "city": p["city"],
                            "type": "period", "start": d, "days": step, "group": p.get("group", f"{p['city']} period")})
            d += timedelta(days=step)
    names = [w["name"] for w in windows]
    if len(names) != len(set(names)):
        raise SystemExit("study file: window names must be unique")
    for w in windows:
        if w["city"] not in cities:
            raise SystemExit(f"study file: window {w['name']} uses city {w['city']} not listed under cities")
        if w["type"] not in {"event", "baseline", "period"}:
            raise SystemExit(f"study file: window {w['name']} type must be event, baseline or period")
        tz = ZoneInfo(cities[w["city"]]["timezone"])
        w["tz"] = tz
        w["t0"] = int(datetime.combine(w["start"], time(0), tz).timestamp())
        w["t1"] = int(datetime.combine(w["start"] + timedelta(days=w["days"]), time(0), tz).timestamp())
        w["end"] = w["start"] + timedelta(days=w["days"] - 1)
    out = Path(cfg.get("output_root", "data/processed/reddit")) / name
    return {
        "cfg": cfg, "name": name, "cities": cities, "windows": windows, "out": out,
        "lex_topic": Path(cfg.get("lexicon_topic", "data/lexicons/lexicon_air_v1.csv")),
        "lex_registers": Path(cfg.get("lexicon_registers", "data/lexicons/lexicon_registers_v0.csv")),
        "topic": cfg.get("topic_name", "air"),
        "near_miss_cities": cfg.get("near_miss_cities", []),
        "near_miss_hint": cfg.get("near_miss_hint",
            r"\b(?:air|outside|breath\w*|burn\w*|haz\w*|fog\w*|cough\w*|visib\w*|allerg\w*|asthma\w*|pollut\w*|inversion\w*|valley)\b"),
    }


def raw_files(study, city):
    pats = study["cities"][city].get("raw", [f"data/raw/reddit/arctic-shift/{city.lower().replace(' ', '')}_*.jsonl"])
    files = sorted({f for p in pats for f in glob.glob(p)})
    return files


class WindowIndex:
    """Finds every window of one city that contains a timestamp."""
    def __init__(self, windows):
        self.w = sorted(windows, key=lambda x: x["t0"])
        self.starts = [x["t0"] for x in self.w]
        self.maxlen = max((x["t1"] - x["t0"] for x in self.w), default=0)

    def find(self, t):
        hits, j = [], bisect.bisect_right(self.starts, t) - 1
        while j >= 0 and t - self.w[j]["t0"] < self.maxlen:
            if self.w[j]["t0"] <= t < self.w[j]["t1"]:
                hits.append(self.w[j])
            j -= 1
        return hits


def load_topic_lexicon(path):
    lex = {"include": [], "candidate": [], "exclude": []}
    sep = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        t = r["type"].strip()
        p = (r["term"], re.compile(r["pattern"], re.IGNORECASE))
        if t in STD_TYPES:
            lex[t].append(p)
        else:                              # any other type is its own separate measure (e.g. "fire")
            sep.setdefault(t, []).append(p)
    lex["separate"] = sep
    return lex


def flag_topic(text, lex):
    t = text or ""
    for _, p in lex["exclude"]:
        t = p.sub(" ", t)
    inc = [term for term, p in lex["include"] if p.search(t)]
    cand = [term for term, p in lex["candidate"] if p.search(t)]
    seps = {k: [term for term, p in v if p.search(t)] for k, v in lex["separate"].items()}
    terms = inc + [c + "*" for c in cand] + [x + "^" for v in seps.values() for x in v]
    return bool(inc), bool(inc or cand), {k: bool(v) for k, v in seps.items()}, terms


def boot_mean(df, col, rng, B):
    """Thread-level bootstrap of the mean of df[col] (a share if col is True/False)."""
    g = df.groupby("thread_id")[col].agg(["sum", "count"])
    s, n = g["sum"].to_numpy(dtype=float), g["count"].to_numpy(dtype=float)
    if len(g) == 0:
        return np.full(B, np.nan)
    idx = rng.integers(0, len(g), size=(B, len(g)))
    return s[idx].sum(1) / n[idx].sum(1)


def comparisons(study):
    """For each group: its event windows and its baseline windows."""
    out = []
    groups = {}
    for w in study["windows"]:
        groups.setdefault(w["group"], {"event": [], "baseline": []})
        if w["type"] in ("event", "baseline"):
            groups[w["group"]][w["type"]].append(w["name"])
    for g, v in groups.items():
        if v["event"] and v["baseline"]:
            for e in v["event"]:
                out.append({"group": g, "event": e, "baselines": v["baseline"]})
    return out


def topic_for(study, lexicon_arg):
    """Word list and topic name for this run: the study file's, or the --lexicon override
    (topic named from the file, e.g. lexicon_heat_v0.csv -> "heat")."""
    if not lexicon_arg:
        return study["lex_topic"], study["topic"]
    lex = Path(lexicon_arg)
    parts = lex.stem.split("_")
    return lex, (parts[1] if len(parts) > 1 and parts[0] == "lexicon" else lex.stem)
