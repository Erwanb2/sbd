import os
import sqlite3
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
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 
SECRET_KEY = os.getenv("SECRET_KEY")

QUOTAS = {
    "free": 3,
    "premium": 50,
    "pro": 100
}

class PlanUpdateRequest(BaseModel):
    plan: str

class GoogleToken(BaseModel):
    token: str

class AnalyzeRequest(BaseModel):
    file_name: str
    movement: str

# ==========================================
# 🗄️ BASE DE DONNÉES (SQLite)
# ==========================================
def get_db_connection():
    """Ouvre une connexion à la base de données."""
    conn = sqlite3.connect("utilisateurs.db")
    conn.row_factory = sqlite3.Row # Permet d'utiliser les résultats comme des dictionnaires
    return conn

def init_db():
    """Crée la table des utilisateurs au démarrage de l'API s'il elle n'existe pas."""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            plan TEXT,
            uploads_today INTEGER,
            last_upload_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# On initialise la DB tout de suite
init_db()

def get_user(email: str):
    """Récupère un utilisateur dans la base."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def save_user(user: dict):
    """Insère un nouvel utilisateur ou met à jour s'il existe déjà."""
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO users (email, plan, uploads_today, last_upload_date)
        VALUES (:email, :plan, :uploads_today, :last_upload_date)
        ON CONFLICT(email) DO UPDATE SET
            plan=excluded.plan,
            uploads_today=excluded.uploads_today,
            last_upload_date=excluded.last_upload_date
    ''', user)
    conn.commit()
    conn.close()


# ==========================================
# 🔐 ROUTES D'AUTHENTIFICATION
# ==========================================
@app.post("/auth/google")
async def auth_google(body: GoogleToken):
    try:
        # 1. Vérification auprès de Google
        idinfo = id_token.verify_oauth2_token(body.token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']

        # 2. Création/Récupération de l'utilisateur dans SQLite
        user = get_user(email)
        
        if not user:
            # Nouvel utilisateur !
            user = {
                "email": email,
                "plan": "free",
                "uploads_today": 0,
                "last_upload_date": str(date.today())
            }
        
        # 3. Réinitialisation journalière du quota
        if user["last_upload_date"] != str(date.today()):
            user["uploads_today"] = 0
            user["last_upload_date"] = str(date.today())

        # On sauvegarde les changements (nouveau user ou reset de date)
        save_user(user)

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
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé. Connectez-vous.")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        
        # On va chercher le user dans la vraie DB
        user = get_user(email)
        
        # Si la base de données est vide ou l'utilisateur supprimé
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable. Veuillez vous reconnecter.")
            
        # Mise à jour du jour
        today_str = str(date.today())
        if user["last_upload_date"] != today_str:
            user["uploads_today"] = 0
            user["last_upload_date"] = today_str
            save_user(user) # On n'oublie pas de sauvegarder en base
            
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Session expirée, veuillez vous reconnecter")


# ==========================================
# 🚀 ROUTES EXISTANTES
# ==========================================
@app.put("/users/me/plan")
async def update_user_plan(request: PlanUpdateRequest, user: dict = Depends(get_current_user)):
    """Permet à l'utilisateur de changer d'abonnement"""
    if request.plan not in QUOTAS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    # Mise à jour en base de données
    user["plan"] = request.plan
    save_user(user)
    
    quota_left = max(0, QUOTAS[user["plan"]] - user["uploads_today"])
    
    return {
        "message": "Plan mis à jour avec succès",
        "plan": user["plan"],
        "quota_left": quota_left
    }


@app.post("/detect")
async def detect_video(video: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if user["uploads_today"] >= QUOTAS[user["plan"]]:
        raise HTTPException(status_code=403, detail="Quota journalier atteint ! Revenez demain ou passez Premium.")
        
    # On retire un crédit et on SAUVEGARDE en base de données !
    user["uploads_today"] += 1
    save_user(user)
    
    temp_file_path = f"temp_{video.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await video.read())

    try:
        result = detect_movement(temp_file_path)
        result["quota_restant"] = QUOTAS[user["plan"]] - user["uploads_today"]
        return result
        
    except HTTPException:
        # En cas d'erreur IA, on rembourse le crédit en base de données
        user["uploads_today"] -= 1
        save_user(user)
        raise
    except Exception as e:
        user["uploads_today"] -= 1
        save_user(user)
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@app.post("/analyze")
async def analyze_video(request: AnalyzeRequest, user: dict = Depends(get_current_user)):
    try:
        return analyze_movement(request.file_name, request.movement)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")