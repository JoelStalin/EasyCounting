from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REMOTE_SCRIPT = r"""#!/usr/bin/env bash
set -Eeuo pipefail

log() {
  printf '[mailcow-prepare] %s\n' "$1"
}

run_root() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

run_docker() {
  if docker info >/dev/null 2>&1; then
    docker "$@"
  else
    run_root docker "$@"
  fi
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Falta comando requerido: $1"
    exit 1
  fi
}

PORT_REPORT="${PORT_REPORT}"
REMOTE_DIR="${REMOTE_DIR}"
MAILCOW_REPO="${MAILCOW_REPO}"
MAILCOW_HOSTNAME="${MAILCOW_HOSTNAME}"
MAILCOW_TZ="${MAILCOW_TZ}"
MAILCOW_GIT_REF="${MAILCOW_GIT_REF}"
HTTP_PORT="${HTTP_PORT}"
HTTPS_PORT="${HTTPS_PORT}"
START_STACK="${START_STACK}"
INSTALL_DOCKER="${INSTALL_DOCKER}"

mkdir -p "$(dirname "${PORT_REPORT}")"

{
  echo "timestamp=$(date -Is)"
  echo "hostname=$(hostname -f 2>/dev/null || hostname)"
  echo "remote_dir=${REMOTE_DIR}"
  echo "mailcow_hostname=${MAILCOW_HOSTNAME}"
  echo "http_port=${HTTP_PORT}"
  echo "https_port=${HTTPS_PORT}"
  echo "---"
  echo "listeners:"
  ss -ltnp || true
} > "${PORT_REPORT}"

log "Reporte inicial guardado en ${PORT_REPORT}"

if [[ "${INSTALL_DOCKER}" == "1" ]]; then
  run_root apt-get update
  run_root apt-get install -y ca-certificates curl git gnupg lsb-release python3
fi

require_cmd git
require_cmd python3
require_cmd curl
require_cmd gpg

if [[ "${INSTALL_DOCKER}" == "1" ]] && ! command -v docker >/dev/null 2>&1; then
  log "Instalando Docker Engine y Compose Plugin"
  run_root install -m 0755 -d /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | run_root gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    run_root chmod a+r /etc/apt/keyrings/docker.gpg
  fi
  ARCH="$(dpkg --print-architecture)"
  CODENAME="$(
    . /etc/os-release
    echo "${VERSION_CODENAME}"
  )"
  echo \
    "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
    | run_root tee /etc/apt/sources.list.d/docker.list >/dev/null
  run_root apt-get update
  run_root apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  run_root systemctl enable --now docker
else
  log "Docker ya esta instalado o se omitio la instalacion"
fi

require_cmd docker

if ! getent group docker >/dev/null 2>&1; then
  run_root groupadd docker
fi

if [[ "${EUID}" -ne 0 ]]; then
  run_root usermod -aG docker "${USER}" || true
fi

if [[ -d "${REMOTE_DIR}/.git" ]]; then
  log "Actualizando repositorio Mailcow existente"
  git -C "${REMOTE_DIR}" fetch --tags --prune
  if [[ -n "${MAILCOW_GIT_REF}" ]]; then
    git -C "${REMOTE_DIR}" checkout "${MAILCOW_GIT_REF}"
  fi
  git -C "${REMOTE_DIR}" pull --ff-only
else
  log "Clonando Mailcow en ${REMOTE_DIR}"
  run_root mkdir -p "$(dirname "${REMOTE_DIR}")"
  if [[ "${EUID}" -ne 0 ]]; then
    sudo chown "${USER}:${USER}" "$(dirname "${REMOTE_DIR}")"
  fi
  git clone "${MAILCOW_REPO}" "${REMOTE_DIR}"
  if [[ -n "${MAILCOW_GIT_REF}" ]]; then
    git -C "${REMOTE_DIR}" checkout "${MAILCOW_GIT_REF}"
  fi
fi

cd "${REMOTE_DIR}"

if [[ ! -f mailcow.conf ]]; then
  log "Generando mailcow.conf via generate_config.sh"
  printf '%s\n' "${MAILCOW_HOSTNAME}" | ./generate_config.sh >/tmp/mailcow-generate.log 2>&1
fi

python3 - <<'PY'
from pathlib import Path
import os

path = Path("mailcow.conf")
text = path.read_text(encoding="utf-8").splitlines()
updates = {
    "MAILCOW_HOSTNAME": os.environ["MAILCOW_HOSTNAME"],
    "TZ": os.environ["MAILCOW_TZ"],
    "HTTP_PORT": os.environ["HTTP_PORT"],
    "HTTPS_PORT": os.environ["HTTPS_PORT"],
}

seen = set()
result = []
for line in text:
    key = line.split("=", 1)[0] if "=" in line else ""
    if key in updates:
        result.append(f"{key}={updates[key]}")
        seen.add(key)
    else:
        result.append(line)

for key, value in updates.items():
    if key not in seen:
        result.append(f"{key}={value}")

path.write_text("\n".join(result) + "\n", encoding="utf-8")
PY

log "mailcow.conf alineado para ${MAILCOW_HOSTNAME}"
run_docker --version
run_docker compose version

if [[ "${START_STACK}" == "1" ]]; then
  log "Validando puertos antes de iniciar la pila"
  PORT_CONFLICTS=""
  for port in 25 465 587 993 4190 "${HTTP_PORT}" "${HTTPS_PORT}"; do
    CURRENT_CONFLICTS="$(ss -ltn "( sport = :${port} )" | tail -n +2 || true)"
    if [[ -n "${CURRENT_CONFLICTS}" ]]; then
      PORT_CONFLICTS+="port ${port}\n${CURRENT_CONFLICTS}\n"
    fi
  done
  if [[ -n "${PORT_CONFLICTS}" ]]; then
    echo "--- port_conflicts ---" >> "${PORT_REPORT}"
    printf '%b' "${PORT_CONFLICTS}" >> "${PORT_REPORT}"
    log "Hay puertos ocupados. Revisa ${PORT_REPORT} antes de levantar Mailcow."
    exit 2
  fi

  log "Levantando Mailcow"
  run_docker compose pull
  run_docker compose up -d
  run_docker compose ps
else
  log "Preparacion completada sin levantar contenedores"
fi
"""


def build_remote_command(args: argparse.Namespace) -> str:
    env_map = {
        "PORT_REPORT": args.remote_report,
        "REMOTE_DIR": args.remote_dir,
        "MAILCOW_REPO": args.mailcow_repo,
        "MAILCOW_HOSTNAME": args.hostname,
        "MAILCOW_TZ": args.timezone,
        "MAILCOW_GIT_REF": args.git_ref or "",
        "HTTP_PORT": str(args.http_port),
        "HTTPS_PORT": str(args.https_port),
        "START_STACK": "1" if args.start_stack else "0",
        "INSTALL_DOCKER": "0" if args.skip_docker_install else "1",
    }
    exports = " ".join(f"{key}={shlex.quote(value)}" for key, value in env_map.items())
    return f"{exports} bash -s --"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepara Mailcow remotamente sobre getupsoft o un alias SSH compatible."
    )
    parser.add_argument("--ssh-host", default="getupsoft", help="Alias o host SSH configurado localmente.")
    parser.add_argument("--remote-dir", default="/opt/mailcow-dockerized")
    parser.add_argument("--hostname", default="mail.getupsoft.com.do", help="FQDN de Mailcow.")
    parser.add_argument("--timezone", default="America/Santo_Domingo")
    parser.add_argument("--http-port", type=int, default=8081, help="Puerto HTTP para UI/ACME.")
    parser.add_argument("--https-port", type=int, default=8443, help="Puerto HTTPS para UI.")
    parser.add_argument("--git-ref", default="", help="Branch o tag opcional de mailcow-dockerized.")
    parser.add_argument("--mailcow-repo", default="https://github.com/mailcow/mailcow-dockerized")
    parser.add_argument(
        "--remote-report",
        default="/var/tmp/mailcow-getupsoft-preflight.txt",
        help="Ruta remota para guardar listeners y conflictos detectados.",
    )
    parser.add_argument("--start-stack", action="store_true", help="Levanta Mailcow si no hay conflicto de puertos.")
    parser.add_argument(
        "--skip-docker-install",
        action="store_true",
        help="Omite la instalacion de Docker y Compose Plugin.",
    )
    parser.add_argument(
        "--output",
        default="artifacts_live_dns/getupsoft_mailcow_prepare.log",
        help="Archivo local para guardar stdout/stderr de la ejecucion.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = ["ssh", args.ssh_host, build_remote_command(args)]
    result = subprocess.run(
        command,
        input=REMOTE_SCRIPT,
        text=True,
        capture_output=True,
    )

    timestamp = datetime.now(timezone.utc).isoformat()
    output = [
        f"timestamp_utc={timestamp}",
        f"ssh_host={args.ssh_host}",
        f"remote_dir={args.remote_dir}",
        f"hostname={args.hostname}",
        f"http_port={args.http_port}",
        f"https_port={args.https_port}",
        f"start_stack={args.start_stack}",
        f"returncode={result.returncode}",
        "--- stdout ---",
        result.stdout.rstrip(),
        "--- stderr ---",
        result.stderr.rstrip(),
        "",
    ]
    output_path.write_text("\n".join(output), encoding="utf-8")

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    if result.returncode != 0:
        print(f"\nEvidencia guardada en: {output_path}", file=sys.stderr)
    else:
        print(f"\nEvidencia guardada en: {output_path}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
