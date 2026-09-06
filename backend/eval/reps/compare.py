"""Confronte le comptage MediaPipe a la verite terrain comptee a la main.

    cd backend
    uv run python eval/reps/compare.py [--signal ext] [--tous]

Sort le taux d'exactitude, la tolerance a +/-1 rep, l'erreur absolue moyenne, et la
liste des ecarts. Les clips marques "na" dans la verite terrain (pas de mouvement
comptable) sont sortis du calcul et listes a part.

Les clips marques `ambigu` restent dans le calcul principal — ce sont de vraies videos,
filmees comme le font les vrais utilisateurs — mais le score sans eux est affiche juste
en dessous, pour qu'on voie tout de suite s'ils portent la conclusion ou non.
"""

import argparse
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

from compte_reps import compte                       # noqa: E402

VT = os.path.join(ICI, "verite_terrain.json")
SIGNAUX = os.path.join(ICI, "signaux.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal", default="ext", choices=["ext", "hip", "wri", "post", "abs", "med"])
    ap.add_argument("--tous", action="store_true", help="afficher aussi les clips justes")
    ap.add_argument("--bas", type=float, default=None)
    ap.add_argument("--haut", type=float, default=None)
    a = ap.parse_args()

    vt = json.load(open(VT))["clips"]
    sig = json.load(open(SIGNAUX))
    kw = {}
    if a.bas is not None:
        kw["bas"] = a.bas
    if a.haut is not None:
        kw["haut"] = a.haut

    lignes, manquants, na = [], [], []
    for clip, ref in sorted(vt.items()):
        if clip not in sig:
            manquants.append(clip)
            continue
        n, verrous = compte(sig[clip]["points"], a.signal, details=True, **kw)
        if ref["n"] == "na":
            na.append((clip, n))
            continue
        lignes.append((clip, ref["n"], n, ref.get("conf", ""), verrous, ref.get("ambigu")))

    def mesures(lot):
        ex = sum(1 for _, r, n, _, _, _ in lot if r == n)
        pm = sum(1 for _, r, n, _, _, _ in lot if abs(r - n) <= 1)
        mae = sum(abs(r - n) for _, r, n, _, _, _ in lot) / max(len(lot), 1)
        return ex, pm, mae

    exact, proche, mae = mesures(lignes)
    tot_ref = sum(r for _, r, _, _, _, _ in lignes)
    tot_n = sum(n for _, _, n, _, _, _ in lignes)
    ambigus = [x for x in lignes if x[5]]

    print(f"signal={a.signal}  bas={kw.get('bas','defaut')} haut={kw.get('haut','defaut')}")
    print(f"{len(lignes)} clips comptables")
    print(f"exact      {exact}/{len(lignes)}  ({100*exact/max(len(lignes),1):.0f} %)")
    print(f"a +/-1 rep {proche}/{len(lignes)}  ({100*proche/max(len(lignes),1):.0f} %)")
    print(f"erreur absolue moyenne  {mae:.2f} rep")
    print(f"total reps  verite {tot_ref}  mesure {tot_n}")
    if ambigus:
        net = [x for x in lignes if not x[5]]
        e2, p2, m2 = mesures(net)
        print(f"sans les {len(ambigus)} clip(s) ambigu(s) : exact {e2}/{len(net)} "
              f"({100*e2/len(net):.0f} %)  a +/-1 {p2}/{len(net)} ({100*p2/len(net):.0f} %)  "
              f"eam {m2:.2f}")
    print()
    print(f"{'ref':>4} {'mp':>4} {'ecart':>6}  clip")
    for clip, r, n, conf, v, amb in sorted(lignes, key=lambda x: -abs(x[1] - x[2])):
        if not a.tous and r == n:
            continue
        print(f"{r:>4} {n:>4} {n-r:>+6}  {clip}   {conf}{'  [ambigu]' if amb else ''}")
    if na:
        print("\nhors calcul (pas de mouvement comptable) :")
        for clip, n in na:
            print(f"     {n:>4}         {clip}")
    if manquants:
        print("\nsans signal de pose :")
        for c in manquants:
            print("     ", c)


if __name__ == "__main__":
    main()
