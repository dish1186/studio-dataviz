#!/bin/bash
# Step 3 · city-selection · total stories for "air pollution" OR "air quality" in each state collection, 2024-09-25 to 2026-09-25.
# Commands as run on 2026-09-26. Only change: API key read from $MEDIACLOUD_API_KEY.
K="Authorization: Token $MEDIACLOUD_API_KEY"
Q=$(python3 -c "import urllib.parse;print(urllib.parse.quote('\"air pollution\" OR \"air quality\"'))")

# Attempt 1 (all 10 states, no pacing). California and Oregon returned counts; the other 8 returned "rate limited".
for p in "California:38380550" "Oregon:38381398" "Texas:38381323" "Alaska:38381315" "Michigan:38381374" "Indiana:38381358" "Pennsylvania:38381340" "Ohio:38381394" "West Virginia:38381408" "Arizona:38381317"; do
 n=${p%%:*}; id=${p##*:}
 echo "$n | $(curl -s -m 180 -H "$K" "https://search.mediacloud.org/api/search/total-count?q=$Q&start=2024-09-25&end=2026-09-25&cs=$id&platform=onlinenews-mediacloud")"
done

# Attempt 2 (the 8 rate-limited states), paced: 20 s between states, up to 6 tries 30 s apart.
for p in "Texas:38381323" "Alaska:38381315" "Michigan:38381374" "Indiana:38381358" "Pennsylvania:38381340" "Ohio:38381394" "West Virginia:38381408" "Arizona:38381317"; do
 n=${p%%:*}; id=${p##*:}
 for try in 1 2 3 4 5 6; do
  r=$(curl -s -m 180 -H "$K" "https://search.mediacloud.org/api/search/total-count?q=$Q&start=2024-09-25&end=2026-09-25&cs=$id&platform=onlinenews-mediacloud")
  echo "$r" | grep -q relevant && break; perl -e 'select(undef,undef,undef,30)'
 done
 echo "$n | $r"; perl -e 'select(undef,undef,undef,20)'
done
