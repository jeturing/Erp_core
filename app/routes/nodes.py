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
from datetime import datetime

from ..models.database import (
    SessionLocal, ProxmoxNode, LXCContainer, TenantDeployment,
    NodeStatus, ContainerStatus, PlanType
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
                    "priority": node.priority,
                    "containers": {
                        "current": node.current_containers,
                        "max": node.max_containers
                    },
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
            node.last_health_check  = datetime.utcnow()
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
                "last_updated": datetime.utcnow().isoformat()
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
                    node.last_health_check = datetime.utcnow()
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
