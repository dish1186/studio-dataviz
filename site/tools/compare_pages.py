"""Compare how the site looks with the published snapshot, screenshot by screenshot. Reads files only.

What it does: unpacks the snapshot (commit d689e08) to a temporary folder, serves it and site/ on two local ports,
loads both in headless Chrome with reduced motion (so animations sit still) and the same random numbers, scrolls
both from top to bottom in 700 px steps, and compares the screenshots pixel by pixel. It also lists any script
errors or files that failed to load. With reduced motion the two should be identical.

Needs: Python with Pillow and websocket-client (pip install pillow websocket-client), and Google Chrome started
headless with remote debugging, e.g. on a Mac:
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --remote-debugging-port=9333 \
      --user-data-dir=/tmp/bf-chrome --window-size=1440,900 --hide-scrollbars about:blank &
Run from the repo root:  python3 site/tools/compare_pages.py
"""
import base64
import functools
import http.server
import io
import json
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

import websocket
from PIL import Image, ImageChops

SNAPSHOT, CHROME, STEP, TOL = "d689e08", "http://127.0.0.1:9333", 700, 0.002


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(folder):
    handler = functools.partial(Quiet, directory=folder)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}/"


tmp = tempfile.mkdtemp()
subprocess.run(f"git archive {SNAPSHOT} site | tar -x -C {tmp}", shell=True, check=True)
pages = {"snapshot": serve(f"{tmp}/site"), "site": serve("site")}

tabs = [t for t in json.load(urllib.request.urlopen(f"{CHROME}/json")) if t["type"] == "page"]
tab = tabs[0] if tabs else json.load(urllib.request.urlopen(urllib.request.Request(f"{CHROME}/json/new?about:blank", method="PUT")))
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=120, suppress_origin=True)
mid = 0


def call(method, **params):
    global mid
    mid += 1
    ws.send(json.dumps({"id": mid, "method": method, "params": params}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid:
            return r.get("result", r)


def ev(expr, wait=False):
    return call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=wait).get("result", {}).get("value")


call("Emulation.setDeviceMetricsOverride", width=1440, height=900, deviceScaleFactor=1, mobile=False)
call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"},
                                             {"name": "prefers-reduced-motion", "value": "reduce"}])
# same random numbers in both pages, and a record of every script error or file that failed to load
call("Page.addScriptToEvaluateOnNewDocument", source="""(()=>{let s=12345;Math.random=()=>{s=(s*1103515245+12345)%2147483648;return s/2147483648};
 window.__errs=[];addEventListener("error",e=>__errs.push(e.message||("failed: "+(e.target&&(e.target.src||e.target.href)))),true);})()""")
call("Page.enable")

shots = {}
for name, url in pages.items():
    call("Page.navigate", url=url)
    time.sleep(7)
    ev("document.fonts.ready.then(()=>1)", True)
    height = ev("document.documentElement.scrollHeight")
    imgs = []
    for y in range(0, height, STEP):
        ev(f"scrollTo(0,{y});1")
        time.sleep(1.3)
        imgs.append(Image.open(io.BytesIO(base64.b64decode(call("Page.captureScreenshot", format="png")["data"]))).convert("RGB"))
    shots[name] = (height, imgs, ev("__errs"))
    print(f"{name}: page height {height}px, {len(imgs)} screenshots, errors: {shots[name][2] or 'none'}")

(h1, a, e1), (h2, b, e2) = shots["snapshot"], shots["site"]
diff = []
for k, (x, y) in enumerate(zip(a, b)):
    d = ImageChops.difference(x, y).convert("L").point(lambda v: 255 if v > 24 else 0)
    frac = d.histogram()[255] / (d.width * d.height)
    if frac > TOL:
        diff.append((k * STEP, round(100 * frac, 2)))
same = h1 == h2 and len(a) == len(b) and not diff and not e2
print("differing positions (scroll px, % of pixels):", diff or "none")
print("IDENTICAL" if same else "DIFFERENT")
sys.exit(0 if same else 1)
