# studio-dataviz
MDE Collaborative Design Engineering Studio I (Harvard GSD + SEAS, Fall 2026)
Project 2: "AI-Augmented Storytelling with Data" · theme: Natural + Artificial
Team: Bidisha (Dish) Chowdhury & Gina

**Question:** what prompts human action on air quality and heat — the sensor
reading, what the body perceives, or the media — and where are our tolerance
thresholds?

## Scope
10 cities (Bakersfield, Fresno, Los Angeles, Fairbanks, Eugene, Brownsville,
Detroit, Pittsburgh, San Francisco, Boston) · city limits · daily,
2016-01-01 – 2026-09-25 · heat baseline 1991–2020

## Datasets
| Dataset | Row | Source | Status |
|---|---|---|---|
| Visibility | embodied air quality | METAR/ASOS via Iowa Environmental Mesonet | done |
| Actual temperature | sensor heat | gridMET 4 km via ClimateEngine | in progress |
| Felt heat (UTCI) | embodied heat | Copernicus ERA5-HEAT | not started |

## Layout
- `data/raw/<dataset>/` untouched downloads (never edited)
- `data/processed/<dataset>/stepNN_*/` intermediate outputs; `final/` for viz-ready files
- `scripts/<dataset>/NN_<step>.py` one script per step, run from the repo root
- `logs/data-log-dish.md` plain-language log of every step (feeds the
  Algorithmic Forensics Appendix); Gina keeps her own
- `docs/references.md` methods and citations

## Requirements
Python 3 with pandas (geopandas for boundary steps).

AI-assisted with Claude; every data step was approved by a human and logged.
