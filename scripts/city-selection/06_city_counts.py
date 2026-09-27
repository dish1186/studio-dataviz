# Step 6 · city-selection · ("air pollution" OR "air quality") AND "[city]" for each of the 36 cities, in its own state's collection.
# Reconstructed on 2026-09-27: the original file (cities.py) was in a scratch folder that was cleared when the session restarted.
# This is the original text with the fix applied mid-step (requests switched from urllib to curl, because Python's
# urllib failed the SSL certificate check on this Mac). The API key, typed inline originally, is read from $MEDIACLOUD_API_KEY.
import os, subprocess, json, time, urllib.parse, urllib.request
K = os.environ["MEDIACLOUD_API_KEY"]
C = {'CA':38380550,'OR':38381398,'TX':38381323,'AK':38381315,'MI':38381374,'IN':38381358,'PA':38381340,'OH':38381394,'WV':38381408,'AZ':38381317}
rows = [("Bakersfield-Delano, CA","CA",["Bakersfield","Delano"]),
("Eugene-Springfield, OR","OR",["Eugene","Springfield"]),
("Brownsville-Harlingen-Raymondville, TX","TX",["Brownsville","Harlingen","Raymondville"]),
("Fresno-Hanford-Corcoran, CA","CA",["Fresno","Hanford","Corcoran"]),
("Visalia, CA","CA",["Visalia"]),
("Fairbanks-College, AK","AK",["Fairbanks","College"]),
("Los Angeles-Long Beach, CA","CA",["Los Angeles","Long Beach"]),
("Detroit-Warren-Ann Arbor, MI","MI",["Detroit","Warren","Ann Arbor"]),
("Indianapolis-Carmel-Muncie, IN","IN",["Indianapolis","Carmel","Muncie"]),
("Pittsburgh-Weirton-Steubenville, PA-OH-WV","PA",["Pittsburgh"]),
("Pittsburgh-Weirton-Steubenville, PA-OH-WV","WV",["Weirton"]),
("Pittsburgh-Weirton-Steubenville, PA-OH-WV","OH",["Steubenville"]),
("McAllen-Edinburg, TX","TX",["McAllen","Edinburg"]),
("San Diego-Chula Vista-Carlsbad, CA","CA",["San Diego","Chula Vista","Carlsbad"]),
("Phoenix-Mesa, AZ","AZ",["Phoenix","Mesa"]),
("San Jose-San Francisco-Oakland, CA","CA",["San Jose","San Francisco","Oakland"]),
("Houston-Pasadena, TX","TX",["Houston","Pasadena"])]
out = open("city_results.jsonl","a")
for metro, st, cities in rows:
    for city in cities:
        q = f'("air pollution" OR "air quality") AND "{city}"'
        url = "https://search.mediacloud.org/api/search/total-count?" + urllib.parse.urlencode(dict(q=q,start="2024-09-25",end="2026-09-25",cs=C[st],platform="onlinenews-mediacloud"))
        for t in range(8):
            try:
                r = json.loads(subprocess.run(["curl","-s","-m","180","-H","Authorization: Token "+K,url],capture_output=True,text=True).stdout)
            except Exception as e:
                r = {"err": str(e)}
            if "count" in r: break
            time.sleep(30)
        rec = dict(metro=metro, state=st, city=city, q=q, cs=C[st], result=r)
        out.write(json.dumps(rec)+"\n"); out.flush()
        print(st, city, r.get("count", r), flush=True)
        time.sleep(20)
print("DONE", flush=True)
