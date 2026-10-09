"""Render Plate II (the threshold doors) as a looping high-res GIF.

Same geometry and timing as the scroll-driven SVG in index.html (draw(p, t)), drawn with Pillow at
SS x supersampling and downsampled to OUT_W px wide. The scroll progress p is replaced by a clock:
hold at the first door, walk door to door, hold in the light of the last door, loop.

    python3 make_threshold_gif.py            -> img/threshold-walk.gif (2000 x 600)
    python3 make_threshold_gif.py --width 1200 --no-paper
"""
import argparse, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
GREEN, DOOR, FLOOR, BEAM, SHADOW, WALKER = "#03764f", "#c4285c", "#ef9581", "#eab198", "#3e484e", "#210515"
VW, VH = 2000, 600
# each door: left edge x, top and bottom y; right edge x, top and bottom y (from index.html)
D = [dict(zip(("x", "yt", "yb", "xr", "ytr", "ybr"), d)) for d in
     [(62, 140, 385, 184, 117, 355), (486, 128, 368, 608, 100, 338), (910, 122, 368, 1032, 100, 338), (1255, 113, 330, 1358, 95, 310)]]


def ss(t):
    return t * t * (3 - 2 * t)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def perlin(h, w, freq, seed):
    """2-D gradient noise, roughly what feTurbulence fractalNoise (1 octave) gives: values around 0.5."""
    rng = np.random.default_rng(seed)
    gh, gw = int(h * freq) + 2, int(w * freq) + 2
    ang = rng.uniform(0, 2 * np.pi, (gh, gw))
    gx, gy = np.cos(ang), np.sin(ang)
    y, x = np.mgrid[0:h, 0:w] * freq
    x0, y0 = x.astype(int), y.astype(int)
    fx, fy = x - x0, y - y0
    dot = lambda ix, iy, dx, dy: gx[iy, ix] * dx + gy[iy, ix] * dy
    n00, n10 = dot(x0, y0, fx, fy), dot(x0 + 1, y0, fx - 1, fy)
    n01, n11 = dot(x0, y0 + 1, fx, fy - 1), dot(x0 + 1, y0 + 1, fx - 1, fy - 1)
    u, v = ss(fx), ss(fy)
    n = (n00 * (1 - u) + n10 * u) * (1 - v) + (n01 * (1 - u) + n11 * u) * v
    return (n + 1) / 2


def walker_shape(fx, fy):
    """The figure: head circle + body path (M2,-118 C2,-126 24,-126 24,-118 L26,-44 L21,0 L5,0 L0,-44 Z)."""
    top = [((1 - t) ** 3 * 2 + 3 * (1 - t) ** 2 * t * 2 + 3 * (1 - t) * t * t * 24 + t ** 3 * 24,
            (1 - t) ** 3 * -118 + 3 * (1 - t) ** 2 * t * -126 + 3 * (1 - t) * t * t * -126 + t ** 3 * -118)
           for t in np.linspace(0, 1, 16)]
    body = top + [(26, -44), (21, 0), (5, 0), (0, -44)]
    return [(fx + x, fy + y) for x, y in body], (fx + 13, fy - 132, 8.5)


def frame_geometry(p, t):
    """Port of draw(p, t) in index.html."""
    f = min(3, p * 3); k = min(2, math.floor(f)); u = f - k
    e = ss(min(1, max(0, (u - .25) / .5)))
    a, b = D[k], D[min(3, k + 1)]
    moving = 0 < e < 1
    fx = a["x"] - 4 + (b["x"] - a["x"]) * e
    fy = a["yb"] - 2 + (b["yb"] - a["yb"]) * e
    pos = k + e
    wy = fy + (-abs(math.sin(t * 9)) * 3 if moving else 0)
    beams = []
    for i, d in enumerate(D):
        w = max(0, 1 - abs(pos - i) * 1.6)
        if w <= 0:
            continue
        L = (760 if i == 3 else 520) * ss(w)
        beams.append([(d["x"], d["yb"]), (d["xr"], d["ybr"]), (d["xr"] + L * 1.08, d["ybr"] + L * 1.08 * .32), (d["x"] + L, d["yb"] + L * .4)])
    near = round(pos)
    wn = max(0, 1 - abs(pos - near) * 1.6)
    L = (760 if near == 3 else 520) * ss(wn) * .86
    shadow = [(fx + 5, fy), (fx + 22, fy - 3), (fx + 22 + L, fy - 3 + L * .3), (fx + 4 + L, fy + L * .345 + 8)]
    return fx, wy, beams, shadow, wn * .85


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=2000)
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--walk", type=float, default=7.0, help="seconds for the walk past all doors")
    ap.add_argument("--hold-start", type=float, default=0.8)
    ap.add_argument("--hold-end", type=float, default=2.6)
    ap.add_argument("--no-paper", action="store_true")
    ap.add_argument("--out", default=str(HERE / "img" / "threshold-walk.gif"))
    a = ap.parse_args()

    SS = 3
    OW, OH = a.width, round(a.width * VH / VW)
    s = OW * SS / VW                                   # viewBox units -> supersampled px
    W, H = OW * SS, OH * SS
    sc = lambda pts: [(x * s, y * s) for x, y in pts]

    # speck mask for the light beams: noise thresholded into dots (feColorMatrix alpha = 5n - 1.6), fixed in space.
    # The noise lives at output resolution (its grain is ~1 viewBox unit, finer than a supersampled pixel would hold).
    n = perlin(OH, OW, 0.9 * VW / OW * 1.0, seed=7)
    speck = np.clip(5 * n - 1.6, 0, 1)
    speck = np.asarray(Image.fromarray((speck * 255).astype(np.uint8)).resize((W, H), Image.NEAREST), dtype=np.float32) / 255

    # static layer: the doors and the light on each doorway floor
    doors = Image.new("L", (W, H), 0); dd = ImageDraw.Draw(doors)
    floors = Image.new("L", (W, H), 0); fd = ImageDraw.Draw(floors)
    for d in D:
        dd.polygon(sc([(d["x"], d["yt"]), (d["xr"], d["ytr"]), (d["xr"], d["ybr"]), (d["x"], d["yb"])]), fill=255)
        fd.polygon(sc([(d["x"], d["yb"] - 62), (d["xr"], d["ybr"] - 2), (d["xr"], d["ybr"]), (d["x"], d["yb"])]), fill=255)
    doors_m = np.asarray(doors, dtype=np.float32) / 255
    floors_m = np.asarray(floors, dtype=np.float32) / 255
    col = {k: np.array(rgb(v), dtype=np.float32) for k, v in dict(g=GREEN, d=DOOR, f=FLOOR, b=BEAM, s=SHADOW, w=WALKER).items()}

    paper = None
    if not a.no_paper:                                 # the page's paper grain: img/paper.jpg, multiply at 16%, tiled at 1440 css px
        pj = Image.open(HERE / "img" / "paper.jpg").convert("RGB")
        tile = round(1440 * OW / 1280)                 # the plate is ~1280 css px wide on a laptop
        pj = pj.resize((tile, round(pj.height * tile / pj.width)), Image.LANCZOS)
        P = Image.new("RGB", (OW, OH)); [P.paste(pj, (x, y)) for x in range(0, OW, pj.width) for y in range(0, OH, pj.height)]
        paper = 1 - .16 * (1 - np.asarray(P, dtype=np.float32) / 255)

    def over(img, mask, c, alpha=1.0):
        m = mask[..., None] * alpha
        img *= 1 - m; img += m * c

    n_hold0, n_walk, n_hold1 = (round(x * a.fps) for x in (a.hold_start, a.walk, a.hold_end))
    frames = []
    for i in range(n_hold0 + n_walk + n_hold1):
        p = min(1, max(0, (i - n_hold0) / (n_walk - 1)))
        fx, fy, beams, shadow, sop = frame_geometry(p, i / a.fps)
        img = np.empty((H, W, 3), np.float32); img[:] = col["g"]
        for bp in beams:                               # beams sit under everything, speckled
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(sc(bp), fill=255)
            over(img, np.asarray(m, dtype=np.float32) / 255 * speck, col["b"], .95)
        if sop > 0:
            m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(sc(shadow), fill=255)
            over(img, np.asarray(m, dtype=np.float32) / 255, col["s"], sop)
        over(img, doors_m, col["d"]); over(img, floors_m, col["f"])
        body, (cx, cy, r) = walker_shape(fx, fy)
        m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
        md.polygon(sc(body), fill=255); md.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=255)
        over(img, np.asarray(m, dtype=np.float32) / 255, col["w"])
        out = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((OW, OH), Image.BOX)
        if paper is not None:
            out = Image.fromarray((np.asarray(out, dtype=np.float32) * paper).clip(0, 255).astype(np.uint8))
        frames.append(out)
        print(f"\rframe {i + 1}/{n_hold0 + n_walk + n_hold1}", end="", flush=True)

    # one shared palette (taken from the busiest frame) keeps the static green from flickering between frames
    pal = frames[n_hold0 + n_walk - 1].quantize(colors=256, method=Image.MEDIANCUT, dither=Image.NONE)
    q = [f.quantize(palette=pal, dither=Image.NONE) for f in frames]
    q[0].save(a.out, save_all=True, append_images=q[1:], duration=round(1000 / a.fps), loop=0, optimize=False, disposal=1)
    print(f"\nwrote {a.out}  {OW}x{OH}, {len(q)} frames, {Path(a.out).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
