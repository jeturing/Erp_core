#!/usr/bin/env bash

set -euo pipefail

# deploy_to_server.sh
# Copiar el contenido del repositorio al servidor remoto usando rsync+ssh
# Requiere definir variables de entorno o pasarlas como argumentos.

show_help() {
  cat <<'EOF'
Usage: ./scripts/deploy_to_server.sh [--dry-run] [--service "sudo systemctl restart myapp"]

Environment variables (alternativa a args):
  SERVER_USER   - usuario SSH remoto
  SERVER_HOST   - host o IP remoto
  SERVER_PATH   - ruta remota donde desplegar (ej: /var/www/myapp)
  SSH_KEY       - ruta al private key SSH (opcional)
  SSH_PORT      - puerto SSH (opcional, default 22)

Examples:
  SERVER_USER=deploy SERVER_HOST=example.com SERVER_PATH=/var/www/myapp ./scripts/deploy_to_server.sh
  SSH_KEY=~/.ssh/id_rsa SERVER_USER=deploy SERVER_HOST=example.com SERVER_PATH=/var/www/myapp ./scripts/deploy_to_server.sh --service "sudo systemctl restart myapp"
  ./scripts/deploy_to_server.sh --dry-run
EOF
}

# Defaults
SSH_PORT=${SSH_PORT:-22}
DRY_RUN=""
SERVICE_CMD=""

# Parse simple flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN="--dry-run"
      shift
      ;;
    --service)
      SERVICE_CMD="$2"
      shift 2
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

# Validate required environment variables
: "${SERVER_USER:?Please set SERVER_USER}" 
: "${SERVER_HOST:?Please set SERVER_HOST}"
: "${SERVER_PATH:?Please set SERVER_PATH}"

SSH_OPTS=( -p "$SSH_PORT" )
if [ -n "${SSH_KEY-}" ]; then
  SSH_OPTS=( -i "$SSH_KEY" -p "$SSH_PORT" )
fi

RSYNC_EXCLUDES=( --exclude '.git' --exclude 'venv' --exclude '__pycache__' --exclude '.DS_Store' )

RSYNC_CMD=( rsync -az --delete "${RSYNC_EXCLUDES[@]}" )
if [ -n "$DRY_RUN" ]; then
  RSYNC_CMD+=( --dry-run )
fi
RSYNC_CMD+=( -e "ssh ${SSH_OPTS[*]}" ./ "$SERVER_USER@$SERVER_HOST:$SERVER_PATH" )

echo "Ejecutando rsync hacia $SERVER_HOST:$SERVER_PATH"
# Mostrar y ejecutar
echo "${RSYNC_CMD[*]}"
# Ejecutar
eval "${RSYNC_CMD[*]}"

if [ -n "$SERVICE_CMD" ]; then
  echo "Ejecutando comando remoto: $SERVICE_CMD"
  SSH_CMD=( ssh "${SSH_OPTS[@]}" "$SERVER_USER@$SERVER_HOST" "$SERVICE_CMD" )
  echo "${SSH_CMD[*]}"
  eval "${SSH_CMD[*]}"
fi

echo "Despliegue completado. Verifica en el servidor que los archivos estén correctos."
