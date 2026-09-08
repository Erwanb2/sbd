"""Des indicateurs observes aux resultats montres a l'utilisateur.

C'est la couche qui NOTE. Elle ne parle ni a MediaPipe ni au modele : elle recoit d'un
cote les mesures de pose, de l'autre les observations du modele, et n'en fait qu'une
chose — des etats du catalogue, puis des notes, puis une page.

    mesures POSE  ---\\
                      >--- etats du catalogue --- notes --- note /20, conseils, persona
    observations LLM -/

Les trois regles d'agregation, et pourquoi elles sont ce qu'elles sont :

1. **Note d'un critere sur une repetition = la plus basse de ses indicateurs.** Un
   critere est aussi bon que son pire element : c'est ainsi qu'un juge lit un lift, et
   ca evite qu'un dos qui s'enroule soit dilue par cinq indicateurs corrects.
2. **Note d'un critere sur le set = moyenne arrondie au plus proche des notes par rep.**
   Ni mediane (elle efface la repetition isolee que l'histogramme montre juste au-dessus)
   ni arrondi a l'inferieur (sur trois reps et un point d'ecart, il est arithmetiquement
   identique au minimum : mesure sur 6 clips, il egalait la pire rep sur 45 criteres
   sur 45).
3. **Note sur 20 = moyenne ponderee des criteres**, poids declares dans le catalogue.
   Un critere non evaluable sort du calcul ET du denominateur : un clip ou le dos n'est
   pas visible n'est pas un clip ou le dos est mauvais.
"""

from __future__ import annotations

import indicators
import persona as persona_mod
from indicators import Portee, Source

NOTE_MAX = 3


# --------------------------------------------------------------- etats observes

def etats_de_rep(mesures: dict, observations: dict, variante: str) -> dict[str, str]:
    """Les etats du catalogue pour une repetition, des deux sources reunies.

    Les mesures de pose passent par leurs seuils, les observations du modele sont deja
    des cles d'etat. Une source qui n'a rien a dire ne met simplement pas la cle.
    """
    etats: dict[str, str] = {}
    for ind in indicators.pour(variante):
        if ind.source is Source.POSE:
            cle = ind.etat_depuis_mesure((mesures or {}).get(ind.mesure))
        else:
            cle = (observations or {}).get(ind.nom)
            if isinstance(cle, str) and ind.etat(cle) is None:
                cle = None
        if cle is not None:
            etats[ind.nom] = cle
    return etats


# ------------------------------------------------------------------- notation

def _moyenne(notes) -> float | None:
    notes = [n for n in notes if n is not None]
    return sum(notes) / len(notes) if notes else None


def _moyenne_arrondie(notes) -> int | None:
    m = _moyenne(notes)
    return None if m is None else int(m + 0.5)     # notes positives : au plus proche


def note_du_critere(etats: dict, critere: str, variante: str) -> tuple[int | None, list[dict]]:
    """(note, faits) : la note du critere sur cette rep, et ce qui l'a produite.

    La note est la plus basse des notes de ses indicateurs. `faits` liste tout ce qui a
    ete observe pour ce critere, note ou non — c'est ce que la page montre.
    """
    notes, faits = [], []
    for ind in indicators.pour(variante):
        if ind.critere != critere:
            continue
        cle = etats.get(ind.nom)
        if cle is None:
            continue
        etat = ind.etat(cle)
        if etat is None:
            continue
        faits.append({"indicateur": ind.id, "phase": ind.phase.value,
                      "source": ind.source.value, "fait": etat.description,
                      "note": etat.note})
        if etat.note is not None:
            notes.append(etat.note)
    return (min(notes) if notes else None), faits


def note_sur_20(notes_criteres: dict[str, float | None]) -> int | None:
    """La note affichee, ponderee. Les criteres non evaluables sortent du denominateur.

    Elle se calcule sur les moyennes NON ARRONDIES des notes par repetition, alors que
    la note montree a cote de chaque critere est arrondie. Ce n'est pas une incoherence,
    c'est ce qui l'evite : sur deux repetitions notees 3 et 2, l'arrondi au plus proche
    rend 3, et un set dont la moitie des reps est fautive sortait a 19/20 sous deux
    conseils correctifs. L'arrondi reste sur la note du critere, ou il sert a afficher
    un entier ; il ne decide pas du total.
    """
    haut = sum(indicators.POIDS[c] * n for c, n in notes_criteres.items() if n is not None)
    bas = sum(indicators.POIDS[c] * NOTE_MAX for c, n in notes_criteres.items() if n is not None)
    return None if bas == 0 else int(haut / bas * 20 + 0.5)


# ------------------------------------------------------------------- conseils

def conseils(reps: list[dict], limite: int = 2) -> list[dict]:
    """Au plus deux conseils, les plus graves d'abord.

    Deux et non huit : une page qui reproche huit choses ne fait rien changer. Un
    conseil dit quoi essayer, jamais pourquoi le defaut existe — la cause ne se lit pas
    sur une video.
    """
    trouves: dict[str, dict] = {}
    for rep in reps:
        for critere, bloc in rep["criteres"].items():
            for fait in bloc["faits"]:
                ind = indicators.PAR_ID[fait["indicateur"]]
                cle = etat_cle(rep, ind.nom)
                texte = indicators.CONSEILS.get(f"{ind.nom}:{cle}")
                if texte is None or fait["note"] is None:
                    continue
                entree = trouves.setdefault(ind.nom, {
                    "indicateur": ind.id, "critere": critere,
                    "constat": fait["fait"], "a_essayer": texte,
                    "note": fait["note"], "reps": []})
                entree["reps"].append(rep["index"])
                # La gravite retenue est la PIRE observee, pas la premiere : un defaut
                # qui vaut 2 sur la rep 1 et 1 sur la rep 4 est un defaut a 1.
                if fait["note"] < entree["note"]:
                    entree.update(note=fait["note"], constat=fait["fait"])
    ordre = sorted(trouves.values(),
                   key=lambda c: (c["note"], -indicators.POIDS[c["critere"]], -len(c["reps"])))
    return ordre[:limite]


def etat_cle(rep: dict, nom: str) -> str | None:
    return rep["etats"].get(nom)


# --------------------------------------------------------------- tenue du set

def tenue_du_set(reps: list[dict]) -> dict:
    """Comment la technique tient d'une repetition a l'autre.

    Calculee, pas jugee : c'est le seul critere que le modele notait a l'oeil alors que
    "la derniere rep a pris deux fois plus longtemps que la premiere" est un fait. La
    duree de tiree vient des horodatages reels de la pose.
    """
    if len(reps) <= 1:
        return {"etat": "rep_unique", "texte": "A single repetition: there is nothing to "
                                               "compare across the set."}
    premiere, derniere = reps[0], reps[-1]
    if premiere["note"] is None or derniere["note"] is None:
        return {"etat": "indeterminee",
                "texte": "The first or the last rep could not be assessed, so the set "
                         "cannot be compared end to end."}
    ecart_note = derniere["note"] - premiere["note"]
    t1, t2 = premiere["temps"].get("tiree_s"), derniere["temps"].get("tiree_s")
    ralentissement = (t2 / t1) if (t1 and t2) else 1.0

    # premiere repetition dont la note descend sous celle de la premiere
    decroche = next((r["index"] for r in reps[1:]
                     if r["note"] is not None and r["note"] < premiere["note"]), None)

    if ecart_note <= -2 or ralentissement >= 2.0:
        etat, texte = "s_effondre", "The set falls apart: the last rep looks nothing like the first."
    elif ecart_note <= -1 or ralentissement >= 1.4:
        etat, texte = "derive", "The technique drifts over the set."
    else:
        etat, texte = "tient", "The set holds together: the last rep looks like the first."
    if decroche:
        texte += f" It starts changing at rep {decroche}."
    return {"etat": etat, "texte": texte, "ecart_note": ecart_note,
            "ralentissement": round(ralentissement, 2), "decroche_a": decroche}


# ------------------------------------------------------------------- assemblage

def _aligne(candidats: list, entrees: list) -> dict[int, dict]:
    """{position du candidat: observations} — par rang, ou par `rep_index` si besoin.

    Le protocole demande une entree par segment, dans l'ordre : quand les comptes
    correspondent, le rang suffit et c'est le cas normal. Mais un modele faible supprime
    parfois une entree au lieu de la marquer `non`, ou en invente une (mesure : flash-lite
    fait les deux). Le rang glisse alors, et les observations d'une repetition seraient
    collees sur une autre — un decalage silencieux, bien pire qu'un trou. On retombe donc
    sur `rep_index`, et ce qui ne tombe sur aucun candidat est ignore.
    """
    if len(entrees) == len(candidats):
        return dict(enumerate(entrees))
    sortie: dict[int, dict] = {}
    for rang, entree in enumerate(entrees):
        index = entree.get("rep_index")
        position = (index - 1) if isinstance(index, int) and index >= 1 else rang
        if 0 <= position < len(candidats) and position not in sortie:
            sortie[position] = entree
    return sortie

def evalue(pose: dict, observations: dict) -> dict:
    """Le resultat complet montre a l'utilisateur.

    `pose` est ce que rend `pose_analysis.analyse`, `observations` ce que rend le modele.
    Les deux listes de repetitions sont alignees par position : le modele recoit un
    segment video par candidat de pose, dans l'ordre, et rend une entree par segment.
    """
    variante = pose.get("variante") or "conventional"
    criteres = list(indicators.CRITERES)
    par_llm = _aligne(pose.get("reps") or [], (observations or {}).get("reps") or [])

    reps, retirees = [], []
    for position, cand in enumerate(pose.get("reps") or []):
        obs = par_llm.get(position, {})
        etats = etats_de_rep(cand.get("mesures"), obs, variante)

        # La pose voit le corps, pas la barre : se redresser apres l'avoir reposee produit
        # exactement le meme mouvement qu'une repetition. Seul le modele tranche, et il
        # le fait ici, avant toute notation.
        reel = etats.get("bar_left_floor", "oui")
        if reel == "non":
            retirees.append(position + 1)
            continue

        bloc = {}
        for critere in criteres:
            note, faits = note_du_critere(etats, critere, variante)
            # Une tentative inachevee n'a pas de lockout ni de descente : ces phases ne
            # sont pas invisibles, elles n'ont pas eu lieu. Non applicable, pas mauvais.
            if reel == "inachevee" and critere in ("lockout", "descent"):
                bloc[critere] = {"libelle": indicators.LIBELLE[critere], "note": None,
                                 "statut": "non_applicable", "faits": faits}
                continue
            bloc[critere] = {"libelle": indicators.LIBELLE[critere], "note": note,
                             "statut": "note" if note is not None else "non_evaluable",
                             "faits": faits}

        mes = cand.get("mesures") or {}
        reps.append({
            "index": len(reps) + 1,
            "debut_s": cand.get("debut_s"), "fin_s": cand.get("fin_s"),
            "statut": "inachevee" if reel == "inachevee" else "complete",
            "criteres": bloc,
            "note": _moyenne_arrondie([b["note"] for b in bloc.values()]),
            "sur": NOTE_MAX,
            "temps": {"tiree_s": mes.get("duree_tiree_s"),
                      "lockout_s": mes.get("duree_lockout_s")},
            "resume": obs.get("resume", ""),
            "etats": etats,
        })

    par_critere = {c: [r["criteres"][c]["note"] for r in reps] for c in criteres}
    notes_set = {c: _moyenne_arrondie(n) for c, n in par_critere.items()}
    moyennes = {c: _moyenne(n) for c, n in par_critere.items()}
    # Le contexte reunit les indicateurs de portee SET des deux sources. Les mesures de
    # pose y passent par leurs seuils comme partout ailleurs : la page montre "filmed
    # from the side", pas "vue = 0.029".
    contexte = {"variante": variante}
    mesures_set = {"variante": variante, "vue": pose.get("vue"),
                   "visibilite": pose.get("visibilite")}
    for ind in indicators.pour(variante, portee=Portee.SET):
        cle = (ind.etat_depuis_mesure(mesures_set.get(ind.mesure))
               if ind.source is Source.POSE else (observations or {}).get(ind.nom))
        etat = ind.etat(cle) if cle else None
        contexte[ind.nom] = {"etat": cle, "texte": etat.description if etat else None}
    contexte["mesures"] = {k: v for k, v in mesures_set.items() if k != "variante"}

    return {
        "variante": variante,
        "contexte": contexte,
        "reps": [{k: v for k, v in r.items() if k != "etats"} for r in reps],
        "criteres": {c: {"libelle": indicators.LIBELLE[c], "note": notes_set[c],
                         "poids": indicators.POIDS[c],
                         "notes_par_rep": [r["criteres"][c]["note"] for r in reps]}
                     for c in criteres},
        "note_sur_20": note_sur_20(moyennes),
        "nb_reps": len(reps),
        "segments_ecartes": retirees,
        "tenue_du_set": tenue_du_set(reps),
        "conseils": conseils(reps),
        "persona": persona_mod.deduis([r["etats"] for r in reps]),
    }
