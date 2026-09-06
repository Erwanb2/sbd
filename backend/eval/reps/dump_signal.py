"""Une passe MediaPipe dense sur chaque clip de data/ -> un signal temporel par clip.

    cd backend
    uv run python eval/reps/dump_signal.py [--fps 6] [--clip nom.mp4]

Le but est de payer la pose UNE fois. Le comptage de reps se met au point ensuite
sur le JSON, sans repasser la video (compte_reps.py).

Par frame echantillonnee on garde ce qui peut porter une repetition :
  hip_deg / knee_deg   angles du cote camera, en degres (invariants a la distance)
  hip_y / wri_y / sh_y  hauteurs image, normalisees par la longueur du tronc du clip
  vis_*                 visibilite, pour savoir quand ne pas croire le reste
"""

import argparse
import json
import os
import sys
import time

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)

import pose_analysis as pa                                     # noqa: E402

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
SORTIE = os.path.join(ICI, "signaux.json")
L = pa.L


def _ang(a, b, c):
    return pa._angle(a, b, c)


def signal_clip(chemin, fps_cible=6.0):
    n, fps = pa._probe(chemin)
    if not n or not fps:
        return None
    # fps_cible <= 0 : toutes les frames. C'est le mode pour lequel le running_mode VIDEO
    # de MediaPipe est fait — il suit les reperes d'une frame a la suivante, et sauter des
    # images le fait travailler a contre-emploi.
    pas = 1 if fps_cible <= 0 else max(1, int(round(fps / fps_cible)))
    idx = list(range(0, n, pas))
    frames, _ = pa._read_frames(chemin, idx)
    if not frames:
        return None
    poses = pa._detect(frames, fps)
    if len(poses) < 6:
        return None

    s = pa._side_clip(poses)
    # Longueur de tronc de reference : mediane sur le clip. Normalise les hauteurs
    # image, qui dependent sinon du cadrage et du zoom.
    troncs = []
    for f in poses:
        sh = (pa._px(f, "l_sh") + pa._px(f, "r_sh")) / 2
        hp = (pa._px(f, "l_hip") + pa._px(f, "r_hip")) / 2
        troncs.append(float(np.linalg.norm(sh - hp)))
    tronc = float(np.median(troncs)) or 1e-6

    pts = []
    for f in poses:
        im = f["im"]
        try:
            hip_deg, knee_deg = pa._joint_angles(f, s)
        except Exception:
            continue
        # En PIXELS, comme `tronc` : les y des landmarks sont normalises 0-1, les diviser
        # tels quels par une longueur en pixels donne un signal cinquante fois trop plat,
        # et un garde-fou d'amplitude qui rejette alors tous les clips.
        h = f["h"]
        hy = float((im[L["l_hip"], 1] + im[L["r_hip"], 1]) / 2 * h)
        sy = float((im[L["l_sh"], 1] + im[L["r_sh"], 1]) / 2 * h)
        wy = float((im[L["l_wr"], 1] + im[L["r_wr"], 1]) / 2 * h)
        ky = float((im[L["l_kn"], 1] + im[L["r_kn"], 1]) / 2 * h)
        vis = lambda k: float(im[L[k], 3])
        pts.append(dict(
            t=round(f["t"], 3),
            hip_deg=round(hip_deg, 2), knee_deg=round(knee_deg, 2),
            hip_y=round(hy / tronc, 4), sh_y=round(sy / tronc, 4),
            wri_y=round(wy / tronc, 4), kn_y=round(ky / tronc, 4),
            vis_legs=round(min(vis("l_kn"), vis("r_kn"), vis("l_an"), vis("r_an")), 3),
            vis_near=round(float(np.mean([vis(f"{s}_sh"), vis(f"{s}_hip"),
                                          vis(f"{s}_kn"), vis(f"{s}_an")])), 3),
        ))
    return dict(fps=round(fps, 3), n_frames=n, duree_s=round(n / fps, 2),
                cote=s, tronc=round(tronc, 4), fps_echantillon=round(fps / pas, 2),
                points=pts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=float, default=6.0,
                    help="cadence d'echantillonnage ; 0 = toutes les frames (cadence native)")
    ap.add_argument("--clip", default=None)
    ap.add_argument("--sortie", default=SORTIE)
    a = ap.parse_args()

    clips = ([a.clip] if a.clip else sorted(f for f in os.listdir(DATA) if f.endswith(".mp4")))
    out = {}
    if os.path.exists(a.sortie):
        out = json.load(open(a.sortie))
    for i, c in enumerate(clips, 1):
        t0 = time.time()
        try:
            r = signal_clip(os.path.join(DATA, c), a.fps)
        except Exception as e:
            r = None
            print(f"[{i}/{len(clips)}] {c}: ERREUR {e}", flush=True)
        if r:
            out[c] = r
            print(f"[{i}/{len(clips)}] {c}: {len(r['points'])} pts, "
                  f"{r['duree_s']}s -> {time.time()-t0:.1f}s", flush=True)
        json.dump(out, open(a.sortie, "w"), indent=1)


if __name__ == "__main__":
    main()
