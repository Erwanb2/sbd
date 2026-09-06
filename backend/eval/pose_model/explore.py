"""Lecture descriptive : quelle mesure bouge avec quelle note, et est-ce un artefact ?

Complement de `fit.py`, qui dit si un modele predit ; ici on regarde si une mesure
*correle*, ce qui est plus faible mais interpretable. Le controle par variante est le
garde-fou principal : `largeur` ou `profondeur` separent sumo et conventionnel, et les
clips sumo du jeu viennent surtout d'Instagram (lifters forts, bien filmes, bien notes).
Une correlation qui disparait a l'interieur de chaque variante ne mesure pas la
technique, elle mesure la provenance du clip.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
from scipy.stats import spearmanr

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import fit                                                          # noqa: E402


def rho(xs, ys):
    ok = [(x, y) for x, y in zip(xs, ys) if x is not None and not np.isnan(x)]
    if len(ok) < 8 or len({x for x, _ in ok}) < 4:
        return None
    r, p = spearmanr([x for x, _ in ok], [y for _, y in ok])
    return (float(r), float(p), len(ok))


def niveaux(H):
    """Note moyenne du clip, toutes rubriques confondues : son « niveau ».

    L'humain note un bon lifter bon partout : les huit criteres d'un clip sont fortement
    lies entre eux. Une mesure correlee a ce niveau general correlera mecaniquement avec
    chaque critere pris un a un, sans rien dire du defaut vise. C'est le halo, et c'est
    ce qui explique qu'une seule feature — la vitesse de descente — arrive en tete de
    huit criteres sur onze.
    """
    out = {}
    for clip, h in H.items():
        v = [s for s in (h.get("scores") or {}).values() if s in (1, 2, 3)]
        if v:
            out[clip] = float(np.mean(v))
    return out


def main():
    F = json.load(open(os.path.join(ICI, "features.json")))
    H = json.load(open(os.path.join(fit.SCORER, "human_labels.json")))
    NIV = niveaux(H)
    toutes = sorted({k for v in F.values() for k in v} - fit.EXCLUES)

    # 1. le niveau general du clip est-il lisible dans la pose ?
    noms, lignes, _ = fit.jeu("starting_position", F, H, False, True)
    niv = np.array([NIV[n] for n in noms])
    print(f"== NIVEAU GENERAL DU CLIP (moyenne des criteres humains)  n={len(niv)}")
    cl = []
    for f in toutes:
        r = rho([l.get(f) for l in lignes], niv)
        if r:
            cl.append((abs(r[0]), r[0], r[1], r[2], f))
    for _, r, p, n, f in sorted(cl, reverse=True)[:6]:
        print(f"  {'*' if p < 0.05 else ' '} {f:26s} rho={r:+.2f} p={p:.3f} n={n}")
    print()

    for crit, guide in fit.GUIDE.items():
        noms, lignes, y = fit.jeu(crit, F, H, False, True)
        if len(y) < 12:
            continue
        niv = np.array([NIV[n] for n in noms])
        res = []
        for f in toutes:
            xs = [l.get(f) for l in lignes]
            r = rho(xs, y)
            rs = rho(xs, y - niv)          # part propre au critere, halo retire
            if r and rs:
                res.append((abs(rs[0]), r[0], r[1], r[2], f, f in guide, rs[0], rs[1],
                            (rho(xs, niv) or (float("nan"),))[0]))
        res.sort(reverse=True)
        print(f"== {crit}  n={len(y)}   (trie sur la correlation HORS halo)")
        for _, r, p, n, f, dans_guide, rs, ps, rn in res[:4]:
            marque = "*" if p < 0.05 else " "
            # meme correlation a l'interieur de chaque variante : si elle s'effondre,
            # la mesure separait sumo et conventionnel, pas les bonnes et mauvaises
            # executions
            parts = []
            for v in ("conventional", "sumo"):
                idx = [i for i, l in enumerate(lignes) if l.get("variante_pose") == v]
                rr = rho([lignes[i].get(f) for i in idx], y[idx])
                parts.append(f"{v[:4]} {rr[0]:+.2f} (n={rr[2]})" if rr else f"{v[:4]} n/a")
            marque = "*" if ps < 0.05 else " "
            print(f"  {marque} {'G' if dans_guide else ' '} {f:26s} hors halo {rs:+.2f} "
                  f"(p={ps:.3f}) | brut {r:+.2f} | halo {rn:+.2f} | n={n}   "
                  + "  ".join(parts))
        print()


if __name__ == "__main__":
    main()
