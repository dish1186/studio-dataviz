# Step 3b · city-selection · write the state-level results table to CSV.
# Script as run on 2026-09-26 (values typed in from the Step 3 output). Written to the working folder, then moved to
# ~/Desktop/MDE/dataviz/ at Gina's request; repo copy: data/processed/city-selection/step03_state_coverage/.
import csv
d=[('California',38380550,'California, United States -State & Local',1283,26181,'Bakersfield-Delano; Fresno-Hanford-Corcoran; Visalia; Los Angeles-Long Beach; San Diego-Chula Vista-Carlsbad; San Jose-San Francisco-Oakland'),
('Oregon',38381398,'Oregon, United States - State & Local',145,1845,'Eugene-Springfield'),
('Texas',38381323,'Texas, United States - State & Local',593,6474,'Brownsville-Harlingen-Raymondville; McAllen-Edinburg; Houston-Pasadena'),
('Alaska',38381315,'Alaska, United States - State & Local',77,562,'Fairbanks-College'),
('Michigan',38381374,'Michigan, United States - State & Local',203,4672,'Detroit-Warren-Ann Arbor'),
('Indiana',38381358,'Indiana, United States - State & Local',167,2150,'Indianapolis-Carmel-Muncie'),
('Pennsylvania',38381340,'Pennsylvania, United States - State & Local',249,5046,'Pittsburgh-Weirton-Steubenville'),
('Ohio',38381394,'Ohio, United States - State & Local',256,3010,'Pittsburgh-Weirton-Steubenville'),
('West Virginia',38381408,'West Virginia, United States - State & Local',81,1754,'Pittsburgh-Weirton-Steubenville'),
('Arizona',38381317,'Arizona, United States - State & Local',139,1211,'Phoenix-Mesa')]
with open('mediacloud_air_pollution_by_state.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['#','State','Query','Collection ID (cs=)','Collection','Cities','Start date','End date','Platform','Total sources in collection','Total stories','Index (stories / sources)','API request URL'])
    for i,(s,cid,c,src,st,cities) in enumerate(d,1):
        w.writerow([i,s,'"air pollution" OR "air quality"',cid,c,cities,'2024-09-25','2026-09-25','onlinenews-mediacloud',src,st,round(st/src,2),
          f'https://search.mediacloud.org/api/search/total-count?q="air pollution" OR "air quality"&start=2024-09-25&end=2026-09-25&cs={cid}&platform=onlinenews-mediacloud'])
