import time
import json
import cv2
from PIL import Image
from fastapi import HTTPException
from google import genai
from google.genai import types
from schemas import VideoClassification, schema_mapping
import logging
client = genai.Client()

logger = logging.getLogger(__name__)


def extraire_images(file_path: str, num_images: int = 3) -> list:
    """
    Extrait rapidement quelques images (frames) de la vidéo réparties sur sa durée.
    Utilisé pour le triage rapide (fail-fast).
    """
    cap = cv2.VideoCapture(file_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    images = []

    if total_frames > 0:
        step = total_frames // (num_images + 1)
        for i in range(1, num_images + 1):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
            ret, frame = cap.read()
            if ret:
                # Convertir l'image de BGR (format OpenCV) vers RGB (format attendu par Pillow)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                images.append(pil_img)
    cap.release()
    return images

def detect_movement(file_path: str) -> dict:
    """
    Étape 1 du workflow (appelée par /detect) :
    - Extrait 3 images.
    - Demande à Gemini Flash-Lite d'identifier le mouvement.
    - Si la vidéo est valide, l'upload vers Google.
    - Retourne l'identifiant du fichier et le nom du mouvement.
    """
    
    images = extraire_images(file_path, num_images=3)
    logger.info("Images extraites")

    if not images:
        raise HTTPException(status_code=400, detail="Impossible de lire la vidéo. Fichier potentiellement corrompu.")

    prompt_classif = "Regarde ces 3 images extraites d'une vidéo. Est-ce un squat, un bench press, ou un deadlift ? Si c'est autre chose ou si c'est inexploitable, choisis video_inexploitable."
    
    try:
        reponse_classif = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[*images, prompt_classif],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoClassification,
                temperature=0.0,
            )
        )
        mouvement_detecte = json.loads(reponse_classif.text)["mouvement_detecte"]
        logger.info("Mouvement détecté")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la classification par l'IA: {str(e)}")

    # Si c'est une vidéo de chat ou de paysage, on coupe direct !
    if mouvement_detecte == "video_inexploitable":
        raise HTTPException(status_code=400, detail="Vidéo inexploitable. Merci d'envoyer un Squat, Bench ou Deadlift clair.")

    try:
        video_file = client.files.upload(file=file_path)
        
        # On attend que Google finisse de processer la vidéo
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state.name == "FAILED":
            # On supprime pour ne pas garder de déchet
            client.files.delete(name=video_file.name)
            raise HTTPException(status_code=500, detail="L'analyse vidéo a échoué côté Google.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'upload vers Google: {str(e)}")

    # Le dictionnaire retourné ici correspond exactement à ce que /detect attend 
    # avant d'y ajouter le 'quota_restant'.
    return {
        "file_name": video_file.name,
        "mouvement_detecte": mouvement_detecte
    }

def analyze_movement(file_name: str, mouvement_detecte: str) -> dict:
    """
    Étape 2 du workflow (appelée par /analyze) :
    - Récupère la vidéo existante chez Google.
    - Fait l'analyse biomécanique complète avec Gemini Flash 1.5.
    - Supprime la vidéo du serveur Google à la fin (succès ou échec).
    """
    try:
        # On récupère le pointeur vers le fichier uploadé à l'étape 1
        video_file = client.files.get(name=file_name)
        
        chosen_schema = schema_mapping.get(mouvement_detecte)
        if not chosen_schema:
            raise HTTPException(status_code=400, detail="Type de mouvement non reconnu pour l'analyse.")

        prompt_analyse = f"You are a strict powerlifting judge. The athlete executes a {mouvement_detecte.upper()}. Give a score between 1 and 3 and comment for each criteria."
        
        reponse_analyse = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[video_file, prompt_analyse],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=chosen_schema,
                temperature=0.1, # Faible pour rester analytique et factuel
            )
        )
        
        resultat = json.loads(reponse_analyse.text)
        
        # Calcul dynamique du score total (basé sur toutes les clés retournées par l'IA qui ont une note)
        score_total = sum(critere.get("note", 0) for critere in resultat.values() if isinstance(critere, dict) and "note" in critere)
        
        # On injecte les métadonnées dans la réponse pour le frontend React
        resultat["note_globale_brute"] = score_total
        resultat["score_max_brut"] = len(chosen_schema.model_fields) * 3
        resultat["mouvement_detecte"] = mouvement_detecte
        
        return resultat

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse détaillée: {str(e)}")

    finally:
        # ⚠️ ÉTAPE FINALE CRUCIALE : On supprime DEFINITIVEMENT la vidéo des serveurs Google
        try:
            client.files.delete(name=file_name)
        except Exception as e:
            # On ignore l'erreur ici car l'essentiel est de retourner la réponse à l'utilisateur
            print(f"Attention : Impossible de supprimer le fichier {file_name} côté Google - {e}")