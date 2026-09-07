"""Schemas d'analyse — le modele observe, Python note.

Principe directeur, et seule vraie difference avec la version precedente : le
modele ne rend plus de chiffre. Pour chaque critere et chaque repetition, il
choisit **un etat observable** dans une liste fermee ("le torse garde son angle",
"les hanches partent d'un coup"), et c'est `note_de()` qui traduit cet etat en
1, 2, 3 ou None.

Trois consequences, dans l'ordre de ce qu'elles rapportent :

1. **Recalibrer ne coute plus un appel.** Le bareme est une table Python. On le
   rejoue sur des sorties deja stockees et on renote les 49 clips gratuitement.
   Vu que le plancher de bruit interdit de conclure sous ~10 points (AGENTS.md),
   pouvoir renoter a volonte sans repasser par Gemini est le levier le plus
   rentable disponible : une passe sert desormais a plusieurs baremes.
2. **Moins de bruit a l'entree.** "Les hanches montent avant les epaules" est un
   jugement plus stable d'une passe a l'autre que "ca vaut 2". On ne demande au
   modele que ce qu'il voit, jamais l'arbitrage.
3. **Le bareme se relit.** Il etait dissemine dans des `description=` que seul le
   modele interpretait ; il est ici en clair, diffable, et testable sans reseau.

Ce qui est garde de la version precedente, parce que c'etait juste : la
distinction "pas visible" / "vu et mauvais", `bar_left_floor` en champ dedie,
l'observation avant le jugement, et le persona en dernier — pousse ici jusqu'au
bout, voir `persona_du_set`.

Ce qui n'est PAS repris : la mediane pour agreger les reps. Elle a l'air plus
robuste au bruit, mais `_moyenne_arrondie` dans ai_service.py porte la mesure
qui la refuse (elle efface la rep isolee que l'histogramme montre juste au
dessus). L'agregation reste ou elle est.
"""

from dataclasses import dataclass
from enum import Enum
from typing import get_args

from pydantic import BaseModel, Field, create_model


class VideoClassification(BaseModel):
    # We use a str and not Enum purposely because it works better
    mouvement_detecte: str = Field(description="Must be 'squat', 'bench press', 'sumo deadlift', 'conventional deadlift', or 'unworkable_video")


# --- Vocabulaire du bareme ---------------------------------------------------


@dataclass(frozen=True)
class Etat:
    """Un etat observable d'un critere, et ce qu'il vaut.

    `note` a None veut dire "non evaluable" — reserve a `NON_VISIBLE`.
    `persona` est l'archetype que CET etat declenche : le persona se rattache a
    une observation precise, pas a un critere entier. "Les hanches partent d'un
    coup" fait The Crane ; le reste du critere leg drive ne fait rien.
    """

    cle: str
    description: str
    note: int | None
    persona: str | None = None


# Present sur tous les criteres, ajoute automatiquement en dernier. C'est
# l'ancien "NA", devenu un etat observable comme les autres : la question posee
# au modele est toujours "qu'est-ce que tu vois", et "je ne vois pas" en est une
# reponse valable. Un defaut VU reste une note basse, jamais celui-ci.
NON_VISIBLE = Etat(
    cle="not_visible",
    description="The camera angle, framing, lighting or video quality makes this "
                "criterion impossible to assess on this rep (e.g. the feet are out "
                "of frame, so bar-over-midfoot cannot be judged). Not for something "
                "you saw and disliked.",
    note=None,
)


@dataclass(frozen=True)
class Critere:
    """Un critere note, declare UNE seule fois.

    Le bloc "une rep" et le bloc de synthese sont tous les deux generes a partir
    d'ici. La version precedente ecrivait les noms de criteres deux fois et
    devait lever une RuntimeError a l'import pour rattraper les fautes de frappe
    entre les deux : ce garde-fou n'a plus d'objet.

    `poids` : tous les defauts ne se valent pas. Un dos qui s'enroule sous
    charge et un lockout mou ne devraient pas peser pareil dans la note sur 20.
    """

    nom: str
    question: str
    etats: tuple[Etat, ...]
    poids: float = 1.0

    @property
    def tous_les_etats(self) -> tuple[Etat, ...]:
        return self.etats + (NON_VISIBLE,)

    def etat(self, cle) -> Etat | None:
        if isinstance(cle, Enum):
            cle = cle.value
        return next((e for e in self.tous_les_etats if e.cle == cle), None)

    def enum(self) -> type[Enum]:
        """L'enum ferme des cles, tel que le decodage contraint l'imposera."""
        return Enum(
            f"{''.join(m.capitalize() for m in self.nom.split('_'))}Observation",
            {e.cle.upper(): e.cle for e in self.tous_les_etats},
            type=str,
        )

    def consigne(self) -> str:
        """La description portee par le champ `observation`, en anglais."""
        lignes = [f"- '{e.cle}': {e.description}" for e in self.tous_les_etats]
        return (
            f"{self.question} Pick the ONE option below that matches what you "
            f"actually see on this repetition. Do not pick an option because the "
            f"previous rep had it — judge this rep on its own.\n" + "\n".join(lignes)
        )


def _bloc_observation(critere: Critere) -> type[BaseModel]:
    """Le modele Pydantic d'un critere sur UNE rep : l'etat, et une phrase.

    Pas de `visual_analysis` ici : sur un set de cinq reps la sortie triplerait
    sans rien apprendre de plus. La description libre reste au niveau du set.
    """
    return create_model(
        f"{''.join(m.capitalize() for m in critere.nom.split('_'))}Rep",
        observation=(critere.enum(), Field(description=critere.consigne())),
        note=(str, Field(description="One short sentence, specific to this rep, "
                                     "describing what you saw. No score, no advice.")),
    )


class SetCriterion(BaseModel):
    """Synthese d'un critere sur l'ensemble du set.

    Pas de champ de note, deliberement : la note affichee est CALCULEE a partir
    des etats observes rep par rep. Si on demandait en plus une synthese chiffree
    au modele, la page porterait deux nombres pour la meme chose, libres de se
    contredire.
    """

    visual_analysis: str = Field(description="Describe strictly what you see physically across the whole set for this criterion (e.g. 'the lower back is visibly rounding', 'the bar drifts away from the shins'). No score.")
    feedback: str = Field(description="Actionable advice when the set is flawed on this criterion. A single short, punchy sentence of praise when it is executed well. When the criterion was not visible on any rep, state exactly what is not visible and how to reframe the next video.")


SET_CONSISTENCY = Critere(
    nom="set_consistency",
    question="How does the technique hold up ACROSS the reps of the set?",
    etats=(
        Etat("holds_together", "The last rep looks like the first - same setup, same bar path, same lockout - with at most a slight decay on the final rep.", 3),
        Etat("visible_drift", "Visible drift over the set: the bar drifts further out, the back rounds a little more, or the lockout gets slower rep after rep.", 2),
        Etat("collapses", "The technique collapses: a clearly dangerous rep appears late, or the last rep looks nothing like the first.", 1),
        Etat("single_rep", "The video contains a single repetition: there is nothing to compare.", None),
    ),
)

# Le seul critere que le modele note encore lui-meme : il porte sur l'ecart ENTRE
# les reps, il n'a donc pas de version "une rep" et rien a agreger. `ai_service`
# le force a 'single_rep' quand la video n'en contient qu'une.
SetConsistency = create_model(
    "SetConsistency",
    visual_analysis=(str, Field(description="Compare the first rep to the last: setup, bar path, lockout speed. Describe what changes across the set, if anything.")),
    observation=(SET_CONSISTENCY.enum(), Field(description=SET_CONSISTENCY.consigne())),
    feedback=(str, Field(description="Name the reps you are talking about, e.g. 'it starts to break down between rep 5 and rep 8'.")),
)


# --- Baremes -----------------------------------------------------------------
# Un critere par evenement physique INDEPENDANT. La version precedente notait
# huit criteres dont plusieurs decrivaient la meme chose : `leg_drive_activation`,
# `hip_hinge_mechanics` et le persona The Crane parlent tous des hanches qui
# partent en premier, donc un seul defaut pesait trois fois dans la note sur 20.
# Un chiffre qui bouge parce qu'un defaut est compte trois fois n'est pas plus
# precis, juste plus bruyant.

SETUP_CONV = Critere(
    nom="setup_and_tension",
    question="What does the lifter's position and tension look like in the instant BEFORE the bar leaves the floor?",
    etats=(
        Etat("set_and_wedged", "Bar over mid-foot with the shins close to it, hips between knees and shoulders, back flat, arms pulled taut and the slack out before the bar moves.", 3),
        Etat("one_element_off", "The setup is sound but one element is slightly off - bar a little forward, hips a touch high or low, or the upper back a little soft.", 3),
        Etat("tension_fades", "Tension is set up but lost before the bar moves: the hips shift or the arms go soft at liftoff.", 2),
        Etat("hips_too_low", "The lifter squats the setup: pelvis very low, shins pushed forward, knees over the bar.", 2, persona="The Squatter"),
        Etat("elbows_bent", "The elbows are actively flexed at the start, loading the biceps tendon directly.", 1, persona="The T-Rex"),
        Etat("grip_and_rip", "No pre-tension at all: the lifter jerks the bar off the floor from a loose position.", 1, persona="The Grip & Rip"),
    ),
)

LEG_DRIVE_CONV = Critere(
    nom="leg_drive_off_the_floor",
    question="What happens to the torso angle over the first third of the pull?",
    etats=(
        Etat("torso_angle_held", "The torso angle is held, hips and shoulders rising together, the legs driving the floor away.", 3),
        Etat("hips_slightly_ahead", "The hips rise slightly ahead of the shoulders, but the torso does not pitch forward.", 3),
        Etat("early_hip_rise", "Noticeable early hip rise: quad drive is minimal and the back starts taking over.", 2),
        Etat("hips_shoot_up", "The hips shoot up immediately and it becomes a stiff-legged pull finished by the back.", 1, persona="The Crane"),
    ),
)

SPINE = Critere(
    nom="spine_under_load",
    question="Does the back keep the SAME shape from setup to lockout, or does flexion get added under load?",
    etats=(
        Etat("shape_unchanged", "The back holds the same shape at setup, at knee height and at lockout - no flexion added under load.", 3),
        Etat("stable_rounding", "There is upper-back rounding, but it is set from the start and does not get worse during the pull.", 3),
        Etat("flexion_appears", "Noticeable lumbar flexion appears during the pull that was not there at setup.", 2),
        Etat("back_rounds_hard", "The lower back is visibly rounded under load and rounds further as the bar rises.", 1, persona="The Fishing Rod"),
    ),
    poids=2.0,  # le seul critere ou une mauvaise note est une blessure, pas un kilo perdu
)

BAR_PROXIMITY = Critere(
    nom="bar_proximity",
    question="How close does the bar stay to the legs on the way up?",
    etats=(
        Etat("stays_on_the_legs", "The bar stays against or within a few centimetres of the legs the whole way up.", 3),
        Etat("brief_loss_at_knee", "Contact is briefly lost around the knee, then the bar comes back to the legs.", 3),
        Etat("loops_forward", "The bar loops forward around the knees before coming back in.", 2),
        Etat("drifts_far", "The bar drifts well away from the legs, pulling the lifter forward and lengthening the moment arm.", 1, persona="The Pendulum"),
    ),
)

LOCKOUT_CONV = Critere(
    nom="lockout",
    question="How does the lift finish?",
    etats=(
        Etat("hips_and_knees_together", "Hips and knees reach full extension together, the lifter standing tall with the bar against the thighs.", 3),
        Etat("brief_stall", "A brief stall at the top or a slight lean back, but the lockout is completed cleanly.", 3),
        Etat("shrugged_finish", "The lifter shrugs the shoulders to finish instead of completing hip extension - the shrug adds no height to the bar.", 2, persona="The Shrugger"),
        Etat("soft_or_stuttering", "The lockout is slow or stuttering, or the hips and knees stay visibly soft at the top.", 2, persona="The Soft-Lock"),
        Etat("hyperextended", "Extreme lumbar hyperextension at the top instead of finishing with the glutes.", 1, persona="The Over-Extender"),
        Etat("hitched", "The lifter re-flexes the knees and rests the bar on the thighs to ratchet it up.", 1, persona="The Hitcher"),
    ),
    poids=1.5,
)

DESCENT = Critere(
    nom="descent",
    question="How is the bar brought back down? If each rep is reset on the floor, only a dropped or uncontrolled bar is a fault - a deliberately fast but accompanied lowering is not. If the reps are touch-and-go, judge the transition into the next rep.",
    etats=(
        Etat("hips_back_first", "The bar is lowered under control, hips travelling back first, knees bending once the bar has passed them.", 3),
        Etat("fast_but_accompanied", "The descent is quick but the lifter stays with the bar all the way down.", 3),
        Etat("knees_bend_early", "The knees bend before the bar has passed them, pushing the bar forward or into the kneecaps.", 2, persona="The Kneecapper"),
        Etat("dropped", "The bar is dropped, crashes down, or bounces heavily off the floor or the knees.", 1),
    ),
)

SETUP_SUMO = Critere(
    nom="setup_and_wedge",
    question="What does the sumo setup and the wedge look like in the instant BEFORE the bar leaves the floor?",
    etats=(
        Etat("wedged_and_tight", "Wide stance, toes flared, shins vertical or nearly so, shoulders stacked over the bar, hips wedged in close with full-body tension before the bar moves.", 3),
        Etat("one_element_off", "The wedge is there but one element is slightly off - shins a little angled, hips a touch low, or shoulders slightly behind the bar.", 3),
        Etat("wedge_lost", "The lifter wedges in but loses it instantly: the hips shift back before the bar leaves the floor.", 2),
        Etat("hips_far_from_bar", "The hips start far behind the bar, closer to a wide-stance conventional pull than to a wedge.", 2, persona="The Squatter"),
        Etat("elbows_bent", "The elbows are actively flexed at the start, loading the biceps tendon directly.", 1, persona="The T-Rex"),
        Etat("grip_and_rip", "No pre-tension at all: the lifter jerks the bar off the floor from a loose position.", 1, persona="The Grip & Rip"),
    ),
)

LEG_DRIVE_SUMO = Critere(
    nom="leg_drive_and_floor_spread",
    question="What happens to the torso angle and the lateral push over the first third of the pull?",
    etats=(
        Etat("spreads_the_floor", "Solid leg drive actively spreading the floor laterally, the torso staying upright off the floor.", 3),
        Etat("hips_slightly_ahead", "The hips rise slightly ahead, but the torso does not pitch forward.", 3),
        Etat("early_hip_rise", "Noticeable early hip rise, weak quad drive, the erectors taking over.", 2),
        Etat("hips_shoot_up", "The hips shoot straight up with no lateral push and the back finishes the lift.", 1, persona="The Crane"),
    ),
)

KNEE_TRACKING = Critere(
    nom="knee_tracking",
    question="Where do the knees go relative to the toes during the pull? (frontal plane)",
    etats=(
        Etat("track_over_toes", "The hips stay open and the knees track outward over the flared toes throughout.", 3),
        Etat("minor_wavering", "The knees waver slightly inward at the hardest point but never really collapse.", 3),
        Etat("knees_cave", "Noticeable knee cave through the middle of the pull, the lifter struggling to keep the hips open.", 2),
        Etat("severe_valgus", "The knees violently collapse inward off the floor.", 1, persona="The X-Wing"),
    ),
    poids=1.5,
)

LOCKOUT_SUMO = Critere(
    nom="lockout",
    question="How does the lift finish?",
    etats=(
        Etat("knees_and_hips_together", "Knees and hips lock out together, upright and neutral, without leaning back.", 3),
        Etat("brief_stall", "A brief stall at the top, but the lockout is completed cleanly.", 3),
        Etat("shrugged_finish", "The lifter shrugs the shoulders to finish instead of completing hip extension - the shrug adds no height to the bar.", 2, persona="The Shrugger"),
        Etat("soft_or_stuttering", "The lockout is slow or stuttering, or the hips and knees stay visibly soft at the top.", 2, persona="The Soft-Lock"),
        Etat("uneven", "The lockout is asymmetrical: one side finishes before the other and the bar rotates horizontally.", 2, persona="The Helicopter"),
        Etat("falls_backward", "The lifter's balance goes behind the heels at the top and they lean or stumble backward.", 1, persona="The Heel Tipper"),
        Etat("hitched", "The lifter re-flexes the knees and rests the bar on the thighs to ratchet it up.", 1, persona="The Hitcher"),
    ),
    poids=1.5,
)

DEPTH = Critere(
    nom="depth",
    question="Where is the hip crease at the bottom, relative to the top of the knee?",
    etats=(
        Etat("at_or_below_parallel", "The hip crease reaches or passes the top of the knee.", 3),
        Etat("just_above_parallel", "The hip crease stops just short of the top of the knee.", 2),
        Etat("clearly_high", "The squat stops clearly above parallel, or is barely a quarter squat.", 1),
    ),
)

SQUAT_BAR_PATH = Critere(
    nom="bar_path",
    question="What line does the bar follow relative to the mid-foot?",
    etats=(
        Etat("over_midfoot", "A straight line over mid-foot; a few centimetres of wander is still this.", 3),
        Etat("forward_out_of_the_hole", "Visible forward drift as the lifter comes out of the hole.", 2),
        Etat("turns_into_good_morning", "The bar drifts far forward and the hips shoot up, turning the rep into a good-morning.", 1),
    ),
)

SQUAT_KNEES = Critere(
    nom="knee_tracking",
    question="Where do the knees go relative to the toes?",
    etats=(
        Etat("track_over_toes", "The knees track over the toes throughout, with at most minor wavering.", 3),
        Etat("cave_and_recover", "The knees cave slightly under load, then recover.", 2),
        Etat("severe_valgus", "Severe valgus: the knees collapse inward.", 1),
    ),
    poids=1.5,
)

SQUAT_BRACING = Critere(
    nom="bracing",
    question="What happens to the chest and the spine under load?",
    etats=(
        Etat("holds_its_shape", "Proud chest, neutral spine holding its shape; a slight forward lean out of the hole is still this.", 3),
        Etat("some_chest_drop", "Some chest drop or rounding coming out of the hole.", 2),
        Etat("collapses", "The chest collapses and the back rounds under the bar.", 1),
    ),
    poids=2.0,
)

SQUAT_DESCENT = Critere(
    nom="descent",
    question="How does the lifter start and control the way down?",
    etats=(
        Etat("simultaneous_and_controlled", "Hips and knees break together and the eccentric is smooth and controlled.", 3),
        Etat("slight_mistiming", "Slight mistiming between hips and knees, or the descent gets fast in the bottom third.", 2),
        Etat("hinge_only_or_divebomb", "The lifter hinges at the hips only (or the knees only), or free-falls into the bottom.", 1),
    ),
)

BENCH_SETUP = Critere(
    nom="setup_and_arch",
    question="What does the upper-back setup look like, and does it survive the press?",
    etats=(
        Etat("held_throughout", "Scapulae retracted and the arch held throughout; a modest arch that stays tight is still this.", 3),
        Etat("lost_during_press", "The arch and retraction are set up but lost during the press.", 2),
        Etat("flat_and_loose", "Completely flat back, shoulders loose on the bench.", 1),
    ),
)

BENCH_LEG_DRIVE = Critere(
    nom="leg_drive",
    question="What are the legs doing during the press?",
    etats=(
        Etat("constant_tension", "Constant tension driving the body towards the head, feet planted.", 3),
        Etat("drive_fades", "The legs are tense but the drive fades and the feet shift mid-set.", 2),
        Etat("butt_lifts_or_loose", "The glutes come off the bench, or the legs are completely loose.", 1),
    ),
)

BENCH_BAR_PATH = Critere(
    nom="bar_path_and_touch",
    question="What line does the bar follow, and where does it touch?",
    etats=(
        Etat("j_curve_to_sternum", "A J-curve back over the shoulders, touching the lower chest or sternum.", 3),
        Etat("consistent_but_vertical", "A nearly vertical but consistent path, touching the same spot every rep.", 3),
        Etat("drifts_or_wanders", "The path drifts towards the face or the belly, or the touch point moves from rep to rep.", 2),
        Etat("guillotine", "The bar comes down to the neck or collarbone, or is pressed straight up from the belly.", 1),
    ),
    poids=1.5,
)

BENCH_ELBOWS = Critere(
    nom="elbow_stability",
    question="What angle do the elbows hold relative to the torso?",
    etats=(
        Etat("stacked_and_stable", "Stacked under the bar at roughly 45-60 degrees and holding that angle.", 3),
        Etat("flare_off_the_chest", "The elbows flare out as the bar leaves the chest.", 2),
        Etat("extreme_flare_or_tuck", "The elbows are extremely flared at 90 degrees, or heavily tucked to the ribs.", 1),
    ),
)

BENCH_PAUSE = Critere(
    nom="chest_pause",
    question="What happens when the bar reaches the chest?",
    etats=(
        Etat("dead_stop", "A visible, dead stop on the chest.", 3),
        Etat("touch_and_go", "A brief touch-and-go with no real stop.", 2),
        Etat("bounced", "The bar is heaved or bounced off the chest.", 1),
    ),
)


BAREMES: dict[str, tuple[Critere, ...]] = {
    "squat": (DEPTH, SQUAT_DESCENT, SQUAT_BAR_PATH, SQUAT_KNEES, SQUAT_BRACING),
    "bench press": (BENCH_SETUP, BENCH_LEG_DRIVE, BENCH_BAR_PATH, BENCH_ELBOWS, BENCH_PAUSE),
    "conventional deadlift": (SETUP_CONV, LEG_DRIVE_CONV, SPINE, BAR_PROXIMITY, LOCKOUT_CONV, DESCENT),
    "sumo deadlift": (SETUP_SUMO, LEG_DRIVE_SUMO, KNEE_TRACKING, SPINE, BAR_PROXIMITY, LOCKOUT_SUMO, DESCENT),
}


# --- Generation des schemas --------------------------------------------------

REPS_RUBRIC = (
    "One entry per repetition performed in the video, in chronological order, "
    "starting at rep_index 1. Fill EVERY criterion for EVERY rep. If the lifter "
    "performs a single rep, return exactly one entry."
)

BAR_LEFT_FLOOR = Field(
    default=True,
    description="true if the bar left the floor and was lifted to lockout in this "
                "segment: this is a real repetition. false if the bar stayed on the "
                "floor, or was already down and the athlete simply stood back up: "
                "that is NOT a repetition and the entry will be discarded.")


def _modele_de_rep(mouvement: str, criteres: tuple[Critere, ...]) -> type[BaseModel]:
    nom = "".join(m.capitalize() for m in mouvement.replace(" ", "_").split("_"))
    champs: dict = {
        "rep_index": (int, Field(description="1 for the first rep of the set, 2 for the second, and so on. Never repeat an index.")),
    }
    for critere in criteres:
        champs[critere.nom] = (_bloc_observation(critere), Field(description=critere.question))
    if "deadlift" in mouvement:
        # La pose voit le corps, pas la barre : se redresser apres avoir repose la
        # barre produit exactement le meme mouvement qu'une repetition, et seul le
        # modele peut trancher. Champ dedie et non `not_visible` — "pas visible"
        # repond deja a une autre question, et les confondre supprimerait une vraie
        # rep filmee sous un mauvais angle.
        champs["bar_left_floor"] = (bool, BAR_LEFT_FLOOR)
    return create_model(f"{nom}Rep", **champs)


def _modele_d_analyse(mouvement: str, criteres: tuple[Critere, ...]) -> type[BaseModel]:
    """Le schema complet d'un mouvement.

    L'ordre des champs est l'ordre de generation en decodage contraint : le
    detail par rep d'abord, la synthese ensuite, la consistance en dernier. Le
    persona ne figure plus dans le schema du tout (voir `persona_du_set`) : c'est
    la conclusion la plus tardive possible, donc elle ne se genere pas.
    """
    nom = "".join(m.capitalize() for m in mouvement.replace(" ", "_").split("_"))
    champs: dict = {
        "reps": (list[_modele_de_rep(mouvement, criteres)], Field(description=REPS_RUBRIC)),
    }
    for critere in criteres:
        champs[critere.nom] = (SetCriterion, Field(description=critere.question))
    champs["set_consistency"] = (SetConsistency, Field(description=SET_CONSISTENCY.question))
    return create_model(f"Analyze{nom}", **champs)


schema_mapping: dict[str, type[BaseModel]] = {
    mouvement: _modele_d_analyse(mouvement, criteres)
    for mouvement, criteres in BAREMES.items()
}


# --- Notation ----------------------------------------------------------------

PERSONA_PAR_DEFAUT = "The Technician"


def critere(mouvement: str, nom: str) -> Critere | None:
    return next((c for c in BAREMES.get(mouvement, ()) if c.nom == nom), None)


def criteres_de_synthese(mouvement: str) -> list[str]:
    """Noms des criteres notes, dans l'ordre. `set_consistency` n'en fait pas partie."""
    return [c.nom for c in BAREMES.get(mouvement, ())]


def note_de(mouvement: str, nom_critere: str, observation) -> int | None:
    """La note d'un etat observe. None si non evaluable OU si l'etat est inconnu.

    C'est ici, et nulle part ailleurs, que se decide combien vaut un defaut.
    Changer un chiffre dans les tables ci-dessus et relancer sur des sorties
    stockees suffit a renoter tout le jeu d'evaluation, sans un seul appel.
    """
    c = SET_CONSISTENCY if nom_critere == SET_CONSISTENCY.nom else critere(mouvement, nom_critere)
    if c is None:
        return None
    etat = c.etat(observation)
    return etat.note if etat is not None else None


def note_sur_20(notes: dict[str, int | None], mouvement: str) -> int | None:
    """La note affichee, ponderee par `Critere.poids`.

    Les criteres non evaluables sortent du calcul ET du denominateur : un clip ou
    le dos n'est pas visible n'est pas un clip ou le dos est mauvais.
    """
    haut, bas = 0.0, 0.0
    for nom, note in notes.items():
        c = critere(mouvement, nom)
        if c is None or note is None:
            continue
        haut += c.poids * note
        bas += c.poids * 3
    return None if bas == 0 else int(haut / bas * 20 + 0.5)


def persona_du_set(observations: list[tuple[str, str]], mouvement: str) -> str:
    """Le persona, DEDUIT des etats observes. Le modele ne le choisit plus.

    Chaque persona est deja la description d'un etat precis — The Fishing Rod est
    "le dos s'enroule", The Soft-Lock est "le lockout reste mou". Le demander au
    modele en plus, c'est lui faire refaire un travail qu'il vient de faire, avec
    le droit de se contredire : la version precedente le mesurait a 4 accords sur
    48, et sortait The Crane 15 fois sur 48.

    Regle : le defaut le plus grave observe. A gravite egale, le critere le plus
    lourd ; puis l'ordre de declaration, qui va du plus grave au moins grave.
    `observations` est la liste des (nom_critere, cle_etat) de TOUTES les reps :
    un defaut qui n'apparait qu'une fois compte, c'est l'histogramme qui dit s'il
    est isole.
    """
    candidats = []
    for rang, (nom_critere, cle) in enumerate(observations):
        c = critere(mouvement, nom_critere)
        if c is None:
            continue
        etat = c.etat(cle)
        if etat is None or etat.persona is None or etat.note is None:
            continue
        candidats.append((etat.note, -c.poids, c.etats.index(etat), rang, etat.persona))
    return min(candidats)[-1] if candidats else PERSONA_PAR_DEFAUT


def personas_possibles(mouvement: str) -> list[str]:
    """Le vocabulaire des personas d'un mouvement, pour le front et les tests."""
    vus = {e.persona for c in BAREMES.get(mouvement, ()) for e in c.etats if e.persona}
    return sorted(vus) + [PERSONA_PAR_DEFAUT]


def prompt_de_justification(persona: str, observations: list[str]) -> str:
    """Le prompt du second appel, court, qui habille le persona deja calcule.

    Un appel de plus, sur le modele le moins cher : le persona reste explique
    dans les mots de la video plutot que par une phrase generique, sans lui
    laisser le droit de choisir l'etiquette.
    """
    faits = "\n".join(f"- {o}" for o in observations)
    return (
        f'A lifter was analysed and classified as "{persona}", based strictly on '
        f"these observations from the video:\n{faits}\n\n"
        f"Write ONE short, fun sentence explaining why they earned that nickname. "
        f"Use only the observations above. Do not invent anything, do not give advice, "
        f"do not mention scores."
    )


# --- Compatibilite ------------------------------------------------------------

def numeric_score(value) -> int | None:
    """Score as an int, or None when the criterion was not assessable.

    Ne sert plus qu'aux sorties deja stockees par l'ancien schema : le modele
    n'emet plus de chiffre du tout.
    """
    if isinstance(value, Enum):
        value = value.value
    if isinstance(value, bool):  # bool est un sous-type d'int, on le refuse
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 3 else None
    if isinstance(value, str) and value.isdigit():
        n = int(value)
        return n if 1 <= n <= 3 else None
    return None


def modele_de_rep(schema):
    """Le modele "une rep" associe a un schema d'analyse."""
    champ = schema.model_fields.get("reps")
    return get_args(champ.annotation)[0] if champ is not None else None
