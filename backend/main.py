import os
import time
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

app = FastAPI(title="Deadlift AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Sous-modèle : Chaque critère aura sa note ET sa phrase d'explication
class EvaluationCritere(BaseModel):
    note: int = Field(description="Note stricte de 1 à 3.", ge=1, le=3)
    commentaire: str = Field(description="Une seule phrase courte et percutante donnant un conseil ou justifiant la note.")

# 2. Modèle principal reprenant les 7 critères avec le sous-modèle
class AnalyseDeadlift(BaseModel):
    hauteur_stabilite_hanches: EvaluationCritere = Field(
        description="1 = Mauvais (hanches shootent ou trop basses type squat). 2 = Moyen. 3 = Bon (hauteur optimale, hanches/épaules montent ensemble)."
    )
    hip_hinge_maitrise: EvaluationCritere = Field(
        description="1 = Mauvais (squat son deadlift, dos plié). 2 = Moyen. 3 = Bon (superbe recul du bassin, tension ischio, barre au-dessus mi-pied)."
    )
    engagement_grand_dorsal: EvaluationCritere = Field(
        description="1 = Mauvais (épaules en avant, barre s'éloigne). 2 = Moyen. 3 = Bon (barre rase les tibias, aisselles fermées, bras longs)."
    )
    tirage_slack: EvaluationCritere = Field(
        description="1 = Mauvais (tirage brutal/explosif sans tension). 2 = Moyen. 3 = Bon (utilise son poids corporel pour courber la barre avant décollage)."
    )
    tronc_gaine_stable: EvaluationCritere = Field(
        description="1 = Mauvais (dos s'arrondit, flexion lombaire). 2 = Moyen. 3 = Bon (bracing massif, colonne rigide et neutre)."
    )
    trajectoire_barre: EvaluationCritere = Field(
        description="1 = Mauvais (trajectoire en S, contourne les genoux). 2 = Moyen. 3 = Bon (trajectoire parfaitement verticale)."
    )
    poussee_active_jambes: EvaluationCritere = Field(
        description="1 = Mauvais (tirage exclusif dos/lombaires). 2 = Moyen. 3 = Bon (repousse le sol avec les pieds type leg press)."
    )

@app.post("/analyze")
async def analyze_video(video: UploadFile = File(...)):
    client = genai.Client()
    
    temp_file_path = f"temp_{video.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await video.read())

    try:
        video_file = client.files.upload(file=temp_file_path)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(3)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state.name == "FAILED":
            raise HTTPException(status_code=500, detail="L'analyse vidéo a échoué côté Google.")

        prompt = """Tu es un coach d'élite en force athlétique. 
        Pour chacun des 7 critères demandés, donne une note de 1 à 3 et Rédige UNE SEULE phrase courte de conseil."""
        
        # J'ai mis 1.5-flash pour assurer la stabilité maximale
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[video_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalyseDeadlift,
                temperature=0.1,
            )
        )
        
        client.files.delete(name=video_file.name)
        
        # 3. ON CALCULE LE SCORE EXACT EN PYTHON (C'est beaucoup plus sûr)
        resultat = json.loads(response.text)
        
        score_total = 0
        for critere in resultat.values():
            score_total += critere["note"]
            
        # On injecte la note globale dans le JSON avant de l'envoyer à React
        resultat["note_globale"] = score_total
        
        return resultat

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)