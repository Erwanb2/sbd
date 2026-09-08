"""Le persona : l'archetype du lifter, DEDUIT des etats observes.

Le modele ne le choisit plus. Chaque persona est deja la description d'un etat precis du
catalogue — The Fishing Rod est "le dos s'enroule sous charge", The Soft-Lock est "les
genoux restent mous en haut". Le demander en plus au modele, c'est lui faire refaire un
travail qu'il vient de faire, avec le droit de se contredire : dans la version
precedente il tombait d'accord avec l'humain 4 fois sur 48, et sortait "The Crane"
15 fois sur 48.

Deux conditions pour meriter un surnom, et elles repondent a deux erreurs constatees :

1. **Le defaut doit survivre a la serie.** Un persona etiquette un SET, pas une
   repetition. Il n'est retenu que si le critere auquel il appartient est lui-meme sous
   le maximum apres agregation. Mesure sur conventionnal_deadlift_12 : une descente
   notee 2 sur deux reps sur cinq a decroche "The Kneecapper" sur un lift que l'humain
   qualifie de "tres propre" et que le systeme note 20/20 — un critere a 1 sur une rep
   sur cinq ressort a 20/20 apres moyenne, donc le persona et la note se contredisaient.

2. **Un tres bon lift ne recoit pas de sobriquet.** Au-dessus de `SEUIL_TECHNICIEN` sur
   20, et a condition qu'aucun critere ne soit tombe a 1, c'est The Technician.
   La condition sur les criteres n'est pas decorative : la note sur 20 est ponderee, et
   quatre criteres sur six peuvent valoir 1/3 pour un total d'exactement 18. Sans elle,
   le produit feliciterait un lifter dont la barre part loin du corps.

Entre les candidats restants : le defaut le plus grave. A gravite egale, le critere le
plus lourd ; puis l'ordre du catalogue, qui va du debut du geste a la fin.
"""

from __future__ import annotations

import indicators

PAR_DEFAUT = "The Technician"

# Au-dessus de cette note, et sans aucun critere effondre, pas de surnom.
SEUIL_TECHNICIEN = 18
JUSTIFICATION_PAR_DEFAUT = "Nothing in this set stood out as a fault worth a nickname."


def possibles(variante: str) -> list[str]:
    """Le vocabulaire des personas de cette variante, pour le front et les tests."""
    vus = {e.persona for i in indicators.pour(variante) for e in i.etats if e.persona}
    return sorted(vus) + [PAR_DEFAUT]


def deduis(etats_par_rep: list[dict], notes_criteres: dict | None = None,
           note_sur_20: int | None = None) -> dict:
    """{nom, fait, rep} : l'archetype, l'observation qui l'a declenche, et ou.

    `etats_par_rep` est la liste, une entree par repetition retenue, des etats observes
    sous la forme {nom_indicateur: cle_etat}. `notes_criteres` porte les notes de synthese
    (celles affichees), `note_sur_20` la note finale.
    """
    notes_criteres = notes_criteres or {}
    parfait = (note_sur_20 is not None and note_sur_20 >= SEUIL_TECHNICIEN
               and all(n != 1 for n in notes_criteres.values()))
    if parfait:
        return {"nom": PAR_DEFAUT, "fait": JUSTIFICATION_PAR_DEFAUT, "rep": None}

    candidats = []
    for position, etats in enumerate(etats_par_rep):
        for rang, ind in enumerate(indicators.INDICATEURS):
            cle = etats.get(ind.nom)
            if cle is None:
                continue
            etat = ind.etat(cle)
            if etat is None or etat.persona is None or etat.note is None:
                continue
            # Le defaut doit avoir survecu a l'agregation du set : un accident isole
            # sur une repetition ne nomme pas la serie entiere.
            note_set = notes_criteres.get(ind.critere)
            if note_set is not None and note_set >= 3:
                continue
            poids = indicators.POIDS.get(ind.critere, 1.0)
            candidats.append((etat.note, -poids, rang, position, ind, etat))

    if not candidats:
        return {"nom": PAR_DEFAUT, "fait": JUSTIFICATION_PAR_DEFAUT, "rep": None}

    _, _, _, position, ind, etat = min(candidats, key=lambda c: c[:3])
    return {"nom": etat.persona, "fait": etat.description, "rep": position + 1,
            "indicateur": ind.id}
