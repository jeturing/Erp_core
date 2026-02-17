#!/bin/bash
# Eliminar un tenant
# Uso: ./delete_tenant.sh subdomain

SUBDOMAIN="${1:-}"
if [ -z "$SUBDOMAIN" ]; then
    echo "Uso: $0 subdomain"
    echo "Ejemplo: $0 cliente_antiguo"
    exit 1
fi

SUBDOMAIN=$(echo "$SUBDOMAIN" | tr '[:upper:]' '[:lower:]' | tr '-' '_')

echo "⚠️  Eliminando tenant: $SUBDOMAIN"
read -p "¿Confirmas? (escribe 'si' para confirmar): " confirm

if [ "$confirm" != "si" ]; then
    echo "Cancelado"
    exit 1
fi

echo "[*] Terminando conexiones..."
sudo -u postgres psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$SUBDOMAIN';" >/dev/null 2>&1

echo "[*] Eliminando BD..."
sudo -u postgres dropdb "$SUBDOMAIN" 2>/dev/null && echo "[✓] BD eliminada" || echo "[!] Error eliminando BD"
