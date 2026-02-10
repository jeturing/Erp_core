#!/usr/bin/env python3
"""
Odoo Database Watcher - Auto-provisioning de subdominios Cloudflare

Este servicio monitorea las bases de datos de PostgreSQL y automáticamente:
1. Detecta nuevas bases de datos de Odoo
2. Crea el registro DNS CNAME en Cloudflare
3. Configura el web.base.url en Odoo

Ejecutar como servicio systemd o con: python3 odoo_db_watcher.py
"""

import os
import sys
import time
import json
import logging
import subprocess
import requests
import psycopg2
from datetime import datetime
from pathlib import Path

# Configuración
DOMAIN = "sajet.us"
CF_ZONE_ID = "4a83b88793ac3688486ace69b6ae80f9"
CF_TUNNEL_ID = "da2bc763-a93b-41f5-9a22-1731403127e3"
CHECK_INTERVAL = 30  # segundos entre verificaciones
STATE_FILE = "/var/lib/odoo/db_watcher_state.json"
LOG_FILE = "/var/log/odoo/db_watcher.log"

# Bases de datos a ignorar (sistema)
IGNORED_DBS = {'postgres', 'template0', 'template1'}

# Cargar credenciales
def load_credentials():
    """Carga credenciales desde archivos de configuración."""
    creds = {}
    
    # Buscar archivo de credenciales
    cred_paths = [
        "/opt/Erp_core/Cloudflare/.cf_credentials",
        "/opt/odoo/scripts/.cf_credentials",
        "/etc/cloudflare/credentials",
        os.path.expanduser("~/.cf_credentials")
    ]
    
    for path in cred_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        creds[key.strip()] = value.strip().strip('"\'')
            break
    
    # Priorizar el token con minúsculas (parece ser el correcto)
    return creds.get('cloudflare_api_token') or creds.get('CLOUDFLARE_API_TOKEN', '')

# Configurar logging
def setup_logging():
    """Configura el sistema de logging."""
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE) if os.path.exists(os.path.dirname(LOG_FILE) or '.') else logging.StreamHandler(),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('db_watcher')

logger = setup_logging()

class CloudflareManager:
    """Gestiona operaciones con la API de Cloudflare."""
    
    def __init__(self, api_token: str, zone_id: str):
        self.api_token = api_token
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_dns_record(self, subdomain: str) -> dict | None:
        """Obtiene un registro DNS existente."""
        hostname = f"{subdomain}.{DOMAIN}"
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
        params = {"type": "CNAME", "name": hostname}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            data = response.json()
            if data.get('success') and data.get('result'):
                return data['result'][0]
        except Exception as e:
            logger.error(f"Error obteniendo DNS para {subdomain}: {e}")
        return None
    
    def create_dns_record(self, subdomain: str) -> bool:
        """Crea un registro CNAME para el subdominio."""
        hostname = f"{subdomain}.{DOMAIN}"
        
        # Verificar si ya existe
        if self.get_dns_record(subdomain):
            logger.info(f"DNS ya existe para {hostname}")
            return True
        
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
        data = {
            "type": "CNAME",
            "name": subdomain,
            "content": f"{CF_TUNNEL_ID}.cfargotunnel.com",
            "ttl": 1,  # Auto
            "proxied": True,
            "comment": f"Auto-created by db_watcher for Odoo tenant {subdomain}"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            result = response.json()
            
            if result.get('success'):
                logger.info(f"✅ DNS creado: {hostname} -> tunnel")
                return True
            else:
                errors = result.get('errors', [])
                error_msg = errors[0].get('message', 'Unknown') if errors else 'Unknown'
                logger.error(f"❌ Error creando DNS para {hostname}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción creando DNS para {hostname}: {e}")
            return False
    
    def delete_dns_record(self, subdomain: str) -> bool:
        """Elimina un registro DNS."""
        record = self.get_dns_record(subdomain)
        if not record:
            return True
        
        url = f"{self.base_url}/zones/{self.zone_id}/dns_records/{record['id']}"
        
        try:
            response = requests.delete(url, headers=self.headers, timeout=10)
            result = response.json()
            if result.get('success'):
                logger.info(f"✅ DNS eliminado: {subdomain}.{DOMAIN}")
                return True
        except Exception as e:
            logger.error(f"Error eliminando DNS: {e}")
        return False


class OdooDBWatcher:
    """Monitorea bases de datos de Odoo y provisiona automáticamente."""
    
    def __init__(self):
        self.cf_token = load_credentials()
        if not self.cf_token:
            logger.error("❌ No se encontró token de Cloudflare")
            sys.exit(1)
        
        self.cf = CloudflareManager(self.cf_token, CF_ZONE_ID)
        self.known_dbs = self._load_state()
        
        # Conexión a PostgreSQL
        self.pg_user = self._detect_pg_user()
        logger.info(f"Usuario PostgreSQL detectado: {self.pg_user}")
    
    def _detect_pg_user(self) -> str:
        """Detecta el usuario de PostgreSQL para Odoo."""
        try:
            result = subprocess.run(
                ['sudo', '-u', 'postgres', 'psql', '-t', '-c',
                 "SELECT usename FROM pg_user WHERE usename NOT IN ('postgres') LIMIT 1;"],
                capture_output=True, text=True, timeout=5
            )
            user = result.stdout.strip()
            return user if user else 'odoo'
        except:
            return 'odoo'
    
    def _load_state(self) -> set:
        """Carga el estado anterior de bases de datos conocidas."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    return set(data.get('databases', []))
            except:
                pass
        return set()
    
    def _save_state(self):
        """Guarda el estado actual."""
        state_dir = os.path.dirname(STATE_FILE)
        if state_dir and not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)
        
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    'databases': list(self.known_dbs),
                    'last_update': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar estado: {e}")
    
    def get_current_databases(self) -> set:
        """Obtiene la lista actual de bases de datos."""
        try:
            result = subprocess.run(
                ['sudo', '-u', 'postgres', 'psql', '-t', '-c',
                 "SELECT datname FROM pg_database WHERE datistemplate = false;"],
                capture_output=True, text=True, timeout=10
            )
            dbs = {db.strip() for db in result.stdout.split('\n') if db.strip()}
            return dbs - IGNORED_DBS
        except Exception as e:
            logger.error(f"Error obteniendo bases de datos: {e}")
            return set()
    
    def is_odoo_database(self, db_name: str) -> bool:
        """Verifica si una base de datos es de Odoo (tiene tabla ir_config_parameter)."""
        try:
            result = subprocess.run(
                ['sudo', '-u', 'postgres', 'psql', '-d', db_name, '-t', '-c',
                 "SELECT 1 FROM information_schema.tables WHERE table_name = 'ir_config_parameter' LIMIT 1;"],
                capture_output=True, text=True, timeout=5
            )
            return '1' in result.stdout
        except:
            return False
    
    def configure_odoo_base_url(self, db_name: str):
        """Configura web.base.url en la base de datos de Odoo."""
        base_url = f"https://{db_name}.{DOMAIN}"
        
        try:
            sql = f"""
            INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
            VALUES ('web.base.url', '{base_url}', NOW(), NOW(), 1, 1)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, write_date = NOW();
            
            INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
            VALUES ('web.base.url.freeze', 'True', NOW(), NOW(), 1, 1)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, write_date = NOW();
            """
            
            subprocess.run(
                ['sudo', '-u', 'postgres', 'psql', '-d', db_name, '-c', sql],
                capture_output=True, timeout=10
            )
            logger.info(f"✅ web.base.url configurado: {base_url}")
            return True
        except Exception as e:
            logger.error(f"Error configurando base_url: {e}")
            return False
    
    def provision_tenant(self, db_name: str):
        """Provisiona un nuevo tenant (DNS + configuración)."""
        logger.info(f"🚀 Provisionando nuevo tenant: {db_name}")
        
        # Esperar un poco para que Odoo termine de inicializar
        time.sleep(5)
        
        # Verificar que es una BD de Odoo
        if not self.is_odoo_database(db_name):
            logger.info(f"⏭️ {db_name} no es una BD de Odoo, ignorando")
            return
        
        # Crear DNS en Cloudflare
        if self.cf.create_dns_record(db_name):
            # Configurar Odoo
            self.configure_odoo_base_url(db_name)
            logger.info(f"✅ Tenant {db_name} provisionado correctamente")
            logger.info(f"   URL: https://{db_name}.{DOMAIN}")
        else:
            logger.error(f"❌ Fallo al provisionar {db_name}")
    
    def check_for_new_databases(self):
        """Verifica si hay nuevas bases de datos."""
        current_dbs = self.get_current_databases()
        new_dbs = current_dbs - self.known_dbs
        removed_dbs = self.known_dbs - current_dbs
        
        # Procesar nuevas BDs
        for db_name in new_dbs:
            logger.info(f"📦 Nueva base de datos detectada: {db_name}")
            self.provision_tenant(db_name)
        
        # Log de BDs eliminadas (no eliminamos DNS automáticamente por seguridad)
        for db_name in removed_dbs:
            logger.info(f"🗑️ Base de datos eliminada: {db_name}")
            logger.info(f"   DNS para {db_name}.{DOMAIN} debe eliminarse manualmente")
        
        # Actualizar estado
        self.known_dbs = current_dbs
        self._save_state()
    
    def run(self):
        """Ejecuta el watcher en loop."""
        logger.info("=" * 60)
        logger.info("🔍 Odoo Database Watcher iniciado")
        logger.info(f"   Dominio: {DOMAIN}")
        logger.info(f"   Intervalo: {CHECK_INTERVAL}s")
        logger.info(f"   Estado: {STATE_FILE}")
        logger.info("=" * 60)
        
        # Primera verificación - registrar BDs existentes
        current_dbs = self.get_current_databases()
        logger.info(f"📊 Bases de datos existentes: {', '.join(sorted(current_dbs))}")
        
        # Si es primera ejecución, solo registrar sin provisionar
        if not self.known_dbs:
            logger.info("Primera ejecución - registrando BDs existentes sin provisionar")
            self.known_dbs = current_dbs
            self._save_state()
        
        # Loop principal
        while True:
            try:
                self.check_for_new_databases()
            except Exception as e:
                logger.error(f"Error en verificación: {e}")
            
            time.sleep(CHECK_INTERVAL)


def main():
    """Punto de entrada principal."""
    # Verificar si se ejecuta con argumentos especiales
    if len(sys.argv) > 1:
        if sys.argv[1] == '--provision':
            # Provisionar una BD específica
            if len(sys.argv) < 3:
                print("Uso: db_watcher.py --provision <db_name>")
                sys.exit(1)
            
            db_name = sys.argv[2]
            watcher = OdooDBWatcher()
            watcher.provision_tenant(db_name)
            
        elif sys.argv[1] == '--list':
            # Listar BDs actuales
            watcher = OdooDBWatcher()
            dbs = watcher.get_current_databases()
            print(f"Bases de datos: {', '.join(sorted(dbs))}")
            
        elif sys.argv[1] == '--check':
            # Verificación única
            watcher = OdooDBWatcher()
            watcher.check_for_new_databases()
            
        elif sys.argv[1] == '--help':
            print("""
Odoo Database Watcher - Auto-provisioning de subdominios

Uso:
  python3 db_watcher.py           # Ejecutar como servicio
  python3 db_watcher.py --check   # Verificación única
  python3 db_watcher.py --list    # Listar bases de datos
  python3 db_watcher.py --provision <db>  # Provisionar BD específica
            """)
        else:
            print(f"Opción desconocida: {sys.argv[1]}")
            sys.exit(1)
    else:
        # Ejecutar como servicio
        watcher = OdooDBWatcher()
        watcher.run()


if __name__ == '__main__':
    main()
