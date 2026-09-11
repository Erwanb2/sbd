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

## Deux axes, et un seul nombre

Depuis le 2026-09-09, les criteres sont les MECANIQUES du geste et non ses phases, et
ils se lisent sur deux axes qui ne se melangent pas :

* **La sequence** — les six mecaniques, dans l'ordre causal. Elle produit l'EPINGLE :
  un seul defaut mis en avant, le plus en amont, avec ce qui en decoule rattache
  dessous. Voir `epingle()`.
* **La structure** — le dos, les genoux, la symetrie. Des choses qui ne s'executent
  pas, qui LACHENT. Elle produit l'URGENCE, un bandeau avec sa propre gravite. Voir
  `urgence()`.

Montrer les deux ne disperse pas le lifter, la ou montrer deux fautes de sequence le
disperserait : l'un dit "change ca dans ton geste", l'autre "ton corps ne tient pas,
baisse". Le danger fixe l'urgence, la cause fixe l'action.

Un seul nombre en sort quand meme : `structure` garde son poids dans la note sur 20,
sinon un dos qui s'effondre sortirait a 18/20 et le chiffre mentirait.
"""

from __future__ import annotations

import math

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
    """Moyenne arrondie au plus proche, les EGALITES vers le bas.

    L'arrondi reste au plus proche — 2,67 vaut 3 — ce qui ecarte l'arrondi a
    l'inferieur, mesure comme arithmetiquement identique au minimum sur trois
    repetitions et un point d'ecart. Seules les egalites exactes changent, et elles
    descendent : sur un set ou une repetition sur deux est fautive, la moyenne vaut
    2,5, et afficher 3/3 au-dessus de la liste des fautes se lit comme une erreur.
    """
    m = _moyenne(notes)
    return None if m is None else math.ceil(m - 0.5)


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

def _defauts(reps: list[dict]) -> dict[str, dict]:
    """Un defaut par indicateur fautif sur la serie, avec sa pire note et ses reps.

    La gravite retenue est la PIRE observee, pas la premiere : un defaut qui vaut 2 sur
    la rep 1 et 1 sur la rep 4 est un defaut a 1. Le constat suit — sinon la page affiche
    "termine ta serie" sur un dos qui s'effondre.
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
                    "indicateur": ind.id, "nom": ind.nom, "critere": critere,
                    "constat": fait["fait"], "a_essayer": texte, "etat": cle,
                    "note": fait["note"], "reps": []})
                entree["reps"].append(rep["index"])
                if fait["note"] < entree["note"]:
                    entree.update(note=fait["note"], constat=fait["fait"],
                                  a_essayer=texte, etat=cle)
    return trouves


def epingle(reps: list[dict]) -> dict | None:
    """LE defaut mis en avant, et ce qui en decoule. Un seul, jamais deux.

    Cinq cartes a 3/3 et une a 2/3, ce n'est pas du coaching, c'est un bulletin. Ce qui
    aide un lifter, c'est UNE chose a corriger pour la prochaine seance.

    Deux regles, et elles sont tout l'ecart entre un bulletin et un coach :

    1. **L'epingle est le defaut le plus EN AMONT de la chaine causale**, pas le plus
       grave. Une faute de placement produit trois reproches — hanches basses, hanches
       qui decollent, barre qui s'eloigne — pour une seule cause, et c'est la premiere
       qu'il faut corriger : les deux autres disparaissent avec elle.
    2. **Ce qui en decoule est RATTACHE, pas liste a cote.** Annoncer les deux, c'est
       demander deux corrections pour une cause et n'en obtenir aucune.

    L'epingle ne pointe jamais vers l'axe structure : "utilise moins tes lombaires"
    n'est pas une consigne executable. Le danger fixe l'urgence, la cause fixe l'action.
    """
    defauts = _defauts(reps)
    candidats = [d for d in defauts.values() if d["critere"] != indicators.STRUCTURE]
    if not candidats:
        return None

    # On part du PIRE defaut, puis on remonte la chaine aussi loin qu'elle va, et on
    # epingle la racine. "Le plus en amont" tout court ne marche pas : mesure sur la
    # demo de la page d'accueil, un slack a 2 se placait devant des hanches qui
    # decollent a 1 et les reprochait separement, alors que c'est la meme histoire.
    # Une broutille de setup masquerait en permanence un effondrement plus loin.
    pire = min(candidats, key=lambda d: (d["note"], indicators.rang_causal(d["critere"]),
                                         -len(d["reps"])))

    # Les ancetres du pire defaut : ceux dont la chaine y mene, de proche en proche.
    parents: dict[str, list[dict]] = {}
    for d in defauts.values():
        for aval in indicators.ENCHAINEMENTS.get(f"{d['nom']}:{d['etat']}", ()):
            if aval in defauts:
                parents.setdefault(aval, []).append(d)
    racines, vus, a_voir = [pire], {pire["nom"]}, [pire]
    while a_voir:
        for parent in parents.get(a_voir.pop(0)["nom"], ()):
            if parent["nom"] not in vus and parent["critere"] != indicators.STRUCTURE:
                vus.add(parent["nom"])
                racines.append(parent)
                a_voir.append(parent)

    tete = min(racines, key=lambda d: (indicators.rang_causal(d["critere"]),
                                       d["note"], -len(d["reps"])))

    # Le parcours est TRANSITIF : des hanches trop basses expliquent des hanches qui
    # decollent, qui expliquent a leur tour une barre qui s'eloigne. S'arreter au
    # premier cran laisserait le bout de la chaine en defaut independant, et la page
    # reprocherait deux fois la meme cause.
    #
    # Une arete ne joue que si les DEUX bouts sont fautifs sur cette serie : un
    # enchainement declare n'est une consequence que si la consequence a eu lieu.
    consequences, vus, a_voir = [], {tete["nom"]}, [tete]
    while a_voir:
        courant = a_voir.pop(0)
        for nom in indicators.ENCHAINEMENTS.get(f"{courant['nom']}:{courant['etat']}", ()):
            if nom in vus or nom not in defauts:
                continue
            vus.add(nom)
            suivant = defauts[nom]
            if suivant["critere"] != indicators.STRUCTURE:
                consequences.append(suivant)
            a_voir.append(suivant)
    # Le dos et les genoux ne descendent pas dans les consequences affichees : ils
    # remontent au bandeau, qui a sa propre urgence. Ils restent "vus" pour ne pas
    # etre rapportes une seconde fois comme defaut independant.
    consequences.sort(key=lambda d: indicators.rang_causal(d["critere"]))
    expliques = vus

    return {**tete, "consequences": consequences,
            # Ce qui reste et que l'epingle n'explique pas. Un seul : la page ne doit
            # pas rallonger, et deux reproches independants se neutralisent deja.
            #
            # Un defaut du MEME critere que l'epingle n'y figure pas : il s'affiche
            # deja sur la carte de la mecanique, et le sortir ici donnerait deux
            # consignes sous le meme titre.
            "autres": sorted((d for d in candidats if d["nom"] not in expliques
                              and d["critere"] != tete["critere"]),
                             key=lambda d: (d["note"], -len(d["reps"])))[:1]}


def urgence(reps: list[dict]) -> dict:
    """Le bandeau de l'axe structure : ce qui a lache, et a quel point c'est grave.

    Elle se lit sur la PIRE note vue sur une repetition, jamais sur la note agregee :
    un dos qui s'effondre sur une rep sur cinq ressort a 3/3 apres moyenne, et il faut
    quand meme dire de s'arreter. C'est l'inverse du persona, qui exige au contraire
    que le defaut survive a la serie — parce qu'un surnom etiquette une serie et qu'une
    blessure n'attend pas la moyenne.
    """
    notes = [rep["criteres"][indicators.STRUCTURE]["note"] for rep in reps]
    notes = [n for n in notes if n is not None]
    defauts = [d for d in _defauts(reps).values() if d["critere"] == indicators.STRUCTURE]
    if not notes:
        return {"etat": "inconnu", "note": None, "defauts": defauts,
                "texte": "The camera angle never showed enough to judge back, knees or "
                         "symmetry on this set."}
    pire = min(notes)
    etat, texte = indicators.URGENCES[pire]
    return {"etat": etat, "note": pire, "texte": texte,
            "defauts": sorted(defauts, key=lambda d: d["note"])}


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
    # Le decrochage n'est mentionne que si le set DERIVE vraiment. Le verdict compare
    # la premiere et la derniere rep, `decroche` cherche le premier creux n'importe ou :
    # un creux isole au milieu d'un set qui finit comme il a commence n'est pas une
    # derive, et la phrase se contredisait ("the set holds together... it starts
    # changing at rep 2").
    if decroche and etat != "tient":
        texte += f" It starts changing at rep {decroche}."
    return {"etat": etat, "texte": texte, "ecart_note": ecart_note,
            "ralentissement": round(ralentissement, 2), "decroche_a": decroche}


# ------------------------------------------------------------------- assemblage

def faits_du_critere(reps: list[dict], critere: str) -> list[dict]:
    """Les faits observes pour un critere sur toute la serie, dedoublonnes.

    Le modele n'ecrit plus de paragraphe par critere : la page montre ce qui a ete
    observe, dans les mots du catalogue, avec les repetitions concernees. "Les hanches
    partent en premier — reps 2, 3" est plus utile qu'un commentaire de coach genere,
    et surtout il ne peut pas contredire la note.
    """
    groupes: dict[str, dict] = {}
    for rep in reps:
        for fait in rep["criteres"][critere]["faits"]:
            entree = groupes.setdefault(fait["fait"], {**fait, "reps": []})
            entree["reps"].append(rep["index"])
    return sorted(groupes.values(),
                  key=lambda f: (f["note"] is None, f["note"] if f["note"] else 0))


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
        reel = etats.get("bar_left_floor", "yes")
        if reel == "no":
            retirees.append(position + 1)
            continue

        bloc = {}
        for critere in criteres:
            note, faits = note_du_critere(etats, critere, variante)
            # Une tentative inachevee n'a ni position d'arrivee ni reset : ces mecaniques
            # ne sont pas invisibles, elles n'ont pas eu lieu. Non applicable, pas mauvais.
            if reel == "incomplete" and critere in ("finish_position", "reset"):
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
            "statut": "incomplete" if reel == "incomplete" else "complete",
            "criteres": bloc,
            "note": _moyenne_arrondie([b["note"] for b in bloc.values()]),
            # Note fine, non arrondie : c'est elle qui donne la hauteur des barres de
            # l'histogramme. Sans elle, deux reps que l'arrondi met a egalite sont
            # dessinees identiques alors que l'une est nettement moins bonne.
            "note_precise": (lambda m: None if m is None else round(m, 2))(
                _moyenne([b["note"] for b in bloc.values()])),
            "sur": NOTE_MAX,
            "non_evaluables": sum(1 for b in bloc.values() if b["note"] is None),
            # `decollage_s` est l'horodatage exact ou la barre quitte le sol (lu sur les
            # images, dans `_phases`), pas `debut_s` : celui-la inclut la marge de mise en
            # place ajoutee par `rep_detection` autour de la fenetre. C'est ce que le front
            # utilise pour marquer le decollage sur la barre de lecture de la rep.
            "temps": {"tiree_s": mes.get("pull_s"),
                      "lockout_s": mes.get("lockout_s"),
                      "decollage_s": (mes.get("_phases") or {}).get("decollage_s")},
            "resume": obs.get("summary", ""),
            "etats": etats,
            # Ce que le modele a decrit AVANT de choisir chaque etat. Produit par le
            # schema (`<nom>_observed`), conserve ici parce que c'est la seule fenetre
            # qu'on ait sur ce qu'il regarde, critere par critere. Sans ca, le texte est
            # genere, facture, puis jete — et une divergence entre la description et
            # l'etat choisi devient introuvable.
            "observations": {nom: txt for nom in etats
                             if (txt := obs.get(f"{nom}_observed"))},
        })

    par_critere = {c: [r["criteres"][c]["note"] for r in reps] for c in criteres}
    notes_set = {c: _moyenne_arrondie(n) for c, n in par_critere.items()}
    moyennes = {c: _moyenne(n) for c, n in par_critere.items()}
    # Le contexte reunit les indicateurs de portee SET des deux sources. Les mesures de
    # pose y passent par leurs seuils comme partout ailleurs : la page montre "filmed
    # from the side", pas "vue = 0.029".
    contexte = {}
    mesures_set = {"variant": variante, "view": pose.get("view"),
                   "visibility": pose.get("visibility")}
    for ind in indicators.pour(variante, portee=Portee.SET):
        cle = (ind.etat_depuis_mesure(mesures_set.get(ind.mesure))
               if ind.source is Source.POSE else (observations or {}).get(ind.nom))
        etat = ind.etat(cle) if cle else None
        contexte[ind.nom] = {"etat": cle, "texte": etat.description if etat else None}
    contexte["mesures"] = {k: v for k, v in mesures_set.items() if k != "variant"}

    note = note_sur_20(moyennes)
    pin = epingle(reps)
    return {
        "variante": variante,
        "contexte": contexte,
        "reps": [{k: v for k, v in r.items() if k != "etats"} for r in reps],
        "criteres": {c: {"libelle": indicators.LIBELLE[c], "note": notes_set[c],
                         "poids": indicators.POIDS[c],
                         "notes_par_rep": [r["criteres"][c]["note"] for r in reps],
                         "faits": faits_du_critere(reps, c)}
                     for c in criteres},
        # Les six mecaniques, dans l'ordre causal. Le front itere cette liste pour la
        # grille ; `structure` est deja dans `criteres` mais s'affiche en bandeau.
        "mecaniques": list(indicators.MECANIQUES),
        "structure": urgence(reps),
        "epingle": pin,
        "note_sur_20": note,
        "nb_reps": len(reps),
        "segments_ecartes": retirees,
        "tenue_du_set": tenue_du_set(reps),
        # Liste a plat, l'epingle en tete : gardee pour l'eval et le scorer, qui
        # comptent des conseils sans se soucier de la chaine causale.
        "conseils": ([pin] + pin["autres"]) if pin else [],
        "persona": persona_mod.deduis([r["etats"] for r in reps], notes_set, note),
        # Le suivi dense deja calcule par la pose, recopie tel quel pour l'overlay du
        # front. Absent si la pose ne l'a pas produit (voir `pose_analysis._squelette`).
        "squelette": pose.get("squelette"),
    }
