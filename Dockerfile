# syntax=docker/dockerfile:1

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Usa el requirements versionado para evitar depender de Poetry durante el build.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia el resto
COPY . /app

# Usa módulo para evitar problemas de PATH
# El target asgi:app se corrige en docker-compose (ver abajo)
CMD ["python", "-m", "gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
