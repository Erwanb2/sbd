"""Le systeme sait-il reconnaitre les videos qu'il ne sait pas lire ?

    cd backend && uv run python eval/reps/sait_il_qu_il_ne_sait_pas.py

Rater des repetitions est une chose ; le rater SANS LE DIRE en est une autre. Ce script
confronte, clip par clip, le rappel reel (mesure contre les instants annotes) aux
indicateurs de qualite que le systeme calcule DEJA et pourrait utiliser pour s'abstenir :

    visibilite    confiance moyenne des reperes du cote camera
    instabilite   part des sauts d'extension > 40 deg entre deux images, physiquement
                  impossibles : c'est la signature d'un suivi qui decroche
"""
import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
sys.path.insert(0, os.path.dirname(os.path.dirname(ICI)))

from rappel_instants import candidats_depuis_cache             # noqa: E402


def qualite(sig):
    pts = [p for p in sig["points"]
           if p.get("hip_deg") is not None and p.get("knee_deg") is not None]
    if len(pts) < 5:
        return 0.0, 1.0
    vis = float(np.median([p.get("vis_near", 0) for p in pts]))
    ext = np.array([(p["hip_deg"] + p["knee_deg"]) / 2 for p in pts])
    return vis, float(np.mean(np.abs(np.diff(ext)) > 40))


def main():
    vt = json.load(open(os.path.join(ICI, "verite_terrain.json"), encoding="utf-8"))["clips"]
    cache = json.load(open(os.path.join(ICI, "signaux_6fps.json"), encoding="utf-8"))
    lignes = []
    for clip, e in vt.items():
        reels = e.get("verrous")
        if not reels or clip not in cache:
            continue
        cands = candidats_depuis_cache(cache[clip])
        couvertes = sum(1 for t in reels
                        if any(c["debut_s"] <= t <= c["fin_s"] for c in cands))
        vis, inst = qualite(cache[clip])
        lignes.append(dict(clip=clip, reps=len(reels), cands=len(cands),
                           couvertes=couvertes, vis=vis, inst=inst))

    complets = [l for l in lignes if l["couvertes"] == l["reps"]]
    partiels = [l for l in lignes if 0 < l["couvertes"] < l["reps"]]
    muets = [l for l in lignes if l["cands"] == 0]
    rates = [l for l in lignes if l["couvertes"] < l["reps"]]

    print(f"{len(lignes)} clips, {sum(l['reps'] for l in lignes)} repetitions\n")
    print(f"  rappel complet          {len(complets):2d} clips")
    print(f"  rappel partiel          {len(partiels):2d} clips  <- rate SANS LE DIRE")
    print(f"  aucun candidat du tout  {len(muets):2d} clips  <- le systeme refuse, il le DIT")
    print()

    def resume(nom, groupe):
        if not groupe:
            return
        print(f"  {nom:24s} visibilite mediane {np.median([l['vis'] for l in groupe]):.2f}"
              f"   instabilite mediane {np.median([l['inst'] for l in groupe]):.1%}")
    resume("rappel complet", complets)
    resume("rappel incomplet", rates)
    print()

    print("  les clips ou des reps sont ratees :")
    for l in sorted(rates, key=lambda x: -x["inst"]):
        etat = "AUCUN CANDIDAT" if l["cands"] == 0 else f"{l['couvertes']}/{l['reps']} couvertes"
        print(f"     {l['clip'][:38]:40s} {etat:16s} vis {l['vis']:.2f}  instab {l['inst']:5.1%}")
    print()

    # Un indicateur ne sert que s'il SEPARE. On le teste comme un classifieur.
    print("  pouvoir de separation d'un seuil sur l'instabilite :")
    for seuil in (0.08, 0.10, 0.12, 0.15, 0.20):
        alerte = [l for l in lignes if l["inst"] >= seuil]
        vrais = [l for l in alerte if l["couvertes"] < l["reps"]]
        manques = [l for l in rates if l["inst"] < seuil]
        print(f"     >= {seuil:.0%} : {len(alerte):2d} clips signales, dont {len(vrais):2d} "
              f"vraiment fautifs | {len(manques):2d} fautifs non signales")


if __name__ == "__main__":
    main()
