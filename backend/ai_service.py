import os
import time
import json
import cv2
import concurrent.futures
from PIL import Image
from fastapi import HTTPException
from google import genai
from google.genai import types
from schemas import VideoClassification, schema_mapping
import logging

client = genai.Client()
logger = logging.getLogger(__name__)

def extraire_images(file_path: str, num_images: int = 3) -> list:
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
    images = extraire_images(file_path, num_images=3)
    if not images:
        raise ValueError("Impossible de lire la vidéo. Fichier potentiellement corrompu.")

    prompt_classif = "Regarde ces 3 images extraites d'une vidéo. Est-ce un squat, un bench press, ou un deadlift ? Si c'est autre chose ou si c'est inexploitable, choisis video_inexploitable."
    
    reponse_classif = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[*images, prompt_classif],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoClassification,
            temperature=0.0,
        )
    )
    mouvement = json.loads(reponse_classif.text)["mouvement_detecte"]
    
    if mouvement == "video_inexploitable":
        raise ValueError("Vidéo inexploitable. Merci d'envoyer un Squat, Bench ou Deadlift clair.")
        
    return mouvement

def _task_upload_video(file_path: str):
    """TÂCHE B : Upload du fichier chez Google (Tourne en arrière-plan)"""
    video_file = client.files.upload(file=file_path)
    
    # On attend que Google finisse le processing
    while video_file.state.name == "PROCESSING":
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
            mouvement_detecte = future_detect.result()
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
            uploaded_file = future_upload.result()
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

        # --- LE BON PROMPT (Avec échelle sur 4 et consignes Persona) ---
        prompt_analyse = f"""
        You are a brutally strict, elite IPF powerlifting judge and highly analytical biomechanics coach. 
        The athlete executes a {mouvement_detecte.upper()}.
        

        GRADING RULE: 
          1.  Assume the default score is 1 (Poor)
          2. A Score: An integer from 1 to 4, based strictly on the provided rubrics.
          3. A Brief Explanation: A concise 1-2 sentence justification explaining EXACTLY what visual evidence led to this score.

        CRITICAL VISIBILITY RULE (The "NA" Rule): 
        If the camera angle, framing, lighting, or video quality makes it impossible to accurately assess a specific body part or phase of the lift (e.g., the lifter's feet are out of frame, making 'Starting Position' impossible to judge), you MUST output "NA" for the score. Do not guess. In the explanation, state exactly why it cannot be scored (e.g., "NA - Lower legs and feet are out of frame, cannot evaluate bar proximity").

        At the end of your analysis, calculate the AVERAGE SCORE of the lift based only on the criteria that received a numerical score (exclude "NA" from the math).

        Output your analysis in the following structured format:

        1. Starting Position
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on mid-foot placement, hip height, and scapula position]

        2. Slack Pull and Lat Engagement
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on upper back tension and pre-lift tightness]

        3. Leg Drive Activation
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on hip rise and quad usage off the floor]

        4. Hip Hinge Mechanics
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on posterior chain tension and joint synchronization]

        5. Core Bracing and Spine Neutrality
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on lumbar/thoracic rounding and brace]

        6. Bar Path and Proximity
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on how close the bar stays to the shins/thighs]

        7. Lockout Execution
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on hip/knee extension and posture at the top]

        8. Eccentric Control and Descent
        - Score: [1, 2, 3, 4, or NA]
        - Explanation: [Briefly explain the score based on how the weight is lowered]
        """
        
        if "deadlift" in mouvement_detecte.lower():
            prompt_analyse += """
            LIFTER PERSONA CLASSIFICATION
            Based on your analysis, assign exactly ONE fun 'lifter_persona'. 
            
            - 'The Technician': Form is perfect.
            - 'The Crane': Hips shoot up early.
            - 'The Squatter': Hips are way too low. 
            - 'The Fishing Rod': Visible back rounding. 
            - 'The Hitcher': Bar rests on thighs. 
            - 'The Over-Extender': Leans backward at lockout. 
            - 'The Grip & Rip': Rushes setup.
            
            Provide a fun, engaging 'persona_justification'.
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
                # Conversion 1-4 vers 1-3 pour le Frontend
                if raw_score <= 2:
                    critere["score"] = 1
                elif raw_score == 3:
                    critere["score"] = 2
                elif raw_score == 4:
                    critere["score"] = 3
        
        # --- CALCUL DU SCORE ET DU MAX EXACT ---
        score_total = sum(critere.get("score", 0) for critere in resultat.values() if isinstance(critere, dict) and "score" in critere)
        nb_criteres_notes = sum(1 for critere in resultat.values() if isinstance(critere, dict) and "score" in critere)
        
        resultat["total_raw_score"] = score_total
        resultat["raw_max_score"] = nb_criteres_notes * 3
        resultat["movement_detected"] = mouvement_detecte
        
        return resultat

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

    finally:
        try:
            client.files.delete(name=file_name)
        except Exception as e:
            logger.warning(f"Attention : Impossible de supprimer le fichier {file_name} - {e}")