#!/usr/bin/env python3
"""
Odoo Database Watcher — MODO AUDITOR (solo lectura)

Monitorea las bases de datos de PostgreSQL y registra cambios en el log.
NO crea registros DNS, NO provisiona tenants, NO modifica Cloudflare.

Toda acción de provisioning se maneja desde SAJET (tenants.py).
Este script solo detecta y reporta.

Ejecutar como servicio systemd o con: python3 odoo_db_watcher.py
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime

# ─── Configuración ───
DOMAIN = "sajet.us"
CHECK_INTERVAL = 30  # segundos entre verificaciones
STATE_FILE = "/var/lib/odoo/db_watcher_state.json"
LOG_FILE = "/var/log/odoo/db_watcher.log"

# BDs del sistema e infraestructura — nunca reportar como "nuevas"
EXCLUDED_DBS = {
    # PostgreSQL sistema
    'postgres', 'template0', 'template1',
    # SAJET interno
    'template_tenant', 'root', 'erp_core_db',
    # Infraestructura Jeturing
    'n8n', 'segrd', 'segrd_forensics', 'grafana', 'prometheus',
    'glitchtip', 'keycloak', 'nextcloud', 'gitea', 'minio',
    'wazuh', 'thehive', 'cortex', 'pentagi', 'ollama',
    'redis', 'auth0',
    # Cloudflare tunnels y servicios
    'tunnel', 'cloudflare', 'cf_tunnel', 'backup',
    # Bases de mantenimiento
    'test', 'test_db', 'demo', 'staging',
}


def setup_logging() -> logging.Logger:
    """Configura logging."""
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    handlers = [logging.StreamHandler()]
    if os.path.exists(os.path.dirname(LOG_FILE) or '.'):
        handlers.insert(0, logging.FileHandler(LOG_FILE))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers,
    )
    return logging.getLogger('db_watcher_auditor')


logger = setup_logging()


def is_valid_odoo_database(db_name: str) -> bool:
    """Verifica que la BD sea realmente Odoo (tiene ir_module_module con base instalado)."""
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-d', db_name, '-t', '-c',
             "SELECT 1 FROM ir_module_module WHERE name='base' AND state='installed' LIMIT 1;"],
            capture_output=True, text=True, timeout=5,
        )
        return '1' in result.stdout
    except Exception:
        return False


class OdooDBWatcher:
    """Monitorea bases de datos — MODO AUDITOR (solo logging, sin provisioning)."""

    def __init__(self):
        self.known_dbs = self._load_state()

    def _load_state(self) -> set:
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data.get('databases', []))
            except Exception:
                pass
        return set()

    def _save_state(self):
        state_dir = os.path.dirname(STATE_FILE)
        if state_dir and not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    'databases': list(self.known_dbs),
                    'last_update': datetime.now().isoformat(),
                    'mode': 'auditor',
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar estado: {e}")

    def get_current_databases(self) -> set:
        try:
            result = subprocess.run(
                ['sudo', '-u', 'postgres', 'psql', '-t', '-c',
                 "SELECT datname FROM pg_database WHERE datistemplate = false;"],
                capture_output=True, text=True, timeout=10,
            )
            dbs = {db.strip() for db in result.stdout.split('\n') if db.strip()}
            return dbs - EXCLUDED_DBS
        except Exception as e:
            logger.error(f"Error obteniendo bases de datos: {e}")
            return set()

    def check_for_new_databases(self):
        """Detecta cambios y los registra en log — NO provisiona nada."""
        current_dbs = self.get_current_databases()
        new_dbs = current_dbs - self.known_dbs
        removed_dbs = self.known_dbs - current_dbs

        if new_dbs:
            for db_name in sorted(new_dbs):
                is_odoo = is_valid_odoo_database(db_name)
                tag = "ODOO" if is_odoo else "NO-ODOO"
                logger.info(f"📋 [AUDITOR] Nueva BD detectada: {db_name} [{tag}]")
                if is_odoo:
                    logger.info(f"   ℹ️  Para provisionar: usar SAJET Admin → /api/tenants o panel Tenants")

        if removed_dbs:
            for db_name in sorted(removed_dbs):
                logger.info(f"🗑️ [AUDITOR] BD eliminada: {db_name}")

        self.known_dbs = current_dbs
        self._save_state()

    def run(self):
        logger.info("=" * 60)
        logger.info("🔍 Odoo Database Watcher — MODO AUDITOR")
        logger.info(f"   Dominio: {DOMAIN}")
        logger.info(f"   Intervalo: {CHECK_INTERVAL}s")
        logger.info(f"   ⚠️  NO crea DNS ni provisiona — solo observa")
        logger.info("=" * 60)

        current_dbs = self.get_current_databases()
        logger.info(f"📊 Bases de datos existentes: {', '.join(sorted(current_dbs))}")

        if not self.known_dbs:
            logger.info("Primera ejecución — registrando BDs existentes")
            self.known_dbs = current_dbs
            self._save_state()

        while True:
            try:
                self.check_for_new_databases()
            except Exception as e:
                logger.error(f"Error en verificación: {e}")
            time.sleep(CHECK_INTERVAL)


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            watcher = OdooDBWatcher()
            dbs = watcher.get_current_databases()
            print(f"Bases de datos (excluidas infra): {', '.join(sorted(dbs))}")
        elif sys.argv[1] == '--check':
            watcher = OdooDBWatcher()
            watcher.check_for_new_databases()
        elif sys.argv[1] == '--help':
            print("""
Odoo Database Watcher — MODO AUDITOR (solo lectura)

Uso:
  python3 odoo_db_watcher.py           # Ejecutar como servicio
  python3 odoo_db_watcher.py --check   # Verificación única
  python3 odoo_db_watcher.py --list    # Listar bases de datos
            """)
        else:
            print(f"Opción desconocida: {sys.argv[1]}")
            print("Nota: --provision fue removido. Usar SAJET Admin para provisionar.")
            sys.exit(1)
    else:
        watcher = OdooDBWatcher()
        watcher.run()


if __name__ == '__main__':
    main()
