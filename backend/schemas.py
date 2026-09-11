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


# Ce qu'on demande AVANT chaque etat. L'ordre des champs est l'ordre de generation en
# decodage contraint : ce texte est donc produit avant que l'etat soit choisi, et il ne
# peut pas etre reecrit apres coup pour coller a la reponse.
#
# La formulation compte, et elle vient d'une mesure. Une premiere version demandait "ecris
# ce que tu VOIS qui tranche ce champ, avec un horodatage" : le modele rendait 21 phrases
# qui etaient son verdict avec une heure collee devant ("At 4.50s the hips and shoulders
# rise together"), et aucun etat ne changeait. Interroge au contraire sur la GEOMETRIE,
# sans liste et sans verdict, il produit une description fine et juste — c'est ainsi qu'on
# a obtenu "the lumbar spine starts in a state of mild flexion" sur un clip ou la liste
# fermee lui faisait repondre "the back is flat".
#
# D'ou : on demande des formes, des positions et leur evolution. On INTERDIT de nommer une
# option ou de qualifier. Et on demande l'incertitude, qui est la partie la plus utile a
# la relecture — c'est elle qui a revele que le modele croyait regarder un profil, et que
# la ceinture masquait le rachis lombaire.
OBSERVATION = (
    "Before answering '{nom}', describe what you actually SEE about it: the shapes, the "
    "positions, and how they change, with timestamps. Describe the geometry, not your "
    "conclusion — do NOT name any of the options listed for that field, and do NOT say "
    "whether it looks good or bad. Finish by saying what, if anything, stops you from "
    # RETIRE le 2026-09-11, une heure apres l'avoir ajoute. Le paragraphe demandait, pour
    # les champs portant sur un evenement, soit l'horodatage soit "dis que tu as suivi le
    # mouvement image par image et nomme les images verifiees". Mesure sur pr_160 : les
    # champs exprimant une reserve tombent de 22/23 a 2/23, et 22/23 se terminent par
    # "Nothing stops me from being sure". On lui a demande de certifier son exhaustivite,
    # il l'a certifiee — et la certitude s'est propagee aux etats. `asymmetry` est passe
    # d'une abstention correcte a "les deux cotes montent ensemble" sur un clip filme de
    # trois-quarts. Deuxieme consigne d'observation de la journee a se retourner : la
    # premiere demandait "la preuve qui tranche" et rendait des verdicts horodates.
    "being sure.")


def _modele_de_rep(variante: str) -> type[BaseModel]:
    """Une repetition : par indicateur, une observation libre PUIS un etat ferme.

    L'ordre des champs est l'ordre de generation en decodage contraint. Il suit la
    chronologie du mouvement — setup, decollage, tiree, lockout, descente — pour que le
    modele observe dans l'ordre ou les choses arrivent.

    Chaque etat est precede de son champ `_observed`, libre. Deux raisons, dans cet ordre :
    la relecture — on voit enfin sur quoi le modele s'appuie, critere par critere — et
    l'espoir qu'ecrire la forme avant de la classer rende l'etat flatteur plus couteux.
    Le second point n'est PAS acquis : mesure au 2026-09-10, un champ libre mal formule
    n'avait rien change aux etats. La valeur de diagnostic, elle, est acquise.
    """
    champs: dict = {
        "rep_index": (int, Field(description="1 for the first repetition, 2 for the "
                                             "second, and so on. Never repeat an index.")),
    }
    for ind in indicators.juges_par_le_modele(variante, Portee.REP):
        champs[f"{ind.nom}_observed"] = (
            str, Field(description=OBSERVATION.format(nom=ind.nom)))
        champs[ind.nom] = (_enum(ind), Field(description=ind.consigne()))
    champs["summary"] = (str, Field(description="One short sentence in ENGLISH describing "
                                                "what you saw on THIS repetition. No score, "
                                                "no advice."))
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
