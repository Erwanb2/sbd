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
    note: int = Field(description="Note stricte de 1 à 3.", ge=1, le=3)
    commentaire: str = Field(description="Une seule phrase courte et percutante donnant un conseil ciblé.")

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
    hauteur_stabilite_hanches: EvaluationCritere = Field(description="1=Mauvais (hanches shootent). 2=Moyen. 3=Bon (hauteur optimale).")
    hip_hinge_maitrise: EvaluationCritere = Field(description="1=Mauvais (squat le deadlift). 2=Moyen. 3=Bon (recul bassin, tension).")
    engagement_grand_dorsal: EvaluationCritere = Field(description="1=Mauvais (barre s'éloigne). 2=Moyen. 3=Bon (rase les tibias).")
    tirage_slack: EvaluationCritere = Field(description="1=Mauvais (arrache la barre). 2=Moyen. 3=Bon (tension avant décollage).")
    tronc_gaine_stable: EvaluationCritere = Field(description="1=Mauvais (dos rond). 2=Moyen. 3=Bon (bracing massif).")
    poussee_active_jambes: EvaluationCritere = Field(description="1=Mauvais (tirage dos pur). 2=Moyen. 3=Bon (leg drive).")
    # ON RÉINTÈGRE LA TRAJECTOIRE DE LA BARRE ICI :
    trajectoire_barre: EvaluationCritere = Field(description="1=Mauvais (trajectoire en S, contourne genoux). 2=Moyen. 3=Bon (verticale).")

# Dictionnaire de correspondance (Mapping)
schema_mapping = {
    "squat": AnalyseSquat,
    "bench": AnalyseBench,
    "deadlift": AnalyseDeadlift
}