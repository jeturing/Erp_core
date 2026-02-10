"""
Proxmox Manager - Multi-node cluster management for distributed Odoo deployment
"""
import subprocess
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

from ..models.database import (
    SessionLocal, ProxmoxNode, LXCContainer, TenantDeployment,
    Subscription, NodeStatus, ContainerStatus, PlanType
)

logger = logging.getLogger(__name__)


class ProxmoxManager:
    """Gestiona el cluster de nodos Proxmox para despliegue distribuido"""
    
    # Configuración de recursos por plan
    PLAN_RESOURCES = {
        PlanType.basic: {
            "cpu_cores": 1,
            "ram_mb": 2048,
            "disk_gb": 20,
            "shared": True,
            "priority": 1
        },
        PlanType.pro: {
            "cpu_cores": 2,
            "ram_mb": 4096,
            "disk_gb": 50,
            "shared": False,
            "priority": 2
        },
        PlanType.enterprise: {
            "cpu_cores": 4,
            "ram_mb": 8192,
            "disk_gb": 100,
            "shared": False,
            "priority": 3
        }
    }
    
    @classmethod
    def get_available_node(cls, plan: PlanType = PlanType.basic) -> Optional[ProxmoxNode]:
        """
        Selecciona el mejor nodo disponible para un nuevo tenant.
        Criterios:
        1. Estado online
        2. Capacidad disponible
        3. Prioridad del nodo
        4. Menor carga actual
        """
        db = SessionLocal()
        try:
            resources = cls.PLAN_RESOURCES.get(plan, cls.PLAN_RESOURCES[PlanType.basic])
            
            # Buscar nodos online con capacidad
            nodes = db.query(ProxmoxNode).filter(
                ProxmoxNode.status == NodeStatus.online,
                ProxmoxNode.is_database_node == False,
                ProxmoxNode.current_containers < ProxmoxNode.max_containers
            ).order_by(
                ProxmoxNode.priority.desc(),
                ProxmoxNode.used_cpu_percent.asc()
            ).all()
            
            for node in nodes:
                # Verificar recursos disponibles
                available_ram = node.total_ram_gb * 1024 - node.used_ram_gb * 1024
                available_storage = node.total_storage_gb - node.used_storage_gb
                
                if (available_ram >= resources["ram_mb"] and 
                    available_storage >= resources["disk_gb"]):
                    return node
            
            logger.warning("No hay nodos disponibles con capacidad suficiente")
            return None
            
        finally:
            db.close()
    
    @classmethod
    def get_next_vmid(cls, node: ProxmoxNode) -> int:
        """Obtiene el siguiente VMID disponible en un nodo"""
        db = SessionLocal()
        try:
            max_vmid = db.query(LXCContainer).filter(
                LXCContainer.node_id == node.id
            ).order_by(LXCContainer.vmid.desc()).first()
            
            if max_vmid:
                return max_vmid.vmid + 1
            return 200  # VMID inicial para tenants
        finally:
            db.close()
    
    @classmethod
    async def provision_on_node(
        cls,
        node: ProxmoxNode,
        subdomain: str,
        plan: PlanType,
        subscription_id: int
    ) -> Dict[str, Any]:
        """
        Provisiona un nuevo contenedor en un nodo específico.
        """
        db = SessionLocal()
        try:
            resources = cls.PLAN_RESOURCES.get(plan, cls.PLAN_RESOURCES[PlanType.basic])
            vmid = cls.get_next_vmid(node)
            hostname = f"{subdomain}-odoo"
            
            # Crear registro del contenedor
            container = LXCContainer(
                node_id=node.id,
                vmid=vmid,
                hostname=hostname,
                cpu_cores=resources["cpu_cores"],
                ram_mb=resources["ram_mb"],
                disk_gb=resources["disk_gb"],
                is_shared=resources["shared"],
                status=ContainerStatus.provisioning,
                template_used="odoo-17-template"
            )
            db.add(container)
            db.commit()
            db.refresh(container)
            
            # Ejecutar provisioning real via SSH/API
            success = await cls._execute_provisioning(node, container, subdomain)
            
            if success:
                # Actualizar estado
                container.status = ContainerStatus.running
                container.ip_address = await cls._get_container_ip(node, vmid)
                
                # Crear deployment
                deployment = TenantDeployment(
                    subscription_id=subscription_id,
                    container_id=container.id,
                    subdomain=subdomain,
                    database_name=subdomain,
                    plan_type=plan,
                    tunnel_url=f"{subdomain}.sajet.us"
                )
                db.add(deployment)
                
                # Actualizar contador de nodo
                node.current_containers += 1
                node.used_ram_gb += resources["ram_mb"] / 1024
                node.used_storage_gb += resources["disk_gb"]
                
                # Actualizar suscripción
                subscription = db.query(Subscription).filter_by(id=subscription_id).first()
                if subscription:
                    from ..models.database import SubscriptionStatus
                    subscription.status = SubscriptionStatus.active
                    subscription.tenant_provisioned = True
                
                db.commit()
                
                logger.info(f"Tenant {subdomain} provisionado en nodo {node.name} (VMID: {vmid})")
                
                return {
                    "success": True,
                    "node": node.name,
                    "vmid": vmid,
                    "url": f"https://{subdomain}.sajet.us",
                    "container_id": container.id
                }
            else:
                container.status = ContainerStatus.error
                db.commit()
                return {
                    "success": False,
                    "error": "Provisioning failed"
                }
                
        except Exception as e:
            logger.exception(f"Error provisioning tenant: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()
    
    @classmethod
    async def _execute_provisioning(
        cls,
        node: ProxmoxNode,
        container: LXCContainer,
        subdomain: str
    ) -> bool:
        """Ejecuta el script de provisioning en el nodo remoto"""
        try:
            # Comando para crear contenedor via pct
            cmd = (
                f"ssh -p {node.ssh_port} {node.ssh_user}@{node.hostname} "
                f"'cd /root/Cloudflare && ./create_tenant.sh {subdomain}'"
            )
            
            logger.info(f"Ejecutando provisioning: {cmd}")
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Provisioning exitoso para {subdomain}")
                return True
            else:
                logger.error(f"Provisioning fallido: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout en provisioning de {subdomain}")
            return False
        except Exception as e:
            logger.exception(f"Error en provisioning: {e}")
            return False
    
    @classmethod
    async def _get_container_ip(cls, node: ProxmoxNode, vmid: int) -> Optional[str]:
        """Obtiene la IP de un contenedor"""
        try:
            cmd = (
                f"ssh -p {node.ssh_port} {node.ssh_user}@{node.hostname} "
                f"'pct exec {vmid} -- hostname -I | cut -d\" \" -f1'"
            )
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    @classmethod
    def get_cluster_status(cls) -> Dict[str, Any]:
        """Obtiene el estado general del cluster"""
        db = SessionLocal()
        try:
            nodes = db.query(ProxmoxNode).all()
            
            total_containers = 0
            total_cpu = 0
            used_cpu = 0
            total_ram = 0
            used_ram = 0
            online_nodes = 0
            
            node_stats = []
            for node in nodes:
                total_containers += node.current_containers
                total_cpu += node.total_cpu_cores
                total_ram += node.total_ram_gb
                used_ram += node.used_ram_gb
                
                if node.status == NodeStatus.online:
                    online_nodes += 1
                
                node_stats.append({
                    "id": node.id,
                    "name": node.name,
                    "region": node.region,
                    "status": node.status.value,
                    "containers": node.current_containers,
                    "max_containers": node.max_containers,
                    "cpu_percent": node.used_cpu_percent,
                    "ram_used_gb": node.used_ram_gb,
                    "ram_total_gb": node.total_ram_gb,
                    "storage_used_gb": node.used_storage_gb,
                    "storage_total_gb": node.total_storage_gb
                })
            
            return {
                "total_nodes": len(nodes),
                "online_nodes": online_nodes,
                "total_containers": total_containers,
                "cluster_health": "healthy" if online_nodes > 0 else "critical",
                "total_ram_gb": total_ram,
                "used_ram_gb": used_ram,
                "ram_percent": (used_ram / total_ram * 100) if total_ram > 0 else 0,
                "nodes": node_stats
            }
        finally:
            db.close()
    
    @classmethod
    def register_node(
        cls,
        name: str,
        hostname: str,
        total_cpu: int,
        total_ram_gb: float,
        total_storage_gb: float,
        region: str = "default",
        ssh_port: int = 22,
        api_port: int = 8006,
        max_containers: int = 50,
        is_database_node: bool = False
    ) -> ProxmoxNode:
        """Registra un nuevo nodo en el cluster"""
        db = SessionLocal()
        try:
            node = ProxmoxNode(
                name=name,
                hostname=hostname,
                ssh_port=ssh_port,
                api_port=api_port,
                total_cpu_cores=total_cpu,
                total_ram_gb=total_ram_gb,
                total_storage_gb=total_storage_gb,
                max_containers=max_containers,
                is_database_node=is_database_node,
                region=region,
                status=NodeStatus.online
            )
            db.add(node)
            db.commit()
            db.refresh(node)
            
            logger.info(f"Nodo registrado: {name} ({hostname})")
            return node
        finally:
            db.close()
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, Any]:
        """Ejecuta health check en todos los nodos"""
        db = SessionLocal()
        try:
            nodes = db.query(ProxmoxNode).all()
            results = []
            
            for node in nodes:
                try:
                    # Ping simple
                    cmd = f"ssh -p {node.ssh_port} -o ConnectTimeout=5 {node.ssh_user}@{node.hostname} 'echo ok'"
                    result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
                    
                    is_online = result.returncode == 0
                    
                    if is_online:
                        node.status = NodeStatus.online
                        node.last_health_check = datetime.utcnow()
                    else:
                        node.status = NodeStatus.offline
                    
                    results.append({
                        "node": node.name,
                        "status": "online" if is_online else "offline"
                    })
                    
                except Exception as e:
                    node.status = NodeStatus.offline
                    results.append({
                        "node": node.name,
                        "status": "error",
                        "error": str(e)
                    })
            
            db.commit()
            return {"checks": results}
        finally:
            db.close()
