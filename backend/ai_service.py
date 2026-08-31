import concurrent.futures
import json
import logging
import os
import time

import cv2
from fastapi import HTTPException
from google import genai
from google.genai import types
from PIL import Image
from schemas import VideoClassification, schema_mapping

client = genai.Client()
logger = logging.getLogger(__name__)

# Délais de garde (en secondes) pour ne JAMAIS rester bloqué indéfiniment.
GOOGLE_PROCESSING_TIMEOUT = int(os.getenv("GEMINI_PROCESSING_TIMEOUT", "180"))
GOOGLE_UPLOAD_FUTURE_TIMEOUT = GOOGLE_PROCESSING_TIMEOUT + 30
GOOGLE_DETECT_FUTURE_TIMEOUT = int(os.getenv("GEMINI_DETECT_TIMEOUT", "120"))


def probe_video_duration_seconds(file_path: str):
    """Durée de la vidéo en secondes via OpenCV, ou None si illisible."""
    cap = cv2.VideoCapture(file_path)
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    finally:
        cap.release()
    if fps <= 0 or frame_count <= 0:
        return None
    return frame_count / fps

def extraire_images(file_path: str, num_images: int = 15) -> list:
    """Extrait rapidement des frames de la vidéo pour le triage rapide."""
    cap = cv2.VideoCapture(file_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    images = []

    if total_frames > 0:
        step = total_frames // (num_images + 1)
        for i in range(1, num_images + 1):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                images.append(pil_img)
    cap.release()
    return images

def _task_detect_movement(file_path: str) -> str:
    """TÂCHE A : Extraction et Détection par l'IA (Tourne en arrière-plan)"""
    images = extraire_images(file_path, num_images=10)
    if not images:
        raise ValueError("Impossible de lire la vidéo. Fichier potentiellement corrompu.")

    prompt_classif = """
    Based on these images, classify the exercise into one of the following categories:
        - squat
        - bench press
        - sumo deadlift
        - conventional deadlift
        - unworkable_video (if none of the above or unclear)
    Deadlift classification rules:
        Classify as sumo deadlift if at least one condition is met:
            - Feet are wide apart
            - Arms are inside the knees
        Otherwise, classify as conventional deadlift.
    """
    # 1. Création de la session de chat avec la configuration voulue
    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoClassification,
            temperature=0.0,
        ),
    )

    # 2. Envoi des images et du prompt
    reponse_classif = chat.send_message(
        message=[*images, prompt_classif]
    )

    # 3. Récupération directe de l'objet Pydantic parsé
    mouvement = reponse_classif.parsed.mouvement_detecte

    # 4. Condition d'échec
    if mouvement == "unworkable_video":
        raise ValueError("Vidéo inexploitable. Merci d'envoyer un Squat, Bench ou Deadlift clair.")

    return mouvement

def _task_upload_video(file_path: str):
    """TÂCHE B : Upload du fichier chez Google (Tourne en arrière-plan)"""
    video_file = client.files.upload(file=file_path)

    # On attend que Google finisse le processing, MAIS avec un timeout dur :
    # un job Google coincé en "PROCESSING" ne doit plus bloquer la requête.
    deadline = time.monotonic() + GOOGLE_PROCESSING_TIMEOUT
    while video_file.state.name == "PROCESSING":
        if time.monotonic() > deadline:
            try:
                client.files.delete(name=video_file.name)
            except Exception:
                pass
            raise ValueError(
                "La préparation de la vidéo par Google a expiré (timeout). Réessaie."
            )
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)

    if video_file.state.name == "FAILED":
        client.files.delete(name=video_file.name)
        raise ValueError("L'analyse de la vidéo a échoué côté Google.")

    return video_file

def upload_and_detect_concurrent(file_path: str) -> dict:
    """
    Lance la Détection ET l'Upload en PARALLÈLE.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_detect = executor.submit(_task_detect_movement, file_path)
        future_upload = executor.submit(_task_upload_video, file_path)
        
        # 1. On attend d'abord le résultat de la détection (c'est souvent le plus rapide)
        try:
            mouvement_detecte = future_detect.result(timeout=GOOGLE_DETECT_FUTURE_TIMEOUT)
        except concurrent.futures.TimeoutError:
            future_detect.cancel()
            try:
                uploaded_file = future_upload.result(timeout=5)
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
            raise HTTPException(
                status_code=504, detail="La détection du mouvement a expiré. Réessaie."
            )
        except Exception as e:
            # SI LA DÉTECTION ÉCHOUE (ex: vidéo de chat)
            # L'upload est peut-être déjà fini ou en cours. On le récupère pour le supprimer !
            try:
                uploaded_file = future_upload.result()
                client.files.delete(name=uploaded_file.name)
                logger.info(f"Fichier invalide supprimé de Google : {uploaded_file.name}")
            except Exception:
                pass # Si l'upload avait crashé aussi, on ignore.
                
            raise HTTPException(status_code=400, detail=str(e))
            
        # 2. Si la détection est bonne, on s'assure que l'upload est bien terminé
        try:
            uploaded_file = future_upload.result(timeout=GOOGLE_UPLOAD_FUTURE_TIMEOUT)
        except concurrent.futures.TimeoutError:
            raise HTTPException(
                status_code=504, detail="L'upload de la vidéo a expiré. Réessaie."
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
    return {
        "file_name": uploaded_file.name,
        "mouvement_detecte": mouvement_detecte
    }

def analyze_movement(file_name: str, mouvement_detecte: str) -> dict:
    try:
        video_file = client.files.get(name=file_name)
        
        chosen_schema = schema_mapping.get(mouvement_detecte)
        if not chosen_schema:
            raise HTTPException(status_code=400, detail="Type de mouvement non reconnu pour l'analyse.")

        # LOOK HOW SMALL THE PROMPT IS NOW!
        prompt_analyse = f"""
        You are a brutally strict, elite IPF powerlifting judge and highly analytical biomechanics coach. 
        The athlete executes a {mouvement_detecte.upper()}.
        
        GRADING RULE: 
          1. Assume the default score is 1 (Poor)
          2. A Score: An integer from 1 to 4, based strictly on the provided rubrics in the schema.
          
        CRITICAL VISIBILITY RULE (The "NA" Rule): 
        If the camera angle makes it impossible to accurately assess a specific body part, score it based on the best visible evidence or penalize for poor framing if highly ambiguous. Do not guess blindly.
        """

        chat = client.chats.create(
            model=os.environ["MODEL_GEMINI"],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=chosen_schema,
                temperature=0.0, 
            )
        )           

        reponse_analyse = chat.send_message([video_file, prompt_analyse])
        resultat = json.loads(reponse_analyse.text)
        
        # --- LE SCALE STRETCHING SÉCURISÉ ---
        for key, critere in resultat.items():
            if isinstance(critere, dict) and "score" in critere:
                raw_score = critere["score"]
                if raw_score <= 2:
                    critere["score"] = 1
                elif raw_score == 3:
                    critere["score"] = 2
                elif raw_score == 4:
                    critere["score"] = 3
        
        # --- CALCUL DU SCORE ---
        score_total = sum(critere.get("score", 0) for critere in resultat.values() if isinstance(critere, dict) and "score" in critere)
        nb_criteres_notes = sum(1 for critere in resultat.values() if isinstance(critere, dict) and "score" in critere)
        
        resultat["total_raw_score"] = score_total
        if resultat["total_raw_score"] >= 22 and "deadlift" in mouvement_detecte.lower():
            resultat["lifter_persona"] = "The Technician"
            resultat["persona_justification"] = "You are the GOAT. Form is flawless."
            
        resultat["raw_max_score"] = nb_criteres_notes * 3
        resultat["movement_detected"] = mouvement_detecte
        
        return resultat

    except HTTPException:
        # Erreurs métier déjà formatées (ex: mouvement non reconnu) : on ne les
        # transforme surtout pas en 500.
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

    finally:
        try:
            client.files.delete(name=file_name)
        except Exception as e:
            logger.warning(f"Attention : Impossible de supprimer le fichier {file_name} - {e}")
