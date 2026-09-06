"""Compare la passe de pose a 6 fps et a pleine cadence, sur les memes clips.

    cd backend
    uv run python eval/reps/effet_cadence.py

Deux mesures, volontairement separees :

1. **Le bruit de la pose**, independamment du comptage. Sur des fenetres ou le lifter est
   immobile (variation lente du signal lisse), on mesure l'ecart-type de l'angle
   d'extension apres le meme filtre de 0,5 s. Si le mode VIDEO de MediaPipe travaillait
   a contre-emploi a 6 fps, ce bruit doit baisser a pleine cadence.

2. **Le comptage**, avec exactement le meme compteur : ses constantes sont en secondes,
   donc changer la cadence ne change pas sa nervosite. L'ecart mesure la pose, pas le filtre.
"""

import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

from compte_reps import compte, serie, _lisse, _cadence   # noqa: E402

A = os.path.join(ICI, "signaux_6fps.json")
B = os.path.join(ICI, "signaux_full.json")
VT = os.path.join(ICI, "verite_terrain.json")
SIGS = ("ext", "wri", "hip", "post", "med")


def bruit(points):
    """Ecart-type residuel de l'angle d'extension la ou le mouvement est lent.

    On prend les fenetres d'une seconde ou le signal lisse varie de moins de 8 degres —
    le lifter y est immobile — et on regarde ce qui reste comme dispersion. C'est du bruit
    de suivi : un corps immobile n'a pas de raison de bouger de dix degres.
    """
    ts, vs = serie(points, "ext")
    if len(ts) < 20:
        return None
    fps = _cadence(ts)
    liss = _lisse(vs, fps)
    k = max(3, int(round(1.0 * fps)))
    res = []
    for i in range(0, len(vs) - k, max(1, k // 2)):
        fen = liss[i:i + k]
        if float(np.ptp(fen)) < 8.0:                    # fenetre immobile
            res.append(float(np.std(vs[i:i + k])))
    return float(np.median(res)) if len(res) >= 3 else None


def main():
    a, b = json.load(open(A)), json.load(open(B))
    vt = json.load(open(VT))["clips"]
    communs = sorted(set(a) & set(b))
    print(f"{len(communs)} clips dans les deux passes\n")

    na, nb = [], []
    for c in communs:
        x, y = bruit(a[c]["points"]), bruit(b[c]["points"])
        if x is not None and y is not None:
            na.append(x)
            nb.append(y)
    print("--- 1. bruit de suivi sur corps immobile (ecart-type de l'extension, degres) ---")
    print(f"   6 fps          mediane {np.median(na):5.2f}   sur {len(na)} clips")
    print(f"   pleine cadence mediane {np.median(nb):5.2f}")
    mieux = sum(1 for x, y in zip(na, nb) if y < x)
    print(f"   moins bruite a pleine cadence sur {mieux}/{len(na)} clips")

    print("\n--- 2. comptage, meme compteur, meme verite terrain ---")
    print(f"{'signal':6} {'6 fps':>16} {'pleine cadence':>18}")
    for s in SIGS:
        r = {}
        for nom, d in (("6", a), ("f", b)):
            ex = pm = tot = 0
            for c in communs:
                ref = vt.get(c)
                if not ref or ref.get("mouvement") == "bench" or ref["n"] == "na":
                    continue
                n = compte(d[c]["points"], s)
                ex += n == ref["n"]
                pm += abs(n - ref["n"]) <= 1
                tot += 1
            r[nom] = (ex, pm, tot)
        e6, p6, t = r["6"]
        ef, pf, _ = r["f"]
        print(f"{s:6} {e6:3}/{t} ({100*e6/t:3.0f}%) +/-1 {100*p6/t:3.0f}%"
              f"   {ef:3}/{t} ({100*ef/t:3.0f}%) +/-1 {100*pf/t:3.0f}%")


if __name__ == "__main__":
    main()
