#!/usr/bin/env bash

set -euo pipefail

SSH_HOST="${PROXMOX_SSH_HOST:-10.10.10.1}"
SSH_USER="${PROXMOX_SSH_USER:-root}"
SSH_KEY="${PROXMOX_SSH_KEY:-/root/.ssh/id_ed25519}"

usage() {
  cat <<'EOF' >&2
Usage:
  sajet-proxmox-admin pct-exec <pct_id> <command>
EOF
  exit 64
}

assert_pct_id() {
  local pct_id="$1"
  if [[ ! "$pct_id" =~ ^[0-9]+$ ]]; then
    echo "PCT no permitido: $pct_id" >&2
    exit 65
  fi
}

ssh_host() {
  local remote_cmd="$1"
  ssh \
    -i "$SSH_KEY" \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=no \
    -o IdentitiesOnly=yes \
    -o ConnectTimeout=10 \
    "${SSH_USER}@${SSH_HOST}" \
    "$remote_cmd"
}

cmd="${1:-}"
[[ -n "$cmd" ]] || usage
shift || true

case "$cmd" in
  pct-exec)
    [[ $# -eq 2 ]] || usage
    pct_id="$1"
    remote_bash_cmd="$2"
    assert_pct_id "$pct_id"
    printf -v quoted_bash_cmd '%q' "$remote_bash_cmd"
    ssh_host "pct exec ${pct_id} -- bash -lc ${quoted_bash_cmd}"
    ;;
  *)
    usage
    ;;
esac
