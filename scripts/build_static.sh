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
if ! npm ci; then
  echo "[build_static] ⚠️  package-lock desactualizado; ejecutando npm install para reconciliar dependencias"
  npm install
fi

echo "[build_static] Ejecutando checks (warnings no bloquean)"
npm run check || echo "[build_static] ⚠️  svelte-check reportó warnings/errores de tipos — build continúa"

echo "[build_static] Generando build"
npm run build

echo "[build_static] Publicando assets en ${STATIC_SPA_DIR}"
rm -rf "${STATIC_SPA_DIR}"
mkdir -p "${STATIC_SPA_DIR}"

# SvelteKit adapter-static outputs to build/, legacy Vite outputs to dist/
if [[ -d "${FRONTEND_DIR}/build" ]]; then
  cp -a "${FRONTEND_DIR}/build/." "${STATIC_SPA_DIR}/"
  echo "[build_static] Build completado (SvelteKit adapter-static)"
  echo "[build_static] Shell SPA: ${STATIC_SPA_DIR}/200.html"
elif [[ -d "${FRONTEND_DIR}/dist" ]]; then
  cp -a "${FRONTEND_DIR}/dist/." "${STATIC_SPA_DIR}/"
  echo "[build_static] Build completado (Vite legacy)"
  echo "[build_static] Shell SPA: ${STATIC_SPA_DIR}/index.html"
else
  echo "[build_static] No se encontró directorio de build (build/ ni dist/)" >&2
  exit 1
fi
