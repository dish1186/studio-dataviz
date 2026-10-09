"""Assemble captured PNG frames into a seamlessly looping GIF (and, for transparent frames, an animated WebP).

The last XF frames are crossfaded into the first XF, and those first XF are then dropped, so the loop has no jump
(puffs and the water's wave don't repeat on their own). One shared palette keeps the static parts from flickering.

Transparent frames: everything is cropped to the artwork, and since GIF transparency is on/off only, partial alpha
(the fading steam, antialiased edges) is turned into a fixed 8x8 ordered stipple, which stays still between frames.
The WebP keeps the full, smooth alpha.

    python3 frames_to_gif.py FRAME_DIR OUT.gif [--fps 20] [--xfade 20] [--pad 12]

Frames come from a browser capture of index.html with a stepped clock (the Plate I hero and the outro pot).
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image

BAYER = np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                  [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                  [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64 + 1 / 128


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames"); ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--xfade", type=int, default=20, help="frames of crossfade at the loop seam")
    ap.add_argument("--pad", type=int, default=12, help="px kept around the artwork when cropping transparent frames")
    a = ap.parse_args()

    fr = [Image.open(p) for p in sorted(Path(a.frames).glob("*.png"))]
    alpha = fr[0].mode == "RGBA" and any(f.getextrema()[3][0] < 255 for f in fr[:3])
    fr = [f.convert("RGBA" if alpha else "RGB") for f in fr]
    X = a.xfade
    head, body = fr[:X], fr[X:]
    for i in range(X):                               # tail fades into the head, which then plays from frame X on
        w = (i + 1) / (X + 1)
        body[len(body) - X + i] = Image.blend(body[len(body) - X + i], head[i], w)

    if alpha:                                        # crop to everything that is ever drawn
        boxes = [f.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox() for f in body]
        boxes = [b for b in boxes if b]
        W0, H0 = body[0].size
        box = (max(0, min(b[0] for b in boxes) - a.pad), max(0, min(b[1] for b in boxes) - a.pad),
               min(W0, max(b[2] for b in boxes) + a.pad), min(H0, max(b[3] for b in boxes) + a.pad))
        body = [f.crop(box) for f in body]
    w, h = body[0].size

    # palette from a spread of frames tiled together, so every frame's colours are in it
    picks = body[::max(1, len(body) // 6)][:6]
    sheet = Image.new("RGB", (w // 3 * len(picks), h // 3))
    for i, p in enumerate(picks):
        sheet.paste(p.convert("RGB").resize((w // 3, h // 3), Image.BOX), (i * (w // 3), 0))
    pal = sheet.quantize(colors=255, method=Image.MEDIANCUT, dither=Image.NONE)

    q = []
    thr = np.tile(BAYER, (h // 8 + 1, w // 8 + 1))[:h, :w]
    for f in body:
        p = f.convert("RGB").quantize(palette=pal, dither=Image.NONE)
        if alpha:
            idx = np.asarray(p).copy()
            idx[np.asarray(f.getchannel("A"), dtype=np.float32) / 255 < thr] = 255   # index 255 = transparent
            p = Image.fromarray(idx, "P"); p.putpalette(pal.getpalette()[:765] + [0, 0, 0])
        q.append(p)
    extra = dict(transparency=255, disposal=2) if alpha else dict(disposal=1)
    q[0].save(a.out, save_all=True, append_images=q[1:], duration=round(1000 / a.fps), loop=0, optimize=False, **extra)
    print(f"wrote {a.out}  {w}x{h}, {len(q)} frames ({len(q) / a.fps:.1f} s), {Path(a.out).stat().st_size / 1e6:.1f} MB")

    if alpha:                                        # smooth-alpha version for places that take WebP
        wp = str(Path(a.out).with_suffix(".webp"))
        body[0].save(wp, save_all=True, append_images=body[1:], duration=round(1000 / a.fps), loop=0, lossless=False, quality=92, alpha_quality=100, method=4)
        print(f"wrote {wp}  {Path(wp).stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
