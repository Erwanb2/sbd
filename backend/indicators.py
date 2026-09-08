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


# Les criteres affiches a l'utilisateur. Six, et non un par indicateur : plusieurs
# indicateurs decrivent le meme evenement physique et ne doivent peser qu'une fois.
# Le poids dit ce que le critere vaut dans la note sur 20 : le dos sous charge est le
# seul ou une mauvaise note est une blessure et non un kilo perdu.
CRITERES = {
    "setup":     ("Setup and tension", 1.0),
    "leg_drive": ("Leg drive off the floor", 1.0),
    "spine":     ("Spine under load", 2.0),
    "bar_path":  ("Bar path and proximity", 1.0),
    "lockout":   ("Lockout", 1.5),
    "descent":   ("Descent", 1.0),
}

LIBELLE = {c: t for c, (t, _) in CRITERES.items()}
POIDS = {c: p for c, (_, p) in CRITERES.items()}


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
    id="S01", nom="hip_height", phase=Phase.SETUP, source=Source.POSE, portee=Portee.REP,
    critere="setup", vue=Vue.PROFIL,
    question="How high are the hips at the start, between the knees and the shoulders?",
    etats=(Etat("too_high", "The hips start very high: the pull begins as a stiff-legged "
                               "lift with the shoulders far in front.", 2),
           Etat("between_knees_and_shoulders", "The hips sit between the knees and the shoulders.", 3),
           Etat("too_low", "The lifter squats the setup: pelvis very low, shins pushed "
                               "forward, knees over the bar.", 2, persona="The Squatter")),
    mesure="hip_ratio", seuils=((0.40, "too_high"), (0.80, "between_knees_and_shoulders"), (INF, "too_low")),
    note_source="(y_hanche - y_epaule) / (y_genou - y_epaule) a l'instant du decollage. "
                "Sans dimension, donc insensible au zoom. Deja en production.",
)

S02 = Indicateur(
    id="S02", nom="shoulders_over_bar", phase=Phase.SETUP, source=Source.POSE, portee=Portee.REP,
    critere="setup", vue=Vue.PROFIL,
    question="Where are the shoulders relative to the bar at the start?",
    etats=(Etat("behind_bar", "The shoulders start behind the bar, which sends the bar forward "
                            "as soon as it leaves the floor.", 2),
           Etat("over_bar", "The shoulders are stacked over or just ahead of the bar.", 3),
           Etat("far_ahead", "The shoulders are far ahead of the bar, lengthening the "
                              "lever on the lower back.", 2)),
    mesure="shoulder_bar_offset", seuils=((-0.08, "behind_bar"), (0.30, "over_bar"), (INF, "far_ahead")),
    note_source="(x_epaule - x_poignet) rapporte a la longueur du femur, oriente par le "
                "sens du regard. En fraction de femur et non en cm : le fichier convertissait "
                "les pixels avec un femur suppose de 40 cm, ce qui habillait un ratio en unite.",
)

S03 = Indicateur(
    id="S03", nom="shin_angle", phase=Phase.SETUP, source=Source.POSE, portee=Portee.REP,
    critere="setup", vue=Vue.PROFIL, variantes=("sumo",),
    question="How vertical are the shins at the start? (sumo)",
    etats=(Etat("vertical", "The shins are vertical or nearly so: the wedge is in place.", 3),
           Etat("angled", "The shins lean forward, pushing the knees over the bar.", 2)),
    mesure="shin_deg", seuils=((20.0, "vertical"), (INF, "angled")),
    note_source="Angle du segment cheville-genou par rapport a la verticale de l'image. "
                "Sumo seulement : en conventionnel un tibia incline est normal.",
)

S04 = Indicateur(
    id="S04", nom="bar_over_midfoot", phase=Phase.SETUP, source=Source.A_TESTER, portee=Portee.REP,
    critere="setup", vue=Vue.PROFIL,
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
    critere="spine",
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
    id="S06", nom="arms_straight", phase=Phase.SETUP, source=Source.A_TESTER, portee=Portee.REP,
    critere="setup",
    question="Are the arms straight at the start, or are the elbows actively bent?",
    etats=(Etat("straight", "The arms hang straight, elbows locked out.", 3),
           Etat("bent", "The elbows are visibly flexed, loading the biceps tendon.", 1,
                persona="The T-Rex")),
    note_source="A TESTER : l'angle epaule-coude-poignet est calculable. Mais une flexion "
                "de 10-15 deg est dans le bruit de la projection, et le bras oppose est "
                "souvent occulte. A mesurer avant de basculer en POSE.",
)

S07 = Indicateur(
    id="S07", nom="slack_pull", phase=Phase.SETUP, source=Source.LLM, portee=Portee.REP,
    critere="setup",
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
    id="L01", nom="hip_vs_shoulder_rise", phase=Phase.DECOLLAGE, source=Source.POSE,
    portee=Portee.REP, critere="leg_drive", vue=Vue.PROFIL,
    question="Do the hips and the shoulders rise together over the first third of the pull?",
    etats=(Etat("together", "Hips and shoulders rise together: the legs are driving the "
                            "floor away and the torso angle holds.", 3),
           Etat("hips_slightly_ahead", "The hips rise somewhat ahead of the shoulders, but the "
                                  "torso does not pitch forward.", 3),
           Etat("hips_shoot_up", "The hips shoot up while the shoulders barely move: the "
                                  "lift turns into a stiff-legged pull finished by the back.",
                1, persona="The Crane")),
    mesure="rise_ratio", seuils=((1.60, "together"), (2.60, "hips_slightly_ahead"), (INF, "hips_shoot_up")),
    note_source="Delta y de la hanche divise par delta y de l'epaule, sur le premier tiers "
                "de la tiree. Sans dimension. C'est le defaut n.1 du deadlift et le seul "
                "persona qui se deduit d'un nombre. Seuils A VALIDER contre une annotation "
                "image : ils sont poses au jugement, pas mesures.",
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
    portee=Portee.REP, critere="setup",
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
    portee=Portee.REP, critere="spine",
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
    id="P05", nom="knee_valgus", phase=Phase.TIREE, source=Source.POSE,
    portee=Portee.REP, critere="leg_drive", vue=Vue.FACE,
    question="Do the knees stay out over the feet, or do they collapse inward?",
    etats=(Etat("tracks_out", "The knees track outward over the feet throughout.", 3),
           Etat("slight", "The knees waver inward at the hardest point but never collapse.", 3),
           Etat("collapses_in", "The knees collapse inward off the floor.", 1, persona="The X-Wing")),
    mesure="valgus_ratio", seuils=((0.08, "tracks_out"), (0.20, "slight"), (INF, "collapses_in")),
    note_source="Ecart median (x_genou - x_cheville) rapporte a l'ecart des chevilles, vers "
                "l'interieur, pendant la tiree. VUE DE FACE uniquement : de profil un genou "
                "qui rentre est indiscernable d'un genou qui avance. C'est la seule mesure "
                "qui donne quelque chose aux clips de face, ou la derive est suspendue.",
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
    portee=Portee.REP, critere="lockout",
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
    portee=Portee.REP, critere="lockout", vue=Vue.FACE,
    question="Does one side of the bar rise ahead of the other?",
    etats=(Etat("even", "Both sides rise together.", 3),
           Etat("uneven", "One side finishes ahead of the other and the bar rotates.", 2,
                persona="The Helicopter")),
    note_source="A TESTER : la difference de hauteur des deux poignets est calculable de "
                "face. Mais perspective, prise mixte et flexion de barre imitent une "
                "asymetrie. Confirmer sur une seconde vue avant de conclure.",
)

P10 = Indicateur(
    id="P10", nom="elbow_flexion", phase=Phase.TIREE, source=Source.A_TESTER,
    portee=Portee.REP, critere="setup",
    question="Do the elbows bend during the pull?",
    etats=(Etat("straight", "The arms stay long throughout the pull.", 3),
           Etat("bent", "The elbows flex during the pull, pulling with the arms.", 1,
                persona="The T-Rex")),
    note_source="A TESTER, meme raison que S06 : l'angle est calculable, la flexion utile "
                "a detecter est petite et le bras oppose est souvent occulte.",
)


# =============================================================================
# LOCKOUT
# =============================================================================

K01 = Indicateur(
    id="K01", nom="hip_extension", phase=Phase.LOCKOUT, source=Source.POSE,
    portee=Portee.REP, critere="lockout", vue=Vue.PROFIL,
    question="Do the hips reach full extension at the top?",
    etats=(Etat("incomplete", "The hips stay visibly bent at the top.", 1,
                persona="The Soft-Lock"),
           Etat("complete", "The hips reach full extension, the lifter standing tall.", 3)),
    mesure="hip_lockout_deg", seuils=((160.0, "incomplete"), (INF, "complete")),
)

K02 = Indicateur(
    id="K02", nom="knee_extension", phase=Phase.LOCKOUT, source=Source.POSE,
    portee=Portee.REP, critere="lockout", vue=Vue.PROFIL,
    question="Do the knees reach full extension at the top?",
    etats=(Etat("incomplete", "The knees stay visibly soft at the top.", 1,
                persona="The Soft-Lock"),
           Etat("complete", "The knees lock out fully.", 3)),
    mesure="knee_lockout_deg", seuils=((160.0, "incomplete"), (INF, "complete")),
)

K03 = Indicateur(
    id="K03", nom="lean_back", phase=Phase.LOCKOUT, source=Source.POSE,
    portee=Portee.REP, critere="lockout", vue=Vue.PROFIL,
    question="Does the lifter lean back at the top?",
    etats=(Etat("upright", "The lifter finishes upright and neutral.", 3),
           Etat("slight", "A slight lean back at the top.", 3),
           Etat("hyperextension", "Marked lumbar hyperextension at the top instead of "
                                  "finishing with the glutes.", 1, persona="The Over-Extender")),
    mesure="lean_back_deg", seuils=((5.0, "upright"), (15.0, "slight"), (INF, "hyperextension")),
    note_source="Inclinaison du segment hanche-epaule au-dela de la verticale, du cote "
                "oppose au regard. Seuils poses au jugement, A VALIDER.",
)

K04 = Indicateur(
    id="K04", nom="shrug", phase=Phase.LOCKOUT, source=Source.A_TESTER,
    portee=Portee.REP, critere="lockout",
    question="Does the lifter shrug the shoulders to finish?",
    etats=(Etat("no", "The lift finishes with hip extension alone.", 3),
           Etat("yes", "The lifter shrugs the shoulders at the top: the shrug adds no "
                       "height to the bar and abandons the lat position.", 2,
                persona="The Shrugger")),
    note_source="A TESTER : l'elevation de l'epaule par rapport a l'oreille est calculable, "
                "mais elle se confond avec un simple redressement du cou. A annoter.",
)

K05 = Indicateur(
    id="K05", nom="lockout_balance", phase=Phase.LOCKOUT, source=Source.A_TESTER,
    portee=Portee.REP, critere="lockout", vue=Vue.PROFIL,
    question="Where is the lifter's balance at the top?",
    etats=(Etat("held", "The lifter finishes balanced over the feet.", 3),
           Etat("behind_heels", "The lifter's weight goes behind the heels and they lean or "
                           "stumble backward.", 2, persona="The Heel Tipper")),
    note_source="A TESTER : x_hanche par rapport a x_cheville est calculable de profil, "
                "mais c'est un proxy grossier du centre de masse et la pose ne mesure "
                "aucune pression plantaire.",
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
# DESCENTE
# =============================================================================

E01 = Indicateur(
    id="E01", nom="descent_initiation", phase=Phase.DESCENTE, source=Source.POSE,
    portee=Portee.REP, critere="descent", vue=Vue.PROFIL,
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
    portee=Portee.REP, critere="descent",
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
    portee=Portee.REP, critere=None,
    question="How does this rep connect to the next one?",
    etats=(Etat("reset", "The bar comes to a full stop on the floor before the next rep."),
           Etat("touch_and_go", "The bar touches and is immediately pulled again."),
           Etat("bounce", "The plates bounce off the floor and the bounce is used."),
           Etat("last_rep", "This is the last rep of the set.")),
    note_source="Descriptif : le touch-and-go n'est pas une faute, c'est un style. "
                "Sert a interpreter le critere de descente et la tenue du set.",
)


# =============================================================================
# La liste. Tout le reste du code lit ceci.
# =============================================================================

INDICATEURS: tuple[Indicateur, ...] = (
    C01, C02, C03, C04, C05,
    S01, S02, S03, S04, S05, S06, S07, S08,
    L01, L02, L03, L04,
    P01, P02, P03, P04, P05, P06, P07, P08, P09, P10,
    K01, K02, K03, K04, K05, K06,
    E01, E02, E03,
)

# L'action a essayer pour chaque etat fautif, en une consigne.
#
# Un conseil ne dit jamais pourquoi ("tes dorsaux sont faibles") : il dit quoi essayer
# a charge maitrisee. La cause d'un defaut ne se lit pas sur une video, et un essai de
# consigne peut aider sans prouver quoi que ce soit. Les etats sans entree ici ne
# produisent aucun conseil : c'est le cas normal d'un etat correct ou descriptif.
CONSEILS = {
    "hip_height:too_low": "Set the hips higher, between the knees and the shoulders, before you pull.",
    "hip_height:too_high": "Drop the hips a little and bring the shoulders over the bar.",
    "shoulders_over_bar:behind_bar": "Set the shoulders over or just ahead of the bar before you pull.",
    "shoulders_over_bar:far_ahead": "Bring the hips down slightly so the shoulders sit closer to over the bar.",
    "shin_angle:angled": "Sit the hips back until the shins are vertical before you pull.",
    "bar_over_midfoot:ahead_of_midfoot": "Set the bar over the middle of your foot, close to the shins.",
    "arms_straight:bent": "Keep the arms long and let the legs do the work.",
    "elbow_flexion:bent": "Keep the arms long through the whole pull.",
    "slack_pull:partial": "Pull the slack out until you feel the bar load, then push the floor away.",
    "slack_pull:yanked": "Take the slack out of the bar before you pull instead of yanking it.",
    "jerky_start:jerked": "Build tension against the bar, then accelerate: do not snatch it off the floor.",
    "back_at_setup:lower_back_rounded": "Set the back flat before the bar moves; drop the load if you cannot hold it.",
    "hip_vs_shoulder_rise:hips_shoot_up": "Push the floor away and hold your chest angle through the first third of the pull.",
    "torso_pitch:pitches_forward": "Keep the torso angle as the bar leaves the floor rather than letting the hips win.",
    "hand_drift:moderate_drift": "Pull the shoulders down and keep the bar tracking over the mid-foot.",
    "hand_drift:large_drift": "Keep the bar against your legs: pull the shoulders down and drag it up the shins.",
    "bar_leg_contact:away_from_legs": "Keep the bar in contact with the legs the whole way up.",
    "past_the_knees:loops": "Let the hips come through as the bar reaches the knees so it passes close.",
    "past_the_knees:catches": "Sit the hips back a touch at the knees so the bar has a path.",
    "back_under_load:flexion_appears": "Brace before you pull, and end the set when the shape starts to change.",
    "back_under_load:collapses": "Stop the set. Rebuild this at a load where the back holds its shape.",
    "knee_valgus:collapses_in": "Push the knees out over your toes as you drive off the floor.",
    "hitch:yes": "Finish with one continuous hip extension instead of ratcheting the bar up the thighs.",
    "asymmetry:uneven": "Film a front view and check whether one side is leading before changing anything.",
    "hip_extension:incomplete": "Finish standing tall, hips and knees locked together.",
    "knee_extension:incomplete": "Lock the knees at the top instead of leaving them soft.",
    "lean_back:hyperextension": "Finish tall by squeezing the glutes, not by leaning back.",
    "shrug:yes": "Finish with the hips: the shrug adds no height to the bar.",
    "lockout_balance:behind_heels": "Finish balanced over your feet rather than drifting behind your heels.",
    "descent_initiation:at_the_knees": "Send the hips back first and let the knees bend once the bar has passed them.",
    "descent_control:dropped": "Stay with the bar on the way down instead of dropping it.",
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


_verifie()
