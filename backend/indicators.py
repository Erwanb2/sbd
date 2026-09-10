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

    @property
    def plausible(self) -> tuple[float, float] | None:
        """Les bornes physiques de la mesure, hors desquelles on n'y croit pas."""
        return PLAUSIBLE.get(self.mesure) if self.mesure else None

    @property
    def tous_les_etats(self) -> tuple[Etat, ...]:
        """Les etats declares, plus `not_visible` pour ceux que le modele juge."""
        if self.source is Source.POSE:
            return self.etats
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
# SETUP — avant que la barre quitte le sol
# =============================================================================

S01 = Indicateur(
    id="S01", nom="hip_height", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="start_position", vue=Vue.PROFIL,
    question="How high are the hips at the start, between the knees and the shoulders?",
    etats=(Etat("too_high", "The hips start very high: the pull begins as a stiff-legged "
                               "lift with the shoulders far in front.", 2),
           Etat("between_knees_and_shoulders", "The hips sit between the knees and the shoulders.", 3),
           Etat("too_low", "The lifter squats the setup: pelvis very low, shins pushed "
                               "forward, knees over the bar.", 2, persona="The Squatter")),
    note_source="Etait POSE (hip_ratio) jusqu'au 2026-09-09, retire avec les 16 autres. "
                "Revient en LLM le 2026-09-09 : c'est la premiere mecanique enseignable "
                "du geste, et une hauteur de hanche est justement le genre de chose "
                "grossiere qu'un modele lit bien sur une image de profil. La mesure "
                "n'est PAS restauree — on repose la question, on ne rebranche pas le "
                "ratio. A confronter aux annotations humaines avant de faire confiance.",
)

S02 = Indicateur(
    id="S02", nom="shoulders_over_bar", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="start_position", vue=Vue.PROFIL,
    question="Where are the shoulders relative to the bar at the start?",
    etats=(Etat("behind_bar", "The shoulders start behind the bar, which sends the bar forward "
                            "as soon as it leaves the floor.", 2),
           Etat("over_bar", "The shoulders are stacked over or just ahead of the bar.", 3),
           Etat("far_ahead", "The shoulders are far ahead of the bar, lengthening the "
                              "lever on the lower back.", 2)),
    note_source="Etait POSE (shoulder_bar_offset) jusqu'au 2026-09-09. Revient en LLM : "
                "la position des epaules PAR RAPPORT A LA BARRE demande de voir la barre, "
                "ce que la pose ne fait pas — elle lisait le poignet. Meme reserve que "
                "S01 : a mesurer contre les annotations avant d'y croire.",
)

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

S04 = Indicateur(
    id="S04", nom="bar_over_midfoot", phase=Phase.SETUP, source=Source.A_TESTER, portee=Portee.REP,
    critere="start_position", vue=Vue.PROFIL,
    question="Where is the bar over the foot at the start?",
    etats=(Etat("over_midfoot", "The bar sits over the middle of the foot, close to the shins.", 3),
           Etat("ahead_of_midfoot", "The bar starts away from the shins, ahead of the mid-foot.", 2),
           Etat("against_the_shins", "The bar starts jammed against the shins, behind the mid-foot.", 3)),
    note_source="A TESTER : au setup la main tient la barre, donc x_poignet est un proxy "
                "bien meilleur que pendant la tiree. Mais le poignet n'est pas le centre de "
                "la barre, et le milieu du pied demande cheville ET orteil visibles. "
                "A mesurer contre une annotation image avant de basculer en POSE.",
)

S05 = Indicateur(
    id="S05", nom="back_at_setup", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="structure",
    question="What shape is the back in before the bar moves?",
    etats=(Etat("flat", "The back is flat and set before the bar moves.", 3),
           Etat("upper_back_rounded", "The upper back is rounded but the position looks deliberate "
                                "and set.", 3),
           Etat("lower_back_rounded", "The lower back is already rounded at the start.", 2,
                persona="The Fishing Rod")),
    note_source="LIMITE DURE : aucun repere entre epaules et hanches. Le tronc est un "
                "segment droit pour MediaPipe. Ne jamais fabriquer un proxy ici.",
)

S06 = Indicateur(
    id="S06", nom="arms_long", phase=Phase.SETUP, source=Source.A_TESTER, portee=Portee.REP,
    critere="start_position",
    question="Do the arms stay straight from the start to lockout, or do the elbows bend "
             "at any point?",
    etats=(Etat("straight", "The arms hang straight and stay long, elbows locked out, from "
                            "the setup to the top.", 3),
           Etat("bent", "The elbows are visibly flexed at some point, loading the biceps "
                        "tendon.", 1, persona="The T-Rex")),
    note_source="2026-09-09 : fusion de l'ancien S06 (arms_straight, au setup) et de P10 "
                "(elbow_flexion, pendant la tiree). C'etait la MEME faute physique posee "
                "deux fois, ce que l'en-tete de CRITERES interdit — et avec la regle du "
                "minimum ca ne changeait pas la note quand la faute etait la, ca doublait "
                "seulement la chance qu'un faux positif du modele plombe le critere. "
                "A TESTER cote pose, meme raison qu'avant : l'angle epaule-coude-poignet "
                "est calculable mais une flexion de 10-15 deg est dans le bruit de la "
                "projection, et le bras oppose est souvent occulte.",
)

S07 = Indicateur(
    id="S07", nom="slack_pull", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="slack_and_brace",
    question="Does the lifter take the slack out before the bar leaves the floor?",
    etats=(Etat("progressive", "The arms pull taut and the bar or plates visibly load "
                               "before anything moves.", 3),
           Etat("partial", "Some tension is taken but it is lost as the bar breaks the floor.", 2),
           Etat("yanked", "No pre-tension at all: the lifter yanks the bar off the floor "
                          "from a loose position.", 1, persona="The Grip & Rip")),
    note_source="Se lit sur la barre et les disques, que la pose ne voit pas. "
                "Attention : une barre qui ne flechit pas visiblement ne prouve pas "
                "l'absence de tension.",
)

S09 = Indicateur(
    id="S09", nom="brace", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="slack_and_brace",
    question="Does the lifter brace before pulling? Look for the breath taken and held at "
             "the bottom, the belly and ribcage expanding and staying expanded, and a "
             "still moment before the bar moves.",
    etats=(Etat("braced", "A breath is taken at the bottom and held: the midsection stays "
                          "expanded and rigid through the pull.", 3),
           Etat("partial", "Some air is taken but the midsection gives during the pull, or "
                           "the breath is let go before lockout.", 2),
           Etat("none", "No visible brace: the lifter reaches down and pulls on a soft "
                        "midsection.", 1, persona="The Deflator")),
    note_source="NOUVEAU le 2026-09-09, et le PLUS INCERTAIN du catalogue : le gainage est "
                "a peine visible sur une video — on voit la respiration, l'expansion du "
                "ventre, la pause avant la tiree, jamais la pression intra-abdominale. Il "
                "ne reste que s'il bat le hasard contre les annotations humaines ; sinon "
                "on le retire et le critere redevient 'slack' seul. Ne jamais basculer en "
                "POSE : MediaPipe n'a aucun repere de tronc.",
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


# =============================================================================
# DECOLLAGE — le premier tiers de la tiree
# =============================================================================

L01 = Indicateur(
    id="L01", nom="hip_vs_shoulder_rise", phase=Phase.DECOLLAGE, source=Source.LLM,
    portee=Portee.REP, critere="leg_drive", vue=Vue.PROFIL,
    question="Over the first third of the pull, do the hips and the shoulders rise "
             "together, or do the hips rise faster and leave the shoulders behind?",
    etats=(Etat("together", "Hips and shoulders rise together: the legs are driving the "
                            "floor away and the torso angle holds.", 3),
           Etat("hips_slightly_ahead", "The hips rise somewhat ahead of the shoulders, but the "
                                  "torso does not pitch forward.", 3),
           Etat("hips_shoot_up", "The hips shoot up while the shoulders barely move: the "
                                  "lift turns into a stiff-legged pull finished by the back.",
                1, persona="The Crane")),
    note_source="Etait POSE (rise_ratio) jusqu'au 2026-09-09, ou il sortait sa sentinelle "
                "9,99 sur une repetition dont la fenetre de phase etait POSTERIEURE au "
                "verrouillage. Revient en LLM le 2026-09-09, et c'est l'indicateur qui "
                "compte le plus du catalogue : c'est LE defaut n.1 du souleve de terre. "
                "\n"
                "Attention a ce qu'on en fait : 'les hanches decollent' n'est JAMAIS la "
                "faute a rapporter telle quelle. C'est la CORRECTION d'un mauvais depart, "
                "en cours de mouvement — le corps va chercher sous charge l'angle de dos "
                "qu'il aurait du avoir des le debut. Dire 'ne laisse pas tes hanches "
                "monter' est inapplicable. Le conseil est au depart, d'ou l'entree "
                "ENCHAINEMENTS depuis hip_height.",
)

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

L03 = Indicateur(
    id="L03", nom="jerky_start", phase=Phase.DECOLLAGE, source=Source.A_TESTER,
    portee=Portee.REP, critere="slack_and_brace",
    question="Is the start smooth, or is the bar jerked off the floor?",
    etats=(Etat("smooth", "The bar accelerates smoothly out of the floor.", 3),
           Etat("jerked", "The bar is jerked and the lifter is pulled out of position.", 1,
                persona="The Grip & Rip")),
    note_source="A TESTER : une discontinuite de vitesse verticale est calculable, mais "
                "a 6 im/s le pic d'acceleration tombe souvent entre deux images. "
                "A mesurer sur une passe dense avant de basculer.",
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


# =============================================================================
# TIREE — du sol au verrouillage
# =============================================================================

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

P02 = Indicateur(
    id="P02", nom="past_the_knees", phase=Phase.TIREE, source=Source.A_TESTER,
    portee=Portee.REP, critere="bar_path",
    question="How does the bar get past the knees?",
    etats=(Etat("clean", "The bar passes the knees close to the legs, in one line.", 3),
           Etat("loops", "The bar loops forward around the knees before coming back in.", 2),
           Etat("catches", "The bar catches on the knees and the lifter has to work "
                             "around them.", 1)),
    note_source="A TESTER : la relation temporelle poignet/genou est calculable de profil, "
                "mais la boucle se joue sur quelques centimetres de barre, pas de main. "
                "A confronter a une annotation image avant de basculer.",
)

P03 = Indicateur(
    id="P03", nom="bar_leg_contact", phase=Phase.TIREE, source=Source.LLM,
    portee=Portee.REP, critere="bar_path",
    question="Does the bar stay in contact with, or very close to, the legs?",
    etats=(Etat("in_contact", "The bar stays against or within a few centimetres of the legs "
                           "the whole way up.", 3),
           Etat("brief_loss", "Contact is briefly lost, then the bar comes back to the legs.", 3),
           Etat("away_from_legs", "The bar travels visibly away from the legs.", 1,
                persona="The Pendulum")),
    note_source="Le contact barre-jambe n'est pas observable par la pose : il faut voir la "
                "barre. Ne pas exiger de racler les tibias, ce n'est pas un objectif.",
)

P04 = Indicateur(
    id="P04", nom="back_under_load", phase=Phase.TIREE, source=Source.LLM,
    portee=Portee.REP, critere="structure",
    question="Does the back keep the SAME shape from the floor to lockout, or does flexion "
             "get added under load?",
    etats=(Etat("unchanged", "The back holds the same shape at the floor, at knee height and "
                            "at lockout: no flexion added under load.", 3),
           Etat("stable_rounding", "There is rounding, but it is set from the start and does "
                                  "not get worse during the pull.", 3),
           Etat("flexion_appears", "Flexion appears during the pull that was not there at "
                                    "the start.", 2),
           Etat("collapses", "The lower back rounds hard and keeps rounding as the bar "
                                "rises.", 1, persona="The Fishing Rod")),
    note_source="LIMITE DURE, comme S05 : pas de repere rachidien. C'est le critere ou une "
                "mauvaise note est une blessure et non un kilo perdu, et c'est precisement "
                "celui que la pose ne verra jamais. Il reste au modele, definitivement.",
)

P05 = Indicateur(
    id="P05", nom="knee_valgus", phase=Phase.TIREE, source=Source.LLM,
    portee=Portee.REP, critere="structure", vue=Vue.FACE,
    question="Do the knees stay out over the feet, or do they collapse inward? This is only "
             "answerable from the front or three-quarter view: from the side a knee coming "
             "in is indistinguishable from a knee coming forward, so answer 'not_visible'.",
    etats=(Etat("tracks_out", "The knees track outward over the feet throughout.", 3),
           Etat("slight", "The knees waver inward at the hardest point but never collapse.", 3),
           Etat("collapses_in", "The knees collapse inward off the floor.", 1, persona="The X-Wing")),
    note_source="Etait POSE (valgus_ratio) jusqu'au 2026-09-09. Revient en LLM, et il "
                "rejoint l'axe STRUCTURE et non une mecanique : un genou qui rentre n'est "
                "pas une etape qu'on execute mal, c'est une articulation qui ne tient pas "
                "sa position sous charge — meme famille que le dos qui s'enroule. "
                "Comme les hanches hautes, il a deux causes qu'aucune video ne separe : "
                "manque de rotation externe au placement (un repere suffit) ou vraie "
                "faiblesse (rien a faire ici). Le conseil nomme donc l'observation et "
                "donne le test, il ne devine pas la cause.",
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

P08 = Indicateur(
    id="P08", nom="hitch", phase=Phase.TIREE, source=Source.A_TESTER,
    portee=Portee.REP, critere="finish_position",
    question="Does the lifter ratchet the bar up the thighs?",
    etats=(Etat("no", "The bar rises in one continuous motion.", 3),
           Etat("yes", "The lifter re-flexes the knees and rests the bar on the thighs to "
                       "ratchet it up.", 1, persona="The Hitcher")),
    note_source="A TESTER : une re-flexion du genou apres le passage des genoux est une "
                "non-monotonie de l'extension, calculable sur le signal existant. C'est "
                "la piste POSE la plus prometteuse du catalogue. Mais un ralentissement "
                "n'est pas un hitch et le contact cuisse-barre n'est pas un appui : "
                "annoter d'abord.",
)

P09 = Indicateur(
    id="P09", nom="asymmetry", phase=Phase.TIREE, source=Source.A_TESTER,
    portee=Portee.REP, critere="structure", vue=Vue.FACE,
    question="Does one side of the bar rise ahead of the other?",
    etats=(Etat("even", "Both sides rise together.", 3),
           Etat("uneven", "One side finishes ahead of the other and the bar rotates.", 2,
                persona="The Helicopter")),
    note_source="A TESTER : la difference de hauteur des deux poignets est calculable de "
                "face. Mais perspective, prise mixte et flexion de barre imitent une "
                "asymetrie. Confirmer sur une seconde vue avant de conclure.",
)

# P10 elbow_flexion : SUPPRIME le 2026-09-09, fusionne dans S06 `arms_long`. "Bras
# tendus au setup" et "coudes qui plient a la tiree" sont la meme faute physique a deux
# instants ; S06 porte desormais la question sur toute la repetition.


# =============================================================================
# LOCKOUT
# =============================================================================

# K01 hip_extension + K02 knee_extension : fusionnes le 2026-09-09 dans K07
# `lockout_completion`. Les deux posaient la meme question — "est-ce que le lift est
# fini ?" — et la regle du minimum les rendait indissociables a l'affichage.

K07 = Indicateur(
    id="K07", nom="lockout_completion", phase=Phase.LOCKOUT, source=Source.LLM,
    portee=Portee.REP, critere="finish_position", vue=Vue.PROFIL,
    question="Is the lift actually finished at the top: hips and knees both locked, the "
             "lifter standing tall?",
    etats=(Etat("locked", "Hips and knees both reach full extension: the lifter stands tall "
                          "and the rep is finished.", 3),
           Etat("soft_knees", "The knees stay visibly soft at the top.", 1,
                persona="The Soft-Lock"),
           Etat("hips_short", "The hips stay visibly bent at the top: the lifter never comes "
                              "all the way through.", 1, persona="The Soft-Lock")),
    note_source="2026-09-09 : fusion de K01 (hip_lockout_deg) et K02 (knee_lockout_deg), "
                "tous deux POSE et retires le meme jour. C'est la mecanique 'position "
                "d'arrivee', qui n'existait pas : l'ancien critere `lockout` ne contenait "
                "que du hitch, du shrug, de l'asymetrie et de la bascule — des controles "
                "de LEGALITE en competition, pas la mecanique de finir debout.",
)

K03 = Indicateur(
    id="K03", nom="lean_back", phase=Phase.LOCKOUT, source=Source.LLM,
    portee=Portee.REP, critere="finish_position", vue=Vue.PROFIL,
    question="Does the lifter lean back at the top?",
    etats=(Etat("upright", "The lifter finishes upright and neutral.", 3),
           Etat("slight", "A slight lean back at the top.", 3),
           Etat("hyperextension", "Marked lumbar hyperextension at the top instead of "
                                  "finishing with the glutes.", 1, persona="The Over-Extender")),
    note_source="Etait POSE (lean_back_deg) jusqu'au 2026-09-09. Revient en LLM. Il absorbe "
                "K05 `lockout_balance`, supprime le meme jour : 'le poids part derriere les "
                "talons' et 'hyperextension lombaire en haut' decrivaient le meme instant.",
)

K04 = Indicateur(
    id="K04", nom="shrug", phase=Phase.LOCKOUT, source=Source.A_TESTER,
    portee=Portee.REP, critere="finish_position",
    question="Does the lifter shrug the shoulders to finish?",
    etats=(Etat("no", "The lift finishes with hip extension alone.", 3),
           Etat("yes", "The lifter shrugs the shoulders at the top: the shrug adds no "
                       "height to the bar and abandons the lat position.", 2,
                persona="The Shrugger")),
    note_source="A TESTER : l'elevation de l'epaule par rapport a l'oreille est calculable, "
                "mais elle se confond avec un simple redressement du cou. A annoter.",
)

# K05 lockout_balance : SUPPRIME le 2026-09-09, redondant avec K03 `lean_back`. Se
# coucher en arriere en haut et laisser le poids partir derriere les talons sont le meme
# instant vu deux fois ; K03 le porte, et le persona "The Heel Tipper" disparait avec.

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
# DESCENTE
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

E02 = Indicateur(
    id="E02", nom="descent_control", phase=Phase.DESCENTE, source=Source.LLM,
    portee=Portee.REP, critere="reset",
    question="How does the bar get back to the floor? If each rep is reset on the floor, "
             "only a dropped or uncontrolled bar is a fault: a deliberately fast but "
             "accompanied lowering is not.",
    etats=(Etat("controlled", "The bar is lowered under control, the lifter staying with it.", 3),
           Etat("fast_but_controlled", "The descent is quick but the hands stay with the bar "
                                      "all the way down.", 3),
           Etat("dropped", "The bar is dropped or crashes to the floor.", 1),
           Etat("cut_off", "The lowering is cut off by the end of the video.", None)),
    note_source="Il faut voir la barre et le sol : la pose ne voit ni l'un ni l'autre. "
                "L'etat 'cut_off' est distinct de 'not_visible' : la video s'arrete, "
                "ce n'est pas un probleme de cadrage.",
)

E03 = Indicateur(
    id="E03", nom="rep_transition", phase=Phase.DESCENTE, source=Source.LLM,
    portee=Portee.REP, critere="reset",
    question="How does this rep connect to the next one?",
    etats=(Etat("reset", "The bar comes to a full stop on the floor and the lifter rebuilds "
                         "the setup before the next rep.", 3),
           Etat("touch_and_go", "The bar touches and is immediately pulled again, but the "
                                "position is still under control.", 3),
           Etat("bounce", "The plates bounce off the floor and the bounce is used to start "
                          "the next rep.", 2, persona="The Trampolinist"),
           Etat("last_rep", "This is the last rep of the set.", None)),
    note_source="2026-09-09 : passe de descriptif a NOTE, et devient la mecanique 'reset'. "
                "C'est la version enseignable de la question 'est-ce que ta serie a tenu' : "
                "reconstruire le placement a chaque rep, ou enchainer sur un placement qui "
                "se degrade. "
                "Le touch-and-go reste a 3 : c'est un style, pas une faute. Seul le rebond "
                "descend a 2, parce qu'il remplace la reconstruction par de l'elastique. "
                "'last_rep' n'est pas notable — sur une serie d'une seule rep le critere "
                "sort entier du denominateur, ce qui est le comportement voulu.",
)


# =============================================================================
# La liste. Tout le reste du code lit ceci.
# =============================================================================

# AUCUN indicateur `Source.POSE` n'est note. Les 17 ont ete retires le 2026-09-09,
# apres l'instruction de conventionnal_deadlift_12 : un lift propre que le systeme
# notait 19/20 avec deux conseils correctifs, les deux issus de mesures fausses
# (P01 hand_drift lisait un poignet a 0,05 de visibilite ; L01 sortait sa sentinelle
# 9,99 sur une fenetre posterieure au verrouillage). La pose reste indispensable
# ailleurs — cascade sumo/conventionnel 39/39, detection des repetitions 142/146 —
# c'est la NOTATION par la pose qui s'est arretee.
#
# 2026-09-09, meme jour, refonte des criteres : quatre de ces questions REVIENNENT,
# posees au modele et non mesurees. S01 hip_height, S02 shoulders_over_bar,
# L01 hip_vs_shoulder_rise, P05 knee_valgus, plus K01+K02 fusionnes en K07 et K03
# lean_back. Ce n'est pas un retour en arriere : on ne rebranche aucun ratio, on pose
# la question a la seule source qui voit la barre et le rachis. Rien ne prouve encore
# que le modele y repond bien — c'est le risque principal de la refonte, et il se
# mesure contre les annotations humaines avant qu'on fasse confiance a ces six-la.
INDICATEURS: tuple[Indicateur, ...] = (
    C04, C05,
    S01, S02, S04, S05, S06, S07, S08, S09,
    L01, L03, L04,
    P02, P03, P04, P05, P08, P09,
    K03, K04, K07,
    E02, E03,
    # --- toujours retires, mesures par la pose et jamais rebranches ------------------
    # contexte  : C01 variant, C02 camera_view, C03 pose_quality
    # setup     : S03 shin_angle
    # leg_drive : L02 torso_pitch
    # bar_path  : P01 hand_drift
    # descent   : E01 descent_initiation
    # non notes : P06 sticking_point, P07 pull_duration, K06 lockout_duration
    # --- fusionnes ou supprimes le 2026-09-09 ---------------------------------------
    # P10 elbow_flexion  -> S06 arms_long
    # K01 + K02          -> K07 lockout_completion
    # K05 lockout_balance-> K03 lean_back
)

# L'action a essayer pour chaque etat fautif, en une consigne.
#
# Un conseil ne dit jamais pourquoi ("tes dorsaux sont faibles") : il dit quoi essayer
# a charge maitrisee. La cause d'un defaut ne se lit pas sur une video, et un essai de
# consigne peut aider sans prouver quoi que ce soit. Les etats sans entree ici ne
# produisent aucun conseil : c'est le cas normal d'un etat correct ou descriptif.
CONSEILS = {
    # --- mecanique 1-2 : le placement et la position de depart ----------------------
    "bar_over_midfoot:ahead_of_midfoot": "Set the bar over the middle of your foot, close to the shins.",
    # Deux personnes differentes ont les hanches hautes : celle qui se place comme ca,
    # et celle qui NE PEUT PAS tenir plus bas (chevilles, hanches, quadriceps). Aucune
    # video ne les separe. Le conseil nomme donc l'observation et donne le test, il ne
    # devine pas la cause — et le lifter apprend au passage la difference entre un
    # defaut de geste et une limite de corps.
    "hip_height:too_high": "Drop the hips until your shoulders sit over the bar. If you cannot hold it there, that is mobility, not technique.",
    "hip_height:too_low": "Raise the hips until your shoulders sit just ahead of the bar: squatting the setup gives the bar nowhere to go.",
    "shoulders_over_bar:behind_bar": "Set the shoulders over or just ahead of the bar before you pull.",
    "shoulders_over_bar:far_ahead": "Bring the hips down slightly so the shoulders sit closer to over the bar.",
    "arms_long:bent": "Keep the arms long from the floor to the top and let the legs do the work.",

    # --- mecanique 3 : le slack et le gainage ---------------------------------------
    "slack_pull:partial": "Pull the slack out until you feel the bar load, then push the floor away.",
    "slack_pull:yanked": "Take the slack out of the bar before you pull instead of yanking it.",
    "jerky_start:jerked": "Build tension against the bar, then accelerate: do not snatch it off the floor.",
    "brace:partial": "Take the same breath every rep and hold it all the way to lockout.",
    "brace:none": "Take a big breath at the bottom, push it into your belly, and hold it until the bar is down.",

    # --- mecanique 4 : le leg drive --------------------------------------------------
    # "Ne laisse pas tes hanches monter" est INAPPLICABLE : la montee des hanches est
    # ce qui rend la barre soulevable depuis une mauvaise position. Le conseil porte
    # donc sur ce qu'on peut faire — pousser le sol — et ENCHAINEMENTS rattache ce
    # defaut a la position de depart quand c'est elle qui l'a cause.
    "hip_vs_shoulder_rise:hips_shoot_up": "Push the floor away with your legs and hold your chest angle through the first third of the pull.",

    # --- mecanique 5 : la barre contre le corps --------------------------------------
    "bar_leg_contact:away_from_legs": "Keep the bar in contact with the legs the whole way up.",
    "past_the_knees:loops": "Let the hips come through as the bar reaches the knees so it passes close.",
    "past_the_knees:catches": "Sit the hips back a touch at the knees so the bar has a path.",

    # --- mecanique 6 : la position d'arrivee -----------------------------------------
    "lockout_completion:hips_short": "Finish standing tall: drive the hips all the way through and squeeze the glutes.",
    "lockout_completion:soft_knees": "Lock the knees at the top instead of leaving them soft.",
    "lean_back:hyperextension": "Finish tall by squeezing the glutes, not by leaning back.",
    "hitch:yes": "Finish with one continuous hip extension instead of ratcheting the bar up the thighs.",
    "shrug:yes": "Finish with the hips: the shrug adds no height to the bar.",

    # --- mecanique 7 : le reset -------------------------------------------------------
    "descent_control:dropped": "Stay with the bar on the way down instead of dropping it.",
    "rep_transition:bounce": "Let the plates settle and rebuild your setup instead of riding the bounce.",

    # --- axe structure ---------------------------------------------------------------
    # Ces conseils ne servent JAMAIS d'epingle : ils accompagnent le bandeau d'urgence.
    "back_at_setup:lower_back_rounded": "Set the back flat before the bar moves; drop the load if you cannot hold it.",
    "back_under_load:flexion_appears": "Brace before you pull, and end the set when the shape starts to change.",
    "back_under_load:collapses": "Stop the set. Rebuild this at a load where the back holds its shape.",
    "knee_valgus:collapses_in": "Screw your feet into the floor and push the knees out over your toes as you drive.",
    "asymmetry:uneven": "Film a front view and check whether one side is leading before changing anything.",
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
    "hip_height:too_low": ("hip_vs_shoulder_rise", "shoulders_over_bar", "past_the_knees"),
    # Des hanches trop hautes, c'est deja un souleve jambes tendues : plus de leg drive
    # disponible, et la lombaire prend ce que les jambes ne donnent pas.
    "hip_height:too_high": ("hip_vs_shoulder_rise", "back_under_load", "lockout_completion"),
    "shoulders_over_bar:behind_bar": ("bar_leg_contact", "past_the_knees"),
    "shoulders_over_bar:far_ahead": ("back_under_load",),
    # Le decollage des hanches fait plonger la poitrine, et la barre part en avant.
    "hip_vs_shoulder_rise:hips_shoot_up": ("bar_leg_contact", "past_the_knees",
                                           "back_under_load", "hitch"),
    # Partir sans tension arrache le lifter de sa position avant meme la tiree. La
    # tension seulement PARTIELLE compte autant : elle est prise puis perdue quand la
    # barre casse le sol, et c'est exactement le moment ou les hanches gagnent.
    "slack_pull:yanked": ("hip_vs_shoulder_rise", "back_under_load"),
    "slack_pull:partial": ("hip_vs_shoulder_rise",),
    "jerky_start:jerked": ("hip_vs_shoulder_rise", "back_under_load"),
    "brace:none": ("back_under_load",),
    "brace:partial": ("back_under_load",),
    # Une barre loin du corps allonge le bras de levier : le verrouillage se paie.
    "bar_leg_contact:away_from_legs": ("hitch", "lockout_completion", "lean_back"),
    "past_the_knees:loops": ("hitch",),
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
