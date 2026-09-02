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
from pricing import log_usage
from schemas import VideoClassification, numeric_score, schema_mapping

client = genai.Client()
logger = logging.getLogger(__name__)

# Délais de garde (en secondes) pour ne JAMAIS rester bloqué indéfiniment.
GOOGLE_PROCESSING_TIMEOUT = int(os.getenv("GEMINI_PROCESSING_TIMEOUT", "180"))
GOOGLE_UPLOAD_FUTURE_TIMEOUT = GOOGLE_PROCESSING_TIMEOUT + 30
GOOGLE_DETECT_FUTURE_TIMEOUT = int(os.getenv("GEMINI_DETECT_TIMEOUT", "120"))

# Modèle du triage rapide (images seules), distinct du modèle d'analyse vidéo.
MODEL_CLASSIFICATION = os.getenv("MODEL_GEMINI_CLASSIFICATION", "gemini-3.5-flash-lite")

# Modèle de repli quand le modèle principal est saturé (503 UNAVAILABLE).
# Moins fin, mais une analyse dégradée vaut mieux qu'une erreur 500.
MODEL_ANALYSIS_FALLBACK = os.getenv("MODEL_GEMINI_FALLBACK", "gemini-3.5-flash-lite")


def _is_model_overloaded(exc: Exception) -> bool:
    """Vrai si l'échec vient de la saturation du modèle, pas de notre requête.

    `google.genai` lève une APIError qui porte `.code` (int) et `.status`
    ("UNAVAILABLE"). On retombe sur le texte du message en dernier recours, au
    cas où l'erreur remonterait enveloppée dans autre chose.
    """
    if getattr(exc, "code", None) == 503:
        return True
    status = getattr(exc, "status", None)
    if isinstance(status, str) and status.upper() == "UNAVAILABLE":
        return True
    message = str(exc).upper()
    return "503" in message and "UNAVAILABLE" in message


def _run_analysis(model: str, video_file, prompt: str, schema, mouvement: str) -> dict:
    """Un passage d'analyse vidéo avec un modèle donné."""
    chat = client.chats.create(
        model=model,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.0,
        ),
    )
    reponse = chat.send_message([video_file, prompt])
    log_usage(model=model, response=reponse, label="analyse", extra=mouvement)
    return json.loads(reponse.text)


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
        model=MODEL_CLASSIFICATION,
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
    log_usage(
        model=MODEL_CLASSIFICATION,
        response=reponse_classif,
        label="classification",
        extra=f"{len(images)} images",
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
          2. A Score: "1" to "4", based strictly on the provided rubrics in the schema.

        CRITICAL VISIBILITY RULE (The "NA" Rule):
        If the camera angle, framing, lighting or video quality makes a specific
        criterion impossible to assess, output "NA" for that criterion and say in
        the feedback exactly what is not visible. Do not guess.
        "NA" means you could not SEE it, never that you saw it and disliked it:
        a flaw you can see is a low score, not "NA".
        Judge every other criterion normally; one "NA" must not drag the others down.
        """

        model_analyse = os.environ["MODEL_GEMINI"]
        modele_de_repli = None

        try:
            resultat = _run_analysis(
                model_analyse, video_file, prompt_analyse, chosen_schema, mouvement_detecte
            )
        except Exception as exc:
            # Saturation du modèle principal : on retente une seule fois sur le
            # modèle de repli. Toute autre erreur remonte telle quelle.
            if not _is_model_overloaded(exc) or MODEL_ANALYSIS_FALLBACK == model_analyse:
                raise
            logger.warning(
                "Modèle %s saturé (503 UNAVAILABLE), repli sur %s",
                model_analyse,
                MODEL_ANALYSIS_FALLBACK,
            )
            modele_de_repli = MODEL_ANALYSIS_FALLBACK
            resultat = _run_analysis(
                modele_de_repli, video_file, prompt_analyse, chosen_schema, mouvement_detecte
            )
        
        # --- LE SCALE STRETCHING SÉCURISÉ ---
        # Les critères "NA" (non visibles à l'image) sortent du score : ils
        # passent à None et ne comptent NI au numérateur NI au dénominateur.
        score_total = 0
        nb_criteres_notes = 0
        for critere in resultat.values():
            if not (isinstance(critere, dict) and "score" in critere):
                continue

            raw_score = numeric_score(critere["score"])
            if raw_score is None:
                critere["score"] = None
                critere["not_assessable"] = True
                continue

            compressed = 1 if raw_score <= 2 else (2 if raw_score == 3 else 3)
            critere["score"] = compressed
            score_total += compressed
            nb_criteres_notes += 1

        # --- CALCUL DU SCORE ---
        score_max = nb_criteres_notes * 3
        resultat["total_raw_score"] = score_total
        resultat["raw_max_score"] = score_max
        resultat["not_assessable_count"] = sum(
            1 for c in resultat.values() if isinstance(c, dict) and c.get("not_assessable")
        )

        # Seuil proportionnel : avec des critères "NA" le maximum n'est plus
        # forcément 24, donc un seuil en dur passerait à côté.
        if (
            score_max > 0
            and score_total >= 0.9 * score_max
            and "deadlift" in mouvement_detecte.lower()
        ):
            resultat["lifter_persona"] = "The Technician"
            resultat["persona_justification"] = "You are the GOAT. Form is flawless."

        resultat["movement_detected"] = mouvement_detecte

        # Ajouté APRÈS la boucle de scoring : ce dict n'a pas de clé "score",
        # il ne sera donc jamais pris pour un critère, ni ici ni côté front.
        if modele_de_repli:
            resultat["model_fallback"] = {
                "used": True,
                "primary": model_analyse,
                "model": modele_de_repli,
            }

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
