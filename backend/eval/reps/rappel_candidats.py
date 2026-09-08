"""Rejoue l'hysteresis DE PRODUCTION sur les signaux en cache, a 6 et 15 im/s.

La metrique qui compte pour l'architecture n'est pas l'exactitude du compte : le modele
ne peut qu'ELAGUER la liste des candidats, jamais l'enrichir. Ce qu'il faut mesurer,
c'est donc le RAPPEL — la pose propose-t-elle au moins autant de candidats qu'il y a
de vraies repetitions ?
"""
import json, sys
import numpy as np

ICI = "/mnt/c/Users/erwan/Documents/dev_projects/sbd/backend"
sys.path.insert(0, ICI)
import rep_detection as rd


def candidats_depuis_cache(sig):
    """Le meme algorithme que rep_detection.candidats, sur des points deja calcules."""
    pts = [p for p in sig["points"]
           if p.get("hip_deg") is not None and p.get("knee_deg") is not None
           and p.get("vis_near", 0) >= rd.VIS_MIN]
    if len(pts) < 6:
        return []
    ts = np.array([p["t"] for p in pts])
    vs = np.array([(p["hip_deg"] + p["knee_deg"]) / 2 for p in pts])
    cad = rd._cadence(ts)
    vs = rd._lisse(vs, cad)
    lo, hi = float(np.percentile(vs, 5)), float(np.percentile(vs, 95))
    if hi - lo < rd.AMPLITUDE_MIN:
        return []
    norm = (vs - lo) / (hi - lo)
    mini_bas = max(2, round(rd.DUREE_BAS * cad))

    verrous = []
    for a, b in rd._segments(ts, vs):
        arme = norm[a] < rd.HAUT
        dernier, sous = -1e9, 0
        for i in range(a, b):
            if norm[i] < rd.BAS:
                sous += 1
                if sous >= mini_bas:
                    arme = True
            elif norm[i] > rd.HAUT and arme:
                sous = 0
                if ts[i] - dernier >= rd.PERIODE_MIN:
                    verrous.append(float(ts[i]))
                    dernier = ts[i]
                arme = False
            else:
                sous = 0
    return verrous


vt = json.load(open(f"{ICI}/eval/reps/verite_terrain.json"))["clips"]
caches = {f: json.load(open(f"{ICI}/eval/reps/signaux_{f}.json")) for f in ("6fps", "15fps")}

stats = {f: {"couvre": 0, "total": 0, "cands": 0, "reps": 0} for f in caches}
detail = []
for clip, ref in vt.items():
    n = ref.get("n")
    if not isinstance(n, int) or n == 0 or any(clip not in c for c in caches.values()):
        continue
    ligne = [clip, n]
    for f, cache in caches.items():
        k = len(candidats_depuis_cache(cache[clip]))
        stats[f]["total"] += 1
        stats[f]["couvre"] += 1 if k >= n else 0
        stats[f]["cands"] += k
        stats[f]["reps"] += n
        ligne.append(k)
    detail.append(ligne)

print(f"{len(detail)} clips avec un compte humain\n")
for f, s in stats.items():
    print(f"  {f:6s}  au moins autant de candidats que de reps : "
          f"{s['couvre']}/{s['total']} ({s['couvre']/s['total']:.0%})   "
          f"candidats totaux {s['cands']} pour {s['reps']} reps")
print()
print("  clips ou 15 im/s change la couverture :")
for clip, n, a, b in detail:
    if (a >= n) != (b >= n):
        sens = "GAGNE" if b >= n else "PERD"
        print(f"     {sens:5s} {clip[:42]:44s} ref {n}  6fps {a:2d}  15fps {b:2d}")
