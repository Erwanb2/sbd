FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT="/venv"
ENV UV_PYTHON_DOWNLOADS="never"
ENV UV_PYTHON="python3.11"

COPY pyproject.toml uv.lock* ./

# C'est cette ligne qui est cruciale :
RUN uv sync --no-dev --no-install-project

COPY . .

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]