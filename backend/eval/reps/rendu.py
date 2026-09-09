"""Rend un clip avec le squelette ET le signal qui pilote le comptage, pour voir pourquoi
le compteur se trompe.

    cd backend
    uv run python eval/reps/rendu.py conventionnal_deadlift_14.mp4 --debut 4 --fin 15.5

En haut : le squelette, avec en surbrillance les trois reperes qui font l'angle d'extension
(epaule, hanche, genou du cote camera) — c'est lui qui sert de signal.
En bas : le signal sur toute la fenetre, les deux seuils d'hysteresis, le curseur, et un
trait rouge a chaque repetition comptee. Quand le squelette saute sur un corps immobile,
on voit le trait du bas sauter avec lui.

Deux passes : la pose d'abord (couteux), le dessin ensuite, pour ne pas garder les images
en memoire.
"""

import argparse
import os
import sys

import cv2
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)
sys.path.insert(0, ICI)

import pose_analysis as pa                                    # noqa: E402
import rep_detection as rd                                    # noqa: E402

BAS, HAUT = rd.BAS, rd.HAUT

DATA = os.path.abspath(os.path.join(BACKEND, "..", "data"))
SORTIE = os.path.join(BACKEND, "extracted_frames", "reps")
L = pa.L

# Les segments dessines : le squelette utile, sans le visage.
OS = [("l_sh", "r_sh"), ("l_sh", "l_hip"), ("r_sh", "r_hip"), ("l_hip", "r_hip"),
      ("l_sh", "l_el"), ("l_el", "l_wr"), ("r_sh", "r_el"), ("r_el", "r_wr"),
      ("l_hip", "l_kn"), ("l_kn", "l_an"), ("r_hip", "r_kn"), ("r_kn", "r_an")]

VERT, ORANGE, ROUGE, JAUNE, BLANC = (120, 255, 120), (0, 140, 255), (60, 60, 255), (0, 220, 255), (255, 255, 255)
BANDE = 190          # hauteur du graphe du bas, en pixels


def pose_fenetre(chemin, debut, fin):
    "Une passe MediaPipe sur toutes les frames de la fenetre. Rend (indices, landmarks, fps)."
    n, fps = pa._probe(chemin)
    a, b = int(debut * fps), min(n, int(fin * fps))
    frames, _ = pa._read_frames(chemin, range(a, b))
    poses = pa._detect(frames, fps)
    return {p["i"]: p for p in poses}, fps, a, b


def signal(poses, fps):
    "L'angle d'extension par frame, lisse comme le fait le compteur."
    ts, vs, idx = [], [], []
    for i in sorted(poses):
        f = poses[i]
        try:
            hip, knee = pa._joint_angles(f, pa._side_clip([f]))
        except Exception:
            continue
        ts.append(f["t"]); vs.append((hip + knee) / 2.0); idx.append(i)
    if not ts:
        return {}, None, None, None, None, None
    ts, vs = np.array(ts), np.array(vs)
    v = rd._lisse(vs, rd._cadence(ts))
    return dict(zip(idx, v)), float(np.percentile(v, 5)), float(np.percentile(v, 95)), ts, vs, idx


def verrous(sig, poses, lo, hi, ts=None, vs=None, idx=None):
    """Les frames ou la PRODUCTION declare une repetition.

    On appelle le coeur de rep_detection plutot que de recopier sa boucle : une copie a
    deja diverge une fois, et l'outil dessinait un algorithme qui n'existait plus.
    """
    if ts is None:
        return []
    # La video est rendue dense pour etre regardable, mais la production echantillonne a
    # FPS_ANALYSE : on lui donne le meme signal qu'elle aurait, sinon l'outil dessine des
    # repetitions que la production ne voit pas.
    grille = np.arange(ts[0], ts[-1] + 1e-9, 1.0 / rd.FPS_ANALYSE)
    pris = sorted({int(np.argmin(np.abs(ts - g))) for g in grille})
    ts, vs, idx = ts[pris], vs[pris], [idx[k] for k in pris]
    cands = rd.depuis_signal(ts, vs, float(ts[-1]))
    out = []
    for c in cands:                                  # ramener chaque lockout a sa frame
        k = int(np.argmin(np.abs(ts - c["lockout_s"])))
        out.append(idx[k])
    return out


def dessine(fr, f, w, h):
    "Squelette. Les trois reperes de l'angle sont plus gros : c'est eux qui font le signal."
    s = pa._side_clip([f])
    pt = lambda k: (int(f["im"][L[k], 0] * w), int(f["im"][L[k], 1] * h))
    ep = max(2, w // 480)
    for a, b in OS:
        cv2.line(fr, pt(a), pt(b), VERT, ep, cv2.LINE_AA)
    for k in {x for o in OS for x in o}:
        cv2.circle(fr, pt(k), max(3, w // 320), ORANGE, -1, cv2.LINE_AA)
    for k in (f"{s}_sh", f"{s}_hip", f"{s}_kn"):
        cv2.circle(fr, pt(k), max(7, w // 140), JAUNE, max(2, w // 500), cv2.LINE_AA)
    return s


def graphe(fr, sig, ordre, cur, lo, hi, verr, w, h, bas=BAS, haut=HAUT):
    "Le signal sur toute la fenetre, les seuils, le curseur et les reps comptees."
    y0 = h - BANDE
    cv2.rectangle(fr, (0, y0), (w, h), (18, 18, 20), -1)
    n = len(ordre)
    X = lambda k: int(k * (w - 20) / max(n - 1, 1)) + 10
    Y = lambda v: int(y0 + BANDE - 30 - (v - lo) / max(hi - lo, 1e-6) * (BANDE - 55))
    for seuil, lab in ((bas, "seuil bas"), (haut, "seuil haut")):
        y = Y(lo + seuil * (hi - lo))
        for x in range(10, w - 10, 22):
            cv2.line(fr, (x, y), (x + 11, y), (95, 95, 105), 1, cv2.LINE_AA)
        cv2.putText(fr, lab, (w - 150, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 150), 1, cv2.LINE_AA)
    pts = [(X(k), Y(sig[i])) for k, i in enumerate(ordre)]
    cv2.polylines(fr, [np.array(pts, np.int32)], False, (120, 220, 255), 2, cv2.LINE_AA)
    for k, i in enumerate(ordre):
        if i in verr:
            cv2.line(fr, (X(k), y0 + 8), (X(k), h - 8), ROUGE, 2, cv2.LINE_AA)
    cv2.line(fr, (X(cur), y0), (X(cur), h), BLANC, 2, cv2.LINE_AA)
    cv2.putText(fr, "angle d'extension hanche+genou (lisse)", (12, y0 + 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (170, 170, 180), 1, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("--debut", type=float, default=0.0)
    ap.add_argument("--fin", type=float, default=1e9)
    ap.add_argument("--vrai", type=int, default=None, help="nombre de reps reel, affiche en haut")
    a = ap.parse_args()

    chemin = os.path.join(DATA, a.clip)
    poses, fps, i0, i1 = pose_fenetre(chemin, a.debut, a.fin)
    sig, lo, hi, ts_s, vs_s, idx_s = signal(poses, fps)
    if not sig:
        print("aucune pose exploitable"); return
    ordre = sorted(sig)
    verr = set(verrous(sig, poses, lo, hi, ts_s, vs_s, idx_s))
    print(f"{len(ordre)} frames, {len(verr)} repetition(s) comptee(s) sur la fenetre")

    os.makedirs(SORTIE, exist_ok=True)
    dst = os.path.join(SORTIE, a.clip.replace(".mp4", "") + "__squelette.mp4")
    rot = pa._rotation(chemin)
    cap = cv2.VideoCapture(chemin)
    vw, compte_rep, i = None, 0, 0
    rang = {v: k for k, v in enumerate(ordre)}
    try:
        while True:
            ok, fr = cap.read()
            if not ok or i >= i1:
                break
            if i >= i0 and i in sig:
                if rot is not None:
                    fr = cv2.rotate(fr, rot)
                h, w = fr.shape[:2]
                if vw is None:
                    vw = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
                dessine(fr, poses[i], w, h)
                if i in verr:
                    compte_rep += 1
                graphe(fr, sig, ordre, rang[i], lo, hi, verr, w, h)
                bandeau = f"t={poses[i]['t']:5.2f}s   extension {sig[i]:5.1f} deg   comptees: {compte_rep}"
                if a.vrai is not None:
                    bandeau += f"   (vrai: {a.vrai})"
                cv2.rectangle(fr, (0, 0), (w, 46), (0, 0, 0), -1)
                cv2.putText(fr, bandeau, (12, 32), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8 * w / 900, BLANC, 2, cv2.LINE_AA)
                if i in verr:
                    cv2.rectangle(fr, (0, 0), (w - 1, h - 1), ROUGE, 12)
                vw.write(fr)
            i += 1
    finally:
        cap.release()
        if vw:
            vw.release()
    print("->", dst)


if __name__ == "__main__":
    main()
