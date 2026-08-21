import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import jwt
from datetime import date

from ai_service import detect_movement, analyze_movement

app = FastAPI(title="SBD Reviews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# ⚙️ CONFIGURATION AUTHENTIFICATION & QUOTAS
# ==========================================
# À remplacer par l'ID que tu obtiendras sur Google Cloud Console
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 
# Clé secrète pour générer tes propres tokens (mets une phrase au hasard très longue)
SECRET_KEY = os.getenv("SECRET_KEY")

QUOTAS = {
    "free": 3,
    "pro": 50
}

# Fausse base de données en mémoire (remplacera par SQLAlchemy/Postgres plus tard)
fake_db_users = {}

class GoogleToken(BaseModel):
    token: str

class AnalyzeRequest(BaseModel):
    file_name: str
    movement: str


# ==========================================
# 🔐 ROUTES D'AUTHENTIFICATION
# ==========================================
@app.post("/auth/google")
async def auth_google(body: GoogleToken):
    """Reçoit le token Google du frontend, le vérifie, et renvoie un token API."""
    try:
        # 1. Vérification auprès de Google
        idinfo = id_token.verify_oauth2_token(body.token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']

        # 2. Création/Récupération de l'utilisateur
        if email not in fake_db_users:
            fake_db_users[email] = {
                "email": email,
                "plan": "free", # free par défaut
                "uploads_today": 0,
                "last_upload_date": str(date.today())
            }
        
        user = fake_db_users[email]
        
        # 3. Réinitialisation journalière invisible du quota
        if user["last_upload_date"] != str(date.today()):
            user["uploads_today"] = 0
            user["last_upload_date"] = str(date.today())

        # 4. Génération d'un token propre à TON application
        access_token = jwt.encode({"sub": email}, SECRET_KEY, algorithm="HS256")
        quota_left = QUOTAS[user["plan"]] - user["uploads_today"]

        return {
            "access_token": access_token,
            "user": {"email": email, "plan": user["plan"], "quota_left": quota_left}
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="Token Google invalide")


# ==========================================
# 🛡️ DÉPENDANCE DE SÉCURITÉ (Middleware)
# ==========================================
def get_current_user(authorization: str = Header(None)):
    """Vérifie le token JWT et retourne l'utilisateur."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé. Connectez-vous.")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        user = fake_db_users.get(email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
            
        # Mise à jour du jour (au cas où il reste connecté la nuit)
        today_str = str(date.today())
        if user["last_upload_date"] != today_str:
            user["uploads_today"] = 0
            user["last_upload_date"] = today_str
            
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Session expirée, veuillez vous reconnecter")


# ==========================================
# 🚀 ROUTES EXISTANTES (Désormais protégées)
# ==========================================
@app.post("/detect")
async def detect_video(video: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Étape 1 : Upload, détection, ET consommation du quota."""
    
    # 1. Vérification du quota AVANT de faire quoi que ce soit
    if user["uploads_today"] >= QUOTAS[user["plan"]]:
        raise HTTPException(status_code=403, detail="Quota journalier atteint ! Revenez demain ou passez Pro.")
        
    # 2. On retire un crédit
    user["uploads_today"] += 1
    
    temp_file_path = f"temp_{video.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await video.read())

    try:
        result = detect_movement(temp_file_path)
        # On peut renvoyer le quota mis à jour au frontend si besoin
        result["quota_restant"] = QUOTAS[user["plan"]] - user["uploads_today"]
        return result
        
    except HTTPException:
        # En cas d'erreur de la part de l'API, on rembourse le crédit !
        user["uploads_today"] -= 1
        raise
    except Exception as e:
        user["uploads_today"] -= 1
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/analyze")
async def analyze_video(request: AnalyzeRequest, user: dict = Depends(get_current_user)):
    """Étape 2 : Analyse. (Pas besoin de re-vérifier le quota ici)"""
    try:
        return analyze_movement(request.file_name, request.movement)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")