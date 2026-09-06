"""Peut-on predire une note humaine a partir des seules mesures de pose ?

Protocole, ecrit avant de regarder les resultats — les pieges sont ceux deja payes sur
la cascade sumo (skill `sumo-stance-mediapipe`) :

* modele : UNE feature, deux seuils, monotone. Avec 40 clips et 3 classes, tout ce qui
  est plus riche apprend le bruit.
* deux lectures, toujours les deux affichees :
  - `guidee`  : les features candidates du critere sont declarees a l'avance d'apres le
                libelle du barreme (2 a 5 features). Seuls les seuils sont appris.
  - `libre`   : selection de la feature dans le pli, sur les ~35 disponibles. C'est la
                mesure honnete d'un modele qu'on laisserait choisir tout seul, et elle
                est systematiquement plus basse : la selection surapprend a elle seule.
* validation : leave-one-out imbriquee (seuils — et feature en mode libre — appris sur
  les n-1 clips restants uniquement).
* reference : predire la mediane d'apprentissage. Un modele qui ne la bat pas n'a rien.
* p-value : test de permutation (labels melanges, protocole rejoue). Il dit que le
  signal existe, pas que le seuil tient sur un lot neuf.
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
SCORER = os.path.join(os.path.dirname(ICI), "scorer")

# Features declarees a l'avance pour chaque critere, d'apres le libelle du barreme.
GUIDE = {
    "starting_position": ["setup_hip_ratio", "setup_bar_midfoot", "setup_shoulder_bar",
                          "setup_torso_deg", "setup_knee_deg"],
    "slack_pull_and_lat_engagement": ["pre_bar_rise", "pre_hip_drop", "pre_sh_drop",
                                      "pull_coude_p25_deg"],
    "slack_pull_and_wedge": ["pre_bar_rise", "pre_hip_drop", "pre_sh_drop",
                             "pull_coude_p25_deg"],
    "leg_drive_activation": ["pull_torso_delta_t1", "pull_hip_vs_sh_t1",
                             "pull_knee_share_t1", "pull_torso_min"],
    "leg_drive_and_floor_spread": ["pull_torso_delta_t1", "pull_hip_vs_sh_t1",
                                   "pull_knee_share_t1", "pull_torso_min"],
    "hip_hinge_mechanics": ["pull_sync_ecart_max", "pull_sync_ecart_moy",
                            "pull_sync_signe", "pull_hip_share_t1"],
    "hip_opening_and_knee_tracking": ["pull_sync_ecart_max", "pull_sync_signe",
                                      "setup_knee_deg"],
    "core_bracing_and_spine_neutrality": ["tronc_raccourcissement", "tronc_long_setup",
                                          "pull_torso_delta_t1", "pull_torso_min"],
    "bar_path_and_proximity": ["pull_bar_drift", "pull_bar_max_forward",
                               "pull_bar_gap_knee", "setup_bar_midfoot"],
    "lockout_execution": ["lock_knee_deg", "lock_hip_deg", "lock_lean_back",
                          "lock_temps_dernier_10pct", "lock_desync_fin", "pull_stall"],
    "eccentric_control_and_descent": ["desc_vitesse_max", "desc_duree_mi_course",
                                      "desc_ratio_montee", "desc_hinge_first",
                                      "desc_knee_delta"],
}

# Diagnostics et proprietes de prise de vue : ce ne sont pas des mesures de technique,
# elles n'ont rien a faire dans les features candidates.
EXCLUES = {"clip", "variante_pose", "origine", "phases_ok", "n_frames", "vue_side",
           "vue_face", "course_barre", "dans_cadre", "vis_moy_pull", "vis_min_pull",
           "phases_ecart_prod_s", "n_reps"}


def mesurable(f):
    """La fenetre de tiree est-elle credible ?

    Une barre qui monte d'a peu pres une longueur de jambe, un sujet dans le cadre et
    des reperes vus : sans ces trois conditions les features sont calculees proprement
    sur une fenetre fausse, ce qui est pire qu'une absence de mesure.
    """
    return (f.get("phases_ok")
            and 0.5 <= (f.get("course_barre") or 0) <= 1.2
            and (f.get("dans_cadre") or 0) >= 0.5
            and (f.get("vis_moy_pull") or 0) >= 0.5)


# ------------------------------------------------------------------ modele

def _cuts(x, y):
    """Deux seuils monotones minimisant la MAE d'apprentissage.

    Forme fermee plutot que double boucle : avec c1 <= c2 les indicatrices se
    telescopent (cout = K + u[a] + v[b]), donc la grille entiere des couples de seuils
    est un simple produit exterieur. Sans ca le test de permutation coute des heures.
    """
    ok = ~np.isnan(x)
    xv, yv = x[ok], y[ok]
    if len(xv) < 6 or len(np.unique(xv)) < 4:
        return None
    m = len(yv)
    C = np.abs(np.arange(1, 4)[None, :] - yv[:, None])          # cout par classe
    best = None
    for sens in (1.0, -1.0):
        z = xv * sens
        zq = np.unique(np.percentile(z, np.linspace(5, 95, 19)))
        A = (z[:, None] >= zq[None, :]).astype(float)           # (m, q)
        M = (C[:, 0].sum() + ((C[:, 1] - C[:, 0]) @ A)[:, None]
             + ((C[:, 2] - C[:, 1]) @ A)[None, :]) / m
        sa = A.sum(0)
        n1, n2, n3 = m - sa[:, None], sa[:, None] - sa[None, :], sa[None, :]
        distinct = (n1 > 0).astype(float) + (n2 > 0) + (n3 > 0)
        # a MAE egale on prefere le decoupage qui sort vraiment trois classes : un
        # modele degenere en une seule classe passe le test de MAE sans rien predire
        M = M + 1e-3 * (3.0 - distinct)
        q = len(zq)
        iu = np.triu_indices(q)
        k = int(np.argmin(M[iu]))
        a, b = int(iu[0][k]), int(iu[1][k])
        if best is None or M[a, b] < best[0]:
            best = (float(M[a, b]), sens, float(zq[a]), float(zq[b]))
    return None if best is None else (best[1], best[2], best[3], best[0])


def _predire(modele, x, mediane):
    if modele is None or x is None or np.isnan(x):
        return mediane
    sens, c1, c2 = modele[0], modele[1], modele[2]
    z = x * sens
    return 1 if z < c1 else (2 if z < c2 else 3)


def _loo(X, y, feats, mediane_globale):
    """LOO imbriquee : seuils — et feature en mode libre — appris hors du clip teste."""
    n = len(y)
    preds, choisies = np.zeros(n), []
    idx = np.arange(n)
    for i in range(n):
        tr = idx != i
        ytr = y[tr]
        med = int(np.round(np.median(ytr)))
        best = None
        for k in range(X.shape[1]):
            m = _cuts(X[tr, k], ytr)
            if m is None:
                continue
            # penalise les features absentes chez beaucoup de clips : leur MAE
            # d'apprentissage ne porte que sur le sous-ensemble ou elles existent
            couv = float(np.mean(~np.isnan(X[tr, k])))
            score = m[3] * couv + (1.0 - couv) * float(np.mean(np.abs(med - ytr)))
            if best is None or score < best[0]:
                best = (score, k, m)
        if best is None:
            preds[i], f_i = med, None
        else:
            _, k, m = best
            preds[i] = _predire(m, X[i, k], med)
            f_i = feats[k]
        choisies.append(f_i)
    return preds, choisies


def _constante(y):
    "La note fixe qui minimise la MAE sur `y`, a egalite la plus frequente."
    return min((float(np.mean(np.abs(c - y))), -int(np.sum(y == c)), c)
               for c in (1, 2, 3))[2]


def _baseline(y):
    """Reference : la MEILLEURE note constante, choisie sur tout le jeu.

    Surtout pas la mediane d'apprentissage en LOO. Quand les classes sont a egalite,
    retirer un 3 fait baisser la mediane et retirer un 1 la fait monter : la reference
    devient anti-correlee avec le point retire et son exactitude tombe a zero, ce qui
    est impossible pour un predicteur constant. Elle gonflait la MAE de reference de
    0,6 a 1,2 sur deux criteres et fabriquait un gain la ou il n'y en a pas.

    Choisir la constante sur tout le jeu la rend legerement optimiste — c'est
    volontaire : le modele doit battre la meilleure constante possible, pas une
    reference commode.
    """
    return np.full(len(y), _constante(y), dtype=float)


def evaluer(X, y, feats, n_perm=100, graine=0):
    if X.shape[1] == 0 or len(y) < 12:
        return None
    p, ch = _loo(X, y, feats, _constante(y))
    b = _baseline(y)
    mae, mae_b = float(np.mean(np.abs(p - y))), float(np.mean(np.abs(b - y)))
    from collections import Counter
    if mae >= mae_b:
        # aucun gain sur la reference : la p-value ne dirait rien de plus, et les
        # permutations coutent une minute par critere
        return dict(n=len(y), mae=round(mae, 3), mae_baseline=round(mae_b, 3),
                    gain=round(mae_b - mae, 3),
                    exact=round(float(np.mean(p == y)), 3),
                    exact_baseline=round(float(np.mean(b == y)), 3), p_perm=None,
                    feature=Counter([c for c in ch if c]).most_common(3),
                    preds=p.tolist(), vrai=y.tolist())
    rng = np.random.default_rng(graine)
    mieux = 0
    for _ in range(n_perm):
        ys = rng.permutation(y)
        pp, _ = _loo(X, ys, feats, _constante(ys))
        if float(np.mean(np.abs(pp - ys))) <= mae:
            mieux += 1
    return dict(n=len(y), mae=round(mae, 3), mae_baseline=round(mae_b, 3),
                gain=round(mae_b - mae, 3),
                exact=round(float(np.mean(p == y)), 3),
                exact_baseline=round(float(np.mean(b == y)), 3),
                p_perm=round((mieux + 1) / (n_perm + 1), 4),
                feature=Counter([c for c in ch if c]).most_common(3),
                preds=p.tolist(), vrai=y.tolist())


# ------------------------------------------------------------------ donnees

def jeu(critere, F, H, seulement_profil=False, seulement_mesurable=False):
    noms, lignes, ys = [], [], []
    for clip, h in H.items():
        s = (h.get("scores") or {}).get(critere)
        f = F.get(clip[:-4] if clip.endswith(".mp4") else clip) or F.get(clip)
        if s not in (1, 2, 3) or not f or not f.get("phases_ok"):
            continue
        if seulement_mesurable and not mesurable(f):
            continue
        if seulement_profil and not f.get("vue_side"):
            continue
        noms.append(clip)
        lignes.append(f)
        ys.append(s)
    return noms, lignes, np.array(ys, dtype=float)


def llm_mae(critere, noms, y, fichier="llm_scores_persona_last.json"):
    """MAE du pipeline Gemini sur exactement les memes clips.

    Sans ce point de comparaison, une MAE de 0,55 ne veut rien dire. Avec lui, la
    question devient : une regle a deux seuils sur une mesure de pose fait-elle aussi
    bien que flash-lite, qui a vu la video entiere ?
    """
    chemin = os.path.join(SCORER, fichier)
    if not os.path.exists(chemin):
        return None
    D = json.load(open(chemin))
    p, v = [], []
    for n, vrai in zip(noms, y):
        c = ((D.get(n) or {}).get("criteria") or {}).get(critere) or {}
        s = c.get("score")
        if s in (1, 2, 3):
            p.append(s)
            v.append(vrai)
    if len(p) < 8:
        return None
    p, v = np.array(p, dtype=float), np.array(v, dtype=float)
    return dict(n=len(p), mae=round(float(np.mean(np.abs(p - v))), 3),
                exact=round(float(np.mean(p == v)), 3))


def niveau_clip(H):
    "Note moyenne du clip sur ses criteres notes : la cible « niveau general »."
    out = {}
    for clip, h in H.items():
        v = [s for s in (h.get("scores") or {}).values() if s in (1, 2, 3)]
        if v:
            out[clip] = float(np.mean(v))
    return out


def matrice(lignes, feats):
    return np.array([[float(l.get(f, np.nan)) if l.get(f) is not None else np.nan
                      for f in feats] for l in lignes])


def main():
    F = json.load(open(os.path.join(ICI, "features.json")))
    H = json.load(open(os.path.join(SCORER, "human_labels.json")))
    toutes = sorted({k for v in F.values() for k in v} - EXCLUES)
    profil_seul = "--profil" in sys.argv
    mes_seul = "--mesurable" in sys.argv

    print(f"features disponibles : {len(toutes)}")
    print(f"clips avec phases    : {sum(1 for v in F.values() if v.get('phases_ok'))}/{len(F)}")
    if profil_seul:
        print("RESTRICTION : clips de profil uniquement")
    if mes_seul:
        print(f"RESTRICTION : fenetre de tiree credible uniquement "
              f"({sum(1 for v in F.values() if mesurable(v))}/{len(F)} clips)")
    print()
    lignes_md = []
    for crit, guide in GUIDE.items():
        noms, lignes, y = jeu(crit, F, H, profil_seul, mes_seul)
        if len(y) < 12:
            print(f"== {crit}: {len(y)} clips notes, trop peu\n")
            continue
        print(f"== {crit}  (n={len(y)}, classes {dict(zip(*np.unique(y, return_counts=True)))})")
        res = {}
        for mode, feats in (("guidee", [f for f in guide if f in toutes]),
                            ("libre", toutes)):
            X = matrice(lignes, feats)
            garde = [j for j in range(X.shape[1])
                     if np.mean(~np.isnan(X[:, j])) >= 0.6]
            r = evaluer(X[:, garde], y, [feats[j] for j in garde])
            res[mode] = r
            if r is None:
                print(f"   {mode:7s} : indisponible")
                continue
            pp = "p=%.3f" % r["p_perm"] if r["p_perm"] is not None else "p n/a"
            print(f"   {mode:7s} : MAE {r['mae']:.3f} vs {r['mae_baseline']:.3f} baseline"
                  f"  (gain {r['gain']:+.3f})   exact {r['exact']:.0%} vs {r['exact_baseline']:.0%}"
                  f"   {pp}")
            print(f"             features retenues : {r['feature']}")
        ll = llm_mae(crit, noms, y)
        if ll:
            print(f"   {'gemini':7s} : MAE {ll['mae']:.3f}                        "
                  f"        exact {ll['exact']:.0%}                (n={ll['n']}, flash-lite)")
        res["gemini"] = ll
        lignes_md.append((crit, res))
        print()
    # cible supplementaire : le niveau general du clip, celui que le halo rend lisible
    NIV = niveau_clip(H)
    noms, lignes, _ = jeu("starting_position", F, H, profil_seul, mes_seul)
    y = np.array([NIV[n] for n in noms])
    X = matrice(lignes, toutes)
    garde = [j for j in range(X.shape[1]) if np.mean(~np.isnan(X[:, j])) >= 0.6]
    r = evaluer(X[:, garde], y, [toutes[j] for j in garde])
    if r:
        print(f"== NIVEAU GENERAL DU CLIP (moyenne des criteres humains, n={len(y)})")
        pp = "p=%.3f" % r["p_perm"] if r["p_perm"] is not None else "p n/a"
        print(f"   libre   : MAE {r['mae']:.3f} vs {r['mae_baseline']:.3f} baseline "
              f"(gain {r['gain']:+.3f})   {pp}")
        print(f"             features retenues : {r['feature']}\n")
        lignes_md.append(("niveau_clip", {"libre": r}))

    json.dump({c: r for c, r in lignes_md}, open(os.path.join(
        ICI, "resultats%s%s.json" % ("_profil" if profil_seul else "",
                                     "_mesurable" if mes_seul else "")), "w"), indent=1)


if __name__ == "__main__":
    main()
