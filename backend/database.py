"""
Couche d'accès aux données.

On passe du SQL brut éparpillé dans main.py à un modèle SQLModel unique
(`User`) + quelques fonctions de repository. SQLite reste le moteur, mais :
  - le schéma est décrit une seule fois, en Python typé ;
  - la consommation de quota est ATOMIQUE (plus de race read-modify-write) ;
  - le fichier .db vit dans ./data (monté en volume Docker), pas dans le code.
"""

import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine, delete

# --- Emplacement du fichier SQLite -------------------------------------------
# DATABASE_URL peut surcharger (tests, Postgres un jour...). Par défaut :
# backend/data/utilisateurs.db -> monté en volume nommé côté Docker.
_DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "utilisateurs.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_DEFAULT_DB_PATH}")

if DATABASE_URL.startswith("sqlite:///"):
    Path(DATABASE_URL.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)


class User(SQLModel, table=True):
    __tablename__ = "users"

    email: str = Field(primary_key=True)
    plan: str = Field(default="free")
    uploads_today: int = Field(default=0)
    last_upload_date: str = Field(default_factory=lambda: date.today().isoformat())
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PendingAnalysis(SQLModel, table=True):
    """
    Analyse lancée AVANT que le visiteur ne soit connecté.

    Le résultat est calculé puis conservé ici, et n'est renvoyé au client qu'au
    moment du `claim` (authentifié) : sans ça, n'importe qui lirait la note dans
    l'onglet réseau sans jamais créer de compte.

    `created_at` est une chaîne ISO 8601 UTC (et pas un datetime) pour rester
    cohérent avec `User.last_upload_date` et pour que la purge se fasse par
    simple comparaison lexicographique, sans histoire de fuseau côté SQLite.
    """

    __tablename__ = "pending_analyses"

    token: str = Field(primary_key=True)
    gemini_file_name: str
    movement: str
    result_json: Optional[str] = Field(default=None)
    # Conservé à titre informatif : aucune limite par IP aujourd'hui, mais la
    # donnée est là si l'app décolle et qu'il faut en poser une.
    client_ip: Optional[str] = Field(default=None)
    claimed_by: Optional[str] = Field(default=None)
    created_at: str = Field(default_factory=_utc_now_iso)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dépendance FastAPI : une session par requête."""
    with Session(engine) as session:
        yield session


# --- Repository -------------------------------------------------------------

def get_user(session: Session, email: str) -> Optional[User]:
    return session.get(User, email)


def get_or_create_user(session: Session, email: str) -> User:
    user = session.get(User, email)
    if user is None:
        user = User(email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def _reset_if_new_day(session: Session, user: User) -> User:
    today = date.today().isoformat()
    if user.last_upload_date != today:
        user.uploads_today = 0
        user.last_upload_date = today
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def get_user_fresh(session: Session, email: str) -> Optional[User]:
    """Récupère l'utilisateur avec le compteur du jour remis à zéro si besoin."""
    user = session.get(User, email)
    if user is None:
        return None
    return _reset_if_new_day(session, user)


def update_plan(session: Session, email: str, plan: str) -> User:
    user = session.get(User, email)
    user.plan = plan
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def try_consume_quota(session: Session, email: str, daily_limit: int) -> bool:
    """
    Incrémente `uploads_today` de façon atomique SI le quota n'est pas atteint.

    Un seul UPDATE conditionnel => deux uploads simultanés ne peuvent pas
    passer tous les deux à travers la limite.

    Retourne True si le crédit a été consommé, False si quota dépassé.
    """
    today = date.today().isoformat()
    result = session.execute(
        text(
            """
            UPDATE users
            SET uploads_today = CASE
                    WHEN last_upload_date <> :today THEN 1
                    ELSE uploads_today + 1
                END,
                last_upload_date = :today
            WHERE email = :email
              AND (CASE
                    WHEN last_upload_date <> :today THEN 0
                    ELSE uploads_today
                END) < :limit
            """
        ),
        {"today": today, "email": email, "limit": daily_limit},
    )
    session.commit()
    return result.rowcount == 1


def refund_quota(session: Session, email: str) -> None:
    """Rend un crédit (analyse échouée), sans jamais passer sous zéro."""
    session.execute(
        text(
            "UPDATE users SET uploads_today = MAX(uploads_today - 1, 0) WHERE email = :email"
        ),
        {"email": email},
    )
    session.commit()


# --- Analyses en attente de réclamation --------------------------------------

def create_pending_analysis(
    session: Session,
    token: str,
    gemini_file_name: str,
    movement: str,
    client_ip: Optional[str] = None,
) -> PendingAnalysis:
    pending = PendingAnalysis(
        token=token,
        gemini_file_name=gemini_file_name,
        movement=movement,
        client_ip=client_ip,
    )
    session.add(pending)
    session.commit()
    session.refresh(pending)
    return pending


def get_pending_analysis(session: Session, token: str) -> Optional[PendingAnalysis]:
    return session.get(PendingAnalysis, token)


def save_pending_result(session: Session, token: str, result_json: str) -> None:
    pending = session.get(PendingAnalysis, token)
    if pending is None:
        return
    pending.result_json = result_json
    session.add(pending)
    session.commit()


def mark_pending_claimed(session: Session, token: str, email: str) -> None:
    pending = session.get(PendingAnalysis, token)
    if pending is None:
        return
    pending.claimed_by = email
    session.add(pending)
    session.commit()


def purge_expired_pending(session: Session, ttl_hours: int) -> None:
    """Supprime les analyses non réclamées trop vieilles (appelé à chaque upload)."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=ttl_hours)).isoformat()
    session.execute(delete(PendingAnalysis).where(PendingAnalysis.created_at < cutoff))
    session.commit()
