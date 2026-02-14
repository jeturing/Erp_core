#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT=${PROJECT_ROOT:-"/opt/Erp_core"}
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
STATIC_SPA_DIR="${PROJECT_ROOT}/static/spa"

if [[ ! -d "${FRONTEND_DIR}" ]]; then
  echo "[build_static] frontend no encontrado en ${FRONTEND_DIR}" >&2
  exit 1
fi

echo "[build_static] Instalando dependencias frontend"
cd "${FRONTEND_DIR}"
npm ci

echo "[build_static] Ejecutando checks"
npm run check

echo "[build_static] Generando build"
npm run build

echo "[build_static] Publicando assets en ${STATIC_SPA_DIR}"
rm -rf "${STATIC_SPA_DIR}"
mkdir -p "${STATIC_SPA_DIR}"
cp -a "${FRONTEND_DIR}/dist/." "${STATIC_SPA_DIR}/"

echo "[build_static] Build completado"
echo "[build_static] Shell SPA: ${STATIC_SPA_DIR}/index.html"
