"""COPIE HISTORIQUE FIGEE — CE N'EST PLUS L'ALGORITHME DE PRODUCTION.

Ce module garde la version du detecteur telle qu'elle etait quand `test_candidats.py` et
`test_offsets.py` ont valide l'architecture ; leurs resultats enregistres ne veulent dire
quelque chose que si le code ne bouge pas. Ne rien y reporter.

Pour mesurer la production, appeler `rep_detection.depuis_signal` — c'est ce que font
`rappel_instants.py` et `rendu.py`. Le 2026-09-09, `rendu.py` importait encore d'ici et
dessinait donc un algorithme qui n'existait plus.

Compte les repetitions a partir du signal dense de dump_signal.py.

    cd backend
    uv run python eval/reps/compte_reps.py [--signal ext] [--json]

Principe : une repetition est un aller-retour bas -> haut du corps. On prend un signal
d'extension par frame, on le normalise sur le clip, et on compte les remontees avec une
hysteresis (il faut etre descendu sous BAS avant qu'un passage au-dessus de HAUT compte).
L'hysteresis est ce qui evite de compter le tremblement au verrouillage.

Quatre signaux possibles, gardes separes pour pouvoir les comparer :
  ext    moyenne des angles hanche et genou du cote camera  (invariant au cadrage)
  hip    hauteur des hanches dans l'image, signe inverse    (sensible au cadrage/zoom)
  wri    hauteur des poignets = hauteur de barre            (le plus direct, le plus fragile :
         derriere un disque, MediaPipe invente les poignets et le signal saute)
  post   (genou - epaule) / longueur du tronc : a quel point le buste est redresse. Un
         rapport de longueurs dans l'image, donc insensible au zoom et au panoramique,
         contrairement a hip et wri qui sont des hauteurs brutes.
"""

import argparse
import json
import os

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
SIGNAUX = os.path.join(ICI, "signaux.json")

# Reglages a priori, poses avant de regarder la verite terrain.
BAS, HAUT = 0.35, 0.65      # hysteresis, en fraction de l'amplitude du clip
PERIODE_MIN = 1.0           # s : deux verrouillages plus proches sont le meme
AMPLITUDE_MIN = {"ext": 25.0, "hip": 0.35, "wri": 0.35, "post": 0.5}  # sinon : personne ne bouge
# Les deux constantes du filtre sont en SECONDES, pas en echantillons : sinon changer la
# cadence de la passe de pose change la nervosite du compteur, et on mesure son filtre au
# lieu de mesurer la pose. A 6 fps elles valent bien 3 echantillons et 2 echantillons,
# les valeurs d'origine.
FENETRE_LISSAGE = 0.5       # s : largeur du filtre median
DUREE_BAS = 0.33            # s passees sous BAS pour re-armer : un point bas isole est un
                            # decrochage de suivi, pas une descente
VIS_MIN = 0.3               # sous ce seuil les reperes du cote camera sont devines
TROU_MAX = 1.2              # s : au-dela, coupure de plan -> segment separe


def serie(points, signal):
    """(temps, valeur) filtres sur la visibilite, orientes 'haut = debout'."""
    ts, vs = [], []
    for p in points:
        if p["vis_near"] < VIS_MIN:
            continue
        if signal == "ext":
            v = (p["hip_deg"] + p["knee_deg"]) / 2.0
        elif signal == "hip":
            v = -p["hip_y"]
        elif signal == "wri":
            v = -p["wri_y"]
        elif signal == "post":
            v = p["kn_y"] - p["sh_y"]
        else:
            raise ValueError(signal)
        ts.append(p["t"])
        vs.append(v)
    return np.array(ts), np.array(vs)


def _cadence(ts):
    "Echantillons par seconde, mesuree sur le signal lui-meme."
    if len(ts) < 2:
        return 6.0
    pas = float(np.median(np.diff(ts)))
    return 1.0 / pas if pas > 1e-6 else 6.0


def _lisse(v, fps):
    "Filtre median sur FENETRE_LISSAGE secondes, largeur impaire, minimum 3."
    k = max(3, int(round(FENETRE_LISSAGE * fps)) | 1)
    if len(v) < k:
        return v
    demi = k // 2
    piles = np.stack([v[i:len(v) - k + 1 + i] for i in range(k)])
    out = v.copy()
    out[demi:len(v) - demi] = np.median(piles, axis=0)
    return out


def segments(ts, vs):
    "Coupe la a chaque trou temporel : un plan de coupe n'est pas une descente."
    if len(ts) == 0:
        return []
    bornes = [0] + [i for i in range(1, len(ts)) if ts[i] - ts[i - 1] > TROU_MAX] + [len(ts)]
    return [(ts[a:b], vs[a:b]) for a, b in zip(bornes[:-1], bornes[1:]) if b - a >= 4]


# Variante a seuils ABSOLUS, en degres. Les seuils relatifs a l'amplitude du clip suivent
# le bruit : sur un verrouillage tenu trois secondes, un decrochage de suivi redescend sous
# la fraction basse et une meme repetition est comptee deux fois. Un verrouillage de
# souleve de terre, lui, a une definition physique : hanches et genoux tendus. Au bas de la
# tiree la moyenne hanche/genou vaut 70 a 100 degres, au verrouillage 165 a 180.
DEG_BAS, DEG_HAUT = 120.0, 155.0


def compte_absolu(points, details=False, bas=DEG_BAS, haut=DEG_HAUT):
    ts, vs = serie(points, "ext")
    if len(ts) < 6:
        return (0, []) if details else 0
    fps = _cadence(ts)
    vs = _lisse(vs, fps)
    n, verrous = 0, []
    for st, sv in segments(ts, vs):
        arme, dernier, sous = sv[0] < haut, -1e9, 0
        for t, x in zip(st, sv):
            if x < bas:
                sous += 1
                if sous >= max(2, round(DUREE_BAS * fps)):
                    arme = True
            elif x > haut and arme:
                sous = 0
                if t - dernier >= PERIODE_MIN:
                    n += 1
                    verrous.append(round(float(t), 2))
                    dernier = t
                arme = False
            else:
                sous = 0
    return (n, verrous) if details else n


def compte(points, signal="ext", bas=BAS, haut=HAUT, details=False):
    if signal == "abs":
        return compte_absolu(points, details=details)
    if signal == "med":
        # Mediane des quatre signaux. Chacun se trompe sur des clips differents (les
        # poignets derriere un disque, les hauteurs brutes sous un panoramique), donc
        # le vote reduit surtout les gros ecarts : c'est la variante qui tient le mieux
        # a +/-1 rep (47/48 contre 45/48 pour le meilleur signal seul).
        import statistics
        cs = sorted(compte(points, x, bas, haut) for x in ("ext", "hip", "wri", "post"))
        n = int(statistics.median(cs))
        if not details:
            return n
        # les horodatages rendus sont ceux du signal dont le compte egale la mediane
        for x in ("wri", "ext", "post", "hip"):
            k, v = compte(points, x, bas, haut, details=True)
            if k == n:
                return n, v
        return n, []
    ts, vs = serie(points, signal)
    if len(ts) < 6:
        return (0, []) if details else 0
    fps = _cadence(ts)
    vs = _lisse(vs, fps)
    lo, hi = np.percentile(vs, 5), np.percentile(vs, 95)
    if hi - lo < AMPLITUDE_MIN[signal]:
        return (0, []) if details else 0

    n, verrous = 0, []
    for st, sv in segments(ts, vs):
        norm = (sv - lo) / (hi - lo)
        # etat de depart : on n'exige une descente prealable que si on commence en haut
        arme = norm[0] < haut
        dernier, sous = -1e9, 0
        for t, x in zip(st, norm):
            if x < bas:
                sous += 1
                if sous >= max(2, round(DUREE_BAS * fps)):
                    arme = True
            elif x > haut and arme:
                sous = 0
                if t - dernier >= PERIODE_MIN:
                    n += 1
                    verrous.append(round(float(t), 2))
                    dernier = t
                arme = False
            else:
                sous = 0
    return (n, verrous) if details else n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal", default="ext", choices=["ext", "hip", "wri", "post", "abs", "med"])
    ap.add_argument("--signaux", default=SIGNAUX)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    d = json.load(open(a.signaux))
    res = {}
    for clip in sorted(d):
        n, v = compte(d[clip]["points"], a.signal, details=True)
        res[clip] = {"n": n, "verrous_s": v}
        if not a.json:
            print(f"{n:>3}  {clip}   {v}")
    if a.json:
        print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
