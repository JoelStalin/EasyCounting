# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder
WORKDIR /app
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 POETRY_VIRTUALENVS_CREATE=false

# Copia archivos de deps primero
COPY pyproject.toml poetry.lock ./
# Si hay Poetry, exporta requirements; si no hay, solo crea vacío para no fallar
RUN pip install --upgrade pip poetry
RUN poetry self add poetry-plugin-export
RUN poetry export --without-hashes -f requirements.txt -o /app/requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Si existe requirements exportado desde builder úsalo
COPY --from=builder /app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia el resto
COPY . /app

# Usa módulo para evitar problemas de PATH
# El target asgi:app se corrige en docker-compose (ver abajo)
CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
