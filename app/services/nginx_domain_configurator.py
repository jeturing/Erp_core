"""
Nginx Domain Configurator
Automatiza la configuración de nginx en PCT160 y CT105 cuando se activa/desactiva
un dominio externo para un tenant Odoo.

Archivos que modifica:
  PCT160 (local):
    /etc/nginx/sites-available/external-domains  → map $external_tenant_db + server_name
    /etc/nginx/conf.d/odoo_http_routes.map       → dominio → backend
    /etc/nginx/conf.d/odoo_chat_routes.map       → dominio → backend
  CT105 (via SSH):
    /etc/nginx/sites-enabled/odoo                → maps ($tenant_db, $odoo_proxy_host) + server_name + proxy_redirect

Estrategia de enrutamiento (multi-website + multi-tenant):
  - dbfilter = ^%d$ en Odoo: selecciona BD por primer segmento del Host
  - X-Forwarded-Host NO se envía (ProxyFix de Odoo no se activa)
  - Host = subdominio interno ({bd}.{alias}.sajet.us) → Odoo recibe esto
  - Odoo usa Host para dbfilter (%d = {bd}) y para website matching (domain)
  - Cada website en Odoo tiene domain = https://{bd}.{alias}.sajet.us
  - Dominios con mismo nombre que la BD usan alias derivado del TLD
    (ej: techeels.io → techeels.ti.sajet.us, NO techeels.sajet.us)
  - Para websites adicionales: {bd}.{alias}.sajet.us (ej: techeels.em.sajet.us)
  - nginx proxy_redirect reescribe URLs internas a dominio real del usuario

Flujo:
  1. Leer archivos actuales
  2. Insertar entradas en maps y server_name
  3. Validar con nginx -t
  4. Recargar nginx
  5. Si falla, rollback automático
"""

import os
import subprocess
import logging
import re
import shlex
from typing import Dict, Any, List, Optional, Tuple

from ..config import CT105_IP, CT105_NGINX_PORT

logger = logging.getLogger("nginx_configurator")

# ── Constantes ────────────────────────────────────────────────────────────────────
# CT105_SSH removido — ahora se construye dinámicamente en _run_node(node_ip=...)

PCT160_ERP_CONF = "/etc/nginx/sites-available/external-domains"
PCT160_HTTP_MAP = "/etc/nginx/conf.d/odoo_http_routes.map"
PCT160_CHAT_MAP = "/etc/nginx/conf.d/odoo_chat_routes.map"
CT105_ODOO_CONF = "/etc/nginx/sites-enabled/odoo"
NGINX_ADMIN_HELPER = os.getenv("NGINX_ADMIN_HELPER", "/usr/local/bin/sajet-nginx-admin")

_LOCAL_HELPER_COMMANDS = {
    "nginx -t": ["test-local"],
    "systemctl reload nginx": ["reload-local"],
    "nginx -t && systemctl reload nginx": ["test-and-reload-local"],
}

_REMOTE_HELPER_COMMANDS = {
    "nginx -t": "test-remote",
    "systemctl reload nginx": "reload-remote",
    "nginx -t && systemctl reload nginx": "test-and-reload-remote",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_local(cmd: str, timeout: int = 15) -> Tuple[int, str, str]:
    """Ejecuta comando local y devuelve (rc, stdout, stderr)."""
    normalized = " ".join(cmd.strip().split())
    if _should_use_admin_helper() and normalized in _LOCAL_HELPER_COMMANDS:
        return _run_admin_helper(_LOCAL_HELPER_COMMANDS[normalized], timeout=timeout)

    r = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _run_node(cmd: str, node_ip: str = CT105_IP, timeout: int = 15) -> Tuple[int, str, str]:
    """Ejecuta comando en un nodo Odoo via SSH.
    
    Args:
        cmd: Comando a ejecutar
        node_ip: IP del nodo destino (default: CT105_IP para backward compat)
        timeout: Timeout en segundos
    """
    normalized = " ".join(cmd.strip().split())
    if _should_use_admin_helper() and normalized in _REMOTE_HELPER_COMMANDS:
        return _run_admin_helper([_REMOTE_HELPER_COMMANDS[normalized], node_ip], timeout=timeout)

    safe = cmd.replace("'", "'\\''")
    ssh_target = f"root@{node_ip}"
    full = f"ssh -o BatchMode=yes -o ConnectTimeout=5 {ssh_target} '{safe}'"
    return _run_local(full, timeout=timeout)


# Alias para backward compatibility
def _run_ct105(cmd: str, timeout: int = 15) -> Tuple[int, str, str]:
    """Alias legacy → _run_node con CT105_IP."""
    return _run_node(cmd, node_ip=CT105_IP, timeout=timeout)


def _should_use_admin_helper() -> bool:
    """Usa helper privilegiado cuando el proceso no es root y el helper existe."""
    return (
        os.geteuid() != 0
        and os.path.exists(NGINX_ADMIN_HELPER)
    )


def _run_admin_helper(args: List[str], timeout: int = 15) -> Tuple[int, str, str]:
    """Ejecuta el helper privilegiado para operaciones de nginx/SSH."""
    result = subprocess.run(
        ["sudo", "-n", NGINX_ADMIN_HELPER, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _read_file_local(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except PermissionError:
        if not _should_use_admin_helper():
            raise
        rc, out, err = _run_admin_helper(["read-local", path], timeout=15)
        if rc != 0:
            raise RuntimeError(f"No se pudo leer {path} localmente: {err or out}")
        return out


def _write_file_local(path: str, content: str) -> None:
    try:
        with open(path, "w") as f:
            f.write(content)
        return
    except PermissionError:
        if not _should_use_admin_helper():
            raise

    import tempfile

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False)
    try:
        tmp.write(content)
        tmp.close()
        rc, out, err = _run_admin_helper(["write-local", path, tmp.name], timeout=20)
        if rc != 0:
            raise RuntimeError(f"No se pudo escribir {path} localmente: {err or out}")
    finally:
        try:
            os.unlink(tmp.name)
        except FileNotFoundError:
            pass


def _read_file_node(path: str, node_ip: str = CT105_IP) -> str:
    """Lee archivo de un nodo remoto via SSH."""
    if _should_use_admin_helper():
        rc, out, err = _run_admin_helper(["read-remote", node_ip, path], timeout=20)
    else:
        rc, out, err = _run_node(f"cat {shlex.quote(path)}", node_ip=node_ip)
    if rc != 0:
        raise RuntimeError(f"No se pudo leer {path} en {node_ip}: {err}")
    return out


def _write_file_node(path: str, content: str, node_ip: str = CT105_IP) -> None:
    """Escribe archivo en un nodo remoto via SSH + scp."""
    import tempfile

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False)
    tmp.write(content)
    tmp.close()
    try:
        if _should_use_admin_helper():
            rc, out, err = _run_admin_helper(["write-remote", node_ip, path, tmp.name], timeout=25)
        else:
            ssh_target = f"root@{node_ip}"
            rc, out, err = _run_local(
                f"scp -o BatchMode=yes -o ConnectTimeout=5 {tmp.name} {ssh_target}:{path}",
                timeout=20,
            )
        if rc != 0:
            raise RuntimeError(f"No se pudo escribir {path} en {node_ip}: {err or out}")
    finally:
        try:
            os.unlink(tmp.name)
        except FileNotFoundError:
            pass


# Aliases legacy para backward compatibility
def _read_file_ct105(path: str) -> str:
    return _read_file_node(path, node_ip=CT105_IP)


def _write_file_ct105(path: str, content: str) -> None:
    _write_file_node(path, content, node_ip=CT105_IP)


# ── Funciones de edición de nginx maps ────────────────────────────────────────

def _add_to_map(content: str, map_var: str, domain: str, value: str) -> str:
    """
    Agrega una entrada a un bloque 'map $host $map_var { ... }'.
    Inserta la línea justo antes del cierre '}' del map o antes de un comentario
    tipo '# --- Agregar más'.
    """
    # Encontrar el bloque map correcto
    pattern = rf"(map\s+\S+\s+\${re.escape(map_var)}\s*\{{)(.*?)(\}})"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        logger.warning(f"Map ${map_var} no encontrado")
        return content

    entry = f"    {domain} {value};\n"
    map_body = match.group(2)
    existing_pattern = rf"^(\s*){re.escape(domain)}\s+([^;]+);(\s*)$"
    existing_match = re.search(existing_pattern, map_body, re.MULTILINE)
    if existing_match:
        current_value = existing_match.group(2).strip()
        if current_value == value:
            return content  # Ya existe con el valor correcto en este map
        replacement = f"{existing_match.group(1)}{domain} {value};{existing_match.group(3)}"
        new_body = re.sub(existing_pattern, replacement, map_body, count=1, flags=re.MULTILINE)
        return content[: match.start()] + match.group(1) + new_body + match.group(3) + content[match.end() :]

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
    # Buscar server_name dentro de la sección
    # Buscamos el server_name más cercano después del marker
    idx = content.find(section_marker)
    if idx == -1:
        return content

    section = content[idx:]
    sn_match = re.search(r"(server_name\b)([^;]*)(;)", section, re.DOTALL)
    if not sn_match:
        return content

    if re.search(rf"\b{re.escape(domain)}\b", sn_match.group(2)):
        return content  # Ya presente en este server_name

    current_names = sn_match.group(2).rstrip()
    separator = "\n" if current_names else " "
    new_names = f"{current_names}{separator}        {domain}"
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
    updated = _add_to_route_map_content(content, domain, backend)
    if updated != content:
        _write_file_local(filepath, updated)


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

    @staticmethod
    def generate_internal_subdomain(
        tenant_db: str,
        external_domain: str,
        alias: Optional[str] = None,
    ) -> str:
        """
        Genera el subdominio interno .sajet.us para un dominio externo.
        Patrón: {bd}.{alias}.sajet.us donde %d (primer segmento) = {bd}

        Si alias es None, genera uno automático basado en el dominio externo:
          - impulse-max.com → "im" (iniciales de palabras)
          - evolucionamujer.com → "em" (iniciales)
          - techeels.io → "ti" (t de techeels + i de io, evita colisión con nativo)

        Returns:
            Subdominio interno (ej: "techeels.em.sajet.us")
        """
        if alias:
            return f"{tenant_db}.{alias}.sajet.us"

        # Generar alias automático a partir del dominio externo
        domain_base = external_domain.lower().split(".")[0]
        domain_parts = external_domain.lower().rsplit(".", 1)
        tld = domain_parts[-1] if len(domain_parts) > 1 else ""

        # Si el primer segmento del dominio externo == nombre de BD,
        # DEBE generar alias con TLD para evitar colisión con el subdominio nativo
        # Ej: techeels.io → techeels.ti.sajet.us (t de techeels + i de io)
        #     techeels.com → techeels.tc.sajet.us
        if domain_base == tenant_db:
            alias = f"{domain_base[0]}{tld[0]}" if tld else "ext"
            return f"{tenant_db}.{alias}.sajet.us"

        # Tomar iniciales de partes separadas por - o camelCase
        parts = domain_base.replace("-", " ").split()
        if len(parts) > 1:
            alias = "".join(p[0] for p in parts)  # impulse-max → im
        else:
            # Para nombres sin separador, tomar primeras 2-3 letras
            alias = domain_base[:3] if len(domain_base) > 3 else domain_base

        return f"{tenant_db}.{alias}.sajet.us"

    def configure_domain(
        self,
        external_domain: str,
        tenant_db: str,
        tenant_subdomain: str,
        node_ip: str = CT105_IP,
        website_alias: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Agrega un dominio externo a la configuración nginx de ambos servidores.

        Estrategia:
          - PCT160: pasa Host original al CT105 (donde se mapea internamente)
          - CT105: mapea dominio externo → subdominio interno ({bd}.{alias}.sajet.us)
          - Odoo recibe Host = subdominio interno, dbfilter %d selecciona BD
          - Website module matchea por domain = https://{subdominio_interno}
          - X-Forwarded-Host NO se envía (ProxyFix no se activa)
          - proxy_redirect reescribe URLs internas a dominio real del usuario

        Args:
            external_domain: dominio del cliente (ej: impulse-max.com)
            tenant_db: nombre de la BD en Odoo (ej: techeels)
            tenant_subdomain: subdominio de sajet.us (ej: techeels)
            node_ip: IP del nodo Odoo (from env ODOO_PRIMARY_IP)
            website_alias: alias corto opcional para el subdominio interno
        """
        # Generar el subdominio interno para este dominio externo
        internal_subdomain = self.generate_internal_subdomain(
            tenant_db, external_domain, website_alias
        )

        logger.info(
            f"Configurando nginx: {external_domain} → "
            f"{internal_subdomain} (BD: {tenant_db})"
        )
        backups: Dict[str, str] = {}
        www_domain = f"www.{external_domain}"

        try:
            # ── 1. PCT160: editar /etc/nginx/sites-available/external-domains
            erp_content = _read_file_local(PCT160_ERP_CONF)
            backups["pct160_erp"] = erp_content

            backend = f"{node_ip}:{CT105_NGINX_PORT}"

            # Map $external_tenant_db → dominio → BD (para validación)
            erp_content = _add_to_map(erp_content, "external_tenant_db", external_domain, tenant_db)
            erp_content = _add_to_map(erp_content, "external_tenant_db", www_domain, tenant_db)
            # server_name en bloque server
            erp_content = _add_to_server_name(erp_content, "listen 443", external_domain)
            erp_content = _add_to_server_name(erp_content, "listen 443", www_domain)

            _write_file_local(PCT160_ERP_CONF, erp_content)

            # ── 2. PCT160: route maps ─────────────────────────────────────
            backups["pct160_http_map"] = _read_file_local(PCT160_HTTP_MAP)
            backups["pct160_chat_map"] = _read_file_local(PCT160_CHAT_MAP)
            _add_to_route_map(PCT160_HTTP_MAP, external_domain, backend)
            _add_to_route_map(PCT160_CHAT_MAP, external_domain, backend)
            _add_to_route_map(PCT160_HTTP_MAP, www_domain, backend)
            _add_to_route_map(PCT160_CHAT_MAP, www_domain, backend)

            # ── 3. PCT160: validar y recargar ─────────────────────────────
            rc, _, err = _run_local("nginx -t")
            if rc != 0:
                raise RuntimeError(f"nginx -t PCT160 falló: {err}")

            _run_local("systemctl reload nginx")
            logger.info("PCT160 nginx recargado ✅")

            # ── 4. Nodo Odoo: editar /etc/nginx/sites-enabled/odoo ────────────
            node_content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
            backups["node_odoo"] = node_content

            # Map $tenant_db → dominio → BD
            node_content = _add_to_map(node_content, "tenant_db", external_domain, tenant_db)
            node_content = _add_to_map(node_content, "tenant_db", www_domain, tenant_db)
            # Map $odoo_proxy_host → subdominio INTERNO (para dbfilter + website match)
            node_content = _add_to_map(node_content, "odoo_proxy_host", external_domain, internal_subdomain)
            node_content = _add_to_map(node_content, "odoo_proxy_host", www_domain, internal_subdomain)
            # server_name en ambos bloques (8080 y 8443)
            node_content = _add_to_server_name(node_content, "listen 8080", external_domain)
            node_content = _add_to_server_name(node_content, "listen 8080", www_domain)
            node_content = _add_to_server_name(node_content, "listen 8443", external_domain)
            node_content = _add_to_server_name(node_content, "listen 8443", www_domain)
            # proxy_redirect: reescribir URLs internas a dominio real
            node_content = _add_proxy_redirect_ct105(node_content, internal_subdomain.replace(".sajet.us", ""))

            _write_file_node(CT105_ODOO_CONF, node_content, node_ip=node_ip)

            # ── 5. Nodo Odoo: validar y recargar ──────────────────────────
            rc, _, err = _run_node("nginx -t", node_ip=node_ip)
            if rc != 0:
                raise RuntimeError(f"nginx -t nodo {node_ip} falló: {err}")

            _run_node("systemctl reload nginx", node_ip=node_ip)
            logger.info(f"Nodo {node_ip} nginx recargado ✅")

            return {
                "success": True,
                "message": f"Nginx configurado: {external_domain} → {internal_subdomain}",
                "internal_subdomain": internal_subdomain,
                "pct160": "ok",
                "node": node_ip,
            }

        except Exception as e:
            logger.error(f"Error configurando nginx: {e}")
            self._rollback(backups)
            return {"success": False, "error": str(e)}

    def remove_domain(
        self,
        external_domain: str,
        tenant_subdomain: str,
        node_ip: str = CT105_IP,
    ) -> Dict[str, Any]:
        """
        Elimina un dominio externo de la configuración nginx de ambos servidores.
        
        Args:
            node_ip: IP del nodo Odoo (default: CT105_IP)
        """
        logger.info(f"Eliminando nginx config para {external_domain}")
        backups: Dict[str, str] = {}
        www_domain = f"www.{external_domain}"

        try:
            # ── PCT160 ───────────────────────────────────────────────────
            erp_content = _read_file_local(PCT160_ERP_CONF)
            backups["pct160_erp"] = erp_content

            erp_content = _remove_from_map(erp_content, "external_tenant_db", external_domain)
            erp_content = _remove_from_map(erp_content, "external_tenant_db", www_domain)
            erp_content = _remove_from_server_name(erp_content, external_domain)
            erp_content = _remove_from_server_name(erp_content, www_domain)
            _write_file_local(PCT160_ERP_CONF, erp_content)

            backups["pct160_http_map"] = _read_file_local(PCT160_HTTP_MAP)
            backups["pct160_chat_map"] = _read_file_local(PCT160_CHAT_MAP)
            _remove_from_route_map(PCT160_HTTP_MAP, external_domain)
            _remove_from_route_map(PCT160_CHAT_MAP, external_domain)
            _remove_from_route_map(PCT160_HTTP_MAP, www_domain)
            _remove_from_route_map(PCT160_CHAT_MAP, www_domain)

            rc, _, err = _run_local("nginx -t")
            if rc != 0:
                raise RuntimeError(f"nginx -t PCT160 falló: {err}")
            _run_local("systemctl reload nginx")
            logger.info("PCT160: dominio eliminado y nginx recargado ✅")

            # ── Nodo Odoo ────────────────────────────────────────────────
            node_content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
            backups["node_odoo"] = node_content

            # Leer el subdominio interno actual del map antes de eliminar
            internal_sub_match = re.search(
                rf"^\s+{re.escape(external_domain)}\s+(\S+);",
                node_content, re.MULTILINE
            )
            internal_subdomain = None
            if internal_sub_match:
                internal_subdomain = internal_sub_match.group(1)

            for map_var in ("tenant_db", "odoo_proxy_host"):
                node_content = _remove_from_map(node_content, map_var, external_domain)
                node_content = _remove_from_map(node_content, map_var, www_domain)
            node_content = _remove_from_server_name(node_content, external_domain)
            node_content = _remove_from_server_name(node_content, www_domain)

            # Eliminar proxy_redirect del subdominio interno si lo encontramos
            if internal_subdomain:
                sub_prefix = internal_subdomain.replace(".sajet.us", "")
                node_content = _remove_proxy_redirect_ct105(node_content, sub_prefix)

            _write_file_node(CT105_ODOO_CONF, node_content, node_ip=node_ip)

            rc, _, err = _run_node("nginx -t", node_ip=node_ip)
            if rc != 0:
                raise RuntimeError(f"nginx -t nodo {node_ip} falló: {err}")
            _run_node("systemctl reload nginx", node_ip=node_ip)
            logger.info(f"Nodo {node_ip}: dominio eliminado y nginx recargado ✅")

            return {
                "success": True,
                "message": f"Nginx: {external_domain} eliminado",
                "pct160": "ok",
                "node": node_ip,
            }

        except Exception as e:
            logger.error(f"Error eliminando nginx config: {e}")
            self._rollback(backups)
            return {"success": False, "error": str(e)}

    def check_domain_configured(self, external_domain: str, node_ip: str = CT105_IP) -> Dict[str, bool]:
        """Verifica si un dominio ya está configurado en ambos servidores."""
        pct160 = False
        node = False

        try:
            erp = _read_file_local(PCT160_ERP_CONF)
            pct160 = external_domain in erp
        except Exception:
            pass

        try:
            odoo = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
            node = external_domain in odoo
        except Exception:
            pass

        return {"pct160": pct160, "node": node}

    def _rollback(self, backups: Dict[str, str], node_ip: str = CT105_IP) -> None:
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

        if "node_odoo" in backups:
            try:
                _write_file_node(CT105_ODOO_CONF, backups["node_odoo"], node_ip=node_ip)
            except Exception as e:
                logger.error(f"Rollback nodo {node_ip} falló: {e}")

        # Intentar recargar nginx en ambos
        try:
            _run_local("nginx -t && systemctl reload nginx")
        except Exception:
            pass

        try:
            _run_node("nginx -t && systemctl reload nginx", node_ip=node_ip)
        except Exception:
            pass

        logger.warning("Rollback completado")


# ── Subdominio .sajet.us automático (para nuevos tenants) ─────────────────────

def provision_sajet_subdomain(
    subdomain: str,
    node_ip: str = CT105_IP,
    http_port: int = CT105_NGINX_PORT,
    chat_port: int = 8072,
) -> Dict[str, Any]:
    """
    Registra un nuevo subdominio.sajet.us en los nginx maps de LXC 160 y el nodo Odoo.
    Solo para el subdominio propio del tenant (no dominios externos).

    Args:
        subdomain: nombre del tenant (ej: "acme")
        node_ip: IP del nodo Odoo destino (default: CT105_IP)
        http_port: puerto HTTP del nginx/odoo en el nodo (default: 8080)
        chat_port: puerto chat/longpolling en el nodo (default: 8072)

    Modifica:
      - PCT160 /etc/nginx/conf.d/odoo_http_routes.map  → subdomain.sajet.us → node_ip:http_port
      - PCT160 /etc/nginx/conf.d/odoo_chat_routes.map  → subdomain.sajet.us → node_ip:chat_port
      - Nodo Odoo /etc/nginx/sites-enabled/odoo → map $tenant_db + $odoo_proxy_host

    Returns:
        {"success": True/False, "steps": [...], "error": str}
    """
    steps = []
    backend_http = f"{node_ip}:{http_port}"
    backend_chat = f"{node_ip}:{chat_port}"
    full_domain = f"{subdomain}.sajet.us"
    www_domain = f"www.{full_domain}"

    try:
        # ── PCT160: agregar a route maps ──────────────────────────────────
        for map_path, backend in [(PCT160_HTTP_MAP, backend_http), (PCT160_CHAT_MAP, backend_chat)]:
            _add_to_route_map(map_path, full_domain, backend)
            _add_to_route_map(map_path, www_domain, backend)

        rc, _, err = _run_local("nginx -t")
        if rc != 0:
            raise RuntimeError(f"nginx -t PCT160 falló: {err}")
        _run_local("systemctl reload nginx")
        steps.append({"step": "pct160_maps", "status": "ok"})

        # ── Nodo Odoo: agregar a maps tenant_db y odoo_proxy_host ─────────────
        node_content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)

        # Map $tenant_db: subdomain.sajet.us → subdomain
        node_content = _add_to_map(node_content, "tenant_db", full_domain, subdomain)
        # Map $odoo_proxy_host: subdomain.sajet.us → subdomain.sajet.us (pasa tal cual)
        node_content = _add_to_map(node_content, "odoo_proxy_host", full_domain, f"{subdomain}.sajet.us")
        # Agregar a server_name
        node_content = _add_to_server_name(node_content, "listen 8080", full_domain)

        _write_file_node(CT105_ODOO_CONF, node_content, node_ip=node_ip)

        rc105, _, err105 = _run_node("nginx -t && systemctl reload nginx", node_ip=node_ip)
        if rc105 != 0:
            logger.warning(f"nginx reload nodo {node_ip} warning (no fatal): {err105}")
        steps.append({"step": "node_maps", "status": "ok", "node_ip": node_ip})

        logger.info(f"✅ Subdominio {full_domain} registrado en nginx")
        return {"success": True, "subdomain": full_domain, "steps": steps}

    except Exception as e:
        logger.error(f"Error provisionando subdominio {full_domain}: {e}")
        return {"success": False, "subdomain": full_domain, "error": str(e), "steps": steps}


def remove_sajet_subdomain(subdomain: str, node_ip: str = CT105_IP) -> Dict[str, Any]:
    """
    Elimina un subdominio.sajet.us de los nginx maps (al borrar un tenant).
    
    Args:
        node_ip: IP del nodo Odoo (default: CT105_IP)
    """
    steps = []
    full_domain = f"{subdomain}.sajet.us"
    www_domain = f"www.{full_domain}"

    try:
        for map_path in [PCT160_HTTP_MAP, PCT160_CHAT_MAP]:
            content = _read_file_local(map_path)
            content = _remove_from_route_map_content(content, full_domain)
            content = _remove_from_route_map_content(content, www_domain)
            _write_file_local(map_path, content)

        _run_local("nginx -t && systemctl reload nginx")
        steps.append({"step": "pct160_maps", "status": "ok"})

        node_content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
        node_content = _remove_from_map(node_content, "tenant_db", full_domain)
        node_content = _remove_from_map(node_content, "odoo_proxy_host", full_domain)
        node_content = _remove_from_server_name(node_content, "listen 8080", full_domain)
        _write_file_node(CT105_ODOO_CONF, node_content, node_ip=node_ip)
        _run_node("nginx -t && systemctl reload nginx", node_ip=node_ip)
        steps.append({"step": "node_maps", "status": "ok", "node_ip": node_ip})

        logger.info(f"✅ Subdominio {full_domain} eliminado de nginx")
        return {"success": True, "subdomain": full_domain, "steps": steps}

    except Exception as e:
        logger.error(f"Error eliminando subdominio {full_domain}: {e}")
        return {"success": False, "error": str(e), "steps": steps}


def _add_to_route_map_content(content: str, domain: str, backend: str) -> str:
    """Agrega o corrige dominio→backend en un archivo de route map."""
    existing_pattern = rf"^(\s*){re.escape(domain)}\s+([^;]+);(\s*)$"
    existing_match = re.search(existing_pattern, content, re.MULTILINE)
    if existing_match:
        current_backend = existing_match.group(2).strip()
        if current_backend == backend:
            return content
        replacement = f"{existing_match.group(1)}{domain} {backend};{existing_match.group(3)}"
        return re.sub(existing_pattern, replacement, content, count=1, flags=re.MULTILINE)

    new_line = f"{domain} {backend};\n"
    # Insertar antes del cierre del último bloque }
    if "}" in content:
        last_brace = content.rfind("}")
        return content[:last_brace] + new_line + content[last_brace:]
    return content.rstrip("\n") + f"\n{new_line}"


def _remove_from_route_map_content(content: str, domain: str) -> str:
    """Elimina una entrada de dominio de un route map."""
    return re.sub(rf"^\s*{re.escape(domain)}\s+[^\n]+\n?", "", content, flags=re.MULTILINE)


def _remove_from_map(content: str, map_var: str, domain: str) -> str:
    """Elimina entrada de un bloque map."""
    return re.sub(rf"^\s*{re.escape(domain)}\s+[^\n]+\n?", "", content, flags=re.MULTILINE)


def _remove_from_server_name(content: str, listen_hint: str, domain: str) -> str:
    """Elimina un dominio de la directiva server_name."""
    def replacer(m):
        line = m.group(0)
        return re.sub(rf"\s+{re.escape(domain)}", "", line)
    block_pattern = rf"(listen {re.escape(listen_hint.replace('listen ', ''))}[^;]*;.*?server_name[^\n]*\n)"
    return re.sub(r"(server_name[^\n]*\n)", replacer, content)
