#!/bin/bash
# Step 4 · city-selection · ("air pollution" OR "air quality") AND "[State]" in the United States - National collection.
# Commands as run on 2026-09-26. Only change: API key read from $MEDIACLOUD_API_KEY.
# The original loop also wrote a copy to us_results.txt in a scratch folder (since deleted); raw values are in
# data/raw/city-selection/mediacloud_us_national_counts_responses.csv.
K="Authorization: Token $MEDIACLOUD_API_KEY"

# Find the national collection
curl -s -m 60 -H "$K" "https://search.mediacloud.org/api/sources/collections/?name=United%20States&limit=100" | python3 -c "import json,sys;[print(c['id'],'|',c['name'],'|',c['source_count']) for c in json.load(sys.stdin)['results'] if 'State & Local' not in c['name']]"

# One query per state, paced
for s in California Oregon Texas Alaska Michigan Indiana Pennsylvania Ohio "West Virginia" Arizona; do
 Q=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote('(\"air pollution\" OR \"air quality\") AND \"'+sys.argv[1]+'\"'))" "$s")
 for try in 1 2 3 4 5 6; do
  r=$(curl -s -m 180 -H "$K" "https://search.mediacloud.org/api/search/total-count?q=$Q&start=2024-09-25&end=2026-09-25&cs=34412234&platform=onlinenews-mediacloud")
  echo "$r" | grep -q relevant && break; perl -e 'select(undef,undef,undef,30)'
 done
 echo "$s | $r" | tee -a us_results.txt; perl -e 'select(undef,undef,undef,20)'
done
