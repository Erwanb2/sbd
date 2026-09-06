"""Prepare de quoi relire chaque clip a la main : planches de frames + mesures de pose.

    cd backend
    uv run python eval/scorer/prepare_frames.py

Pour chaque clip de data/ :
  * extracted_frames/scorer/<clip>__vue.jpg    12 frames sur tout le clip (ou est la tiree)
  * extracted_frames/scorer/<clip>__rep.jpg    16 frames sur la repetition elle-meme
  * eval/scorer/pose_measures.json             cascade sumo/conventionnel + cinematique

La fenetre de la repetition vient des phases de pose_analysis (decollage -> verrouillage)
quand elles sont trouvees, du profil de mouvement sinon : un echantillonnage uniforme
rate la tiree sur les clips ou le lifter tourne autour de la barre pendant 30 s.
Les frames passent par pose_analysis._read_frames, qui applique la rotation du mp4 —
sans quoi deux clips de data/ sortent couches.
"""

import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)
sys.path.insert(0, os.path.join(BACKEND, "eval"))

import pose_analysis                                   # noqa: E402
from extract_frames import contact_sheet               # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
SORTIE_IMG = os.path.join(BACKEND, "extracted_frames", "scorer")
SORTIE_JSON = os.path.join(ICI, "pose_measures.json")


def planche(chemin, temps, sortie, tile):
    fps = pose_analysis._probe(chemin)[1] or 30.0
    idx = [int(round(t * fps)) for t in temps]
    frames, _ = pose_analysis._read_frames(chemin, idx)
    if not frames:
        return None
    return contact_sheet([(t, f) for _, t, f in frames], sortie, cols=4, tile=tile)


def fenetre(chemin, mesures, duree, n):
    """(debut, fin) en secondes de la repetition."""
    ph = ((mesures.get("kinematics") or {}).get("_phases")) or {}
    if ph.get("liftoff_s") is not None and ph.get("lockout_s") is not None:
        return max(0.0, ph["liftoff_s"] - 0.8), min(duree, ph["lockout_s"] + 1.6)
    f = pose_analysis._fenetre_de_mouvement(chemin, n)
    if f:
        fps = pose_analysis._probe(chemin)[1] or 30.0
        a, b = f[0] / fps, f[1] / fps
        # Sur un clip de 40 s la fenetre de mouvement fait souvent 25 s : 16 images
        # espacees de 1,7 s ne montrent aucune repetition. On se recentre sur son milieu.
        if b - a > 8.0:
            centre = (a + b) / 2
            a, b = max(0.0, centre - 3.0), min(duree, centre + 3.0)
        return a, b
    return duree * 0.03, duree * 0.97


def sur_mesure(args):
    """Planche sur une fenetre choisie a la main, quand le reperage automatique se trompe.

        uv run python eval/scorer/prepare_frames.py --clip x.mp4 --start 14.5 --end 19.5
    """
    chemin = os.path.join(DATA, args.clip)
    sortie = os.path.join(SORTIE_IMG, args.clip.replace(".mp4", "") + "__rep2.jpg")
    planche(chemin, list(np.linspace(args.start, args.end, args.n)), sortie, 330)
    print(f"-> {sortie}  ({args.start}-{args.end}s)")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip")
    ap.add_argument("--start", type=float)
    ap.add_argument("--end", type=float)
    ap.add_argument("--n", type=int, default=16)
    args = ap.parse_args()
    os.makedirs(SORTIE_IMG, exist_ok=True)
    if args.clip:
        return sur_mesure(args)
    try:
        with open(SORTIE_JSON, encoding="utf-8") as f:
            mesures_tous = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        mesures_tous = {}

    clips = sorted(f for f in os.listdir(DATA) if f.lower().endswith(".mp4"))
    for k, clip in enumerate(clips, 1):
        chemin = os.path.join(DATA, clip)
        base = os.path.join(SORTIE_IMG, clip.replace(".mp4", ""))
        vue, rep = base + "__vue.jpg", base + "__rep.jpg"
        if os.path.exists(vue) and os.path.exists(rep) and clip in mesures_tous:
            print(f"[{k}/{len(clips)}] {clip} — deja fait")
            continue
        try:
            n, fps = pose_analysis._probe(chemin)
            duree = n / fps if fps else 0.0
            mesures = pose_analysis.analyse(chemin, with_kinematics=True)
            kin = mesures.get("kinematics") or {}
            mesures_tous[clip] = {
                "duree_s": round(duree, 1),
                "variante_pose": mesures.get("variante"),
                "regle": mesures.get("regle"),
                "confiance": mesures.get("confiance"),
                "largeur": mesures.get("largeur"),
                "profondeur": mesures.get("profondeur"),
                "kinematics": kin or None,
                "raison": mesures.get("raison"),
            }
            planche(chemin, list(np.linspace(duree * 0.03, duree * 0.97, 12)), vue, 300)
            a, b = fenetre(chemin, mesures, duree, n)
            planche(chemin, list(np.linspace(a, b, 16)), rep, 330)
            print(f"[{k}/{len(clips)}] {clip} — {duree:.1f}s — "
                  f"{mesures.get('variante')} — rep {a:.1f}-{b:.1f}s")
        except Exception as exc:
            mesures_tous[clip] = {"erreur": f"{type(exc).__name__}: {exc}"}
            print(f"[{k}/{len(clips)}] {clip} — ECHEC : {exc}")
        with open(SORTIE_JSON, "w", encoding="utf-8") as f:
            json.dump(mesures_tous, f, indent=2, ensure_ascii=False)
    print(f"\nplanches -> {SORTIE_IMG}\nmesures  -> {SORTIE_JSON}")


if __name__ == "__main__":
    main()
