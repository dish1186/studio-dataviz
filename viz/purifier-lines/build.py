"""Build data.json for the Purifier Searches line chart (V11): weekly Google Trends "air purifier", 7 metros, as downloaded.
Run from the repo root: python3 viz/purifier-lines/build.py"""
import csv, json
CITIES = [("bakersfield", "Bakersfield"), ("eugene", "Eugene"), ("detroit", "Detroit"), ("boston", "Boston"),
          ("phoenix", "Phoenix"), ("sandiego", "San Diego"), ("sanfrancisco", "San Francisco")]
weeks, series = None, []
for slug, label in CITIES:
    rows = [r for r in list(csv.reader(open(f"data/raw/google-trends/air-search-weekly/{slug}_purifier_5yr.csv")))[3:] if r and r[0]]
    w = [r[0] for r in rows]
    assert weeks is None or w == weeks, slug
    weeks = w
    series.append({"slug": slug, "label": label, "v": [0 if r[1] == "<1" else int(r[1]) for r in rows]})
json.dump({"weeks": weeks, "series": series}, open("viz/purifier-lines/data.json", "w"), separators=(",", ":"))
print(len(weeks), weeks[0], weeks[-1])
