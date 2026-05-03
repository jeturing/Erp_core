"""
Odoo Website Configurator
Configura registros website en la BD Odoo del tenant para soporte multi-website
por subdominio interno.

Estrategia de multi-website (compatible con dbfilter=^%d$):
  - Cada website en Odoo tiene domain = https://{bd}.{alias}.sajet.us
  - El subdominio interno permite que dbfilter seleccione la BD correctamente
    (%d = primer segmento del Host = nombre de BD)
  - Nginx mapea dominios externos a subdominios internos transparentemente
  - El usuario ve su dominio real en el browser; Odoo trabaja con subdominios

Cuando se activa un dominio externo (ej: evolucionamujer.com) para un tenant
(ej: BD techeels), este servicio:
  1. Genera el subdominio interno: techeels.em.sajet.us
  2. Se conecta a la BD Odoo del tenant en CT105
  3. Verifica si ya existe un website con ese subdominio
  4. Si no existe, crea o actualiza un registro website con el subdominio interno
"""

import logging
import os
import re
import subprocess
from typing import Dict, Any, Optional, Tuple

from ..config import CT105_IP, ODOO_DB_USER, ODOO_DB_PASSWORD

logger = logging.getLogger("odoo_website_configurator")

# Conexión directa a PostgreSQL de CT105
ODOO_DB_HOST = CT105_IP
ODOO_DB_PORT = "5432"


def _run_psql(
    tenant_db: str,
    sql: str,
    fetch: bool = True,
) -> Tuple[int, str, str]:
    """
    Ejecuta SQL en la BD Odoo del tenant vía psql directo a CT105.
    Usa variables de entorno PGPASSWORD para autenticación.
    """
    if not re.fullmatch(r"[a-z0-9_]{3,63}", tenant_db or ""):
        return 1, "", "Tenant DB inválida"
    env = {**os.environ, "PGPASSWORD": ODOO_DB_PASSWORD or ""}
    cmd = [
        "psql",
        "-h", ODOO_DB_HOST,
        "-p", ODOO_DB_PORT,
        "-U", ODOO_DB_USER,
        "-d", tenant_db,
        "-t",
        "-A",
        "-c", sql,
    ]
    r = subprocess.run(
        cmd, env=env, capture_output=True, text=True, timeout=15
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


class OdooWebsiteConfigurator:
    """
    Configura websites en la BD Odoo de un tenant para multi-website.
    """

    def configure_website(
        self,
        tenant_db: str,
        external_domain: str,
        internal_subdomain: str,
        website_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Asegura que exista un website en Odoo con el subdominio interno.

        El subdominio interno (ej: techeels.em.sajet.us) se usa como domain
        en Odoo para que el website module pueda matchear correctamente
        con dbfilter=^%d$.

        Si ya existe un website con ese subdominio → no-op.
        Si existe un website con el dominio externo → actualiza al subdominio.
        Si existe un website sin dominio asignado → asigna el subdominio.
        Si no existe → crea uno nuevo.

        Args:
            tenant_db: Nombre de la BD Odoo del tenant (ej: techeels)
            external_domain: Dominio externo original (ej: evolucionamujer.com)
            internal_subdomain: Subdominio interno (ej: techeels.em.sajet.us)
            website_name: Nombre opcional para el website
        """
        logger.info(
            f"Configurando website Odoo: {external_domain} → "
            f"{internal_subdomain} en BD {tenant_db}"
        )

        try:
            internal_domain_url = f"https://{internal_subdomain}"
            external_domain_url = f"https://{external_domain}"

            # 1. Verificar si ya existe un website con el subdominio interno
            rc, out, err = _run_psql(
                tenant_db,
                f"SELECT id, name, domain FROM website "
                f"WHERE domain = '{internal_domain_url}' "
                f"LIMIT 1;"
            )
            if rc != 0:
                return {"success": False, "error": f"Error consultando BD {tenant_db}: {err}"}

            if out:
                parts = out.split("|")
                return {
                    "success": True,
                    "action": "already_exists",
                    "website_id": int(parts[0]),
                    "website_name": parts[1] if len(parts) > 1 else "",
                    "domain": parts[2] if len(parts) > 2 else "",
                    "internal_subdomain": internal_subdomain,
                    "message": f"Website ya configurado con {internal_subdomain}",
                }

            # 2. Verificar si existe un website con el dominio externo (migración)
            rc, out, err = _run_psql(
                tenant_db,
                f"SELECT id, name, domain FROM website "
                f"WHERE domain = '{external_domain_url}' OR domain = '{external_domain}' "
                f"LIMIT 1;"
            )
            if rc == 0 and out:
                # Migrar de dominio externo a subdominio interno
                parts = out.split("|")
                website_id = int(parts[0])
                _run_psql(
                    tenant_db,
                    f"UPDATE website SET domain = '{internal_domain_url}' "
                    f"WHERE id = {website_id};"
                )
                logger.info(
                    f"Website {website_id} migrado de {external_domain} "
                    f"a {internal_subdomain}"
                )
                return {
                    "success": True,
                    "action": "migrated",
                    "website_id": website_id,
                    "domain": internal_domain_url,
                    "internal_subdomain": internal_subdomain,
                    "message": f"Website migrado a subdominio interno {internal_subdomain}",
                }

            # 3. Buscar un website sin dominio que se pueda reutilizar
            # (excluir el website ID=1 que suele ser el default/Admin)
            rc, out, err = _run_psql(
                tenant_db,
                "SELECT id, name FROM website "
                "WHERE (domain IS NULL OR domain = '') AND id > 1 "
                "ORDER BY id LIMIT 1;"
            )

            if rc == 0 and out:
                parts = out.split("|")
                website_id = int(parts[0])
                name = website_name or external_domain.split(".")[0].title()

                _run_psql(
                    tenant_db,
                    f"UPDATE website SET domain = '{internal_domain_url}', "
                    f"name = '{name}' "
                    f"WHERE id = {website_id};"
                )
                logger.info(f"Website {website_id} actualizado con {internal_subdomain}")

                return {
                    "success": True,
                    "action": "updated",
                    "website_id": website_id,
                    "domain": internal_domain_url,
                    "internal_subdomain": internal_subdomain,
                    "message": f"Website existente actualizado con {internal_subdomain}",
                }

            # 4. Crear un nuevo website
            name = website_name or external_domain.split(".")[0].replace("-", " ").title()

            rc, company_out, _ = _run_psql(
                tenant_db,
                "SELECT id FROM res_company ORDER BY id LIMIT 1;"
            )
            company_id = int(company_out) if rc == 0 and company_out else 1

            rc, user_out, _ = _run_psql(
                tenant_db,
                "SELECT id FROM res_users WHERE login = 'admin' OR id = 2 ORDER BY id LIMIT 1;"
            )
            user_id = int(user_out) if rc == 0 and user_out else 2

            rc, lang_out, _ = _run_psql(
                tenant_db,
                "SELECT id FROM res_lang WHERE active = true ORDER BY id LIMIT 1;"
            )
            lang_id = int(lang_out) if rc == 0 and lang_out else 1

            insert_sql = (
                f"INSERT INTO website (name, domain, company_id, user_id, "
                f"default_lang_id, create_uid, write_uid, sequence, "
                f"create_date, write_date) "
                f"VALUES ('{name}', '{internal_domain_url}', {company_id}, {user_id}, "
                f"{lang_id}, {user_id}, {user_id}, 10, "
                f"NOW(), NOW()) RETURNING id;"
            )
            rc, new_id_out, err = _run_psql(tenant_db, insert_sql)

            if rc != 0:
                return {"success": False, "error": f"Error creando website: {err}"}

            website_id = int(new_id_out)
            logger.info(f"Website {website_id} creado con {internal_subdomain} en BD {tenant_db}")

            return {
                "success": True,
                "action": "created",
                "website_id": website_id,
                "domain": internal_domain_url,
                "internal_subdomain": internal_subdomain,
                "message": f"Nuevo website creado con subdominio {internal_subdomain}",
            }

        except Exception as e:
            logger.error(f"Error configurando website Odoo: {e}")
            return {"success": False, "error": str(e)}

    def remove_website_domain(
        self,
        tenant_db: str,
        external_domain: str,
        internal_subdomain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Elimina el dominio de un website Odoo (no borra el website, solo limpia el dominio).
        Busca tanto por subdominio interno como por dominio externo (compatibilidad).
        """
        logger.info(f"Eliminando dominio de website en BD {tenant_db}")

        try:
            # Construir condiciones de búsqueda
            conditions = []
            if internal_subdomain:
                conditions.append(f"domain = 'https://{internal_subdomain}'")
            conditions.append(f"domain = 'https://{external_domain}'")
            conditions.append(f"domain = '{external_domain}'")
            where = " OR ".join(conditions)

            rc, out, err = _run_psql(
                tenant_db,
                f"UPDATE website SET domain = NULL "
                f"WHERE {where} "
                f"RETURNING id;"
            )

            if rc != 0:
                return {"success": False, "error": f"Error: {err}"}

            if out:
                return {
                    "success": True,
                    "website_id": int(out),
                    "message": f"Dominio eliminado del website",
                }

            return {
                "success": True,
                "message": f"No se encontró website con dominio {external_domain}",
            }

        except Exception as e:
            logger.error(f"Error eliminando dominio de website: {e}")
            return {"success": False, "error": str(e)}

    def list_websites(self, tenant_db: str) -> Dict[str, Any]:
        """Lista todos los websites de un tenant Odoo."""
        try:
            rc, out, err = _run_psql(
                tenant_db,
                "SELECT id, name, domain, company_id FROM website ORDER BY id;"
            )

            if rc != 0:
                return {"success": False, "error": f"Error: {err}"}

            websites = []
            for line in out.split("\n"):
                if line.strip():
                    parts = line.split("|")
                    websites.append({
                        "id": int(parts[0]) if parts[0] else 0,
                        "name": parts[1] if len(parts) > 1 else "",
                        "domain": parts[2] if len(parts) > 2 else "",
                        "company_id": int(parts[3]) if len(parts) > 3 and parts[3] else 0,
                    })

            return {"success": True, "websites": websites}

        except Exception as e:
            return {"success": False, "error": str(e)}
