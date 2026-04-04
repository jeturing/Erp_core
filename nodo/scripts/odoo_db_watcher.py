#!/usr/bin/env python3
"""
Odoo Database Watcher — MODO AUDITOR (read-only)
Monitorea PostgreSQL y detecta nuevas bases de datos.
Ya NO crea registros DNS en Cloudflare automáticamente.
Solo loguea las detecciones para auditoría.

El provisioning de DNS se maneja programáticamente desde SAJET
(provision_tenant → create_cloudflare_dns).

Ejecutarse como servicio systemd en el servidor Odoo.

Changelog:
- 2026-04-04: Convertido a auditor read-only. Ya no crea CNAMEs.
"""

import subprocess
import time
import json
import os
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
DB_WATCHER_STATE_FILE = "/var/lib/odoo/db_watcher_state.json"
DOMAIN = os.getenv("ODOO_DOMAIN", "sajet.us")
CHECK_INTERVAL = int(os.getenv("DB_WATCHER_INTERVAL", "30"))  # Aumentado a 30s (era 10s)

# BDs del sistema que se ignoran completamente
EXCLUDED_DBS = {
    'postgres', 'template0', 'template1',
    'template_tenant', 'erp_core_db', 'root',
    # Infraestructura — no son tenants Odoo
    'n8n', 'n8n_queue',
    'segrd', 'segrd_forensics',
    'glitchtip', 'sentry',
    'grafana', 'prometheus',
    'redis', 'minio',
    'wazuh', 'thehive', 'cortex', 'cassandra',
    'pentagi', 'ollama',
    'keycloak', 'auth0',
    'nextcloud', 'gitea',
}


def load_state():
    """Carga el estado anterior de BDs conocidas"""
    if os.path.exists(DB_WATCHER_STATE_FILE):
        try:
            with open(DB_WATCHER_STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"databases": {}}


def save_state(state):
    """Guarda el estado actual de BDs"""
    try:
        os.makedirs(os.path.dirname(DB_WATCHER_STATE_FILE), exist_ok=True)
        with open(DB_WATCHER_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Error guardando estado: {e}")


def get_databases():
    """Obtiene lista actual de BDs en PostgreSQL"""
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-t', '-c',
             "SELECT datname FROM pg_database WHERE datistemplate = false AND datname NOT IN ('postgres');"],
            capture_output=True, text=True, timeout=10
        )
        dbs = [db.strip() for db in result.stdout.split('\n') if db.strip()]
        return dbs
    except Exception as e:
        logger.error(f"Error obteniendo BDs: {e}")
        return []


def is_valid_odoo_database(db_name: str) -> bool:
    """Verifica que una BD sea realmente una instancia Odoo (tiene ir_module_module)."""
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-t', '-d', db_name, '-c',
             "SELECT 1 FROM ir_module_module WHERE name='base' AND state='installed' LIMIT 1;"],
            capture_output=True, text=True, timeout=5
        )
        return '1' in (result.stdout or '')
    except Exception:
        return False


def watch_databases():
    """Loop principal que monitorea BDs — MODO AUDITOR (solo reporta, no crea DNS)"""
    logger.info(f"DB Watcher iniciado en MODO AUDITOR (intervalo: {CHECK_INTERVAL}s)")
    logger.info(f"Dominio: {DOMAIN}")
    logger.info(f"⚠️  MODO READ-ONLY: No se crearán registros DNS automáticamente")
    logger.info(f"    DNS se gestiona desde SAJET provision_tenant()")

    state = load_state()
    known_dbs = set(state.get("databases", {}).keys())

    try:
        while True:
            try:
                current_dbs = set(get_databases())

                # Filtrar BDs excluidas
                current_dbs = {db for db in current_dbs if db not in EXCLUDED_DBS}

                new_dbs = current_dbs - known_dbs
                deleted_dbs = known_dbs - current_dbs

                # Reportar BDs nuevas (solo log, NO crear DNS)
                if new_dbs:
                    logger.info(f"📋 Nuevas BDs detectadas: {new_dbs}")
                    for db in new_dbs:
                        is_odoo = is_valid_odoo_database(db)
                        state["databases"][db] = {
                            "detected_at": datetime.now().isoformat(),
                            "is_odoo": is_odoo,
                            "dns_created": False,
                            "status": "detected",
                        }
                        if is_odoo:
                            logger.info(
                                f"  ✅ '{db}' es una BD Odoo válida. "
                                f"DNS debe crearse via SAJET provision_tenant() si no existe."
                            )
                        else:
                            logger.info(
                                f"  ⚠️  '{db}' NO es una BD Odoo válida. No se requiere DNS."
                            )

                # Reportar BDs eliminadas
                if deleted_dbs:
                    logger.info(f"🗑️  BDs eliminadas detectadas: {deleted_dbs}")
                    for db in deleted_dbs:
                        state["databases"].pop(db, None)

                # Actualizar estado conocido
                if new_dbs or deleted_dbs:
                    save_state(state)
                    known_dbs = current_dbs

                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Error en loop: {e}")
                time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info("DB Watcher detenido por usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")


if __name__ == "__main__":
    watch_databases()
