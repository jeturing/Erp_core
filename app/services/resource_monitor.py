"""
Resource Monitor - Monitoreo de recursos de nodos y contenedores
"""
import subprocess
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, cast

from ..models.database import (
    SessionLocal, ProxmoxNode, LXCContainer, ResourceMetric,
    NodeStatus, ContainerStatus
)

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitorea recursos de nodos Proxmox y contenedores LXC"""
    
    @classmethod
    async def update_node_metrics(cls, node: ProxmoxNode) -> Dict[str, Any]:
        """Actualiza métricas de un nodo específico"""
        try:
            # Obtener uso de CPU
            cpu_cmd = (
                f"ssh -p {node.ssh_port} -o ConnectTimeout=5 {node.ssh_user}@{node.hostname} "
                f"\"grep 'cpu ' /proc/stat | awk '{{usage=($2+$4)*100/($2+$4+$5)}} END {{print usage}}'\""
            )
            
            # Obtener uso de RAM
            ram_cmd = (
                f"ssh -p {node.ssh_port} -o ConnectTimeout=5 {node.ssh_user}@{node.hostname} "
                f"\"free -g | awk 'NR==2{{print $3}}'\""
            )
            
            # Obtener uso de disco
            disk_cmd = (
                f"ssh -p {node.ssh_port} -o ConnectTimeout=5 {node.ssh_user}@{node.hostname} "
                f"\"df -BG /var/lib/vz | awk 'NR==2{{gsub(\\\"G\\\",\\\"\\\"); print $3}}'\""
            )
            
            # Ejecutar comandos
            cpu_result = subprocess.run(cpu_cmd, shell=True, capture_output=True, text=True, timeout=15)
            ram_result = subprocess.run(ram_cmd, shell=True, capture_output=True, text=True, timeout=15)
            disk_result = subprocess.run(disk_cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            cpu_percent = float(cpu_result.stdout.strip()) if cpu_result.returncode == 0 else 0
            ram_used = float(ram_result.stdout.strip()) if ram_result.returncode == 0 else 0
            disk_used = float(disk_result.stdout.strip()) if disk_result.returncode == 0 else 0
            
            # Actualizar en BD (usar update para evitar conflictos con tipos de Column)
            db = SessionLocal()
            try:
                db_node = db.query(ProxmoxNode).filter_by(id=node.id).first()
                if db_node:
                    nid = getattr(db_node, "id")
                    db.query(ProxmoxNode).filter_by(id=nid).update({
                        ProxmoxNode.used_cpu_percent: round(float(cpu_percent), 2),
                        ProxmoxNode.used_ram_gb: float(ram_used),
                        ProxmoxNode.used_storage_gb: float(disk_used),
                        ProxmoxNode.last_health_check: datetime.utcnow(),
                        ProxmoxNode.status: NodeStatus.online,
                    })

                    # Guardar métrica histórica
                    metric = ResourceMetric(
                        node_id=nid,
                        cpu_percent=float(cpu_percent),
                        ram_mb=float(ram_used) * 1024,
                        disk_gb=float(disk_used)
                    )
                    db.add(metric)
                    db.commit()

                return {
                    "node": getattr(node, "name", None),
                    "status": "online",
                    "cpu_percent": cpu_percent,
                    "ram_used_gb": ram_used,
                    "disk_used_gb": disk_used
                }
            finally:
                db.close()
                
        except subprocess.TimeoutExpired:
            nid = getattr(node, "id", None)
            if nid is not None:
                cls._mark_node_offline(nid)
            return {"node": node.name, "status": "timeout"}
        except Exception as e:
            logger.error(f"Error monitoreando nodo {node.name}: {e}")
            nid = getattr(node, "id", None)
            if nid is not None:
                cls._mark_node_offline(nid)
            return {"node": node.name, "status": "error", "error": str(e)}
    
    @classmethod
    def _mark_node_offline(cls, node_id: Any):
        """Marca un nodo como offline"""
        db = SessionLocal()
        try:
            # Usar update para evitar problemas de tipado en analizadores estáticos
            updated = db.query(ProxmoxNode).filter_by(id=node_id).update({
                ProxmoxNode.status: NodeStatus.offline
            })
            if updated:
                db.commit()
        finally:
            db.close()
    
    @classmethod
    async def update_container_metrics(cls, container: LXCContainer) -> Dict[str, Any]:
        """Actualiza métricas de un contenedor específico"""
        try:
            node = container.node
            if not node or node.status != NodeStatus.online:
                return {"container": container.hostname, "status": "node_offline"}
            
            # Obtener métricas via pct
            cmd = (
                f"ssh -p {node.ssh_port} -o ConnectTimeout=5 {node.ssh_user}@{node.hostname} "
                f"\"pct status {container.vmid} && pct exec {container.vmid} -- "
                f"sh -c 'echo CPU:$(cat /proc/loadavg | cut -d\\\" \\\" -f1) "
                f"RAM:$(free -m | awk \\'NR==2{{print $3}}\\') "
                f"DISK:$(df -BM / | awk \\'NR==2{{gsub(\\\"M\\\",\\\"\\\"); print $3}}\\')'\""
            )
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and "running" in result.stdout.lower():
                # Parsear salida
                output = result.stdout
                
                cpu_usage = 0
                ram_usage = 0
                disk_usage = 0
                
                if "CPU:" in output:
                    try:
                        cpu_part = output.split("CPU:")[1].split()[0]
                        cpu_cores = int(getattr(container, "cpu_cores", 1) or 1)
                        cpu_usage = float(cpu_part) * 100 / cpu_cores
                    except Exception:
                        pass
                
                if "RAM:" in output:
                    try:
                        ram_part = output.split("RAM:")[1].split()[0]
                        ram_usage = float(ram_part)
                    except Exception:
                        pass
                
                if "DISK:" in output:
                    try:
                        disk_part = output.split("DISK:")[1].split()[0]
                        disk_usage = float(disk_part) / 1024  # MB a GB
                    except Exception:
                        pass
                
                # Actualizar en BD (usar update para evitar conflictos de tipado)
                db = SessionLocal()
                try:
                    db_container = db.query(LXCContainer).filter_by(id=container.id).first()
                    if db_container:
                        cid = getattr(db_container, "id")
                        db.query(LXCContainer).filter_by(id=cid).update({
                            LXCContainer.cpu_usage_percent: min(100, round(float(cpu_usage), 2)),
                            LXCContainer.ram_usage_mb: float(ram_usage),
                            LXCContainer.disk_usage_gb: float(disk_usage),
                            LXCContainer.status: ContainerStatus.running,
                        })

                        # Guardar métrica histórica
                        metric = ResourceMetric(
                            container_id=cid,
                            cpu_percent=float(cpu_usage),
                            ram_mb=float(ram_usage),
                            disk_gb=float(disk_usage)
                        )
                        db.add(metric)
                        db.commit()
                finally:
                    db.close()
                
                return {
                    "container": container.hostname,
                    "status": "running",
                    "cpu_percent": cpu_usage,
                    "ram_mb": ram_usage,
                    "disk_gb": disk_usage
                }
            else:
                # Contenedor no está corriendo
                db = SessionLocal()
                try:
                    db.query(LXCContainer).filter_by(id=container.id).update({
                        LXCContainer.status: ContainerStatus.stopped
                    })
                    db.commit()
                finally:
                    db.close()
                
                return {"container": container.hostname, "status": "stopped"}
                
        except Exception as e:
            logger.error(f"Error monitoreando contenedor {container.hostname}: {e}")
            return {"container": container.hostname, "status": "error", "error": str(e)}
    
    @classmethod
    async def run_full_scan(cls) -> Dict[str, Any]:
        """Ejecuta un escaneo completo de todos los nodos y contenedores"""
        db = SessionLocal()
        try:
            nodes = db.query(ProxmoxNode).all()
            
            node_results = []
            container_results = []
            
            for node in nodes:
                # Actualizar métricas del nodo
                node_result = await cls.update_node_metrics(node)
                node_results.append(node_result)
                
                # Si el nodo está online, actualizar sus contenedores
                if node_result.get("status") == "online":
                    containers = db.query(LXCContainer).filter_by(node_id=node.id).all()
                    for container in containers:
                        container_result = await cls.update_container_metrics(container)
                        container_results.append(container_result)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "nodes_scanned": len(node_results),
                "containers_scanned": len(container_results),
                "node_results": node_results,
                "container_results": container_results
            }
        finally:
            db.close()
    
    @classmethod
    def get_cluster_summary(cls) -> Dict[str, Any]:
        """Obtiene resumen del cluster para el dashboard"""
        db = SessionLocal()
        try:
            nodes = db.query(ProxmoxNode).all()
            
            total_cpu = 0
            used_cpu_weighted = 0
            total_ram = 0
            used_ram = 0
            total_storage = 0
            used_storage = 0
            online_nodes = 0
            total_containers = 0
            running_containers = 0
            
            for node in nodes:
                t_cpu = int(getattr(node, "total_cpu_cores", 0) or 0)
                t_ram = float(getattr(node, "total_ram_gb", 0) or 0)
                t_storage = float(getattr(node, "total_storage_gb", 0) or 0)
                u_ram = float(getattr(node, "used_ram_gb", 0) or 0)
                u_storage = float(getattr(node, "used_storage_gb", 0) or 0)
                u_cpu = float(getattr(node, "used_cpu_percent", 0) or 0)

                total_cpu += t_cpu
                total_ram += t_ram
                total_storage += t_storage
                used_ram += u_ram
                used_storage += u_storage

                if getattr(node, "status", None) == NodeStatus.online:
                    online_nodes += 1
                    used_cpu_weighted += (u_cpu * t_cpu)

                total_containers += int(getattr(node, "current_containers", 0) or 0)
            
            # Contar contenedores running
            running_containers = db.query(LXCContainer).filter_by(
                status=ContainerStatus.running
            ).count()
            
            avg_cpu = (used_cpu_weighted / total_cpu) if total_cpu > 0 else 0.0
            ram_percent = (used_ram / total_ram * 100) if total_ram > 0 else 0.0
            storage_percent = (used_storage / total_storage * 100) if total_storage > 0 else 0.0
            
            # Determinar estado de salud
            if online_nodes == 0:
                health = "critical"
            elif avg_cpu > 85 or ram_percent > 90:
                health = "warning"
            else:
                health = "healthy"
            
            return {
                "health": health,
                "nodes": {
                    "total": len(nodes),
                    "online": online_nodes
                },
                "containers": {
                    "total": total_containers,
                    "running": running_containers
                },
                "resources": {
                    "cpu": {
                        "cores": total_cpu,
                        "usage_percent": round(float(avg_cpu), 1)
                    },
                    "ram": {
                        "total_gb": total_ram,
                        "used_gb": round(float(used_ram), 1),
                        "usage_percent": round(float(ram_percent), 1)
                    },
                    "storage": {
                        "total_gb": total_storage,
                        "used_gb": round(float(used_storage), 1),
                        "usage_percent": round(float(storage_percent), 1)
                    }
                }
            }
        finally:
            db.close()
    
    @classmethod
    def get_historical_metrics(
        cls,
        node_id: Optional[int] = None,
        container_id: Optional[int] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Obtiene métricas históricas para gráficos"""
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            query = db.query(ResourceMetric).filter(
                ResourceMetric.recorded_at >= since
            )
            
            if node_id:
                query = query.filter(ResourceMetric.node_id == node_id)
            if container_id:
                query = query.filter(ResourceMetric.container_id == container_id)
            
            metrics = query.order_by(ResourceMetric.recorded_at.asc()).all()
            
            return [
                {
                    "timestamp": m.recorded_at.isoformat(),
                    "cpu_percent": m.cpu_percent,
                    "ram_mb": m.ram_mb,
                    "disk_gb": m.disk_gb,
                    "network_in_mb": m.network_in_mb,
                    "network_out_mb": m.network_out_mb
                }
                for m in metrics
            ]
        finally:
            db.close()
    
    @classmethod
    def cleanup_old_metrics(cls, days: int = 30):
        """Limpia métricas antiguas"""
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = db.query(ResourceMetric).filter(
                ResourceMetric.recorded_at < cutoff
            ).delete()
            db.commit()
            logger.info(f"Eliminadas {deleted} métricas antiguas")
            return deleted
        finally:
            db.close()
