"""Orchestration : upload, classification, pose, puis analyse par le modele.

Ce fichier ne decide plus rien. Il transporte :

    la video  -> MediaPipe (pose_analysis) -> mesures par repetition
              -> Gemini    (schemas)       -> observations par repetition
                                           -> rules.evalue -> la page

Le partage des taches entre les deux est declare dans `indicators.py`, la notation dans
`rules.py`. Ici il n'y a que de la plomberie : des futures, des timeouts, un cache entre
les deux requetes du front, et le decoupage de la video en segments.

**Souleve de terre uniquement.** Le squat et le developpe couche ne sont pas portes sur
ce noyau : leur catalogue d'indicateurs reste a ecrire. Ils sont refuses explicitement
plutot que notes avec un bareme de deadlift.
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
import time

import cv2
from fastapi import HTTPException
from google import genai
from google.genai import types
from PIL import Image

import pose_analysis
import rules
from pricing import log_usage
from schemas import SCHEMAS, VideoClassification

client = genai.Client()
logger = logging.getLogger(__name__)

# Delais de garde : ne jamais rester bloque indefiniment.
GOOGLE_PROCESSING_TIMEOUT = int(os.getenv("GEMINI_PROCESSING_TIMEOUT", "180"))
GOOGLE_UPLOAD_FUTURE_TIMEOUT = GOOGLE_PROCESSING_TIMEOUT + 30
GOOGLE_DETECT_FUTURE_TIMEOUT = int(os.getenv("GEMINI_DETECT_TIMEOUT", "120"))
POSE_FUTURE_TIMEOUT = int(os.getenv("POSE_TIMEOUT", "90"))

MODEL_CLASSIFICATION = os.getenv("MODEL_GEMINI_CLASSIFICATION", "gemini-3.5-flash-lite")
MODEL_ANALYSIS_FALLBACK = os.getenv("MODEL_GEMINI_FALLBACK", "gemini-3.5-flash-lite")

# Le front envoie une cle, jamais un nom de modele : sinon n'importe qui pourrait faire
# tourner le modele le plus cher.
MODELES_ANALYSE = {"3.5": "gemini-3.5-flash", "3.7": "gemini-3.7-flash"}

# Budget d'images du mode segments. La cadence est deduite de la duree totale des
# segments plutot que fixee : sinon une serie de dix reps coute dix fois une serie d'une.
# Bornes pour qu'un clip tres court ne parte pas a 60 im/s et qu'un clip long ne tombe
# pas sous la cadence ou un verrouillage bref passe entre deux images.
#
# 24 im/s est le plafond de l'API (30 refuse). C'est la cadence de la run A du
# 2026-09-11 (`eval/runs/pr_160_A_video24.json`), la configuration que la prod doit
# reproduire : c'est a cette cadence que le modele a vu un depart arrache — "the high
# frame rate allows us to see the suddenness of the start". Le budget de 720 images
# couvre 30 s de repetitions a pleine cadence (4-5 reps) ; au-dela la cadence baisse.
# Cout : ~265 tokens par image en HIGH, soit ~190 k tokens d'entree au plafond du budget,
# environ 0,30 $ sur gemini-3.5-flash.
BUDGET_IMAGES = 720
FPS_MIN, FPS_MAX = 2.0, 24.0

_POSE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=2)


# --------------------------------------------------------------------------- video

def probe_video_duration_seconds(file_path: str):
    cap = cv2.VideoCapture(file_path)
    try:
        n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
    finally:
        cap.release()
    return (n / fps) if (n and fps) else None


def extraire_images(file_path: str, num_images: int = 10) -> list:
    """Quelques images uniformes, pour la classification de la famille du mouvement."""
    cap = cv2.VideoCapture(file_path)
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total <= 0:
            return []
        pas = max(1, total // num_images)
        images, i = [], 0
        while len(images) < num_images:
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(i, total - 1))
            ok, frame = cap.read()
            if not ok:
                break
            images.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            i += pas
            if i >= total:
                break
        return images
    finally:
        cap.release()


# ------------------------------------------------------------- taches paralleles

def _task_classification(file_path: str) -> str:
    """La FAMILLE du mouvement, et elle seule.

    La variante sumo/conventionnel n'est plus demandee au modele : la cascade de pose
    fait 39/39 la ou il se trompe.
    """
    images = extraire_images(file_path)
    if not images:
        raise ValueError("Impossible de lire la video. Fichier potentiellement corrompu.")

    reponse = client.chats.create(
        model=MODEL_CLASSIFICATION,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoClassification,
            temperature=0.0),
    ).send_message(message=[*images, """
        Based on these images, classify the exercise into one of:
            - squat
            - bench press
            - deadlift
            - unworkable_video (if none of the above, or unclear)
        Answer with the movement family only. Do not try to tell sumo from conventional.
    """])
    log_usage(model=MODEL_CLASSIFICATION, response=reponse, label="classification",
              extra=f"{len(images)} images")

    mouvement = (reponse.parsed.mouvement_detecte or "").strip().lower()
    for famille in ("deadlift", "bench", "squat"):
        if famille in mouvement:
            return "bench press" if famille == "bench" else famille
    raise ValueError("Video inexploitable. Merci d'envoyer un deadlift clair.")


def _task_upload(file_path: str):
    """Upload chez Google, avec un timeout dur sur le processing."""
    video_file = client.files.upload(file=file_path)
    limite = time.monotonic() + GOOGLE_PROCESSING_TIMEOUT
    while video_file.state.name == "PROCESSING":
        if time.monotonic() > limite:
            raise TimeoutError("Google n'a pas fini de traiter la video.")
        time.sleep(1)
        video_file = client.files.get(name=video_file.name)
    if video_file.state.name == "FAILED":
        raise ValueError("Google n'a pas pu traiter cette video.")
    return video_file


# Les mesures de pose sont calculees a l'upload et relues a l'analyse, qui est une
# seconde requete du front. Cache en memoire, borne : le processus est mono-instance.
_POSE_CACHE: dict[str, dict] = {}
_CACHE_MAX = 64


def _memorise(file_name: str, pose: dict) -> None:
    if len(_POSE_CACHE) >= _CACHE_MAX:
        _POSE_CACHE.pop(next(iter(_POSE_CACHE)), None)
    _POSE_CACHE[file_name] = pose


def upload_and_detect_concurrent(file_path: str) -> dict:
    """Upload, classification et pose en parallele. Rend de quoi lancer l'analyse."""
    future_pose = _POSE_EXECUTOR.submit(pose_analysis.analyse, file_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_classif = executor.submit(_task_classification, file_path)
        future_upload = executor.submit(_task_upload, file_path)

        try:
            famille = future_classif.result(timeout=GOOGLE_DETECT_FUTURE_TIMEOUT)
        except concurrent.futures.TimeoutError:
            _nettoie(future_upload)
            raise HTTPException(status_code=504,
                                detail="La detection du mouvement a expire. Reessaie.")
        except Exception as exc:
            _nettoie(future_upload)
            raise HTTPException(status_code=400, detail=str(exc))

        if famille != "deadlift":
            _nettoie(future_upload)
            raise HTTPException(
                status_code=400,
                detail="Seul le souleve de terre est analyse pour l'instant.")

        try:
            video_file = future_upload.result(timeout=GOOGLE_UPLOAD_FUTURE_TIMEOUT)
        except concurrent.futures.TimeoutError:
            raise HTTPException(status_code=504, detail="L'upload de la video a expire.")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    try:
        pose = future_pose.result(timeout=POSE_FUTURE_TIMEOUT)
    except Exception as exc:
        logger.warning("pose indisponible : %s", exc)
        pose = {"ok": False, "raison": str(exc)}

    if not pose.get("ok"):
        # Sans pose il n'y a ni variante, ni segments, ni mesures : les trois entrees du
        # systeme. Mieux vaut le dire que rendre une analyse dont on sait qu'elle est
        # amputee. Le repli "variante par le modele" de l'ancienne version ne suffit plus.
        raise HTTPException(
            status_code=422,
            detail="Video non exploitable par l'analyse de pose : "
                   f"{pose.get('raison', 'raison inconnue')}. Refilme de profil, "
                   "corps entier dans le cadre.")

    _memorise(video_file.name, pose)
    logger.info("variante %s (regle %s), vue %s, %d repetition(s) candidate(s)",
                pose["variante"], pose["regle"], pose["view"], len(pose["reps"]))

    return {
        "file_name": video_file.name,
        "mouvement_detecte": f"{pose['variante']} deadlift",
        # `reps` et `squelette` ne servent qu'a `analyze_movement` (repli sur le cache) et
        # a l'overlay du resultat final : les taire ici evite de doubler leur poids dans
        # cette premiere reponse, qui n'anime que l'ecran de chargement.
        "pose": {k: v for k, v in pose.items() if k not in ("reps", "squelette")},
        "nb_candidats": len(pose["reps"]),
    }


def _nettoie(future_upload) -> None:
    """Supprime chez Google un fichier dont l'analyse ne partira jamais."""
    try:
        client.files.delete(name=future_upload.result(timeout=5).name)
    except Exception:
        pass


# ------------------------------------------------------------------- analyse

def _cadence(reps: list[dict]) -> float:
    total = sum(max(0.1, r["fin_s"] - r["debut_s"]) for r in reps) or 1.0
    return round(min(FPS_MAX, max(FPS_MIN, BUDGET_IMAGES / total)), 2)


def _segments(video_file, reps: list[dict]) -> list:
    """Un Part video par repetition candidate, borne par start/end_offset.

    La segmentation est donnee par la STRUCTURE de la requete, pas par une phrase du
    prompt : le modele n'a plus a rattacher une portion de video a une repetition.
    """
    fps = _cadence(reps)
    return [types.Part(
        file_data=types.FileData(file_uri=video_file.uri, mime_type=video_file.mime_type),
        video_metadata=types.VideoMetadata(start_offset=f"{r['debut_s']:.2f}s",
                                           end_offset=f"{r['fin_s']:.2f}s", fps=fps),
    ) for r in reps]


def _prompt(variante: str, n: int) -> str:
    """Le prompt. Court, parce que le schema porte deja toutes les consignes.

    Aucune regle de notation ici : le modele ne note pas. Aucune regle "NA" non plus :
    chaque champ porte son propre etat `not_visible`.
    """
    return f"""You are an elite powerlifting coach watching a {variante.upper()} DEADLIFT.

You are given {n} video segments, in chronological order. Each segment is ONE candidate
repetition.

Fill `reps` with exactly {n} entries, one per segment, in the same order.

Each field offers a closed list of things that can be seen: pick the one that matches this segment.

`bar_left_floor` - The segment detector cannot tell a repetition from an athlete standing up.
Look at the bar and the plates:
  - 'yes'        : the bar left the floor and was lifted.
  - 'no'         : the bar never left the floor, or was already down. Not a repetition.
  - 'incomplete' : the bar left the floor but came back down before lockout.
Return the entry either way, with every other field filled as best you can.

When something genuinely cannot be seen, use 'not_visible' for that field alone."""


# Les reglages de l'appel d'analyse, tous au plafond, identiques a la run A du
# 2026-09-11. Exposes dans `debug` pour que la page dise avec quoi elle a ete produite.
REGLAGES_ANALYSE = {"media_resolution": "HIGH", "thinking_level": "HIGH", "temperature": 0.0}


def _appelle(modele: str, contenus: list, schema, label: str):
    """L'appel d'analyse, et le detail de ce qu'il a coute (`pricing.log_usage`)."""
    reponse = client.models.generate_content(
        model=modele, contents=contenus,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=schema,
            temperature=REGLAGES_ANALYSE["temperature"],
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
            # Raisonnement au plafond. Le repli flash-lite l'accepte aussi (verifie par
            # un appel texte le 2026-09-11). `include_thoughts` ne change ni le
            # raisonnement ni la facture (les tokens de pensee sont deja comptes en
            # sortie) : il fait seulement revenir le texte des pensees, pour l'onglet debug.
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.HIGH,
                                                 include_thoughts=True)),
    )
    usage = log_usage(model=modele, response=reponse, label=label)
    return reponse, usage


def _pensees(reponse) -> str | None:
    """Le texte des pensees du modele, tel que l'API le renvoie (brut ou resume selon le
    modele). Genere AVANT le JSON, sans contrainte de forme — mais apres lecture du
    schema, qui fait partie de l'entree."""
    try:
        parts = reponse.candidates[0].content.parts or []
    except (AttributeError, IndexError, TypeError):
        return None
    textes = [p.text for p in parts if getattr(p, "thought", False) and p.text]
    return "\n\n".join(textes) or None


def _usage_public(usage: dict | None) -> dict | None:
    """Les tokens et le cout d'un appel, sans les grilles tarifaires internes."""
    if not usage:
        return None
    cles = ("prompt_tokens", "thoughts_tokens", "candidates_tokens", "total_tokens",
            "input_usd", "output_usd", "total_usd")
    return {k: (round(v, 4) if isinstance(v, float) else v)
            for k, v in usage.items() if k in cles}


def _sature(exc: Exception) -> bool:
    """Vrai si l'echec vient de la saturation du modele, pas de notre requete."""
    if getattr(exc, "code", None) == 503:
        return True
    if getattr(exc, "status", None) == "UNAVAILABLE":
        return True
    return "503" in str(exc) or "UNAVAILABLE" in str(exc)


def analyze_movement(file_name: str, mouvement_detecte: str,
                     modele_demande: str | None = None) -> dict:
    """L'analyse complete d'une serie : observations du modele, puis notation Python."""
    pose = _POSE_CACHE.get(file_name)
    if not pose:
        raise HTTPException(status_code=409,
                            detail="Mesures de pose introuvables. Renvoie la video.")

    variante = pose["variante"]
    schema = SCHEMAS.get(variante)
    candidats = pose.get("reps") or []
    if not candidats:
        raise HTTPException(status_code=422,
                            detail="Aucune repetition detectee dans cette video.")

    modele = MODELES_ANALYSE.get(modele_demande or "", MODELES_ANALYSE["3.5"])
    try:
        video_file = client.files.get(name=file_name)
        segments = _segments(video_file, candidats)
        prompt = _prompt(variante, len(candidats))
        contenus = [*segments, prompt]

        repli = None
        try:
            reponse, usage = _appelle(modele, contenus, schema, f"analyse {variante}")
        except Exception as exc:
            if not _sature(exc):
                raise
            # Repli mesure comme moins fiable sur ce protocole : flash-lite supprime
            # parfois une entree au lieu de la marquer 'non', et invente des reps.
            # `rules` realigne sur `rep_index`, mais le resultat reste degrade : on le dit.
            logger.warning("modele sature, repli sur %s", MODEL_ANALYSIS_FALLBACK)
            repli = MODEL_ANALYSIS_FALLBACK
            reponse, usage = _appelle(repli, contenus, schema, f"analyse {variante} (repli)")

        observations = reponse.parsed.model_dump(mode="json")
        resultat = rules.evalue(pose, observations)
        resultat["modele"] = repli or modele
        # Tout ce qui a produit la reponse, pour l'onglet debug : le modele, les
        # reglages, les fenetres envoyees, le prompt, et ce que l'appel a coute.
        resultat["debug"]["appel"] = {
            "modele": repli or modele, "repli": repli is not None,
            **REGLAGES_ANALYSE, "fps": segments[0].video_metadata.fps,
            "segments": [{"debut_s": c["debut_s"], "fin_s": c["fin_s"]} for c in candidats],
            "prompt": prompt,
            "pensees": _pensees(reponse),
            "usage": _usage_public(usage),
        }
        if repli:
            resultat["avertissement"] = ("Modele principal sature : analyse produite par "
                                         "un modele de repli, moins fiable sur le "
                                         "decoupage en repetitions.")
        if not resultat["reps"]:
            raise HTTPException(
                status_code=422,
                detail="Aucune repetition retenue : le modele n'a vu la barre quitter le "
                       "sol sur aucun des segments proposes.")
        return resultat
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("analyse impossible")
        raise HTTPException(status_code=502, detail=f"Analyse impossible : {exc}")
