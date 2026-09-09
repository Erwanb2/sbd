"""Detection des repetitions candidates : ou le lifter se redresse dans la video.

La pose voit le corps, pas la barre. Ce module ne pretend donc pas compter les reps —
il propose des INSTANTS ou une repetition est possible, et c'est le modele de langage
qui tranche ensuite (champ `bar_left_floor` du schema). Mesure a l'appui : se redresser
apres avoir repose la barre produit exactement le meme mouvement de corps qu'une rep.

Consequence sur le reglage : le modele ne peut qu'ELAGUER la liste, jamais l'enrichir.
L'hysteresis est donc calee pour le RAPPEL (0.40/0.60) et non pour l'exactitude — mieux
vaut un candidat de trop, que le modele ecartera, qu'une repetition jamais proposee.
Sur les 47 clips etiquetes de data/, ce reglage met toutes les vraies reps dans la liste
sur 43 clips ; le reglage equilibre n'en couvrait que 42.

Passe de pose SEPAREE de celle de pose_analysis, volontairement : la cascade
sumo/conventionnel est validee sur exactement 30 frames avec leurs horodatages reels, et
son resultat change si on touche a son echantillonnage. On paye un second decodage
plutot que de risquer de la desetalonner.
"""

from __future__ import annotations

import logging

import numpy as np

import pose_analysis as pa

logger = logging.getLogger(__name__)

L = pa.L

FPS_ANALYSE = 6.0          # cadence de la passe de pose, en images par seconde
BAS, HAUT = 0.40, 0.60     # hysteresis, en fraction de l'amplitude du clip
PERIODE_MIN = 1.0          # s : deux verrouillages plus proches sont le meme
FENETRE_LISSAGE = 0.5      # s : largeur du filtre median
DUREE_BAS = 0.33           # s sous le seuil bas pour re-armer
AMPLITUDE_MIN = 25.0       # degres : sous ca, personne ne se redresse
VIS_MIN = 0.3              # sous ca, les reperes du cote camera sont devines
TROU_MAX = 1.2             # s : au-dela, coupure de plan -> segment separe
MARGE = 0.6                # s ajoutees de part et d'autre d'une fenetre de repetition


def _des_la_premiere_extension(ts, vs):
    """Jette l'entree de la video, jusqu'au creux d'ou part la premiere extension.

    Filmer, poser le telephone, tourner autour de la barre : ce temps mort debout entre
    dans les centiles et fausse les DEUX reperes. Mesure sur engueran_sumo (34 s de mise
    en place, une rep a 33,4 s) : le 5e centile ne descend jamais jusqu'au creux, il vaut
    155,4 deg la ou le creux reel est a 140 -> 18,8 deg d'amplitude apparente, sous le
    minimum, zero candidat pour une vraie repetition. Mesure sur long_deadlift : l'entree
    tire le 95e centile a 170,7 deg contre 163,7 pour la serie elle-meme, la normalisation
    est etalonnee sur du temps mort et l'hysteresis ne se re-arme plus entre deux reps
    enchainees -> 2 des 11 reps ratees.

    On ne touche qu'a l'ENTREE : des que l'extension est trouvee, le reste est intact.
    Une variante qui elaguait aussi les plages mortes du milieu perdait 3 reps de plus
    (136/146) — elle jetait les tirees lentes, dont l'extension s'etale sur plus de temps
    que la fenetre. Le seuil est AMPLITUDE_MIN, la meme extension que la porte exige.

    Rappel mesure sur les 146 repetitions horodatees : 141/146 a 6 im/s, contre 138 sans
    elagage et 139 avec une porte sur max - min.
    """
    creux = 0
    for j in range(1, len(vs)):
        if vs[j] < vs[creux]:
            creux = j
        elif vs[j] - vs[creux] >= AMPLITUDE_MIN:
            break
    else:
        return ts, vs                      # aucune extension : rien a elaguer
    if len(ts) - creux < 6:
        return ts, vs
    return ts[creux:], vs[creux:]


def _signal(poses):
    """(temps, extension) : moyenne des angles hanche et genou du cote camera.

    Choisi parmi quatre candidats mesures sur les 47 clips : c'est le seul qui soit
    invariant au cadrage. Les hauteurs brutes dans l'image suivent le moindre
    panoramique ou zoom, et celle des poignets saute des que les mains passent
    derriere un disque.
    """
    if not poses:
        return np.array([]), np.array([])
    cote = pa._side_clip(poses)
    ts, vs = [], []
    for f in poses:
        vis = float(np.mean([f["im"][L[f"{cote}_{k}"], 3] for k in ("sh", "hip", "kn", "an")]))
        if vis < VIS_MIN:
            continue
        try:
            hanche, genou = pa._joint_angles(f, cote)
        except Exception:
            continue
        ts.append(f["t"])
        vs.append((hanche + genou) / 2.0)
    return np.array(ts), np.array(vs)


def _cadence(ts):
    if len(ts) < 2:
        return FPS_ANALYSE
    pas = float(np.median(np.diff(ts)))
    return 1.0 / pas if pas > 1e-6 else FPS_ANALYSE


def _lisse(v, fps):
    """Filtre median sur FENETRE_LISSAGE secondes.

    En secondes et non en echantillons : sinon changer la cadence de la passe change
    la nervosite du filtre, et on ne mesure plus la pose mais son propre reglage.
    """
    k = max(3, int(round(FENETRE_LISSAGE * fps)) | 1)
    if len(v) < k:
        return v
    demi = k // 2
    piles = np.stack([v[i:len(v) - k + 1 + i] for i in range(k)])
    out = v.copy()
    out[demi:len(v) - demi] = np.median(piles, axis=0)
    return out


def _segments(ts, vs):
    "Coupe a chaque trou temporel : un plan de coupe n'est pas une descente."
    if len(ts) == 0:
        return []
    bornes = ([0] + [i for i in range(1, len(ts)) if ts[i] - ts[i - 1] > TROU_MAX]
              + [len(ts)])
    return [(a, b) for a, b in zip(bornes[:-1], bornes[1:]) if b - a >= 4]


def candidats_et_poses(file_path: str, fps_analyse: float = FPS_ANALYSE):
    """([{lockout_s, debut_s, fin_s}], poses) : les candidats ET la passe dense.

    Les poses sont rendues telles quelles pour que `pose_analysis` mesure les
    repetitions sans repasser MediaPipe une troisieme fois sur la meme video.
    L'echantillonnage et l'hysteresis ne changent pas : le reglage cale pour le rappel
    (0.40/0.60) est exactement celui valide sur les 47 clips.
    """
    return _candidats(file_path, fps_analyse)


def candidats(file_path: str, fps_analyse: float = FPS_ANALYSE) -> list[dict]:
    "Les candidats seuls, pour les appelants qui n'ont pas besoin des poses."
    return _candidats(file_path, fps_analyse)[0]


def _candidats(file_path: str, fps_analyse: float = FPS_ANALYSE):
    """[{lockout_s, debut_s, fin_s}] : les instants ou une repetition est possible.

    La fenetre d'un candidat va du creux qui precede sa montee au creux qui suit sa
    descente, plus une marge : c'est la repetition entiere, phase excentrique comprise.
    Sans elle, `eccentric_control_and_descent` est note a l'aveugle — mesure sur
    conventionnal_deadlift_11, la note passe de 1 a 2-4 (mesure faite sur l'ancienne
    echelle 1-4 du schema) quand la descente est dans
    la fenetre.
    """
    n, fps = pa._probe(file_path)
    if not n or not fps:
        return [], []
    pas = max(1, int(round(fps / fps_analyse)))
    frames, _ = pa._read_frames(file_path, range(0, n, pas))
    if not frames:
        return [], []
    poses = pa._detect(frames, fps)
    if len(poses) < 6:
        return [], []

    ts, vs = _signal(poses)
    if len(ts) < 6:
        return [], poses
    cad = _cadence(ts)
    vs = _lisse(vs, cad)
    ts, vs = _des_la_premiere_extension(ts, vs)
    lo, hi = float(np.percentile(vs, 5)), float(np.percentile(vs, 95))
    if hi - lo < AMPLITUDE_MIN:
        return [], poses
    norm = (vs - lo) / (hi - lo)
    duree = float(n / fps)
    mini_bas = max(2, round(DUREE_BAS * cad))

    verrous = []
    for a, b in _segments(ts, vs):
        arme = norm[a] < HAUT
        dernier, sous = -1e9, 0
        for i in range(a, b):
            if norm[i] < BAS:
                sous += 1
                if sous >= mini_bas:
                    arme = True
            elif norm[i] > HAUT and arme:
                sous = 0
                if ts[i] - dernier >= PERIODE_MIN:
                    verrous.append(i)
                    dernier = ts[i]
                arme = False
            else:
                sous = 0

    out = []
    for i in verrous:
        avant = [k for k in range(i, -1, -1) if norm[k] < BAS]
        apres = [k for k in range(i, len(ts)) if norm[k] < BAS]
        debut = float(ts[avant[0]]) if avant else 0.0
        fin = float(ts[apres[0]]) if apres else duree
        out.append({"lockout_s": round(float(ts[i]), 2),
                    "debut_s": round(max(0.0, debut - MARGE), 2),
                    "fin_s": round(min(duree, fin + MARGE), 2)})
    return out, poses


def analyse_candidats(file_path: str) -> list[dict]:
    "Enveloppe qui ne leve jamais : sans candidats, on retombe sur l'ancien prompt."
    try:
        return candidats(file_path)
    except Exception as exc:
        logger.warning("detection des repetitions candidates echouee : %s", exc)
        return []
