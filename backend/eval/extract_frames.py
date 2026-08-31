"""
Frame extraction for reviewing lifting videos by hand.

Used to build ground_truth.json, and useful for spot-checking any label in it.

    # contact sheet over a whole clip, to find where the rep is
    uv run --with opencv-python-headless,pillow,numpy python extract_frames.py \
        ../../data/pr_160.mp4

    # dense sheet over one rep
    uv run --with opencv-python-headless,pillow,numpy python extract_frames.py \
        ../../data/pr_160.mp4 --start 2.0 --end 7.8 --n 16

    # big lower-body crop, to settle a sumo-vs-conventional stance call
    uv run --with opencv-python-headless,pillow,numpy python extract_frames.py \
        ../../data/oscar_sumo.mp4 --at 5.6 6.9 8.2 --crop 0.45

The motion profile printed by --motion is the same idea as sampling frames
from the lift rather than uniformly across the clip: several clips in data/
put the actual rep in their last 20%, where uniform sampling barely looks.
"""

import argparse
import math
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw


def probe(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()
    return fps, n, (n / fps if fps > 0 else 0.0)


def grab(path, times):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    out = []
    for t in times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(t * fps)))
        ok, frame = cap.read()
        if ok:
            out.append((t, frame))
    cap.release()
    return out


def motion_profile(path, step=3, width=160):
    """Mean absolute frame difference over time. Peaks are where the bar moves."""
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    prev, ts, vals, i = None, [], [], 0
    while cap.grab():
        if i % step == 0:
            ok, frame = cap.retrieve()
            if ok:
                g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                g = cv2.resize(g, (width, max(int(g.shape[0] * width / g.shape[1]), 1)))
                if prev is not None:
                    ts.append(i / fps)
                    vals.append(float(np.mean(cv2.absdiff(g, prev))))
                prev = g
        i += 1
    cap.release()
    return np.array(ts), np.array(vals)


def print_sparkline(ts, vals, cols=60):
    blocks = " ▁▂▃▄▅▆▇█"
    if len(vals) == 0:
        print("  (no frames)")
        return
    idx = np.linspace(0, len(vals) - 1, cols).astype(int)
    r = vals[idx]
    norm = (r - r.min()) / (r.max() - r.min() + 1e-9)
    print("  |" + "".join(blocks[min(int(x * 8), 8)] for x in norm) + "|")
    print("  " + "".join(f"{ts[idx[i]]:<10.1f}" for i in range(0, cols, 10)))


def contact_sheet(frames, out_path, cols=4, tile=340, crop_top=0.0):
    tiles = []
    for t, frame in frames:
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if crop_top > 0:
            img = img.crop((0, int(img.height * crop_top), img.width, img.height))
        img.thumbnail((tile, tile))
        tiles.append((f"{t:.2f}s", img))

    tw = max(im.width for _, im in tiles)
    th = max(im.height for _, im in tiles)
    rows = math.ceil(len(tiles) / cols)
    bar = 26
    canvas = Image.new("RGB", (cols * tw, rows * (th + bar)), (20, 20, 22))
    draw = ImageDraw.Draw(canvas)
    for i, (label, im) in enumerate(tiles):
        r, c = divmod(i, cols)
        x, y = c * tw, r * (th + bar)
        canvas.paste(im, (x + (tw - im.width) // 2, y + bar))
        draw.text((x + 6, y + 7), label, fill=(255, 210, 60))
    canvas.save(out_path, quality=90)
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--start", type=float, help="window start in seconds")
    ap.add_argument("--end", type=float, help="window end in seconds")
    ap.add_argument("--at", type=float, nargs="+", help="explicit timestamps")
    ap.add_argument("--n", type=int, default=12, help="frames in the sheet")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--tile", type=int, default=340, help="max px per tile")
    ap.add_argument("--crop", type=float, default=0.0,
                    help="drop this fraction off the top of each frame (e.g. 0.45 for feet)")
    ap.add_argument("--motion", action="store_true", help="print a motion sparkline and exit")
    ap.add_argument("-o", "--out", help="output jpg (default: alongside the video)")
    args = ap.parse_args()

    fps, n, dur = probe(args.video)
    print(f"{os.path.basename(args.video)}  {dur:.1f}s  {fps:.1f}fps  {n} frames")

    if args.motion:
        print_sparkline(*motion_profile(args.video))
        return

    if args.at:
        times = args.at
    else:
        a = args.start if args.start is not None else dur * 0.03
        b = args.end if args.end is not None else dur * 0.97
        times = list(np.linspace(a, b, args.n))

    frames = grab(args.video, times)
    if not frames:
        raise SystemExit("could not read any frame")

    out = args.out or os.path.splitext(args.video)[0] + "_sheet.jpg"
    contact_sheet(frames, out, cols=args.cols, tile=args.tile, crop_top=args.crop)
    print(f"-> {out}  ({len(frames)} frames)")


if __name__ == "__main__":
    main()
