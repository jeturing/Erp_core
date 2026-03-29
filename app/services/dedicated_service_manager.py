"""
DedicatedServiceManager — Provisioning y gestión de servicios Odoo dedicados (Fase 3).

Pasos 3.1–3.4 del plan de migración:
  3.1  Template systemd odoo-tenant@.service con conf per-tenant
  3.2  Port management: HTTP 9000-9499, chat 9500-9999 por nodo
  3.3  Overlay de addons: /opt/odoo/tenant-addons/{tenant}
  3.4  Provisioning completo: reservar puertos → generar conf → crear overlay
       → levantar servicio → validar /web/login → publicar rutas

PostgreSQL sigue centralizado en PCT 137 — no se crea BD nueva.
"""
from __future__ import annotations

import logging
import subprocess
import textwrap
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..config import ODOO_DB_HOST, ODOO_DB_PORT, ODOO_DB_USER, ODOO_DB_PASSWORD
from ..models.database import (
    AuditEventRecord,
    MigrationState,
    ProxmoxNode,
    RoutingMode,
    RuntimeMode,
    TenantDeployment,
)

logger = logging.getLogger(__name__)

# ── Constantes de rango de puertos ──────────────────────────────────
HTTP_PORT_RANGE = (9000, 9499)   # 500 slots por nodo
CHAT_PORT_RANGE = (9500, 9999)   # 500 slots por nodo

# Paths estándar en los nodos Odoo
ODOO_BASE_ADDONS_PATH = "/opt/odoo/odoo-bin/../addons,/opt/odoo/extra-addons"
TENANT_ADDONS_BASE = "/opt/odoo/tenant-addons"
TENANT_CONF_DIR = "/etc/odoo"
ODOO_BIN_PATH = "/opt/odoo/odoo-bin"
ODOO_VENV_PYTHON = "/opt/odoo/venv/bin/python3"


class DedicatedServiceManager:
    """Gestiona el ciclo de vida de servicios Odoo dedicados por tenant."""

    # ══════════════════════════════════════════════════════════════════
    # 3.2 — Port Management
    # ══════════════════════════════════════════════════════════════════

    def get_used_ports(self, db: Session, node_id: int) -> Dict[str, List[int]]:
        """
        Obtiene los puertos HTTP y chat ya asignados a tenants dedicados
        en un nodo específico.
        """
        deployments = db.query(TenantDeployment).filter(
            TenantDeployment.active_node_id == node_id,
            TenantDeployment.runtime_mode == RuntimeMode.dedicated_service,
        ).all()

        http_ports = []
        chat_ports = []
        for dep in deployments:
            if dep.http_port and HTTP_PORT_RANGE[0] <= dep.http_port <= HTTP_PORT_RANGE[1]:
                http_ports.append(dep.http_port)
            if dep.chat_port and CHAT_PORT_RANGE[0] <= dep.chat_port <= CHAT_PORT_RANGE[1]:
                chat_ports.append(dep.chat_port)

        return {"http": sorted(http_ports), "chat": sorted(chat_ports)}

    def allocate_ports(self, db: Session, node_id: int) -> Tuple[int, int]:
        """
        Reserva atómicamente un par de puertos (HTTP, chat) para un nuevo
        servicio dedicado en un nodo.

        Retorna (http_port, chat_port).
        Lanza ValueError si no hay puertos disponibles.
        """
        used = self.get_used_ports(db, node_id)

        # Buscar primer puerto HTTP libre
        http_port = None
        for p in range(HTTP_PORT_RANGE[0], HTTP_PORT_RANGE[1] + 1):
            if p not in used["http"]:
                http_port = p
                break

        if http_port is None:
            raise ValueError(
                f"No hay puertos HTTP disponibles en nodo {node_id} "
                f"(rango {HTTP_PORT_RANGE[0]}-{HTTP_PORT_RANGE[1]} lleno)"
            )

        # Chat port tiene offset fijo: http_port + 500
        chat_port = http_port + (CHAT_PORT_RANGE[0] - HTTP_PORT_RANGE[0])
        if chat_port in used["chat"]:
            # Fallback: buscar siguiente chat port libre
            chat_port = None
            for p in range(CHAT_PORT_RANGE[0], CHAT_PORT_RANGE[1] + 1):
                if p not in used["chat"]:
                    chat_port = p
                    break
            if chat_port is None:
                raise ValueError(
                    f"No hay puertos chat disponibles en nodo {node_id} "
                    f"(rango {CHAT_PORT_RANGE[0]}-{CHAT_PORT_RANGE[1]} lleno)"
                )

        return http_port, chat_port

    def release_ports(self, deployment: TenantDeployment) -> None:
        """
        Libera los puertos de un deployment dedicado (resetea a defaults shared).
        Se llama al desmontar el servicio dedicado.
        """
        deployment.http_port = 8080
        deployment.chat_port = 8072

    # ══════════════════════════════════════════════════════════════════
    # 3.1 — Template systemd + configuración per-tenant
    # ══════════════════════════════════════════════════════════════════

    def generate_odoo_conf(
        self,
        subdomain: str,
        db_name: str,
        http_port: int,
        chat_port: int,
        addons_path_extra: str = "",
    ) -> str:
        """
        Genera el contenido de /etc/odoo/tenant-{subdomain}.conf
        """
        addons_path = ODOO_BASE_ADDONS_PATH
        if addons_path_extra:
            addons_path = f"{addons_path_extra},{addons_path}"

        return textwrap.dedent(f"""\
            [options]
            ; Tenant: {subdomain}
            ; Auto-generated by SAJET DedicatedServiceManager
            admin_passwd = False
            db_host = {ODOO_DB_HOST}
            db_port = {ODOO_DB_PORT}
            db_user = {ODOO_DB_USER}
            db_password = {ODOO_DB_PASSWORD}
            db_name = {db_name}
            dbfilter = ^{db_name}$
            http_port = {http_port}
            longpolling_port = {chat_port}
            gevent_port = {chat_port}
            workers = 2
            max_cron_threads = 1
            limit_memory_hard = 2684354560
            limit_memory_soft = 2147483648
            limit_time_cpu = 600
            limit_time_real = 1200
            data_dir = /var/lib/odoo
            logfile = /var/log/odoo/tenant-{subdomain}.log
            log_level = info
            addons_path = {addons_path}
            server_wide_modules = base,web,redis_session_store
            session_redis_url = redis://:JtrRedis2026!@10.10.10.7:6379/0
            session_redis_expire = 604800
            proxy_mode = True
            list_db = False
        """)

    def generate_systemd_unit(self) -> str:
        """
        Genera el template systemd odoo-tenant@.service.

        El nombre de instancia (%i) es el subdomain del tenant.
        Conf en /etc/odoo/tenant-%i.conf.
        """
        return textwrap.dedent(f"""\
            [Unit]
            Description=Odoo Tenant Dedicated Service - %i
            Documentation=https://sajet.us/docs/dedicated-service
            After=network.target postgresql.service
            Wants=network.target

            [Service]
            Type=simple
            User=odoo
            Group=odoo
            ExecStart={ODOO_VENV_PYTHON} {ODOO_BIN_PATH} -c {TENANT_CONF_DIR}/tenant-%i.conf
            Restart=on-failure
            RestartSec=10
            TimeoutStartSec=120
            TimeoutStopSec=30
            StandardOutput=journal
            StandardError=journal
            SyslogIdentifier=odoo-tenant-%i
            LimitNOFILE=65536

            [Install]
            WantedBy=multi-user.target
        """)

    # ══════════════════════════════════════════════════════════════════
    # 3.3 — Overlay de addons per-tenant
    # ══════════════════════════════════════════════════════════════════

    def create_addons_overlay(
        self, node_ip: str, subdomain: str
    ) -> Tuple[bool, str]:
        """
        Crea el directorio de overlay de addons para un tenant dedicado.
        Path: /opt/odoo/tenant-addons/{subdomain}/
        """
        overlay_path = f"{TENANT_ADDONS_BASE}/{subdomain}"
        rc, _, err = self._ssh_cmd(
            node_ip,
            f"mkdir -p {overlay_path} && chown odoo:odoo {overlay_path}",
        )
        if rc == 0:
            return True, overlay_path
        return False, f"Failed to create overlay: {err}"

    def remove_addons_overlay(
        self, node_ip: str, subdomain: str
    ) -> Tuple[bool, str]:
        """Elimina el overlay de addons de un tenant dedicado."""
        overlay_path = f"{TENANT_ADDONS_BASE}/{subdomain}"
        rc, _, err = self._ssh_cmd(
            node_ip,
            f"rm -rf {overlay_path}",
        )
        if rc == 0:
            return True, "Overlay removed"
        return False, f"Failed to remove overlay: {err}"

    # ══════════════════════════════════════════════════════════════════
    # 3.4 — Provisioning completo de dedicated_service
    # ══════════════════════════════════════════════════════════════════

    async def provision_dedicated(
        self,
        db: Session,
        deployment: TenantDeployment,
        node: ProxmoxNode,
        initiated_by: str = "admin",
    ) -> Dict:
        """
        Provisiona un servicio Odoo dedicado para un tenant existente.

        Pasos:
          1. Reservar puertos (HTTP + chat)
          2. Crear overlay de addons
          3. Generar conf per-tenant
          4. Instalar template systemd (idempotente)
          5. Desplegar conf y habilitar servicio
          6. Arrancar servicio y validar /web/login
          7. Actualizar TenantDeployment
          8. Auditoría

        Retorna dict con resultado detallado.
        """
        import asyncio

        subdomain = deployment.subdomain
        db_name = deployment.database_name or subdomain
        node_ip = node.hostname
        result: Dict = {"subdomain": subdomain, "node": node.name, "steps": {}}

        logger.info(
            f"🚀 Provisioning dedicated service: {subdomain} on {node.name} ({node_ip})"
        )

        try:
            # 1. Reservar puertos
            http_port, chat_port = self.allocate_ports(db, node.id)
            result["steps"]["ports"] = {
                "status": "ok", "http_port": http_port, "chat_port": chat_port
            }
            logger.info(f"  📌 Ports allocated: HTTP={http_port}, Chat={chat_port}")

            # 2. Crear overlay de addons
            ok, overlay_path = await asyncio.to_thread(
                self.create_addons_overlay, node_ip, subdomain
            )
            if not ok:
                raise RuntimeError(f"Failed to create addons overlay: {overlay_path}")
            result["steps"]["overlay"] = {"status": "ok", "path": overlay_path}
            logger.info(f"  📁 Addons overlay created: {overlay_path}")

            # 3. Generar conf
            conf_content = self.generate_odoo_conf(
                subdomain=subdomain,
                db_name=db_name,
                http_port=http_port,
                chat_port=chat_port,
                addons_path_extra=overlay_path,
            )
            conf_path = f"{TENANT_CONF_DIR}/tenant-{subdomain}.conf"

            # 4. Instalar template systemd (idempotente)
            template_content = self.generate_systemd_unit()
            await asyncio.to_thread(
                self._deploy_systemd_template, node_ip, template_content
            )
            result["steps"]["systemd_template"] = {"status": "ok"}
            logger.info("  ⚙️ Systemd template deployed")

            # 5. Desplegar conf y habilitar servicio
            await asyncio.to_thread(
                self._deploy_tenant_conf, node_ip, conf_path, conf_content, subdomain
            )
            result["steps"]["conf"] = {"status": "ok", "path": conf_path}
            logger.info(f"  📝 Tenant conf deployed: {conf_path}")

            # 6. Arrancar servicio y validar
            service_name = f"odoo-tenant@{subdomain}"
            await asyncio.to_thread(
                self._start_and_validate, node_ip, service_name, http_port
            )
            result["steps"]["service"] = {"status": "ok", "name": service_name}
            logger.info(f"  ✅ Service started and validated: {service_name}")

            # 7. Actualizar TenantDeployment
            deployment.runtime_mode = RuntimeMode.dedicated_service
            deployment.routing_mode = RoutingMode.direct_service
            deployment.http_port = http_port
            deployment.chat_port = chat_port
            deployment.service_name = service_name
            deployment.addons_overlay_path = overlay_path
            deployment.active_node_id = node.id
            deployment.backend_host = node_ip
            db.flush()
            result["steps"]["deployment_updated"] = {"status": "ok"}
            logger.info("  💾 Deployment updated to dedicated_service")

            # 8. Auditoría
            self._audit(db, "dedicated_provisioned", subdomain, {
                "node_id": node.id,
                "http_port": http_port,
                "chat_port": chat_port,
                "service_name": service_name,
                "initiated_by": initiated_by,
            })

            result["success"] = True
            result["message"] = f"Servicio dedicado '{service_name}' provisionado en {node.name}"
            logger.info(f"🎉 Dedicated service provisioned: {subdomain} on {node.name}")

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.error(f"❌ Dedicated provisioning failed for {subdomain}: {e}", exc_info=True)
            # Intentar cleanup parcial
            await self._cleanup_partial(db, deployment, node_ip, subdomain)
            raise

        return result

    async def deprovision_dedicated(
        self,
        db: Session,
        deployment: TenantDeployment,
        node_ip: str,
    ) -> Dict:
        """
        Desmonta un servicio dedicado — revierte a shared_pool.

        Pasos:
          1. Detener y deshabilitar servicio systemd
          2. Eliminar conf per-tenant
          3. Eliminar overlay de addons
          4. Liberar puertos
          5. Actualizar deployment a shared_pool
        """
        import asyncio

        subdomain = deployment.subdomain
        service_name = deployment.service_name or f"odoo-tenant@{subdomain}"
        result: Dict = {"subdomain": subdomain, "steps": {}}

        logger.info(f"🔧 Deprovisioning dedicated service: {service_name}")

        try:
            # 1. Detener servicio
            await asyncio.to_thread(
                self._stop_service, node_ip, service_name
            )
            result["steps"]["service_stopped"] = {"status": "ok"}

            # 2. Eliminar conf
            conf_path = f"{TENANT_CONF_DIR}/tenant-{subdomain}.conf"
            self._ssh_cmd(node_ip, f"rm -f {conf_path}")
            result["steps"]["conf_removed"] = {"status": "ok"}

            # 3. Eliminar overlay
            await asyncio.to_thread(
                self.remove_addons_overlay, node_ip, subdomain
            )
            result["steps"]["overlay_removed"] = {"status": "ok"}

            # 4. Liberar puertos
            self.release_ports(deployment)
            result["steps"]["ports_released"] = {"status": "ok"}

            # 5. Actualizar deployment
            deployment.runtime_mode = RuntimeMode.shared_pool
            deployment.routing_mode = RoutingMode.node_proxy
            deployment.service_name = None
            deployment.addons_overlay_path = None
            db.flush()
            result["steps"]["deployment_updated"] = {"status": "ok"}

            self._audit(db, "dedicated_deprovisioned", subdomain, {
                "service_name": service_name,
            })

            result["success"] = True
            result["message"] = f"Servicio dedicado '{service_name}' desmontado"
            logger.info(f"✅ Dedicated service deprovisioned: {subdomain}")

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.error(f"❌ Deprovision failed for {subdomain}: {e}", exc_info=True)

        return result

    # ══════════════════════════════════════════════════════════════════
    # Infrastructure helpers
    # ══════════════════════════════════════════════════════════════════

    def _ssh_cmd(
        self, node_ip: str, cmd: str, timeout: int = 30
    ) -> Tuple[int, str, str]:
        """Ejecuta comando SSH en un nodo."""
        safe = cmd.replace("'", "'\\''")
        full = f"ssh -o BatchMode=yes -o ConnectTimeout=5 root@{node_ip} '{safe}'"
        try:
            r = subprocess.run(
                full, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        except subprocess.TimeoutExpired:
            return 1, "", f"SSH timeout after {timeout}s"
        except Exception as e:
            return 1, "", str(e)

    def _deploy_systemd_template(self, node_ip: str, content: str) -> None:
        """
        Despliega el template systemd odoo-tenant@.service en el nodo.
        Idempotente — solo escribe si el contenido cambió.
        """
        import base64
        b64 = base64.b64encode(content.encode()).decode()
        template_path = "/etc/systemd/system/odoo-tenant@.service"

        self._ssh_cmd(
            node_ip,
            f"echo '{b64}' | base64 -d > {template_path} && systemctl daemon-reload",
            timeout=15,
        )

    def _deploy_tenant_conf(
        self, node_ip: str, conf_path: str, content: str, subdomain: str
    ) -> None:
        """Despliega la configuración per-tenant y habilita el servicio."""
        import base64
        b64 = base64.b64encode(content.encode()).decode()
        service_name = f"odoo-tenant@{subdomain}"

        # Crear directorio de logs
        self._ssh_cmd(node_ip, "mkdir -p /var/log/odoo && chown odoo:odoo /var/log/odoo")

        # Desplegar conf
        rc, _, err = self._ssh_cmd(
            node_ip,
            f"echo '{b64}' | base64 -d > {conf_path} && "
            f"chown odoo:odoo {conf_path} && "
            f"systemctl enable {service_name}",
            timeout=15,
        )
        if rc != 0:
            raise RuntimeError(f"Failed to deploy conf for {subdomain}: {err}")

    def _start_and_validate(
        self, node_ip: str, service_name: str, http_port: int
    ) -> None:
        """Arranca el servicio y valida que Odoo responde."""
        import time

        # Arrancar servicio
        rc, _, err = self._ssh_cmd(
            node_ip,
            f"systemctl start {service_name}",
            timeout=30,
        )
        if rc != 0:
            raise RuntimeError(f"Failed to start {service_name}: {err}")

        # Esperar arranque (max 60s)
        for attempt in range(12):
            time.sleep(5)
            rc, out, _ = self._ssh_cmd(
                node_ip,
                f"curl -s -o /dev/null -w '%{{http_code}}' "
                f"http://127.0.0.1:{http_port}/web/login",
                timeout=10,
            )
            if rc == 0 and out.strip() in ("200", "303"):
                return

        # Si no responde, obtener log y fallar
        _, log_tail, _ = self._ssh_cmd(
            node_ip,
            f"journalctl -u {service_name} --no-pager -n 20",
            timeout=10,
        )
        raise RuntimeError(
            f"Service {service_name} started but Odoo not responding on port "
            f"{http_port} after 60s. Last log:\n{log_tail[:500]}"
        )

    def _stop_service(self, node_ip: str, service_name: str) -> None:
        """Detiene y deshabilita un servicio systemd."""
        self._ssh_cmd(
            node_ip,
            f"systemctl stop {service_name} 2>/dev/null; "
            f"systemctl disable {service_name} 2>/dev/null",
            timeout=30,
        )

    async def _cleanup_partial(
        self,
        db: Session,
        deployment: TenantDeployment,
        node_ip: str,
        subdomain: str,
    ) -> None:
        """Limpieza parcial tras un fallo de provisioning."""
        import asyncio
        logger.info(f"🧹 Cleaning up partial provisioning for {subdomain}")
        try:
            service_name = f"odoo-tenant@{subdomain}"
            await asyncio.to_thread(self._stop_service, node_ip, service_name)
            self._ssh_cmd(node_ip, f"rm -f {TENANT_CONF_DIR}/tenant-{subdomain}.conf")
            await asyncio.to_thread(self.remove_addons_overlay, node_ip, subdomain)
        except Exception as e:
            logger.warning(f"Cleanup error for {subdomain}: {e}")

    def _audit(self, db: Session, event_type: str, subdomain: str, details: dict) -> None:
        """Registra evento de auditoría."""
        try:
            evt = AuditEventRecord(
                event_type=event_type.upper(),
                actor_username="dedicated_service_manager",
                resource=f"tenant:{subdomain}",
                action="dedicated_service",
                status="info",
                details=details,
            )
            db.add(evt)
            db.flush()
        except Exception as e:
            logger.warning(f"Could not create audit event: {e}")

    # ══════════════════════════════════════════════════════════════════
    # Queries de estado
    # ══════════════════════════════════════════════════════════════════

    def get_dedicated_stats(self, db: Session, node_id: int) -> Dict:
        """Obtiene estadísticas de servicios dedicados en un nodo."""
        dedicated_count = db.query(TenantDeployment).filter(
            TenantDeployment.active_node_id == node_id,
            TenantDeployment.runtime_mode == RuntimeMode.dedicated_service,
        ).count()

        shared_count = db.query(TenantDeployment).filter(
            TenantDeployment.active_node_id == node_id,
            TenantDeployment.runtime_mode == RuntimeMode.shared_pool,
        ).count()

        used_ports = self.get_used_ports(db, node_id)

        return {
            "dedicated_count": dedicated_count,
            "shared_count": shared_count,
            "total_deployments": dedicated_count + shared_count,
            "http_ports_used": len(used_ports["http"]),
            "chat_ports_used": len(used_ports["chat"]),
            "http_ports_available": (HTTP_PORT_RANGE[1] - HTTP_PORT_RANGE[0] + 1) - len(used_ports["http"]),
            "chat_ports_available": (CHAT_PORT_RANGE[1] - CHAT_PORT_RANGE[0] + 1) - len(used_ports["chat"]),
        }


# ── Singleton ──────────────────────────────────────────────────────────

dedicated_manager = DedicatedServiceManager()
