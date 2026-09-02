import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel
from sqlmodel import Session

from ai_service import (
    analyze_movement,
    probe_video_duration_seconds,
    upload_and_detect_concurrent,
)
from database import (
    create_pending_analysis,
    get_or_create_user,
    get_pending_analysis,
    get_session,
    get_user_fresh,
    init_db,
    mark_pending_claimed,
    purge_expired_pending,
    refund_quota,
    save_pending_result,
    try_consume_quota,
    update_plan,
)

app = FastAPI(title="SBD Reviews API")

# --- CORS -------------------------------------------------------------------
# Le front et l'API sont servis derrière le même domaine via Caddy, donc en
# prod aucune requête n'est réellement "cross-origin". On garde quand même une
# liste blanche explicite (dev local + domaine) pilotée par la variable
# d'environnement CORS_ORIGINS (séparée par des virgules).
# On n'utilise PAS allow_credentials : l'auth passe par un header Bearer, pas
# par un cookie -> inutile, et incompatible avec un wildcard "*".
_default_origins = "http://localhost:5173,http://localhost:3000"
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Config ----------------------------------------------------------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY manquant dans l'environnement.")

JWT_ALGORITHM = "HS256"
JWT_TTL = timedelta(days=int(os.getenv("JWT_TTL_DAYS", "7")))

QUOTAS = {"free": 3, "premium": 50, "pro": 100}

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_DURATION_SECONDS = int(os.getenv("MAX_VIDEO_SECONDS", "60"))

# Durée de vie d'une analyse calculée mais pas encore réclamée.
PENDING_TTL_HOURS = int(os.getenv("PENDING_ANALYSIS_TTL_HOURS", "6"))


class PlanUpdateRequest(BaseModel):
    plan: str


class GoogleToken(BaseModel):
    token: str


class AnalyzeRequest(BaseModel):
    file_name: str
    movement: str


class ClaimRequest(BaseModel):
    claim_token: str


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/config")
def get_config():
    """Limites exposées au front pour qu'il puisse les afficher / pré-valider."""
    return {
        "max_upload_mb": MAX_UPLOAD_MB,
        "max_video_seconds": MAX_DURATION_SECONDS,
    }


def _issue_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": email, "iat": now, "exp": now + JWT_TTL},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


@app.post("/auth/google")
async def auth_google(body: GoogleToken, session: Session = Depends(get_session)):
    try:
        idinfo = id_token.verify_oauth2_token(
            body.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo["email"]
    except ValueError:
        raise HTTPException(status_code=401, detail="Token Google invalide")

    user = get_or_create_user(session, email)
    user = get_user_fresh(session, email)  # remet uploads_today à 0 si nouveau jour

    quota_left = max(0, QUOTAS[user.plan] - user.uploads_today)
    return {
        "access_token": _issue_token(email),
        "user": {"email": email, "plan": user.plan, "quota_left": quota_left},
    }


def get_current_user(
    authorization: str = Header(None),
    session: Session = Depends(get_session),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé. Connectez-vous.")

    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expirée, reconnectez-vous.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Session invalide, reconnectez-vous.")

    email = payload.get("sub")
    user = get_user_fresh(session, email)
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable.")
    return user


@app.put("/users/me/plan")
async def update_user_plan(
    request: PlanUpdateRequest,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if request.plan not in QUOTAS:
        raise HTTPException(status_code=400, detail="Plan invalide")

    user = update_plan(session, user.email, request.plan)
    quota_left = max(0, QUOTAS[user.plan] - user.uploads_today)
    return {
        "message": "Plan mis à jour avec succès",
        "plan": user.plan,
        "quota_left": quota_left,
    }


async def _save_upload_to_temp(video: UploadFile) -> str:
    """Écrit l'upload sur disque en refusant tout dépassement de taille."""
    safe_name = f"temp_{uuid.uuid4().hex}_{os.path.basename(video.filename or 'video')}"
    temp_path = os.path.join("/tmp", safe_name)

    size = 0
    with open(temp_path, "wb") as buffer:
        while chunk := await video.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                buffer.close()
                os.remove(temp_path)
                raise HTTPException(
                    status_code=413,
                    detail=f"Vidéo trop lourde (max {MAX_UPLOAD_MB} Mo).",
                )
            buffer.write(chunk)
    return temp_path


@app.post("/upload_and_detect")
async def detect_video(
    video: UploadFile = File(...),
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    temp_file_path = await _save_upload_to_temp(video)

    try:
        # 1. Validation locale AVANT de consommer le quota / d'appeler Gemini.
        duration = probe_video_duration_seconds(temp_file_path)
        if duration is None:
            raise HTTPException(
                status_code=400,
                detail="Impossible de lire la vidéo (fichier corrompu ou format non supporté).",
            )
        if duration > MAX_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Vidéo trop longue ({duration:.0f}s). "
                    f"Maximum {MAX_DURATION_SECONDS}s : filme une seule série."
                ),
            )

        # 2. Consommation atomique du quota.
        if not try_consume_quota(session, user.email, QUOTAS[user.plan]):
            raise HTTPException(
                status_code=403,
                detail="Quota journalier atteint ! Revenez demain ou passez Premium.",
            )

        # 3. Analyse (upload Google + détection en parallèle).
        try:
            result = upload_and_detect_concurrent(temp_file_path)
        except Exception:
            refund_quota(session, user.email)
            raise

        user = get_user_fresh(session, user.email)
        result["quota_restant"] = max(0, QUOTAS[user.plan] - user.uploads_today)
        return result

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/analyze")
async def analyze_video(request: AnalyzeRequest, user=Depends(get_current_user)):
    return analyze_movement(request.file_name, request.movement)


# --- Parcours anonyme --------------------------------------------------------
# Le visiteur lance l'analyse SANS être connecté : on calcule le résultat, on le
# garde côté serveur, et on ne le lui rend qu'une fois qu'il s'est authentifié
# (/analysis/claim). Il voit donc sa propre analyse tourner avant de créer un
# compte, ce qui est bien plus convaincant qu'un mur de connexion à l'entrée.
#
# Aucune limite par IP pour l'instant : choix assumé tant que l'app est gratuite
# sur les premiers essais. `PendingAnalysis.client_ip` est renseigné pour qu'on
# puisse en poser une plus tard sans migration.


def _client_ip(request: Request) -> str | None:
    """IP réelle du client, en tenant compte du reverse proxy Caddy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@app.post("/anonymous/upload_and_detect")
async def anonymous_upload_and_detect(
    request: Request,
    video: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    temp_file_path = await _save_upload_to_temp(video)

    try:
        duration = probe_video_duration_seconds(temp_file_path)
        if duration is None:
            raise HTTPException(
                status_code=400,
                detail="Impossible de lire la vidéo (fichier corrompu ou format non supporté).",
            )
        if duration > MAX_DURATION_SECONDS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Vidéo trop longue ({duration:.0f}s). "
                    f"Maximum {MAX_DURATION_SECONDS}s : filme une seule série."
                ),
            )

        detection = upload_and_detect_concurrent(temp_file_path)

        purge_expired_pending(session, PENDING_TTL_HOURS)
        token = uuid.uuid4().hex
        create_pending_analysis(
            session,
            token=token,
            gemini_file_name=detection["file_name"],
            movement=detection["mouvement_detecte"],
            client_ip=_client_ip(request),
        )

        # On ne renvoie que le mouvement détecté : de quoi animer l'écran de
        # chargement, sans rien dévoiler de la note.
        return {
            "claim_token": token,
            "mouvement_detecte": detection["mouvement_detecte"],
        }

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/anonymous/analyze")
async def anonymous_analyze(body: ClaimRequest, session: Session = Depends(get_session)):
    pending = get_pending_analysis(session, body.claim_token)
    if pending is None:
        raise HTTPException(
            status_code=404, detail="Analyse introuvable ou expirée. Relance l'upload."
        )

    # Le nom du fichier Gemini vient de la base, jamais du client : impossible
    # de faire analyser une vidéo arbitraire déjà uploadée par quelqu'un d'autre.
    if pending.result_json is None:
        resultat = analyze_movement(pending.gemini_file_name, pending.movement)
        save_pending_result(session, pending.token, json.dumps(resultat))

    return {"ready": True}


@app.post("/analysis/claim")
async def claim_analysis(
    body: ClaimRequest,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    pending = get_pending_analysis(session, body.claim_token)
    if pending is None or pending.result_json is None:
        raise HTTPException(
            status_code=404, detail="Analyse introuvable ou expirée. Relance l'upload."
        )

    resultat = json.loads(pending.result_json)

    def _with_quota() -> dict:
        fresh = get_user_fresh(session, user.email)
        resultat["quota_restant"] = max(0, QUOTAS[fresh.plan] - fresh.uploads_today)
        return resultat

    # Déjà réclamée par ce même utilisateur (refresh, double-clic) : on rend le
    # résultat sans reprélever de crédit.
    if pending.claimed_by == user.email:
        return _with_quota()

    if pending.claimed_by is not None:
        raise HTTPException(status_code=409, detail="Cette analyse a déjà été réclamée.")

    if not try_consume_quota(session, user.email, QUOTAS[user.plan]):
        raise HTTPException(
            status_code=403,
            detail="Quota journalier atteint ! Revenez demain ou passez Premium.",
        )

    mark_pending_claimed(session, pending.token, user.email)
    return _with_quota()
