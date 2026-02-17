#!/usr/bin/env bash
set -euo pipefail

BASE="/usr/lib/python3/dist-packages/odoo/extra-addons"

# Detecta carpeta "new" o "New"
ORIGEN=$(find "$BASE" -maxdepth 1 -type d -iname 'new' | head -n1)
if [[ ! -d "$ORIGEN" ]]; then
  echo "❌ No se encontró carpeta 'new' o 'New' en $BASE"
  exit 1
fi

cd "$ORIGEN"

for zip in *.zip; do
  echo "🔄 Procesando: $zip"
  tmp=$(mktemp -d)
  unzip -q "$zip" -d "$tmp"
  module_dir=$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -n1)
  if [[ -z "$module_dir" ]]; then
    echo "⚠️  No se encontró carpeta interna en $zip, omitiendo."
    rm -rf "$tmp"
    continue
  fi
  name=$(basename "$module_dir")
  echo "   📦 Moviendo módulo '$name' a $BASE/"
  mv "$module_dir" "$BASE/"
  rm -rf "$tmp"
  echo "   ✅ Módulo '$name' listo."
done

echo "🎉 Todos los módulos han sido aplanados y movidos a '$BASE/'."
