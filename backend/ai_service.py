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
from schemas import (
    VideoClassification,
    criteres_de_synthese,
    numeric_score,
    schema_mapping,
)
import pose_analysis
import rep_detection

client = genai.Client()
logger = logging.getLogger(__name__)

# Délais de garde (en secondes) pour ne JAMAIS rester bloqué indéfiniment.
GOOGLE_PROCESSING_TIMEOUT = int(os.getenv("GEMINI_PROCESSING_TIMEOUT", "180"))
GOOGLE_UPLOAD_FUTURE_TIMEOUT = GOOGLE_PROCESSING_TIMEOUT + 30
GOOGLE_DETECT_FUTURE_TIMEOUT = int(os.getenv("GEMINI_DETECT_TIMEOUT", "120"))
POSE_FUTURE_TIMEOUT = int(os.getenv("POSE_TIMEOUT", "45"))

# Il n'y a plus de table de compression : le modele note directement sur 1-3.
# L'ancienne table (note brute sur 4 ramenee sur 3) est morte avec le niveau 4 du
# bareme, qui etait ecrit en superlatifs et ne sortait que sur 5,7 % des cases
# notees alors que l'humain met 3/3 sur 30 % — le haut de l'echelle etait
# inatteignable autrement qu'en le redistribuant apres coup. Voir `CriteriaScore`
# dans schemas.py, et eval/scorer/scale_lab.py pour la mesure qui l'a tranche.

# Modèle du triage rapide (images seules), distinct du modèle d'analyse vidéo.
MODEL_CLASSIFICATION = os.getenv("MODEL_GEMINI_CLASSIFICATION", "gemini-3.5-flash-lite")


# Modèle de repli quand le modèle principal est saturé (503 UNAVAILABLE).
# Moins fin, mais une analyse dégradée vaut mieux qu'une erreur 500.
MODEL_ANALYSIS_FALLBACK = os.getenv("MODEL_GEMINI_FALLBACK", "gemini-3.5-flash-lite")

# Modeles d'analyse que le client a le droit de demander. Le front envoie une cle, jamais
# un nom de modele : sinon n'importe qui pourrait faire tourner le modele le plus cher.
MODELES_ANALYSE = {
    "3.5": "gemini-3.5-flash",
    "3.7": "gemini-3.7-flash",
}


def _moyenne_arrondie(notes) -> int | None:
    """Moyenne des notes exploitables, arrondie au plus proche. None s'il n'y en a pas.

    Ni mediane, ni arrondi a l'inferieur, et les deux ont ete essayes.

    La mediane efface la valeur isolee : sur (3, 3, 2) elle vaut 3, et la page
    porterait un histogramme disant "la rep 3 decroche" au-dessus d'une liste de
    notes disant que tout va bien.

    L'arrondi a l'inferieur fait l'inverse, et c'est pire : **sur un set de 3 reps
    ou moins avec un ecart d'un point, il est arithmetiquement identique au
    minimum** — (2, 2, 1) donne 1,67 donc 1, (3, 3, 2) donne 2,67 donc 2. Mesure
    sur 6 clips (gemini-3.1-flash-lite) : il egalait la pire rep sur 45 criteres
    notes sur 45, et coutait 5 a 6 points de total sur les clips a 3 reps. La note
    d'un critere n'etait plus une synthese, c'etait sa plus mauvaise repetition.

    L'arrondi au plus proche bouge des qu'une rep se degrade sans se coller au
    minimum, et la rep isolee reste visible dans l'histogramme juste au-dessus.
    """
    notes = [n for n in notes if n is not None]
    if not notes:
        return None
    return int(sum(notes) / len(notes) + 0.5)  # notes positives : arrondi au plus proche


def _note_les_reps(resultat: dict, criteres: list[str]) -> list[dict]:
    """Normalise les notes de chaque rep et calcule sa note d'ensemble.

    Renvoie la liste des reps normalisee, celle qui part au front. Une rep dont
    aucun critere n'est lisible garde une note `None` : elle reste dans
    l'histogramme, signalee comme non evaluable, plutot que de disparaitre et de
    decaler la numerotation de toutes les suivantes.
    """
    reps = []
    for rang, rep in enumerate(resultat.get("reps") or [], start=1):
        if not isinstance(rep, dict):
            continue
        # Le modele numerote parfois mal (deux reps "1", ou un trou) : le rang
        # dans la liste est la seule source fiable de l'ordre chronologique.
        rep["rep_index"] = rang
        notes = []
        for nom in criteres:
            bloc = rep.get(nom)
            if not isinstance(bloc, dict):
                continue
            note = numeric_score(bloc.get("score"))
            bloc["score"] = note
            bloc["not_assessable"] = note is None
            notes.append(note)
        evaluables = [n for n in notes if n is not None]
        rep["score"] = _moyenne_arrondie(notes)
        rep["total"] = sum(evaluables)
        rep["max"] = len(evaluables) * 3
        rep["not_assessable_count"] = len(notes) - len(evaluables)
        reps.append(rep)
    return reps


def _agrege_les_criteres(resultat: dict, criteres: list[str], reps: list[dict]) -> None:
    """Donne sa note a chaque critere de synthese, a partir des notes par rep.

    Le modele ne rend PAS de note de synthese (voir `SetCriterion`) : elle est
    calculee ici. C'est la seule source de verite de la page — le nombre affiche
    sous l'histogramme est, par construction, la moyenne des barres qu'il montre.
    """
    for nom in criteres:
        bloc = resultat.get(nom)
        if not isinstance(bloc, dict):
            continue
        par_rep = [r.get(nom) if isinstance(r.get(nom), dict) else {} for r in reps]
        # Le detail par rep est conserve a cote de l'agregat : sans lui, toute
        # question sur la regle d'agregation demanderait de redepenser les appels.
        bloc["rep_scores"] = [b.get("score") for b in par_rep]
        bloc["score"] = _moyenne_arrondie(bloc["rep_scores"])
        bloc["not_assessable"] = bloc["score"] is None


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


def _run_analysis(model: str, contenus: list, schema, mouvement: str,
                  media_resolution=None) -> dict:
    """Un passage d'analyse video avec un modele donne.

    `contenus` est la liste envoyee telle quelle : un seul Part video plus le prompt dans
    le mode historique, un Part par repetition candidate plus le prompt dans le mode
    segments. `media_resolution` pilote le nombre de tokens par image, independamment de
    la cadence portee par les VideoMetadata.
    """
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
    )
    if media_resolution is not None:
        config.media_resolution = media_resolution
    chat = client.chats.create(model=model, config=config)
    reponse = chat.send_message(contenus)
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

    # La distinction sumo / conventionnel n'est plus demandee au modele : elle est
    # mesuree sur la pose (pose_analysis), qui la tranche mieux que des images fixes.
    prompt_classif = """
    Based on these images, classify the exercise into one of the following categories:
        - squat
        - bench press
        - deadlift
        - unworkable_video (if none of the above or unclear)
    Answer with the movement family only. Do not try to tell sumo from conventional.
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
    mouvement = (reponse_classif.parsed.mouvement_detecte or "").strip().lower()

    # 4. Condition d'échec
    if "unworkable" in mouvement or not mouvement:
        raise ValueError("Vidéo inexploitable. Merci d'envoyer un Squat, Bench ou Deadlift clair.")

    # Le modèle répond parfois "sumo deadlift" par habitude : on ne garde que la famille,
    # la variante est décidée par la pose.
    if "deadlift" in mouvement:
        return "deadlift"
    if "bench" in mouvement:
        return "bench press"
    if "squat" in mouvement:
        return "squat"
    raise ValueError("Vidéo inexploitable. Merci d'envoyer un Squat, Bench ou Deadlift clair.")

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

# La cinématique est calculée au moment de la détection, mais consommée plus tard, à
# l'analyse. On la garde en mémoire, indexée par le nom du fichier Gemini : pas de
# changement de schéma en base, pas de contrat d'API élargi. En cas de perte (process
# relancé, plusieurs workers), l'analyse tourne simplement sans, ce qui est bénin.
_KINEMATICS_CACHE: dict[str, tuple[float, dict]] = {}
_KINEMATICS_TTL = 3 * 3600
_KINEMATICS_MAX = 200


# Les repetitions candidates suivent le meme chemin que la cinematique : calculees a la
# detection, reprises a l'analyse. Meme duree de vie, meme benignite en cas de perte —
# sans candidats on retombe simplement sur l'ancien prompt.
_CANDIDATS_CACHE: dict[str, tuple[float, list]] = {}


def _memorise(cache: dict, file_name: str, data) -> None:
    now = time.time()
    for k, (t, _) in list(cache.items()):
        if now - t > _KINEMATICS_TTL:
            cache.pop(k, None)
    if len(cache) >= _KINEMATICS_MAX:
        oldest = min(cache, key=lambda k: cache[k][0])
        cache.pop(oldest, None)
    cache[file_name] = (now, data)


def _reprend(cache: dict, file_name: str):
    entry = cache.get(file_name)
    if entry is None:
        return None
    ts, data = entry
    if time.time() - ts > _KINEMATICS_TTL:
        cache.pop(file_name, None)
        return None
    return data


def _remember_kinematics(file_name: str, data: dict) -> None:
    _memorise(_KINEMATICS_CACHE, file_name, data)


def _take_kinematics(file_name: str) -> dict | None:
    return _reprend(_KINEMATICS_CACHE, file_name)


# Executeur dedie a la pose : le bloc "with" ci-dessous attend la fin de toutes ses
# taches en sortant. Pour un squat ou un bench, la variante n'a aucun interet et on ne
# veut pas payer les quelques secondes de calcul : en le sortant du bloc, on peut
# simplement ignorer le resultat.
_POSE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="pose")


def _task_pose(file_path: str) -> dict:
    """TÂCHE C : mesures de pose. Ne lève jamais, l'appelant se rabat sur le modèle."""
    try:
        return pose_analysis.analyse(file_path)
    except Exception as exc:
        logger.warning("pose_analysis a échoué : %s", exc)
        return {"ok": False, "raison": str(exc)}


def _task_candidats(file_path: str) -> list[dict]:
    """TÂCHE D : instants ou une repetition est possible. Ne lève jamais.

    Passe de pose dense, distincte de celle de la cascade sumo/conventionnel — celle-ci
    est validee sur exactement 30 frames et son resultat change si on touche a son
    echantillonnage. Elle tourne pour toutes les videos, y compris squat et bench ou son
    resultat est ignore : la lancer apres la classification la rendrait sequentielle, et
    on paierait en latence ce qu'on economise en CPU.
    """
    return rep_detection.analyse_candidats(file_path)


def _variante_par_modele(file_path: str, mesures: dict | None) -> str:
    """Repli quand la pose est inexploitable : on redemande la variante au modèle,
    en lui joignant les mesures disponibles. Configuration mesurée à 19/21."""
    images = extraire_images(file_path, num_images=10)
    contexte = ""
    if mesures:
        contexte = (
            "\nAutomatic pose measurements (noisy, weigh them with what you see):\n"
            f"{json.dumps(mesures)}\n"
            "`largeur` is heel spread divided by shoulder spread (above ~1.6 means a wide "
            "stance); `confiance` near zero means the lifter is filmed edge-on and the "
            "stance width cannot be trusted."
        )
    prompt = (
        "The athlete performs a deadlift. Decide the variant.\n"
        "Answer exactly 'sumo deadlift' or 'conventional deadlift'.\n"
        "Sumo: feet clearly wider than shoulders AND hands gripping inside the knees.\n"
        "Conventional: hands gripping outside the knees." + contexte
    )
    reponse = client.models.generate_content(
        model=MODEL_CLASSIFICATION,
        contents=[*images, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoClassification,
            temperature=0.0,
        ),
    )
    log_usage(model=MODEL_CLASSIFICATION, response=reponse, label="variante_repli",
              extra=f"{len(images)} images")
    reponse_txt = (reponse.parsed.mouvement_detecte or "").lower()
    return "sumo deadlift" if "sumo" in reponse_txt else "conventional deadlift"


def upload_and_detect_concurrent(file_path: str) -> dict:
    """
    Lance la Détection ET l'Upload en PARALLÈLE.
    """
    future_pose = _POSE_EXECUTOR.submit(_task_pose, file_path)
    future_candidats = _POSE_EXECUTOR.submit(_task_candidats, file_path)
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
            
        # 3. La famille vient du modèle, la variante du deadlift vient de la pose.
        pose = {"ok": False, "raison": "pose non calculée"}
        if mouvement_detecte == "deadlift":
            try:
                pose = future_pose.result(timeout=POSE_FUTURE_TIMEOUT)
            except Exception as exc:
                logger.warning("pose indisponible : %s", exc)
                pose = {"ok": False, "raison": str(exc)}

    if mouvement_detecte == "deadlift":
        if pose.get("ok"):
            mouvement_detecte = f"{pose['variante']} deadlift"
            logger.info("variante par la pose : %s (règle %s, largeur %s, confiance %s, "
                        "profondeur %s)", mouvement_detecte, pose.get("regle"),
                        pose.get("largeur"), pose.get("confiance"), pose.get("profondeur"))
        else:
            mesures = {k: pose[k] for k in ("largeur", "confiance", "profondeur") if k in pose}
            try:
                mouvement_detecte = _variante_par_modele(file_path, mesures or None)
                logger.info("variante par repli modèle : %s (%s)", mouvement_detecte,
                            pose.get("raison"))
            except Exception as exc:
                logger.warning("repli modèle impossible (%s), conventionnel par défaut", exc)
                mouvement_detecte = "conventional deadlift"

    if pose.get("kinematics"):
        _remember_kinematics(uploaded_file.name, pose["kinematics"])

    # Les candidats ne servent qu'au souleve de terre : `bar_left_floor` n'a pas de sens
    # au squat (barre sur le dos) ni au developpe couche, et le compteur de pose n'a ete
    # valide que sur des deadlifts.
    if "deadlift" in mouvement_detecte:
        try:
            candidats = future_candidats.result(timeout=POSE_FUTURE_TIMEOUT)
        except Exception as exc:
            logger.warning("candidats de repetition indisponibles : %s", exc)
            candidats = []
        if candidats:
            _memorise(_CANDIDATS_CACHE, uploaded_file.name, candidats)
            logger.info("%d repetition(s) candidate(s) : %s", len(candidats),
                        [c["lockout_s"] for c in candidats])

    return {
        "file_name": uploaded_file.name,
        "mouvement_detecte": mouvement_detecte,
        "pose": {k: v for k, v in pose.items() if k != "kinematics"},
    }

# Budget d'images pour le mode segments. La cadence est deduite de la duree totale des
# segments plutot que fixee : sinon une serie de dix reps coute dix fois une serie d'une,
# et une video longue explose le cout. Bornes basses et hautes pour qu'un clip tres court
# ne parte pas a 60 im/s et qu'un clip tres long ne tombe pas sous le seuil ou un
# verrouillage bref passe entre deux images.
BUDGET_IMAGES = 300
FPS_MIN, FPS_MAX = 2.0, 10.0


def _cadence_segments(candidats: list[dict]) -> float:
    total = sum(max(0.1, c["fin_s"] - c["debut_s"]) for c in candidats) or 1.0
    return round(min(FPS_MAX, max(FPS_MIN, BUDGET_IMAGES / total)), 2)


def _parts_par_candidat(video_file, candidats: list[dict]) -> list:
    """Un Part video par repetition candidate, borne par start/end_offset.

    Donner la segmentation par la structure de la requete plutot que par une phrase du
    prompt : le modele n'a plus a rattacher une portion de video a une repetition. Mesure
    sur conventionnal_deadlift_11, `eccentric_control_and_descent` passe de 1 a 2-4
    (mesure faite sur l'ancienne echelle 1-4 du schema)
    quand la phase de descente est dans le segment de sa propre repetition.
    """
    fps = _cadence_segments(candidats)
    return [
        types.Part(
            file_data=types.FileData(file_uri=video_file.uri,
                                     mime_type=video_file.mime_type),
            video_metadata=types.VideoMetadata(
                start_offset=f"{c['debut_s']:.2f}s",
                end_offset=f"{c['fin_s']:.2f}s",
                fps=fps),
        )
        for c in candidats
    ]


def _prompt_candidats(mouvement: str, candidats: list[dict], regle_plancher: str,
                      bloc_visibilite: str) -> str:
    """Le prompt du mode segments.

    La regle de la barre est la raison d'etre du dispositif : la pose voit le corps, pas
    la barre, et se redresser apres l'avoir reposee produit exactement le meme mouvement
    qu'une repetition. Le champ `bar_left_floor` est volontairement distinct de "NA" —
    "NA" repond a "est-ce que je VOIS ce critere", et confondre les deux supprimerait une
    vraie repetition filmee sous un mauvais angle.
    """
    lignes = "\n".join(
        f"          segment {k} — video part {k}, covering {c['debut_s']:.1f}s to "
        f"{c['fin_s']:.1f}s of the original clip (the athlete stands up at about "
        f"{c['lockout_s']:.1f}s)"
        for k, c in enumerate(candidats, 1))
    return f"""
        You are a brutally strict, elite IPF powerlifting judge and highly analytical biomechanics coach.
        The athlete executes a {mouvement.upper()}.

        WHAT YOU ARE GIVEN:
        You receive {len(candidats)} video segments, one per POSSIBLE repetition, in
        chronological order. Each segment was cut by pose tracking around a moment where
        the athlete stood up, and it covers that whole attempt: the pull, the lockout,
        and the phase that follows it.
{lignes}
        Fill `reps` with ONE ENTRY PER SEGMENT, in this order. Judge each segment using
        ONLY what that segment shows.

        GRADING RULE:
        {regle_plancher}A Score: "1" to "3", based strictly on the provided rubrics in the schema.
        "3" is the top of the scale and it means the criterion is MET, not that the
        execution is superlative: give it whenever level 3 of the rubric is satisfied.

        THE BAR RULE (this is why the segments exist):
        Pose tracking sees the body, not the bar. Standing up after LOWERING the bar to
        the floor, standing up EMPTY-HANDED, or straightening up while setting up produces
        exactly the same body movement as a repetition. You can see the bar; the tracker
        cannot. For each segment, set `bar_left_floor`:
          true  — the bar left the floor and was lifted to lockout. This is a real repetition.
          false — the bar stayed on the floor, or was already down and the athlete simply
                  stood back up. This is NOT a repetition.
        Judge each segment on its own. A false segment can occur anywhere — at the start
        during setup, in the middle on a camera cut, or at the end of the set. Do not
        assume it is the last one.
        When `bar_left_floor` is false, still return the entry, and set every criterion of
        that rep to "NA": the entry will be discarded.

        REP-BY-REP RULE:
        Score EVERY criterion on EVERY segment whose `bar_left_floor` is true, against the
        rubric of the field of the same name in the schema. Judge each rep on its own: if
        the third rep is worse than the first, its scores must be lower.
        `eccentric_control_and_descent` is judged on the lowering phase shown at the END of
        that same segment. Only then write the summary blocks — they carry no score of
        their own, the displayed score is computed from your per-rep scores.
{bloc_visibilite}        "NA" answers "could I SEE this criterion?". It never answers "was this a
        repetition?" — that question is `bar_left_floor`, and only that field removes an entry.
        """


def analyze_movement(file_name: str, mouvement_detecte: str,
                     modele_demande: str | None = None) -> dict:
    try:
        video_file = client.files.get(name=file_name)
        
        chosen_schema = schema_mapping.get(mouvement_detecte)
        if not chosen_schema:
            raise HTTPException(status_code=400, detail="Type de mouvement non reconnu pour l'analyse.")

        # Mesures de pose calculées à la détection. Elles ne sont plus injectées dans le
        # prompt — le modèle a maintenant un segment vidéo par répétition, ce qui lui
        # donne directement ce que ces chiffres résumaient — mais elles restent dans la
        # réponse renvoyée au front.
        kinematics = _take_kinematics(file_name)

        # Consigne mesuree, pas figee : elle plaque le modele au plancher (biais -0,78
        # sur les 49 clips etiquetes). SBD_NO_FLOOR_RULE=1 la retire pour comparer.
        regle_plancher = ("" if os.getenv("SBD_NO_FLOOR_RULE") == "1"
                          else "  1. Assume the default score of a rep is 1 (Poor)\n          2. ")

        bloc_visibilite = """
        CRITICAL VISIBILITY RULE (The "NA" Rule):
        If the camera angle, framing, lighting or video quality makes a specific
        criterion impossible to assess, output "NA" for that criterion and say in
        the feedback exactly what is not visible. Do not guess.
        "NA" means you could not SEE it, never that you saw it and disliked it:
        a flaw you can see is a low score, not "NA".
        Judge every other criterion normally; one "NA" must not drag the others down.
        """

        prompt_historique = f"""
        You are a brutally strict, elite IPF powerlifting judge and highly analytical biomechanics coach. 
        The athlete executes a {mouvement_detecte.upper()}.

        GRADING RULE:
        {regle_plancher}A Score: "1" to "3", based strictly on the provided rubrics in the schema.
        "3" is the top of the scale and it means the criterion is MET, not that the
        execution is superlative: give it whenever level 3 of the rubric is satisfied.

        REP-BY-REP RULE:
        The video contains a whole set. First count the repetitions, then fill
        `reps` with one entry per rep, in order, scoring EVERY criterion on EVERY
        rep. Judge each rep on its own: if the third rep is worse than the first,
        its scores must be lower. Only then write the summary blocks — they carry
        no score of their own, the displayed score is computed from your per-rep
        scores, so a criterion is only ever as good as the reps you scored.
        {bloc_visibilite}"""

        # Mode segments : un Part video par repetition candidate, borne par la pose.
        # Le modele n'a plus a deviner quelle portion de la video appartient a quelle
        # repetition, et il tranche pour chacune si la barre a decolle — ce que la pose
        # ne peut pas voir. Sans candidats (pose muette, squat, bench), on garde le
        # chemin historique.
        candidats = _reprend(_CANDIDATS_CACHE, file_name) or []
        mode_segments = bool(candidats) and "deadlift" in mouvement_detecte

        if mode_segments:
            contenus = _parts_par_candidat(video_file, candidats)
            contenus.append(_prompt_candidats(mouvement_detecte, candidats,
                                              regle_plancher, bloc_visibilite))
            resolution = types.MediaResolution.MEDIA_RESOLUTION_HIGH
        else:
            contenus = [video_file, prompt_historique]
            resolution = None

        model_analyse = MODELES_ANALYSE.get(modele_demande) or os.environ["MODEL_GEMINI"]
        modele_de_repli = None

        try:
            resultat = _run_analysis(
                model_analyse, contenus, chosen_schema, mouvement_detecte, resolution
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
            # Le repli repasse par le prompt historique, video entiere : mesure sur
            # deux clips, flash-lite ne suit pas le protocole des candidats. Il supprime
            # une entree au lieu de la marquer, et en invente une sur un clip a deux
            # candidats. Lui envoyer le prompt segmente donnerait des comptes faux
            # silencieusement.
            resultat = _run_analysis(
                modele_de_repli, [video_file, prompt_historique], chosen_schema,
                mouvement_detecte
            )
        
        # --- NOTATION PAR REP ---
        # Le modele ne note plus que des reps. Les notes de synthese affichees a
        # l'utilisateur sont calculees ici a partir de ces notes-la : c'est ce qui
        # garantit que l'histogramme des reps et la liste des criteres sous lui ne
        # peuvent pas raconter deux histoires differentes.
        criteres = criteres_de_synthese(chosen_schema)

        # Mode segments : le modele a tranche pour chaque candidat si la barre avait
        # decolle. Les candidats ecartes ne sont pas des repetitions ratees, ce sont des
        # mouvements de corps sans la barre — se relever apres l'avoir reposee, se
        # redresser pendant l'installation. On les retire avant toute notation, sinon ils
        # entrent dans la moyenne des criteres et dans l'histogramme.
        if mode_segments:
            brutes = resultat.get("reps") or []
            gardees = [r for r in brutes
                       if not isinstance(r, dict) or r.get("bar_left_floor", True)]
            if len(gardees) != len(brutes):
                logger.info("%d candidat(s) sur %d ecarte(s) : barre non decollee",
                            len(brutes) - len(gardees), len(brutes))
            resultat["reps"] = gardees
            resultat["rep_candidates"] = len(brutes)

        reps = _note_les_reps(resultat, criteres)
        if not reps:
            # Deux causes tres differentes derriere un set vide. Quand des candidats
            # existaient et ont tous ete ecartes, la barre n'a jamais quitte le sol :
            # c'est une tentative ratee, pas une panne, et le dire vaut mieux que
            # "reessaie" sur une video ou reessayer ne changera rien.
            if mode_segments and resultat.get("rep_candidates"):
                raise HTTPException(
                    status_code=422,
                    detail="Aucune répétition complète sur cette vidéo : la barre n'a "
                           "pas quitté le sol. Filme une série où le lift va jusqu'au "
                           "verrouillage.",
                )
            # Une page de huit "non visible" serait pire qu'une erreur franche.
            raise HTTPException(
                status_code=502,
                detail="Le modèle n'a rendu aucune répétition exploitable. Réessaie.",
            )
        resultat["reps"] = reps
        resultat["rep_count"] = len(reps)
        _agrege_les_criteres(resultat, criteres, reps)

        # `set_consistency` est le seul critere note directement par le modele :
        # il porte sur l'ecart ENTRE les reps, il n'a donc pas de version par rep.
        # Sur une video d'une seule rep, il n'y a rien a comparer : quoi qu'ait
        # repondu le modele, la note ne veut rien dire.
        consistance = resultat.get("set_consistency")
        if isinstance(consistance, dict):
            if len(reps) <= 1:
                consistance["score"] = "NA"
                consistance["feedback"] = (
                    "Only one rep in this video, so there is nothing to compare. "
                    "Film a full set and this one gets scored."
                )
            note = numeric_score(consistance.get("score"))
            consistance["score"] = note
            consistance["not_assessable"] = note is None

        # --- CALCUL DU SCORE ---
        # Les critères "NA" (non visibles à l'image) sortent du score : ils ne
        # comptent NI au numérateur NI au dénominateur.
        notes = [c["score"] for c in resultat.values()
                 if isinstance(c, dict) and c.get("score") is not None]
        score_total = sum(notes)
        nb_criteres_notes = len(notes)
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

        # Bloc de mesures rendu au client. Pas de clé "score" : il ne sera jamais pris
        # pour un critère, ni par la boucle de scoring ci-dessus ni par le front.
        if kinematics:
            resultat["kinematics"] = {k: v for k, v in kinematics.items()
                                      if not k.startswith("_")}
            resultat["kinematics"]["phases"] = kinematics.get("_phases", {})

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
