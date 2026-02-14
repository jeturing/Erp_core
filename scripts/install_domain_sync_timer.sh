#!/usr/bin/env bash
set -euo pipefail

PCT_ID="${1:-105}"
LOCAL_SCRIPT="/opt/Erp_core/scripts/domain_sync.sh"
REMOTE_SCRIPT="/opt/scripts/domain_sync.sh"

echo "[1/4] Copiando domain_sync.sh a PCT ${PCT_ID}"
cat "${LOCAL_SCRIPT}" | pct exec "${PCT_ID}" -- bash -lc "mkdir -p /opt/scripts && cat > ${REMOTE_SCRIPT} && chmod +x ${REMOTE_SCRIPT}"

echo "[2/4] Creando service/timer systemd"
pct exec "${PCT_ID}" -- bash -lc 'cat > /etc/systemd/system/domain-sync.service << "EOF"
[Unit]
Description=Domain Sync from ERP Core DB to Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/scripts/domain_sync.sh
User=root
Group=root
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=/etc/cloudflared /var/log /opt/scripts

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/domain-sync.timer << "EOF"
[Unit]
Description=Run Domain Sync every 2 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=2min
AccuracySec=30s
Persistent=true
Unit=domain-sync.service

[Install]
WantedBy=timers.target
EOF'

echo "[3/4] Recargando daemon y habilitando timer"
pct exec "${PCT_ID}" -- bash -lc 'systemctl daemon-reload && systemctl enable --now domain-sync.timer'

echo "[4/4] Ejecución de prueba"
pct exec "${PCT_ID}" -- bash -lc 'systemctl start domain-sync.service; systemctl status domain-sync.service --no-pager | head -15; echo; tail -20 /var/log/domain_sync.log || true'

echo "OK: timer instalado en PCT ${PCT_ID}"