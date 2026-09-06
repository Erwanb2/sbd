"""Dump des landmarks MediaPipe des 49 clips de `data/`, une fois pour toutes.

Le but est de decoupler le cout (une passe de pose par clip, ~40 s) de l'iteration sur
les features, qui devient gratuite : tout ce que MediaPipe a vu est sur le disque.

Deux passes par clip, comme en production :
  1. 30 frames uniformes -> `pose_analysis._phases` situe la repetition, `_cascade`
     donne la variante. C'est la configuration validee de la cascade, on n'y touche pas.
  2. passe dense (12 img/s) sur [decollage - 1 s, verrouillage + 2 s], la ou se jouent
     la tiree et la descente. Repli sur la fenetre de mouvement, puis sur tout le clip,
     quand la premiere passe ne trouve pas de repetition.

Sortie : un .npz par clip dans backend/extracted_frames/landmarks/ (ignore par git).
"""

from __future__ import annotations

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pose_analysis as pa                                          # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(RACINE, "data")
SORTIE = os.path.join(RACINE, "backend", "extracted_frames", "landmarks")

FPS_DENSE = 12.0
MAX_FRAMES = 110
AVANT_S, APRES_S = 1.0, 2.0


def _indices(n, fps, t0, t1):
    "Indices uniformes a FPS_DENSE sur [t0, t1], plafonnes a MAX_FRAMES."
    i0, i1 = max(0, int(t0 * fps)), min(n - 1, int(t1 * fps))
    if i1 <= i0:
        i0, i1 = 0, n - 1
    combien = int(round((i1 - i0) / fps * FPS_DENSE)) + 1
    combien = max(12, min(MAX_FRAMES, combien))
    return np.unique(np.linspace(i0, i1, combien).astype(int))


def dump(path: str, sortie: str) -> dict:
    t_debut = time.time()
    n, fps = pa._probe(path)
    if n <= 0:
        return {"ok": False, "raison": "video illisible"}

    idx = np.linspace(n * 0.05, n * 0.95, pa.N_CASCADE).astype(int)
    frames, fps = pa._read_frames(path, idx)
    poses = pa._detect(frames, fps) if len(frames) >= 6 else []
    if len(poses) < 6:
        return {"ok": False, "raison": "aucune pose exploitable"}

    casc = pa._cascade(poses) or {}
    ph = pa._phases(poses)
    origine = "phases"
    if ph is not None:
        t0 = poses[ph["liftoff"]]["t"] - AVANT_S
        t1 = poses[ph["lockout"]]["t"] + APRES_S
    else:
        fen = pa._fenetre_de_mouvement(path, n)
        origine = "mouvement" if fen else "clip_entier"
        t0, t1 = (fen[0] / fps, fen[1] / fps) if fen else (0.0, n / fps)

    dense_idx = _indices(n, fps, t0, t1)
    fr2, _ = pa._read_frames(path, dense_idx)
    poses2 = pa._detect(fr2, fps) if fr2 else []
    if len(poses2) < 8:
        return {"ok": False, "raison": "passe dense vide"}

    np.savez_compressed(
        sortie,
        t=np.array([p["t"] for p in poses2], dtype=np.float32),
        i=np.array([p["i"] for p in poses2], dtype=np.int32),
        im=np.stack([p["im"] for p in poses2]).astype(np.float32),
        wd=np.stack([p["wd"] for p in poses2]).astype(np.float32),
        meta=np.array([poses2[0]["w"], poses2[0]["h"], fps, n], dtype=np.float32),
        fenetre=np.array([t0, t1], dtype=np.float32),
        phases=np.array([poses[ph["liftoff"]]["t"] if ph else -1.0,
                         poses[ph["lockout"]]["t"] if ph else -1.0], dtype=np.float32),
        cascade=np.array([casc.get("largeur", np.nan), casc.get("confiance", np.nan),
                          casc.get("profondeur", np.nan)], dtype=np.float32),
        variante=np.array(casc.get("variante", "?")),
        origine=np.array(origine),
    )
    return {"ok": True, "frames": len(poses2), "origine": origine,
            "variante": casc.get("variante"), "s": round(time.time() - t_debut, 1)}


def main():
    os.makedirs(SORTIE, exist_ok=True)
    clips = sorted(f for f in os.listdir(DATA) if f.lower().endswith(".mp4"))
    t0 = time.time()
    for k, clip in enumerate(clips, 1):
        cible = os.path.join(SORTIE, clip + ".npz")
        if os.path.exists(cible) and "--force" not in sys.argv:
            print(f"[{k:2d}/{len(clips)}] {clip[:48]:48s} deja fait", flush=True)
            continue
        try:
            r = dump(os.path.join(DATA, clip), cible)
        except Exception as exc:
            r = {"ok": False, "raison": f"{type(exc).__name__}: {exc}"}
        print(f"[{k:2d}/{len(clips)}] {clip[:48]:48s} {r}", flush=True)
    print(f"total {round(time.time() - t0, 1)} s", flush=True)


if __name__ == "__main__":
    main()
