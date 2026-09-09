"""Le VRAI rappel du detecteur de candidats : couvre-t-il les repetitions reelles ?

    cd backend && uv run python eval/reps/rappel_instants.py

Jusqu'ici la couverture etait comptee en NOMBRE de candidats, et ce proxy ment : sur
conventionnal_deadlift_14, trois candidats pour trois reps donnaient une couverture
"parfaite" alors qu'un seul candidat etait reel — les deux autres etant le lifter qui
marche vers la camera. Avec les instants de verrouillage marques a la main (`verrous`
dans verite_terrain.json), la question se pose correctement :

    rappel     une repetition reelle tombe-t-elle dans la fenetre d'un candidat ?
    precision  un candidat contient-il une repetition reelle ?

Le detecteur est regle pour le RAPPEL — le modele de langage ne peut qu'elaguer la
liste, jamais l'enrichir. C'est donc la premiere ligne qui commande.
"""
import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(os.path.dirname(ICI))
sys.path.insert(0, BACKEND)

import rep_detection as rd                                     # noqa: E402


def candidats_depuis_cache(sig):
    """[{lockout_s, debut_s, fin_s}] — l'algorithme de production sur un signal en cache."""
    pts = [p for p in sig["points"]
           if p.get("hip_deg") is not None and p.get("knee_deg") is not None
           and p.get("vis_near", 0) >= rd.VIS_MIN]
    if len(pts) < 6:
        return []
    ts = np.array([p["t"] for p in pts])
    vs = np.array([(p["hip_deg"] + p["knee_deg"]) / 2 for p in pts])
    return rd.depuis_signal(ts, vs, float(sig.get("duree_s") or ts[-1]))


def main():
    vt = json.load(open(os.path.join(ICI, "verite_terrain.json"), encoding="utf-8"))["clips"]
    caches = {}
    for nom, f in (("6 im/s", "signaux_6fps.json"), ("15 im/s", "signaux_15fps.json")):
        chemin = os.path.join(ICI, f)
        if os.path.exists(chemin):
            caches[nom] = json.load(open(chemin, encoding="utf-8"))

    annotes = {k: v["verrous"] for k, v in vt.items() if v.get("verrous")}
    print(f"{len(annotes)} clip(s) avec des instants marques, "
          f"{sum(len(v) for v in annotes.values())} repetitions\n")

    for nom, cache in caches.items():
        trouvees = manquees = total_cands = cands_vides = 0
        ecarts, detail = [], []
        for clip, reels in annotes.items():
            if clip not in cache:
                continue
            cands = candidats_depuis_cache(cache[clip])
            total_cands += len(cands)
            couvertes = 0
            for t in reels:
                pris = [c for c in cands if c["debut_s"] <= t <= c["fin_s"]]
                if pris:
                    trouvees += 1
                    couvertes += 1
                    ecarts.append(min(abs(c["lockout_s"] - t) for c in pris))
                else:
                    manquees += 1
            cands_vides += sum(
                1 for c in cands if not any(c["debut_s"] <= t <= c["fin_s"] for t in reels))
            detail.append((clip, len(reels), len(cands), couvertes))

        n = max(trouvees + manquees, 1)
        print(f"=== {nom}")
        print(f"    RAPPEL     {trouvees}/{trouvees + manquees} repetitions reelles "
              f"couvertes ({trouvees / n:.0%})")
        print(f"    precision  {total_cands - cands_vides}/{total_cands} candidats "
              f"contiennent une vraie rep "
              f"({(total_cands - cands_vides) / max(total_cands, 1):.0%})")
        if ecarts:
            print(f"    ecart du verrouillage detecte : median {np.median(ecarts):.2f}s, "
                  f"90e centile {np.percentile(ecarts, 90):.2f}s")
        for clip, r, c, cv in detail:
            marque = "" if cv == r else f"   <- {r - cv} ratee(s)"
            print(f"      {clip[:40]:42s} {r} reps, {c} candidats, {cv} couvertes{marque}")
        print()


if __name__ == "__main__":
    main()
