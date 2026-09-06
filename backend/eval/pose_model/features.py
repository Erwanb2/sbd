"""Features mecaniques par clip, calculees sur les landmarks dumpes.

Chaque feature est ecrite en regardant le libelle du critere qu'elle vise dans
`schemas.py` — pas en balayant tout ce qui est calculable. Le balayage a deja ete paye
une fois sur la cascade sumo (voir la skill `sumo-stance-mediapipe`) : avec assez de
features, une separation parfaite sur 40 clips est le comportement attendu, pas un
resultat.

Convention : `vue_*` decrit la prise de vue, `setup_*` l'instant du decollage, `pull_*`
la tiree, `lock_*` le verrouillage, `desc_*` la descente. Les features marquees
PROFIL_SEUL n'ont de sens que filmees de cote et valent NaN ailleurs.
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pose_analysis as pa                                          # noqa: E402

L = pa.L
DOSSIER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "extracted_frames", "landmarks")

PROFIL_SEUL = {"setup_bar_midfoot", "setup_shoulder_bar", "pull_bar_drift",
               "pull_bar_max_forward", "pull_bar_gap_knee", "lock_lean_back",
               "setup_torso_deg", "pull_torso_delta_t1", "pull_torso_min"}


# ------------------------------------------------------------------ chargement

def charger(clip: str):
    d = np.load(os.path.join(DOSSIER, clip + ".npz"), allow_pickle=False)
    w, h, fps, n = d["meta"]
    poses = [dict(i=int(i), t=float(t), w=int(w), h=int(h), im=im, wd=wd)
             for i, t, im, wd in zip(d["i"], d["t"], d["im"], d["wd"])]
    return poses, dict(w=int(w), h=int(h), fps=float(fps), n=int(n),
                       cascade=d["cascade"], variante=str(d["variante"]),
                       origine=str(d["origine"]), phases_30=d["phases"])


# ------------------------------------------------------------------ geometrie

def _pt(f, k):
    "Repere en pixels (x corrige du ratio d'image)."
    return np.array([f["im"][L[k], 0] * f["w"], f["im"][L[k], 1] * f["h"]])


def _vis(f, k):
    return float(f["im"][L[k], 3])


def _angle_horizontal(a, b):
    "Angle en degres de la droite a->b par rapport a l'horizontale, dans [0, 90]."
    v = b - a
    if np.linalg.norm(v) < 1e-6:
        return float("nan")
    return float(abs(np.degrees(np.arctan2(v[1], v[0]))) % 180.0)


def _echelle_frame(f):
    """Longueur de jambe en pixels, cote le plus visible : l'unite de la frame.

    Une hauteur de barre en pixels bruts n'est pas comparable d'une image a l'autre :
    un lifter qui recule apres avoir lache la barre remonte dans le cadre et fabrique un
    faux verrouillage. Cuisse + tibia plutot que femur seul : quand la cuisse pointe vers
    la camera elle se raccourcit, le tibia beaucoup moins.
    """
    vals = []
    for c in ("l", "r"):
        v = min(_vis(f, f"{c}_hip"), _vis(f, f"{c}_kn"), _vis(f, f"{c}_an"))
        d = (np.linalg.norm(_pt(f, f"{c}_hip") - _pt(f, f"{c}_kn"))
             + np.linalg.norm(_pt(f, f"{c}_kn") - _pt(f, f"{c}_an")))
        vals.append((v, float(d)))
    return max(vals)[1]


def _serie(poses, s):
    """Angles hanche / genou / tronc et hauteur de barre, image par image."""
    hip, knee, torso, bar, sh_y, hip_y = [], [], [], [], [], []
    for f in poses:
        hip.append(pa._angle(_pt(f, f"{s}_sh"), _pt(f, f"{s}_hip"), _pt(f, f"{s}_kn")))
        knee.append(pa._angle(_pt(f, f"{s}_hip"), _pt(f, f"{s}_kn"), _pt(f, f"{s}_an")))
        v = _pt(f, f"{s}_sh") - _pt(f, f"{s}_hip")
        torso.append(float(abs(np.degrees(np.arctan2(-v[1], abs(v[0]) + 1e-9)))))
        # Hauteurs prises sur les reperes MONDE de MediaPipe, pas sur l'image : ils
        # sont metriques et independants de la distance camera. En pixels normalises
        # par la jambe, la cuisse raccourcie du setup gonflait le rapport et la station
        # debout devenait indiscernable de la position de depart.
        w = lambda k: float(f["wd"][L[k], 1])
        sol = (w("l_an") + w("r_an")) / 2
        bar.append(sol - (w("l_wr") + w("r_wr")) / 2)
        sh_y.append(sol - (w("l_sh") + w("r_sh")) / 2)
        hip_y.append(sol - (w("l_hip") + w("r_hip")) / 2)
    # longueur de jambe du sujet, en metres : rend les hauteurs sans dimension
    jambe = max(float(np.percentile(hip_y, 90)), 0.1)
    return (np.array(hip), np.array(knee), np.array(torso),
            np.array(bar) / jambe, np.array(sh_y) / jambe, np.array(hip_y) / jambe)


def _lisse(v, k=3):
    if len(v) < k:
        return v
    pad = np.r_[v[0], v, v[-1]]
    return np.convolve(pad, np.ones(k) / k, mode="same")[1:-1]


def _median3(v):
    "Filtre median a trois points : une frame ou un repere saute ne fait plus un pic."
    if len(v) < 3:
        return np.asarray(v, dtype=float)
    pad = np.r_[v[0], v, v[-1]]
    return np.array([np.median(pad[i:i + 3]) for i in range(len(v))])


def _zigzag(b, seuil):
    """Extremes alternes du signal, ceux dont l'aller-retour depasse `seuil`.

    Sans ca, la plus forte montee d'un clip de cinq repetitions va du creux de la
    premiere au sommet de la derniere : quinze secondes de « tiree ».
    """
    piv, i_min, i_max, sens = [], 0, 0, 0
    for j in range(1, len(b)):
        # tant que le sens n'est pas etabli, les deux extremes courent en parallele :
        # c'est le premier des deux a franchir le seuil qui donne la direction
        if sens >= 0 and b[j] > b[i_max]:
            i_max = j
        if sens <= 0 and b[j] < b[i_min]:
            i_min = j
        if sens <= 0 and b[j] - b[i_min] >= seuil:
            piv.append((i_min, "min"))
            sens, i_max = 1, j
        elif sens >= 0 and b[i_max] - b[j] >= seuil:
            piv.append((i_max, "max"))
            sens, i_min = -1, j
    piv.append((i_max, "max") if sens > 0 else (i_min, "min"))
    return piv


def _phases_barre(bar, tenue=None):
    """Decollage et verrouillage lus sur la hauteur de barre, pas sur les angles.

    L'axe vertical de l'image est le seul qui survit a n'importe quel azimut de camera :
    une barre qui monte, monte, qu'on filme de face, de trois quarts ou de profil. Les
    angles hanche/genou, eux, ne valent qu'en vue sagittale — c'est ce qui rendait la
    fenetre de `pose_analysis._phases` fausse sur les clips de face.

    On prend la plus forte montee d'un creux vers le sommet qui le suit, puis on
    resserre sur les 5 % - 95 % de sa course : le temps ou le lifter reste immobile la
    barre au sol ne fait pas partie de la tiree.
    """
    b = _lisse(_median3(np.asarray(bar, dtype=float)))
    if len(b) < 6:
        return None
    etendue = float(np.ptp(b))
    if etendue <= 1e-6:
        return None
    # Les mains ne montent jamais au-dessus des hanches pendant un souleve de terre :
    # au-dela, la barre est lachee (chalk, celebration, remise en place) et le signal
    # de poignet ne dit plus rien de la barre. Ces frames sont retirees de la recherche,
    # sinon le « verrouillage » tombe sur un lifter debout les mains en l'air.
    if tenue is None:
        tenue = np.ones(len(b), dtype=bool)
    segments, deb = [], None
    for j in range(len(b)):
        if tenue[j] and deb is None:
            deb = j
        elif not tenue[j] and deb is not None:
            segments.append((deb, j))
            deb = None
    if deb is not None:
        segments.append((deb, len(b)))
    montees = []
    for a, z in segments:
        if z - a < 5:
            continue
        piv = _zigzag(b[a:z], 0.25 * etendue)
        montees += [(b[a + piv[k + 1][0]] - b[a + piv[k][0]], a + piv[k][0], a + piv[k + 1][0])
                    for k in range(len(piv) - 1)
                    if piv[k][1] == "min" and piv[k + 1][1] == "max"]
    if not montees:
        return None
    course, lo, lk = max(montees)
    bas = b[lo]
    # premier passage au-dessus de 95 % de la course, dernier en dessous de 5 % :
    # cherche par seuil et non de proche en proche, sinon un creux d'une image au
    # milieu du plateau arrete la remontee et le verrouillage tombe deux secondes trop
    # tard, sur un lifter qui a deja repose la barre
    haut = np.where(b[lo:lk + 1] >= bas + 0.95 * course)[0]
    if len(haut):
        lk = lo + int(haut[0])
    bas_idx = np.where(b[lo:lk + 1] <= bas + 0.05 * course)[0]
    if len(bas_idx):
        lo = lo + int(bas_idx[-1])
    return dict(liftoff=lo, lockout=lk, course=course, n_reps=sum(
        1 for k in range(len(piv) - 1)
        if piv[k][1] == "min" and b[piv[k + 1][0]] - b[piv[k][0]] > 0.6 * course))


def _echelle(poses, s, lo, lk):
    "Longueur de femur en pixels, mediane sur la tiree : l'unite de toutes les distances."
    v = [float(np.linalg.norm(_pt(f, f"{s}_hip") - _pt(f, f"{s}_kn")))
         for f in poses[lo:lk + 1]]
    v = [x for x in v if x > 1.0]
    return float(np.median(v)) if v else float("nan")


def _interp(x, y, cible):
    "Valeur de y quand x franchit `cible` (x suppose croissant en gros)."
    idx = int(np.argmax(x >= cible)) if np.any(x >= cible) else len(x) - 1
    return int(idx)


# ------------------------------------------------------------------ features

def phases_clip(poses):
    """Cote camera, series temporelles et fenetre de tiree. Chemin unique.

    Les outils de verification passent par ici : une fenetre verifiee aux images doit
    etre celle que les features utilisent, sinon la verification ne verifie rien.
    """
    s = pa._side_clip(poses)
    hip, knee, torso, bar, sh_y, hip_y = _serie(poses, s)
    ph = _phases_barre(bar, tenue=_median3(bar) <= _median3(hip_y) + 0.05)
    return s, (hip, knee, torso, bar, sh_y, hip_y), ph


def mesures(clip: str) -> dict:
    poses, meta = charger(clip)
    out = {"clip": clip, "variante_pose": meta["variante"], "origine": meta["origine"],
           "n_frames": len(poses)}

    t = np.array([f["t"] for f in poses])
    s, (hip, knee, torso, bar, sh_y, hip_y), ph = phases_clip(poses)
    ref = pa._phases(poses)                    # fenetre de production, pour comparaison
    if ph is None:
        out["phases_ok"] = 0
        return out
    out["phases_ok"] = 1
    lo, lk = ph["liftoff"], ph["lockout"]
    if ref is not None:
        out["phases_ecart_prod_s"] = round(float(abs(t[lo] - t[ref["liftoff"]])
                                                 + abs(t[lk] - t[ref["lockout"]])), 2)
    femur = _echelle(poses, s, lo, lk)
    facing = pa._facing(poses[lk])
    sens = 1.0 if facing == "right" else -1.0

    vue = pa._vue_de_face(poses[lo:lk + 1])
    out["vue_face"] = round(vue, 3)
    de_profil = vue < 0.6                       # face exclue
    out["vue_side"] = int(vue < 0.3)            # profil strict
    out["pull_duree_s"] = round(float(t[lk] - t[lo]), 3)
    out["n_reps"] = int(ph.get("n_reps", 1))
    out["vis_min_pull"] = round(float(np.median(
        [min(_vis(f, f"{s}_an"), _vis(f, f"{s}_kn"), _vis(f, f"{s}_hip"))
         for f in poses[lo:lk + 1]])), 3)
    # Trois garde-fous : sans eux, un clip ou MediaPipe decroche produit des features
    # parfaitement calculees et parfaitement fausses.
    # 1. la barre doit monter d'a peu pres une longueur de jambe sur un souleve de terre
    out["course_barre"] = round(float(bar[lk] - bar[lo]), 3)
    # 2. le sujet doit tenir dans le cadre
    dedans = []
    for f in poses[lo:lk + 1]:
        xy = [f["im"][L[k], :2] for k in ("l_sh", "r_sh", "l_an", "r_an", "l_wr", "r_wr")]
        dedans.append(all(0.01 < a < 0.99 and 0.01 < b < 0.99 for a, b in xy))
    out["dans_cadre"] = round(float(np.mean(dedans)), 3)
    # 3. visibilite moyenne des reperes qui portent toutes les mesures
    out["vis_moy_pull"] = round(float(np.mean(
        [np.mean([_vis(f, k) for k in ("l_sh", "r_sh", "l_hip", "r_hip", "l_kn", "r_kn",
                                       "l_an", "r_an")]) for f in poses[lo:lk + 1]])), 3)

    # ---- setup : « barre au milieu du pied, hanches entre genoux et epaules »
    f0 = poses[lo]
    sy, hy, ky = _pt(f0, f"{s}_sh")[1], _pt(f0, f"{s}_hip")[1], _pt(f0, f"{s}_kn")[1]
    if abs(ky - sy) > 1e-6:
        out["setup_hip_ratio"] = round(float((hy - sy) / (ky - sy)), 3)
    if femur > 1.0:
        wr0 = (_pt(f0, "l_wr") + _pt(f0, "r_wr")) / 2
        pied = (_pt(f0, f"{s}_heel") + _pt(f0, f"{s}_toe")) / 2
        out["setup_bar_midfoot"] = round(float((wr0[0] - pied[0]) * sens / femur), 3)
        out["setup_shoulder_bar"] = round(
            float((_pt(f0, f"{s}_sh")[0] - wr0[0]) * sens / femur), 3)
    out["setup_knee_deg"] = round(float(knee[lo]), 1)
    out["setup_hip_deg"] = round(float(hip[lo]), 1)
    out["setup_torso_deg"] = round(float(torso[lo]), 1)

    # ---- tiree : progression normalisee de la barre, du sol au verrouillage
    course = bar[lk] - bar[lo]
    if abs(course) > 1e-6:
        prog = (bar[lo:lk + 1] - bar[lo]) / course
        prog = np.maximum.accumulate(np.clip(prog, 0, 1.2))          # monotone
        i_t1 = lo + _interp(prog, prog, 0.33)                        # premier tiers
        i_t2 = lo + _interp(prog, prog, 0.66)

        # « les hanches partent en premier » : angle du tronc perdu sur le premier tiers
        out["pull_torso_delta_t1"] = round(float(torso[i_t1] - torso[lo]), 1)
        out["pull_torso_min"] = round(float(np.min(torso[lo:lk + 1]) - torso[lo]), 1)
        # montee des hanches rapportee a celle des epaules sur le premier tiers
        d_sh = sh_y[i_t1] - sh_y[lo]
        d_hp = hip_y[i_t1] - hip_y[lo]
        if abs(d_sh) + abs(d_hp) > 1e-6:
            out["pull_hip_vs_sh_t1"] = round(float(d_hp / (abs(d_sh) + 1e-6)), 3)
        # part de l'extension du genou consommee sur le premier tiers de la barre
        ext_k = knee[lk] - knee[lo]
        ext_h = hip[lk] - hip[lo]
        if ext_k > 5:
            out["pull_knee_share_t1"] = round(float((knee[i_t1] - knee[lo]) / ext_k), 3)
        if ext_h > 5:
            out["pull_hip_share_t1"] = round(float((hip[i_t1] - hip[lo]) / ext_h), 3)
        # « hanches et genoux etendent ensemble » : ecart max des deux progressions
        if ext_k > 5 and ext_h > 5:
            pk = np.clip((knee[lo:lk + 1] - knee[lo]) / ext_k, 0, 1)
            phh = np.clip((hip[lo:lk + 1] - hip[lo]) / ext_h, 0, 1)
            out["pull_sync_ecart_max"] = round(float(np.max(np.abs(pk - phh))), 3)
            out["pull_sync_ecart_moy"] = round(float(np.mean(np.abs(pk - phh))), 3)
            out["pull_sync_signe"] = round(float(np.mean(phh - pk)), 3)
        # regularite de la vitesse de barre : a-coup, hitch, stall
        dt = np.diff(t[lo:lk + 1])
        v = np.diff(bar[lo:lk + 1]) / np.maximum(dt, 1e-6)
        if len(v) >= 4 and np.mean(v) > 1e-6:
            out["pull_vitesse_cv"] = round(float(np.std(v) / abs(np.mean(v))), 3)
            out["pull_stall"] = round(float(np.sum(v < 0.15 * np.mean(v)) / len(v)), 3)
        # trajectoire de barre : derive horizontale rapportee aux chevilles PROFIL_SEUL
        if femur > 1.0:
            xs = np.array([(_pt(f, "l_wr")[0] + _pt(f, "r_wr")[0]) / 2
                           - (_pt(f, "l_an")[0] + _pt(f, "r_an")[0]) / 2
                           for f in poses[lo:lk + 1]]) * sens / femur
            out["pull_bar_drift"] = round(float(np.percentile(xs, 95) - np.percentile(xs, 5)), 3)
            out["pull_bar_max_forward"] = round(float(np.max(xs) - xs[0]), 3)
            h_genou = (_pt(f0, "l_an")[1] + _pt(f0, "r_an")[1]) / 2 - _pt(f0, f"{s}_kn")[1]
            i_kn = lo + _interp(bar[lo:lk + 1], bar[lo:lk + 1],
                                float(h_genou / max(_echelle_frame(f0), 1.0)))
            out["pull_bar_gap_knee"] = round(float(abs(
                (_pt(poses[i_kn], "l_wr")[0] + _pt(poses[i_kn], "r_wr")[0]) / 2
                - _pt(poses[i_kn], f"{s}_kn")[0]) / femur), 3)

    # ---- avant le decollage : slack pull, mise en tension
    av = [j for j in range(lo) if t[lo] - t[j] <= 0.8]
    if len(av) >= 3 and femur > 1.0:
        out["pre_bar_rise"] = round(float(bar[lo] - np.min(bar[av])), 3)
        out["pre_hip_drop"] = round(float(np.max(hip_y[av]) - hip_y[lo]), 3)
        out["pre_sh_drop"] = round(float(np.max(sh_y[av]) - sh_y[lo]), 3)
    coudes = []
    for f in poses[lo:lk + 1]:
        vals = [pa._angle(_pt(f, f"{c}_sh"), _pt(f, f"{c}_el"), _pt(f, f"{c}_wr"))
                for c in ("l", "r")
                if _vis(f, f"{c}_el") > 0.6 and _vis(f, f"{c}_wr") > 0.6]
        vals = [v for v in vals if not np.isnan(v)]
        if vals:
            coudes.append(max(vals))     # le bras occulte s'effondre : on garde l'autre
    if len(coudes) >= 4:
        out["pull_coude_p25_deg"] = round(float(np.percentile(coudes, 25)), 1)

    # ---- verrouillage
    out["lock_knee_deg"] = round(float(knee[lk]), 1)
    out["lock_hip_deg"] = round(float(hip[lk]), 1)
    v_lock = _pt(poses[lk], f"{s}_sh") - _pt(poses[lk], f"{s}_hip")
    out["lock_lean_back"] = round(float(np.degrees(np.arctan2(v_lock[0] * sens, -v_lock[1]))), 1)
    ext = (hip + knee) / 2.0
    haut = float(ext[lk])
    seuil = ext[lo] + 0.9 * (haut - ext[lo])
    j = lo + _interp(ext[lo:lk + 1], ext[lo:lk + 1], seuil)
    out["lock_temps_dernier_10pct"] = round(float((t[lk] - t[j]) / max(t[lk] - t[lo], 1e-6)), 3)
    # desynchronisation hanche / genou en fin de tiree
    if knee[lk] - knee[lo] > 5 and hip[lk] - hip[lo] > 5:
        pk = np.clip((knee[lo:lk + 1] - knee[lo]) / (knee[lk] - knee[lo]), 0, 1)
        phh = np.clip((hip[lo:lk + 1] - hip[lo]) / (hip[lk] - hip[lo]), 0, 1)
        out["lock_desync_fin"] = round(float(abs(
            _interp(pk, pk, 0.95) - _interp(phh, phh, 0.95)) / max(lk - lo, 1)), 3)

    # ---- descente
    ap = [j for j in range(lk + 1, len(poses)) if t[j] - t[lk] <= 2.0]
    if len(ap) >= 3 and femur > 1.0:
        b = bar[ap] - bar[lk]
        chute = float(-np.min(b))
        out["desc_amplitude"] = round(chute, 3)
        vd = np.diff(bar[ap]) / np.maximum(np.diff(t[ap]), 1e-6)
        out["desc_vitesse_max"] = round(float(-np.min(vd)) if len(vd) else float("nan"), 3)
        if abs(course) > 1e-6:
            # duree pour redescendre la moitie de la course de la tiree
            cible = bar[lk] - 0.5 * course
            k = next((j for j in ap if bar[j] <= cible), None)
            out["desc_duree_mi_course"] = round(
                float(t[k] - t[lk]) if k else 2.0, 3)
            if out["pull_duree_s"] > 0:
                out["desc_ratio_montee"] = round(
                    out["desc_duree_mi_course"] / out["pull_duree_s"], 3)
        cible_f = next((f for f in poses[lk + 1:] if f["t"] - t[lk] >= 0.35), None)
        if cible_f is not None:
            k2 = pa._angle(_pt(cible_f, f"{s}_hip"), _pt(cible_f, f"{s}_kn"), _pt(cible_f, f"{s}_an"))
            h2 = pa._angle(_pt(cible_f, f"{s}_sh"), _pt(cible_f, f"{s}_hip"), _pt(cible_f, f"{s}_kn"))
            if not np.isnan(k2) and not np.isnan(h2):
                out["desc_knee_delta"] = round(float(knee[lk] - k2), 1)
                out["desc_hip_delta"] = round(float(hip[lk] - h2), 1)
                out["desc_hinge_first"] = round(float((hip[lk] - h2) - (knee[lk] - k2)), 1)

    # ---- tronc : seul indice de dos disponible, la longueur projetee epaule-hanche
    if femur > 1.0:
        tr = np.array([float(np.linalg.norm(_pt(f, f"{s}_sh") - _pt(f, f"{s}_hip")))
                       for f in poses[lo:lk + 1]]) / femur
        out["tronc_long_setup"] = round(float(tr[0]), 3)
        out["tronc_raccourcissement"] = round(float((np.max(tr) - np.min(tr)) / np.max(tr)), 3)

    if not de_profil:
        for k in PROFIL_SEUL:
            out.pop(k, None)
    return out


def toutes(clips=None) -> dict:
    clips = clips or sorted(f[:-4] for f in os.listdir(DOSSIER) if f.endswith(".npz"))
    res = {}
    for c in clips:
        try:
            res[c] = mesures(c)
        except Exception as exc:
            res[c] = {"clip": c, "erreur": f"{type(exc).__name__}: {exc}"}
    return res


if __name__ == "__main__":
    import json
    r = toutes()
    cible = os.path.join(os.path.dirname(os.path.abspath(__file__)), "features.json")
    json.dump(r, open(cible, "w"), indent=1, ensure_ascii=False, sort_keys=True)
    ok = sum(1 for v in r.values() if v.get("phases_ok"))
    print(f"{len(r)} clips, {ok} avec phases, -> {cible}")
