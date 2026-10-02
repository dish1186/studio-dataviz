"""Render the V11 chart (7 metros, weekly 'air purifier' searches, 4-week centred average, last partial week dropped)
as PNG with no dependencies: black lines, optional faint baseline. Writes a transparent and a white-background version.
Run from the repo root: python3 viz/purifier-lines/render_png.py"""
import json, zlib, struct, math
D = json.load(open("viz/purifier-lines/data.json"))
S = 3                        # scale: SVG viewBox 1000x440 -> 3000x1320 plus padding
PAD = 60
W, H = 1000 * S + 2 * PAD, 440 * S + 2 * PAD
HALF = 1.1 * S / 2           # line half-width in px (SVG stroke 1.1)
n = len(D["weeks"]) - 1      # drop the last, partial week
X = lambda i: PAD + i / (n - 1) * 1000 * S
Y = lambda v: PAD + (430 - v / 100 * 420) * S
def sm(v):
    return [sum(v[max(0, i - 1):min(n, i + 3)]) / len(v[max(0, i - 1):min(n, i + 3)]) for i in range(n)]
cov = bytearray(W * H)       # line coverage 0-255 (max, so overlaps stay solid black)
def seg(x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy or 1e-9
    for py in range(max(0, int(min(y0, y1) - HALF - 2)), min(H, int(max(y0, y1) + HALF + 3))):
        for px in range(max(0, int(min(x0, x1) - HALF - 2)), min(W, int(max(x0, x1) + HALF + 3))):
            cx, cy = px + .5, py + .5
            t = max(0, min(1, ((cx - x0) * dx + (cy - y0) * dy) / L2))
            d = math.hypot(cx - x0 - t * dx, cy - y0 - t * dy)
            a = HALF + .5 - d
            if a > 0:
                c = 255 if a >= 1 else int(a * 255); k = py * W + px
                if c > cov[k]: cov[k] = c
for s in D["series"]:
    v = sm(s["v"][:n]); pts = [(X(i), Y(t)) for i, t in enumerate(v)]
    for (a, b), (c, d) in zip(pts, pts[1:]): seg(a, b, c, d)
base_y = int(Y(0)) + 0   # faint baseline under the lines, as on the page
def png(path, white):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            c = cov[y * W + x]
            if white:
                if c: g = 17 + (255 - 17) * (255 - c) // 255; raw += bytes((g, g, g - 1 if g else 0, 255))
                elif abs(y - base_y) < S // 2 + 1 and PAD <= x < W - PAD: raw += bytes((0xd9, 0xd5, 0xcf, 255))
                else: raw += b"\xff\xff\xff\xff"
            else:
                if c: raw += bytes((17, 17, 16, c))
                elif abs(y - base_y) < S // 2 + 1 and PAD <= x < W - PAD: raw += bytes((0, 0, 0, 40))
                else: raw += b"\x00\x00\x00\x00"
    def chunk(t, b): return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xffffffff)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
png("viz/purifier-lines/purifier-lines.png", True)
png("viz/purifier-lines/purifier-lines-transparent.png", False)
print(W, H)
