"""Le persona : l'archetype du lifter, DEDUIT des etats observes.

Le modele ne le choisit plus. Chaque persona est deja la description d'un etat precis du
catalogue — The Fishing Rod est "le dos s'enroule sous charge", The Soft-Lock est "les
genoux restent mous en haut". Le demander en plus au modele, c'est lui faire refaire un
travail qu'il vient de faire, avec le droit de se contredire : dans la version
precedente il tombait d'accord avec l'humain 4 fois sur 48, et sortait "The Crane"
15 fois sur 48.

Regle : le defaut le plus grave observe sur l'ensemble de la serie. A gravite egale, le
critere le plus lourd ; puis l'ordre du catalogue, qui va du debut du geste a la fin.
"""

from __future__ import annotations

import indicators

PAR_DEFAUT = "The Technician"
JUSTIFICATION_PAR_DEFAUT = "Nothing in this set stood out as a fault worth a nickname."


def possibles(variante: str) -> list[str]:
    """Le vocabulaire des personas de cette variante, pour le front et les tests."""
    vus = {e.persona for i in indicators.pour(variante) for e in i.etats if e.persona}
    return sorted(vus) + [PAR_DEFAUT]


def deduis(etats_par_rep: list[dict]) -> dict:
    """{nom, fait, rep} : l'archetype, l'observation qui l'a declenche, et ou.

    `etats_par_rep` est la liste, une entree par repetition retenue, des etats observes
    sous la forme {nom_indicateur: cle_etat}.
    """
    candidats = []
    for position, etats in enumerate(etats_par_rep):
        for rang, ind in enumerate(indicators.INDICATEURS):
            cle = etats.get(ind.nom)
            if cle is None:
                continue
            etat = ind.etat(cle)
            if etat is None or etat.persona is None or etat.note is None:
                continue
            poids = indicators.POIDS.get(ind.critere, 1.0)
            candidats.append((etat.note, -poids, rang, position, ind, etat))

    if not candidats:
        return {"nom": PAR_DEFAUT, "fait": JUSTIFICATION_PAR_DEFAUT, "rep": None}

    _, _, _, position, ind, etat = min(candidats, key=lambda c: c[:3])
    return {"nom": etat.persona, "fait": etat.description, "rep": position + 1,
            "indicateur": ind.id}
