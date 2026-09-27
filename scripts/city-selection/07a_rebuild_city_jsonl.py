# Step 7a · city-selection · rebuild city_results.jsonl from news_coverage_by_city.csv.
# Script as run on 2026-09-27 (the original jsonl had been lost with the scratch folder). Keeps only the 'relevant'
# (Total Stories) count; the collection-wide 'total' is in data/raw/city-selection/mediacloud_city_counts_responses.csv.
import csv,json,os
rows=list(csv.DictReader(open(os.path.expanduser('~/Desktop/MDE/dataviz/news_coverage_by_city.csv'),encoding='utf-8-sig')))
print(len(rows), list(rows[0].keys()))
with open('city_results.jsonl','w') as o:
    for r in rows:
        o.write(json.dumps(dict(metro=r['Metro area (as listed)'],state=r['State'],city=r['City searched'],q=r['Query'],cs=int(r['Collection ID (cs=)']),result={'count':{'relevant':int(r['Total stories'])}}))+'\n')
