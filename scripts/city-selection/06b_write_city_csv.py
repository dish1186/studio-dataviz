# Step 6b · city-selection · write news_coverage_by_city.csv from the Step 6 results (city_results.jsonl).
# Script as run on 2026-09-27. Usage: python3 06b_write_city_csv.py <output.csv>
# (Original also refused to overwrite an existing output file via a shell check before running.)
import csv,json,sys,urllib.parse
N={'CA':('California, United States -State & Local',1283),'OR':('Oregon, United States - State & Local',145),'TX':('Texas, United States - State & Local',593),'AK':('Alaska, United States - State & Local',77),'MI':('Michigan, United States - State & Local',203),'IN':('Indiana, United States - State & Local',167),'PA':('Pennsylvania, United States - State & Local',249),'OH':('Ohio, United States - State & Local',256),'WV':('West Virginia, United States - State & Local',81),'AZ':('Arizona, United States - State & Local',139)}
flag={'Springfield':'Also a city in IL/MA/MO','College':'Common word','Pasadena':'Also a city in CA','Warren':'Also a surname (e.g., Elizabeth Warren)','Mesa':'Also a common word / other places','Carmel':'Also Carmel, CA','Long Beach':'','Delano':'Also a surname'}
recs=[json.loads(l) for l in open('city_results.jsonl')]
assert len(recs)==36 and all('count' in r['result'] for r in recs)
with open(sys.argv[1],'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['#','Metro area (as listed)','City searched','State','Query','Collection ID (cs=)','Collection','Total sources in collection','Total stories','Index (stories / sources)','Start date','End date','Ambiguity note','API request URL'])
    for i,r in enumerate(recs,1):
        c,s=N[r['state']]; t=r['result']['count']['relevant']
        url='https://search.mediacloud.org/api/search/total-count?'+urllib.parse.urlencode(dict(q=r['q'],start='2024-09-25',end='2026-09-25',cs=r['cs'],platform='onlinenews-mediacloud'))
        w.writerow([i,r['metro'],r['city'],r['state'],r['q'],r['cs'],c,s,t,round(t/s,2),'2024-09-25','2026-09-25',flag.get(r['city'],''),url])
        print(f"| {i} | `{r['q']}` | {r['metro']} | {c} ({r['cs']}) | {s:,} | {t:,} | {t/s:.2f} |")
