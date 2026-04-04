#!/usr/bin/env python3
"""
Odoo Database Watcher
Monitorea PostgreSQL y detecta nuevas bases de datos
Crea automáticamente registros DNS en Cloudflare para cada BD nueva

Ejecutarse como servicio systemd en el servidor Odoo
"""

import subprocess
import time
import json
import os
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
DB_WATCHER_STATE_FILE = "/var/lib/odoo/db_watcher_state.json"
DOMAINS_CONFIG_FILE = "/opt/odoo/config/domains.json"
DOMAIN = os.getenv("ODOO_DOMAIN", "sajet.us")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CF_ZONES = {}
CF_TUNNEL_ID = os.getenv("CF_TUNNEL_ID", "")
CHECK_INTERVAL = int(os.getenv("DB_WATCHER_INTERVAL", "10"))

# Cargar configuración de dominios
if os.path.exists(DOMAINS_CONFIG_FILE):
    try:
        with open(DOMAINS_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            CF_ZONES = config.get("zones", {})
            CF_TUNNEL_ID = config.get("tunnel_id", CF_TUNNEL_ID)
            logger.info(f"Dominios cargados: {list(CF_ZONES.keys())}")
    except Exception as e:
        logger.error(f"Error cargando {DOMAINS_CONFIG_FILE}: {e}")


def load_state():
    """Carga el estado anterior de BDs conocidas"""
    if os.path.exists(DB_WATCHER_STATE_FILE):
        try:
            with open(DB_WATCHER_STATE_FILE, 'r') as f:
                return json.load(f)
        except:
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


def create_cloudflare_dns(subdomain, domain):
    """Crea registro CNAME en Cloudflare"""
    if not CF_API_TOKEN or not CF_ZONES:
        logger.warning(f"Cloudflare no configurado, no se crea DNS para {subdomain}")
        return False
    
    zone_id = CF_ZONES.get(domain)
    if not zone_id:
        logger.error(f"Zone ID no encontrado para {domain}")
        return False
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Verificar si ya existe
        resp = requests.get(
            url, headers=headers,
            params={"type": "CNAME", "name": f"{subdomain}.{domain}"},
            timeout=10
        )
        if resp.status_code == 200 and resp.json().get("result"):
            logger.info(f"DNS ya existe: {subdomain}.{domain}")
            return True
        
        # Crear nuevo
        data = {
            "type": "CNAME",
            "name": subdomain,
            "content": f"{CF_TUNNEL_ID}.cfargotunnel.com",
            "ttl": 1,
            "proxied": True,
            "comment": f"Auto-provisioned {subdomain} ({datetime.now().isoformat()})"
        }
        
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        success = resp.json().get("success", False)
        
        if success:
            logger.info(f"✓ DNS creado: {subdomain}.{domain}")
            return True
        else:
            logger.error(f"Error Cloudflare: {resp.json().get('errors')}")
            return False
    except Exception as e:
        logger.error(f"Error creando DNS: {e}")
        return False


def watch_databases():
    """Loop principal que monitorea BDs"""
    logger.info(f"DB Watcher iniciado (intervalo: {CHECK_INTERVAL}s)")
    logger.info(f"Dominio: {DOMAIN}")
    logger.info(f"Túnel Cloudflare: {CF_TUNNEL_ID}")
    
    state = load_state()
    known_dbs = set(state.get("databases", {}).keys())
    
    try:
        while True:
            try:
                current_dbs = set(get_databases())
                new_dbs = current_dbs - known_dbs
                deleted_dbs = known_dbs - current_dbs
                
                # Procesar BDs nuevas
                if new_dbs:
                    logger.info(f"Nuevas BDs detectadas: {new_dbs}")
                    for db in new_dbs:
                        # Usar el nombre de BD como subdomain
                        dns_created = create_cloudflare_dns(db, DOMAIN)
                        state["databases"][db] = {
                            "created_at": datetime.now().isoformat(),
                            "dns_created": dns_created,
                            "status": "active"
                        }
                
                # Procesar BDs eliminadas
                if deleted_dbs:
                    logger.info(f"BDs eliminadas detectadas: {deleted_dbs}")
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
