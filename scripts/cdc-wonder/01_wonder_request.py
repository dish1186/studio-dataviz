# CDC WONDER · Step 1 · send one saved query to the CDC WONDER API and save the response unchanged.
#
# How to make the query file (once, by hand, in the browser):
#   1. Open the database's request form on https://wonder.cdc.gov (e.g. Multiple Cause of Death), set the query
#      (group by, years, cause-of-death codes), and run it.
#   2. On the Results tab, click "API Options" and save the XML request file into data/raw/cdc-wonder/queries/.
# The API returns national data only: WONDER does not allow grouping or filtering by state, county or region
# through the API (https://wonder.cdc.gov/wonder/help/wonder-api.html). State-level numbers need the web form.
#
# Usage (from the repo root):  python3 scripts/cdc-wonder/01_wonder_request.py <query.xml> <database ID, e.g. D77>
# Sends: POST https://wonder.cdc.gov/controller/datarequest/<database ID>
#        with request_xml = the file's text and accept_datause_restrictions = true.
#        Sending "true" means the user has read and agreed to WONDER's data-use restrictions (Gina must confirm this).
# Saves: data/raw/cdc-wonder/<query name>_response.xml (as returned) and a parsed CSV of the data table
#        (data/processed/cdc-wonder/<query name>.csv); cells keep WONDER's own text, e.g. "Suppressed".
# CDC asks for at most one query every 2 minutes; this script sends exactly one request per run.
import csv, os, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

xml_path, db = sys.argv[1], sys.argv[2]
name = os.path.splitext(os.path.basename(xml_path))[0]
body = urllib.parse.urlencode({"request_xml": open(xml_path, encoding="utf-8").read(),
                               "accept_datause_restrictions": "true"}).encode()
req = urllib.request.Request(f"https://wonder.cdc.gov/controller/datarequest/{db}", data=body, method="POST",
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
with urllib.request.urlopen(req, timeout=300) as r:
    raw = r.read()
os.makedirs("data/raw/cdc-wonder", exist_ok=True); os.makedirs("data/processed/cdc-wonder", exist_ok=True)
open(f"data/raw/cdc-wonder/{name}_response.xml", "wb").write(raw)

root = ET.fromstring(raw)
rows = []
for r in root.iter("r"):                       # data table: rows <r>, cells <c l="label"> or <c v="value">
    rows.append([c.get("l") or c.get("v") or c.get("dt") or "" for c in r.findall("c")])
with open(f"data/processed/cdc-wonder/{name}.csv", "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)
print(len(raw), "bytes;", len(rows), "data rows ->", f"data/processed/cdc-wonder/{name}.csv")
