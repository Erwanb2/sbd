import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai_service import detect_movement, analyze_movement

app = FastAPI(title="SBD Reviews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schéma attendu pour la 2ème étape (l'analyse)
class AnalyzeRequest(BaseModel):
    file_name: str
    movement: str

@app.post("/detect")
async def detect_video(video: UploadFile = File(...)):
    """Étape 1 : Upload la vidéo chez Google et détecte le mouvement."""
    temp_file_path = f"temp_{video.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await video.read())

    try:
        return detect_movement(temp_file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/analyze")
async def analyze_video(request: AnalyzeRequest):
    """Étape 2 : Utilise la vidéo déjà uploadée pour l'analyse approfondie."""
    try:
        return analyze_movement(request.file_name, request.movement)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")