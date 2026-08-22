from enum import Enum
from pydantic import BaseModel, Field

class MovementType(str, Enum):
    squat = "squat"
    bench = "bench"
    sumo_deadlift = "Sumo deadlift"
    conventional_deadlift = "Conventional deadlift"
    video_inexploitable = "video_inexploitable"

class VideoClassification(BaseModel):
    mouvement_detecte: MovementType = Field(description="Le mouvement de force athlétique détecté dans la vidéo.")

class EvaluationCritere(BaseModel):
    note: int = Field(description="Score from 1 to 3.", ge=1, le=3)
    commentaire: str = Field(description="A single short, punchy sentence providing targeted advice if the score is 1/3 or 2/3. Shower the user with extreme praise if the score is 3/3.")
class AnalyseSquat(BaseModel):
    profondeur: EvaluationCritere = Field(description="1=Mauvais (demi-squat). 2=Moyen. 3=Bon (creux hanche sous le genou).")
    trajectoire_barre: EvaluationCritere = Field(description="1=Mauvais (part en avant). 2=Moyen. 3=Bon (au-dessus mi-pied).")
    stabilite_genoux: EvaluationCritere = Field(description="1=Mauvais (valgus). 2=Moyen. 3=Bon (alignés avec orteils).")
    gainage_tronc: EvaluationCritere = Field(description="1=Mauvais (poitrine s'effondre). 2=Moyen. 3=Bon (buste fier).")
    initiation_descente: EvaluationCritere = Field(description="1=Mauvais (bassin seul). 2=Moyen. 3=Bon (hanches/genoux ensemble).")
    rythme_controle: EvaluationCritere = Field(description="1=Mauvais (chute libre). 2=Moyen. 3=Bon (descente contrôlée).")

class AnalyseBench(BaseModel):
    setup_arches: EvaluationCritere = Field(description="1=Mauvais (dos plat). 2=Moyen. 3=Bon (omoplates resserrées).")
    leg_drive: EvaluationCritere = Field(description="1=Mauvais (fesses se lèvent). 2=Moyen. 3=Bon (tension vers la tête).")
    trajectoire_barre: EvaluationCritere = Field(description="1=Mauvais (guillotine). 2=Moyen. 3=Bon (J-curve).")
    point_contact: EvaluationCritere = Field(description="1=Mauvais (cou/ventre). 2=Moyen. 3=Bon (bas des pectoraux).")
    stabilite_coudes: EvaluationCritere = Field(description="1=Mauvais (coudes écartés). 2=Moyen. 3=Bon (coudes à 45°).")
    pause_poitrine: EvaluationCritere = Field(description="1=Mauvais (rebond violent). 2=Moyen. 3=Bon (arrêt net).")

class AnalyseConventionalDeadlift(BaseModel):
    starting_position: EvaluationCritere = Field(
        description="Evaluates the setup before the pull. "
                    "1=Poor (Bar too far forward/backward from mid-foot, shoulders behind the bar, or stance too wide/narrow). "
                    "2=Average (Minor setup flaws, slightly off-balance). "
                    "3=Optimal (Bar perfectly over mid-foot, scapula directly over the bar, armpits directly above the bar, shin touching the bar upon hinging)."
    )
    
    slack_pull_and_lat_engagement: EvaluationCritere = Field(
        description="Evaluates the vertical pre-tension and the smooth transition from setup to lift-off ('pulling the slack')"
                    "1=Poor ('Grip and rip' yanking, lats completely relaxed, bent elbows, zero initial stiffness). "
                    "2=Average (Some vertical tension created, but lats are slightly soft, or the lift-off is still a bit abrupt). "
                    "3=Optimal (Lifter wedges into position, audible/visible tension on the bar ('pulling the slack'), lats aggressively engaged ('bending the bar'), resulting in a perfectly smooth lift-off)."
    )

    leg_drive_activation: EvaluationCritere = Field(
        description="Evaluates quad recruitment off the floor and torso angle stability during the first pull. "
                    "1=Poor (Hips shoot up prematurely before the bar breaks the floor, hips rise faster than the chest turning it into a stiff-legged lower-back pull, or zero leg drive). "
                    "2=Average (Good initial leg drive, but torso angle collapses or hips rise disproportionately early as the bar passes mid-shin). "
                    "3=Optimal (Explosive 'push the floor away' quad drive; torso angle remains constant and rigid until the bar passes the knees before transitioning seamlessly into hip extension)."
    )


    hip_hinge_mechanics: EvaluationCritere = Field(
        description="Evaluates the posterior chain loading (hamstrings and glutes). "
                    "1=Poor (Squatting the deadlift: hips too low, knees pushed too far forward, zero tension in hamstrings). "
                    "2=Average (Moderate hinge, but quad-dominant setup lacking maximal posterior chain stretch). "
                    "3=Optimal (Excellent hip hinge, high tension in hamstrings and glutes, knees slightly bent but not protruding over the bar)."
    )


    core_bracing_and_spine_neutrality: EvaluationCritere = Field(
        description="Evaluates intra-abdominal pressure (Valsalva maneuver) and spine integrity under load. "
                    "1=Poor (Severe lumbar/lower back rounding under load, completely loose core, high risk of injury). "
                    "2=Average (Slight spinal flexion during the hardest part of the pull, but acceptable core brace). "
                    "3=Optimal (Massive 360-degree core brace, neutral spine rigidly locked into place from setup to lockout)."
    )


    bar_path_and_proximity: EvaluationCritere = Field(
        description="Evaluates the vertical trajectory of the bar and its closeness to the lifter's body throughout the pull. "
                    "1=Poor (Bar drifts significantly away from the shins/thighs creating a dangerous lever arm, or extreme S-curve having to navigate actively around the knees). "
                    "2=Average (Slight horizontal deviation, momentary loss of leg contact, or slight swinging of the bar). "
                    "3=Optimal (Perfectly straight vertical bar path directly over the mid-foot, maintaining light contact with shins and thighs from floor to lockout)."
    )

    lockout_execution: EvaluationCritere = Field(
        description="Evaluates the final completion of the lift at the top. "
                    "1=Poor (Soft knees, hitched rep, or extreme and dangerous hyperextension of the lower back leaning backward). "
                    "2=Average (Lift completed, but with minor flaws: incomplete glute squeeze, slightly soft knees, shrugging shoulders up, or a mild backward lean). "
                    "3=Optimal (Crisp glute squeeze, tall proud chest posture, hips and knees fully locked out without any lumbar hyperextension)."
    )

    eccentric_control_and_descent: EvaluationCritere = Field(
        description="Evaluates the lowering phase and path of the bar back to the floor. "
                    "1=Poor (Uncontrolled drop/crash, bending the knees too early causing the bar to collide with or roll around the knees, or severe lumbar flexion during the descent). "
                    "2=Average (Controlled descent, but initiates slightly with knee flexion before hip hinge, causing a slight detour around the kneecaps). "
                    "3=Optimal (Hinge-first descent pushing hips back until the bar clears the knees before bending knees, maintaining bar-to-leg proximity and full control without dropping)."
    )

class AnalyseSumoDeadlift(BaseModel):
    starting_position: EvaluationCritere = Field(
        description="Evaluates the sumo setup before the pull. "
                    "1=Poor (Stance width inappropriate, feet parallel instead of flared, arms outside knees, shins angled forward, or hips too far back/high). "
                    "2=Average (Minor setup flaws, arms slightly too wide, slight knee valgus at setup, or shins not fully perpendicular to the floor). "
                    "3=Optimal (Wide stance with feet flared 30°-45°, shins vertical and touching the bar, arms hanging strictly vertical inside the knees, hips open and close to the bar)."
    )

    slack_pull_and_wedge: EvaluationCritere = Field(
        description="Evaluates vertical slack removal and hip wedging into the bar before floor break. "
                    "1=Poor ('Grip and rip' yanking, zero hip wedge, loose lats, shoulders completely in front of the bar, elbows bent). "
                    "2=Average (Partial slack pull, but wedge is incomplete or lifter rushes the transition without full whole-body tension). "
                    "3=Optimal (Aggressive lat engagement 'bending the bar', audible slack pull, hips actively wedged forward and down close to the bar creating maximal full-body tension)."
    )

    leg_drive_and_floor_spread: EvaluationCritere = Field(
        description="Evaluates initial drive off the floor using quad/adductor engagement and 'spreading the floor'. "
                    "1=Poor (Hips shoot up prematurely before the bar breaks the floor, knees collapse inward [valgus], turning into a stiff-leg lower back pull). "
                    "2=Average (Bar breaks the floor well, but knees slightly cave in or hips rise slightly faster than the chest). "
                    "3=Optimal (Relentless 'spread the floor' drive pushing outward through the feet, knees remain tracking over toes, upright torso angle maintained rigidly until the bar passes the knees)."
    )

    hip_opening_and_knee_tracking: EvaluationCritere = Field(
        description="Evaluates hip abduction/external rotation and knee-to-toe alignment throughout the pull. "
                    "1=Poor (Severe dynamic knee valgus / caving inward, hips shooting backwards, inability to open hips). "
                    "2=Average (Acceptable hip position, but slight inward knee cave under maximal load or premature forward knee drift). "
                    "3=Optimal (Maximal hip opening, knees locked tracking directly over flared toes throughout the entire range of motion, maintaining a high vertical chest)."
    )

    core_bracing_and_spine_neutrality: EvaluationCritere = Field(
        description="Evaluates intra-abdominal pressure (Valsalva) and upright spinal rigidity. "
                    "1=Poor (Spinal flexion/rounding in lumbar or thoracic spine pitching the lifter forward, loose brace, high failure/injury risk). "
                    "2=Average (Slight upper-back soft posture under maximal load, but lumbar spine remains neutral and braced). "
                    "3=Optimal (Solid 360-degree intra-abdominal brace, completely rigid and upright neutral spine throughout the entire lift)."
    )

    bar_path_and_proximity: EvaluationCritere = Field(
        description="Evaluates vertical bar trajectory and proximity to shins and inner thighs. "
                    "1=Poor (Bar drifts away forward from shins creating excessive leverage, or tilts horizontally). "
                    "2=Average (Minor forward drift or momentary loss of contact with inner thighs). "
                    "3=Optimal (Strictly vertical bar path staying in continuous light contact with vertical shins and inner thighs from floor to lockout with zero forward drift)."
    )

    lockout_execution: EvaluationCritere = Field(
        description="Evaluates the completion of the lift at the top. "
                    "1=Poor (Soft/unlocked knees, downward motion/hitching on thighs, or excessive lumbar hyperextension leaning back). "
                    "2=Average (Lockout achieved but with minor soft knees, slight shoulder shrugging, or delayed glute engagement). "
                    "3=Optimal (Crisp simultaneous lockout of knees and hips via maximal glute/quad contraction, tall neutral upright posture without backward leaning)."
    )

    eccentric_control_and_descent: EvaluationCritere = Field(
        description="Evaluates the controlled return of the bar to the floor. "
                    "1=Poor (Complete uncontrolled drop, or bending knees forward immediately causing the bar to crash into thighs/knees). "
                    "2=Average (Controlled descent, but knees cave inward slightly or bar collides lightly with the knees on the way down). "
                    "3=Optimal (Controlled lowering keeping hips open and bar close to inner thighs/shins until touching the floor smoothly)."
    )

schema_mapping = {
    "squat": AnalyseSquat,
    "bench": AnalyseBench,
    "Conventional deadlift": AnalyseConventionalDeadlift,
    "Sumo_deadlift": AnalyseSumoDeadlift

}