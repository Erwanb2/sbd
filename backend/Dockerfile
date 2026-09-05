FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT="/venv"
ENV UV_PYTHON_DOWNLOADS="never"
ENV UV_PYTHON="python3.11"

# MediaPipe tire opencv-contrib-python (et non la variante headless) : il lui faut
# libGL et libglib, absents de l'image slim. Sans eux, l'import casse au runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./

# C'est cette ligne qui est cruciale :
RUN uv sync --no-dev --no-install-project

# Modele de pose MediaPipe embarque dans l'image : pas de telechargement au premier
# appel, donc pas de latence surprise ni de dependance reseau au demarrage.
ADD https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task /models/pose_landmarker_heavy.task
RUN chmod 644 /models/pose_landmarker_heavy.task

COPY . .

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
