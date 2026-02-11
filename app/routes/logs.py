"""
Logs Routes - API para logs del sistema en tiempo real
"""
from fastapi import APIRouter, HTTPException, Request, Cookie, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import subprocess
import os
import logging

from .roles import verify_token_with_role
from ..models.database import SessionLocal

router = APIRouter(prefix="/api/logs", tags=["Logs"])
logger = logging.getLogger(__name__)

# Directorio base de logs
LOG_DIR = "/opt/Erp_core/logs"


def _verify_admin(token: str):
    """Verifica que el usuario sea admin"""
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        verify_token_with_role(token, required_role="admin")
    except HTTPException:
        raise


@router.get("/provisioning")
async def get_provisioning_logs(
    request: Request,
    access_token: str = Cookie(None),
    lines: int = Query(100, ge=10, le=500),
    level: Optional[str] = Query(None, description="Filtrar por nivel: info, warning, error")
) -> Dict[str, Any]:
    """
    Obtiene logs de provisioning del sistema.
    
    Args:
        lines: Número de líneas a retornar (default 100, max 500)
        level: Filtrar por nivel (info, warning, error)
    """
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
    try:
        log_file = os.path.join(LOG_DIR, "provisioning.log")
        logs = []
        
        if os.path.exists(log_file):
            # Leer últimas N líneas del archivo
            result = subprocess.run(
                ["tail", "-n", str(lines), log_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    # Filtrar por nivel si se especifica
                    if level:
                        level_upper = level.upper()
                        if level_upper not in line.upper():
                            continue
                    
                    # Colorear según nivel
                    log_class = "text-slate-400"  # default
                    if "ERROR" in line.upper():
                        log_class = "text-rose-400"
                    elif "WARN" in line.upper():
                        log_class = "text-amber-400"
                    elif "INFO" in line.upper():
                        log_class = "text-emerald-400"
                    elif "DEBUG" in line.upper():
                        log_class = "text-slate-500"
                    
                    logs.append({
                        "line": line,
                        "class": log_class
                    })
        else:
            # Si no existe el archivo, crear uno vacío
            os.makedirs(LOG_DIR, exist_ok=True)
            with open(log_file, 'w') as f:
                f.write(f"[{datetime.utcnow().isoformat()}] INFO: Log file initialized\n")
            logs.append({
                "line": f"[{datetime.utcnow().isoformat()}] INFO: Log file initialized",
                "class": "text-emerald-400"
            })
        
        return {
            "logs": logs,
            "total": len(logs),
            "file": "provisioning.log"
        }
    except Exception as e:
        logger.error(f"Error leyendo logs: {e}")
        return {"logs": [], "total": 0, "error": str(e)}


@router.get("/app")
async def get_app_logs(
    request: Request,
    access_token: str = Cookie(None),
    lines: int = Query(100, ge=10, le=500),
    level: Optional[str] = None
) -> Dict[str, Any]:
    """Obtiene logs de la aplicación FastAPI"""
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
    try:
        log_file = os.path.join(LOG_DIR, "app.log")
        logs = []
        
        if os.path.exists(log_file):
            result = subprocess.run(
                ["tail", "-n", str(lines), log_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    if level and level.upper() not in line.upper():
                        continue
                    
                    log_class = "text-slate-400"
                    if "ERROR" in line.upper():
                        log_class = "text-rose-400"
                    elif "WARN" in line.upper():
                        log_class = "text-amber-400"
                    elif "INFO" in line.upper():
                        log_class = "text-emerald-400"
                    
                    logs.append({"line": line, "class": log_class})
        
        return {"logs": logs, "total": len(logs), "file": "app.log"}
    except Exception as e:
        return {"logs": [], "total": 0, "error": str(e)}


@router.get("/system")
async def get_system_logs(
    request: Request,
    access_token: str = Cookie(None),
    lines: int = Query(50, ge=10, le=200)
) -> Dict[str, Any]:
    """Obtiene logs del sistema (journalctl)"""
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
    try:
        # Intentar obtener logs de journalctl para el servicio
        result = subprocess.run(
            ["journalctl", "-u", "erp_core", "-n", str(lines), "--no-pager", "--output=short-iso"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        logs = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                log_class = "text-slate-400"
                if "error" in line.lower():
                    log_class = "text-rose-400"
                elif "warn" in line.lower():
                    log_class = "text-amber-400"
                logs.append({"line": line, "class": log_class})
        
        return {"logs": logs, "total": len(logs), "source": "journalctl"}
    except Exception as e:
        return {"logs": [], "total": 0, "error": str(e)}


@router.get("/status")
async def get_system_status(
    request: Request,
    access_token: str = Cookie(None)
) -> Dict[str, Any]:
    """
    Obtiene estado de los servicios del sistema.
    
    Retorna estado de:
    - PostgreSQL
    - FastAPI
    - LXC Containers
    - Disco
    """
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
    status = {
        "postgresql": {"status": "unknown", "latency_ms": None},
        "fastapi": {"status": "running", "port": 4443},
        "lxc_105": {"status": "unknown", "name": "sajet.us Container"},
        "disk": {"usage_percent": 0, "free_gb": 0}
    }
    
    # Verificar PostgreSQL
    try:
        import time
        from ..models.database import SessionLocal
        start = time.time()
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        latency = int((time.time() - start) * 1000)
        status["postgresql"] = {"status": "healthy", "latency_ms": latency}
    except Exception as e:
        status["postgresql"] = {"status": "error", "error": str(e)}
    
    # Verificar LXC 105
    try:
        result = subprocess.run(
            ["pct", "status", "105"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "running" in result.stdout.lower():
            status["lxc_105"]["status"] = "active"
        else:
            status["lxc_105"]["status"] = "stopped"
    except:
        status["lxc_105"]["status"] = "unknown"
    
    # Verificar uso de disco
    try:
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            parts = lines[1].split()
            usage_str = parts[4].replace('%', '')
            status["disk"]["usage_percent"] = int(usage_str)
            
            # Parsear espacio libre (formato: "50G")
            free_str = parts[3]
            if 'G' in free_str:
                status["disk"]["free_gb"] = float(free_str.replace('G', ''))
            elif 'T' in free_str:
                status["disk"]["free_gb"] = float(free_str.replace('T', '')) * 1024
    except:
        pass
    
    return status


@router.post("/write")
async def write_log(
    request: Request,
    access_token: str = Cookie(None),
    message: str = "",
    level: str = "INFO",
    source: str = "api"
) -> Dict[str, Any]:
    """
    Escribe un mensaje en el log de provisioning.
    Útil para debugging y tracking de operaciones.
    """
    token = access_token
    if token is None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if token:
        _verify_admin(token)
    
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, "provisioning.log")
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {level.upper()} [{source}]: {message}\n"
        
        with open(log_file, 'a') as f:
            f.write(log_line)
        
        return {"success": True, "logged": log_line.strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}
