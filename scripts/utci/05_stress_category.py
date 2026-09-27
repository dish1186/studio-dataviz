"""UTCI Step 5: heat/cold stress category per day from daily max UTCI (Bröde et al. 2012 scale, 10 bands).
Bands include their upper edge (Dish). Classified on °C (the scale's native unit); ranges reported in °F.
Read-only on inputs. Output: data/processed/utci/step05_stress/utci_<city>_stress.csv (+ summary)."""
import pathlib, numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
IN = ROOT/"data/processed/utci/step04_daily_max"
OUT = ROOT/"data/processed/utci/step05_stress"; OUT.mkdir(parents=True, exist_ok=True)
CITIES = ["losangeles","phoenix","sandiego","detroit","bakersfield","sanfrancisco",
          "fresno","boston","eugene","fairbanks","brownsville","annarbor"]   # D10 order
EDGES_C = [-np.inf, -40, -27, -13, 0, 9, 26, 32, 38, 46, np.inf]
LEVEL = [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4]
NAME = ["Extreme cold stress", "Very strong cold stress", "Strong cold stress", "Moderate cold stress",
        "Slight cold stress", "No thermal stress", "Moderate heat stress", "Strong heat stress",
        "Very strong heat stress", "Extreme heat stress"]
f = lambda c: round(c * 9/5 + 32, 1)
RANGE_F = ["<= -40.0 F"] + [f"{f(lo)} to {f(hi)} F" for lo, hi in zip(EDGES_C[1:-2], EDGES_C[2:-1])] + ["> 114.8 F"]

summary = []
for city in CITIES:
    d = pd.read_csv(IN/f"utci_{city}_daily_max.csv")
    k = pd.cut(d.utci_max_c, EDGES_C, labels=False, right=True)      # (lo, hi]: upper edge included
    d["stress_level"] = k.map(dict(enumerate(LEVEL))).astype("Int64")
    d["stress_category"] = k.map(dict(enumerate(NAME)))
    d["stress_range_f"] = k.map(dict(enumerate(RANGE_F)))
    d.to_csv(OUT/f"utci_{city}_stress.csv", index=False)
    s = d[(d.valid == 1) & (d.date >= "2016-01-01")].stress_level.value_counts().reindex(LEVEL, fill_value=0)
    summary.append({"city": city, "blank_days": int(d.stress_level.isna().sum()), **{f"L{l}": int(n) for l, n in s.items()}})
pd.DataFrame(summary).to_csv(OUT/"step05_summary.csv", index=False)
print(pd.DataFrame(summary).to_string(index=False))
