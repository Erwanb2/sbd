"""Analyse de pose : variante du deadlift (sumo/conventionnel) et cinematique du lift.

Une seule passe de decodage et une seule passe MediaPipe servent les deux usages.

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
N_DENSE = N_CASCADE     # une seule passe : le suivi inter-frames change les mesures,
                        # donc la cascade doit voir exactement sa configuration validee
N_DESCENT = 12          # frames supplementaires juste apres le lockout

REGLES = {
    "seuil_largeur": 1.605,
    "seuil_confiance": 0.0056,
    "seuil_profondeur": -0.0129,
}

L = dict(nose=0, l_ear=7, r_ear=8, l_sh=11, r_sh=12, l_el=13, r_el=14, l_wr=15, r_wr=16,
         l_idx=19, r_idx=20, l_hip=23, r_hip=24, l_kn=25, r_kn=26, l_an=27, r_an=28,
         l_heel=29, r_heel=30, l_toe=31, r_toe=32)

FEMUR_CM = 40.0         # longueur de femur supposee, pour convertir les pixels en cm


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

def _side(f):
    """Cote tourne vers la camera : ses reperes sont mesures, l'autre est devine."""
    im = f["im"]
    vl = np.mean([im[L[k], 3] for k in ("l_sh", "l_hip", "l_kn", "l_an", "l_wr")])
    vr = np.mean([im[L[k], 3] for k in ("r_sh", "r_hip", "r_kn", "r_an", "r_wr")])
    return "l" if vl >= vr else "r"


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


def _joint_angles(f, s=None):
    """Angles hanche et genou du cote camera, en degres."""
    s = s or _side(f)
    hip = _angle(_px(f, f"{s}_sh"), _px(f, f"{s}_hip"), _px(f, f"{s}_kn"))
    knee = _angle(_px(f, f"{s}_hip"), _px(f, f"{s}_kn"), _px(f, f"{s}_an"))
    return hip, knee


def _phases(poses):
    """Bas de la tiree et verrouillage, lus sur l'extension des articulations.

    Les coordonnees image ne conviennent pas : la hauteur des hanches ne varie que de
    quelques centiemes et depend du cadrage. On suit l'extension moyenne hanche+genou,
    insensible au zoom et a la distance, et on y cherche la plus forte MONTEE : c'est la
    tiree. Chercher un minimum global echouerait sur un clip qui finit en flexion, ou qui
    contient plusieurs repetitions.
    """
    if len(poses) < 6:
        return None
    cote = _side_clip(poses)
    ang = np.array([_joint_angles(f, cote) for f in poses], dtype=float)
    ext = np.nanmean(ang, axis=1)
    if np.isnan(ext).all():
        return None
    ext = np.where(np.isnan(ext), np.nanmedian(ext), ext)
    if len(ext) >= 5:
        lisse = np.convolve(ext, np.ones(3) / 3, mode="same")
        lisse[0], lisse[-1] = ext[0], ext[-1]
        ext = lisse

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

    # on resserre le depart sur la tiree elle-meme : en remontant depuis le verrouillage
    # jusqu'a ce que l'extension cesse de decroitre. Sans ca, un lifter qui reste debout
    # avant de se pencher etire la fenetre sur plusieurs secondes et fausse la derive.
    j = lockout
    while j - 1 > liftoff and ext[j - 1] <= ext[j] + 1.5:
        j -= 1
    liftoff = j
    return dict(liftoff=liftoff, lockout=lockout, ext=ext, amplitude=best, cote=cote)


def _kinematics(poses, extra=None):
    """Les six mesures demandees, plus les instants des phases."""
    ph = _phases(poses)
    if ph is None:
        return None
    lo, lk = ph["liftoff"], ph["lockout"]
    f_lo, f_lk = poses[lo], poses[lk]
    s = ph["cote"]
    facing = _facing(f_lk)
    out = {}

    # 1. hauteur des hanches au decollage
    im = f_lo["im"]
    sy, hy, ky = im[L[f"{s}_sh"], 1], im[L[f"{s}_hip"], 1], im[L[f"{s}_kn"], 1]
    denom = ky - sy
    if abs(denom) > 1e-6:
        ratio = float((hy - sy) / denom)
        out["setup_hips_position"] = ("Too low (squatter setup)" if ratio > 0.8 else
                                      "Too high (stiff-legged)" if ratio < 0.4 else
                                      "Optimal (midway between knees and shoulders)")
        out["setup_hip_ratio"] = round(ratio, 3)

    # 2. epaules par rapport a la barre au decollage
    sh, wr = _px(f_lo, f"{s}_sh"), _px(f_lo, f"{s}_wr")
    # echelle prise sur la mediane de la tiree : une seule frame ou le genou saute
    # suffirait a fausser toutes les conversions en centimetres
    femurs = [float(np.linalg.norm(_px(f, f"{s}_hip") - _px(f, f"{s}_kn")))
              for f in poses[lo:lk + 1]]
    femur_px = float(np.median([x for x in femurs if x > 1.0])) if any(x > 1.0 for x in femurs) else 1.0
    diff = (sh[0] - wr[0]) * (1.0 if facing == "right" else -1.0)
    rel = diff / femur_px
    out["shoulder_to_bar_alignment_at_start"] = (
        "Shoulders slightly ahead of bar (good)" if rel > 0.08 else
        "Shoulders behind bar (subpar)" if rel < -0.08 else
        "Shoulders directly over bar")
    out["shoulder_bar_offset_cm"] = round(rel * FEMUR_CM, 1)

    # 3. derive horizontale de la barre pendant la montee
    # Mesuree par rapport aux chevilles, qui ne bougent pas de la tiree : un panoramique
    # de camera ou un lifter qui se decale ne comptent plus comme de la derive de barre.
    # C'est aussi ce qu'un juge regarde, la barre au-dessus du milieu du pied.
    cm_per_px = FEMUR_CM / femur_px
    vue = _vue_de_face(poses[lo:lk + 1])
    if vue < 0.6:                    # de face, un deplacement horizontal n'est pas de la
        xs = []                      # derive de barre : la trajectoire se juge de profil
        for f in poses[lo:lk + 1]:
            ank = (_px(f, "l_an")[0] + _px(f, "r_an")[0]) / 2
            xs.append(_px(f, f"{s}_wr")[0] - ank)
        if len(xs) >= 4:
            # ecart entre 5e et 95e centile plutot que max moins min : un seul repere
            # egare ne doit pas definir la trajectoire de barre
            span = float(np.percentile(xs, 95) - np.percentile(xs, 5)) * cm_per_px
            if span <= 60.0:
                out["wrist_horizontal_drift_cm"] = round(span, 1)
            else:
                out["wrist_drift_note"] = "bar path not measurable: pose too unstable"
    else:
        # cle absente plutot que nulle : le modele n'a pas a interpreter un null
        out["wrist_drift_note"] = "bar path not measurable: lifter filmed from the front"
    out["camera_view"] = ("front" if vue >= 0.6 else "three-quarter" if vue >= 0.3 else "side")

    # 4 et 5. angles au lockout
    kn_a = _angle(_px(f_lk, f"{s}_hip"), _px(f_lk, f"{s}_kn"), _px(f_lk, f"{s}_an"))
    hp_a = _angle(_px(f_lk, f"{s}_sh"), _px(f_lk, f"{s}_hip"), _px(f_lk, f"{s}_kn"))
    if not math.isnan(kn_a):
        out["lockout_knee_angle"] = round(kn_a, 1)
    if not math.isnan(hp_a):
        out["lockout_hip_angle"] = round(hp_a, 1)

    # 6. quelle articulation flechit en premier a la descente
    desc = [f for f in (extra or []) if f["t"] > f_lk["t"]] or [f for f in poses[lk + 1:]]
    cible = next((f for f in desc if f["t"] - f_lk["t"] >= 0.35), desc[-1] if desc else None)
    if cible is not None and not math.isnan(kn_a) and not math.isnan(hp_a):
        k2 = _angle(_px(cible, f"{s}_hip"), _px(cible, f"{s}_kn"), _px(cible, f"{s}_an"))
        h2 = _angle(_px(cible, f"{s}_sh"), _px(cible, f"{s}_hip"), _px(cible, f"{s}_kn"))
        if not math.isnan(k2) and not math.isnan(h2):
            dk, dh = kn_a - k2, hp_a - h2
            out["descent_initial_movement"] = (
                "Knees flexed before hips" if dk > 5 and dh < 2 else
                "Hips flexed before knees (good hinge)" if dh > 5 and dk < 2 else
                "Simultaneous flexion")
            out["descent_knee_delta_deg"] = round(dk, 1)
            out["descent_hip_delta_deg"] = round(dh, 1)

    # Si les articulations ne sont pas etendues sur la frame retenue, ce n'est pas un
    # verrouillage : le reperage des phases a echoue et tout le bloc serait trompeur.
    # Mieux vaut ne rien fournir au modele que des chiffres faux.
    if out.get("lockout_knee_angle", 0) < 120 or out.get("lockout_hip_angle", 0) < 120:
        return None

    out["_phases"] = dict(liftoff_s=round(f_lo["t"], 2), lockout_s=round(f_lk["t"], 2),
                          facing=facing, side=s)
    return out


# ------------------------------------------------------------------- point d'entree

def analyse(file_path: str, with_kinematics: bool = True) -> dict:
    """Analyse complete : variante du deadlift et cinematique.

    Ne leve jamais : en cas d'echec, renvoie {"ok": False, "raison": ...} et l'appelant
    se rabat sur le modele de langage.
    """
    t0 = time.time()
    try:
        n, fps = _probe(file_path)
        if n <= 0:
            return {"ok": False, "raison": "video illisible"}
        idx = np.linspace(n * 0.05, n * 0.95, N_CASCADE).astype(int)
        frames, fps = _read_frames(file_path, idx)
        if len(frames) < 6:
            return {"ok": False, "raison": "trop peu de frames lisibles"}
        poses = _detect(frames, fps)
        if len(poses) < 6:
            return {"ok": False, "raison": "aucune pose exploitable"}

        casc = _cascade(poses)

        kin = None
        if with_kinematics and _phases(poses) is None:
            # 30 frames sur un clip de 40 s laissent passer la tiree. On tente d'abord
            # deux fois plus dense, puis, en dernier recours seulement, un recentrage sur
            # la fenetre ou l'image bouge — ce recentrage peut se tromper de segment.
            essais = [np.linspace(n * 0.05, n * 0.95, N_CASCADE * 2).astype(int)]
            fenetre = _fenetre_de_mouvement(file_path, n)
            if fenetre:
                essais.append(np.linspace(fenetre[0], fenetre[1], N_CASCADE).astype(int))
            for idx2 in essais:
                fr2, _ = _read_frames(file_path, idx2)
                if len(fr2) < 12:
                    continue
                poses2 = _detect(fr2, fps)
                if _phases(poses2) is not None:
                    poses = poses2
                    break
        if with_kinematics:
            extra = []
            ph = _phases(poses)
            if ph is not None:                     # passe dense juste apres le lockout
                t_lk = poses[ph["lockout"]]["t"]
                lo_i, hi_i = int(t_lk * fps) + 1, int((t_lk + 1.2) * fps)
                more = [i for i in range(lo_i, min(hi_i, n)) if i not in set(idx.tolist())]
                if more:
                    step = max(1, len(more) // N_DESCENT)
                    sel = more[::step][:N_DESCENT]
                    fr2, _ = _read_frames(file_path, sel)
                    if fr2:
                        extra = _detect(fr2, fps)
            # Les frames denses de la descente participent aussi a la recherche des
            # phases : sans elles, un verrouillage tardif est vu trop tot et les angles
            # sont sous-estimes.
            fusion = poses
            if extra:
                vus = {p["i"] for p in poses}
                fusion = sorted(poses + [p for p in extra if p["i"] not in vus],
                                key=lambda p: p["t"])
            kin = _kinematics(fusion, extra)

        res = {"ok": casc is not None, "duree_s": round(time.time() - t0, 2),
               "frames_pose": len(poses)}
        if casc:
            res.update(casc)
        else:
            res["raison"] = "mesures de stance indisponibles"
        if kin:
            res["kinematics"] = kin
        return res
    except Exception as exc:                        # jamais bloquant pour la requete
        logger.warning("analyse de pose impossible: %s", exc)
        return {"ok": False, "raison": f"{type(exc).__name__}: {exc}"}
