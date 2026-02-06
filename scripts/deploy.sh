#!/usr/bin/env bash
set -euo pipefail

# Script de despliegue automatizado para getupsoft.
# Se encarga de construir las imágenes, ejecutar migraciones y levantar
# los servicios definidos en deploy/docker-compose.yml.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/deploy/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env.development"

print_step() {
  echo
  echo "[getupsoft] $1"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: se requiere el comando '$1' para continuar." >&2
    exit 1
  fi
}

choose_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo "Error: no se encontró una instalación de Docker Compose." >&2
    exit 1
  fi
}

main() {
  require_command docker

  if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "Error: no se encontró el archivo $COMPOSE_FILE" >&2
    exit 1
  fi

  if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: no existe $ENV_FILE. Ejecute 'python scripts/setup_env.py' antes del despliegue." >&2
    exit 1
  fi

  COMPOSE_BIN=$(choose_compose)

  print_step "Construyendo imágenes Docker"
  $COMPOSE_BIN -f "$COMPOSE_FILE" build

  print_step "Aplicando migraciones de base de datos"
  $COMPOSE_BIN -f "$COMPOSE_FILE" run --rm api alembic upgrade head

  print_step "Levantando servicios"
  $COMPOSE_BIN -f "$COMPOSE_FILE" up -d

  print_step "Estado de los contenedores"
  $COMPOSE_BIN -f "$COMPOSE_FILE" ps

  echo
  echo "Despliegue completado. Nginx expone la API en https://localhost:8443"
}

main "$@"
