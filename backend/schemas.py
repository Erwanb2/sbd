from enum import Enum
from pydantic import BaseModel, Field

# --- 1. SCHÉMAS DE CLASSIFICATION (LE "VIDEUR") ---
class MovementType(str, Enum):
    squat = "squat"
    bench = "bench"
    deadlift = "deadlift"
    video_inexploitable = "video_inexploitable"

class VideoClassification(BaseModel):
    mouvement_detecte: MovementType = Field(description="Le mouvement de force athlétique détecté dans la vidéo.")

# --- 2. SCHÉMAS D'ANALYSE (LE "COACH") ---
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

class AnalyseDeadlift(BaseModel):
    starting_position: EvaluationCritere = Field(
        description="Evaluates the setup before the pull. "
                    "1=Poor (Bar too far forward/backward from mid-foot, shoulders behind the bar, or stance too wide/narrow). "
                    "2=Average (Minor setup flaws, slightly off-balance). "
                    "3=Optimal (Bar perfectly over mid-foot, scapula directly over the bar, armpits directly above the bar, shin touching the bar upon hinging)."
    )
    
    slack_pull_and_tension: EvaluationCritere = Field(
        description="Evaluates the ability to create full-body tension before the plates leave the floor ('pulling the slack'). "
                    "1=Poor (Yanking/jerking the bar off the floor, bent elbows, zero initial tension). "
                    "2=Average (Some tension created, but loses stiffness at the moment of lift-off). "
                    "3=Optimal (Lifter wedges into position, audible 'click' of the bar against the plates, heavy in the hands before liftoff, arms straight as cables)."
    )

    hip_height_and_stability: EvaluationCritere = Field(
        description="Evaluates the synchronization of the hips and chest during the initial pull. "
                    "1=Poor (Hips shoot up prematurely, legs straighten completely before the bar leaves the ground, turning it into a stiff-leg deadlift). "
                    "2=Average (Slight early hip rise, but the lifter manages to recover and use the legs partially). "
                    "3=Optimal (Hips and chest rise at the exact same time, maintaining the back angle until the bar passes the knees)."
    )

    hip_hinge_mechanics: EvaluationCritere = Field(
        description="Evaluates the posterior chain loading (hamstrings and glutes). "
                    "1=Poor (Squatting the deadlift: hips too low, knees pushed too far forward, zero tension in hamstrings). "
                    "2=Average (Moderate hinge, but quad-dominant setup lacking maximal posterior chain stretch). "
                    "3=Optimal (Excellent hip hinge, high tension in hamstrings and glutes, knees slightly bent but not protruding over the bar)."
    )

    lat_engagement_and_bar_proximity: EvaluationCritere = Field(
        description="Evaluates upper back tightness and keeping the bar close to the center of mass. "
                    "1=Poor (Lats relaxed, bar drifts away from the shins/thighs, placing dangerous leverage on the lower back). "
                    "2=Average (Bar loses contact momentarily but is pulled back towards the body during the lift). "
                    "3=Optimal (Lats aggressively engaged 'bending the bar around the shins', bar maintains light contact with legs throughout the entire lift)."
    )

    core_bracing_and_spine_neutrality: EvaluationCritere = Field(
        description="Evaluates intra-abdominal pressure (Valsalva maneuver) and spine integrity under load. "
                    "1=Poor (Severe lumbar/lower back rounding under load, completely loose core, high risk of injury). "
                    "2=Average (Slight spinal flexion during the hardest part of the pull, but acceptable core brace). "
                    "3=Optimal (Massive 360-degree core brace, neutral spine rigidly locked into place from setup to lockout)."
    )

    leg_drive_activation: EvaluationCritere = Field(
        description="Evaluates the use of the quads to initiate the movement (pushing the floor away). "
                    "1=Poor (Zero leg drive, the lifter purely 'pulls' the weight up with their lower back). "
                    "2=Average (Initial leg push, but transitions to back-extension too early before the bar reaches the knees). "
                    "3=Optimal (Explosive 'leg press' off the floor using the quads, seamlessly transitioning into a glute drive as the bar passes the knees)."
    )

    bar_path_efficiency: EvaluationCritere = Field(
        description="Evaluates the trajectory of the bar from the floor to the top. "
                    "1=Poor (Extreme S-curve, having to move the bar actively around the knees on the way up or down). "
                    "2=Average (Slight horizontal deviation, slight swinging of the bar). "
                    "3=Optimal (Perfectly vertical bar path traveling in a straight line strictly over the mid-foot)."
    )

    lockout_execution: EvaluationCritere = Field(
        description="Evaluates the final completion of the lift at the top. "
                    "1=Poor (Soft knees, hitched rep, or extreme and dangerous hyperextension of the lower back leaning backward). "
                    "2=Average (Slightly soft knees or shoulders not fully rolled back, but hips are through). "
                    "3=Optimal (Crisp glute squeeze, tall proud chest posture, hips and knees fully locked out without any lumbar hyperextension)."
    )

# Dictionnaire de correspondance (Mapping)
schema_mapping = {
    "squat": AnalyseSquat,
    "bench": AnalyseBench,
    "deadlift": AnalyseDeadlift
}