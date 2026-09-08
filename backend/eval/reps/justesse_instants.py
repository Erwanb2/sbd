"""A quel point les instants calcules tombent-ils sur les vrais verrouillages ?

    cd backend && uv run python eval/reps/justesse_instants.py

Deux instants differents sont compares aux reperes humains :

  `lockout_s` du candidat   ce que rend rep_detection : le premier echantillon qui
                            franchit 60 % de l'amplitude du clip. C'est un DECLENCHEUR,
                            pas un verrouillage — le nom du champ est trompeur.
  `_phases`                 le verrouillage que pose_analysis situe DANS la fenetre,
                            et sur lequel toutes les mesures sont accrochees.
"""
import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)

import pose_analysis as pa                                     # noqa: E402
from rappel_instants import candidats_depuis_cache             # noqa: E402


def phases_sur_cache(sig, debut, fin):
    """Rejoue pose_analysis._phases sur la fenetre d'un candidat. Rend (decollage, lockout)."""
    pts = [p for p in sig["points"]
           if p.get("hip_deg") is not None and p.get("knee_deg") is not None
           and debut <= p["t"] <= fin]
    if len(pts) < 6:
        return None
    ts = np.array([p["t"] for p in pts])
    ext = np.array([(p["hip_deg"] + p["knee_deg"]) / 2 for p in pts])
    if len(ext) >= 5:                          # filtre median, comme _phases
        ext = np.array([float(np.median(ext[max(0, i - 1):i + 2])) for i in range(len(ext))])
    best, lo, lk, imin = -1.0, 0, 0, 0
    for j in range(1, len(ext)):
        if ext[j] - ext[imin] > best:
            best, lo, lk = float(ext[j] - ext[imin]), imin, j
        if ext[j] < ext[imin]:
            imin = j
    if best < 12.0 or lk <= lo:
        return None
    apres = ext[lo + 1:]
    haut = float(np.max(apres))
    lk = lo + 1 + int(np.argmax(apres >= haut - 3.0))
    bas = float(np.min(ext[lo:lk + 1]))                        # depart par un NIVEAU
    seuil = bas + 0.10 * (float(ext[lk]) - bas)
    en_bas = [i for i in range(lo, lk) if ext[i] <= seuil]
    lo = en_bas[-1] if en_bas else lo
    return float(ts[lo]), float(ts[lk])


def main():
    vt = json.load(open(os.path.join(ICI, "verite_terrain.json"), encoding="utf-8"))["clips"]
    annotes = {k: v["verrous"] for k, v in vt.items() if v.get("verrous")}

    for nom, f in (("6 im/s", "signaux_6fps.json"), ("15 im/s", "signaux_15fps.json")):
        chemin = os.path.join(ICI, f)
        if not os.path.exists(chemin):
            continue
        cache = json.load(open(chemin, encoding="utf-8"))
        ecarts_decl, ecarts_ph = [], []
        for clip, reels in annotes.items():
            if clip not in cache:
                continue
            for c in candidats_depuis_cache(cache[clip]):
                dedans = [t for t in reels if c["debut_s"] <= t <= c["fin_s"]]
                if not dedans:
                    continue
                vrai = min(dedans, key=lambda t: abs(t - c["lockout_s"]))
                ecarts_decl.append(c["lockout_s"] - vrai)
                ph = phases_sur_cache(cache[clip], c["debut_s"], c["fin_s"])
                if ph:
                    ecarts_ph.append(ph[1] - vrai)

        print(f"=== {nom}   ({len(ecarts_decl)} repetitions couvertes)")
        for etiquette, e in (("declencheur du candidat", ecarts_decl), ("_phases", ecarts_ph)):
            if not e:
                continue
            e = np.array(e)
            print(f"    {etiquette:24s} biais {np.median(e):+.2f}s | "
                  f"ecart absolu median {np.median(np.abs(e)):.2f}s | "
                  f"en avance {float(np.mean(e < 0)):.0%} du temps")
        print()


if __name__ == "__main__":
    main()
