"""Catalogue des indicateurs biomecaniques du souleve de terre.

C'est LE fichier de reference du projet. Tout le reste en decoule :

    indicators.py  ->  schemas.py        (le schema Pydantic des indicateurs LLM)
                   ->  pose_analysis.py  (les mesures MediaPipe, par repetition)
                   ->  rules.py          (indicateurs -> criteres notes -> note /20)
                   ->  persona.py        (l'archetype, deduit des etats observes)

Une seule liste, `INDICATEURS`, et trois consommateurs. Ajouter un indicateur, c'est
ajouter une entree ici : le schema, la notation et le persona suivent tout seuls.

## Le principe : le modele observe, Python note

Aucun indicateur ne demande une note au modele. Chacun definit une liste FERMEE d'etats
observables, et c'est `note_de()` qui traduit l'etat en 1, 2, 3 ou None. Le barème est
donc du code : il se relit, se teste, et se rejoue sur des sorties deja stockees sans
depenser un seul appel.

## Les trois sources

`Source.POSE`      MediaPipe le mesure. La valeur est un nombre, `seuils` la transforme
                   en etat. Deterministe d'une passe a l'autre.
`Source.LLM`       Seul un modele de langage peut le voir. Typiquement : tout ce qui
                   concerne la barre, les disques, le contact, la forme du dos.
`Source.A_TESTER`  Mesurable en theorie par la pose, mais rien ne prouve encore que la
                   mesure tient. **En attendant, c'est le LLM qui repond** : le champ
                   part dans le schema exactement comme un `LLM`. Le commentaire
                   `note_source` dit ce qu'il faudrait mesurer pour trancher.

## Deux limites dures, a ne pas contourner par un proxy

1. **MediaPipe ne voit pas la barre.** Aucun repere de barre ni de disque. Le poignet en
   est un substitut acceptable au setup (la main tient la barre) et douteux pendant la
   tiree. Tout ce qui porte sur la barre elle-meme est `LLM`.
2. **MediaPipe ne voit pas le rachis.** Il n'existe aucun repere entre les epaules et les
   hanches : le tronc est un segment droit par construction. Un "angle de flexion
   lombaire" calcule depuis epaule-hanche mesure l'inclinaison du buste, pas sa courbure.
   `P04` et `S05` restent `LLM`, definitivement.

## La vue conditionne la mesure

Les angles et les derives lus a l'image ne veulent rien dire hors profil (mesure : le
comptage par seuils absolus en degres tombe a 43 % contre 58 %). Chaque indicateur porte
donc une `vue` requise, et `pose_analysis` rend `None` plutot qu'un chiffre trompeur
quand la camera n'est pas au bon endroit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Source(str, Enum):
    POSE = "pose"           # mesure par MediaPipe
    LLM = "llm"             # juge par le modele de langage
    A_TESTER = "a_tester"   # mesurable en theorie ; LLM en attendant la mesure


class Phase(str, Enum):
    CONTEXTE = "contexte"   # vrai pour toute la video
    SETUP = "setup"         # avant que la barre bouge
    DECOLLAGE = "decollage" # premier tiers de la tiree
    TIREE = "tiree"         # du sol au verrouillage
    LOCKOUT = "lockout"     # la fin du mouvement
    DESCENTE = "descente"   # le retour au sol


class Portee(str, Enum):
    REP = "rep"   # peut changer d'une repetition a l'autre
    SET = "set"   # vrai pour toute la serie, demande une seule fois


class Vue(str, Enum):
    PROFIL = "side"   # mesurable seulement de cote
    FACE = "front"       # mesurable seulement de face ou trois-quarts
    TOUTE = "toute"     # ne depend pas de l'angle de camera


# Les criteres affiches a l'utilisateur sont les MECANIQUES du souleve de terre, dans
# l'ordre ou elles s'apprennent et ou elles s'enchainent.
#
# Ce ne sont plus les phases du geste (setup / tiree / lockout / descente). Une phase
# est l'endroit ou une faute APPARAIT, jamais l'endroit ou elle se corrige : personne
# n'a un "probleme de lockout", on a des hanches qui ne passent pas, et ca se voit au
# lockout. Decouper par phase garantit qu'on rapporte des symptomes.
#
# Un critere a deux metiers, et les deux comptent :
#   - NOMMER une mecanique, pour que la chose existe dans la tete du lifter avec un
#     nom, un repere et un exercice. C'est la partie qui apprend, et c'est pour ca
#     qu'on n'a pas le droit de fusionner deux habiletes distinctes pour raccourcir
#     la liste : "la barre t'a quitte aux genoux" n'apprend ni a se placer, ni a
#     sortir le slack, ni ce qu'est le leg drive.
#   - DESIGNER quoi corriger. Ce metier-la n'est PAS porte par la liste : il est
#     porte par l'ordre du dict, qui est l'ordre causal, et par ENCHAINEMENTS.
#
# L'ordre est donc signifiant, et il descend jusqu'au front, qui itere ce dict.
CRITERES = {
    "start_position":  ("Start position", 1.5),
    "slack_and_brace": ("Slack and brace", 1.0),
    "leg_drive":       ("Leg drive off the floor", 1.5),
    "bar_path":        ("Bar against the body", 1.5),
    "finish_position": ("Finish position", 1.0),
    "reset":           ("Reset between reps", 0.5),
    # L'axe STRUCTURE n'est pas une mecanique : ce ne sont pas des choses qu'on
    # execute, ce sont des choses qui LACHENT — le dos, les genoux, la symetrie. Il
    # garde son poids dans la note (sinon un dos qui s'effondre sort a 18/20 et le
    # chiffre ment) mais il s'affiche a part, en bandeau, avec sa propre urgence.
    # Et l'epingle ne pointe JAMAIS vers lui : "utilise moins tes lombaires" n'est
    # pas une consigne executable, la lombaire qui prend est le prix paye pour des
    # hanches hautes sans leg drive.
    # Le danger fixe l'urgence, la cause fixe l'action.
    "structure":       ("Structure under load", 2.0),
}

STRUCTURE = "structure"

# Les six mecaniques, dans l'ordre causal. C'est cette suite, et pas CRITERES, qui
# sert a choisir l'epingle et a ordonner les cartes.
MECANIQUES = tuple(c for c in CRITERES if c != STRUCTURE)

NOTE_MAX_ETAT = 3

# Des mesures de pose qui ne notent RIEN et survivent quand meme au filtrage : ce sont
# des faits du clip lus sur les images — combien de temps a dure la tiree, combien le
# verrouillage — consommes par du code et non par un bareme. `tenue_du_set` s'en sert
# pour dire qu'une derniere repetition a pris deux fois plus longtemps que la premiere,
# ce qui est un fait et non un jugement, et l'histogramme les affiche.
MESURES_TECHNIQUES = ("pull_s", "lockout_s")


def rang_causal(critere: str) -> int:
    """La place du critere dans la chaine. L'axe structure est hors chaine, donc dernier."""
    return MECANIQUES.index(critere) if critere in MECANIQUES else len(MECANIQUES)

LIBELLE = {c: t for c, (t, _) in CRITERES.items()}
POIDS = {c: p for c, (_, p) in CRITERES.items()}

# Ce que le bandeau structure dit, par note. L'urgence se lit sur la PIRE note vue sur
# une repetition, pas sur la note agregee du critere : un dos qui s'effondre sur une
# rep sur cinq ressort a 3/3 apres moyenne, et il faut quand meme dire de s'arreter.
URGENCES = {
    1: ("stop", "Stop the set: something is giving way under the load."),
    2: ("caution", "Keep an eye on this: the position starts to give under the load."),
    3: ("ok", "Your structure held from the floor to lockout."),
}


@dataclass(frozen=True)
class Etat:
    """Un etat observable, et ce qu'il vaut.

    `note` a None = etat non notable : soit purement descriptif (le type de prise),
    soit non evaluable (rien n'est visible). `rules.py` distingue les deux par le
    critere de l'indicateur.

    `persona` est l'archetype que CET etat declenche. Le persona se rattache a une
    observation precise, pas a un critere entier : "les hanches partent d'un coup"
    fait The Crane, le reste du leg drive ne fait rien.
    """

    cle: str
    description: str          # en anglais : lue par le modele, et par l'utilisateur
    note: int | None = None
    persona: str | None = None


# Present sur tout indicateur juge par le modele. C'est l'ancien "NA" : une reponse
# a "qu'est-ce que tu vois", pas un jugement. Un defaut VU est une note basse.
NON_VISIBLE = Etat(
    cle="not_visible",
    description="Not assessable on this rep: the camera angle, framing, lighting or "
                "video quality makes it impossible to see. Never use this for something "
                "you saw and disliked.",
    note=None,
)


@dataclass(frozen=True)
class Indicateur:
    """Un indicateur biomecanique observable sur une video de souleve de terre."""

    id: str                       # identifiant stable, cite par les tests et l'eval
    nom: str                      # cle technique : champ du schema, cle des mesures
    phase: Phase
    source: Source
    portee: Portee
    question: str                 # en anglais : ce que le modele doit regarder
    etats: tuple[Etat, ...]
    critere: str | None = None    # a quel critere affiche il contribue ; None = descriptif
    vue: Vue = Vue.TOUTE
    variantes: tuple[str, ...] = ("conventional", "sumo")
    mesure: str | None = None     # POSE : nom de la grandeur rendue par pose_analysis
    seuils: tuple[tuple[float, str], ...] = ()   # POSE : (borne superieure exclue, cle)
    note_source: str = ""         # pourquoi cette source, et quoi mesurer pour trancher
    non_visible: str = ""         # LLM : ce qui, precisement, empeche de repondre ici

    @property
    def plausible(self) -> tuple[float, float] | None:
        """Les bornes physiques de la mesure, hors desquelles on n'y croit pas."""
        return PLAUSIBLE.get(self.mesure) if self.mesure else None

    @property
    def tous_les_etats(self) -> tuple[Etat, ...]:
        """Les etats declares, plus `not_visible` pour ceux que le modele juge."""
        if self.source is Source.POSE:
            return self.etats
        # La cle reste `not_visible` (rules.py la reconnait) ; seul le texte est propre
        # au champ, pour dire ce qui bloque : les disques cachent le pied, la vue est de
        # profil... Le texte generique ne sert que si l'indicateur n'en donne pas.
        if self.non_visible:
            return self.etats + (Etat(NON_VISIBLE.cle, self.non_visible),)
        return self.etats + (NON_VISIBLE,)

    def etat(self, cle) -> Etat | None:
        if isinstance(cle, Enum):
            cle = cle.value
        return next((e for e in self.tous_les_etats if e.cle == cle), None)

    def etat_depuis_mesure(self, valeur) -> str | None:
        """POSE : la grandeur mesuree devient un etat. None si non mesurable.

        Sans `seuils`, la mesure est categorielle : elle rend deja une cle d'etat
        (la cascade rend "sumo" ou "conventional", pas un nombre a decouper).
        """
        if valeur is None:
            return None
        if not self.seuils:
            return valeur if self.etat(valeur) is not None else None
        for borne, cle in self.seuils:
            if valeur < borne:
                return cle
        return self.seuils[-1][1]

    def consigne(self) -> str:
        """La description portee par le champ du schema, en anglais."""
        lignes = "\n".join(f"- '{e.cle}': {e.description}" for e in self.tous_les_etats)
        return (f"{self.question}\nPick the ONE option that matches what you actually "
                f"see. Judge this on its own, do not copy another repetition.\n{lignes}")


INF = float("inf")

# Sous cette confiance de reperes, plus aucune mesure de pose n'est croyable.
# C'est le seuil bas de C03 : en dessous, le squelette est devine.
VISIBILITE_MIN = 0.40

# Bornes physiques de chaque mesure. Une valeur au-dela n'est PAS un mauvais lift :
# c'est le symptome d'un reperage de phase qui a echoue, et la mesure est jetee.
#
# Sans ces bornes, le systeme note avec assurance a partir de bruit. Mesure sur
# conventionnal_deadlift_12 : une repetition sortait un tibia a 157 degres et un buste
# bascule de 142, et c'est elle qui donnait son persona au clip ; en parallele la
# derive de main valait 1,0 a 1,4 femur sur toutes les reps — soit 40 a 57 cm de
# barre — et produisait un 1/3 "dangereux" la ou l'humain repond "pas visible".
#
# Une mesure jetee ne devient pas une mauvaise note : elle disparait, et le critere
# s'affiche "not visible". C'est ainsi que la pose s'abstient.
PLAUSIBLE: dict[str, tuple[float, float]] = {
    "view": (0.0, 1.0),
    "visibility": (0.0, 1.0),
    "hip_ratio": (0.0, 1.5),              # hanches entre epaules et genoux, avec marge
    "shoulder_bar_offset": (-1.5, 1.5),   # en fractions de femur
    "shin_deg": (0.0, 60.0),              # au-dela, ce n'est plus un tibia
    "rise_ratio": (0.0, 10.0),            # 9.99 est la sentinelle "les epaules ne montent pas"
    "pitch_deg": (-45.0, 45.0),           # variation d'inclinaison du buste sur un tiers de tiree
    "drift_ratio": (0.0, 1.0),            # 1 femur de derive de main est deja enorme
    "valgus_ratio": (-0.5, 0.5),
    "sticking": (-1.0, 1.0),
    "pull_s": (0.3, 8.0),                 # sous 0,3 s la tiree n'a pas ete vue
    "hip_lockout_deg": (120.0, 190.0),
    "knee_lockout_deg": (120.0, 190.0),
    "lean_back_deg": (0.0, 45.0),
    "lockout_s": (0.0, 5.0),
    "descent_order": (-60.0, 60.0),
}


# =============================================================================
# CONTEXTE — vrai pour toute la video, demande une seule fois
# =============================================================================

C01 = Indicateur(
    id="C01", nom="variant", phase=Phase.CONTEXTE, source=Source.POSE, portee=Portee.SET,
    question="Sumo or conventional?",
    etats=(Etat("sumo", "Hands inside the legs, wide stance."),
           Etat("conventional", "Hands outside the legs, hip-width stance.")),
    mesure="variant",
    note_source="Cascade largeur -> profondeur de pose_analysis : 39/39 sur le jeu "
                "complet, 12/12 sur les clips arrives apres le figeage des seuils. "
                "Ne pas redemander au modele, il fait moins bien.",
)

C02 = Indicateur(
    id="C02", nom="camera_view", phase=Phase.CONTEXTE, source=Source.POSE, portee=Portee.SET,
    question="Where is the camera relative to the lifter?",
    etats=(Etat("side", "Filmed from the side: bar path and joint angles are readable."),
           Etat("three_quarter", "Three-quarter view: angles are projected and only "
                                "large changes are meaningful."),
           Etat("front", "Filmed from the front: knee tracking is readable, bar path is not.")),
    mesure="view", seuils=((0.30, "side"), (0.60, "three_quarter"), (INF, "front")),
    note_source="Ecart des epaules rapporte a la longueur du tronc. C'est cette valeur "
                "qui autorise ou suspend les indicateurs marques PROFIL et FACE.",
)

C03 = Indicateur(
    id="C03", nom="pose_quality", phase=Phase.CONTEXTE, source=Source.POSE, portee=Portee.SET,
    question="How reliable are the body landmarks over the clip?",
    etats=(Etat("good", "Landmarks are stable and visible throughout."),
           Etat("fair", "Landmarks are usable but drop out on part of the clip."),
           Etat("poor", "Landmarks are unreliable: measurements are suspended.")),
    mesure="visibility", seuils=((0.40, "poor"), (0.70, "fair"), (INF, "good")),
    note_source="Une bonne confiance de pose ne prouve pas que la barre est visible : "
                "cet indicateur ne conditionne que les mesures POSE.",
)

C04 = Indicateur(
    id="C04", nom="equipment", phase=Phase.CONTEXTE, source=Source.LLM, portee=Portee.SET,
    question="What is being lifted, and with what equipment?",
    etats=(Etat("barbell", "A standard barbell with plates on the floor."),
           Etat("trap_bar", "A trap bar / hex bar: the lifter stands inside the frame."),
           Etat("other", "Something else: dumbbells, Smith machine, blocks, deficit, "
                         "or a variant that is not a standard floor deadlift.")),
    note_source="Aucun repere de pose ne distingue une trap bar d'une barre droite. "
                "Sert a ne pas noter un mouvement avec le mauvais bareme.",
)

C05 = Indicateur(
    id="C05", nom="grip", phase=Phase.CONTEXTE, source=Source.LLM, portee=Portee.SET,
    question="How does the lifter grip the bar?",
    etats=(Etat("double_overhand", "Both palms facing the lifter (double overhand)."),
           Etat("mixed", "One palm forward, one back (mixed grip)."),
           Etat("hook", "Hook grip: the thumb is trapped under the fingers."),
           Etat("straps", "Lifting straps are used.")),
    note_source="Le detail des mains est trop fin pour MediaPipe (les doigts ne sont pas "
                "des reperes de Pose). Descriptif : n'entre dans aucune note.",
)

# =============================================================================
# Les criteres, reecrits le 2026-09-11 (soir) sur une regle : des FRONTIERES, pas
# des intensites.
# =============================================================================
#
# Le catalogue precedent demandait "un peu", "nettement", "presque" — des seuils
# subjectifs invisibles. Mesure sur 260 reponses : zero etat a 2/3, le modele se
# rabattait sur l'etat par defaut des qu'il fallait trancher une gradation. Les
# questions ci-dessous (voir AGENTS.md, regles 2.1 et 2.2) remplacent chaque
# gradation par une geometrie binaire : une ligne est coupee ou ne l'est pas, un angle
# vaut 180 ou non, une distance change ou ne change pas. Elles nomment une IMAGE
# precise ("the exact frame immediately preceding the first upward movement") et une
# seule affirmation verifiable dessus — le point commun des huit champs propres de
# l'audit de pr_160.
#
# Les noms de champs, les questions, les etats et les notes sont ceux de la liste
# humaine, tels quels. Ce qui vient du code d'avant : les personas, reportes sur
# l'etat equivalent ; le critere de rattachement ; CONSEILS ; ENCHAINEMENTS.
#
# Disparus avec cette passe : `arms_long` + `slack_pull` + `jerky_start` (fondus dans
# `arms_tension_at_setup` : un coude qui se tend AU moment du decollage EST le slack
# arrache), `thoracic_under_load` et `asymmetry` (pas de question equivalente). Les
# personas The T-Rex et The Helicopter partent avec eux.
#
# Chaque champ porte son propre texte `not_visible` : il dit precisement ce qui
# empeche de repondre (les disques cachent le pied, la vue est de profil...) au lieu
# du texte generique.


# -----------------------------------------------------------------------------
# PHASE 1 — le setup, sur l'image qui precede le premier mouvement vers le haut
# -----------------------------------------------------------------------------

S04 = Indicateur(
    id="S04", nom="bar_over_midfoot_topology", phase=Phase.SETUP, source=Source.A_TESTER,
    portee=Portee.REP, critere="start_position", vue=Vue.PROFIL,
    question="Pause the video at the exact frame immediately preceding the first upward "
             "movement of the lifter's body. Look vertically down from the barbell to the "
             "lifter's shoe. Which specific part of the shoe is physically located directly "
             "underneath the barbell sleeve/shaft?",
    etats=(Etat("bar_over_ankle_or_shin", "The barbell is positioned over the ankle joint "
                                          "or is pressed hard against the shin, fully "
                                          "exposing the laces and toes in front of it.", 1),
           Etat("bar_over_laces", "The barbell is positioned directly over the tongue/laces "
                                  "of the shoe (the midfoot).", 3),
           Etat("bar_over_toes_or_floor", "The barbell is positioned over the toe box of the "
                                          "shoe, or completely in front of the shoe over the "
                                          "empty floor.", 2)),
    non_visible="The plates completely block the view of the shoe.",
    note_source="A TESTER : au setup la main tient la barre, donc x_poignet est un proxy "
                "bien meilleur que pendant la tiree. Mais le poignet n'est pas le centre de "
                "la barre, et le milieu du pied demande cheville ET orteil visibles. "
                "A mesurer contre une annotation image avant de basculer en POSE.",
)

S02 = Indicateur(
    id="S02", nom="shoulders_over_bar_gravity", phase=Phase.SETUP, source=Source.LLM,
    portee=Portee.REP, critere="start_position", vue=Vue.PROFIL,
    question="Pause the video at the exact frame immediately preceding the first upward "
             "movement of the lifter's body. Focus ONLY on the lifter's arm (from the "
             "shoulder joint to the hand holding the bar). Analyze the angle of the arm "
             "relative to the floor in 3D space, acting as a plumb line.",
    # Le bras est le fil a plomb : epaule derriere la main = epaules derriere la barre.
    etats=(Etat("arm_angled_forward", "The shoulder joint is closer to the lifter's heels "
                                      "than the hand is. The arm creates a diagonal line "
                                      "pointing forward towards the bar.", 1),
           Etat("arm_perfectly_vertical", "The arm acts as a perfect vertical plumb line, "
                                          "strictly perpendicular to the floor (90 degrees). "
                                          "The shoulder joint is stacked exactly above the "
                                          "hand.", 3),
           Etat("arm_angled_backward", "The shoulder joint is closer to the lifter's toes "
                                       "than the hand is. The arm creates a diagonal line "
                                       "pointing backward towards the lifter's body.", 2)),
    non_visible="The arm is obscured.",
    note_source="Etait POSE (shoulder_bar_offset) jusqu'au 2026-09-09. Revient en LLM : "
                "la position des epaules PAR RAPPORT A LA BARRE demande de voir la barre, "
                "ce que la pose ne fait pas — elle lisait le poignet.",
)

S01 = Indicateur(
    id="S01", nom="hip_height_via_femur", phase=Phase.SETUP, source=Source.LLM,
    portee=Portee.REP, critere="start_position", vue=Vue.PROFIL,
    question="Pause the video at the exact frame immediately preceding the first upward "
             "movement of the lifter's body. Focus strictly on the lifter's femur (the "
             "thigh bone connecting the knee to the hip). Analyze the physical inclination "
             "of the femur relative to the floor.",
    # Le femur remplace la comparaison de distances : un os rigide, une pente, une image.
    etats=(Etat("femur_angled_upward", "The femur creates a clear upward diagonal line from "
                                       "the knee to the hip, AND the torso also creates a "
                                       "diagonal line.", 3),
           Etat("femur_parallel_or_downward", "The femur is exactly parallel to the floor, "
                                              "or the hip joint sits strictly lower than the "
                                              "knee joint (downward angle).", 1,
                persona="The Squatter"),
           Etat("torso_parallel_to_floor", "The hip joint is positioned so high that the "
                                           "torso is parallel to the floor, and the femurs "
                                           "are nearly vertical (knees locked or almost "
                                           "locked).", 2)),
    non_visible="The thighs are obscured.",
    note_source="Etait POSE (hip_ratio) jusqu'au 2026-09-09, retire avec les 16 autres. "
                "Revient en LLM : c'est la premiere mecanique enseignable du geste. La "
                "mesure n'est PAS restauree — on repose la question, on ne rebranche pas "
                "le ratio.",
)

# Le dos se demande en DEUX questions, une par segment, et non en un choix exclusif.
# Mesure du 2026-09-10 sur pr_160 : en texte libre le modele decrit les deux segments
# separement et correctement ; somme de designer UN segment il nommait le dominant.
S05 = Indicateur(
    id="S05", nom="lumbar_at_setup", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="structure",
    question="Pause the video at the exact frame immediately preceding the first upward "
             "movement of the lifter's body. Draw an imaginary line connecting the lifter's "
             "pelvis (sacrum) to the bottom of their rib cage. Analyze the geometric shape "
             "of this lower back segment.",
    etats=(Etat("lumbar_straight_or_concave", "The line forms a straight plane or a visible "
                                              "inward curve (extension/neutral).", 3),
           Etat("lumbar_convex", "The line forms a strict outward curve (flexion/rounded) "
                                 "pointing away from the torso.", 1,
                persona="The Fishing Rod")),
    non_visible="Clothing or angle prevents a clear view of the lower back contour.",
    note_source="LIMITE DURE : aucun repere entre epaules et hanches. Le tronc est un "
                "segment droit pour MediaPipe. Ne jamais fabriquer un proxy ici.",
)

S10 = Indicateur(
    id="S10", nom="thoracic_at_setup", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="structure",
    question="Pause the video at the exact frame immediately preceding the first upward "
             "movement of the lifter's body. Draw an imaginary line connecting the bottom of "
             "the lifter's rib cage to the base of their neck. Analyze the geometric shape "
             "of this upper back segment.",
    # Les DEUX etats valent 3 : un haut du dos arrondi et fige des le depart est une
    # technique assumee, pas une faute. L'indicateur EXISTE pour que le modele puisse
    # dire ce qu'il voit du thoracique sans que ce soit sa reponse a la question
    # lombaire. (La liste humaine du 2026-09-11 soir le mettait a 1 ; remis a 3 le
    # meme soir, avec un poids de 2 sur `structure` ca sortait en bandeau "stop" un
    # lifter qui tire volontairement le haut du dos rond.)
    etats=(Etat("thoracic_straight_or_concave", "The line forms a straight plane or an "
                                                "inward curve.", 3),
           Etat("thoracic_convex", "The line forms a strict outward curve (rounded "
                                   "shoulders/flexion).", 3)),
    non_visible="Clothing or angle prevents a clear view of the upper back contour.",
    note_source="Meme limite dure que S05. Separe du lombaire le 2026-09-10 pour que "
                "reconnaitre l'arrondi ici ne soit plus la reponse a la question lombaire.",
)

S06 = Indicateur(
    id="S06", nom="arms_tension_at_setup", phase=Phase.SETUP, source=Source.A_TESTER,
    portee=Portee.REP, critere="slack_and_brace",
    question="Analyze the sequence leading up to the exact frame the plates leave the "
             "floor. Look strictly at the angle formed by the shoulder, elbow, and wrist "
             "joints. Does this geometric angle change exactly as the weight leaves the "
             "floor?",
    # Un seul champ pour ce qui etait trois (arms_long, slack_pull, jerky_start) : un
    # coude qui se tend AU moment ou les disques decollent, c'est le slack arrache, et
    # c'est le seul evenement observable de cette famille. D'ou le critere
    # slack_and_brace et le persona The Grip & Rip, pas The T-Rex.
    etats=(Etat("elbow_locked_prior", "The arm forms a strict 180-degree straight line "
                                      "BEFORE the plates leave the floor, and this exact "
                                      "180-degree angle remains static during liftoff.", 3),
           Etat("elbow_angle_changes", "The elbow angle is less than 180 degrees (bent) "
                                       "and/or visually straightens exactly AT or AFTER the "
                                       "moment the plates leave the floor (yanking the "
                                       "bar).", 1, persona="The Grip & Rip")),
    non_visible="The arms are obscured.",
    note_source="A TESTER : l'angle epaule-coude-poignet est calculable, mais une flexion "
                "de 10-15 deg est dans le bruit de la projection, et le bras oppose est "
                "souvent occulte. Le CHANGEMENT d'angle au decollage est plus robuste que "
                "l'angle absolu — a mesurer sur une passe dense.",
)

S08 = Indicateur(
    id="S08", nom="foot_orientation", phase=Phase.SETUP, source=Source.LLM, portee=Portee.SET,
    question="How are the feet oriented?",
    etats=(Etat("flared", "The toes are flared outwards."),
           Etat("forward", "The toes point roughly forward.")),
    note_source="L'angle 3D entre les deux pieds a ete mesure (AUC 0.82) puis ecarte : "
                "il subit le meme repliement que la stance en vue de profil. Descriptif "
                "uniquement, aucun angle optimal universel n'existe.",
)


# -----------------------------------------------------------------------------
# PHASE 2 — le decollage et la tiree
# -----------------------------------------------------------------------------

L01 = Indicateur(
    id="L01", nom="initiation_sequence", phase=Phase.DECOLLAGE, source=Source.LLM,
    portee=Portee.REP, critere="leg_drive", vue=Vue.PROFIL,
    question="Analyze the sequence from the exact frame the lifter initiates physical "
             "effort (T0) to the exact frame the plates break physical contact with the "
             "floor (T1). Focus ONLY on the angle of the torso relative to the floor. "
             "Compare this angle at T0 and at T1.",
    # Une seule grandeur (l'angle du buste), deux images nommees. Sur la run A, le
    # modele repondait "hanches et epaules ensemble" dans la meme reponse que "buste
    # horizontal au depart" : la question ne lui laisse plus deux grandeurs a concilier.
    etats=(Etat("torso_angle_decreases", "The torso angle becomes visibly smaller (more "
                                         "horizontal to the floor) between T0 and T1. The "
                                         "hips rise at a faster rate than the shoulders "
                                         "before the bar leaves the floor.", 1,
                persona="The Crane"),
           Etat("torso_angle_constant", "The torso angle remains strictly identical between "
                                        "T0 and T1. The hips and shoulders rise at the exact "
                                        "same rate to lift the bar.", 3),
           # Pas de persona : la cause est en amont (hip_height_via_femur, dans
           # ENCHAINEMENTS), et c'est elle que l'epingle doit designer.
           Etat("torso_angle_increases", "The torso angle becomes visibly larger (more "
                                         "vertical to the floor) between T0 and T1. The "
                                         "shoulders rise at a faster rate than the hips "
                                         "before the bar leaves the floor.", 2)),
    non_visible="Lighting or framerate prevents a clear comparison.",
    note_source="Etait POSE (rise_ratio) jusqu'au 2026-09-09. Revient en LLM : c'est LE "
                "defaut n.1 du souleve de terre.\n"
                "'Les hanches decollent' n'est JAMAIS la faute a rapporter telle quelle : "
                "c'est la CORRECTION d'un mauvais depart, en cours de mouvement. Le conseil "
                "est au depart, d'ou l'entree ENCHAINEMENTS depuis hip_height_via_femur.",
)

L04 = Indicateur(
    id="L04", nom="bar_left_floor", phase=Phase.DECOLLAGE, source=Source.LLM,
    portee=Portee.REP,
    question="Did the bar actually leave the floor in this segment?",
    etats=(Etat("yes", "The bar left the floor and was lifted: this is a real repetition."),
           Etat("no", "The bar stayed on the floor, or was already down and the athlete "
                       "simply stood back up: this is NOT a repetition."),
           Etat("incomplete", "The bar left the floor but came back down before lockout: "
                             "a real attempt that was not completed.")),
    note_source="LA question que la pose ne peut pas trancher : elle voit le corps, pas la "
                "barre, et se redresser apres avoir repose la barre produit exactement le "
                "meme mouvement. Champ dedie et jamais 'not_visible' : confondre les deux "
                "supprimerait une vraie rep filmee sous un mauvais angle. "
                "'incomplete' est nouveau : une tentative reelle reste analysable, ses "
                "phases non atteintes deviennent non applicables.",
)

P02 = Indicateur(
    id="P02", nom="bar_path_at_knees_topology", phase=Phase.TIREE, source=Source.A_TESTER,
    portee=Portee.REP, critere="bar_path", vue=Vue.PROFIL,
    question="Play the video from liftoff until the barbell passes the lifter's knees. Look "
             "strictly at the physical distance between the barbell shaft and the "
             "kneecaps. Does the barbell physically loop forward to navigate around the "
             "knees?",
    etats=(Etat("bar_slides_past_knees", "The barbell maintains its trajectory without "
                                         "creating any forward visual gap. It clears the "
                                         "knees smoothly without horizontal forward "
                                         "deviation.", 3),
           Etat("bar_deviates_forward", "A visual horizontal gap opens up between the "
                                        "trajectory of the bar and the shins/knees because "
                                        "the bar moves forward (away from the lifter) to "
                                        "avoid hitting the kneecaps.", 1)),
    non_visible="The knees or the bar are obscured.",
    note_source="A TESTER : la relation temporelle poignet/genou est calculable de profil, "
                "mais la boucle se joue sur quelques centimetres de barre, pas de main.",
)

P03 = Indicateur(
    id="P03", nom="bar_leg_daylight", phase=Phase.TIREE, source=Source.LLM,
    portee=Portee.REP, critere="bar_path", vue=Vue.PROFIL,
    question="Analyze the video from the moment the plates leave the floor until the "
             "barbell reaches the hips. Look strictly at the physical space (daylight) "
             "between the barbell and the lifter's legs, and project a vertical line from "
             "the barbell to the floor.",
    # Le cran du milieu est une frontiere (la verticale tombe dans la chaussure ou
    # devant), pas une intensite ("brievement", "un peu").
    etats=(Etat("zero_daylight", "There is absolutely zero visual daylight between the "
                                 "barbell and the lifter's legs at any point. They maintain "
                                 "physical contact.", 3),
           Etat("daylight_over_shoe", "Daylight appears between the bar and the legs, BUT a "
                                      "vertical line dropped from the barbell still lands "
                                      "inside the footprint of the lifter's shoe.", 2),
           Etat("daylight_beyond_shoe", "Daylight appears between the bar and the legs, AND "
                                        "a vertical line dropped from the barbell lands "
                                        "strictly in front of the lifter's shoe (on the "
                                        "empty floor).", 1, persona="The Pendulum")),
    non_visible="Plates or angle obscure the gap.",
    note_source="Le contact barre-jambe n'est pas observable par la pose : il faut voir la "
                "barre.",
)

P04 = Indicateur(
    id="P04", nom="lumbar_geometry_delta", phase=Phase.TIREE, source=Source.LLM,
    portee=Portee.REP, critere="structure",
    question="Compare the exact frame just before liftoff (T0) to the exact frame where the "
             "barbell reaches the kneecaps (T1). Look strictly at the lumbar spine segment "
             "(pelvis to bottom ribs). Does the geometric shape of this segment change "
             "between T0 and T1?",
    # `lumbar_geometry_constant` est DESCRIPTIF (note None), comme l'ancien `unchanged`
    # depuis le 2026-09-11 : "ca ne bouge pas" n'est pas un merite — une lombaire
    # convexe au depart et qui le reste n'a pas a s'afficher avec un badge vert. Ce que
    # la lombaire vaut au depart est dit par S05.
    etats=(Etat("lumbar_geometry_constant", "The exact shape of the lumbar segment at T0 "
                                            "remains strictly identical at T1."),
           Etat("lumbar_becomes_convex", "The lumbar segment adds flexion between T0 and "
                                         "T1, creating a new or more pronounced outward "
                                         "curve (rounding under load).", 1,
                persona="The Fishing Rod")),
    non_visible="The lower back is obscured.",
    note_source="LIMITE DURE, comme S05 : pas de repere rachidien. C'est le critere ou une "
                "mauvaise note est une blessure et non un kilo perdu. Il reste au modele, "
                "definitivement. Deux images nommees et non trois : decouper en trois "
                "questions quasi identiques poussait a une reponse uniforme (mesure du "
                "2026-09-11).",
)

P05 = Indicateur(
    id="P05", nom="knee_valgus_tracking", phase=Phase.TIREE, source=Source.LLM,
    portee=Portee.REP, critere="structure", vue=Vue.FACE,
    question="Watch the pull from a front or 3/4 angle. Draw a strict vertical line upward "
             "from the inner edge of the lifter's shoe (the side closest to the other "
             "foot). Track the center of the kneecaps (patellas) during the ascent relative "
             "to this line.",
    etats=(Etat("knees_outside_line", "The center of both kneecaps remains strictly outside "
                                      "(wider than) the vertical line from the inner edge of "
                                      "the shoe.", 3),
           Etat("knees_touch_line", "The center of one or both kneecaps moves inward and "
                                    "touches the vertical line, but does not cross it.", 2),
           Etat("knees_cross_inside_line", "The center of one or both kneecaps physically "
                                           "crosses inside (narrower than) the vertical line "
                                           "from the inner edge of the shoe.", 1,
                persona="The X-Wing")),
    non_visible="Pure side angle makes this tracking impossible.",
    note_source="Etait POSE (valgus_ratio) jusqu'au 2026-09-09. Axe STRUCTURE : un genou "
                "qui rentre n'est pas une etape qu'on execute mal, c'est une articulation "
                "qui ne tient pas sous charge. Deux causes qu'aucune video ne separe "
                "(rotation externe ou faiblesse) : le conseil nomme l'observation et donne "
                "le test.",
)

P08 = Indicateur(
    id="P08", nom="vertical_velocity_hitch", phase=Phase.TIREE, source=Source.A_TESTER,
    portee=Portee.REP, critere="finish_position",
    question="Track the upward movement of the barbell on the Y-axis from the floor to the "
             "hips. Does the vertical upward velocity ever drop to zero or become negative "
             "before the lockout?",
    etats=(Etat("continuous_positive_velocity", "The barbell's Y-axis height strictly "
                                                "increases on every single frame until "
                                                "lockout.", 3),
           Etat("velocity_hits_zero_or_negative", "The barbell's Y-axis height stops "
                                                  "increasing (pauses) or decreases (drops "
                                                  "slightly) while resting on the lifter's "
                                                  "thighs (hitching).", 1,
                persona="The Hitcher")),
    non_visible="Framerate prevents tracking the bar's continuous height.",
    note_source="A TESTER : une re-flexion du genou apres le passage des genoux est une "
                "non-monotonie de l'extension, calculable sur le signal existant. Mais un "
                "ralentissement n'est pas un hitch : annoter d'abord.",
)


# -----------------------------------------------------------------------------
# PHASE 3 — le verrouillage
# -----------------------------------------------------------------------------

K07 = Indicateur(
    id="K07", nom="lockout_extension", phase=Phase.LOCKOUT, source=Source.LLM,
    portee=Portee.REP, critere="finish_position", vue=Vue.PROFIL,
    question="Pause the video at the exact frame of maximum upward completion (the "
             "lockout). Look strictly at the angle of the knee joint and the hip joint.",
    etats=(Etat("full_180_extension", "Both the knee joint and the hip joint form a strict "
                                      "180-degree straight line.", 3),
           Etat("hip_angle_under_180", "The knee joint is at 180 degrees, but the hip joint "
                                       "angle remains visibly less than 180 degrees (torso "
                                       "leaning forward).", 2, persona="The Soft-Lock"),
           Etat("knee_angle_under_180", "The knee joint angle remains visibly less than "
                                        "180 degrees (knees bent).", 1,
                persona="The Soft-Lock")),
    non_visible="The joints are obscured.",
    note_source="2026-09-09 : fusion de K01 (hip_lockout_deg) et K02 (knee_lockout_deg), "
                "tous deux POSE et retires le meme jour. C'est la mecanique 'position "
                "d'arrivee'.",
)

K03 = Indicateur(
    id="K03", nom="sagittal_torso_angle", phase=Phase.LOCKOUT, source=Source.LLM,
    portee=Portee.REP, critere="finish_position", vue=Vue.PROFIL,
    question="Pause the video at the exact frame of maximum upward completion (the "
             "lockout). Analyze the angle of the lifter's torso relative to the floor in "
             "3D space.",
    etats=(Etat("torso_perpendicular", "The torso is perfectly perpendicular to the floor "
                                       "(90 degrees).", 3),
           Etat("torso_obtuse_angle", "The torso forms an obtuse angle relative to the floor "
                                      "in front of the lifter. The lifter is leaning "
                                      "backward away from the barbell (lumbar "
                                      "hyperextension).", 1, persona="The Over-Extender")),
    non_visible="The torso is obscured.",
    note_source="Etait POSE (lean_back_deg) jusqu'au 2026-09-09. Revient en LLM. Absorbe "
                "K05 `lockout_balance` : 'le poids part derriere les talons' et "
                "'hyperextension lombaire en haut' decrivaient le meme instant.",
)

K04 = Indicateur(
    id="K04", nom="shoulder_elevation_delta", phase=Phase.LOCKOUT, source=Source.A_TESTER,
    portee=Portee.REP, critere="finish_position",
    question="Compare the vertical physical distance between the lifter's shoulder joint "
             "and their ear lobe at two moments: when the barbell is at the knees (T1), and "
             "at the final lockout (T2).",
    etats=(Etat("distance_remains_constant", "The vertical distance between the shoulder "
                                             "and the ear is strictly identical at T1 and "
                                             "T2.", 3),
           Etat("distance_decreases", "The vertical distance between the shoulder and the "
                                      "ear visibly decreases at T2 (the shoulders move "
                                      "closer to the ears/shrugging).", 1,
                persona="The Shrugger")),
    non_visible="The neck/shoulder area is obscured.",
    note_source="A TESTER : l'elevation de l'epaule par rapport a l'oreille est calculable, "
                "mais elle se confond avec un simple redressement du cou. A annoter.",
)


# -----------------------------------------------------------------------------
# PHASE 4 — la descente et la transition
# -----------------------------------------------------------------------------

E02 = Indicateur(
    id="E02", nom="descent_hand_contact", phase=Phase.DESCENTE, source=Source.LLM,
    portee=Portee.REP, critere="reset",
    question="Analyze the sequence from the final lockout until the plates physically "
             "touch the floor again. Look strictly at the lifter's hands.",
    # "Controlee" / "rapide mais controlee" etaient des intensites. Ce qui se voit, c'est
    # si les mains lachent la barre avant que les disques touchent — rien d'autre.
    etats=(Etat("hands_maintain_contact", "The lifter's fingers remain wrapped around or in "
                                          "physical contact with the barbell until the exact "
                                          "frame the plates hit the floor.", 3),
           Etat("hands_break_contact", "Visual space appears between the lifter's hands and "
                                       "the barbell BEFORE the plates touch the floor (the "
                                       "bar is dropped).", 1)),
    # Remplace l'ancien etat `cut_off` : une descente coupee par la fin de la video est
    # une descente qu'on n'a pas vue.
    non_visible="The hands leave the video frame during the descent.",
    note_source="Il faut voir la barre et le sol : la pose ne voit ni l'un ni l'autre.",
)

E03 = Indicateur(
    id="E03", nom="rep_transition_velocity", phase=Phase.DESCENTE, source=Source.LLM,
    portee=Portee.REP, critere="reset",
    question="Observe the exact moment the barbell touches the floor between two "
             "repetitions. Track the barbell's movement on the Y-axis. How long does the "
             "Y-axis velocity remain exactly at zero?",
    # Le touch-and-go reste a 3 : c'est un style, pas une faute. Seul le rebond descend
    # a 1, parce qu'il remplace la reconstruction du placement par de l'elastique.
    etats=(Etat("zero_velocity_maintained", "The barbell's Y-axis velocity reaches zero and "
                                            "remains exactly at zero for at least 0.5 "
                                            "seconds before the next pull begins (dead "
                                            "stop).", 3),
           Etat("immediate_positive_velocity", "The barbell touches the floor and its Y-axis "
                                               "velocity becomes positive again instantly "
                                               "(under 0.5 seconds), but the plates do not "
                                               "physically bounce off the floor (touch and "
                                               "go).", 3),
           Etat("impact_rebound", "The plates strike the floor and visibly rebound, causing "
                                  "the bar to bounce upward using momentum.", 1,
                persona="The Trampolinist")),
    # L'ancien `last_rep` (descriptif) est fondu dans le non-visible : sur une serie
    # d'une seule rep le critere sort entier du denominateur, comme avant.
    non_visible="The video ends, this is the final repetition, or the floor contact is "
                "cut off.",
    note_source="2026-09-09 : devient la mecanique 'reset', la version enseignable de "
                "'est-ce que ta serie a tenu'.",
)


# =============================================================================
# Mesures de pose, HORS SCHEMA — definies pour pouvoir etre rebranchees
# =============================================================================
#
# AUCUN indicateur `Source.POSE` n'est note depuis le 2026-09-09 (instruction de
# conventionnal_deadlift_12 : un lift propre note 19/20 sur deux mesures fausses). La
# pose reste indispensable ailleurs — cascade sumo/conventionnel 39/39, detection des
# repetitions 142/146. Pour rebrancher l'un d'eux : le remettre dans INDICATEURS avec
# ses entrees dans CONSEILS.

S03 = Indicateur(
    id="S03", nom="shin_angle", phase=Phase.SETUP, source=Source.POSE, portee=Portee.REP,
    critere="start_position", vue=Vue.PROFIL, variantes=("sumo",),
    question="How vertical are the shins at the start? (sumo)",
    etats=(Etat("vertical", "The shins are vertical or nearly so: the wedge is in place.", 3),
           Etat("angled", "The shins lean forward, pushing the knees over the bar.", 2)),
    mesure="shin_deg", seuils=((20.0, "vertical"), (INF, "angled")),
    note_source="Angle du segment cheville-genou par rapport a la verticale de l'image. "
                "Sumo seulement : en conventionnel un tibia incline est normal.",
)

# Reecrit le 2026-09-11. `against_the_shins` (3/3) est supprime : sur pr_160 le modele
# le choisissait avec une description qui ne parlait jamais du pied — "the barbell is
# positioned directly against the shins, with no visible gap". C'est une reponse a une
# AUTRE question (le contact tibia, que `bar_leg_contact` pose deja), et elle valait 3.
# La question devient une projection verticale sur le pied, sur une image nommee, et
# dit dans quelle vue elle est repondable — meme precedent que `knee_valgus`.

L02 = Indicateur(
    id="L02", nom="torso_pitch", phase=Phase.DECOLLAGE, source=Source.POSE,
    portee=Portee.REP, critere="leg_drive", vue=Vue.PROFIL,
    question="Does the torso pitch further forward as the bar breaks the floor?",
    etats=(Etat("held", "The torso angle holds as the bar leaves the floor.", 3),
           Etat("pitches_forward", "The torso pitches further forward at liftoff: the hips win "
                           "the race and the back takes the load.", 2)),
    mesure="pitch_deg", seuils=((8.0, "held"), (INF, "pitches_forward")),
    note_source="Variation de l'angle du segment epaule-hanche par rapport a la verticale, "
                "entre le decollage et le premier tiers. On mesure l'inclinaison du buste, "
                "jamais la flexion du rachis.",
)


P01 = Indicateur(
    id="P01", nom="hand_drift", phase=Phase.TIREE, source=Source.POSE,
    portee=Portee.REP, critere="bar_path", vue=Vue.PROFIL,
    question="How far does the hand travel horizontally during the pull?",
    etats=(Etat("close", "The hands stay over the same point through the pull.", 3),
           Etat("moderate_drift", "The hands drift forward and come back.", 2),
           Etat("large_drift", "The hands drift well away from the body, lengthening the "
                                "lever on the lower back.", 1, persona="The Pendulum")),
    mesure="drift_ratio", seuils=((0.35, "close"), (0.70, "moderate_drift"), (INF, "large_drift")),
    note_source="Ecart 5e-95e centile de (x_poignet - x_cheville) pendant la tiree, "
                "rapporte a la longueur du femur. Mesure par rapport aux CHEVILLES pour "
                "qu'un panoramique de camera ne compte pas comme une derive. "
                "ATTENTION : c'est la main, pas la barre. Le nom du champ le dit.",
)


P06 = Indicateur(
    id="P06", nom="sticking_point", phase=Phase.TIREE, source=Source.POSE,
    portee=Portee.REP, critere=None, vue=Vue.PROFIL,
    question="Where does the bar slow down most during the pull?",
    etats=(Etat("none", "The pull is continuous, with no marked slowdown."),
           Etat("off_the_floor", "The lift is hardest breaking the floor."),
           Etat("at_the_knees", "The lift slows down around knee height."),
           Etat("lockout", "The lift slows down near the top.")),
    mesure="sticking", seuils=((0.0, "none"), (0.34, "off_the_floor"), (0.67, "at_the_knees"), (INF, "lockout")),
    note_source="Position relative du minimum de vitesse d'extension dans la tiree. "
                "Descriptif et non note : un grind n'est pas une faute technique. "
                "Sert a localiser l'echec dans le conseil.",
)


P07 = Indicateur(
    id="P07", nom="pull_duration", phase=Phase.TIREE, source=Source.POSE,
    portee=Portee.REP, critere=None,
    question="How long does the concentric take?",
    etats=(Etat("fast", "Under a second: the bar moves easily."),
           Etat("normal", "One to two seconds."),
           Etat("grind", "Over two seconds: a slow grind.")),
    mesure="pull_s", seuils=((1.0, "fast"), (2.0, "normal"), (INF, "grind")),
    note_source="Difference d'horodatages reels entre decollage et verrouillage. "
                "Descriptif : la vitesse seule ne prouve aucune degradation technique. "
                "C'est en revanche la mesure OBJECTIVE de la tenue du set (voir rules.py).",
)


K06 = Indicateur(
    id="K06", nom="lockout_duration", phase=Phase.LOCKOUT, source=Source.POSE,
    portee=Portee.REP, critere=None,
    question="How long does the top of the lift take to complete?",
    etats=(Etat("immediate", "The lockout is immediate."),
           Etat("slow", "The lockout takes a moment to complete."),
           Etat("stalls", "The lift stalls at the top before finishing.")),
    mesure="lockout_s", seuils=((0.4, "immediate"), (1.0, "slow"), (INF, "stalls")),
    note_source="Descriptif : un lockout lent sur une charge maximale n'est pas une faute.",
)


# =============================================================================

E01 = Indicateur(
    id="E01", nom="descent_initiation", phase=Phase.DESCENTE, source=Source.POSE,
    portee=Portee.REP, critere="reset", vue=Vue.PROFIL,
    question="Which joint bends first on the way down?",
    etats=(Etat("hips_first", "The hips travel back first, the knees bending once the bar has "
                           "passed them.", 3),
           Etat("simultaneous", "Hips and knees bend together.", 3),
           Etat("at_the_knees", "The knees bend before the bar has passed them, pushing the bar "
                          "forward or into the kneecaps.", 2, persona="The Kneecapper")),
    mesure="descent_order", seuils=((-5.0, "at_the_knees"), (5.0, "simultaneous"), (INF, "hips_first")),
    note_source="Difference entre la perte d'angle de hanche et celle de genou, 0,35 s "
                "apres le verrouillage. Deja en production.",
)




# =============================================================================
# La liste. Tout le reste du code lit ceci.
# =============================================================================

INDICATEURS: tuple[Indicateur, ...] = (
    C04, C05,
    S04, S02, S01, S05, S10, S06, S08,
    L01, L04,
    P02, P03, P04, P05, P08,
    K07, K03, K04,
    E02, E03,
    # --- mesures par la pose, jamais rebranchees depuis le 2026-09-09 ---------------
    # contexte  : C01 variant, C02 camera_view, C03 pose_quality
    # setup     : S03 shin_angle
    # leg_drive : L02 torso_pitch
    # bar_path  : P01 hand_drift
    # descent   : E01 descent_initiation
    # non notes : P06 sticking_point, P07 pull_duration, K06 lockout_duration
    # --- supprimes le 2026-09-11 soir, avec la reecriture en frontieres --------------
    # arms_long + slack_pull + jerky_start -> S06 arms_tension_at_setup
    # thoracic_under_load, asymmetry, brace : plus de question equivalente
)

# L'action a essayer pour chaque etat fautif, en une consigne.
#
# Un conseil ne dit jamais pourquoi ("tes dorsaux sont faibles") : il dit quoi essayer
# a charge maitrisee. La cause d'un defaut ne se lit pas sur une video, et un essai de
# consigne peut aider sans prouver quoi que ce soit. Les etats sans entree ici ne
# produisent aucun conseil : c'est le cas normal d'un etat correct ou descriptif.
CONSEILS = {
    # --- mecanique 1 : la position de depart ----------------------------------------
    "bar_over_midfoot_topology:bar_over_ankle_or_shin": "Bring the bar forward over the laces: pressed against the shins it has to travel forward to clear the knees.",
    "bar_over_midfoot_topology:bar_over_toes_or_floor": "Set the bar over the middle of your foot, close to the shins.",
    # Deux personnes differentes ont les hanches hautes : celle qui se place comme ca,
    # et celle qui NE PEUT PAS tenir plus bas (chevilles, hanches, quadriceps). Aucune
    # video ne les separe. Le conseil nomme donc l'observation et donne le test, il ne
    # devine pas la cause — et le lifter apprend au passage la difference entre un
    # defaut de geste et une limite de corps.
    "hip_height_via_femur:torso_parallel_to_floor": "Drop the hips until your shoulders sit over the bar. If you cannot hold it there, that is mobility, not technique.",
    "hip_height_via_femur:femur_parallel_or_downward": "Raise the hips until your shoulders sit just ahead of the bar: squatting the setup gives the bar nowhere to go.",
    "shoulders_over_bar_gravity:arm_angled_forward": "Set the shoulders over or just ahead of the bar before you pull.",
    "shoulders_over_bar_gravity:arm_angled_backward": "Bring the hips down slightly so the shoulders sit closer to over the bar.",

    # --- mecanique 2 : le slack ---------------------------------------------------
    "arms_tension_at_setup:elbow_angle_changes": "Straighten the arms and pull the slack out until you feel the bar load, then push the floor away: the elbows are locked before anything moves.",

    # --- mecanique 3 : le leg drive --------------------------------------------------
    # "Ne laisse pas tes hanches monter" est INAPPLICABLE : la montee des hanches est
    # ce qui rend la barre soulevable depuis une mauvaise position. Le conseil porte
    # donc sur ce qu'on peut faire — pousser le sol — et ENCHAINEMENTS rattache ce
    # defaut a la position de depart quand c'est elle qui l'a cause.
    "initiation_sequence:torso_angle_decreases": "Push the floor away with your legs and hold your chest angle until the plates leave the floor.",
    "initiation_sequence:torso_angle_increases": "Keep the chest angle as the plates leave the floor: hips and shoulders rise together, the legs do the first push.",

    # --- mecanique 4 : la barre contre le corps --------------------------------------
    "bar_leg_daylight:daylight_over_shoe": "Keep the bar on the legs the whole way up: let it brush the shins and thighs.",
    "bar_leg_daylight:daylight_beyond_shoe": "Keep the bar in contact with the legs the whole way up.",
    "bar_path_at_knees_topology:bar_deviates_forward": "Let the hips come through as the bar reaches the knees so it passes close.",

    # --- mecanique 5 : la position d'arrivee -----------------------------------------
    "lockout_extension:hip_angle_under_180": "Finish standing tall: drive the hips all the way through and squeeze the glutes.",
    "lockout_extension:knee_angle_under_180": "Lock the knees at the top instead of leaving them soft.",
    "sagittal_torso_angle:torso_obtuse_angle": "Finish tall by squeezing the glutes, not by leaning back.",
    "vertical_velocity_hitch:velocity_hits_zero_or_negative": "Finish with one continuous hip extension instead of ratcheting the bar up the thighs.",
    "shoulder_elevation_delta:distance_decreases": "Finish with the hips: the shrug adds no height to the bar.",

    # --- mecanique 6 : le reset -------------------------------------------------------
    "descent_hand_contact:hands_break_contact": "Stay with the bar on the way down instead of dropping it.",
    "rep_transition_velocity:impact_rebound": "Let the plates settle and rebuild your setup instead of riding the bounce.",

    # --- axe structure ---------------------------------------------------------------
    # Ces conseils ne servent JAMAIS d'epingle : ils accompagnent le bandeau d'urgence.
    "lumbar_at_setup:lumbar_convex": "Set the lower back flat before the bar moves; drop the load if you cannot hold it.",
    "lumbar_geometry_delta:lumbar_becomes_convex": "Stop the set. Rebuild this at a load where the lower back holds its shape.",
    "knee_valgus_tracking:knees_touch_line": "Push the knees out over your toes as you drive: they should never reach the line of the inner foot.",
    "knee_valgus_tracking:knees_cross_inside_line": "Screw your feet into the floor and push the knees out over your toes as you drive.",
}


# La chaine causale : quel etat amont EXPLIQUE quel indicateur aval.
#
# Sans elle, une seule faute de placement produit trois reproches — hanches trop basses,
# hanches qui decollent, barre qui s'eloigne — pour une seule cause. Le lifter essaie de
# corriger trois choses et n'en corrige aucune. Avec elle, le rapport nomme la cause et
# RATTACHE le reste : "et c'est pour ca que ta barre s'eloigne".
#
# C'est une table DECLAREE, et non une regle "tout ce qui est en aval est supprime" :
# toute faute en aval n'est pas une consequence, et une suppression automatique
# effacerait des defauts independants. `_verifie()` la relit a l'import.
#
# Une arete ne joue que si les DEUX bouts sont fautifs sur la meme serie.
ENCHAINEMENTS: dict[str, tuple[str, ...]] = {
    # Des hanches trop basses forcent le corps a les remonter sous charge pour aller
    # chercher l'angle de dos qu'il aurait fallu avoir des le depart.
    "hip_height_via_femur:femur_parallel_or_downward": (
        "initiation_sequence", "shoulders_over_bar_gravity", "bar_path_at_knees_topology"),
    # Des hanches trop hautes, c'est deja un souleve jambes tendues : plus de leg drive
    # disponible (les epaules montent seules), et la lombaire prend ce que les jambes
    # ne donnent pas.
    "hip_height_via_femur:torso_parallel_to_floor": (
        "initiation_sequence", "lumbar_geometry_delta", "lockout_extension"),
    # Une barre contre les tibias doit partir en avant pour passer les genoux.
    "bar_over_midfoot_topology:bar_over_ankle_or_shin": ("bar_path_at_knees_topology",),
    # Une barre devant le pied, c'est de la lumiere entre la barre et les jambes des
    # le premier centimetre.
    "bar_over_midfoot_topology:bar_over_toes_or_floor": ("bar_leg_daylight",),
    "shoulders_over_bar_gravity:arm_angled_forward": (
        "bar_leg_daylight", "bar_path_at_knees_topology"),
    "shoulders_over_bar_gravity:arm_angled_backward": ("lumbar_geometry_delta",),
    # Le decollage des hanches fait plonger la poitrine, et la barre part en avant.
    "initiation_sequence:torso_angle_decreases": (
        "bar_leg_daylight", "bar_path_at_knees_topology", "lumbar_geometry_delta",
        "vertical_velocity_hitch"),
    # Partir sans tension arrache le lifter de sa position avant meme la tiree.
    "arms_tension_at_setup:elbow_angle_changes": (
        "initiation_sequence", "lumbar_geometry_delta"),
    # Une barre loin du corps allonge le bras de levier : le verrouillage se paie.
    "bar_leg_daylight:daylight_beyond_shoe": (
        "vertical_velocity_hitch", "lockout_extension", "sagittal_torso_angle"),
    "bar_path_at_knees_topology:bar_deviates_forward": ("vertical_velocity_hitch",),
}

PAR_NOM = {i.nom: i for i in INDICATEURS}
PAR_ID = {i.id: i for i in INDICATEURS}


def pour(variante: str, source=None, portee=None) -> list[Indicateur]:
    """Les indicateurs applicables, filtres. L'ordre du catalogue est conserve."""
    out = [i for i in INDICATEURS if variante in i.variantes]
    if source is not None:
        sources = source if isinstance(source, (tuple, list, set)) else (source,)
        out = [i for i in out if i.source in sources]
    if portee is not None:
        out = [i for i in out if i.portee is portee]
    return out


def juges_par_le_modele(variante: str, portee=None) -> list[Indicateur]:
    """Ceux qui partent dans le schema : les LLM, plus les A_TESTER en attendant."""
    return pour(variante, source=(Source.LLM, Source.A_TESTER), portee=portee)


def note_de(nom: str, cle) -> int | None:
    """La note d'un etat observe. None si non evaluable ou si l'etat est inconnu.

    C'est ici, et nulle part ailleurs, que se decide combien vaut un defaut.
    """
    ind = PAR_NOM.get(nom)
    if ind is None:
        return None
    etat = ind.etat(cle)
    return etat.note if etat is not None else None


def _verifie() -> None:
    """Coherence du catalogue, verifiee a l'import : c'est la qu'elle se voit."""
    vus = set()
    for i in INDICATEURS:
        if i.id in vus or i.nom in vus:
            raise RuntimeError(f"identifiant en double dans le catalogue : {i.id} / {i.nom}")
        vus |= {i.id, i.nom}
        if i.critere is not None and i.critere not in CRITERES:
            raise RuntimeError(f"{i.id} pointe vers un critere inconnu : {i.critere}")
        if i.source is Source.POSE:
            if not i.mesure:
                raise RuntimeError(f"{i.id} est POSE mais ne dit pas quelle mesure le porte")
            cles = {c for _, c in i.seuils}
            declares = {e.cle for e in i.etats}
            if not cles <= declares:
                raise RuntimeError(f"{i.id} : seuils vers des etats non declares "
                                   f"{cles - declares}")
        elif i.seuils:
            raise RuntimeError(f"{i.id} n'est pas POSE mais porte des seuils")
        if len(i.etats) < 2:
            raise RuntimeError(f"{i.id} n'a pas d'alternative : un seul etat declare")
        if i.source is Source.POSE and i.seuils and i.plausible is None:
            raise RuntimeError(f"{i.id} mesure {i.mesure} sans bornes de plausibilite")
    for cle in CONSEILS:
        nom, _, etat = cle.partition(":")
        ind = PAR_NOM.get(nom)
        if ind is None or ind.etat(etat) is None:
            raise RuntimeError(f"conseil oriente vers un etat inexistant : {cle}")
    # Chaque critere doit avoir de quoi se noter, sinon il s'affiche "not visible" sur
    # toutes les reps : c'est ce qui avait fait retirer `leg_drive` le 2026-09-09.
    portes = {i.critere for i in INDICATEURS if i.critere}
    if orphelins := set(CRITERES) - portes:
        raise RuntimeError(f"criteres sans aucun indicateur pour les noter : {orphelins}")
    for cle, avals in ENCHAINEMENTS.items():
        nom, _, etat = cle.partition(":")
        ind = PAR_NOM.get(nom)
        if ind is None or ind.etat(etat) is None:
            raise RuntimeError(f"enchainement depuis un etat inexistant : {cle}")
        if (note := ind.etat(etat).note) is None or note >= NOTE_MAX_ETAT:
            raise RuntimeError(f"enchainement depuis un etat non fautif : {cle}")
        for aval in avals:
            cible = PAR_NOM.get(aval)
            if cible is None:
                raise RuntimeError(f"enchainement {cle} vers un indicateur inconnu : {aval}")
            # Une consequence doit etre EN AVAL dans l'ordre causal, sinon la table
            # inverse cause et effet et l'epingle designe le mauvais defaut.
            if cible.critere is None or ind.critere is None:
                raise RuntimeError(f"enchainement {cle} -> {aval} : critere manquant")
            if cible.critere != STRUCTURE and rang_causal(cible.critere) < rang_causal(ind.critere):
                raise RuntimeError(f"enchainement {cle} -> {aval} remonte la chaine causale")


_verifie()
