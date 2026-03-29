#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT=${PROJECT_ROOT:-/opt/Erp_core}
ERP_ENV=${ERP_ENV:-production}
TARGET_PCT=""
TENANT=""
BASE_URL=""
ADMIN_USER=""
ADMIN_PASS=""
INITIATED_BY=""
POLL_INTERVAL=${POLL_INTERVAL:-5}
TIMEOUT_SECONDS=${TIMEOUT_SECONDS:-900}
WAIT_FOR_COMPLETION=1
STATUS_ONLY=0
ENSURE_DEPLOYMENT_ONLY=0

usage() {
  cat <<'EOF'
Uso: jd_migrate_tenant.sh --pct <105|161> <tenant> [opciones]

Inicia una migración SAJET hacia runtime dedicated_service en el PCT indicado.
Resuelve el node_id real desde la BDA canónica, autentica como admin y hace polling
del job hasta completarse, fallar o entrar en rollback.

Opciones:
  --pct <id>             PCT destino (ej: 105, 161)
  --base-url <url>       URL base de SAJET (default: APP_URL de producción)
  --admin-user <email>   Usuario admin para login (default: ADMIN_USERNAME)
  --admin-pass <pass>    Password admin para login (default: ADMIN_PASSWORD)
  --initiated-by <txt>   initiated_by del job (default: JD:M<PCT>)
  --interval <seg>       Polling en segundos (default: 5)
  --timeout <seg>        Timeout total (default: 900)
  --no-wait              Solo encola el job y sale
  --ensure-deployment-only Repara/crea tenant_deployment y sale
  --status               No inicia nada; muestra estado actual y sale
  -h, --help             Muestra esta ayuda

Ejemplos:
  jd_migrate_tenant.sh --pct 105 cliente1
  jd_migrate_tenant.sh --pct 161 techeels --no-wait
  jd_migrate_tenant.sh --pct 105 techeels --status
EOF
}

detect_python_bin() {
  local venv_bin
  venv_bin="${PROJECT_ROOT}/.venv/bin/python"
  if [[ -x "${venv_bin}" ]]; then
    echo "${venv_bin}"
    return 0
  fi
  echo "python3"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[JD:migrate][error] Comando requerido no encontrado: $1" >&2
    exit 1
  fi
}

urlencode() {
  "${PYTHON_BIN}" - "$1" <<'PY'
import sys
from urllib.parse import quote
print(quote(sys.argv[1], safe=""))
PY
}

json_field() {
  local field="$1"
  local json_input="${2-}"
  printf '%s' "${json_input}" | "${PYTHON_BIN}" -c '
import json
import sys

field = sys.argv[1]
payload = json.load(sys.stdin)
value = payload
for part in field.split("."):
    if isinstance(value, dict):
        value = value.get(part)
    else:
        value = None
        break

if value is None:
    raise SystemExit(1)
if isinstance(value, bool):
    print("true" if value else "false")
elif isinstance(value, (dict, list)):
    print(json.dumps(value))
else:
    print(value)
' "$field"
}

resolve_context() {
  "${PYTHON_BIN}" - "${PROJECT_ROOT}" "${ERP_ENV}" "${TARGET_PCT}" "${TENANT}" <<'PY'
import json
import os
import sys

project_root, erp_env, target_pct, tenant = sys.argv[1:5]
os.chdir(project_root)
os.environ["ERP_ENV"] = erp_env

import app.config as cfg  # noqa: F401
from app.models.database import ProxmoxNode, SessionLocal, TenantDeployment

db = SessionLocal()
try:
    deployment = (
        db.query(TenantDeployment)
        .filter(TenantDeployment.subdomain == tenant)
        .first()
    )
    node = db.query(ProxmoxNode).filter(ProxmoxNode.vmid == int(target_pct)).first()
    if not node:
        raise SystemExit(f"No existe ProxmoxNode con vmid={target_pct}")

    print(
        json.dumps(
            {
                "app_url": os.getenv("APP_URL", "https://sajet.us").rstrip("/"),
                "admin_username": os.getenv("ADMIN_USERNAME", "admin@sajet.us"),
                "admin_password": os.getenv("ADMIN_PASSWORD", ""),
                "tenant_subdomain": deployment.subdomain if deployment else tenant,
                "deployment_id": deployment.id if deployment else None,
                "active_node_id": deployment.active_node_id if deployment else None,
                "runtime_mode": deployment.runtime_mode.value if deployment and deployment.runtime_mode else None,
                "migration_state": deployment.migration_state.value if deployment and deployment.migration_state else None,
                "target_node_id": node.id,
                "target_node_name": node.name,
                "target_node_vmid": node.vmid,
            }
        )
    )
finally:
    db.close()
PY
}

resolve_entity_context() {
  "${PYTHON_BIN}" - "${PROJECT_ROOT}" "${ERP_ENV}" "${TENANT}" <<'PY'
import json
import os
import sys

project_root, erp_env, tenant = sys.argv[1:4]
os.chdir(project_root)
os.environ["ERP_ENV"] = erp_env

import app.config as cfg  # noqa: F401
from app.models.database import Customer, SessionLocal, Subscription, TenantDeployment

db = SessionLocal()
try:
    customer = db.query(Customer).filter(Customer.subdomain == tenant).first()
    deployment = db.query(TenantDeployment).filter(TenantDeployment.subdomain == tenant).first()
    subscription = None
    if customer:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.customer_id == customer.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

    print(
        json.dumps(
            {
                "customer_exists": bool(customer),
                "customer_id": customer.id if customer else None,
                "company_name": customer.company_name if customer else None,
                "subscription_exists": bool(subscription),
                "subscription_id": subscription.id if subscription else None,
                "subscription_status": subscription.status.value if subscription and subscription.status else None,
                "plan_name": getattr(subscription, "plan_name", None) if subscription else None,
                "deployment_exists": bool(deployment),
                "deployment_id": deployment.id if deployment else None,
                "active_node_id": deployment.active_node_id if deployment else None,
                "runtime_mode": deployment.runtime_mode.value if deployment and deployment.runtime_mode else None,
                "migration_state": deployment.migration_state.value if deployment and deployment.migration_state else None,
            }
        )
    )
finally:
    db.close()
PY
}

ensure_deployment_record() {
  "${PYTHON_BIN}" - "${PROJECT_ROOT}" "${ERP_ENV}" "${TENANT}" "${TARGET_PCT}" <<'PY'
import json
import os
import sys

project_root, erp_env, tenant, target_pct = sys.argv[1:5]
os.chdir(project_root)
os.environ["ERP_ENV"] = erp_env

import app.config as cfg  # noqa: F401
from app.models.database import Customer, SessionLocal, Subscription
from app.services.deployment_writer import ensure_tenant_deployment

db = SessionLocal()
try:
    customer = db.query(Customer).filter(Customer.subdomain == tenant).first()
    if not customer:
        raise SystemExit(f"Customer no encontrado para subdomain={tenant}")

    subscription = (
        db.query(Subscription)
        .filter(Subscription.customer_id == customer.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    if not subscription:
        raise SystemExit(f"No hay subscription para tenant={tenant}")

    result = ensure_tenant_deployment(
        subdomain=tenant,
        subscription_id=subscription.id,
        customer_id=customer.id,
        server_id=f"pct-{target_pct}",
        plan_name=getattr(subscription, "plan_name", None),
        db=db,
    )
    if not result.get("success"):
        raise SystemExit(result.get("error") or "ensure_tenant_deployment falló")

    db.commit()
    print(json.dumps(result))
finally:
    db.close()
PY
}

extract_message() {
  local json_input="${1-}"
  printf '%s' "${json_input}" | "${PYTHON_BIN}" -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    print("Respuesta no JSON")
    raise SystemExit(0)

for key in ("detail", "message", "error"):
    value = payload.get(key)
    if value:
        print(value)
        raise SystemExit(0)

meta = payload.get("meta") or {}
if isinstance(meta, dict):
    for key in ("message", "error"):
        value = meta.get(key)
        if value:
            print(value)
            raise SystemExit(0)

data = payload.get("data") or {}
if isinstance(data, dict):
    for key in ("message", "error_log"):
        value = data.get(key)
        if value:
            print(value)
            raise SystemExit(0)

print("Sin detalle adicional")
'
}

refresh_dedicated_memory() {
  if "${PYTHON_BIN}" "${PROJECT_ROOT}/scripts/jd_tenant_catalog.py" refresh-dedicated-memory >/dev/null 2>&1; then
    echo "[JD:migrate] inventario dedicated actualizado"
  else
    echo "[JD:migrate][warn] no se pudo actualizar inventario dedicated en memory/context" >&2
  fi
}

api_request() {
  local method="$1"
  local endpoint="$2"
  local body="${3-}"
  local response_file http_code

  response_file="$(mktemp)"
  if [[ -n "${body}" ]]; then
    http_code="$(curl -sS \
      -X "${method}" \
      -H 'Content-Type: application/json' \
      -b "${COOKIE_JAR}" \
      -c "${COOKIE_JAR}" \
      --data "${body}" \
      -o "${response_file}" \
      -w '%{http_code}' \
      "${BASE_URL}${endpoint}")"
  else
    http_code="$(curl -sS \
      -X "${method}" \
      -b "${COOKIE_JAR}" \
      -c "${COOKIE_JAR}" \
      -o "${response_file}" \
      -w '%{http_code}' \
      "${BASE_URL}${endpoint}")"
  fi

  API_HTTP_CODE="${http_code}"
  API_RESPONSE="$(cat "${response_file}")"
  rm -f "${response_file}"
}

login_admin() {
  local payload
  payload="$("${PYTHON_BIN}" - "${ADMIN_USER}" "${ADMIN_PASS}" <<'PY'
import json
import sys
print(json.dumps({"email": sys.argv[1], "password": sys.argv[2]}))
PY
)"

  api_request "POST" "/api/auth/login" "${payload}"
  if [[ "${API_HTTP_CODE}" != "200" ]]; then
    echo "[JD:migrate][error] Login admin falló (${API_HTTP_CODE}): $(extract_message "${API_RESPONSE}")" >&2
    exit 1
  fi
}

print_status_summary() {
  local payload="${1-}"
  local state has_active job_id source_node target_node error_log

  state="$(json_field "data.state" "${payload}" 2>/dev/null || true)"
  has_active="$(json_field "meta.has_active_migration" "${payload}" 2>/dev/null || true)"
  job_id="$(json_field "data.id" "${payload}" 2>/dev/null || true)"
  source_node="$(json_field "data.source_node_name" "${payload}" 2>/dev/null || true)"
  target_node="$(json_field "data.target_node_name" "${payload}" 2>/dev/null || true)"
  error_log="$(json_field "data.error_log" "${payload}" 2>/dev/null || true)"

  if [[ -z "${state}" ]]; then
    echo "[JD:migrate] ${TENANT}: sin job registrado"
    return 0
  fi

  echo "[JD:migrate] tenant=${TENANT} job=${job_id:-n/a} state=${state} active=${has_active:-false} source=${source_node:-n/a} target=${target_node:-n/a}"
  if [[ -n "${error_log}" ]]; then
    echo "[JD:migrate] error_log: ${error_log}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pct)
      TARGET_PCT="$2"
      shift 2
      ;;
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --admin-user)
      ADMIN_USER="$2"
      shift 2
      ;;
    --admin-pass)
      ADMIN_PASS="$2"
      shift 2
      ;;
    --initiated-by)
      INITIATED_BY="$2"
      shift 2
      ;;
    --interval)
      POLL_INTERVAL="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT_SECONDS="$2"
      shift 2
      ;;
    --no-wait)
      WAIT_FOR_COMPLETION=0
      shift
      ;;
    --ensure-deployment-only)
      ENSURE_DEPLOYMENT_ONLY=1
      shift
      ;;
    --status)
      STATUS_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "[JD:migrate][error] Parámetro no reconocido: $1" >&2
      usage
      exit 1
      ;;
    *)
      if [[ -z "${TENANT}" ]]; then
        TENANT="$1"
      else
        echo "[JD:migrate][error] Tenant duplicado/no esperado: $1" >&2
        usage
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "${TARGET_PCT}" || -z "${TENANT}" ]]; then
  usage
  exit 1
fi

if [[ ! "${TARGET_PCT}" =~ ^[0-9]+$ ]]; then
  echo "[JD:migrate][error] --pct debe ser numérico" >&2
  exit 1
fi

require_command curl
require_command python3
PYTHON_BIN="$(detect_python_bin)"

ENTITY_JSON="$(resolve_entity_context)"
if [[ -z "${ENTITY_JSON}" ]]; then
  echo "[JD:migrate][error] No se pudo resolver entidad tenant/customer/subscription" >&2
  exit 1
fi

CONTEXT_JSON="$(resolve_context 2>/dev/null || true)"

if [[ -z "${BASE_URL}" ]]; then
  if [[ -n "${CONTEXT_JSON}" ]]; then
    BASE_URL="$(json_field "app_url" "${CONTEXT_JSON}")"
  else
    BASE_URL="$("${PYTHON_BIN}" - "${PROJECT_ROOT}" "${ERP_ENV}" <<'PY'
import os
import sys
project_root, erp_env = sys.argv[1:3]
os.chdir(project_root)
os.environ["ERP_ENV"] = erp_env
import app.config as cfg  # noqa: F401
print(os.getenv("APP_URL", "https://sajet.us").rstrip("/"))
PY
)"
  fi
fi
if [[ -z "${ADMIN_USER}" ]]; then
  if [[ -n "${CONTEXT_JSON}" ]]; then
    ADMIN_USER="$(json_field "admin_username" "${CONTEXT_JSON}")"
  fi
fi
if [[ -z "${ADMIN_PASS}" ]]; then
  if [[ -n "${CONTEXT_JSON}" ]]; then
    ADMIN_PASS="$(json_field "admin_password" "${CONTEXT_JSON}")"
  fi
fi
if [[ -z "${INITIATED_BY}" ]]; then
  INITIATED_BY="JD:M${TARGET_PCT}"
fi

TARGET_NODE_ID="$(json_field "target_node_id" "${CONTEXT_JSON}" 2>/dev/null || true)"
TARGET_NODE_NAME="$(json_field "target_node_name" "${CONTEXT_JSON}" 2>/dev/null || true)"
CUSTOMER_EXISTS="$(json_field "customer_exists" "${ENTITY_JSON}" 2>/dev/null || true)"
CUSTOMER_ID="$(json_field "customer_id" "${ENTITY_JSON}" 2>/dev/null || true)"
SUBSCRIPTION_EXISTS="$(json_field "subscription_exists" "${ENTITY_JSON}" 2>/dev/null || true)"
SUBSCRIPTION_ID="$(json_field "subscription_id" "${ENTITY_JSON}" 2>/dev/null || true)"
DEPLOYMENT_EXISTS="$(json_field "deployment_exists" "${ENTITY_JSON}" 2>/dev/null || true)"
CURRENT_NODE_ID="$(json_field "active_node_id" "${ENTITY_JSON}" 2>/dev/null || true)"
CURRENT_RUNTIME_MODE="$(json_field "runtime_mode" "${ENTITY_JSON}" 2>/dev/null || true)"
CURRENT_MIGRATION_STATE="$(json_field "migration_state" "${ENTITY_JSON}" 2>/dev/null || true)"

if [[ -z "${ADMIN_PASS}" ]]; then
  echo "[JD:migrate][error] ADMIN_PASSWORD vacío; defínelo en .env.production o pásalo por --admin-pass" >&2
  exit 1
fi

echo "[JD:migrate] tenant=${TENANT} target_pct=${TARGET_PCT} target_node_id=${TARGET_NODE_ID} target_node_name=${TARGET_NODE_NAME}"
echo "[JD:migrate] current_node_id=${CURRENT_NODE_ID:-n/a} runtime_mode=${CURRENT_RUNTIME_MODE:-n/a} migration_state=${CURRENT_MIGRATION_STATE:-n/a}"
echo "[JD:migrate] base_url=${BASE_URL}"

if [[ "${DEPLOYMENT_EXISTS}" != "true" ]]; then
  if [[ "${CUSTOMER_EXISTS}" == "true" && "${SUBSCRIPTION_EXISTS}" == "true" ]]; then
    echo "[JD:migrate] deployment faltante; customer_id=${CUSTOMER_ID} subscription_id=${SUBSCRIPTION_ID}. Se puede reparar."
  else
    echo "[JD:migrate][error] Tenant sin tenant_deployment y sin metadata suficiente para repararlo: ${TENANT}" >&2
    exit 1
  fi
fi

COOKIE_JAR="$(mktemp)"
trap 'rm -f "${COOKIE_JAR}"' EXIT

login_admin

ENCODED_TENANT="$(urlencode "${TENANT}")"
api_request "GET" "/api/migration/${ENCODED_TENANT}/status"
if [[ "${API_HTTP_CODE}" != "200" ]]; then
  echo "[JD:migrate][error] No se pudo consultar estado inicial (${API_HTTP_CODE}): $(extract_message "${API_RESPONSE}")" >&2
  exit 1
fi

print_status_summary "${API_RESPONSE}"

if [[ ${STATUS_ONLY} -eq 1 ]]; then
  if [[ "${DEPLOYMENT_EXISTS}" != "true" ]]; then
    echo "[JD:migrate] ${TENANT}: customer existe pero falta tenant_deployment"
  fi
  exit 0
fi

if [[ "${DEPLOYMENT_EXISTS}" != "true" ]]; then
  echo "[JD:migrate] reparando tenant_deployment para ${TENANT}"
  ensure_result="$(ensure_deployment_record)"
  echo "[JD:migrate] deployment repaired: ${ensure_result}"
  ENTITY_JSON="$(resolve_entity_context)"
  DEPLOYMENT_EXISTS="$(json_field "deployment_exists" "${ENTITY_JSON}" 2>/dev/null || true)"
  CURRENT_NODE_ID="$(json_field "active_node_id" "${ENTITY_JSON}" 2>/dev/null || true)"
  CURRENT_RUNTIME_MODE="$(json_field "runtime_mode" "${ENTITY_JSON}" 2>/dev/null || true)"
  CURRENT_MIGRATION_STATE="$(json_field "migration_state" "${ENTITY_JSON}" 2>/dev/null || true)"
fi

if [[ ${ENSURE_DEPLOYMENT_ONLY} -eq 1 ]]; then
  echo "[JD:migrate] tenant_deployment listo para ${TENANT}"
  exit 0
fi

HAS_ACTIVE="$(json_field "meta.has_active_migration" "${API_RESPONSE}" 2>/dev/null || true)"
JOB_ID="$(json_field "data.id" "${API_RESPONSE}" 2>/dev/null || true)"

if [[ "${CURRENT_NODE_ID}" == "${TARGET_NODE_ID}" ]]; then
  if [[ "${CURRENT_RUNTIME_MODE}" == "dedicated_service" ]]; then
    echo "[JD:migrate] ${TENANT} ya está en dedicated_service en el nodo destino ${TARGET_PCT}"
    exit 0
  fi

  echo "[JD:migrate] mismo nodo detectado; usando provision-dedicated en lugar de migration/start"
  api_request "POST" "/api/migration/${ENCODED_TENANT}/provision-dedicated" "{}"
  if [[ "${API_HTTP_CODE}" != "200" ]]; then
    echo "[JD:migrate][error] provision-dedicated falló (${API_HTTP_CODE}): $(extract_message "${API_RESPONSE}")" >&2
    exit 1
  fi
  echo "[JD:migrate] provision-dedicated completado para ${TENANT}"
  refresh_dedicated_memory
  exit 0
fi

if [[ "${HAS_ACTIVE}" != "true" ]]; then
  START_PAYLOAD="$("${PYTHON_BIN}" - "${TARGET_NODE_ID}" "${INITIATED_BY}" <<'PY'
import json
import sys
print(
    json.dumps(
        {
            "target_node_id": int(sys.argv[1]),
            "target_runtime_mode": "dedicated_service",
            "initiated_by": sys.argv[2],
        }
    )
)
PY
)"

  api_request "POST" "/api/migration/${ENCODED_TENANT}/start" "${START_PAYLOAD}"
  if [[ "${API_HTTP_CODE}" != "200" ]]; then
    echo "[JD:migrate][error] No se pudo iniciar migración (${API_HTTP_CODE}): $(extract_message "${API_RESPONSE}")" >&2
    exit 1
  fi

  JOB_ID="$(json_field "data.id" "${API_RESPONSE}" 2>/dev/null || true)"
  START_STATE="$(json_field "data.state" "${API_RESPONSE}" 2>/dev/null || true)"
  echo "[JD:migrate] job iniciado: ${JOB_ID:-n/a} state=${START_STATE:-unknown}"
else
  echo "[JD:migrate] hay una migración activa; se reusa el job actual ${JOB_ID:-n/a}"
fi

if [[ ${WAIT_FOR_COMPLETION} -eq 0 ]]; then
  exit 0
fi

deadline=$((SECONDS + TIMEOUT_SECONDS))
last_state=""

while (( SECONDS < deadline )); do
  api_request "GET" "/api/migration/${ENCODED_TENANT}/status"
  if [[ "${API_HTTP_CODE}" != "200" ]]; then
    echo "[JD:migrate][error] Falló polling de estado (${API_HTTP_CODE}): $(extract_message "${API_RESPONSE}")" >&2
    exit 1
  fi

  state="$(json_field "data.state" "${API_RESPONSE}" 2>/dev/null || true)"
  current_job_id="$(json_field "data.id" "${API_RESPONSE}" 2>/dev/null || true)"

  if [[ -n "${state}" && "${state}" != "${last_state}" ]]; then
    print_status_summary "${API_RESPONSE}"
    last_state="${state}"
  fi

  case "${state}" in
    completed)
      echo "[JD:migrate] migración completada: tenant=${TENANT} job=${current_job_id:-${JOB_ID:-n/a}} target_pct=${TARGET_PCT}"
      refresh_dedicated_memory
      exit 0
      ;;
    failed|rollback)
      echo "[JD:migrate][error] migración terminó en ${state}: $(extract_message "${API_RESPONSE}")" >&2
      exit 1
      ;;
  esac

  sleep "${POLL_INTERVAL}"
done

echo "[JD:migrate][error] timeout esperando finalización del job para ${TENANT}" >&2
exit 124
