"""Le schema de sortie du modele, genere depuis le catalogue.

Rien n'est ecrit ici a la main : les champs, leurs valeurs possibles et leurs consignes
viennent tous d'`indicators.py`. Ajouter un indicateur `LLM` ou `A_TESTER` au catalogue
le fait apparaitre dans le schema sans toucher a ce fichier.

Le modele ne rend AUCUNE note. Il choisit un etat observable par indicateur, dans une
liste fermee imposee par le decodage contraint — il ne peut donc ni inventer un etat, ni
oublier un indicateur. La notation est faite par `rules.py`, en Python.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, create_model

import indicators
from indicators import Portee


class VideoClassification(BaseModel):
    # str et non Enum, volontairement : mesure, ca marche mieux.
    # La VARIANTE (sumo/conventionnel) ne se demande plus au modele — elle vient de la
    # cascade de pose, qui fait 39/39 la ou le modele se trompe. Seule la famille du
    # mouvement lui est demandee.
    mouvement_detecte: str = Field(
        description="Must be 'squat', 'bench press', 'deadlift', or 'unworkable_video'")


def _classe(nom: str) -> str:
    return "".join(m.capitalize() for m in nom.split("_"))


def _enum(ind: indicators.Indicateur) -> type[Enum]:
    """L'enum ferme des etats, tel que le decodage contraint l'imposera au modele."""
    return Enum(f"{_classe(ind.nom)}Etat",
                {e.cle.upper(): e.cle for e in ind.tous_les_etats}, type=str)


def _modele_de_rep(variante: str) -> type[BaseModel]:
    """Une repetition : un champ par indicateur juge par le modele, dans l'ordre du geste.

    L'ordre des champs est l'ordre de generation en decodage contraint. Il suit la
    chronologie du mouvement — setup, decollage, tiree, lockout, descente — pour que le
    modele observe dans l'ordre ou les choses arrivent.
    """
    champs: dict = {
        "rep_index": (int, Field(description="1 for the first repetition, 2 for the "
                                             "second, and so on. Never repeat an index.")),
    }
    for ind in indicators.juges_par_le_modele(variante, Portee.REP):
        champs[ind.nom] = (_enum(ind), Field(description=ind.consigne()))
    champs["resume"] = (str, Field(description="One short sentence describing what you "
                                               "saw on THIS repetition. No score, no advice."))
    return create_model(f"Rep{_classe(variante)}", **champs)


def _modele_d_analyse(variante: str) -> type[BaseModel]:
    champs: dict = {
        "reps": (list[_modele_de_rep(variante)],
                 Field(description="One entry per segment provided, in chronological "
                                   "order. Fill EVERY field for EVERY entry.")),
    }
    for ind in indicators.juges_par_le_modele(variante, Portee.SET):
        champs[ind.nom] = (_enum(ind), Field(description=ind.consigne()))
    return create_model(f"Analyse{_classe(variante)}", **champs)


SCHEMAS = {v: _modele_d_analyse(v) for v in ("conventional", "sumo")}
