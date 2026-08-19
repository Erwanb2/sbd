import time
import json
from fastapi import HTTPException
from google import genai
from google.genai import types
from schemas import VideoClassification, schema_mapping

def detect_movement(file_path: str) -> dict:
    """Upload la vidéo et utilise flash-lite pour identifier le mouvement."""
    client = genai.Client()
    
    # 1. Upload sur Google
    video_file = client.files.upload(file=file_path)
    while video_file.state.name == "PROCESSING":
        time.sleep(3)
        video_file = client.files.get(name=video_file.name)
        
    if video_file.state.name == "FAILED":
        raise HTTPException(status_code=500, detail="L'analyse vidéo a échoué côté Google.")

    # 2. Triage rapide
    prompt_classif = "Regarde cette vidéo. Est-ce un squat, un bench press, ou un deadlift ? Si autre chose ou inexploitable, choisis video_inexploitable."
    reponse_classif = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[video_file, prompt_classif],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoClassification,
            temperature=0.0,
        )
    )
    
    mouvement_detecte = json.loads(reponse_classif.text)["mouvement_detecte"]
    
    if mouvement_detecte == "video_inexploitable":
        client.files.delete(name=video_file.name) # On nettoie tout de suite
        raise HTTPException(status_code=400, detail="Vidéo inexploitable. Merci d'envoyer un Squat, Bench ou Deadlift clair.")

    # On renvoie le nom du fichier chez Google pour l'utiliser à l'étape 2 !
    return {
        "file_name": video_file.name,
        "mouvement_detecte": mouvement_detecte
    }

def analyze_movement(file_name: str, mouvement_detecte: str) -> dict:
    """Récupère la vidéo existante et fait l'analyse complète avec flash 1.5."""
    client = genai.Client()
    
    try:
        # On récupère le fichier déjà uploadé lors de l'étape 1
        video_file = client.files.get(name=file_name)
        
        chosen_schema = schema_mapping[mouvement_detecte]
        prompt_analyse = f"Tu es un juge d'élite en Powerlifting. L'athlète exécute un {mouvement_detecte.upper()}. Donne une note stricte de 1 à 3 pour tous les critères de la grille et UNE SEULE phrase de conseil pour chacun."
        
        reponse_analyse = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[video_file, prompt_analyse],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=chosen_schema,
                temperature=0.1,
            )
        )
        
        resultat = json.loads(reponse_analyse.text)
        score_total = sum(critere["note"] for critere in resultat.values() if isinstance(critere, dict))
        
        resultat["note_globale_brute"] = score_total
        resultat["score_max_brut"] = len(chosen_schema.model_fields) * 3
        resultat["mouvement_detecte"] = mouvement_detecte
        
        return resultat

    finally:
        # ÉTAPE FINALE : On supprime définitivement la vidéo des serveurs Google
        try:
            client.files.delete(name=file_name)
        except Exception:
            pass