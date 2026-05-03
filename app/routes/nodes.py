"""
Nodes Routes - Proxmox cluster management endpoints
"""
import asyncio
import os
import subprocess
from fastapi import APIRouter, HTTPException, Cookie, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from ..models.database import (
    SessionLocal, ProxmoxNode, LXCContainer, TenantDeployment,
    NodeStatus, ContainerStatus, PlanType, CustomDomain,
    MigrationState,
)
from ..services.proxmox_manager import ProxmoxManager
from ..security.tokens import TokenManager

router = APIRouter(prefix="/api/nodes", tags=["Nodes"])


# ===== DTOs =====

class NodeCreateRequest(BaseModel):
    name: str
    hostname: str
    total_cpu_cores: int
    total_ram_gb: float
    total_storage_gb: float
    region: str = "default"
    ssh_port: int = 22
    api_port: int = 8006
    max_containers: int = 50
    is_database_node: bool = False
    ssh_user: str = "root"
    api_token_id: Optional[str] = None


class NodeUpdateRequest(BaseModel):
    name: Optional[str] = None
    hostname: Optional[str] = None
    max_containers: Optional[int] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    region: Optional[str] = None


class ProvisionRequest(BaseModel):
    subdomain: str
    plan: str = "basic"  # basic, pro, enterprise
    subscription_id: int


# ===== Helper =====

def get_token_from_request(request: Request, cookie_token: str = None) -> str:
    """Extrae token desde cookie o header Authorization: Bearer"""
    if cookie_token:
        return cookie_token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


def verify_admin(token: str) -> bool:
    """Verifica que el token sea de admin"""
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        payload = TokenManager.verify_access_token(token)
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return True
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=401, detail="Token inválido")


# ===== Endpoints =====

@router.get("")
async def list_nodes(access_token: str = Cookie(None)):
    """Lista todos los nodos del cluster"""
    verify_admin(access_token)
    
    db = SessionLocal()
    try:
        nodes = db.query(ProxmoxNode).order_by(ProxmoxNode.priority.desc()).all()

        # Count active deployments per node
        from sqlalchemy import func
        deployment_counts = dict(
            db.query(
                TenantDeployment.active_node_id,
                func.count(TenantDeployment.id),
            )
            .filter(TenantDeployment.active_node_id.isnot(None))
            .group_by(TenantDeployment.active_node_id)
            .all()
        )

        # Count active migrations per node (as target)
        active_migration_states = [
            MigrationState.queued, MigrationState.preflight,
            MigrationState.preparing_target, MigrationState.warming_target,
            MigrationState.cutover, MigrationState.verifying,
        ]
        from ..models.database import TenantMigrationJob
        migrating_to = dict(
            db.query(
                TenantMigrationJob.target_node_id,
                func.count(TenantMigrationJob.id),
            )
            .filter(TenantMigrationJob.state.in_(active_migration_states))
            .group_by(TenantMigrationJob.target_node_id)
            .all()
        )

        # Agrupar dominios activos por target_node_ip para vincularlos a cada nodo
        all_domains = db.query(CustomDomain).filter(CustomDomain.is_active == True).all()
        domains_by_ip: dict = {}
        for d in all_domains:
            ip = d.target_node_ip
            if not ip:
                continue
            if ip not in domains_by_ip:
                domains_by_ip[ip] = []
            domains_by_ip[ip].append({
                "id": d.id,
                "domain": d.external_domain or d.sajet_subdomain,
                "cloudflare_configured": d.cloudflare_configured,
                "ssl_status": d.ssl_status,
                "is_primary": d.is_primary,
                "verification_status": d.verification_status,
            })

        return {
            "items": [
                {
                    "id": node.id,
                    "name": node.name,
                    "hostname": node.hostname,
                    "region": node.region,
                    "status": node.status.value,
                    "proxmox_version": node.proxmox_version,
                    "is_database_node": node.is_database_node,
                    "can_host_tenants": getattr(node, 'can_host_tenants', False),
                    "priority": node.priority,
                    "containers": {
                        "current": node.current_containers,
                        "max": node.max_containers
                    },
                    "active_deployments_count": deployment_counts.get(node.id, 0),
                    "available_slots": max(0, node.max_containers - deployment_counts.get(node.id, 0)),
                    "active_migrations_count": migrating_to.get(node.id, 0),
                    "supported_runtime_modes": ["shared_pool"],
                    "resources": {
                        "cpu": {
                            "total_cores": node.total_cpu_cores,
                            "usage_percent": node.used_cpu_percent
                        },
                        "ram": {
                            "total_gb": node.total_ram_gb,
                            "used_gb": node.used_ram_gb,
                            "usage_percent": (node.used_ram_gb / node.total_ram_gb * 100) if node.total_ram_gb > 0 else 0
                        },
                        "storage": {
                            "total_gb": node.total_storage_gb,
                            "used_gb": node.used_storage_gb,
                            "usage_percent": (node.used_storage_gb / node.total_storage_gb * 100) if node.total_storage_gb > 0 else 0
                        }
                    },
                    "domains": domains_by_ip.get(node.hostname, []),
                    "last_health_check": node.last_health_check.isoformat() if node.last_health_check else None,
                    "created_at": node.created_at.isoformat() if node.created_at else None
                }
                for node in nodes
            ],
            "total": len(nodes)
        }
    finally:
        db.close()


@router.get("/status")
async def get_cluster_status(access_token: str = Cookie(None)):
    """Obtiene el estado general del cluster"""
    verify_admin(access_token)
    return ProxmoxManager.get_cluster_status()


@router.post("")
async def create_node(payload: NodeCreateRequest, access_token: str = Cookie(None)):
    """Registra un nuevo nodo en el cluster"""
    verify_admin(access_token)
    
    db = SessionLocal()
    try:
        # Verificar que no exista
        existing = db.query(ProxmoxNode).filter_by(name=payload.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un nodo con ese nombre")
        
        node = ProxmoxNode(
            name=payload.name,
            hostname=payload.hostname,
            ssh_port=payload.ssh_port,
            api_port=payload.api_port,
            total_cpu_cores=payload.total_cpu_cores,
            total_ram_gb=payload.total_ram_gb,
            total_storage_gb=payload.total_storage_gb,
            max_containers=payload.max_containers,
            is_database_node=payload.is_database_node,
            region=payload.region,
            ssh_user=payload.ssh_user,
            api_token_id=payload.api_token_id,
            status=NodeStatus.online
        )
        db.add(node)
        db.commit()
        db.refresh(node)
        
        return {"message": "Nodo creado", "id": node.id, "name": node.name}
    finally:
        db.close()


# ===== CAPACITY MANAGEMENT ENDPOINTS (before /{node_id} to avoid path conflicts) =====

@router.get("/capacity")
async def get_cluster_capacity(access_token: str = Cookie(None)):
    """
    Evaluación completa de capacidad del cluster.
    Score dinámico 0-100 por nodo, alertas, slots disponibles y recomendaciones.
    """
    verify_admin(access_token)
    from ..services.node_capacity_service import NodeCapacityService
    return NodeCapacityService.evaluate_all_nodes()


@router.post("/evaluate-capacity")
async def evaluate_and_alert(access_token: str = Cookie(None)):
    """
    Fuerza re-evaluación de capacidad, persiste alertas y aplica auto-drain.
    Usar después de un health-check o cambio de recursos.
    """
    verify_admin(access_token)
    from ..services.node_capacity_service import NodeCapacityService
    result = NodeCapacityService.evaluate_all_nodes()
    return {
        "success": True,
        "data": result,
        "meta": {
            "alerts_generated": len(result.get("alerts", [])),
            "cluster_action": result.get("cluster", {}).get("action", "OK"),
        }
    }


@router.get("/capacity/best-node")
async def get_best_node_for_provisioning(access_token: str = Cookie(None)):
    """
    Devuelve el mejor nodo disponible para provisionar un nuevo tenant,
    usando scoring dinámico en vez de prioridad estática.
    """
    verify_admin(access_token)
    from ..services.node_capacity_service import NodeCapacityService

    result = NodeCapacityService.get_best_node()
    if not result:
        raise HTTPException(
            status_code=503,
            detail="No hay nodos con capacidad disponible. SCALE_OUT requerido."
        )

    node = result["node"]
    return {
        "node_id": node.id,
        "name": node.name,
        "hostname": node.hostname,
        "vmid": getattr(node, "vmid", None),
        "capacity_score": result["score"],
        "active_tenants": result["active_tenants"],
        "available_slots": result["available_slots"],
    }


@router.get("/capacity/rebalance")
async def get_rebalance_recommendations(access_token: str = Cookie(None)):
    """
    Recomendaciones de rebalanceo: qué tenants mover y a dónde
    para equilibrar la carga del cluster.
    """
    verify_admin(access_token)
    from ..services.node_capacity_service import NodeCapacityService

    recommendations = NodeCapacityService.get_rebalance_recommendations()
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
        "has_action_required": any(
            r.get("action") == "scale_out" for r in recommendations
        ),
    }


@router.get("/{node_id}")
async def get_node(node_id: int, access_token: str = Cookie(None)):
    """Obtiene detalle de un nodo específico"""
    verify_admin(access_token)
    
    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
        # Obtener contenedores del nodo
        containers = db.query(LXCContainer).filter_by(node_id=node_id).all()
        
        return {
            "id": node.id,
            "name": node.name,
            "hostname": node.hostname,
            "region": node.region,
            "status": node.status.value,
            "proxmox_version": node.proxmox_version,
            "is_database_node": node.is_database_node,
            "priority": node.priority,
            "ssh_port": node.ssh_port,
            "api_port": node.api_port,
            "resources": {
                "cpu_cores": node.total_cpu_cores,
                "cpu_usage": node.used_cpu_percent,
                "ram_total_gb": node.total_ram_gb,
                "ram_used_gb": node.used_ram_gb,
                "storage_total_gb": node.total_storage_gb,
                "storage_used_gb": node.used_storage_gb
            },
            "containers": {
                "current": node.current_containers,
                "max": node.max_containers,
                "list": [
                    {
                        "id": c.id,
                        "vmid": c.vmid,
                        "hostname": c.hostname,
                        "status": c.status.value,
                        "ip": c.ip_address,
                        "cpu": c.cpu_cores,
                        "ram_mb": c.ram_mb
                    }
                    for c in containers
                ]
            },
            "last_health_check": node.last_health_check.isoformat() if node.last_health_check else None
        }
    finally:
        db.close()


@router.put("/{node_id}")
async def update_node(node_id: int, payload: NodeUpdateRequest, access_token: str = Cookie(None)):
    """Actualiza un nodo"""
    verify_admin(access_token)
    
    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
        if payload.name:
            node.name = payload.name
        if payload.hostname:
            node.hostname = payload.hostname
        if payload.max_containers:
            node.max_containers = payload.max_containers
        if payload.priority is not None:
            node.priority = payload.priority
        if payload.region:
            node.region = payload.region
        if payload.status:
            try:
                node.status = NodeStatus(payload.status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Estado inválido")
        
        db.commit()
        return {"message": "Nodo actualizado", "id": node.id}
    finally:
        db.close()


@router.delete("/{node_id}")
async def delete_node(node_id: int, access_token: str = Cookie(None)):
    """Elimina un nodo del cluster"""
    verify_admin(access_token)
    
    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
        # Verificar que no tenga contenedores
        if node.current_containers > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar: tiene {node.current_containers} contenedores activos"
            )
        
        db.delete(node)
        db.commit()
        return {"message": "Nodo eliminado"}
    finally:
        db.close()


@router.post("/{node_id}/maintenance")
async def toggle_maintenance(node_id: int, enable: bool = True, access_token: str = Cookie(None)):
    """Pone un nodo en modo mantenimiento"""
    verify_admin(access_token)
    
    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        
        node.status = NodeStatus.maintenance if enable else NodeStatus.online
        db.commit()
        
        return {
            "message": f"Nodo {'en mantenimiento' if enable else 'activo'}",
            "status": node.status.value
        }
    finally:
        db.close()


@router.get("/{node_id}/domains")
async def get_node_domains(node_id: int, request: Request, access_token: str = Cookie(None)):
    """Devuelve los dominios Cloudflare vinculados a un nodo por target_node_ip"""
    verify_admin(get_token_from_request(request, access_token))
    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")
        domains = db.query(CustomDomain).filter(
            CustomDomain.is_active == True,
            CustomDomain.target_node_ip == node.hostname
        ).all()
        return {
            "node_id": node.id,
            "node_name": node.name,
            "node_ip": node.hostname,
            "domains": [
                {
                    "id": d.id,
                    "domain": d.external_domain or d.sajet_subdomain,
                    "cloudflare_configured": d.cloudflare_configured,
                    "cloudflare_dns_record_id": d.cloudflare_dns_record_id,
                    "ssl_status": d.ssl_status,
                    "verification_status": d.verification_status,
                    "is_primary": d.is_primary,
                    "target_port": d.target_port,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in domains
            ],
            "total": len(domains)
        }
    finally:
        db.close()


@router.get("/{node_id}/live-stats")
async def get_node_live_stats(node_id: int, request: Request, access_token: str = Cookie(None)):
    """Obtiene métricas en vivo de un nodo via SSH con password"""
    verify_admin(get_token_from_request(request, access_token))

    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")

        # Script de stats compacto que corre en el nodo remoto
        stats_script = (
            "nproc; "
            "cat /proc/cpuinfo | grep 'cpu MHz' | awk '{s+=$4;c++} END{printf \"%.0f\\n\", s/c}'; "
            "top -bn1 | grep 'Cpu' | awk '{print 100-$8}'; "
            "free -m | awk '/Mem/{print $2,$3}'; "
            "df / -BG | awk 'NR==2{gsub(/G/,\"\",$2); gsub(/G/,\"\",$3); print $2,$3}'; "
            "uptime -p 2>/dev/null || uptime; "
            "cat /proc/loadavg"
        )

        # Rutas absolutas — el servicio systemd tiene PATH restringido a /var/www/html/venv/bin
        sshpass_bin = "/usr/bin/sshpass" if os.path.exists("/usr/bin/sshpass") else "/bin/sshpass"
        ssh_bin     = "/usr/bin/ssh"     if os.path.exists("/usr/bin/ssh")     else "/bin/ssh"

        use_password = bool(node.ssh_password)
        if use_password:
            cmd = [
                sshpass_bin, "-p", node.ssh_password,
                ssh_bin,
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=8",
                "-o", "BatchMode=no",
                "-p", str(node.ssh_port),
                f"{node.ssh_user}@{node.hostname}",
                stats_script
            ]
        else:
            cmd = [
                ssh_bin,
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=8",
                "-p", str(node.ssh_port),
                f"{node.ssh_user}@{node.hostname}",
                stats_script
            ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                # Actualizar estado a offline si falla
                node.status = NodeStatus.offline
                db.commit()
                return {
                    "node_id": node_id,
                    "name": node.name,
                    "online": False,
                    "error": result.stderr.strip() or "SSH connection failed"
                }

            lines = result.stdout.strip().splitlines()
            cpu_cores   = int(lines[0]) if len(lines) > 0 else node.total_cpu_cores
            cpu_mhz     = int(lines[1]) if len(lines) > 1 else 0
            cpu_pct     = float(lines[2]) if len(lines) > 2 else 0.0
            ram_parts   = lines[3].split() if len(lines) > 3 else ["0", "0"]
            disk_parts  = lines[4].split() if len(lines) > 4 else ["0", "0"]
            uptime_str  = lines[5] if len(lines) > 5 else ""
            loadavg_str = lines[6] if len(lines) > 6 else "0 0 0"

            ram_total_mb = int(ram_parts[0]) if ram_parts else 0
            ram_used_mb  = int(ram_parts[1]) if len(ram_parts) > 1 else 0
            disk_total   = int(disk_parts[0]) if disk_parts else 0
            disk_used    = int(disk_parts[1]) if len(disk_parts) > 1 else 0

            ram_pct  = round(ram_used_mb / ram_total_mb * 100, 1) if ram_total_mb > 0 else 0
            disk_pct = round(disk_used / disk_total * 100, 1) if disk_total > 0 else 0

            loadavg = loadavg_str.split()[:3] if loadavg_str else ["0", "0", "0"]

            # Actualizar BD con métricas frescas
            node.used_cpu_percent   = round(cpu_pct, 1)
            node.used_ram_gb        = round(ram_used_mb / 1024, 2)
            node.total_ram_gb       = round(ram_total_mb / 1024, 2)
            node.used_storage_gb    = float(disk_used)
            node.total_storage_gb   = float(disk_total) if disk_total > 0 else node.total_storage_gb
            node.status             = NodeStatus.online
            node.last_health_check  = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()

            return {
                "node_id": node_id,
                "name": node.name,
                "hostname": node.hostname,
                "online": True,
                "is_database_node": node.is_database_node,
                "region": node.region,
                "cpu": {
                    "cores": cpu_cores,
                    "usage_percent": round(cpu_pct, 1),
                    "mhz": cpu_mhz,
                    "load_avg": {"1m": loadavg[0], "5m": loadavg[1], "15m": loadavg[2]}
                },
                "ram": {
                    "total_mb": ram_total_mb,
                    "used_mb": ram_used_mb,
                    "free_mb": ram_total_mb - ram_used_mb,
                    "usage_percent": ram_pct
                },
                "disk": {
                    "total_gb": disk_total,
                    "used_gb": disk_used,
                    "free_gb": disk_total - disk_used,
                    "usage_percent": disk_pct
                },
                "uptime": uptime_str,
                "last_updated": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            }

        except subprocess.TimeoutExpired:
            node.status = NodeStatus.offline
            db.commit()
            return {"node_id": node_id, "name": node.name, "online": False, "error": "SSH timeout"}
        except FileNotFoundError as e:
            return {"node_id": node_id, "name": node.name, "online": False, "error": f"Binario no encontrado: {e}"}

    finally:
        db.close()


@router.post("/health-check-all")
async def run_health_check_all(request: Request, access_token: str = Cookie(None)):
    """Ejecuta health check + actualiza métricas en todos los nodos"""
    verify_admin(get_token_from_request(request, access_token))

    db = SessionLocal()
    try:
        nodes = db.query(ProxmoxNode).all()
        results = []

        sshpass_bin = "/usr/bin/sshpass" if os.path.exists("/usr/bin/sshpass") else "/bin/sshpass"
        ssh_bin     = "/usr/bin/ssh"     if os.path.exists("/usr/bin/ssh")     else "/bin/ssh"

        for node in nodes:
            use_password = bool(node.ssh_password)
            base_ssh = [sshpass_bin, "-p", node.ssh_password] if use_password else []
            cmd = base_ssh + [
                ssh_bin, "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                "-o", f"BatchMode={'no' if use_password else 'yes'}",
                "-p", str(node.ssh_port),
                f"{node.ssh_user}@{node.hostname}",
                "echo ok"
            ]
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=10)
                is_online = r.returncode == 0
                node.status = NodeStatus.online if is_online else NodeStatus.offline
                if is_online:
                    node.last_health_check = datetime.now(timezone.utc).replace(tzinfo=None)
                results.append({"node": node.name, "status": "online" if is_online else "offline"})
            except Exception as e:
                node.status = NodeStatus.offline
                results.append({"node": node.name, "status": "error", "error": str(e)})

        db.commit()
        return {"checks": results, "total": len(results)}
    finally:
        db.close()


@router.post("/health-check")
async def run_health_check(access_token: str = Cookie(None)):
    """Ejecuta health check en todos los nodos"""
    verify_admin(access_token)
    return await ProxmoxManager.health_check_all()


@router.post("/health-report")
async def receive_health_report(request: Request):
    """
    Endpoint push: un nodo local reporta su estado de salud al orquestador.
    El agente local (odoo_local_api.py) puede llamar aquí periódicamente.
    
    Autenticado via header X-API-KEY (la misma key del agente local).
    Body esperado: {"hostname": "10.10.10.100", "status": "ok", "metrics": {...}}
    """
    # Validar API key del nodo
    api_key = request.headers.get("X-API-KEY", "")
    expected_key = os.getenv("PROVISIONING_API_KEY", "")
    if not api_key or api_key != expected_key:
        raise HTTPException(status_code=401, detail="API key inválida")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body JSON inválido")

    hostname = body.get("hostname", "").strip()
    status = body.get("status", "").strip().lower()
    metrics = body.get("metrics", {})

    if not hostname:
        raise HTTPException(status_code=400, detail="hostname requerido")

    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter(ProxmoxNode.hostname == hostname).first()
        if not node:
            raise HTTPException(status_code=404, detail=f"Nodo {hostname} no registrado")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        node.last_health_check = now

        if status == "ok":
            if node.status == NodeStatus.offline:
                node.status = NodeStatus.online

            # Actualizar métricas si se proporcionaron
            if metrics.get("cpu_percent") is not None:
                node.used_cpu_percent = float(metrics["cpu_percent"])
            if metrics.get("ram_used_gb") is not None:
                node.used_ram_gb = float(metrics["ram_used_gb"])
            if metrics.get("disk_used_gb") is not None:
                node.used_storage_gb = float(metrics["disk_used_gb"])

            # Actualizar last_healthcheck_at en deployments del nodo
            db.query(TenantDeployment).filter(
                TenantDeployment.active_node_id == node.id
            ).update(
                {"last_healthcheck_at": now},
                synchronize_session="fetch",
            )

        db.commit()
        return {
            "success": True,
            "node": node.name,
            "status": node.status.value,
            "last_health_check": now.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/metrics/scan")
async def scan_all_metrics(access_token: str = Cookie(None)):
    """Ejecuta escaneo completo de métricas de todos los nodos y contenedores"""
    verify_admin(access_token)
    from ..services.resource_monitor import ResourceMonitor
    return await ResourceMonitor.run_full_scan()


@router.get("/metrics/summary")
async def get_cluster_summary(access_token: str = Cookie(None)):
    """Obtiene resumen de recursos del cluster para dashboards"""
    verify_admin(access_token)
    from ..services.resource_monitor import ResourceMonitor
    return ResourceMonitor.get_cluster_summary()


@router.get("/metrics/history")
async def get_metrics_history(
    node_id: Optional[int] = None,
    container_id: Optional[int] = None,
    hours: int = 24,
    access_token: str = Cookie(None)
):
    """Obtiene métricas históricas para gráficos"""
    verify_admin(access_token)
    from ..services.resource_monitor import ResourceMonitor
    return {
        "hours": hours,
        "data": ResourceMonitor.get_historical_metrics(node_id, container_id, hours)
    }


@router.post("/provision")
async def provision_tenant(payload: ProvisionRequest, access_token: str = Cookie(None)):
    """Provisiona un nuevo tenant en el mejor nodo disponible"""
    verify_admin(access_token)
    
    # Mapear plan
    plan_map = {
        "basic": PlanType.basic,
        "pro": PlanType.pro,
        "enterprise": PlanType.enterprise
    }
    plan = plan_map.get(payload.plan.lower(), PlanType.basic)
    
    # Obtener mejor nodo
    node = ProxmoxManager.get_available_node(plan)
    if not node:
        raise HTTPException(
            status_code=503,
            detail="No hay nodos disponibles con capacidad suficiente"
        )
    
    # Provisionar
    result = await ProxmoxManager.provision_on_node(
        node=node,
        subdomain=payload.subdomain,
        plan=plan,
        subscription_id=payload.subscription_id
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Provisioning failed"))


@router.get("/containers/all")
async def list_all_containers(access_token: str = Cookie(None)):
    """Lista todos los contenedores de todos los nodos"""
    verify_admin(access_token)
    
    db = SessionLocal()
    try:
        containers = db.query(LXCContainer).join(ProxmoxNode).all()
        
        return {
            "items": [
                {
                    "id": c.id,
                    "node": c.node.name if c.node else None,
                    "vmid": c.vmid,
                    "hostname": c.hostname,
                    "status": c.status.value,
                    "ip": c.ip_address,
                    "resources": {
                        "cpu": c.cpu_cores,
                        "ram_mb": c.ram_mb,
                        "disk_gb": c.disk_gb
                    },
                    "usage": {
                        "cpu_percent": c.cpu_usage_percent,
                        "ram_mb": c.ram_usage_mb,
                        "disk_gb": c.disk_usage_gb
                    },
                    "is_shared": c.is_shared,
                    "created_at": c.created_at.isoformat() if c.created_at else None
                }
                for c in containers
            ],
            "total": len(containers)
        }
    finally:
        db.close()


# ===== PER-NODE CAPACITY ENDPOINTS =====

@router.get("/{node_id}/capacity")
async def get_node_capacity(node_id: int, access_token: str = Cookie(None)):
    """Score y detalle de capacidad de un nodo específico."""
    verify_admin(access_token)
    from ..services.node_capacity_service import NodeCapacityService
    from sqlalchemy import func

    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")

        active = db.query(func.count(TenantDeployment.id)).filter(
            TenantDeployment.active_node_id == node_id
        ).scalar() or 0

        score = NodeCapacityService.compute_score(node, active)
        max_t = NodeCapacityService.effective_max_tenants(node)
        alerts = NodeCapacityService.evaluate_thresholds(node, active)

        return {
            "node_id": node_id,
            "name": node.name,
            "capacity_score": score,
            "tenants": {
                "active": active,
                "max": max_t,
                "max_by_ram": NodeCapacityService.max_tenants_by_ram(node),
                "max_by_io": NodeCapacityService.max_tenants_by_io(node),
                "available_slots": NodeCapacityService.available_slots(node, active),
            },
            "policy": {
                "tenant_ram_mb": int(getattr(node, "tenant_ram_mb", 800) or 800),
                "system_overhead_mb": int(getattr(node, "system_overhead_mb", 1200) or 1200),
                "storage_type": getattr(node, "storage_type", "loop"),
                "io_max_tenants": int(getattr(node, "io_max_tenants", 8) or 8),
                "stagger_delay_sec": int(getattr(node, "stagger_delay_sec", 12) or 12),
                "auto_drain": bool(getattr(node, "auto_drain", False)),
            },
            "thresholds": {
                "cpu": {"warning": getattr(node, "cpu_threshold_warning", 70),
                        "critical": getattr(node, "cpu_threshold_critical", 90)},
                "ram": {"warning": getattr(node, "ram_threshold_warning", 75),
                        "critical": getattr(node, "ram_threshold_critical", 90)},
                "storage": {"warning": getattr(node, "storage_threshold_warning", 70),
                            "critical": getattr(node, "storage_threshold_critical", 85)},
            },
            "alerts": alerts,
        }
    finally:
        db.close()


class NodeCapacityUpdateRequest(BaseModel):
    """Actualizar política de capacidad de un nodo."""
    cpu_threshold_warning: Optional[float] = None
    cpu_threshold_critical: Optional[float] = None
    ram_threshold_warning: Optional[float] = None
    ram_threshold_critical: Optional[float] = None
    storage_threshold_warning: Optional[float] = None
    storage_threshold_critical: Optional[float] = None
    tenant_ram_mb: Optional[int] = None
    system_overhead_mb: Optional[int] = None
    max_tenants_override: Optional[int] = None
    storage_type: Optional[str] = None
    io_max_tenants: Optional[int] = None
    auto_drain: Optional[bool] = None
    stagger_delay_sec: Optional[int] = None


@router.put("/{node_id}/capacity")
async def update_node_capacity_policy(
    node_id: int, payload: NodeCapacityUpdateRequest, access_token: str = Cookie(None)
):
    """Actualizar umbrales y política de capacidad de un nodo."""
    verify_admin(access_token)

    db = SessionLocal()
    try:
        node = db.query(ProxmoxNode).filter_by(id=node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Nodo no encontrado")

        update_data = {
            k: v for k, v in payload.dict().items() if v is not None
        }
        if not update_data:
            raise HTTPException(status_code=400, detail="Sin datos para actualizar")

        db.query(ProxmoxNode).filter_by(id=node_id).update(update_data)
        db.commit()

        return {"success": True, "updated": list(update_data.keys())}
    finally:
        db.close()
