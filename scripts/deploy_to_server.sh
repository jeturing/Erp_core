#!/usr/bin/env bash

set -euo pipefail

show_help() {
  cat <<'USAGE'
Usage: ./scripts/deploy_to_server.sh [--profile pct160] [--dry-run] [--skip-build]

Environment variables:
  SERVER_USER      Usuario SSH remoto
  SERVER_HOST      Host o IP remota
  SERVER_PATH      Ruta remota del proyecto (default: /opt/Erp_core)
  SSH_KEY          Ruta private key SSH (opcional)
  SSH_PORT         Puerto SSH (default: 22)
  APP_SERVICE      Servicio systemd a reiniciar (opcional)
  APP_BASE_URL     URL para smoke test remoto (default: http://127.0.0.1:4443)

Profiles:
  pct160           Aplica defaults para despliegue en PCT160

Examples:
  ./scripts/deploy_to_server.sh --profile pct160
  APP_SERVICE=erp-core SERVER_HOST=10.0.0.160 ./scripts/deploy_to_server.sh
  ./scripts/deploy_to_server.sh --profile pct160 --dry-run
USAGE
}

SSH_PORT=${SSH_PORT:-22}
PROFILE=""
DRY_RUN=""
RUN_BUILD=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="--dry-run"
      shift
      ;;
    --skip-build)
      RUN_BUILD=0
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      show_help
      exit 1
      ;;
  esac
done

if [[ "${PROFILE}" == "pct160" ]]; then
  SERVER_USER=${SERVER_USER:-root}
  SERVER_HOST=${SERVER_HOST:-${PCT160_HOST:-pct160}}
  SERVER_PATH=${SERVER_PATH:-/opt/Erp_core}
  APP_SERVICE=${APP_SERVICE:-erp-core}
fi

: "${SERVER_USER:?Please set SERVER_USER}"
: "${SERVER_HOST:?Please set SERVER_HOST}"
: "${SERVER_PATH:?Please set SERVER_PATH}"

if [[ ${RUN_BUILD} -eq 1 && -z "${DRY_RUN}" ]]; then
  echo "[deploy] Build SPA local"
  PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  "${PROJECT_ROOT}/scripts/build_static.sh"
fi

SSH_OPTS=(-p "${SSH_PORT}")
if [[ -n "${SSH_KEY-}" ]]; then
  SSH_OPTS=(-i "${SSH_KEY}" -p "${SSH_PORT}")
fi

RSYNC_EXCLUDES=(
  --exclude '.git'
  --exclude '.github'
  --exclude 'venv'
  --exclude '__pycache__'
  --exclude '.DS_Store'
  --exclude 'frontend/node_modules'
  --exclude 'frontend/dist'
)

RSYNC_CMD=(rsync -az --delete "${RSYNC_EXCLUDES[@]}")
if [[ -n "${DRY_RUN}" ]]; then
  RSYNC_CMD+=(--dry-run)
fi
RSYNC_CMD+=(-e "ssh ${SSH_OPTS[*]}" ./ "${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}")

echo "[deploy] Sync ${SERVER_HOST}:${SERVER_PATH}"
eval "${RSYNC_CMD[*]}"

if [[ -n "${DRY_RUN}" ]]; then
  echo "[deploy] Dry run complete"
  exit 0
fi

if [[ -n "${APP_SERVICE-}" ]]; then
  echo "[deploy] Restart service ${APP_SERVICE}"
  ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "sudo systemctl restart ${APP_SERVICE} && sudo systemctl is-active ${APP_SERVICE}"
fi

APP_BASE_URL=${APP_BASE_URL:-http://127.0.0.1:4443}
echo "[deploy] Run smoke tests"
ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "cd ${SERVER_PATH} && APP_BASE_URL='${APP_BASE_URL}' ./scripts/smoke_pct160.sh"

echo "[deploy] Deployment complete"
