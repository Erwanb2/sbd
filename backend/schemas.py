from enum import Enum
from pydantic import BaseModel, Field

class MovementType(str, Enum):
    squat = "squat"
    bench = "bench"
    sumo_deadlift = "Sumo deadlift"
    conventional_deadlift = "Conventional deadlift"
    video_inexploitable = "video_inexploitable"

# --- ÉTAPE 1 : CLASSIFICATION DE LA VIDÉO ---
class VideoClassification(BaseModel):
    mouvement_detecte: MovementType = Field(description="The powerlifting movement detected in the video.")

# --- ÉTAPE 2 : PERSONAS POUR LE DEADLIFT ---
class DeadliftPersona(str, Enum):
    THE_TECHNICIAN = "The Technician"
    THE_GRIP_AND_RIP = "The Grip & Rip"
    THE_CRANE = "The Crane"
    THE_SQUATTER = "The Squatter"
    THE_FISHING_ROD = "The Fishing Rod"
    THE_OVER_EXTENDER = "The Over-Extender"
    THE_HITCHER = "The Hitcher"

# --- MODÈLE DE BASE DE NOTATION (ÉCHELLE SUR 4 POUR LE SCALE STRETCHING) ---
class EvaluationCriteria(BaseModel):
    visual_analysis: str = Field(description="Describe strictly what you see physically in the video for this specific criteria (e.g., 'the lower back is visibly rounding', 'the bar drifts away from shins'). Do not give a score yet.")
    # Le fameux hack sur 4 : 1=Danger, 2=Poor, 3=Average, 4=Optimal
    score: int = Field(description="Score from 1 to 4. 1=Danger/Terrible, 2=Poor/Flawed, 3=Average/Acceptable, 4=Optimal/Perfect.", ge=1, le=4)
    feedback: str = Field(description="Detailed advice if the score is 1, 2, or 3. A single short, punchy sentence providing extreme praise if the score is 4.")

# --- SQUAT ---
class AnalyzeSquat(BaseModel):
    depth: EvaluationCriteria = Field(description="1-2=Poor (quarter/half squat). 3=Average (parallel). 4=Optimal (hip crease clearly below the top of the knee).")
    bar_path: EvaluationCriteria = Field(description="1-2=Poor (drifts forward significantly). 3=Average. 4=Optimal (perfectly straight line over mid-foot).")
    knee_stability: EvaluationCriteria = Field(description="1-2=Poor (severe valgus/caving inward). 3=Average. 4=Optimal (knees tracking perfectly over toes).")
    core_bracing: EvaluationCriteria = Field(description="1-2=Poor (chest collapses, upper/lower back rounds). 3=Average. 4=Optimal (proud chest, rigid neutral spine).")
    descent_initiation: EvaluationCriteria = Field(description="1-2=Poor (hinging at hips only first, or knees only). 3=Average. 4=Optimal (breaking at hips and knees simultaneously).")
    descent_control: EvaluationCriteria = Field(description="1-2=Poor (dive-bombing/free-fall). 3=Average. 4=Optimal (smooth, controlled eccentric).")

# --- BENCH PRESS ---
class AnalyzeBench(BaseModel):
    setup_arch: EvaluationCriteria = Field(description="1-2=Poor (completely flat back, loose shoulders). 3=Average. 4=Optimal (scapula heavily retracted, tight arch).")
    leg_drive: EvaluationCriteria = Field(description="1-2=Poor (butt lifts off the bench, or legs are completely loose). 3=Average. 4=Optimal (constant tension pushing the body towards the head).")
    bar_path: EvaluationCriteria = Field(description="1-2=Poor (guillotine straight down to neck, or straight up). 3=Average. 4=Optimal (proper J-curve back over the shoulders).")
    touch_point: EvaluationCriteria = Field(description="1-2=Poor (touching neck, collarbone, or belly). 3=Average. 4=Optimal (touching lower chest/sternum area).")
    elbow_stability: EvaluationCriteria = Field(description="1-2=Poor (elbows extremely flared at 90 degrees or heavily tucked). 3=Average. 4=Optimal (stacked under the bar at ~45-60 degrees).")
    chest_pause: EvaluationCriteria = Field(description="1-2=Poor (heaving/bouncing violently off chest). 3=Average. 4=Optimal (visible, dead stop pause on the chest).")

# --- CONVENTIONAL DEADLIFT ---
class AnalyzeConventionalDeadlift(BaseModel):
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
    # Personas spécifiques au Deadlift
    lifter_persona: DeadliftPersona = Field(description="Classify the lifter into one of the specific archetypes based on their dominant trait or flaw.")
    persona_justification: str = Field(description="A short, fun explanation of why this persona was assigned to the lifter.")

# --- SUMO DEADLIFT ---
class AnalyzeSumoDeadlift(BaseModel):
    starting_position: EvaluationCriteria = Field(description="Evaluates sumo setup. 1-2=Poor (stance too narrow, toes forward, hips too far back). 4=Optimal (wide stance, toes flared, shins vertical).")
    slack_pull_and_wedge: EvaluationCriteria = Field(description="Evaluates pre-tension. 1-2=Poor (grip and rip, no wedge). 4=Optimal (aggressive slack pull, hips wedged close to the bar).")
    leg_drive_and_floor_spread: EvaluationCriteria = Field(description="Evaluates floor drive. 1-2=Poor (hips shoot up, knees cave in). 4=Optimal ('spreading the floor' pushing outward, upright torso).")
    hip_opening_and_knee_tracking: EvaluationCriteria = Field(description="Evaluates hip abduction. 1-2=Poor (severe dynamic knee valgus). 4=Optimal (knees locked tracking directly over flared toes).")
    core_bracing_and_spine_neutrality: EvaluationCriteria = Field(description="Evaluates spine. 1-2=Poor (forward pitch, rounding). 4=Optimal (360-degree brace, rigidly upright and neutral).")
    bar_path_and_proximity: EvaluationCriteria = Field(description="Evaluates trajectory. 1-2=Poor (forward drift). 4=Optimal (strictly vertical, constant contact with inner thighs/shins).")
    lockout_execution: EvaluationCriteria = Field(description="Evaluates completion. 1-2=Poor (soft knees, hitching, leaning back). 4=Optimal (crisp simultaneous knee/hip lockout, neutral upright).")
    eccentric_control_and_descent: EvaluationCriteria = Field(description="Evaluates lowering. 1-2=Poor (drop/crash into knees). 4=Optimal (controlled return keeping hips open).")

    # Personas spécifiques au Deadlift
    lifter_persona: DeadliftPersona = Field(description="Classify the lifter into one of the specific archetypes based on their dominant trait or flaw.")
    persona_justification: str = Field(description="A short, fun explanation of why this persona was assigned to the lifter.")

# --- MAPPING POUR LE BACKEND ---
schema_mapping = {
    "squat": AnalyzeSquat,
    "bench": AnalyzeBench,
    "Conventional deadlift": AnalyzeConventionalDeadlift,
    "Sumo deadlift": AnalyzeSumoDeadlift
}