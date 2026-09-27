# Step 4b · city-selection · write the US-national vs state-collection comparison CSV.
# Script as run on 2026-09-26 (values typed in from the Step 3 and Step 4 output), except the output path: the original
# took it as an argument pointing at ~/Desktop/MDE/dataviz/. Usage: python3 04b_write_us_csv.py <output.csv>
import csv,sys
st={'California':(38380550,1283,26181),'Oregon':(38381398,145,1845),'Texas':(38381323,593,6474),'Alaska':(38381315,77,562),'Michigan':(38381374,203,4672),'Indiana':(38381358,167,2150),'Pennsylvania':(38381340,249,5046),'Ohio':(38381394,256,3010),'West Virginia':(38381408,81,1754),'Arizona':(38381317,139,1211)}
us={'California':4953,'Oregon':905,'Texas':2153,'Alaska':345,'Michigan':1408,'Indiana':720,'Pennsylvania':1032,'Ohio':986,'West Virginia':335,'Arizona':1063}
N=246
rs=sorted(st,key=lambda s:-st[s][2]/st[s][1]); ru=sorted(us,key=lambda s:-us[s])
with open(sys.argv[1],'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['#','State','US query','US collection ID (cs=)','US collection','US collection sources','US total stories','US index (stories / sources)','US rank','State-collection query','State collection ID (cs=)','State collection sources','State-collection total stories','State-collection index','State-collection index rank','Start date','End date','US API request URL'])
    for i,s in enumerate(st,1):
        q=f'("air pollution" OR "air quality") AND "{s}"'
        cid,src,t=st[s]
        w.writerow([i,s,q,34412234,'United States - National',N,us[s],round(us[s]/N,2),ru.index(s)+1,'"air pollution" OR "air quality"',cid,src,t,round(t/src,2),rs.index(s)+1,'2024-09-25','2026-09-25',
          f'https://search.mediacloud.org/api/search/total-count?q={q}&start=2024-09-25&end=2026-09-25&cs=34412234&platform=onlinenews-mediacloud'])
        print(s,us[s],round(us[s]/N,2),ru.index(s)+1,rs.index(s)+1)
