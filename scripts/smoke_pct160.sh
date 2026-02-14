#!/usr/bin/env bash

set -euo pipefail

APP_BASE_URL=${APP_BASE_URL:-http://127.0.0.1:4443}

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

TMP_DIR=$(mktemp -d)
COOKIE_JAR="${TMP_DIR}/cookies.txt"
trap 'rm -rf "${TMP_DIR}"' EXIT

log() {
  echo "[smoke] $*"
}

request() {
  local method="$1"
  local path="$2"
  local data="${3-}"

  if [[ -n "${data}" ]]; then
    curl -sS -o "${TMP_DIR}/response.json" -w '%{http_code}' \
      -X "${method}" \
      -H 'Content-Type: application/json' \
      -H 'X-Forwarded-Proto: https' \
      -b "${COOKIE_JAR}" -c "${COOKIE_JAR}" \
      --data "${data}" \
      "${APP_BASE_URL}${path}"
  else
    curl -sS -o "${TMP_DIR}/response.json" -w '%{http_code}' \
      -X "${method}" \
      -H 'X-Forwarded-Proto: https' \
      -b "${COOKIE_JAR}" -c "${COOKIE_JAR}" \
      "${APP_BASE_URL}${path}"
  fi
}

assert_status() {
  local code="$1"
  shift
  local valid=0
  for expected in "$@"; do
    if [[ "${code}" == "${expected}" ]]; then
      valid=1
      break
    fi
  done

  if [[ ${valid} -ne 1 ]]; then
    echo "[smoke][error] status inesperado: ${code}, esperado: $*" >&2
    cat "${TMP_DIR}/response.json" >&2 || true
    exit 1
  fi
}

assert_json_contains() {
  local pattern="$1"
  if ! grep -q "${pattern}" "${TMP_DIR}/response.json"; then
    echo "[smoke][error] respuesta sin patron esperado: ${pattern}" >&2
    cat "${TMP_DIR}/response.json" >&2 || true
    exit 1
  fi
}

log "Health check"
status=$(request GET '/health')
assert_status "${status}" 200
assert_json_contains '"status"'

log "Ruta /admin sin auth"
status=$(request GET '/admin')
assert_status "${status}" 200 301 302 307

log "Ruta /tenant/portal sin auth"
status=$(request GET '/tenant/portal')
assert_status "${status}" 200 301 302 307

log "Login admin via /api/auth/login"
status=$(request POST '/api/auth/login' "{\"email\":\"${ADMIN_USERNAME}\",\"password\":\"${ADMIN_PASSWORD}\"}")
assert_status "${status}" 200
assert_json_contains '"role"'

log "Usuario autenticado"
status=$(request GET '/api/auth/me')
assert_status "${status}" 200
assert_json_contains '"role"'

log "SPA /admin con cookie"
status=$(request GET '/admin')
assert_status "${status}" 200
if ! grep -Eq 'id="app"|__ERP_BOOTSTRAP__' "${TMP_DIR}/response.json"; then
  echo "[smoke][error] /admin no parece servir SPA shell" >&2
  cat "${TMP_DIR}/response.json" >&2 || true
  exit 1
fi

log "API core admin"
for endpoint in \
  '/api/dashboard/metrics' \
  '/api/tenants' \
  '/api/domains' \
  '/api/nodes' \
  '/api/nodes/status' \
  '/api/nodes/metrics/summary' \
  '/api/nodes/containers/all' \
  '/api/billing/metrics' \
  '/api/settings' \
  '/api/settings/odoo/current'; do
  status=$(request GET "${endpoint}")
  assert_status "${status}" 200
  log "  OK ${endpoint}"
done

log "Smoke tests completados OK"
