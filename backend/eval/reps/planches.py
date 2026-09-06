"""Planches de frames a cadence fixe, pour compter les reps a l'oeil.

    cd backend
    uv run python eval/reps/planches.py [--pas 0.5] [--clip nom.mp4] [--debut 0 --fin 10]

Sortie : extracted_frames/reps/<clip>__NN.jpg, horodatees.

Rendu maison plutot que extract_frames.contact_sheet : la moitie des clips de data/ sont
en portrait, et une vignette bornee par son plus grand cote y devient minuscule. Ici la
HAUTEUR est fixee — c'est elle qui porte l'information debout / plie.

Passe par pose_analysis._read_frames : deux clips de data/ ont un flag de rotation mp4
que cv2 ignore, et sortiraient couches.
"""

import argparse
import math
import os
import sys

import cv2
from PIL import Image, ImageDraw

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)

import pose_analysis as pa                          # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
SORTIE = os.path.join(BACKEND, "extracted_frames", "reps")


def planche(lot, chemin, cols, haut):
    vignettes = []
    for t, fr in lot:
        img = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        larg = max(1, min(int(img.width * haut / img.height), haut * 2))
        vignettes.append((f"{t:.1f}s", img.resize((larg, haut))))
    tw = max(im.width for _, im in vignettes)
    bande = 22
    lignes = math.ceil(len(vignettes) / cols)
    toile = Image.new("RGB", (cols * tw, lignes * (haut + bande)), (18, 18, 20))
    d = ImageDraw.Draw(toile)
    for i, (lab, im) in enumerate(vignettes):
        r, c = divmod(i, cols)
        x, y = c * tw, r * (haut + bande)
        toile.paste(im, (x + (tw - im.width) // 2, y + bande))
        d.text((x + 5, y + 6), lab, fill=(255, 210, 60))
    toile.save(chemin, quality=88)


def planches(clip, pas=0.5, par_planche=32, haut=300, cols=8, debut=None, fin=None, suffixe=""):
    chemin = os.path.join(DATA, clip)
    n, fps = pa._probe(chemin)
    if not n or not fps:
        return []
    a = int((debut or 0) * fps)
    b = int(fin * fps) if fin else n
    idx = list(range(a, b, max(1, int(round(fps * pas)))))
    frames, _ = pa._read_frames(chemin, idx)
    # Colonnes choisies sur le format du clip : une planche d'environ 1500 px de large
    # reste lisible une fois affichee, en portrait comme en paysage. A 8 colonnes en dur,
    # les clips paysage donnent des vignettes ou l'on ne distingue plus debout de plie.
    if cols is None:
        h0, w0 = frames[0][2].shape[:2]
        larg = min(int(w0 * haut / h0), haut * 2)
        cols = max(3, min(8, round(1500 / larg)))
    if par_planche is None:
        par_planche = cols * 5
    base = os.path.join(SORTIE, clip.replace(".mp4", "").replace(" ", "_") + suffixe)
    out = []
    for k in range(0, len(frames), par_planche):
        lot = [(t, f) for _, t, f in frames[k:k + par_planche]]
        p = f"{base}__{k // par_planche:02d}.jpg"
        planche(lot, p, cols, haut)
        out.append(p)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pas", type=float, default=0.5)
    ap.add_argument("--clip", default=None)
    ap.add_argument("--haut", type=int, default=300)
    ap.add_argument("--cols", type=int, default=None)
    ap.add_argument("--par-planche", type=int, default=None)
    ap.add_argument("--debut", type=float, default=None)
    ap.add_argument("--fin", type=float, default=None)
    ap.add_argument("--suffixe", default="")
    a = ap.parse_args()
    os.makedirs(SORTIE, exist_ok=True)
    clips = ([a.clip] if a.clip else sorted(f for f in os.listdir(DATA) if f.endswith(".mp4")))
    for c in clips:
        ps = planches(c, a.pas, a.par_planche, a.haut, a.cols, a.debut, a.fin, a.suffixe)
        print(f"{c}: {len(ps)} planche(s)", flush=True)
