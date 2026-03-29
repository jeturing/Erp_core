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
import shutil
from typing import Dict, Any, List, Optional, Tuple

from ..config import (
    CT105_IP,
    CT105_NGINX_PORT,
    PROXMOX_SSH_HOST,
    PROXMOX_SSH_KEY,
    PROXMOX_SSH_USER,
)

logger = logging.getLogger("nginx_configurator")
SSH_BIN = shutil.which("ssh") or "/usr/bin/ssh"
SUDO_BIN = shutil.which("sudo") or "/usr/bin/sudo"

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
    """Ejecuta comando en un nodo Odoo via SSH al host Proxmox + pct exec.

    SAJET corre dentro de CT160 y no tiene binario `pct`; por eso el salto
    correcto es SSH al host Proxmox y desde ahí `pct exec <PCT_ID>`.
    El mapeo IP → PCT se resuelve dinámicamente desde proxmox_nodes.

    Args:
        cmd: Comando a ejecutar
        node_ip: IP del nodo destino (default: CT105_IP para backward compat)
        timeout: Timeout en segundos
    """
    normalized = " ".join(cmd.strip().split())
    if _should_use_admin_helper() and normalized in _REMOTE_HELPER_COMMANDS:
        return _run_admin_helper([_REMOTE_HELPER_COMMANDS[normalized], node_ip], timeout=timeout)

    from .pct_resolver import resolve_pct_id
    pct_id = resolve_pct_id(node_ip)
    if pct_id is None:
        return 1, "", f"No PCT mapping for IP {node_ip} — check proxmox_nodes.vmid"

    remote_cmd = f"pct exec {pct_id} -- bash -lc {shlex.quote(cmd)}"
    ssh_cmd = [
        SSH_BIN,
        "-i",
        PROXMOX_SSH_KEY,
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "ConnectTimeout=10",
        f"{PROXMOX_SSH_USER}@{PROXMOX_SSH_HOST}",
        remote_cmd,
    ]
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", f"SSH->pct exec timeout after {timeout}s"
    except Exception as exc:
        return 1, "", str(exc)


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
        [SUDO_BIN, "-n", NGINX_ADMIN_HELPER, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _external_domain_aliases(external_domain: str) -> List[str]:
    """Expande un dominio externo a sus variantes raiz/www sin duplicar prefijos."""
    host = (external_domain or "").strip().lower().strip(".")
    if not host:
        return []

    candidates = [host]
    if host.startswith("www.") and "." in host[4:]:
        candidates.append(host[4:])
    else:
        candidates.append(f"www.{host}")

    aliases: List[str] = []
    for candidate in candidates:
        if candidate and candidate not in aliases:
            aliases.append(candidate)
    return aliases


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
    """Escribe archivo en un nodo remoto via SSH -> pct exec + base64."""
    import base64

    if _should_use_admin_helper():
        import tempfile
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False)
        tmp.write(content)
        tmp.close()
        try:
            rc, out, err = _run_admin_helper(["write-remote", node_ip, path, tmp.name], timeout=25)
            if rc != 0:
                raise RuntimeError(f"No se pudo escribir {path} en {node_ip}: {err or out}")
        finally:
            try:
                os.unlink(tmp.name)
            except FileNotFoundError:
                pass
        return

    b64 = base64.b64encode(content.encode()).decode()
    rc, out, err = _run_node(
        f"echo '{b64}' | base64 -d > {shlex.quote(path)}",
        node_ip=node_ip,
        timeout=20,
    )
    if rc != 0:
        raise RuntimeError(f"No se pudo escribir {path} en {node_ip}: {err or out}")


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
        domain_hosts = _external_domain_aliases(external_domain)

        try:
            # ── 1. PCT160: editar /etc/nginx/sites-available/external-domains
            erp_content = _read_file_local(PCT160_ERP_CONF)
            backups["pct160_erp"] = erp_content

            backend = f"{node_ip}:{CT105_NGINX_PORT}"

            # Map $external_tenant_db → dominio → BD (para validación)
            for domain_host in domain_hosts:
                erp_content = _add_to_map(erp_content, "external_tenant_db", domain_host, tenant_db)
                erp_content = _add_to_server_name(erp_content, "listen 443", domain_host)

            _write_file_local(PCT160_ERP_CONF, erp_content)

            # ── 2. PCT160: route maps ─────────────────────────────────────
            backups["pct160_http_map"] = _read_file_local(PCT160_HTTP_MAP)
            backups["pct160_chat_map"] = _read_file_local(PCT160_CHAT_MAP)
            for domain_host in domain_hosts:
                _add_to_route_map(PCT160_HTTP_MAP, domain_host, backend)
                _add_to_route_map(PCT160_CHAT_MAP, domain_host, backend)

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
            for domain_host in domain_hosts:
                node_content = _add_to_map(node_content, "tenant_db", domain_host, tenant_db)
                # Map $odoo_proxy_host → subdominio INTERNO (para dbfilter + website match)
                node_content = _add_to_map(node_content, "odoo_proxy_host", domain_host, internal_subdomain)
                # server_name en ambos bloques (8080 y 8443)
                node_content = _add_to_server_name(node_content, "listen 8080", domain_host)
                node_content = _add_to_server_name(node_content, "listen 8443", domain_host)
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
        domain_hosts = _external_domain_aliases(external_domain)

        try:
            # ── PCT160 ───────────────────────────────────────────────────
            erp_content = _read_file_local(PCT160_ERP_CONF)
            backups["pct160_erp"] = erp_content

            for domain_host in domain_hosts:
                erp_content = _remove_from_map(erp_content, "external_tenant_db", domain_host)
                erp_content = _remove_from_server_name(erp_content, domain_host)
            _write_file_local(PCT160_ERP_CONF, erp_content)

            backups["pct160_http_map"] = _read_file_local(PCT160_HTTP_MAP)
            backups["pct160_chat_map"] = _read_file_local(PCT160_CHAT_MAP)
            for domain_host in domain_hosts:
                _remove_from_route_map(PCT160_HTTP_MAP, domain_host)
                _remove_from_route_map(PCT160_CHAT_MAP, domain_host)

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
                for domain_host in domain_hosts:
                    node_content = _remove_from_map(node_content, map_var, domain_host)
            for domain_host in domain_hosts:
                node_content = _remove_from_server_name(node_content, domain_host)

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
        node_content = _remove_from_server_name_with_hint(node_content, "listen 8080", full_domain)
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


def _remove_from_server_name_with_hint(content: str, listen_hint: str, domain: str) -> str:
    """Elimina un dominio de la directiva server_name."""
    def replacer(m):
        line = m.group(0)
        return re.sub(rf"\s+{re.escape(domain)}", "", line)
    block_pattern = rf"(listen {re.escape(listen_hint.replace('listen ', ''))}[^;]*;.*?server_name[^\n]*\n)"
    return re.sub(r"(server_name[^\n]*\n)", replacer, content)


# ══════════════════════════════════════════════════════════════════════════════
# Dedicated Service Routing (Fase 3)
# ══════════════════════════════════════════════════════════════════════════════

# Los maps $odoo_http_upstream y $odoo_chat_upstream permiten routing per-tenant
# a puertos dedicados sin cambiar la estructura del nginx.
# Default: http://127.0.0.1:8069 (shared pool) / http://127.0.0.1:8072 (chat)
# Dedicated: http://127.0.0.1:{port} per subdomain

DEDICATED_HTTP_MAP_VAR = "odoo_http_upstream"
DEDICATED_CHAT_MAP_VAR = "odoo_chat_upstream"
SHARED_HTTP_DEFAULT = "http://127.0.0.1:8069"
SHARED_CHAT_DEFAULT = "http://127.0.0.1:8072"


def ensure_dedicated_maps_exist(node_ip: str = CT105_IP) -> Dict[str, Any]:
    """
    Asegura que los maps $odoo_http_upstream y $odoo_chat_upstream existen en el
    nginx del nodo y que los proxy_pass usan estas variables.

    Este es un setup one-time que transforma el nginx de routing estático a dinámico.
    Es idempotente — si ya está configurado, no modifica nada.

    Returns:
        {"success": bool, "changed": bool, "message": str}
    """
    try:
        content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
        original = content
        changed = False

        # ── 1. Agregar map $odoo_http_upstream si no existe ──
        if f"${DEDICATED_HTTP_MAP_VAR}" not in content:
            http_map = f"""
# Upstream HTTP por tenant: dedicated=puerto propio, shared=8069
map $host ${DEDICATED_HTTP_MAP_VAR} {{
    default {SHARED_HTTP_DEFAULT};
}}

"""
            # Insertar justo antes de 'server {'
            server_idx = content.find("\nserver {")
            if server_idx == -1:
                server_idx = content.find("server {")
            if server_idx != -1:
                content = content[:server_idx] + http_map + content[server_idx:]
                changed = True

        # ── 2. Agregar map $odoo_chat_upstream si no existe ──
        if f"${DEDICATED_CHAT_MAP_VAR}" not in content:
            chat_map = f"""
# Upstream Chat/LongPolling por tenant: dedicated=puerto propio, shared=8072
map $host ${DEDICATED_CHAT_MAP_VAR} {{
    default {SHARED_CHAT_DEFAULT};
}}

"""
            server_idx = content.find("\nserver {")
            if server_idx == -1:
                server_idx = content.find("server {")
            if server_idx != -1:
                content = content[:server_idx] + chat_map + content[server_idx:]
                changed = True

        # ── 3. Reemplazar proxy_pass estáticos por variables ──
        # SOLO para las locations que apuntan a odoo/odoo-chat (no erp_core)
        replacements = [
            # proxy_pass http://odoo → proxy_pass $odoo_http_upstream
            # Pero NO tocar lines que ya usan la variable o van a erp_core
            (r"proxy_pass http://odoo;", f"proxy_pass ${DEDICATED_HTTP_MAP_VAR};"),
            (r"proxy_pass http://odoo-chat;", f"proxy_pass ${DEDICATED_CHAT_MAP_VAR};"),
        ]

        for old_pattern, new_value in replacements:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_value, content)
                changed = True

        if not changed:
            return {"success": True, "changed": False, "message": "Nginx ya configurado para routing dedicado"}

        # ── 4. Escribir, validar, recargar ──
        backup = original
        _write_file_node(CT105_ODOO_CONF, content, node_ip=node_ip)

        rc, _, err = _run_node("nginx -t", node_ip=node_ip)
        if rc != 0:
            # Rollback
            _write_file_node(CT105_ODOO_CONF, backup, node_ip=node_ip)
            return {"success": False, "changed": False, "message": f"nginx -t falló, rollback: {err}"}

        _run_node("systemctl reload nginx", node_ip=node_ip)
        logger.info(f"✅ Nginx en {node_ip} actualizado para soporte dedicated routing")
        return {"success": True, "changed": True, "message": "Maps de upstream dedicado configurados"}

    except Exception as e:
        logger.error(f"Error configurando dedicated maps en {node_ip}: {e}")
        return {"success": False, "changed": False, "message": str(e)}


def _resolve_all_domains_for_tenant(
    subdomain: str, node_ip: str = CT105_IP
) -> List[str]:
    """
    Resuelve TODOS los hostnames que enrutan a un tenant dado.

    Incluye:
      - {subdomain}.sajet.us (siempre)
      - Dominios públicos del map $tenant_db del nginx (techeels.io, agroliferd.com, etc.)
      - Aliases con www.

    Lee el map $tenant_db del nginx actual para descubrir todos los hostnames
    que mapean a la BD del tenant. Esto es la fuente de verdad porque nginx
    es quien finalmente enruta el tráfico.

    Returns:
        Lista de hostnames (ej: ["cliente1.sajet.us", "midominio.com", "www.midominio.com"])
    """
    domains = [f"{subdomain}.sajet.us"]

    try:
        content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)

        # Extraer el bloque map $host $tenant_db { ... }
        pattern = r"map\s+\$host\s+\$tenant_db\s*\{(.*?)\}"
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            logger.warning("No se encontró map $tenant_db en nginx — solo usando subdominio .sajet.us")
            return domains

        map_body = match.group(1)

        # Parsear cada línea: "dominio valor;"
        # Buscar todas las entradas que mapean al subdomain del tenant
        for line in map_body.split("\n"):
            line = line.strip().rstrip(";").strip()
            if not line or line.startswith("#") or line.startswith("default") or line.startswith("~"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                hostname = parts[0]
                db_name = parts[1]
                # Si este hostname mapea a la BD del tenant, incluirlo
                if db_name == subdomain and hostname not in domains:
                    domains.append(hostname)

    except Exception as e:
        logger.warning(f"Error leyendo dominios de nginx para {subdomain}: {e}")

    logger.info(f"  🌐 Dominios resueltos para {subdomain}: {domains}")
    return domains


def configure_dedicated_routing(
    subdomain: str,
    http_port: int,
    chat_port: int,
    node_ip: str = CT105_IP,
) -> Dict[str, Any]:
    """
    Configura el routing nginx para que un tenant use su servicio dedicado.

    Agrega entries en los maps $odoo_http_upstream y $odoo_chat_upstream
    para TODOS los hostnames del tenant (subdominio .sajet.us + dominios públicos).

    Ejemplo para tenant "techeels" en puerto 9001:
      - techeels.sajet.us → http://127.0.0.1:9001
      - techeels.io       → http://127.0.0.1:9001
      - www.techeels.io   → http://127.0.0.1:9001
      - impulse-max.com   → http://127.0.0.1:9001
      - etc.

    Args:
        subdomain: nombre del tenant (ej: "cliente1")
        http_port: puerto HTTP dedicado (ej: 9000)
        chat_port: puerto chat/longpolling dedicado (ej: 9500)
        node_ip: IP del nodo Odoo

    Returns:
        {"success": bool, "message": str, "domains": list}
    """
    http_backend = f"http://127.0.0.1:{http_port}"
    chat_backend = f"http://127.0.0.1:{chat_port}"

    try:
        # Primero asegurar que los maps de upstream existen
        setup = ensure_dedicated_maps_exist(node_ip=node_ip)
        if not setup["success"]:
            return setup

        # Resolver TODOS los dominios/hostnames del tenant
        all_domains = _resolve_all_domains_for_tenant(subdomain, node_ip=node_ip)

        content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
        backup = content

        # Agregar entry para CADA dominio del tenant
        for domain in all_domains:
            content = _add_to_map(content, DEDICATED_HTTP_MAP_VAR, domain, http_backend)
            content = _add_to_map(content, DEDICATED_CHAT_MAP_VAR, domain, chat_backend)

        _write_file_node(CT105_ODOO_CONF, content, node_ip=node_ip)

        rc, _, err = _run_node("nginx -t", node_ip=node_ip)
        if rc != 0:
            _write_file_node(CT105_ODOO_CONF, backup, node_ip=node_ip)
            return {"success": False, "message": f"nginx -t falló, rollback: {err}"}

        _run_node("systemctl reload nginx", node_ip=node_ip)
        logger.info(
            f"✅ Routing dedicado configurado: {len(all_domains)} dominios → "
            f"HTTP:{http_port}, Chat:{chat_port}"
        )
        return {
            "success": True,
            "message": (
                f"Routing dedicado: {len(all_domains)} dominios → "
                f":{http_port}/:{chat_port}"
            ),
            "domains": all_domains,
            "http_upstream": http_backend,
            "chat_upstream": chat_backend,
        }

    except Exception as e:
        logger.error(f"Error configurando dedicated routing para {subdomain}: {e}")
        return {"success": False, "message": str(e)}


def remove_dedicated_routing(
    subdomain: str,
    node_ip: str = CT105_IP,
) -> Dict[str, Any]:
    """
    Revierte el routing dedicado de un tenant — vuelve al upstream shared default.

    Elimina las entries de TODOS los hostnames del tenant de los maps
    $odoo_http_upstream y $odoo_chat_upstream.
    El default del map (shared 8069/8072) se encarga automáticamente.

    Args:
        subdomain: nombre del tenant (ej: "cliente1")
        node_ip: IP del nodo Odoo
    """
    try:
        # Resolver todos los dominios del tenant
        all_domains = _resolve_all_domains_for_tenant(subdomain, node_ip=node_ip)

        content = _read_file_node(CT105_ODOO_CONF, node_ip=node_ip)
        backup = content

        # Remover entry para CADA dominio del tenant
        for domain in all_domains:
            content = _remove_from_map(content, DEDICATED_HTTP_MAP_VAR, domain)
            content = _remove_from_map(content, DEDICATED_CHAT_MAP_VAR, domain)

        _write_file_node(CT105_ODOO_CONF, content, node_ip=node_ip)

        rc, _, err = _run_node("nginx -t", node_ip=node_ip)
        if rc != 0:
            _write_file_node(CT105_ODOO_CONF, backup, node_ip=node_ip)
            return {"success": False, "message": f"nginx -t falló, rollback: {err}"}

        _run_node("systemctl reload nginx", node_ip=node_ip)
        logger.info(f"✅ Routing dedicado removido: {len(all_domains)} dominios → shared pool")
        return {
            "success": True,
            "message": f"Routing revertido a shared: {len(all_domains)} dominios",
            "domains_removed": all_domains,
        }

    except Exception as e:
        logger.error(f"Error removiendo dedicated routing para {subdomain}: {e}")
        return {"success": False, "message": str(e)}
