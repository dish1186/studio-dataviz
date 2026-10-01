#!/usr/bin/env python3
"""
scripts/reddit/00_download_plan.py

Prints what to download from the Arctic Shift web download tool for a study:
subreddit, start and end dates (one extra day on each side, since the tool only takes
dates and uses your browser's time zone), and the file names to save as.

Run:  python3 scripts/reddit/00_download_plan.py --study studies/boston_heat_2026.json
"""

import argparse
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from study import load_study   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    S = load_study(ap.parse_args().study)
    print(f"Study {S['name']}. Save files to data/raw/reddit/arctic-shift/ (they must match each city's \"raw\" pattern).\n")
    for city, info in S["cities"].items():
        cw = [w for w in S["windows"] if w["city"] == city]
        named = [w for w in cw if w["type"] != "period"]
        period = [w for w in cw if w["type"] == "period"]
        slug = city.lower().replace(" ", "")
        print(f"{city}  (r/{info['subreddit']}, {info['timezone']})")
        for w in named:
            a, b = w["start"] - timedelta(days=1), w["end"] + timedelta(days=2)
            print(f"  {w['name']:32s} download {a} -> {b}   save as {w['name']}_posts.jsonl / {w['name']}_comments.jsonl")
        if period:
            y0, y1 = period[0]["start"].year, period[-1]["end"].year
            print(f"  continuous period {period[0]['start']} -> {period[-1]['end']} ({len(period)} bins): download one year at a time")
            for y in range(y0, y1 + 1):
                print(f"    {y}: {y-1}-12-31 -> {y+1}-01-01   save as {slug}_{y}_posts.jsonl / {slug}_{y}_comments.jsonl")
            print("    (overlapping days are fine: duplicates are dropped by id)")
        print()


if __name__ == "__main__":
    main()
