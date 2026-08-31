from enum import Enum

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


class CriteriaScore(str, Enum):
    """Score values the model may emit.

    A str Enum rather than an int with ge/le: the enum is enforced by
    constrained decoding, so "NA" is a value the model can actually reach and
    3.5 / 0 / 7 are values it cannot.
    """

    NA = "NA"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"


def numeric_score(value) -> int | None:
    """Score as an int, or None when the criterion was not assessable."""
    if isinstance(value, CriteriaScore):
        value = value.value
    if isinstance(value, bool):  # bool is an int subclass, reject it explicitly
        return None
    if isinstance(value, int):
        return value if 1 <= value <= 4 else None
    if isinstance(value, str) and value.isdigit():
        n = int(value)
        return n if 1 <= n <= 4 else None
    return None


class EvaluationCriteria(BaseModel):
    visual_analysis: str = Field(description="Describe strictly what you see physically in the video for this specific criteria (e.g., 'the lower back is visibly rounding', 'the bar drifts away from shins'). Do not give a score yet.")
    score: CriteriaScore = Field(description="'1' to '4' (1=Danger/Terrible, 2=Poor/Flawed, 3=Average/Acceptable, 4=Optimal/Perfect), or 'NA' when the camera angle, framing, lighting or video quality makes this specific criterion impossible to assess (e.g. the feet are out of frame, so bar-over-midfoot cannot be judged). 'NA' is for what you cannot SEE, never for what you saw and disliked: a flaw you can see is a low score, not 'NA'.")
    feedback: str = Field(description="Detailed advice if the score is 1, 2, or 3. A single short, punchy sentence providing extreme praise if the score is 4. If the score is 'NA', state exactly what is not visible and how to reframe the next video.")

class AnalyzeSquat(BaseModel):
    depth: EvaluationCriteria = Field(description="1-2=Poor (quarter/half squat). 3=Average (parallel). 4=Optimal (hip crease clearly below the top of the knee).")
    bar_path: EvaluationCriteria = Field(description="1-2=Poor (drifts forward significantly). 3=Average. 4=Optimal (perfectly straight line over mid-foot).")
    knee_stability: EvaluationCriteria = Field(description="1-2=Poor (severe valgus/caving inward). 3=Average. 4=Optimal (knees tracking perfectly over toes).")
    core_bracing: EvaluationCriteria = Field(description="1-2=Poor (chest collapses, upper/lower back rounds). 3=Average. 4=Optimal (proud chest, rigid neutral spine).")
    descent_initiation: EvaluationCriteria = Field(description="1-2=Poor (hinging at hips only first, or knees only). 3=Average. 4=Optimal (breaking at hips and knees simultaneously).")
    descent_control: EvaluationCriteria = Field(description="1-2=Poor (dive-bombing/free-fall). 3=Average. 4=Optimal (smooth, controlled eccentric).")

class AnalyzeBench(BaseModel):
    setup_arch: EvaluationCriteria = Field(description="1-2=Poor (completely flat back, loose shoulders). 3=Average. 4=Optimal (scapula heavily retracted, tight arch).")
    leg_drive: EvaluationCriteria = Field(description="1-2=Poor (butt lifts off the bench, or legs are completely loose). 3=Average. 4=Optimal (constant tension pushing the body towards the head).")
    bar_path: EvaluationCriteria = Field(description="1-2=Poor (guillotine straight down to neck, or straight up). 3=Average. 4=Optimal (proper J-curve back over the shoulders).")
    touch_point: EvaluationCriteria = Field(description="1-2=Poor (touching neck, collarbone, or belly). 3=Average. 4=Optimal (touching lower chest/sternum area).")
    elbow_stability: EvaluationCriteria = Field(description="1-2=Poor (elbows extremely flared at 90 degrees or heavily tucked). 3=Average. 4=Optimal (stacked under the bar at ~45-60 degrees).")
    chest_pause: EvaluationCriteria = Field(description="1-2=Poor (heaving/bouncing violently off chest). 3=Average. 4=Optimal (visible, dead stop pause on the chest).")


class AnalyzeConventionalDeadlift(BaseModel):
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
    """)
    persona_justification: str = Field(description="A short, fun explanation of why this persona was assigned to the lifter.")

    starting_position: EvaluationCriteria = Field(
        description="Evaluates setup before pull. "
                    "1=Poor (Bar far from mid-foot, hips extremely high/low, shoulders completely misaligned). "
                    "2=Subpar (Bar slightly off mid-foot, hips too low like a squat, or shoulders slightly behind bar). "
                    "3=Good (Bar over mid-foot, hips at acceptable height, minor deviation in scapula position). "
                    "4=Optimal (Bar exactly over mid-foot, shins touching bar, hips at optimal height, scapula directly over bar)."
    )
    slack_pull_and_lat_engagement: EvaluationCriteria = Field(
        description="Evaluates pre-tension. "
                    "1=Poor (Complete 'grip and rip', zero tension before lift, loose lats, rounded shoulders). "
                    "2=Subpar (Attempted tension but lost before liftoff, soft elbows, lats barely engaged). "
                    "3=Good (Noticeable tension and slack pull, but slight loss of upper back tightness during initial pull). "
                    "4=Optimal ('Bending the bar', audible slack pull, lats aggressively engaged and locked throughout)."
    )
    leg_drive_activation: EvaluationCriteria = Field(
        description="Evaluates quad recruitment off the floor. "
                    "1=Poor (Hips shoot up immediately, lifting entirely with the back/stiff-leg pull). "
                    "2=Subpar (Noticeable early hip rise, minimal quad recruitment, back takes over early). "
                    "3=Good (Solid leg drive, torso angle remains mostly constant with only very slight early hip movement). "
                    "4=Optimal (Perfect leg drive, torso angle remains absolutely constant off the floor, pushing the floor away)."
    )
    hip_hinge_mechanics: EvaluationCriteria = Field(
        description="Evaluates posterior chain utilization. "
                    "1=Poor (Squatting the weight up, zero tension in hamstrings/glutes). "
                    "2=Subpar (Poor hinge, knees translate too far forward, relying too much on quads or lower back). "
                    "3=Good (Solid posterior chain tension, but slight mistiming between knee and hip extension). "
                    "4=Optimal (Excellent hamstring/glute tension, perfectly synchronized knee and hip extension)."
    )
    core_bracing_and_spine_neutrality: EvaluationCriteria = Field(
        description="Evaluates spine integrity. "
                    "1=Poor (Complete loss of bracing, severe lumbar and thoracic rounding). "
                    "2=Subpar (Weak brace, noticeable lumbar flexion/rounding during the pull). "
                    "3=Good (Solid brace, neutral lumbar spine, slight but safe and acceptable thoracic rounding). "
                    "4=Optimal (Massive 360-degree brace, perfectly rigid and neutral spine from cervical to lumbar throughout)."
    )
    bar_path_and_proximity: EvaluationCriteria = Field(
        description="Evaluates bar trajectory. "
                    "1=Poor (Bar drifts significantly away from shins/thighs, causing forward balance loss). "
                    "2=Subpar (Bar loses contact with legs off the floor or loops forward around the knees). "
                    "3=Good (Mostly straight vertical path, but intermittent or very light contact with legs). "
                    "4=Optimal (Perfectly straight vertical path, continuous light contact dragging up the shins and thighs)."
    )
    lockout_execution: EvaluationCriteria = Field(
        description="Evaluates completion of the lift. "
                    "1=Poor (Fails to lockout, hitched rep, soft knees, or extreme dangerous lumbar hyperextension). "
                    "2=Subpar (Slow/stuttering lockout, slight hyperextension, or slightly soft hips/knees at the top). "
                    "3=Good (Solid lockout, but slightly lacking an aggressive glute squeeze or perfectly tall posture). "
                    "4=Optimal (Crisp forceful glute squeeze, perfectly tall posture, knees/hips locked simultaneously without leaning back)."
    )
    eccentric_control_and_descent: EvaluationCriteria = Field(
        description="Evaluates lowering of the bar. "
                    "1=Poor (Completely dropping the bar, crashing, or bouncing heavily on knees). "
                    "2=Subpar (Uncontrolled descent, bending knees too early causing the bar to travel forward). "
                    "3=Good (Controlled descent but slight knee interference or slightly rapid drop). "
                    "4=Optimal (Perfectly controlled hinge lowering, hips travel back first, knees bend only after bar passes them)."
    )

class AnalyzeSumoDeadlift(BaseModel):
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
    """)
    persona_justification: str = Field(description="A short, fun explanation of why this persona was assigned to the lifter.")

    starting_position: EvaluationCriteria = Field(
        description="Evaluates sumo setup. "
                    "1=Poor (Stance completely mismatched to mobility, toes pointing forward, hips way too high or low, shins not vertical). "
                    "2=Subpar (Shins slightly angled forward, hips slightly too low, or shoulders positioned behind the barbell). "
                    "3=Good (Wide stance, toes flared, shins mostly vertical, hips at a solid height). "
                    "4=Optimal (Perfect wide stance, toes perfectly flared, shins perfectly vertical, shoulders directly stacked over the bar)."
    )
    slack_pull_and_wedge: EvaluationCriteria = Field(
        description="Evaluates pre-tension and the 'Sumo Wedge'. "
                    "1=Poor (Complete 'grip and rip', zero wedge, hips far away from the bar, totally loose). "
                    "2=Subpar (Attempted to wedge but lost tension instantly, hips shift back before the bar leaves the floor). "
                    "3=Good (Noticeable slack pull and solid wedge, bringing hips close to the bar). "
                    "4=Optimal (Aggressive audible slack pull, hips wedged incredibly close to the barbell, immense full-body pre-tension)."
    )
    leg_drive_and_floor_spread: EvaluationCriteria = Field(
        description="Evaluates quad recruitment and lateral force. "
                    "1=Poor (Hips shoot straight up, lifting entirely with the lower back, zero lateral push). "
                    "2=Subpar (Noticeable early hip rise, weak quad drive, relying heavily on the erectors). "
                    "3=Good (Solid leg drive, actively 'spreading the floor', torso angle remains mostly upright). "
                    "4=Optimal (Flawless leg drive, aggressively spreading the floor laterally, torso remains perfectly upright off the floor)."
    )
    hip_opening_and_knee_tracking: EvaluationCriteria = Field(
        description="Evaluates frontal plane mechanics (hip abduction). "
                    "1=Poor (Severe dynamic knee valgus / knees violently cave inward off the floor). "
                    "2=Subpar (Noticeable knee cave during the middle of the pull, struggling to keep hips open). "
                    "3=Good (Hips stay relatively open, knees mostly track over toes with only minor wavering). "
                    "4=Optimal (Hips impeccably open, knees rigidly locked outward tracking perfectly over flared toes throughout)."
    )
    core_bracing_and_spine_neutrality: EvaluationCriteria = Field(
        description="Evaluates spine integrity. "
                    "1=Poor (Complete loss of bracing, severe forward pitch, lumbar rounding). "
                    "2=Subpar (Weak brace, noticeable upper/mid back rounding causing the chest to collapse). "
                    "3=Good (Solid brace, neutral lumbar spine, maintaining a relatively proud chest). "
                    "4=Optimal (Massive 360-degree brace, perfectly rigid, upright, and neutral spine from cervical to lumbar)."
    )
    bar_path_and_proximity: EvaluationCriteria = Field(
        description="Evaluates bar trajectory. "
                    "1=Poor (Bar drifts significantly forward away from the legs, pulling the lifter onto their toes). "
                    "2=Subpar (Bar loses contact with the shins/thighs off the floor, creating a slight pendulum effect). "
                    "3=Good (Mostly straight vertical path, very light or intermittent contact with the inner legs). "
                    "4=Optimal (Perfectly strictly vertical path, continuous light contact dragging up the inner calves and thighs)."
    )
    lockout_execution: EvaluationCriteria = Field(
        description="Evaluates completion of the lift. "
                    "1=Poor (Fails to lockout, hitched rep, leaning dangerously backward, or extreme soft knees). "
                    "2=Subpar (Slow lockout, slight hitching, or knees/hips not fully extending simultaneously). "
                    "3=Good (Solid lockout, but lacks a forceful glute squeeze or slightly soft knees). "
                    "4=Optimal (Crisp, aggressive simultaneous knee and hip lockout, perfectly upright neutral posture without leaning back)."
    )
    eccentric_control_and_descent: EvaluationCriteria = Field(
        description="Evaluates lowering of the bar. "
                    "1=Poor (Completely dropping the bar, crashing heavily, or dumping it onto the knees). "
                    "2=Subpar (Uncontrolled descent, bending knees too early causing the bar to hit the kneecaps). "
                    "3=Good (Controlled descent but slight knee interference on the way down). "
                    "4=Optimal (Perfectly controlled lowering, hips stay open, knees bend only after the bar passes them)."
    )

schema_mapping = {
    "squat": AnalyzeSquat,
    "bench press": AnalyzeBench,
    "conventional deadlift": AnalyzeConventionalDeadlift,
    "sumo deadlift": AnalyzeSumoDeadlift
}