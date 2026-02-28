#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT=${PROJECT_ROOT:-/opt/Erp_core}
CT_ID=${CT_ID:-160}
APP_SERVICE=${APP_SERVICE:-erp-core}
REMOTE_ROOT=${REMOTE_ROOT:-/var/www/html}
RUN_BUILD=1
RUN_SMOKE=1
PORT=${PORT:-4443}

usage() {
  cat <<'EOF'
Usage: pct_push_160.sh [OPTIONS]

Push cambios locales del repo hacia CT 160 usando `pct push`.

Options:
  --no-build         No ejecutar build SPA local
  --no-smoke         No ejecutar smoke tests en el CT
  --ct <id>          Cambiar CT destino (default: 160)
  --service <name>   Servicio a reiniciar en CT (default: erp-core)
  --remote-root <p>  Ruta destino en CT (default: /var/www/html)
  -h, --help         Mostrar ayuda
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build)
      RUN_BUILD=0
      shift
      ;;
    --no-smoke)
      RUN_SMOKE=0
      shift
      ;;
    --ct)
      CT_ID="$2"
      shift 2
      ;;
    --service)
      APP_SERVICE="$2"
      shift 2
      ;;
    --remote-root)
      REMOTE_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Parametro no reconocido: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -d "${PROJECT_ROOT}" ]]; then
  echo "[p160] Proyecto no encontrado: ${PROJECT_ROOT}" >&2
  exit 1
fi

if [[ ${RUN_BUILD} -eq 1 ]]; then
  echo "[p160] Build SPA local"
  "${PROJECT_ROOT}/scripts/build_static.sh"
fi

temp_ops_list="$(mktemp)"
temp_pushed_list="$(mktemp)"
trap 'rm -f "${temp_ops_list}" "${temp_pushed_list}"' EXIT

python3 - <<'PY' > "${temp_ops_list}"
import pathlib
import subprocess

repo = pathlib.Path("/opt/Erp_core")
status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True).splitlines()

always_push = [
    "app/config.py",
    "app/routes/tenants.py",
    "app/routes/provisioning.py",
    "app/routes/plans.py",
    "app/services/odoo_database_manager.py",
    "frontend/src/pages/Tenants.svelte",
    "frontend/src/pages/Plans.svelte",
    "frontend/src/lib/api/tenants.ts",
    "scripts/smoke_pct160.sh",
    "scripts/pct_push_160.sh",
]

push_files = []
delete_files = []
for line in status:
    status_code = line[:2]
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]

    if "D" in status_code:
        delete_files.append(path)
        continue

    file_path = repo / path
    if file_path.is_file():
        push_files.append(path)

for rel in always_push:
    file_path = repo / rel
    if file_path.is_file():
        push_files.append(rel)

spa_dir = repo / "static" / "spa"
if spa_dir.exists():
    for p in spa_dir.rglob("*"):
        if p.is_file():
            push_files.append(str(p.relative_to(repo)))

for rel in sorted(dict.fromkeys(delete_files)):
    print(f"D\t{rel}")

for rel in sorted(dict.fromkeys(push_files)):
    print(f"P\t{rel}")
PY

total_ops="$(wc -l < "${temp_ops_list}")"
if [[ "${total_ops}" -eq 0 ]]; then
  echo "[p160] No hay archivos para enviar."
else
  echo "[p160] Aplicando ${total_ops} cambios en CT ${CT_ID}"
    current=0
    while IFS=$'\t' read -r op rel; do
      current=$((current + 1))
      if [[ "${op}" == "D" ]]; then
      pct exec "${CT_ID}" -- rm -f "${REMOTE_ROOT}/${rel}"
      echo "[p160] [${current}/${total_ops}] DELETE ${rel}"
      continue
    fi

    src="${PROJECT_ROOT}/${rel}"
    dst="${REMOTE_ROOT}/${rel}"
    dst_dir="$(dirname "${dst}")"

    pct exec "${CT_ID}" -- mkdir -p "${dst_dir}"
    pct push "${CT_ID}" "${src}" "${dst}"
    echo "${rel}" >> "${temp_pushed_list}"
    echo "[p160] [${current}/${total_ops}] PUSH ${rel}"
  done < "${temp_ops_list}"
fi

# Verificación de checksums para asegurar que el runtime quedó sincronizado
if [[ -s "${temp_pushed_list}" ]]; then
  echo "[p160] Verificando checksums de archivos desplegados"
  verify_failures=0
  while IFS= read -r rel; do
    src="${PROJECT_ROOT}/${rel}"
    dst="${REMOTE_ROOT}/${rel}"
    local_sha="$(sha256sum "${src}" | awk '{print $1}')"
    remote_sha="$(pct exec "${CT_ID}" -- sha256sum "${dst}" | awk '{print $1}')"
    if [[ -z "${remote_sha}" || "${local_sha}" != "${remote_sha}" ]]; then
      echo "[p160][error] CHECKSUM mismatch ${rel}" >&2
      verify_failures=$((verify_failures + 1))
    fi
  done < "${temp_pushed_list}"

  if [[ "${verify_failures}" -gt 0 ]]; then
    echo "[p160][error] ${verify_failures} archivos con checksum inválido" >&2
    exit 1
  fi
fi

pct exec "${CT_ID}" -- chmod +x \
  "${REMOTE_ROOT}/scripts/build_static.sh" \
  "${REMOTE_ROOT}/scripts/deploy_to_server.sh" \
  "${REMOTE_ROOT}/scripts/smoke_pct160.sh" \
  "${REMOTE_ROOT}/scripts/pct_push_160.sh" || true

if [[ -n "${APP_SERVICE}" ]]; then
  echo "[p160] Reiniciando servicio ${APP_SERVICE} en CT ${CT_ID}"
  pct exec "${CT_ID}" -- systemctl stop "${APP_SERVICE}" || true
  pct exec "${CT_ID}" -- bash -lc \
    "pid=\$(ss -ltnp | grep ':${PORT} ' | sed -n 's/.*pid=\\([0-9]\\+\\).*/\\1/p' | head -n1); if [[ -n \"\$pid\" ]]; then kill \"\$pid\" || true; fi"
  pct exec "${CT_ID}" -- systemctl start "${APP_SERVICE}"
  pct exec "${CT_ID}" -- systemctl is-active "${APP_SERVICE}"

  working_dir="$(pct exec "${CT_ID}" -- systemctl show "${APP_SERVICE}" -p WorkingDirectory --value | tr -d '\r')"
  if [[ "${working_dir}" != "${REMOTE_ROOT}" ]]; then
    echo "[p160][error] WorkingDirectory de ${APP_SERVICE} es '${working_dir}', esperado '${REMOTE_ROOT}'" >&2
    exit 1
  fi
fi

if [[ ${RUN_SMOKE} -eq 1 ]]; then
  echo "[p160] Esperando healthcheck en puerto ${PORT}"
  pct exec "${CT_ID}" -- bash -lc \
    "for i in \$(seq 1 30); do curl -fsS http://127.0.0.1:${PORT}/health >/dev/null && exit 0; sleep 1; done; exit 1"
  echo "[p160] Ejecutando smoke tests en CT ${CT_ID}"
  pct exec "${CT_ID}" -- bash -lc "cd ${REMOTE_ROOT} && ./scripts/smoke_pct160.sh"
fi

echo "[p160] Push completado."
