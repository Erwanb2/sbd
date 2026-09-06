from enum import Enum
from typing import get_args

from pydantic import BaseModel, Field


class VideoClassification(BaseModel):
    # We use a str and not Enum purposely because it works better
    mouvement_detecte: str = Field(description="Must be 'squat', 'bench press', 'sumo deadlift', 'conventional deadlift', or 'unworkable_video")

class ConventionnalDeadliftPersona(str, Enum):
    THE_GRIP_AND_RIP = "The Grip & Rip"
    THE_CRANE = "The Crane"
    THE_SQUATTER = "The Squatter"
    THE_FISHING_ROD = "The Fishing Rod"
    THE_OVER_EXTENDER = "The Over-Extender"
    THE_HITCHER = "The Hitcher"
    THE_PENDULUM = "The Pendulum"
    THE_KNEECAPPER = "The Kneecapper"
    THE_T_REX = "The T-Rex"
    THE_METEOR = "The Meteor"
    THE_BOUNCER = "The Bouncer"
    THE_PEZ_DISPENSER = "The Pez Dispenser"
    THE_SOFT_LOCK = "The Soft-Lock"
    THE_SHRUGGER = "The Shrugger"


class SumoDeadliftPersona(str, Enum):
    THE_GRIP_AND_RIP = "The Grip & Rip"
    THE_CRANE = "The Crane"
    THE_SQUATTER = "The Squatter"
    THE_FISHING_ROD = "The Fishing Rod"
    THE_OVER_EXTENDER = "The Over-Extender"
    THE_HITCHER = "The Hitcher"
    THE_PENDULUM = "The Pendulum"
    THE_T_REX = "The T-Rex"
    THE_KNEECAPPER = "The Kneecapper"
    THE_SOFT_LOCK = "The Soft-Lock"
    THE_X_WING = "The X-Wing"
    THE_HELICOPTER = "The Helicopter"
    THE_HEEL_TIPPER = "The Heel Tipper"
    THE_SHRUGGER = "The Shrugger"


class CriteriaScore(str, Enum):
    """Score values the model may emit.

    A str Enum rather than an int with ge/le: the enum is enforced by
    constrained decoding, so "NA" is a value the model can actually reach and
    3.5 / 0 / 7 are values it cannot.

    Trois niveaux, et non quatre. Le pipeline a longtemps demande une note sur 4
    puis la ramenait sur 3 (`1->1, 2->2, 3->2, 4->3`). Le niveau 4 etait ecrit en
    superlatifs ("perfectly", "flawless", "impeccably") : sur les 314 cases notees
    de eval/scorer, le modele ne l'a mis que 18 fois (5,7 %) la ou l'humain met
    3/3 dans 30 % des cas. Le haut de l'echelle etait donc quasi inatteignable, et
    c'est la table de compression qui portait la moitie du bareme. L'echelle est
    maintenant celle qui s'affiche : le modele note directement 1, 2 ou 3.
    """

    NA = "NA"
    ONE = "1"
    TWO = "2"
    THREE = "3"


def numeric_score(value) -> int | None:
    """Score as an int, or None when the criterion was not assessable."""
    if isinstance(value, CriteriaScore):
        value = value.value
    if isinstance(value, bool):  # bool is an int subclass, reject it explicitly
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 3 else None
    if isinstance(value, str) and value.isdigit():
        n = int(value)
        return n if 1 <= n <= 3 else None
    return None


class EvaluationCriteria(BaseModel):
    visual_analysis: str = Field(description="Describe strictly what you see physically in the video for this specific criteria (e.g., 'the lower back is visibly rounding', 'the bar drifts away from shins'). Do not give a score yet.")
    score: CriteriaScore = Field(description="'1' to '3' (1=Poor/dangerous, 2=Subpar/flawed, 3=Good), or 'NA' when the camera angle, framing, lighting or video quality makes this specific criterion impossible to assess (e.g. the feet are out of frame, so bar-over-midfoot cannot be judged). '3' is the top of the scale and it means the criterion is MET: give it whenever the rubric's level 3 is satisfied, do not withhold it because the execution is not superlative. 'NA' is for what you cannot SEE, never for what you saw and disliked: a flaw you can see is a low score, not 'NA'.")
    feedback: str = Field(description="Detailed advice if the score is 1, 2, or 3. A single short, punchy sentence providing extreme praise if the score is 4. If the score is 'NA', state exactly what is not visible and how to reframe the next video.")

class RepCriterion(BaseModel):
    """Un critere juge sur UNE repetition.

    Volontairement plus leger que le bloc de synthese : pas de `visual_analysis`
    ici, sinon la sortie triple de taille sur un set de cinq reps sans rien
    apprendre de plus. Les baremes ne sont pas repetes non plus : ils sont
    donnes une seule fois sur les champs de synthese du meme schema, que le
    modele a sous les yeux des le depart.
    """

    score: CriteriaScore = Field(description="Score for THIS repetition only, '1' to '3' against the rubric of the criterion of the same name further down in this schema, or 'NA' when this rep is impossible to assess (out of frame, obscured, cut off). Judge this rep on its own: do not copy the previous rep's score.")
    note: str = Field(description="One short sentence, specific to this rep, justifying the score. If 'NA', state exactly what is not visible on this rep.")


class SetCriterion(BaseModel):
    """Synthese d'un critere sur l'ensemble du set.

    Pas de champ `score`, deliberement : la note affichee est CALCULEE a partir
    des notes par rep (moyenne arrondie au plus proche, voir ai_service). Si on
    demandait en plus une note de synthese au modele, la page porterait deux
    nombres pour la meme chose, libres de se contredire.
    """

    visual_analysis: str = Field(description="Describe strictly what you see physically across the whole set for this criterion (e.g. 'the lower back is visibly rounding', 'the bar drifts away from shins'). Do not give a score.")
    feedback: str = Field(description="Detailed advice when the set is flawed on this criterion. A single short, punchy sentence of extreme praise when it is executed perfectly. When the criterion was not visible on any rep, state exactly what is not visible and how to reframe the next video.")


# Barème de la tenue du set. C'est le seul critère qui n'a pas de sens rep par
# rep : il porte justement sur l'écart ENTRE les reps. Il est donc noté
# directement par le modèle, et forcé à "NA" quand la vidéo ne contient qu'une
# seule rep (ai_service) — il n'y a alors rien à comparer.
SET_CONSISTENCY_RUBRIC = (
    "Evaluates how the technique holds up ACROSS the reps of the set. Compare the "
    "first rep to the last. "
    "'NA' when the video contains a single rep: there is nothing to compare. "
    "1=Poor (technique collapses over the set: a clearly dangerous rep appears late, "
    "or the last rep looks nothing like the first). "
    "2=Subpar (visible drift over the set: the bar drifts further out, the back rounds "
    "a little more, or the lockout gets slower rep after rep). "
    "3=Good (the set holds together: the last rep looks like the first - same setup, "
    "same bar path, same lockout - with at most a slight decay on the final rep). "
    "In the feedback, NAME THE REPS you are talking about, e.g. 'it starts to break "
    "down between rep 5 and rep 8'."
)

# Consigne portee par le champ `reps` de chaque schema d'analyse.
REPS_RUBRIC = (
    "One entry per repetition performed in the video, in chronological order, "
    "starting at rep_index 1. Score EVERY criterion for EVERY rep, against the "
    "rubric of the field of the same name further down in this schema. If the "
    "lifter performs a single rep, return exactly one entry. Judge each rep on its "
    "own merits: a rep that is worse than the one before it must score lower."
)


class SquatRep(BaseModel):
    """Une repetition de squat. Memes criteres que la synthese, notes rep par rep."""

    rep_index: int = Field(description="1 for the first rep of the set, 2 for the second, and so on. Never repeat an index.")
    depth: RepCriterion
    bar_path: RepCriterion
    knee_stability: RepCriterion
    core_bracing: RepCriterion
    descent_initiation: RepCriterion
    descent_control: RepCriterion


class AnalyzeSquat(BaseModel):
    reps: list[SquatRep] = Field(description=REPS_RUBRIC)
    depth: SetCriterion = Field(description="1=Poor (quarter squat). 2=Subpar (clearly above parallel). 3=Good (hip crease at or below the top of the knee).")
    bar_path: SetCriterion = Field(description="1=Poor (drifts forward significantly, turning into a good-morning). 2=Subpar (visible forward drift out of the hole). 3=Good (straight line over mid-foot; a few centimetres of wander is still a 3).")
    knee_stability: SetCriterion = Field(description="1=Poor (severe valgus/caving inward). 2=Subpar (knees cave slightly under load, then recover). 3=Good (knees tracking over the toes throughout, with at most minor wavering).")
    core_bracing: SetCriterion = Field(description="1=Poor (chest collapses, upper/lower back rounds). 2=Subpar (some chest drop or rounding out of the hole). 3=Good (proud chest, neutral spine holding its shape; a slight forward lean out of the hole is still a 3).")
    descent_initiation: SetCriterion = Field(description="1=Poor (hinging at hips only first, or knees only). 2=Subpar (slight mistiming between hips and knees). 3=Good (breaking at hips and knees simultaneously).")
    descent_control: SetCriterion = Field(description="1=Poor (dive-bombing/free-fall). 2=Subpar (the descent gets fast in the bottom third). 3=Good (smooth, controlled eccentric).")

    set_consistency: EvaluationCriteria = Field(description=SET_CONSISTENCY_RUBRIC)


class BenchRep(BaseModel):
    """Une repetition de developpe couche. Memes criteres que la synthese."""

    rep_index: int = Field(description="1 for the first rep of the set, 2 for the second, and so on. Never repeat an index.")
    setup_arch: RepCriterion
    leg_drive: RepCriterion
    bar_path: RepCriterion
    touch_point: RepCriterion
    elbow_stability: RepCriterion
    chest_pause: RepCriterion


class AnalyzeBench(BaseModel):
    reps: list[BenchRep] = Field(description=REPS_RUBRIC)
    setup_arch: SetCriterion = Field(description="1=Poor (completely flat back, loose shoulders). 2=Subpar (arch and retraction are set up but lost during the press). 3=Good (scapula retracted and the arch held throughout; a modest arch that stays tight is still a 3).")
    leg_drive: SetCriterion = Field(description="1=Poor (butt lifts off the bench, or legs are completely loose). 2=Subpar (legs are tense but the drive fades, feet shifting mid-set). 3=Good (constant tension pushing the body towards the head).")
    bar_path: SetCriterion = Field(description="1=Poor (guillotine straight down to neck, or straight up). 2=Subpar (the path drifts towards the face or towards the belly). 3=Good (J-curve back over the shoulders; a nearly vertical but consistent path is still a 3).")
    touch_point: SetCriterion = Field(description="1=Poor (touching neck, collarbone, or belly). 2=Subpar (touching high on the chest, or at a different spot each rep). 3=Good (touching the lower chest/sternum area).")
    elbow_stability: SetCriterion = Field(description="1=Poor (elbows extremely flared at 90 degrees or heavily tucked). 2=Subpar (elbows flare out as the bar leaves the chest). 3=Good (stacked under the bar at roughly 45-60 degrees and holding that angle).")
    chest_pause: SetCriterion = Field(description="1=Poor (heaving/bouncing violently off chest). 2=Subpar (brief touch-and-go, no real stop). 3=Good (visible, dead stop pause on the chest).")

    set_consistency: EvaluationCriteria = Field(description=SET_CONSISTENCY_RUBRIC)


class ConventionalDeadliftRep(BaseModel):
    """Une repetition de souleve de terre conventionnel. Memes criteres que la synthese."""

    rep_index: int = Field(description="1 for the first rep of the set, 2 for the second, and so on. Never repeat an index.")
    starting_position: RepCriterion
    slack_pull_and_lat_engagement: RepCriterion
    leg_drive_activation: RepCriterion
    hip_hinge_mechanics: RepCriterion
    core_bracing_and_spine_neutrality: RepCriterion
    bar_path_and_proximity: RepCriterion
    lockout_execution: RepCriterion
    eccentric_control_and_descent: RepCriterion

    # Renseigne uniquement quand le prompt fournit des repetitions candidates decoupees
    # par la pose (deadlift). La pose voit le corps, pas la barre : se redresser apres
    # avoir repose la barre produit exactement le meme mouvement qu'une repetition, et
    # seul le modele peut trancher. Le backend retire les entrees a `false`.
    # Champ dedie et non "NA" : "NA" repond deja a "est-ce que je VOIS ce critere", et
    # confondre les deux supprimerait une vraie rep filmee sous un mauvais angle.
    bar_left_floor: bool = Field(
        default=True,
        description="true if the bar left the floor and was lifted to lockout in this "
                    "segment: this is a real repetition. false if the bar stayed on the "
                    "floor, or was already down and the athlete simply stood back up: "
                    "that is NOT a repetition and the entry will be discarded.")



class AnalyzeConventionalDeadlift(BaseModel):
    reps: list[ConventionalDeadliftRep] = Field(description=REPS_RUBRIC)
    starting_position: SetCriterion = Field(
        description="Evaluates setup before pull. "
                    "1=Poor (Bar far from mid-foot, hips extremely high/low, shoulders completely misaligned). "
                    "2=Subpar (Bar slightly off mid-foot, hips too low like a squat, or shoulders slightly behind bar). "
                    "3=Good (Bar over mid-foot with the shins close to it, hips between knees and shoulders, shoulders at or just ahead of the bar, back flat and set before the bar moves. One of these slightly off is still a 3.)"
    )
    slack_pull_and_lat_engagement: SetCriterion = Field(
        description="Evaluates pre-tension. "
                    "1=Poor (Complete 'grip and rip', zero tension before lift, loose lats, rounded shoulders). "
                    "2=Subpar (Attempted tension but lost before liftoff, soft elbows, lats barely engaged). "
                    "3=Good (The arms pull taut and the slack comes out before the bar leaves the floor, shoulders pulled down. A slight softening of the upper back during the pull is still a 3.)"
    )
    leg_drive_activation: SetCriterion = Field(
        description="Evaluates quad recruitment off the floor. "
                    "1=Poor (Hips shoot up immediately, lifting entirely with the back/stiff-leg pull). "
                    "2=Subpar (Noticeable early hip rise, minimal quad recruitment, back takes over early). "
                    "3=Good (The torso angle is held through the first third of the pull, hips and shoulders rising together. Hips rising slightly ahead without the torso collapsing forward is still a 3.)"
    )
    hip_hinge_mechanics: SetCriterion = Field(
        description="Evaluates posterior chain utilization. "
                    "1=Poor (Squatting the weight up, zero tension in hamstrings/glutes). "
                    "2=Subpar (Poor hinge, knees translate too far forward, relying too much on quads or lower back). "
                    "3=Good (Hips and knees extend together, the bar rising in one continuous motion. A brief mistiming around knee height is still a 3.)"
    )
    core_bracing_and_spine_neutrality: SetCriterion = Field(
        description="Evaluates spine integrity. "
                    "1=Poor (The lower back is visibly rounded under load, or rounds further during the pull.) "
                    "2=Subpar (Noticeable lumbar flexion appears during the pull.) "
                    "3=Good (The back holds the same shape at setup, at knee height and at lockout - no flexion added under load. Upper-back rounding that is stable and unchanging is still a 3.)"
    )
    bar_path_and_proximity: SetCriterion = Field(
        description="Evaluates bar trajectory. "
                    "1=Poor (Bar drifts significantly away from shins/thighs, causing forward balance loss). "
                    "2=Subpar (Bar loses contact with legs off the floor or loops forward around the knees). "
                    "3=Good (The bar stays against or within a few centimetres of the legs the whole way up, with no forward loop around the knees. A brief loss of contact around the knee is still a 3.)"
    )
    lockout_execution: SetCriterion = Field(
        description="Evaluates completion of the lift. "
                    "1=Poor (Fails to lockout, hitched rep, soft knees, or extreme dangerous lumbar hyperextension). "
                    "2=Subpar (Slow/stuttering lockout, slight hyperextension, or slightly soft hips/knees at the top). "
                    "3=Good (Hips and knees reach full extension together, the lifter standing tall with the bar against the thighs. A brief stall at the top or a slight lean back is still a 3.)"
    )
    eccentric_control_and_descent: SetCriterion = Field(
        description="Evaluates lowering of the bar. If each rep is reset on the floor, only a dropped or uncontrolled bar is a fault: a deliberate fast but accompanied lowering is not. If the reps are touch-and-go, judge the transitions between reps. "
                    "1=Poor (Completely dropping the bar, crashing, or bouncing heavily on knees). "
                    "2=Subpar (Uncontrolled descent, bending knees too early causing the bar to travel forward). "
                    "3=Good (The bar is lowered under control with the hips travelling back first, the knees bending once the bar has passed them. Knees bending a little early, or a quick last portion, is still a 3.)"
    )


    set_consistency: EvaluationCriteria = Field(description=SET_CONSISTENCY_RUBRIC)

    # Le persona est une CONCLUSION, pas une premisse : la sortie structuree est
    # generee dans l'ordre des champs, donc le declarer en tete revenait a choisir
    # l'archetype avant d'avoir analyse le moindre critere, puis a noter en
    # coherence avec l'etiquette deja posee. Mesure a 4/48 dans l'ensemble accepte
    # par l'humain, avec "The Crane" 15 fois sur 48. Garder ce bloc en DERNIER.
    # L'ordre d'affichage du front est independant de l'ordre de generation.
    lifter_persona: ConventionnalDeadliftPersona = Field(description="""Classify the lifter into one of the specific archetypes based on their dominant trait or flaw:
    - The Grip & Rip: Lacks isometric contraction of the latissimus dorsi and posterior chain prior to concentric initiation. Sudden jerk pulling lifter out of optimal leverage.
    - The Crane: Premature knee extension without concurrent hip extension. Upper body is forced to complete a stiff-legged hinge.
    - The Squatter: Attempts a knee-dominant setup for a hip-hinge movement. Pelvis too low, pushing tibia forward and knees over the bar.
    - The Fishing Rod: Failure to maintain intra-abdominal pressure and isometric rigidity in spinal erectors. Spine is pulled into active flexion.
    - The Over-Extender: Excessive lumbar hyperextension at the terminal phase instead of completing the lift via hip extension (gluteal contraction).
    - The Hitcher: Breakdown of concentric momentum. Lifter re-flexes knees and rests barbell on distal quadriceps to create an artificial shelf.
    - The Pendulum: Failure to depress scapulae. Bar drifts anteriorly away from shins, increasing the moment arm exponentially.
    - The T-Rex: Introduces active elbow flexion. Elbows are slightly bent, transferring immense load directly into the distal biceps tendon.
    - The Kneecapper: Initiates descent with knee flexion instead of hip flexion. Patellae translate forward directly into the barbell's vertical path.
    - The Soft-Lock: Failure to achieve terminal extension of hip and knee joints. Glutes and quads do not reach peak concentric contraction.
    - The Shrugger: Attempts to finish the lift by elevating the scapulae with the upper trapezius instead of completing hip extension. The shrug adds no height to the bar and abandons the depressed-lat position that keeps it close to the body.
    """)
    persona_justification: str = Field(description="A short, fun explanation of why this persona was assigned to the lifter.")


class SumoDeadliftRep(BaseModel):
    """Une repetition de souleve de terre sumo. Memes criteres que la synthese."""

    rep_index: int = Field(description="1 for the first rep of the set, 2 for the second, and so on. Never repeat an index.")
    starting_position: RepCriterion
    slack_pull_and_wedge: RepCriterion
    leg_drive_and_floor_spread: RepCriterion
    hip_opening_and_knee_tracking: RepCriterion
    core_bracing_and_spine_neutrality: RepCriterion
    bar_path_and_proximity: RepCriterion
    lockout_execution: RepCriterion
    eccentric_control_and_descent: RepCriterion

    # Renseigne uniquement quand le prompt fournit des repetitions candidates decoupees
    # par la pose (deadlift). La pose voit le corps, pas la barre : se redresser apres
    # avoir repose la barre produit exactement le meme mouvement qu'une repetition, et
    # seul le modele peut trancher. Le backend retire les entrees a `false`.
    # Champ dedie et non "NA" : "NA" repond deja a "est-ce que je VOIS ce critere", et
    # confondre les deux supprimerait une vraie rep filmee sous un mauvais angle.
    bar_left_floor: bool = Field(
        default=True,
        description="true if the bar left the floor and was lifted to lockout in this "
                    "segment: this is a real repetition. false if the bar stayed on the "
                    "floor, or was already down and the athlete simply stood back up: "
                    "that is NOT a repetition and the entry will be discarded.")



class AnalyzeSumoDeadlift(BaseModel):
    reps: list[SumoDeadliftRep] = Field(description=REPS_RUBRIC)
    starting_position: SetCriterion = Field(
        description="Evaluates sumo setup. "
                    "1=Poor (Stance completely mismatched to mobility, toes pointing forward, hips way too high or low, shins not vertical). "
                    "2=Subpar (Shins slightly angled forward, hips slightly too low, or shoulders positioned behind the barbell). "
                    "3=Good (Wide stance, toes flared, shins vertical or nearly so, shoulders stacked over the bar, hips at a solid height. One of these slightly off is still a 3.)"
    )
    slack_pull_and_wedge: SetCriterion = Field(
        description="Evaluates pre-tension and the 'Sumo Wedge'. "
                    "1=Poor (Complete 'grip and rip', zero wedge, hips far away from the bar, totally loose). "
                    "2=Subpar (Attempted to wedge but lost tension instantly, hips shift back before the bar leaves the floor). "
                    "3=Good (Visible slack pull and a solid wedge bringing the hips close to the bar, with full-body tension before the bar moves. A wedge that softens slightly during the pull is still a 3.)"
    )
    leg_drive_and_floor_spread: SetCriterion = Field(
        description="Evaluates quad recruitment and lateral force. "
                    "1=Poor (Hips shoot straight up, lifting entirely with the lower back, zero lateral push). "
                    "2=Subpar (Noticeable early hip rise, weak quad drive, relying heavily on the erectors). "
                    "3=Good (Solid leg drive actively 'spreading the floor' laterally, the torso staying upright off the floor. A slight early hip rise without the torso pitching forward is still a 3.)"
    )
    hip_opening_and_knee_tracking: SetCriterion = Field(
        description="Evaluates frontal plane mechanics (hip abduction). "
                    "1=Poor (Severe dynamic knee valgus / knees violently cave inward off the floor). "
                    "2=Subpar (Noticeable knee cave during the middle of the pull, struggling to keep hips open). "
                    "3=Good (Hips stay open and the knees track outward over the flared toes throughout, with at most minor wavering)."
    )
    core_bracing_and_spine_neutrality: SetCriterion = Field(
        description="Evaluates spine integrity. "
                    "1=Poor (Complete loss of bracing, severe forward pitch, lumbar rounding). "
                    "2=Subpar (Weak brace, noticeable upper/mid back rounding causing the chest to collapse). "
                    "3=Good (Solid brace, neutral spine and a proud chest held from the floor to lockout. Upper-back rounding that is stable and unchanging is still a 3.)"
    )
    bar_path_and_proximity: SetCriterion = Field(
        description="Evaluates bar trajectory. "
                    "1=Poor (Bar drifts significantly forward away from the legs, pulling the lifter onto their toes). "
                    "2=Subpar (Bar loses contact with the shins/thighs off the floor, creating a slight pendulum effect). "
                    "3=Good (Vertical path with light contact along the inner calves and thighs. Contact that is intermittent rather than continuous is still a 3.)"
    )
    lockout_execution: SetCriterion = Field(
        description="Evaluates completion of the lift. "
                    "1=Poor (Fails to lockout, hitched rep, leaning dangerously backward, or extreme soft knees). "
                    "2=Subpar (Slow lockout, slight hitching, or knees/hips not fully extending simultaneously). "
                    "3=Good (Knees and hips lock out together, upright and neutral, without leaning back. A lockout that is solid but not forceful is still a 3.)"
    )
    eccentric_control_and_descent: SetCriterion = Field(
        description="Evaluates lowering of the bar. "
                    "1=Poor (Completely dropping the bar, crashing heavily, or dumping it onto the knees). "
                    "2=Subpar (Uncontrolled descent, bending knees too early causing the bar to hit the kneecaps). "
                    "3=Good (Controlled lowering, hips staying open, knees bending as the bar passes them. Slight knee interference on the way down is still a 3.)"
    )


    set_consistency: EvaluationCriteria = Field(description=SET_CONSISTENCY_RUBRIC)

    # Le persona est une CONCLUSION, pas une premisse : la sortie structuree est
    # generee dans l'ordre des champs, donc le declarer en tete revenait a choisir
    # l'archetype avant d'avoir analyse le moindre critere, puis a noter en
    # coherence avec l'etiquette deja posee. Mesure a 4/48 dans l'ensemble accepte
    # par l'humain, avec "The Crane" 15 fois sur 48. Garder ce bloc en DERNIER.
    # L'ordre d'affichage du front est independant de l'ordre de generation.
    lifter_persona: SumoDeadliftPersona = Field(description="""Classify the lifter into one of the specific archetypes based on their dominant trait or flaw:
    - The Grip & Rip: Lacks isometric contraction prior to concentric initiation. Sudden jerk pulling lifter out of optimal leverage.
    - The Crane: Premature knee extension. Hips shoot up immediately, turning it into a stiff-legged pull.
    - The Squatter: Pelvis too low, pushing tibia forward. Fails to build tension in the hips.
    - The Fishing Rod: Failure to maintain intra-abdominal pressure. Spine is pulled into active flexion.
    - The Over-Extender: Excessive lumbar hyperextension at lockout instead of finishing with glute contraction.
    - The Hitcher: Lifter re-flexes knees and rests barbell on distal quadriceps to artificially finish the lift.
    - The Pendulum: Bar drifts anteriorly away from the legs, increasing the moment arm and taxing the lower back.
    - The T-Rex: Introduces active elbow flexion. Elbows are slightly bent, risking a bicep tear.
    - The Kneecapper: Initiates descent with knee flexion instead of hip flexion. Barbell crashes into the knees.
    - The Soft-Lock: Fails to achieve terminal extension. Knees or hips remain visibly soft at the top.
    - The X-Wing: Severe dynamic knee valgus. Hips lack external rotation strength, causing knees to collapse inward instantly off the floor.
    - The Helicopter: Asymmetrical lockout or uneven tension causing the barbell to rotate horizontally (windmill effect) during the pull.
    - The Heel Tipper: Center of gravity shifts entirely behind the heels due to an overly vertical pull, causing backward balance loss at lockout.
    - The Shrugger: Attempts to finish the lift by elevating the scapulae with the upper trapezius instead of completing hip extension. The shrug adds no height to the bar and abandons the depressed-lat position that keeps it close to the body.
    """)
    persona_justification: str = Field(description="A short, fun explanation of why this persona was assigned to the lifter.")


schema_mapping = {
    "squat": AnalyzeSquat,
    "bench press": AnalyzeBench,
    "conventional deadlift": AnalyzeConventionalDeadlift,
    "sumo deadlift": AnalyzeSumoDeadlift
}

# --- Introspection et garde-fou ---------------------------------------------
# Les noms de criteres sont ecrits deux fois par mouvement : une fois sur le
# bloc "une rep", une fois sur le bloc de synthese qui porte le bareme. Une
# faute de frappe entre les deux ne casserait rien a l'execution, elle
# produirait juste une colonne vide dans l'histogramme et un critere sans note.
# On la fait echouer a l'import, la ou elle se voit.

def criteres_de_synthese(schema) -> list[str]:
    """Noms des criteres notes d'un schema d'analyse, dans l'ordre.

    `set_consistency` n'en fait pas partie : c'est un `EvaluationCriteria`, note
    directement par le modele, pas agrege depuis les reps.
    """
    return [n for n, f in schema.model_fields.items() if f.annotation is SetCriterion]


def modele_de_rep(schema):
    """Le modele "une rep" associe a un schema d'analyse."""
    champ = schema.model_fields.get("reps")
    return get_args(champ.annotation)[0] if champ is not None else None


for _mouvement, _schema in schema_mapping.items():
    _attendus = criteres_de_synthese(_schema)
    _rep = modele_de_rep(_schema)
    _presents = [n for n, f in _rep.model_fields.items() if f.annotation is RepCriterion]
    if _presents != _attendus:
        raise RuntimeError(
            f"{_mouvement} : les criteres de {_rep.__name__} ne correspondent pas a ceux "
            f"de {_schema.__name__} ({_presents} != {_attendus})"
        )
