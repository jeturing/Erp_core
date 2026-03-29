#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT=${PROJECT_ROOT:-/opt/Erp_core}
PUSH_SCRIPT="${PROJECT_ROOT}/scripts/pct_push_160.sh"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
VENV_DIR=${VENV_DIR:-${PROJECT_ROOT}/.venv}
PYTEST_TARGET=${PYTEST_TARGET:-tests}
RUN_TESTS=1
RUN_GIT=1
RUN_DB_MIGRATIONS=1
BUMP_LEVEL=${BUMP_LEVEL:-patch}
COMMENT=""

usage() {
  cat <<'EOF'
Uso: jd_sajet.sh [--status] [--skip-tests] [--skip-git] [--skip-db-migrations] [--bump patch|minor|major] [-m "comentario"] [opciones pct_push_160]

Comando de conveniencia para SAJET:
  - reporta si el frontend corre como SvelteKit real o como SPA Vite
  - ejecuta pruebas Python del repo
  - ejecuta migraciones Alembic sobre la BDA canónica
  - incrementa versión del frontend
  - hace commit y git push de la rama actual
  - compila el frontend
  - publica el repo en el CT 160

Opciones:
  --status      Solo muestra el estado detectado y no despliega
  --skip-tests  Omite pytest
  --skip-git    Omite bump de versión, commit y git push
  --skip-db-migrations Omite alembic upgrade head contra producción
  --bump        patch|minor|major (default: patch)
  -m, --message Comentario adicional para el commit automático
  -h, --help    Muestra esta ayuda

Las demás opciones se pasan a scripts/pct_push_160.sh.
EOF
}

detect_frontend_runtime() {
  if [[ -f "${FRONTEND_DIR}/src/app.html" ]]; then
    echo "sveltekit"
    return 0
  fi

  if [[ -f "${FRONTEND_DIR}/src/App.svelte" ]]; then
    echo "vite-spa"
    return 0
  fi

  echo "unknown"
}

detect_python_bin() {
  if [[ -x "${VENV_DIR}/bin/python" ]]; then
    echo "${VENV_DIR}/bin/python"
    return 0
  fi

  echo "python3"
}

SHOW_STATUS=0
FORWARD_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --status)
      SHOW_STATUS=1
      shift
      ;;
    --skip-tests)
      RUN_TESTS=0
      shift
      ;;
    --skip-git)
      RUN_GIT=0
      shift
      ;;
    --skip-db-migrations)
      RUN_DB_MIGRATIONS=0
      shift
      ;;
    --bump)
      BUMP_LEVEL="$2"
      shift 2
      ;;
    -m|--message)
      COMMENT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      FORWARD_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ! -x "${PUSH_SCRIPT}" ]]; then
  echo "[JD:sajet] Script no encontrado o no ejecutable: ${PUSH_SCRIPT}" >&2
  exit 1
fi

runtime="$(detect_frontend_runtime)"
PYTHON_BIN="$(detect_python_bin)"
echo "[JD:sajet] frontend runtime: ${runtime}"
echo "[JD:sajet] python runtime: ${PYTHON_BIN}"

if [[ "${runtime}" == "vite-spa" ]]; then
  echo "[JD:sajet] navegación actual: hash routing centralizado en frontend/src/App.svelte"
elif [[ "${runtime}" == "sveltekit" ]]; then
  echo "[JD:sajet] navegación actual: filesystem routing de SvelteKit"
fi

if [[ ${SHOW_STATUS} -eq 1 ]]; then
  exit 0
fi

run_tests() {
  ensure_python_runtime
  echo "[JD:sajet] ejecutando pytest (${PYTEST_TARGET})"
  (
    cd "${PROJECT_ROOT}"
    "${PYTHON_BIN}" -m pytest "${PYTEST_TARGET}" -q
  )
}

ensure_python_runtime() {
  echo "[JD:sajet] verificando dependencias Python"
  if ! "${PYTHON_BIN}" - <<'PY'
import alembic
import email_validator
import fastapi
import pytest
import sqlalchemy
try:
    import psycopg2  # noqa: F401
except ModuleNotFoundError:
    raise SystemExit(1)
PY
  then
    echo "[JD:sajet] instalando requirements en el entorno Python activo"
    "${PYTHON_BIN}" -m pip install -r "${PROJECT_ROOT}/requirements.txt"
    "${PYTHON_BIN}" -m pip install psycopg2-binary
  fi
}

run_db_migrations() {
  ensure_python_runtime
  echo "[JD:sajet] ejecutando Alembic sobre ERP_ENV=production"
  (
    cd "${PROJECT_ROOT}"
    ERP_ENV=production "${PYTHON_BIN}" -m alembic upgrade head
  )
}

read_frontend_version() {
  python3 - <<'PY'
import json
from pathlib import Path
package = Path("/opt/Erp_core/frontend/package.json")
print(json.loads(package.read_text())["version"])
PY
}

prepare_git_push() {
  local branch upstream version commit_subject commit_body

  branch="$(git -C "${PROJECT_ROOT}" branch --show-current)"
  upstream="$(git -C "${PROJECT_ROOT}" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || true)"
  if [[ -z "${upstream}" ]]; then
    echo "[JD:sajet] la rama ${branch} no tiene upstream configurado" >&2
    exit 1
  fi

  echo "[JD:sajet] incrementando versión (${BUMP_LEVEL})"
  (
    cd "${FRONTEND_DIR}"
    npm version "${BUMP_LEVEL}" --no-git-tag-version
  )

  version="$(read_frontend_version)"
  commit_subject="chore(release): publish sajet v${version}"
  if [[ -n "${COMMENT}" ]]; then
    commit_body="${COMMENT}"
  else
    commit_body="Automated build, test and publish to CT 160 via JD -sajet."
  fi

  echo "[JD:sajet] creando commit ${commit_subject}"
  (
    cd "${PROJECT_ROOT}"
    git add -A
    git commit -m "${commit_subject}" -m "${commit_body}"
    echo "[JD:sajet] git push ${upstream}"
    git push
  )
}

if [[ ${RUN_TESTS} -eq 1 ]]; then
  run_tests
fi

if [[ ${RUN_GIT} -eq 1 ]]; then
  prepare_git_push
fi

if [[ ${RUN_DB_MIGRATIONS} -eq 1 ]]; then
  run_db_migrations
fi

echo "[JD:sajet] iniciando build y publish hacia CT 160"
exec "${PUSH_SCRIPT}" "${FORWARD_ARGS[@]}"
