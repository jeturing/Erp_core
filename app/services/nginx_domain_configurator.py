"""
Nginx Domain Configurator
Automatiza la configuración de nginx en PCT160 y CT105 cuando se activa/desactiva
un dominio externo para un tenant Odoo.

Archivos que modifica:
  PCT160 (local):
    /etc/nginx/sites-available/erp          → 3 maps + server_name
    /etc/nginx/conf.d/odoo_http_routes.map  → dominio → backend
    /etc/nginx/conf.d/odoo_chat_routes.map  → dominio → backend
  CT105 (via SSH):
    /etc/nginx/sites-enabled/odoo           → 3 maps + server_name + proxy_redirect

Flujo:
  1. Leer archivos actuales
  2. Insertar entradas en maps y server_name
  3. Validar con nginx -t
  4. Recargar nginx
  5. Si falla, rollback automático
"""

import subprocess
import logging
import re
import shlex
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("nginx_configurator")

# ── Constantes ────────────────────────────────────────────────────────────────
CT105_IP = "10.10.10.100"
CT105_SSH = f"root@{CT105_IP}"
CT105_NGINX_PORT = 8080  # Puerto nginx en CT105 para dominios externos

PCT160_ERP_CONF = "/etc/nginx/sites-available/erp"
PCT160_HTTP_MAP = "/etc/nginx/conf.d/odoo_http_routes.map"
PCT160_CHAT_MAP = "/etc/nginx/conf.d/odoo_chat_routes.map"
CT105_ODOO_CONF = "/etc/nginx/sites-enabled/odoo"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_local(cmd: str, timeout: int = 15) -> Tuple[int, str, str]:
    """Ejecuta comando local y devuelve (rc, stdout, stderr)."""
    r = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _run_ct105(cmd: str, timeout: int = 15) -> Tuple[int, str, str]:
    """Ejecuta comando en CT105 via SSH."""
    safe = cmd.replace("'", "'\\''")
    full = f"ssh -o BatchMode=yes -o ConnectTimeout=5 {CT105_SSH} '{safe}'"
    return _run_local(full, timeout=timeout)


def _read_file_local(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def _write_file_local(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def _read_file_ct105(path: str) -> str:
    rc, out, err = _run_ct105(f"cat {path}")
    if rc != 0:
        raise RuntimeError(f"No se pudo leer {path} en CT105: {err}")
    return out


def _write_file_ct105(path: str, content: str) -> None:
    """Escribe archivo en CT105 via SSH + heredoc."""
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False)
    tmp.write(content)
    tmp.close()
    # Copiar via scp
    rc, _, err = _run_local(
        f"scp -o BatchMode=yes -o ConnectTimeout=5 {tmp.name} {CT105_SSH}:{path}",
        timeout=20,
    )
    os.unlink(tmp.name)
    if rc != 0:
        raise RuntimeError(f"No se pudo escribir {path} en CT105: {err}")


# ── Funciones de edición de nginx maps ────────────────────────────────────────

def _add_to_map(content: str, map_var: str, domain: str, value: str) -> str:
    """
    Agrega una entrada a un bloque 'map $host $map_var { ... }'.
    Inserta la línea justo antes del cierre '}' del map o antes de un comentario
    tipo '# --- Agregar más'.
    """
    if re.search(rf"^\s+{re.escape(domain)}\s", content, re.MULTILINE):
        return content  # Ya existe

    # Encontrar el bloque map correcto
    pattern = rf"(map\s+\S+\s+\${re.escape(map_var)}\s*\{{)(.*?)(\}})"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        logger.warning(f"Map ${map_var} no encontrado")
        return content

    map_body = match.group(2)
    entry = f"    {domain} {value};\n"

    # Insertar antes de '# --- Agregar' si existe, o antes del cierre
    marker = re.search(r"(\s*# --- Agregar.*\n)", map_body)
    if marker:
        new_body = map_body[: marker.start()] + "\n" + entry + map_body[marker.start() :]
    else:
        new_body = map_body + entry

    return content[: match.start()] + match.group(1) + new_body + match.group(3) + content[match.end() :]


def _remove_from_map(content: str, map_var: str, domain: str) -> str:
    """Elimina una entrada de un bloque map."""
    pattern = rf"^\s+{re.escape(domain)}\s+[^;]+;\s*\n"
    # Solo dentro del map correcto — hacemos un approach simple:
    # buscamos la línea completa con el domain y la eliminamos
    return re.sub(pattern, "", content, flags=re.MULTILINE)


def _add_to_server_name(content: str, section_marker: str, domain: str) -> str:
    """Agrega un dominio al server_name del bloque indicado."""
    if domain in content:
        return content  # Ya presente

    # Buscar server_name dentro de la sección
    # Buscamos el server_name más cercano después del marker
    idx = content.find(section_marker)
    if idx == -1:
        return content

    section = content[idx:]
    sn_match = re.search(r"(server_name\s*\n?\s*)((?:\S+\s*)+)(;)", section)
    if not sn_match:
        # server_name en una sola línea
        sn_match = re.search(r"(server_name\s+)((?:\S+\s*)+)(;)", section)
        if not sn_match:
            return content

    current_names = sn_match.group(2).strip()
    new_names = current_names + f"\n        {domain}"
    new_section = section[: sn_match.start()] + sn_match.group(1) + new_names + sn_match.group(3) + section[sn_match.end() :]

    return content[:idx] + new_section


def _remove_from_server_name(content: str, domain: str) -> str:
    """Elimina un dominio del server_name."""
    # Eliminar la línea o el dominio inline
    content = re.sub(rf"\s+{re.escape(domain)}\b", "", content)
    return content


def _add_to_route_map(filepath: str, domain: str, backend: str) -> None:
    """Agrega una línea 'domain backend;' a un archivo .map"""
    content = _read_file_local(filepath)
    entry = f"{domain} {backend};"
    if domain in content:
        return  # Ya existe
    content = content.rstrip("\n") + f"\n{entry}\n"
    _write_file_local(filepath, content)


def _remove_from_route_map(filepath: str, domain: str) -> None:
    """Elimina una línea con el domain de un archivo .map"""
    content = _read_file_local(filepath)
    content = re.sub(rf"^{re.escape(domain)}\s+[^;]+;\s*\n?", "", content, flags=re.MULTILINE)
    _write_file_local(filepath, content)


def _add_proxy_redirect_ct105(content: str, tenant_subdomain: str) -> str:
    """
    Agrega proxy_redirect para un tenant si no existe.
    Se inserta a nivel server block junto a los existentes.
    """
    redirect_marker = f"proxy_redirect https://{tenant_subdomain}.sajet.us/"
    if redirect_marker in content:
        return content  # Ya existe para este tenant

    # Buscar la sección de proxy_redirect existente
    existing = re.search(r"(    proxy_redirect https?://\S+ https?://\S+;\n)+", content)
    if existing:
        # Insertar después del bloque existente
        insert_pos = existing.end()
        new_lines = (
            f"    proxy_redirect https://{tenant_subdomain}.sajet.us/ https://$host/;\n"
            f"    proxy_redirect http://{tenant_subdomain}.sajet.us/ https://$host/;\n"
        )
        content = content[:insert_pos] + new_lines + content[insert_pos:]
    return content


def _remove_proxy_redirect_ct105(content: str, tenant_subdomain: str) -> str:
    """Elimina proxy_redirect para un tenant."""
    content = re.sub(
        rf"\s*proxy_redirect https?://{re.escape(tenant_subdomain)}\.sajet\.us/\s+https?://\$host/;\n?",
        "",
        content,
    )
    return content


# ── Clase principal ───────────────────────────────────────────────────────────

class NginxDomainConfigurator:
    """
    Configura nginx en PCT160 (local) y CT105 (SSH) para enrutar dominios
    externos a tenants Odoo.
    """

    def configure_domain(
        self,
        external_domain: str,
        tenant_db: str,
        tenant_subdomain: str,
        node_ip: str = CT105_IP,
    ) -> Dict[str, Any]:
        """
        Agrega un dominio externo a la configuración nginx de ambos servidores.

        Args:
            external_domain: dominio del cliente (ej: impulse-max.com)
            tenant_db: nombre de la BD en Odoo (ej: techeels)
            tenant_subdomain: subdominio de sajet.us (ej: techeels)
            node_ip: IP del nodo Odoo (default 10.10.10.100)
        """
        logger.info(f"Configurando nginx para {external_domain} → {tenant_db}")
        backups: Dict[str, str] = {}

        try:
            # ── 1. PCT160: editar /etc/nginx/sites-available/erp ──────────
            erp_content = _read_file_local(PCT160_ERP_CONF)
            backups["pct160_erp"] = erp_content

            tenant_sajet = f"{tenant_subdomain}.sajet.us"
            backend = f"{node_ip}:{CT105_NGINX_PORT}"

            # Map $external_tenant_db
            erp_content = _add_to_map(erp_content, "external_tenant_db", external_domain, tenant_db)
            # Map $external_odoo_host
            erp_content = _add_to_map(erp_content, "external_odoo_host", external_domain, tenant_sajet)
            # Map $proxy_odoo_host
            erp_content = _add_to_map(erp_content, "proxy_odoo_host", external_domain, tenant_sajet)
            # server_name en bloque DOMINIOS EXTERNOS
            erp_content = _add_to_server_name(erp_content, "DOMINIOS EXTERNOS", external_domain)

            _write_file_local(PCT160_ERP_CONF, erp_content)

            # ── 2. PCT160: route maps ─────────────────────────────────────
            backups["pct160_http_map"] = _read_file_local(PCT160_HTTP_MAP)
            backups["pct160_chat_map"] = _read_file_local(PCT160_CHAT_MAP)
            _add_to_route_map(PCT160_HTTP_MAP, external_domain, backend)
            _add_to_route_map(PCT160_CHAT_MAP, external_domain, backend)

            # ── 3. PCT160: validar y recargar ─────────────────────────────
            rc, _, err = _run_local("nginx -t")
            if rc != 0:
                raise RuntimeError(f"nginx -t PCT160 falló: {err}")

            _run_local("systemctl reload nginx")
            logger.info("PCT160 nginx recargado ✅")

            # ── 4. CT105: editar /etc/nginx/sites-enabled/odoo ────────────
            ct105_content = _read_file_ct105(CT105_ODOO_CONF)
            backups["ct105_odoo"] = ct105_content

            # Map $tenant_db
            ct105_content = _add_to_map(ct105_content, "tenant_db", external_domain, tenant_db)
            # Map $web_redirect_target (usa key "domain:")
            web_map_key = f"{external_domain}:"
            web_map_val = f"/web?db={tenant_db}"
            ct105_content = _add_to_map(ct105_content, "web_redirect_target", web_map_key, web_map_val)
            # Map $odoo_proxy_host
            ct105_content = _add_to_map(ct105_content, "odoo_proxy_host", external_domain, tenant_sajet)
            # server_name
            ct105_content = _add_to_server_name(ct105_content, "listen 8080", external_domain)
            # proxy_redirect
            ct105_content = _add_proxy_redirect_ct105(ct105_content, tenant_subdomain)

            _write_file_ct105(CT105_ODOO_CONF, ct105_content)

            # ── 5. CT105: validar y recargar ──────────────────────────────
            rc, _, err = _run_ct105("nginx -t")
            if rc != 0:
                raise RuntimeError(f"nginx -t CT105 falló: {err}")

            _run_ct105("systemctl reload nginx")
            logger.info("CT105 nginx recargado ✅")

            return {
                "success": True,
                "message": f"Nginx configurado para {external_domain} → {tenant_db}",
                "pct160": "ok",
                "ct105": "ok",
            }

        except Exception as e:
            logger.error(f"Error configurando nginx: {e}")
            self._rollback(backups)
            return {"success": False, "error": str(e)}

    def remove_domain(
        self,
        external_domain: str,
        tenant_subdomain: str,
    ) -> Dict[str, Any]:
        """
        Elimina un dominio externo de la configuración nginx de ambos servidores.
        """
        logger.info(f"Eliminando nginx config para {external_domain}")
        backups: Dict[str, str] = {}

        try:
            # ── PCT160 ───────────────────────────────────────────────────
            erp_content = _read_file_local(PCT160_ERP_CONF)
            backups["pct160_erp"] = erp_content

            for map_var in ("external_tenant_db", "external_odoo_host", "proxy_odoo_host"):
                erp_content = _remove_from_map(erp_content, map_var, external_domain)
            erp_content = _remove_from_server_name(erp_content, external_domain)
            _write_file_local(PCT160_ERP_CONF, erp_content)

            backups["pct160_http_map"] = _read_file_local(PCT160_HTTP_MAP)
            backups["pct160_chat_map"] = _read_file_local(PCT160_CHAT_MAP)
            _remove_from_route_map(PCT160_HTTP_MAP, external_domain)
            _remove_from_route_map(PCT160_CHAT_MAP, external_domain)

            rc, _, err = _run_local("nginx -t")
            if rc != 0:
                raise RuntimeError(f"nginx -t PCT160 falló: {err}")
            _run_local("systemctl reload nginx")
            logger.info("PCT160: dominio eliminado y nginx recargado ✅")

            # ── CT105 ────────────────────────────────────────────────────
            ct105_content = _read_file_ct105(CT105_ODOO_CONF)
            backups["ct105_odoo"] = ct105_content

            for map_var in ("tenant_db", "odoo_proxy_host"):
                ct105_content = _remove_from_map(ct105_content, map_var, external_domain)
            # web_redirect_target usa key "domain:"
            ct105_content = _remove_from_map(ct105_content, "web_redirect_target", f"{external_domain}:")
            ct105_content = _remove_from_server_name(ct105_content, external_domain)

            # Solo eliminar proxy_redirect si no quedan otros dominios de este tenant
            # (verificar si aún hay alguna referencia al tenant_subdomain en los maps)
            if f"{tenant_subdomain}.sajet.us" not in ct105_content.split("proxy_redirect")[0]:
                ct105_content = _remove_proxy_redirect_ct105(ct105_content, tenant_subdomain)

            _write_file_ct105(CT105_ODOO_CONF, ct105_content)

            rc, _, err = _run_ct105("nginx -t")
            if rc != 0:
                raise RuntimeError(f"nginx -t CT105 falló: {err}")
            _run_ct105("systemctl reload nginx")
            logger.info("CT105: dominio eliminado y nginx recargado ✅")

            return {
                "success": True,
                "message": f"Nginx: {external_domain} eliminado",
                "pct160": "ok",
                "ct105": "ok",
            }

        except Exception as e:
            logger.error(f"Error eliminando nginx config: {e}")
            self._rollback(backups)
            return {"success": False, "error": str(e)}

    def check_domain_configured(self, external_domain: str) -> Dict[str, bool]:
        """Verifica si un dominio ya está configurado en ambos servidores."""
        pct160 = False
        ct105 = False

        try:
            erp = _read_file_local(PCT160_ERP_CONF)
            pct160 = external_domain in erp
        except Exception:
            pass

        try:
            odoo = _read_file_ct105(CT105_ODOO_CONF)
            ct105 = external_domain in odoo
        except Exception:
            pass

        return {"pct160": pct160, "ct105": ct105}

    def _rollback(self, backups: Dict[str, str]) -> None:
        """Restaura archivos originales si algo falló."""
        logger.warning("Ejecutando rollback de nginx...")

        if "pct160_erp" in backups:
            try:
                _write_file_local(PCT160_ERP_CONF, backups["pct160_erp"])
            except Exception as e:
                logger.error(f"Rollback PCT160 erp falló: {e}")

        if "pct160_http_map" in backups:
            try:
                _write_file_local(PCT160_HTTP_MAP, backups["pct160_http_map"])
            except Exception as e:
                logger.error(f"Rollback PCT160 http_map falló: {e}")

        if "pct160_chat_map" in backups:
            try:
                _write_file_local(PCT160_CHAT_MAP, backups["pct160_chat_map"])
            except Exception as e:
                logger.error(f"Rollback PCT160 chat_map falló: {e}")

        if "ct105_odoo" in backups:
            try:
                _write_file_ct105(CT105_ODOO_CONF, backups["ct105_odoo"])
            except Exception as e:
                logger.error(f"Rollback CT105 falló: {e}")

        # Intentar recargar nginx en ambos
        try:
            _run_local("nginx -t && systemctl reload nginx")
        except Exception:
            pass

        try:
            _run_ct105("nginx -t && systemctl reload nginx")
        except Exception:
            pass

        logger.warning("Rollback completado")
