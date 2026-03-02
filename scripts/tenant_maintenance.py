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
    python3 tenant_maintenance.py                         # Modo check (solo reporta)
    python3 tenant_maintenance.py --repair                # Modo repair (repara filestore)
    python3 tenant_maintenance.py --tenant sattra         # Solo un tenant específico
    python3 tenant_maintenance.py --clear-assets          # Limpia assets JS/CSS (regenerables)
    python3 tenant_maintenance.py --clear-assets --tenant techeels  # Assets de un tenant

⚠️  ADVERTENCIA CRÍTICA — LIMPIEZA DE ASSETS:
═══════════════════════════════════════════════════════════════════════════════
Al limpiar assets de Odoo (bundles JS/CSS en ir_attachment), Odoo los regenera
automáticamente al recargar la página. Sin embargo, NO se deben borrar:

  - Attachments con store_fname IS NOT NULL  → Son archivos FÍSICOS en filestore
    (imágenes de productos, logos, documentos PDF, fotos de empleados, etc.)
    Si se borran de la BD pero NO del disco, se pierden referencias y las fotos
    desaparecen del frontend aunque el archivo físico siga en disco.

  - Attachments con mimetype LIKE 'image/%'  → Imágenes subidas por usuarios
  - Attachments de type='binary' con res_model != ''  → Datos vinculados a registros

La función clear_tenant_assets() SOLO borra:
    WHERE url LIKE '/web/assets/%'                        ← Bundles CSS/JS compilados
    AND mimetype IN ('text/css','application/javascript') ← Solo JS y CSS
    AND (res_id IS NULL OR res_id = 0)                   ← Sin ID de registro real

    ⚠️  Estructura real Odoo 17 (verificada 2026-03-02):
    - Bundles: res_model='ir.ui.view', res_id=0  → SE BORRAN (regenerables)
    - Imágenes: res_model='product.template', res_id=42 → NUNCA SE BORRAN
    El mimetype es el discriminador definitivo: JS/CSS = bundle, image/* = foto

Esto es 100% seguro: Odoo los regenera en el próximo request.

Si después de limpiar assets faltan FOTOS:
    → Ejecutar: python3 tenant_maintenance.py --repair --tenant <nombre>
    → Esto copia archivos faltantes desde template_tenant al filestore

═══════════════════════════════════════════════════════════════════════════════
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


def clear_tenant_assets(tenant: str, dry_run: bool = False) -> dict:
    """
    Limpia SOLO los bundles de assets JS/CSS de Odoo para un tenant.

    ¿Qué borra?
        ir_attachment WHERE url LIKE '/web/assets/%'
        AND mimetype IN ('text/css', 'application/javascript')
        AND (res_id IS NULL OR res_id = 0)

    ¿Por qué es seguro?
        - Los bundles en Odoo 17 tienen: res_model='ir.ui.view', res_id=0
          y mimetype='text/css' o 'application/javascript'.
        - Las imágenes tienen res_id > 0 (ID real del producto/empleado/etc.)
          y mimetype='image/png', 'image/jpeg', etc. → NUNCA se tocan.
        - Odoo regenera los bundles automáticamente en el próximo request.

    ¿Cuándo usar esto?
        - Después de actualizar módulos de Odoo (web_editor, website, etc.)
        - Cuando el editor web lanza errores JS del tipo:
            "Cannot read properties of undefined (reading 'styles')"
            "UncaughtPromiseError > TypeError"
        - Cuando aparecen estilos/scripts cacheados incorrectamente

    ⚠️  DESPUÉS de limpiar assets, si faltan fotos ejecutar:
        python3 tenant_maintenance.py --repair --tenant <nombre>

    Args:
        tenant: Nombre de la base de datos del tenant
        dry_run: Si True, solo muestra qué borraría sin borrar nada
    """
    logger.info(f"{'[DRY-RUN] ' if dry_run else ''}🧹 Limpiando assets de '{tenant}'...")

    # Query seguro: SOLO bundles web compilados (url /web/assets/)
    # ⚠️  Estructura real en Odoo 17:
    #   - Bundles: url='/web/assets/...', res_model='ir.ui.view', res_id=0
    #             mimetype='text/css' o 'application/javascript'
    #   - Imágenes: url diferente, res_model='product.template' etc, res_id>0
    # El discriminador seguro es: url + mimetype JS/CSS + res_id=0
    safe_delete_sql = """
        SELECT count(*) as total
        FROM ir_attachment
        WHERE url LIKE '/web/assets/%'
          AND mimetype IN ('text/css', 'application/javascript')
          AND (res_id IS NULL OR res_id = 0);
    """

    # Primero contar qué se borraría
    count_cmd = (
        f"PGPASSWORD='{ODOO_DB_PASSWORD}' psql -h {ODOO_DB_HOST} -p {ODOO_DB_PORT} "
        f"-U {ODOO_DB_USER} -d {tenant} -At -c \"{safe_delete_sql.strip()}\""
    )
    ok, output = _run_pct_shell(ODOO_FILESTORE_PCT_ID, count_cmd, timeout=30)

    if not ok:
        return {"tenant": tenant, "success": False, "error": output}

    count = int(output.strip()) if output.strip().isdigit() else 0
    logger.info(f"   → {count} bundles CSS/JS a eliminar (regenerables por Odoo)")

    if dry_run:
        return {"tenant": tenant, "success": True, "deleted": 0, "would_delete": count}

    if count == 0:
        logger.info(f"   ✓ Sin assets que limpiar en '{tenant}'")
        return {"tenant": tenant, "success": True, "deleted": 0}

    # Borrado real — SOLO bundles CSS/JS sin ID de registro asociado
    delete_sql = """
        DELETE FROM ir_attachment
        WHERE url LIKE '/web/assets/%'
          AND mimetype IN ('text/css', 'application/javascript')
          AND (res_id IS NULL OR res_id = 0);
    """
    delete_cmd = (
        f"PGPASSWORD='{ODOO_DB_PASSWORD}' psql -h {ODOO_DB_HOST} -p {ODOO_DB_PORT} "
        f"-U {ODOO_DB_USER} -d {tenant} -c \"{delete_sql.strip()}\""
    )
    ok, output = _run_pct_shell(ODOO_FILESTORE_PCT_ID, delete_cmd, timeout=60)

    if not ok:
        return {"tenant": tenant, "success": False, "error": output}

    logger.info(f"   ✅ {count} assets eliminados. Odoo los regenerará en el próximo request.")
    logger.info(f"   ℹ️  Si faltan fotos: ejecuta --repair --tenant {tenant}")

    return {"tenant": tenant, "success": True, "deleted": count}


def main():
    parser = argparse.ArgumentParser(
        description="Mantenimiento de Tenants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  Verificar todos los tenants:
    python3 tenant_maintenance.py

  Reparar filestore (fotos faltantes):
    python3 tenant_maintenance.py --repair

  Limpiar assets JS/CSS (fix errores editor web):
    python3 tenant_maintenance.py --clear-assets

  Limpiar assets de un tenant específico:
    python3 tenant_maintenance.py --clear-assets --tenant techeels

  Ver qué se borraría sin borrar nada:
    python3 tenant_maintenance.py --clear-assets --dry-run
        """
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Ejecutar reparación de filestore (por defecto solo reporta)"
    )
    parser.add_argument(
        "--clear-assets",
        action="store_true",
        help="Limpiar bundles CSS/JS de Odoo (seguros, se regeneran). "
             "NUNCA borra imágenes ni archivos físicos del filestore."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Con --clear-assets: muestra qué se borraría sin borrar nada"
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
    logger.info(f"Modo: {'REPARACIÓN FILESTORE' if args.repair else 'VERIFICACIÓN'}")
    if args.clear_assets:
        logger.info(f"Modo adicional: LIMPIEZA DE ASSETS {'(DRY-RUN)' if args.dry_run else ''}")
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

    # ─── BLOQUE: LIMPIEZA DE ASSETS ─────────────────────────────────────────
    # Se ejecuta ANTES del check de filestore para que si algo falla después
    # de limpiar assets, --repair pueda recuperar el filestore correctamente.
    #
    # FLUJO RECOMENDADO cuando el editor web da errores JS:
    #   1. python3 tenant_maintenance.py --clear-assets [--tenant X]
    #      → Limpia bundles CSS/JS corruptos/viejos (Odoo los regenera solo)
    #   2. Si desaparecen fotos tras el paso 1:
    #      python3 tenant_maintenance.py --repair [--tenant X]
    #      → Restaura archivos del filestore desde template_tenant
    # ────────────────────────────────────────────────────────────────────────
    if args.clear_assets:
        logger.info("🧹 LIMPIEZA DE ASSETS (CSS/JS bundles)")
        logger.info("   Solo se eliminan bundles regenerables. Las fotos NO se tocan.")
        logger.info("-" * 70)
        asset_results = []
        for tenant in tenants:
            result = clear_tenant_assets(tenant, dry_run=args.dry_run)
            asset_results.append(result)

        cleared = sum(r.get("deleted", 0) for r in asset_results if r["success"])
        failed = [r["tenant"] for r in asset_results if not r["success"]]
        logger.info("-" * 70)
        logger.info(f"✅ Assets eliminados: {cleared} bundles en {len(tenants)} tenant(s)")
        if failed:
            logger.error(f"❌ Falló en: {', '.join(failed)}")
        if not args.dry_run:
            logger.info("ℹ️  Recarga el navegador en Odoo para regenerar los assets.")
            logger.info("ℹ️  Si faltan fotos: python3 tenant_maintenance.py --repair")
        logger.info("=" * 70)

        # Si solo se pidió clear-assets (sin --repair ni check), terminar aquí
        if not args.repair:
            return 0 if not failed else 1
        logger.info("")
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
