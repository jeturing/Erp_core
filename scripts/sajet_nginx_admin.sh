#!/usr/bin/env bash

set -euo pipefail

LOCAL_PATHS=(
  "/etc/nginx/sites-available/external-domains"
  "/etc/nginx/conf.d/odoo_http_routes.map"
  "/etc/nginx/conf.d/odoo_chat_routes.map"
)

REMOTE_PATHS=(
  "/etc/nginx/sites-enabled/odoo"
)

usage() {
  cat <<'EOF' >&2
Usage:
  sajet-nginx-admin read-local <path>
  sajet-nginx-admin write-local <path> <source_file>
  sajet-nginx-admin test-local
  sajet-nginx-admin reload-local
  sajet-nginx-admin test-and-reload-local
  sajet-nginx-admin read-remote <node_ip> <path>
  sajet-nginx-admin write-remote <node_ip> <path> <source_file>
  sajet-nginx-admin test-remote <node_ip>
  sajet-nginx-admin reload-remote <node_ip>
  sajet-nginx-admin test-and-reload-remote <node_ip>
EOF
  exit 64
}

contains() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    if [[ "$item" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

assert_local_path() {
  local path="$1"
  contains "$path" "${LOCAL_PATHS[@]}" || {
    echo "Ruta local no permitida: $path" >&2
    exit 65
  }
}

assert_remote_path() {
  local path="$1"
  contains "$path" "${REMOTE_PATHS[@]}" || {
    echo "Ruta remota no permitida: $path" >&2
    exit 65
  }
}

assert_node_ip() {
  local node_ip="$1"
  if [[ ! "$node_ip" =~ ^10\.10\.10\.[0-9]{1,3}$ ]]; then
    echo "Nodo no permitido: $node_ip" >&2
    exit 66
  fi
}

ssh_root() {
  local node_ip="$1"
  shift
  ssh -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5 "root@${node_ip}" "$@"
}

scp_root() {
  local source_file="$1"
  local node_ip="$2"
  local target_path="$3"
  scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=5 "$source_file" "root@${node_ip}:${target_path}"
}

cmd="${1:-}"
[[ -n "$cmd" ]] || usage
shift || true

case "$cmd" in
  read-local)
    [[ $# -eq 1 ]] || usage
    assert_local_path "$1"
    cat -- "$1"
    ;;
  write-local)
    [[ $# -eq 2 ]] || usage
    assert_local_path "$1"
    install -m 0644 "$2" "$1"
    ;;
  test-local)
    [[ $# -eq 0 ]] || usage
    nginx -t
    ;;
  reload-local)
    [[ $# -eq 0 ]] || usage
    systemctl reload nginx
    ;;
  test-and-reload-local)
    [[ $# -eq 0 ]] || usage
    nginx -t
    systemctl reload nginx
    ;;
  read-remote)
    [[ $# -eq 2 ]] || usage
    assert_node_ip "$1"
    assert_remote_path "$2"
    ssh_root "$1" "cat -- '$2'"
    ;;
  write-remote)
    [[ $# -eq 3 ]] || usage
    assert_node_ip "$1"
    assert_remote_path "$2"
    scp_root "$3" "$1" "$2"
    ;;
  test-remote)
    [[ $# -eq 1 ]] || usage
    assert_node_ip "$1"
    ssh_root "$1" "nginx -t"
    ;;
  reload-remote)
    [[ $# -eq 1 ]] || usage
    assert_node_ip "$1"
    ssh_root "$1" "systemctl reload nginx"
    ;;
  test-and-reload-remote)
    [[ $# -eq 1 ]] || usage
    assert_node_ip "$1"
    ssh_root "$1" "nginx -t && systemctl reload nginx"
    ;;
  *)
    usage
    ;;
esac
