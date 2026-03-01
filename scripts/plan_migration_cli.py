#!/usr/bin/env python3
"""
Script CLI para evaluación y migración de planes
=================================================

Herramienta de línea de comandos para administradores.

Uso:
    # Evaluar un tenant específico
    python3 plan_migration_cli.py evaluate --tenant sattra
    
    # Evaluar todos los tenants
    python3 plan_migration_cli.py evaluate-all
    
    # Ver resumen ejecutivo
    python3 plan_migration_cli.py summary
    
    # Simular migración de un tenant
    python3 plan_migration_cli.py migrate --tenant sattra --dry-run
    
    # Ejecutar migración real
    python3 plan_migration_cli.py migrate --tenant sattra
    
    # Migración batch de todos los que lo requieran
    python3 plan_migration_cli.py migrate-all --dry-run
    python3 plan_migration_cli.py migrate-all  # REAL (con confirmación)
    
    # Ver tamaño de un tenant
    python3 plan_migration_cli.py size --tenant sattra
    
    # Listar planes disponibles
    python3 plan_migration_cli.py plans
"""

import argparse
import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment before imports
os.environ.setdefault("ERP_ENV", "production")

from app.models.database import SessionLocal
from app.services.plan_migration_service import PlanMigrationService
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def format_size(size_mb: float) -> str:
    """Formatea tamaño en MB a formato legible"""
    if size_mb >= 1024:
        return f"{size_mb/1024:.2f} GB"
    return f"{size_mb:.0f} MB"


def print_evaluation(result: dict):
    """Imprime resultado de evaluación formateado"""
    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        return
    
    status_icons = {
        "ok": "✅",
        "warning": "🟡",
        "critical": "🔴",
        "exceeded": "⚠️",
    }
    
    icon = status_icons.get(result["status"], "ℹ️")
    
    print("\n" + "=" * 70)
    print(f"{icon} {result['company_name']} ({result['subdomain']})")
    print("=" * 70)
    print(f"Plan Actual: {result['plan_display']}")
    print(f"Límite Storage: {format_size(result['plan_storage_limit_mb']) if not result['storage_unlimited'] else '∞ Ilimitado'}")
    print(f"\nUso Actual:")
    print(f"  • Base de Datos: {format_size(result['current_usage']['db_size_mb'])}")
    print(f"  • Filestore: {format_size(result['current_usage']['filestore_size_mb'])}")
    print(f"  • TOTAL: {format_size(result['current_usage']['total_size_mb'])}")
    print(f"\nEstado: {result['status'].upper()} ({result['usage_percent']:.1f}% del límite)")
    print(f"Mensaje: {result['message']}")
    
    if result.get("recommendation"):
        rec = result["recommendation"]
        print(f"\n💡 RECOMENDACIÓN:")
        print(f"  Plan sugerido: {rec['plan_display']}")
        print(f"  Límite: {format_size(rec['storage_limit_mb']) if rec['storage_limit_mb'] > 0 else '∞ Ilimitado'}")
        print(f"  Precio base: ${rec['base_price']:.2f}/mes")
        print(f"  Debe migrar: {'SÍ' if result['should_migrate'] else 'NO'}")
    
    print("=" * 70)


def cmd_evaluate(args):
    """Evaluar un tenant específico"""
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        result = service.evaluate_tenant(args.tenant)
        print_evaluation(result)
        
        return 0 if "error" not in result else 1
    finally:
        db.close()


def cmd_evaluate_all(args):
    """Evaluar todos los tenants"""
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        results = service.evaluate_all_tenants()
        
        print(f"\n📊 EVALUACIÓN DE {len(results)} TENANTS\n")
        
        for result in results:
            if "error" not in result:
                icon = {"ok": "✅", "warning": "🟡", "critical": "🔴", "exceeded": "⚠️"}.get(result["status"], "ℹ️")
                print(
                    f"{icon} {result['company_name']:30s} | "
                    f"{result['status']:10s} | "
                    f"{result['usage_percent']:6.1f}% | "
                    f"{format_size(result['current_usage']['total_size_mb']):12s}"
                )
        
        return 0
    finally:
        db.close()


def cmd_summary(args):
    """Ver resumen ejecutivo"""
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        summary = service.get_migration_summary()
        
        print("\n" + "=" * 70)
        print("📊 RESUMEN EJECUTIVO DE PLANES")
        print("=" * 70)
        print(f"Total Tenants: {summary['total_tenants']}")
        print(f"  ✅ OK: {summary['ok']}")
        print(f"  🟡 Warning: {summary['warning']}")
        print(f"  🔴 Critical: {summary['critical']}")
        print(f"  ⚠️  Exceeded: {summary['exceeded']}")
        print(f"  💡 Requieren migración: {summary['migration_recommended']}")
        print("=" * 70)
        
        # Detalles por estado
        for status in ["exceeded", "critical", "warning"]:
            tenants = summary["tenants_by_status"][status]
            if tenants:
                print(f"\n{status.upper()}:")
                for t in tenants:
                    print(f"  • {t['company_name']} ({t['subdomain']}) - {t['usage_percent']:.1f}%")
                    if t.get("recommendation"):
                        print(f"    → Recomendar: {t['recommendation']['plan_display']}")
        
        return 0
    finally:
        db.close()


def cmd_migrate(args):
    """Migrar un tenant específico"""
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        
        if not args.dry_run:
            confirm = input(f"⚠️  ¿Confirmar migración REAL de '{args.tenant}'? (yes/no): ")
            if confirm.lower() != "yes":
                print("❌ Migración cancelada")
                return 1
        
        result = service.auto_migrate_tenant(
            tenant_db=args.tenant,
            dry_run=args.dry_run
        )
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return 1
        
        print_evaluation(result)
        
        if result.get("migration_executed"):
            print(f"\n✅ MIGRACIÓN EJECUTADA:")
            print(f"  • {result['old_plan']} → {result['new_plan']}")
            print(f"  • Razón: {result['migration_reason']}")
        elif args.dry_run:
            print(f"\n💡 DRY RUN - No se ejecutó la migración")
            if result.get("would_migrate_to"):
                print(f"  • Se migraría a: {result['would_migrate_to']['plan_display']}")
        else:
            print(f"\n✅ No se requiere migración")
        
        return 0
    finally:
        db.close()


def cmd_migrate_all(args):
    """Migrar todos los tenants que lo requieran"""
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        evaluations = service.evaluate_all_tenants()
        
        to_migrate = [e for e in evaluations if e.get("should_migrate") and "error" not in e]
        
        if not to_migrate:
            print("✅ No hay tenants que requieran migración")
            return 0
        
        print(f"\n⚠️  Se identificaron {len(to_migrate)} tenants que requieren migración:")
        for e in to_migrate:
            print(f"  • {e['company_name']} ({e['subdomain']}) - {e['usage_percent']:.1f}%")
        
        if not args.dry_run:
            confirm = input(f"\n⚠️  ¿Confirmar migración REAL de {len(to_migrate)} tenants? (yes/no): ")
            if confirm.lower() != "yes":
                print("❌ Migración cancelada")
                return 1
        
        migrated = 0
        for e in to_migrate:
            result = service.auto_migrate_tenant(
                tenant_db=e["tenant_db"],
                customer_id=e["customer_id"],
                dry_run=args.dry_run
            )
            
            if result.get("migration_executed"):
                migrated += 1
                print(f"✅ {e['company_name']}: {result['old_plan']} → {result['new_plan']}")
        
        if args.dry_run:
            print(f"\n💡 DRY RUN - Se migrarían {len(to_migrate)} tenants")
        else:
            print(f"\n✅ Migraciones completadas: {migrated}/{len(to_migrate)}")
        
        return 0
    finally:
        db.close()


def cmd_size(args):
    """Ver tamaño de un tenant"""
    db = SessionLocal()
    try:
        service = PlanMigrationService(db)
        size_info = service.get_tenant_database_size(args.tenant)
        
        print("\n" + "=" * 70)
        print(f"📊 TAMAÑO DE '{args.tenant}'")
        print("=" * 70)
        print(f"Base de Datos: {format_size(size_info['db_size_mb'])}")
        print(f"Filestore: {format_size(size_info['filestore_size_mb'])}")
        print(f"TOTAL: {format_size(size_info['total_size_mb'])}")
        print(f"Medido: {size_info['measured_at']}")
        print("=" * 70)
        
        return 0
    finally:
        db.close()


def cmd_plans(args):
    """Listar planes disponibles"""
    db = SessionLocal()
    try:
        from app.models.database import Plan
        
        plans = db.query(Plan).filter(
            Plan.is_active == True
        ).order_by(Plan.max_storage_mb.asc()).all()
        
        print("\n" + "=" * 90)
        print("📋 PLANES DISPONIBLES")
        print("=" * 90)
        print(f"{'Plan':<15} {'Nombre':<25} {'Storage':<15} {'Base':<10} {'Por Usuario'}")
        print("-" * 90)
        
        for plan in plans:
            storage = format_size(plan.max_storage_mb) if plan.max_storage_mb > 0 else "∞ Ilimitado"
            print(
                f"{plan.name:<15} {plan.display_name:<25} {storage:<15} "
                f"${plan.base_price:>7.2f}  ${plan.price_per_user:>7.2f}"
            )
        
        print("=" * 90)
        
        return 0
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="CLI para evaluación y migración de planes"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Evaluar un tenant")
    p_eval.add_argument("--tenant", required=True, help="Nombre del tenant (subdomain)")
    
    # evaluate-all
    subparsers.add_parser("evaluate-all", help="Evaluar todos los tenants")
    
    # summary
    subparsers.add_parser("summary", help="Resumen ejecutivo")
    
    # migrate
    p_migrate = subparsers.add_parser("migrate", help="Migrar un tenant")
    p_migrate.add_argument("--tenant", required=True, help="Nombre del tenant")
    p_migrate.add_argument("--dry-run", action="store_true", help="Solo simular")
    
    # migrate-all
    p_migrate_all = subparsers.add_parser("migrate-all", help="Migrar todos los que lo requieran")
    p_migrate_all.add_argument("--dry-run", action="store_true", help="Solo simular")
    
    # size
    p_size = subparsers.add_parser("size", help="Ver tamaño de un tenant")
    p_size.add_argument("--tenant", required=True, help="Nombre del tenant")
    
    # plans
    subparsers.add_parser("plans", help="Listar planes disponibles")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        "evaluate": cmd_evaluate,
        "evaluate-all": cmd_evaluate_all,
        "summary": cmd_summary,
        "migrate": cmd_migrate,
        "migrate-all": cmd_migrate_all,
        "size": cmd_size,
        "plans": cmd_plans,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
