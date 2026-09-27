#!/bin/bash
# Step 2 · city-selection · find each state's Media Cloud "State & Local" collection and its source count.
# Commands as run on 2026-09-26. Only change: the API key, which was typed inline, is read from $MEDIACLOUD_API_KEY.
K="Authorization: Token $MEDIACLOUD_API_KEY"

# First command (California), run on its own
curl -s -m 60 -H "$K" "https://search.mediacloud.org/api/sources/collections/?name=California&limit=20" | head -c 3000

# Remaining states
for s in Oregon Texas Alaska Michigan Indiana Pennsylvania Ohio "West%20Virginia" Arizona; do
curl -s -m 60 -H "$K" "https://search.mediacloud.org/api/sources/collections/?name=$s&limit=20" | python3 -c "import json,sys;[print(c['id'],'|',c['name'],'|',c['source_count']) for c in json.load(sys.stdin)['results'] if 'United States' in c['name']]"
done
