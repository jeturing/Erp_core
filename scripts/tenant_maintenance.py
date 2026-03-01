#!/usr/bin/env python3
"""
Script de Mantenimiento de Tenants
====================================

Ejecuta mantenimiento sobre todos los tenants existentes:
1. Verifica integridad del filestore
2. Repara archivos faltantes desde template_tenant
3. Corrige permisos
4. Reporta estadísticas

Uso:
    python3 tenant_maintenance.py                  # Modo check (solo reporta)
    python3 tenant_maintenance.py --repair         # Modo repair (repara todo)
    python3 tenant_maintenance.py --tenant sattra  # Solo un tenant específico
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment before imports
os.environ.setdefault("ERP_ENV", "production")

from app.config import (
    ODOO_DB_HOST,
    ODOO_DB_PORT,
    ODOO_DB_USER,
    ODOO_DB_PASSWORD,
    ODOO_FILESTORE_PATH,
    ODOO_FILESTORE_PCT_ID,
    ODOO_TEMPLATE_DB,
)
from app.services.odoo_database_manager import _run_pct_shell
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_tenant_list() -> list[str]:
    """Lista todos los tenants desde el filestore"""
    cmd = f"ls -1 {ODOO_FILESTORE_PATH}"
    ok, output = _run_pct_shell(ODOO_FILESTORE_PCT_ID, cmd)
    
    if not ok:
        logger.error(f"No se pudo listar filestore: {output}")
        return []
    
    tenants = [t.strip() for t in output.split("\n") if t.strip()]
    # Excluir template
    tenants = [t for t in tenants if t != ODOO_TEMPLATE_DB]
    return tenants


def check_tenant_filestore(tenant: str) -> dict:
    """Verifica el estado del filestore de un tenant"""
    cmd = (
        f"set -e; "
        f"test -d {ODOO_FILESTORE_PATH}/{tenant} && "
        f"file_count=$(find {ODOO_FILESTORE_PATH}/{tenant} -type f 2>/dev/null | wc -l); "
        f"size=$(du -sh {ODOO_FILESTORE_PATH}/{tenant} 2>/dev/null | cut -f1); "
        f"echo \"files=$file_count|size=$size\""
    )
    
    ok, output = _run_pct_shell(ODOO_FILESTORE_PCT_ID, cmd, timeout=30)
    
    if not ok:
        return {"tenant": tenant, "status": "error", "error": output}
    
    # Parse output
    data = {}
    for part in output.split("|"):
        if "=" in part:
            key, value = part.strip().split("=", 1)
            data[key] = value
    
    return {
        "tenant": tenant,
        "status": "ok",
        "files": int(data.get("files", 0)),
        "size": data.get("size", "0"),
    }


def repair_tenant_filestore(tenant: str) -> dict:
    """Repara el filestore de un tenant"""
    logger.info(f"🔧 Reparando filestore de '{tenant}'...")
    
    cmd = (
        f"set -e; "
        f"test -d {ODOO_FILESTORE_PATH}/{ODOO_TEMPLATE_DB}; "
        f"mkdir -p {ODOO_FILESTORE_PATH}/{tenant}; "
        f"cp -an {ODOO_FILESTORE_PATH}/{ODOO_TEMPLATE_DB}/. {ODOO_FILESTORE_PATH}/{tenant}/; "
        f"chown -R odoo:odoo {ODOO_FILESTORE_PATH}/{tenant}; "
        f"echo repaired_files=$(find {ODOO_FILESTORE_PATH}/{tenant} -type f | wc -l)"
    )
    
    ok, output = _run_pct_shell(ODOO_FILESTORE_PCT_ID, cmd, timeout=90)
    
    if not ok:
        return {"tenant": tenant, "success": False, "error": output}
    
    # Parse file count
    file_count = 0
    if "repaired_files=" in output:
        file_count = int(output.split("repaired_files=")[-1].strip())
    
    logger.info(f"✅ Reparado: {tenant} ({file_count} archivos)")
    
    return {
        "tenant": tenant,
        "success": True,
        "files": file_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Mantenimiento de Tenants")
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Ejecutar reparación (por defecto solo reporta)"
    )
    parser.add_argument(
        "--tenant",
        type=str,
        help="Procesar solo un tenant específico"
    )
    parser.add_argument(
        "--min-files",
        type=int,
        default=400,
        help="Mínimo de archivos esperados (default: 400)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("MANTENIMIENTO DE TENANTS")
    logger.info("=" * 70)
    logger.info(f"Modo: {'REPARACIÓN' if args.repair else 'VERIFICACIÓN'}")
    logger.info(f"Filestore PCT: {ODOO_FILESTORE_PCT_ID}")
    logger.info(f"Path: {ODOO_FILESTORE_PATH}")
    logger.info(f"Template: {ODOO_TEMPLATE_DB}")
    logger.info("=" * 70)
    
    # Get tenant list
    if args.tenant:
        tenants = [args.tenant]
    else:
        tenants = get_tenant_list()
    
    if not tenants:
        logger.error("❌ No se encontraron tenants")
        return 1
    
    logger.info(f"📊 Tenants a procesar: {len(tenants)}\n")
    
    # Process each tenant
    issues = []
    repaired = []
    
    for tenant in tenants:
        # Check status
        status = check_tenant_filestore(tenant)
        
        if status["status"] == "error":
            logger.error(f"❌ {tenant}: ERROR - {status.get('error', 'unknown')}")
            issues.append(status)
            continue
        
        files = status["files"]
        size = status["size"]
        
        if files < args.min_files:
            logger.warning(f"⚠️  {tenant}: {files} archivos (esperados ≥{args.min_files}) | {size}")
            issues.append(status)
            
            # Repair if requested
            if args.repair:
                result = repair_tenant_filestore(tenant)
                if result["success"]:
                    repaired.append(result)
        else:
            logger.info(f"✅ {tenant}: {files} archivos | {size}")
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("RESUMEN")
    logger.info("=" * 70)
    logger.info(f"Total tenants: {len(tenants)}")
    logger.info(f"Tenants OK: {len(tenants) - len(issues)}")
    logger.info(f"Tenants con problemas: {len(issues)}")
    
    if args.repair:
        logger.info(f"Tenants reparados: {len(repaired)}")
    
    if issues and not args.repair:
        logger.info("\n💡 Ejecuta con --repair para reparar automáticamente")
    
    logger.info("=" * 70)
    
    return 0 if not issues or args.repair else 1


if __name__ == "__main__":
    sys.exit(main())
