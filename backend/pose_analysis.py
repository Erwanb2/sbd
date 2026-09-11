"""Analyse de pose : variante du deadlift, qualite de la capture, mesures par repetition.

C'est la moitie MediaPipe du systeme. L'autre moitie est le modele de langage ; le
partage des taches est declare une fois pour toutes dans `indicators.py`, et ce fichier
ne calcule que les indicateurs marques `Source.POSE`.

Deux passes MediaPipe : 30 frames uniformes pour la cascade, puis la passe dense a
6 im/s de `rep_detection`, dont les poses servent a la fois a proposer les repetitions
et a les mesurer.

La variante vient d'une cascade a trois mesures, etablie sur 47 clips etiquetes
(46/47, 0.936 en validation leave-one-out) :

    largeur    = mediane sur le clip de (ecart talons / ecart epaules), projete sur
                 l'axe 3D cheville->cheville. Seul axe qui reste defini quel que soit
                 l'angle de camera, contrairement aux axes epaules ou hanches.
    confiance  = 10e centile de (ecart des poignets / longueur du tronc) en 2D. Tombe a
                 zero quand le corps est vu par la tranche : la largeur n'a alors plus
                 aucun appui lateral. Un 10e centile et non un minimum, qui n'est pas
                 stable d'un echantillonnage de frames a l'autre.
    profondeur = (z_main - z_genou) du cote camera, au bas de la tiree. C'est le repere
                 qu'un humain lit de profil : avant-bras devant le genou (mains a
                 l'exterieur, conventionnel) ou derriere (mains entre les jambes, sumo).

Les seuils vivent dans REGLES et ont ete ajustes en conditions de production :
modele heavy, 30 frames, pleine resolution, lecture sequentielle.
"""

from __future__ import annotations

import logging
import math
import os
import struct
import time

import cv2
import numpy as np

import indicators

logger = logging.getLogger(__name__)

_MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
              "pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task")


def _resoudre_modele() -> str:
    """Chemin du modele : variable d'environnement, image Docker, puis cache local.

    En production le modele est embarque dans l'image. En local (scripts d'evaluation),
    on le telecharge une fois dans le cache utilisateur pour que rien ne soit a regler.
    """
    explicite = os.getenv("MEDIAPIPE_POSE_MODEL")
    if explicite:
        return explicite
    if os.path.exists("/models/pose_landmarker_heavy.task"):
        return "/models/pose_landmarker_heavy.task"
    cache = os.path.join(os.path.expanduser("~"), ".cache", "sbd")
    local = os.path.join(cache, "pose_landmarker_heavy.task")
    if not os.path.exists(local):
        import urllib.request
        os.makedirs(cache, exist_ok=True)
        logger.info("telechargement du modele de pose vers %s", local)
        urllib.request.urlretrieve(_MODEL_URL, local)
    return local


_MODEL_CACHE = None


def modele() -> str:
    "Resolution paresseuse : un import ne doit pas declencher un telechargement."
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        _MODEL_CACHE = _resoudre_modele()
    return _MODEL_CACHE
N_CASCADE = 30          # frames de la cascade : la configuration validee

REGLES = {
    "seuil_largeur": 1.605,
    "seuil_confiance": 0.0056,
    "seuil_profondeur": -0.0129,
}

L = dict(nose=0, l_ear=7, r_ear=8, l_sh=11, r_sh=12, l_el=13, r_el=14, l_wr=15, r_wr=16,
         l_idx=19, r_idx=20, l_hip=23, r_hip=24, l_kn=25, r_kn=26, l_an=27, r_an=28,
         l_heel=29, r_heel=30, l_toe=31, r_toe=32)

# Le sous-ensemble de reperes qu'un overlay a besoin de dessiner : le tronc et les
# quatre membres, sans les doigts ni les oreilles. L'ORDRE est le contrat avec le
# front, qui n'a pas les noms — seulement cette meme liste, ecrite en dur.
KEYS_SQUELETTE = ("nose", "l_sh", "r_sh", "l_el", "r_el", "l_wr", "r_wr",
                  "l_hip", "r_hip", "l_kn", "r_kn", "l_an", "r_an",
                  "l_heel", "r_heel", "l_toe", "r_toe")


# --------------------------------------------------------------------------- video

def _rotation(path: str):
    """OpenCV ignore le flag de rotation des mp4 : on lit la matrice du tkhd nous-memes."""
    def walk(f, end):
        while f.tell() < end:
            st = f.tell()
            hdr = f.read(8)
            if len(hdr) < 8:
                return
            size, typ = struct.unpack(">I4s", hdr)
            typ = typ.decode("latin1")
            if size == 1:
                size = struct.unpack(">Q", f.read(8))[0]
            if size < 8:
                return
            if typ in ("moov", "trak", "mdia"):
                yield from walk(f, st + size)
            elif typ == "tkhd":
                data = f.read(size - (f.tell() - st))
                m = struct.unpack(">9i", data[-44:-8])
                yield round(math.degrees(math.atan2(m[1] / 65536.0, m[0] / 65536.0))) % 360
            f.seek(st + size)
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            end = f.tell()
            f.seek(0)
            for r in walk(f, end):
                if r == 90:
                    return cv2.ROTATE_90_CLOCKWISE
                if r == 270:
                    return cv2.ROTATE_90_COUNTERCLOCKWISE
                if r == 180:
                    return cv2.ROTATE_180
    except Exception:
        pass
    return None


def _read_frames(path: str, indices):
    """Lecture sequentielle : plus rapide que cap.set(), qui doit remonter aux images cles.

    Exception faite d'une fenetre courte et tardive (la descente), ou un seul seek au
    debut de la fenetre evite de redecoder tout ce qui precede.
    """
    want = set(int(i) for i in indices)
    if not want:
        return [], 30.0
    lo, hi = min(want), max(want)
    rot = _rotation(path)
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    i = 0
    if lo > 300 and (hi - lo) < 200:              # fenetre etroite et loin du debut
        cap.set(cv2.CAP_PROP_POS_FRAMES, lo)
        i = lo
    out = []
    try:
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if i in want:
                if rot is not None:
                    fr = cv2.rotate(fr, rot)
                out.append((i, i / fps, fr))
            i += 1
    finally:
        cap.release()
    return out, fps


def _fenetre_de_mouvement(path: str, n_frames: int, largeur: int = 160):
    """Intervalle de frames ou l'image bouge le plus : c'est la qu'a lieu la tiree.

    Difference absolue moyenne entre images successives, calculee sur une miniature en
    niveaux de gris. Sert de repli quand un echantillonnage uniforme rate la repetition
    dans un clip long.
    """
    cap = cv2.VideoCapture(path)
    prev, vals, idxs, i = None, [], [], 0
    pas = max(1, n_frames // 120)
    try:
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if i % pas == 0:
                g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
                g = cv2.resize(g, (largeur, max(1, int(g.shape[0] * largeur / g.shape[1]))))
                if prev is not None:
                    vals.append(float(np.mean(cv2.absdiff(g, prev))))
                    idxs.append(i)
                prev = g
            i += 1
    except Exception:
        return None
    finally:
        cap.release()
    if len(vals) < 8:
        return None
    v = np.array(vals)
    if v.max() - v.min() < 1e-6:
        return None
    fort = np.array(idxs)[v >= v.min() + 0.35 * (v.max() - v.min())]
    if len(fort) < 3:
        return None
    marge = int(0.5 * n_frames / max(len(vals), 1))
    return max(0, int(fort[0]) - marge), min(n_frames - 1, int(fort[-1]) + marge)


def _probe(path: str):
    cap = cv2.VideoCapture(path)
    try:
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    finally:
        cap.release()
    return n, fps


# --------------------------------------------------------------------------- pose

def _landmarker():
    import mediapipe as mp
    from mediapipe.tasks.python import vision, BaseOptions
    return vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=modele()),
        running_mode=vision.RunningMode.VIDEO, num_poses=1,
        min_pose_detection_confidence=0.3, min_pose_presence_confidence=0.3,
        min_tracking_confidence=0.3))


def _detect(frames, fps):
    """Renvoie une liste de dicts {i, t, im, wd, w, h} pour les frames ou une pose sort."""
    import mediapipe as mp
    lmk = _landmarker()
    out = []
    for k, (i, t, fr) in enumerate(frames):
        h, w = fr.shape[:2]
        # Horodatage = position reelle dans la video. Le suivi inter-frames de MediaPipe
        # s'en sert : une progression differente donne des reperes legerement differents,
        # et donc des mesures qui ne correspondent plus aux seuils ajustes.
        res = lmk.detect_for_video(
            mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)),
            int(i * 1000 / fps))
        if res.pose_landmarks:
            lm = res.pose_landmarks[0]
            wl = res.pose_world_landmarks[0]
            out.append(dict(i=i, t=t, w=w, h=h,
                            im=np.array([[p.x, p.y, p.z, p.visibility] for p in lm]),
                            wd=np.array([[p.x, p.y, p.z] for p in wl])))
    return out


# ------------------------------------------------------------------- cascade sumo

def _frame_measures(f):
    """Les trois grandeurs par frame, plus ce qu'il faut pour filtrer et agreger."""
    im, wd = f["im"], f["wd"]
    ar = f["w"] / f["h"]
    p = lambda k: np.array([im[L[k], 0] * ar, im[L[k], 1]])
    P = lambda k: wd[L[k], :3]
    V = lambda k: float(im[L[k], 3])

    sh_c, hip_c = (p("l_sh") + p("r_sh")) / 2, (p("l_hip") + p("r_hip")) / 2
    torso = float(np.linalg.norm(sh_c - hip_c))
    if torso < 1e-6:
        return None
    out = {"wri_over_torso": abs(p("l_wr")[0] - p("r_wr")[0]) / torso,
           "hip_y": float(hip_c[1]),
           "vis_legs": float(np.mean([V(k) for k in ("l_an", "r_an", "l_kn", "r_kn")]))}

    an = P("l_an") - P("r_an")
    an[1] = 0.0
    n = np.linalg.norm(an)
    if n > 1e-6:
        u = an / n
        pr = lambda k: float(np.dot(P(k), u))
        sh = abs(pr("l_sh") - pr("r_sh"))
        out["largeur"] = abs(pr("l_heel") - pr("r_heel")) / max(sh, 1e-6)

    vl = np.mean([V(k) for k in ("l_wr", "l_el", "l_kn", "l_an")])
    vr = np.mean([V(k) for k in ("r_wr", "r_el", "r_kn", "r_an")])
    s = "l" if vl >= vr else "r"
    out["vis_near"] = float(max(vl, vr))
    zext = float(np.ptp(wd[:, 2])) + 1e-6
    out["profondeur"] = float((wd[L[f"{s}_idx"], 2] - wd[L[f"{s}_kn"], 2]) / zext)
    return out


def _cascade(poses):
    """Applique la cascade. Renvoie None si la pose n'est pas exploitable."""
    rows = [m for m in (_frame_measures(f) for f in poses) if m and "largeur" in m]
    if len(rows) < 3:
        return None
    strict = [r for r in rows if r["vis_legs"] > 0.4]
    used = strict if len(strict) >= 4 else rows
    largeur = float(np.median([r["largeur"] for r in used]))
    confiance = float(np.percentile([r["wri_over_torso"] for r in rows], 10))

    znear = [r for r in rows if r["vis_near"] > 0.4] or rows
    znear.sort(key=lambda r: -r["hip_y"])
    bot = znear[:max(3, len(znear) // 3)]
    profondeur = float(np.median([r["profondeur"] for r in bot]))

    if confiance >= REGLES["seuil_confiance"]:
        variante = "sumo" if largeur >= REGLES["seuil_largeur"] else "conventional"
        regle = "largeur"
    else:
        variante = "sumo" if profondeur >= REGLES["seuil_profondeur"] else "conventional"
        regle = "profondeur"
    return dict(variante=variante, regle=regle, largeur=round(largeur, 3),
                confiance=round(confiance, 5), profondeur=round(profondeur, 4),
                frames_utilisees=len(used))


# ---------------------------------------------------------------- cinematique

def _px(f, key):
    """Coordonnees en pixels du repere demande."""
    im = f["im"]
    return np.array([im[L[key], 0] * f["w"], im[L[key], 1] * f["h"]])


def _angle(a, b, c):
    """Angle en degres au sommet b."""
    v1, v2 = a - b, c - b
    n = np.linalg.norm(v1) * np.linalg.norm(v2)
    if n < 1e-9:
        return float("nan")
    return float(np.degrees(np.arccos(np.clip(np.dot(v1, v2) / n, -1.0, 1.0))))


def _facing(f):
    """Sens du regard : nez a droite de l'oreille visible = tourne vers la droite."""
    im = f["im"]
    ear = "l_ear" if im[L["l_ear"], 3] >= im[L["r_ear"], 3] else "r_ear"
    return "right" if im[L["nose"], 0] > im[L[ear], 0] else "left"


def _vue_de_face(poses):
    """0 = profil pur, ~1 = face. Ecart des epaules rapporte a la longueur du tronc."""
    vals = []
    for f in poses:
        ar = f["w"] / f["h"]
        sh = abs(f["im"][L["l_sh"], 0] - f["im"][L["r_sh"], 0]) * ar
        # longueur reelle du tronc, pas seulement son etendue verticale : penche en
        # avant, un tronc vu de cote se raccourcit en y et gonflerait le ratio
        sc = np.array([(f["im"][L["l_sh"], 0] + f["im"][L["r_sh"], 0]) / 2 * ar,
                       (f["im"][L["l_sh"], 1] + f["im"][L["r_sh"], 1]) / 2])
        hc = np.array([(f["im"][L["l_hip"], 0] + f["im"][L["r_hip"], 0]) / 2 * ar,
                       (f["im"][L["l_hip"], 1] + f["im"][L["r_hip"], 1]) / 2])
        torso = float(np.linalg.norm(sc - hc))
        if torso > 1e-6:
            vals.append(sh / torso)
    return float(np.median(vals)) if vals else 0.0


def _side_clip(poses):
    """Cote camera decide une fois pour tout le clip.

    Le recalculer image par image fait basculer la reference des que les visibilites
    s'egalisent, et les angles sautent de plusieurs dizaines de degres sans que le lifter
    ait bouge.
    """
    vl = float(np.median([np.mean([f["im"][L[k], 3] for k in ("l_sh", "l_hip", "l_kn", "l_an", "l_wr")])
                          for f in poses]))
    vr = float(np.median([np.mean([f["im"][L[k], 3] for k in ("r_sh", "r_hip", "r_kn", "r_an", "r_wr")])
                          for f in poses]))
    return "l" if vl >= vr else "r"


def _joint_angles(f, s):
    """Angles hanche et genou, en degres, du cote passe en argument.

    Le cote est un argument obligatoire, jamais redecouvert image par image : le
    recalculer fait basculer la reference des que les visibilites s'egalisent, et les
    angles sautent de plusieurs dizaines de degres sans que le lifter ait bouge.
    """
    hip = _angle(_px(f, f"{s}_sh"), _px(f, f"{s}_hip"), _px(f, f"{s}_kn"))
    knee = _angle(_px(f, f"{s}_hip"), _px(f, f"{s}_kn"), _px(f, f"{s}_an"))
    return hip, knee


def _phases(poses, cote=None):
    """Bas de la tiree et verrouillage, lus sur l'extension des articulations.

    Les coordonnees image ne conviennent pas : la hauteur des hanches ne varie que de
    quelques centiemes et depend du cadrage. On suit l'extension moyenne hanche+genou,
    insensible au zoom et a la distance, et on y cherche la plus forte MONTEE : c'est la
    tiree. Chercher un minimum global echouerait sur un clip qui finit en flexion, ou qui
    contient plusieurs repetitions.
    """
    if len(poses) < 6:
        return None
    # Le cote se decide sur le CLIP, pas sur la fenetre d'une repetition. Le
    # redecouvrir par rep le fait basculer en cours de serie : mesure sur
    # conventionnal_deadlift_12, la rep 3 passait a droite quand les quatre autres
    # etaient a gauche, et ses mesures partaient en vrille (tibia a 157 degres,
    # buste a 142) — c'est cette rep-la qui produisait le persona du clip.
    cote = cote or _side_clip(poses)
    ang = np.array([_joint_angles(f, cote) for f in poses], dtype=float)
    ext = np.nanmean(ang, axis=1)
    if np.isnan(ext).all():
        return None
    ext = np.where(np.isnan(ext), np.nanmedian(ext), ext)
    # Filtre MEDIAN, et non moyenne mobile. Une moyenne ne supprime pas une valeur
    # aberrante, elle l'etale sur ses voisins : sur conventionnal_deadlift_14, le
    # squelette a decroche sur UNE image (156 -> 69 -> 160 deg), et la moyenne a
    # ecrase tout le plateau de verrouillage de 156 a ~125. Le maximum du signal
    # lisse est alors tombe une seconde et demie plus loin, EN PLEINE DESCENTE, et
    # les angles "de lockout" ont ete releves pendant que le lifter redescendait.
    # La mediane rend 156 sur les memes trois valeurs : le pic disparait, le plateau
    # reste. C'est deja le filtre de rep_detection ; les deux se rejoignent.
    if len(ext) >= 5:
        ext = np.array([float(np.median(ext[max(0, i - 1):i + 2])) for i in range(len(ext))])

    # plus forte montee : le creux le plus bas qui precede le sommet le plus haut
    best, liftoff, lockout = -1.0, 0, 0
    i_min = 0
    for j in range(1, len(ext)):
        if ext[j] - ext[i_min] > best:
            best, liftoff, lockout = float(ext[j] - ext[i_min]), i_min, j
        if ext[j] < ext[i_min]:
            i_min = j
    # un sumo ne ferme la hanche que d'une trentaine de degres : le seuil reste bas
    if best < 12.0 or lockout <= liftoff:
        return None
    # vrai maximum d'extension apres le depart : c'est le verrouillage. On peut se le
    # permettre parce que la descente est observee par une passe dediee, prise apres cet
    # instant dans la video, et non parmi les frames deja echantillonnees.
    apres = ext[liftoff + 1:]
    haut = float(np.max(apres))
    # premier passage a proximite du maximum : sur un clip ou le lifter reste debout ou
    # s'eloigne apres la serie, le maximum global tombe bien apres le vrai verrouillage
    lockout = liftoff + 1 + int(np.argmax(apres >= haut - 3.0))

    # On resserre le depart sur la tiree elle-meme : sinon un lifter qui reste debout
    # avant de se pencher etire la fenetre sur plusieurs secondes et fausse la derive.
    #
    # La question est posee en NIVEAU — "quel est le dernier instant ou il etait encore
    # en bas ?" — et non en remontant le temps pas a pas. L'ancienne version remontait
    # depuis le verrouillage tant que l'extension decroissait, avec une tolerance de
    # 1,5 degre sur un signal dont le bruit vaut 15 : elle s'arretait au premier
    # soubresaut. Sur conventionnal_deadlift_14 elle a transforme une tiree de deux
    # secondes en 0,16 s, soit une seule image, et tout le clip a ete note la-dessus.
    #
    # Un seuil de niveau ne se laisse pas arreter par une valeur isolee : un point
    # bruite reste de toute facon tres au-dessus du bas de la tiree.
    bas = float(np.min(ext[liftoff:lockout + 1]))
    seuil_bas = bas + 0.10 * (float(ext[lockout]) - bas)
    encore_en_bas = [i for i in range(liftoff, lockout) if ext[i] <= seuil_bas]
    liftoff = encore_en_bas[-1] if encore_en_bas else liftoff
    return dict(liftoff=liftoff, lockout=lockout, ext=ext, amplitude=best, cote=cote)



# ------------------------------------------------------- mesures d'une repetition
#
# Tout ce qui suit remplace l'ancien bloc `_kinematics`, qui calculait UNE cinematique
# pour le clip entier — celle de la plus forte montee — et l'affichait comme si elle
# decrivait la serie. Les mesures sont maintenant calculees par repetition.
#
# Deux regles tenues partout ici :
#   - aucune distance en centimetres. L'ancien code convertissait les pixels avec un
#     femur suppose de 40 cm : le resultat etait un ratio habille en unite calibree.
#     Les distances sont en FRACTION DE FEMUR, et le disent.
#   - aucune mesure hors de sa vue. Les angles lus a l'image ne veulent rien dire hors
#     profil, et un genou qui rentre est indiscernable d'un genou qui avance. Le filtre
#     est applique une fois, dans `_filtre_par_vue`, a partir du catalogue.


def _echelle(poses, s, lo, lk) -> float:
    """Longueur mediane du femur en pixels sur la tiree : l'unite de toutes les distances.

    Mediane et non valeur d'une frame : un seul genou qui saute fausserait toute la
    normalisation.
    """
    fem = [float(np.linalg.norm(_px(f, f"{s}_hip") - _px(f, f"{s}_kn")))
           for f in poses[lo:lk + 1]]
    fem = [x for x in fem if x > 1.0]
    return float(np.median(fem)) if fem else 1.0


def _facing_clip(poses) -> str:
    """Sens du regard decide UNE fois pour le clip, par vote majoritaire.

    Le recalculer par repetition le fait basculer des que le nez et l'oreille se
    croisent, et le signe de toutes les mesures orientees s'inverse avec lui : mesure
    sur conventionnal_deadlift_1, une rep sortait a 50,9 degres de bascule arriere
    faute de ce vote. Meme piege que le cote camera, meme remede.
    """
    droite = sum(1 for f in poses if _facing(f) == "right")
    return "right" if droite * 2 >= len(poses) else "left"


def _inclinaison(f, s) -> float:
    """Ecart du segment hanche->epaule a la verticale, en degres. Toujours positif."""
    v = _px(f, f"{s}_sh") - _px(f, f"{s}_hip")
    return float(abs(np.degrees(np.arctan2(v[0], -v[1]))))


def _inclinaison_signee(f, s, facing) -> float:
    """Meme mesure, signee : positif = epaules devant, negatif = penche en arriere."""
    v = _px(f, f"{s}_sh") - _px(f, f"{s}_hip")
    a = float(np.degrees(np.arctan2(v[0], -v[1])))
    return a if facing == "right" else -a


def mesures_de_rep(poses, extra=None, facing=None, cote=None) -> dict | None:
    """Les mesures POSE d'UNE repetition. None si la tiree n'est pas identifiable.

    `poses` est la fenetre de la repetition, `extra` d'eventuelles frames posterieures
    au verrouillage (la descente), `facing` le sens du regard fige sur tout le clip.
    Les cles rendues sont exactement les `mesure` des indicateurs `Source.POSE`.
    """
    ph = _phases(poses, cote)
    if ph is None:
        return None
    lo, lk, s, ext = ph["liftoff"], ph["lockout"], ph["cote"], ph["ext"]
    f_lo, f_lk = poses[lo], poses[lk]
    facing = facing or _facing_clip(poses)
    femur = _echelle(poses, s, lo, lk)
    m: dict = {}

    # Garde-fou repris de l'ancien code : si les articulations ne sont pas etendues sur
    # la frame retenue, ce n'est pas un verrouillage — le reperage des phases a echoue et
    # toutes les mesures qui suivent seraient fausses. Mieux vaut ne rien rendre.
    hanche_lk = _angle(_px(f_lk, f"{s}_sh"), _px(f_lk, f"{s}_hip"), _px(f_lk, f"{s}_kn"))
    genou_lk = _angle(_px(f_lk, f"{s}_hip"), _px(f_lk, f"{s}_kn"), _px(f_lk, f"{s}_an"))
    if math.isnan(hanche_lk) or math.isnan(genou_lk) or min(hanche_lk, genou_lk) < 120:
        return None

    # --- setup (S01, S02, S03) --------------------------------------------------
    im = f_lo["im"]
    y_sh, y_hip, y_kn = (im[L[f"{s}_sh"], 1], im[L[f"{s}_hip"], 1], im[L[f"{s}_kn"], 1])
    if abs(y_kn - y_sh) > 1e-6:
        m["hip_ratio"] = round(float((y_hip - y_sh) / (y_kn - y_sh)), 3)

    sens = 1.0 if facing == "right" else -1.0
    m["shoulder_bar_offset"] = round(float((_px(f_lo, f"{s}_sh")[0] - _px(f_lo, f"{s}_wr")[0])
                                     * sens / femur), 3)

    v_tibia = _px(f_lo, f"{s}_kn") - _px(f_lo, f"{s}_an")
    m["shin_deg"] = round(float(abs(np.degrees(np.arctan2(v_tibia[0], -v_tibia[1])))), 1)

    # --- decollage (L01, L02) ---------------------------------------------------
    # Premier tiers de la tiree : c'est la que se joue le leg drive.
    #
    # Encore faut-il qu'il y ait un premier tiers. A 6 im/s, une tiree reperee sur
    # trois images ne permet pas de comparer une montee de hanche a une montee
    # d'epaule : le "tiers" fait une image. Mesure sur conventionnal_deadlift_12, une
    # rep de 0,5 s sortait un rapport de 9,99 — la sentinelle "les epaules ne montent
    # pas" — et donnait a elle seule son persona au clip.
    assez_dense = (lk - lo) >= 4
    i_tiers = min(lk, lo + max(1, (lk - lo) // 3))
    f_t = poses[i_tiers]
    # en coordonnees image, y decroit vers le haut : une montee est une difference positive
    montee_hanche = float(_px(f_lo, f"{s}_hip")[1] - _px(f_t, f"{s}_hip")[1])
    montee_epaule = float(_px(f_lo, f"{s}_sh")[1] - _px(f_t, f"{s}_sh")[1])
    if assez_dense and montee_hanche > 0.02 * femur:   # sinon la tiree n'a pas commence
        if montee_epaule <= 0.005 * femur:
            # les epaules ne montent pas du tout : c'est le cas extreme, pas une division
            m["rise_ratio"] = 9.99
        else:
            m["rise_ratio"] = round(montee_hanche / montee_epaule, 2)

    if assez_dense:
        m["pitch_deg"] = round(_inclinaison(f_t, s) - _inclinaison(f_lo, s), 1)

    # --- tiree (P01, P05, P06, P07) ---------------------------------------------
    # Derive mesuree par rapport aux CHEVILLES, qui ne bougent pas de la tiree : un
    # panoramique de camera ou un lifter qui se decale ne comptent plus comme une derive.
    xs = []
    for f in poses[lo:lk + 1]:
        cheville = (_px(f, "l_an")[0] + _px(f, "r_an")[0]) / 2
        xs.append(_px(f, f"{s}_wr")[0] - cheville)
    if len(xs) >= 4:
        # 5e-95e centile et non max-min : un seul repere egare ne definit pas la trajectoire
        span = float(np.percentile(xs, 95) - np.percentile(xs, 5)) / femur
        if span <= 2.0:                        # au-dela, c'est la pose qui delire
            m["drift_ratio"] = round(span, 3)

    valgus = []
    for f in poses[lo:lk + 1]:
        g_an, d_an = _px(f, "l_an")[0], _px(f, "r_an")[0]
        base = abs(g_an - d_an)
        if base < 1e-6:
            continue
        milieu = (g_an + d_an) / 2
        rentre = ((abs(g_an - milieu) - abs(_px(f, "l_kn")[0] - milieu))
                  + (abs(d_an - milieu) - abs(_px(f, "r_kn")[0] - milieu))) / 2
        valgus.append(rentre / base)
    if valgus:
        m["valgus_ratio"] = round(float(np.median(valgus)), 3)

    vitesses = np.diff(ext[lo:lk + 1])
    if len(vitesses) >= 3 and float(np.mean(vitesses)) > 1e-6:
        creux = int(np.argmin(vitesses))
        # -1 = aucun ralentissement marque ; sinon la position relative du creux
        m["sticking"] = (round(creux / max(len(vitesses) - 1, 1), 2)
                           if vitesses[creux] < 0.35 * float(np.mean(vitesses)) else -1.0)

    m["pull_s"] = round(float(f_lk["t"] - f_lo["t"]), 2)

    # --- lockout (K01, K02, K03, K06) -------------------------------------------
    m["hip_lockout_deg"] = round(hanche_lk, 1)
    m["knee_lockout_deg"] = round(genou_lk, 1)
    m["lean_back_deg"] = round(max(0.0, -_inclinaison_signee(f_lk, s, facing)), 1)

    # duree du dernier bout de la tiree : le temps passe a finir le mouvement
    seuil = float(ext[lk]) - 10.0
    j = lk
    while j - 1 > lo and ext[j - 1] >= seuil:
        j -= 1
    m["lockout_s"] = round(float(f_lk["t"] - poses[j]["t"]), 2)

    # --- descente (E01) ----------------------------------------------------------
    apres = [f for f in (extra or []) if f["t"] > f_lk["t"]] or list(poses[lk + 1:])
    cible = next((f for f in apres if f["t"] - f_lk["t"] >= 0.35), apres[-1] if apres else None)
    if cible is not None:
        h2 = _angle(_px(cible, f"{s}_sh"), _px(cible, f"{s}_hip"), _px(cible, f"{s}_kn"))
        k2 = _angle(_px(cible, f"{s}_hip"), _px(cible, f"{s}_kn"), _px(cible, f"{s}_an"))
        if not math.isnan(h2) and not math.isnan(k2):
            # positif = la hanche a plus flechi que le genou = charniere correcte
            m["descent_order"] = round((hanche_lk - h2) - (genou_lk - k2), 1)

    m["_phases"] = dict(decollage_s=round(f_lo["t"], 2), lockout_s=round(f_lk["t"], 2),
                        cote=s, facing=facing)
    return m


def _filtre(mesures: dict, vue: float, visibilite: float) -> dict:
    """Ne garde que les mesures qu'on a le droit de croire.

    Trois raisons de jeter une mesure, toutes declarees dans le catalogue :

    1. **La camera n'est pas au bon endroit** (`Indicateur.vue`). Un genou qui rentre
       est indiscernable d'un genou qui avance vu de profil.
    2. **La valeur est physiquement impossible** (`Indicateur.plausible`). Un tibia a
       157 degres ou un buste bascule de 142 degres ne sont pas un mauvais lift, ce
       sont les symptomes d'un reperage de phase qui a echoue. Sans cette borne, le
       systeme note avec assurance a partir de bruit — mesure sur
       conventionnal_deadlift_12, ou il mettait 1/3 en trajectoire de barre la ou
       l'humain repond "pas visible".
    3. **Les reperes ne sont pas fiables du tout** (`visibilite` sous le seuil bas
       du catalogue) : plus rien n'est mesurable.

    Une mesure jetee ne devient pas une mauvaise note : elle disparait, le critere
    n'a plus de quoi se noter, et la page dit "not visible". C'est la seule facon
    pour la pose de s'abstenir — les indicateurs POSE n'ont pas d'etat `not_visible`,
    puisqu'une mesure absente dit deja la meme chose.
    """
    garde = {k: v for k, v in mesures.items() if k.startswith("_")}
    # Les horodatages ne sont pas des mesures notees : ce sont des faits du clip, lus
    # sur les images et consommes par du code (`tenue_du_set`, l'histogramme). Depuis
    # le retrait des 17 indicateurs POSE le 2026-09-09, plus aucun indicateur ne les
    # reclamait, donc la boucle ci-dessous les jetait avec le reste — et la moitie
    # "ralentissement" de la tenue du set etait morte sans que rien ne le dise.
    garde.update({k: v for k, v in mesures.items() if k in indicators.MESURES_TECHNIQUES})
    if visibilite < indicators.VISIBILITE_MIN:
        return garde
    for ind in indicators.INDICATEURS:
        if ind.source is not indicators.Source.POSE or ind.mesure not in mesures:
            continue
        if ind.vue is indicators.Vue.PROFIL and vue >= 0.60:
            continue
        if ind.vue is indicators.Vue.FACE and vue < 0.30:
            continue
        valeur = mesures[ind.mesure]
        if ind.plausible and isinstance(valeur, (int, float)):
            bas, haut = ind.plausible
            if not (bas <= valeur <= haut):
                logger.info("mesure hors bornes ignoree : %s=%s (%s)", ind.mesure, valeur, ind.id)
                continue
        garde[ind.mesure] = valeur
    return garde


def _visibilite(poses) -> float:
    """Confiance moyenne des reperes qui portent les mesures."""
    cles = ("l_sh", "r_sh", "l_hip", "r_hip", "l_kn", "r_kn", "l_an", "r_an")
    return float(np.mean([np.mean([f["im"][L[k], 3] for k in cles]) for f in poses]))


def _squelette(denses: list[dict]) -> dict:
    """Le suivi dense (6 im/s de `rep_detection`), reduit a ce qu'un overlay dessine.

    Deja calcule pour proposer et mesurer les repetitions : on ne repasse pas
    MediaPipe, on ne garde que `KEYS_SQUELETTE`. `pts` reste dans le repere de `im`
    (x/y normalises [0,1] sur l'image APRES rotation, cf. `_read_frames`) : c'est le
    meme repere que `videoWidth`/`videoHeight` cote navigateur, donc mappable sans
    connaitre l'orientation d'origine du fichier.
    """
    idx = [L[k] for k in KEYS_SQUELETTE]
    return {
        "points": KEYS_SQUELETTE,
        "frames": [{"t": round(float(f["t"]), 2),
                   "pts": [[round(float(x), 3), round(float(y), 3), round(float(v), 3)]
                           for x, y, _z, v in f["im"][idx]]}
                  for f in denses],
    }


# ------------------------------------------------------------------- point d'entree

def analyse(file_path: str, avec_reps: bool = True) -> dict:
    """Variante, qualite de la capture, et les mesures POSE de chaque repetition.

    `avec_reps=False` s'arrete apres la cascade : c'est le mode d'eval/check_pose_cascade,
    qui valide la variante sur les 47 clips et n'a pas besoin de la passe dense.

    Ne leve jamais : en cas d'echec, renvoie {"ok": False, "raison": ...} et l'appelant
    se rabat sur le modele seul.

    Deux passes MediaPipe, et pas une de plus :
      1. 30 frames uniformes pour la cascade sumo/conventionnel. Cet echantillonnage
         est la configuration sur laquelle ses seuils ont ete valides — ne pas y toucher
         sans rejouer eval/check_pose_cascade.py.
      2. une passe dense a 6 im/s, celle de rep_detection, dont les poses servent a la
         fois a proposer les repetitions et a les mesurer.
    """
    t0 = time.time()
    try:
        n, fps = _probe(file_path)
        if n <= 0:
            return {"ok": False, "raison": "video illisible"}

        # --- passe 1 : la cascade, dans sa configuration validee -----------------
        idx = np.linspace(n * 0.05, n * 0.95, N_CASCADE).astype(int)
        frames, fps = _read_frames(file_path, idx)
        if len(frames) < 6:
            return {"ok": False, "raison": "trop peu de frames lisibles"}
        poses = _detect(frames, fps)
        if len(poses) < 6:
            return {"ok": False, "raison": "aucune pose exploitable"}

        casc = _cascade(poses)
        if not casc:
            return {"ok": False, "raison": "mesures de stance indisponibles"}

        vue = _vue_de_face(poses)
        visibilite = _visibilite(poses)
        res = {
            "ok": True,
            "duree_s": round(time.time() - t0, 2),
            "frames_pose": len(poses),
            # Les grandeurs de la cascade restent a plat, comme avant : eval/
            # check_pose_cascade les lit telles quelles pour justifier chaque decision.
            **casc,
            "view": round(vue, 3),
            "visibility": round(visibilite, 3),
            "reps": [],
        }

        if not avec_reps:
            return res

        # --- passe 2 : les repetitions, et leurs mesures --------------------------
        # Import local : rep_detection importe ce module, un import en tete ferait un
        # cycle. C'est le seul endroit ou les deux se rencontrent.
        import rep_detection

        candidats, denses = rep_detection.candidats_et_poses(file_path)
        # Le cote camera et le sens du regard se decident sur tout le clip, jamais par
        # repetition : sinon le signe des mesures orientees s'inverse en cours de serie.
        facing = _facing_clip(denses) if denses else "right"
        cote = _side_clip(denses) if denses else "l"
        for c in candidats:
            fenetre = [f for f in denses if c["debut_s"] <= f["t"] <= c["fin_s"]]
            apres = [f for f in denses if f["t"] > c["lockout_s"]]
            mes = mesures_de_rep(fenetre, apres, facing, cote) if len(fenetre) >= 6 else None
            res["reps"].append({
                "debut_s": c["debut_s"],
                "fin_s": c["fin_s"],
                "lockout_s": c["lockout_s"],
                "mesures": _filtre(mes, vue, visibilite) if mes else {},
            })

        # Le suivi complet du clip, pas seulement des fenetres de repetition : la video
        # cote front se scrube aussi en dehors d'une rep selectionnee.
        res["squelette"] = _squelette(denses)

        res["duree_s"] = round(time.time() - t0, 2)
        return res
    except Exception as exc:                        # jamais bloquant pour la requete
        logger.warning("analyse de pose impossible: %s", exc)
        return {"ok": False, "raison": f"{type(exc).__name__}: {exc}"}
