import os
import sqlite3
from datetime import date

import jwt

# NOUVEL IMPORT : On importe notre fonction optimisée
from ai_service import analyze_movement, upload_and_detect_concurrent
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel

app = FastAPI(title="SBD Reviews API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def get_db_connection():
    conn = sqlite3.connect("utilisateurs.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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

init_db()

def get_user(email: str):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def save_user(user: dict):
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


@app.post("/auth/google")
async def auth_google(body: GoogleToken):
    try:
        idinfo = id_token.verify_oauth2_token(body.token, google_requests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo['email']

        user = get_user(email)
        
        if not user:
            user = {
                "email": email,
                "plan": "free",
                "uploads_today": 0,
                "last_upload_date": str(date.today())
            }
        
        if user["last_upload_date"] != str(date.today()):
            user["uploads_today"] = 0
            user["last_upload_date"] = str(date.today())

        save_user(user)

        access_token = jwt.encode({"sub": email}, SECRET_KEY, algorithm="HS256")
        quota_left = QUOTAS[user["plan"]] - user["uploads_today"]

        return {
            "access_token": access_token,
            "user": {"email": email, "plan": user["plan"], "quota_left": quota_left}
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="Token Google invalide")


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Non autorisé. Connectez-vous.")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        
        user = get_user(email)
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable.")
            
        today_str = str(date.today())
        if user["last_upload_date"] != today_str:
            user["uploads_today"] = 0
            user["last_upload_date"] = today_str
            save_user(user)
            
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Session expirée, reconnectez-vous")


@app.put("/users/me/plan")
async def update_user_plan(request: PlanUpdateRequest, user: dict = Depends(get_current_user)):
    if request.plan not in QUOTAS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    user["plan"] = request.plan
    save_user(user)
    
    quota_left = max(0, QUOTAS[user["plan"]] - user["uploads_today"])
    return {
        "message": "Plan mis à jour avec succès",
        "plan": user["plan"],
        "quota_left": quota_left
    }


# LA ROUTE RENOMMÉE POUR MATCHER TON REACT :
@app.post("/upload_and_detect")
async def detect_video(video: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if user["uploads_today"] >= QUOTAS[user["plan"]]:
        raise HTTPException(status_code=403, detail="Quota journalier atteint ! Revenez demain ou passez Premium.")
        
    user["uploads_today"] += 1
    save_user(user)
    
    temp_file_path = f"temp_{video.filename}"
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await video.read())

    try:
        # On appelle la nouvelle fonction qui tourne en parallèle !
        result = upload_and_detect_concurrent(temp_file_path)
        result["quota_restant"] = QUOTAS[user["plan"]] - user["uploads_today"]
        return result
        
    except HTTPException:
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