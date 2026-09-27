# Step 8 · city-selection · group the 36 cities into pollution × coverage quadrants (state-level and city-level) and list the top 3 per group.
# Written on 2026-09-27, after the fact: the top-3 table was first worked out in chat from the Step 7 check output.
# This script reproduces it from the repo files, using the same thresholds as the workbook (Step 7b):
#   pollution_score = mean of the available ALA ranks; High pollution if <= median over the 36 city rows
#   state coverage: High if state index >= median of the 10 state indices
#   city coverage:  High if city index  >= median of the 36 city indices
# Ranking inside each group (ties broken by the order of Gina's list, i.e. the city row number):
#   High/High: state-level by pollution_score (all CA cities share one index); city-level by index, highest first
#   High pollution/Low coverage: pollution_score, worst first, then lower index
#   Low pollution/High coverage: index, highest first
#   Low/Low: index, lowest first
# Run from the repo root: python3 scripts/city-selection/08_top3_by_group.py
import csv, statistics
P = 'data/processed/city-selection/'
city = list(csv.DictReader(open(P + 'step06_city_coverage/news_coverage_by_city.csv', encoding='utf-8-sig')))
st = list(csv.DictReader(open(P + 'step03_state_coverage/mediacloud_air_pollution_by_state.csv', encoding='utf-8-sig')))
ala = {r['metro_area']: r for r in csv.DictReader(open('data/raw/city-selection/ala_sota2026_pm25_rankings_transcribed.csv'))}
ABBR = {'California':'CA','Oregon':'OR','Texas':'TX','Alaska':'AK','Michigan':'MI','Indiana':'IN','Pennsylvania':'PA','Ohio':'OH','West Virginia':'WV','Arizona':'AZ'}
sidx = {ABBR[r['State']]: int(r['Total stories']) / int(r['Total sources in collection']) for r in st}

rows = []
for r in city:
    a = ala[r['Metro area (as listed)']]
    ranks = [int(x) for x in (a['ala_shortterm_pm25_rank_2026'], a['ala_yearlong_pm25_rank_2026']) if x]
    rows.append(dict(n=int(r['#']), city=r['City searched'], state=r['State'], score=statistics.mean(ranks),
                     s_idx=sidx[r['State']], c_idx=int(r['Total stories']) / int(r['Total sources in collection'])))
pt = statistics.median(r['score'] for r in rows)
stt = statistics.median(sidx.values())
ct = statistics.median(r['c_idx'] for r in rows)
print(f'thresholds: pollution <= {pt}, state coverage >= {stt:.3f}, city coverage >= {ct:.3f}')

GROUPS = ['High pollution / High coverage', 'High pollution / Low coverage', 'Low pollution / High coverage', 'Low pollution / Low coverage']
def group(r, k, thr):
    return ('High pollution' if r['score'] <= pt else 'Low pollution') + ' / ' + ('High coverage' if r[k] >= thr else 'Low coverage')
def order(g, k, level):
    if g == GROUPS[0]:
        return (lambda r: (r['score'], r['n'])) if level == 'state' else (lambda r: (-r[k], r['n']))
    if g == GROUPS[1]: return lambda r: (r['score'], r[k], r['n'])
    if g == GROUPS[2]: return lambda r: (-r[k], r['n'])
    return lambda r: (r[k], r['n'])

out = []
for level, k, thr in (('state', 's_idx', stt), ('city', 'c_idx', ct)):
    for g in GROUPS:
        members = sorted([r for r in rows if group(r, k, thr) == g], key=order(g, k, level))
        for rank, r in enumerate(members, 1):
            out.append([level, g, rank, r['city'], r['state'], r['score'], round(r[k], 4), len(members)])
        print(level, '|', g, '|', ', '.join(f"{r['city']} ({r['state']})" for r in members[:3]))
with open(P + 'step08_top3/quadrant_rankings.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['level', 'group', 'rank_in_group', 'city', 'state', 'pollution_score', 'coverage_index', 'group_size'])
    w.writerows(out)
