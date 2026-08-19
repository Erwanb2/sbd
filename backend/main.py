import os
import time
import json
from enum import Enum
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

app = FastAPI(title="SBD Reviews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. SCHÉMAS DE CLASSIFICATION (LE "VIDEUR") ---
class MovementType(str, Enum):
    squat = "squat"
    bench = "bench"
    deadlift = "deadlift"
    video_inexploitable = "video_inexploitable"

class VideoClassification(BaseModel):
    mouvement_detecte: MovementType = Field(
        description="Le mouvement de force athlétique détecté dans la vidéo."
    )

# --- 2. SCHÉMAS D'ANALYSE (LE "COACH") ---
class EvaluationCritere(BaseModel):
    note: int = Field(description="Note stricte de 1 à 3.", ge=1, le=3)
    commentaire: str = Field(description="Une seule phrase courte et percutante donnant un conseil ciblé.")

class AnalyseDeadlift(BaseModel):
    hauteur_stabilite_hanches: EvaluationCritere = Field(description="1=Mauvais (hanches shootent). 2=Moyen. 3=Bon (hauteur optimale).")
    hip_hinge_maitrise: EvaluationCritere = Field(description="1=Mauvais (squat le deadlift). 2=Moyen. 3=Bon (recul bassin, tension).")
    engagement_grand_dorsal: EvaluationCritere = Field(description="1=Mauvais (barre s'éloigne). 2=Moyen. 3=Bon (rase les tibias).")
    tirage_slack: EvaluationCritere = Field(description="1=Mauvais (arrache la barre). 2=Moyen. 3=Bon (tension avant décollage).")
    tronc_gaine_stable: EvaluationCritere = Field(description="1=Mauvais (dos rond). 2=Moyen. 3=Bon (bracing massif).")
    poussee_active_jambes: EvaluationCritere = Field(description="1=Mauvais (tirage dos pur). 2=Moyen. 3=Bon (leg drive).")

class AnalyseSquat(BaseModel):
    profondeur: EvaluationCritere = Field(description="1=Mauvais (demi-squat). 2=Moyen (parallèle). 3=Bon (sous le genou).")
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

schema_mapping = {
    "squat": AnalyseSquat,
    "bench": AnalyseBench,
    "deadlift": AnalyseDeadlift
}


@app.post("/analyze")
async def analyze_video(video: UploadFile = File(...)):
    client = genai.Client()
    temp_file_path = f"temp_{video.filename}"
    
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await video.read())

    try:
        # Upload Google
        video_file = client.files.upload(file=temp_file_path)
        while video_file.state.name == "PROCESSING":
            time.sleep(3)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state.name == "FAILED":
            raise HTTPException(status_code=500, detail="L'analyse vidéo a échoué côté Google.")

        # ==========================================================
        # ÉTAPE 1 : CLASSIFICATION RAPIDE (Modèle Lite)
        # ==========================================================
        prompt_classif = "Regarde cette vidéo. Est-ce un squat, un bench press, ou un deadlift ? Si c'est un autre exercice, qu'il n'y a pas d'humain, ou qu'on ne voit rien, choisis video_inexploitable."
        
        reponse_classif = client.models.generate_content(
            model="gemini-3.5-flash-lite", # Ou gemini-1.5-flash-8b selon ton compte
            contents=[video_file, prompt_classif],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoClassification,
                temperature=0.0, # 0 absolu pour éviter la créativité
            )
        )
        
        mouvement_detecte = json.loads(reponse_classif.text)["mouvement_detecte"]
        
        # Le "Videur" rejette la vidéo
        if mouvement_detecte == "video_inexploitable":
            client.files.delete(name=video_file.name)
            raise HTTPException(
                status_code=400, 
                detail="Vidéo inexploitable. Merci d'envoyer une vidéo claire de Squat, Bench ou Deadlift."
            )

        # ==========================================================
        # ÉTAPE 2 : ANALYSE PROFONDE (Modèle Standard/Pro)
        # ==========================================================
        chosen_schema = schema_mapping[mouvement_detecte]
        prompt_analyse = f"Tu es un juge d'élite en Powerlifting. L'athlète exécute un {mouvement_detecte.upper()}. Donne une note stricte de 1 à 3 pour les 6 critères et UNE SEULE phrase de conseil pour chacun."
        
        reponse_analyse = client.models.generate_content(
            model="gemini-3.5-flash", # Le "cerveau"
            contents=[video_file, prompt_analyse],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=chosen_schema,
                temperature=0.1,
            )
        )
        
        client.files.delete(name=video_file.name)
        
        resultat = json.loads(reponse_analyse.text)
        
        # Calcul de la note sur 18
        score_total = sum(critere["note"] for critere in resultat.values() if isinstance(critere, dict))
        resultat["note_globale_brute"] = score_total
        
        # On renvoie le mouvement détecté au frontend pour qu'il s'adapte !
        resultat["mouvement_detecte"] = mouvement_detecte 
        
        return resultat

    except HTTPException:
        raise # On relaisse passer notre erreur 400 personnalisée
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)