#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path("/opt/Erp_core")
os.chdir(PROJECT_ROOT)
os.environ.setdefault("ERP_ENV", "production")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.config as cfg  # noqa: F401
from sqlalchemy import text

from app.models.database import Customer, CustomDomain, ProxmoxNode, SessionLocal, Subscription, TenantDeployment
from app.services.deployment_writer import ensure_tenant_deployment

SYSTEM_DBS = {"erp_core_db", "postgres", "template_tenant"}
DEDICATED_MEMORY_PATH = Path("/opt/memory/context/sajet-dedicated-tenants.md")


def deployment_timestamp_iso(deployment: TenantDeployment) -> str | None:
    for attr in ("last_healthcheck_at", "last_accessed", "deployed_at"):
        value = getattr(deployment, attr, None)
        if value:
            return value.isoformat()
    return None


def build_catalog(search: str = "") -> list[dict]:
    db = SessionLocal()
    try:
        db_names = {
            row[0]
            for row in db.execute(
                text("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname")
            ).fetchall()
        }

        customers = {c.subdomain: c for c in db.query(Customer).all() if c.subdomain}
        deployments = {d.subdomain: d for d in db.query(TenantDeployment).all() if d.subdomain}
        nodes = {n.id: n for n in db.query(ProxmoxNode).all()}

        subscription_by_customer: dict[int, Subscription] = {}
        for sub in (
            db.query(Subscription)
            .order_by(Subscription.customer_id.asc(), Subscription.created_at.desc())
            .all()
        ):
            if sub.customer_id and sub.customer_id not in subscription_by_customer:
                subscription_by_customer[sub.customer_id] = sub

        keys = sorted(set(db_names) | set(customers) | set(deployments))
        entries = []
        search_l = search.strip().lower()
        for key in keys:
            customer = customers.get(key)
            deployment = deployments.get(key)
            subscription = subscription_by_customer.get(customer.id) if customer else None
            node = nodes.get(deployment.active_node_id) if deployment and deployment.active_node_id else None
            vmid = node.vmid if node and node.vmid else None

            record = {
                "subdomain": key,
                "company_name": customer.company_name if customer else None,
                "db_present": key in db_names,
                "customer_exists": bool(customer),
                "customer_id": customer.id if customer else None,
                "subscription_exists": bool(subscription),
                "subscription_id": subscription.id if subscription else None,
                "subscription_status": subscription.status.value if subscription and subscription.status else None,
                "plan_name": getattr(subscription, "plan_name", None) if subscription else None,
                "deployment_exists": bool(deployment),
                "deployment_id": deployment.id if deployment else None,
                "runtime_mode": deployment.runtime_mode.value if deployment and deployment.runtime_mode else None,
                "migration_state": deployment.migration_state.value if deployment and deployment.migration_state else None,
                "active_node_id": deployment.active_node_id if deployment else None,
                "active_vmid": vmid,
                "protected": key in {"root"},
                "system_db": key in SYSTEM_DBS,
            }
            haystack = " ".join(
                str(v or "")
                for v in (
                    record["subdomain"],
                    record["company_name"],
                    record["plan_name"],
                    record["subscription_status"],
                    record["runtime_mode"],
                    record["active_vmid"],
                )
            ).lower()
            if search_l and search_l not in haystack:
                continue
            entries.append(record)
        return entries
    finally:
        db.close()


def get_deployment_snapshot(tenant: str) -> dict | None:
    db = SessionLocal()
    try:
        deployment = db.query(TenantDeployment).filter(TenantDeployment.subdomain == tenant).first()
        if not deployment:
            return None

        customer = db.query(Customer).filter(Customer.id == deployment.customer_id).first() if deployment.customer_id else None
        node = db.query(ProxmoxNode).filter(ProxmoxNode.id == deployment.active_node_id).first() if deployment.active_node_id else None
        return {
            "subdomain": deployment.subdomain,
            "company_name": customer.company_name if customer else None,
            "customer_id": deployment.customer_id,
            "deployment_id": deployment.id,
            "runtime_mode": deployment.runtime_mode.value if deployment.runtime_mode else None,
            "routing_mode": deployment.routing_mode.value if deployment.routing_mode else None,
            "migration_state": deployment.migration_state.value if deployment.migration_state else None,
            "active_node_id": deployment.active_node_id,
            "active_vmid": node.vmid if node and node.vmid else None,
            "active_node_name": node.name if node else None,
            "backend_host": deployment.backend_host,
            "http_port": deployment.http_port,
            "chat_port": deployment.chat_port,
            "odoo_port": deployment.odoo_port,
            "service_name": deployment.service_name or (f"odoo-tenant@{deployment.subdomain}" if deployment.runtime_mode and deployment.runtime_mode.value == "dedicated_service" else None),
            "addons_overlay_path": deployment.addons_overlay_path,
            "updated_at": deployment_timestamp_iso(deployment),
        }
    finally:
        db.close()


def build_dedicated_catalog(search: str = "") -> list[dict]:
    db = SessionLocal()
    try:
        nodes = {n.id: n for n in db.query(ProxmoxNode).all()}
        customers = {c.id: c for c in db.query(Customer).all()}
        search_l = search.strip().lower()
        entries: list[dict] = []
        for dep in (
            db.query(TenantDeployment)
            .order_by(TenantDeployment.active_node_id.asc(), TenantDeployment.subdomain.asc())
            .all()
        ):
            runtime_mode = dep.runtime_mode.value if dep.runtime_mode else None
            if runtime_mode != "dedicated_service":
                continue
            node = nodes.get(dep.active_node_id)
            customer = customers.get(dep.customer_id) if dep.customer_id else None
            entry = {
                "subdomain": dep.subdomain,
                "company_name": customer.company_name if customer else None,
                "deployment_id": dep.id,
                "runtime_mode": runtime_mode,
                "routing_mode": dep.routing_mode.value if dep.routing_mode else None,
                "migration_state": dep.migration_state.value if dep.migration_state else None,
                "active_node_id": dep.active_node_id,
                "active_vmid": node.vmid if node and node.vmid else None,
                "active_node_name": node.name if node else None,
                "backend_host": dep.backend_host,
                "http_port": dep.http_port,
                "chat_port": dep.chat_port,
                "service_name": dep.service_name or f"odoo-tenant@{dep.subdomain}",
                "addons_overlay_path": dep.addons_overlay_path,
                "updated_at": deployment_timestamp_iso(dep),
            }
            haystack = " ".join(
                str(v or "")
                for v in (
                    entry["subdomain"],
                    entry["company_name"],
                    entry["active_vmid"],
                    entry["service_name"],
                    entry["http_port"],
                    entry["chat_port"],
                )
            ).lower()
            if search_l and search_l not in haystack:
                continue
            entries.append(entry)
        return entries
    finally:
        db.close()


def list_command(search: str) -> int:
    entries = build_catalog(search=search)
    for entry in entries:
        flags = []
        if entry["db_present"]:
            flags.append("db")
        if entry["customer_exists"]:
            flags.append("customer")
        if entry["subscription_exists"]:
            flags.append("sub")
        if entry["deployment_exists"]:
            flags.append("dep")
        if not entry["deployment_exists"] and entry["customer_exists"]:
            flags.append("orphan")
        if entry["system_db"]:
            flags.append("system")

        label = (
            f"{entry['company_name'] or entry['subdomain']} | "
            f"plan={entry['plan_name'] or '-'} | "
            f"node={entry['active_vmid'] or '-'} | "
            f"runtime={entry['runtime_mode'] or '-'} | "
            f"flags={','.join(flags) or '-'}"
        )
        print(f"{entry['subdomain']}\t{label}")
    return 0


def list_migratable_command(pct: int, search: str) -> int:
    entries = build_catalog(search=search)
    for entry in entries:
        if entry["system_db"] or entry["protected"] or not entry["db_present"]:
            continue

        current_vmid = entry["active_vmid"]
        runtime_mode = entry["runtime_mode"]
        deployment_exists = entry["deployment_exists"]

        already_on_target = current_vmid == pct and runtime_mode == "dedicated_service"
        if already_on_target:
            continue

        reason = "orphan"
        if deployment_exists and current_vmid == pct and runtime_mode != "dedicated_service":
            reason = "shared->dedicated"
        elif deployment_exists and current_vmid not in (None, pct):
            reason = f"node{current_vmid}->{pct}"
        elif deployment_exists and runtime_mode == "dedicated_service" and current_vmid != pct:
            reason = f"dedicated-node{current_vmid}->{pct}"

        label = (
            f"{entry['company_name'] or entry['subdomain']} | "
            f"plan={entry['plan_name'] or '-'} | "
            f"current={current_vmid or '-'} | "
            f"runtime={runtime_mode or '-'} | "
            f"{reason}"
        )
        print(f"{entry['subdomain']}\t{label}")
    return 0


def list_dedicated_command(search: str) -> int:
    entries = build_dedicated_catalog(search=search)
    for entry in entries:
        label = (
            f"{entry['company_name'] or entry['subdomain']} | "
            f"pct={entry['active_vmid'] or '-'} | "
            f"svc={entry['service_name'] or '-'} | "
            f"http={entry['http_port'] or '-'} | "
            f"chat={entry['chat_port'] or '-'}"
        )
        print(f"{entry['subdomain']}\t{label}")
    return 0


def status_command(tenant: str) -> int:
    matches = [e for e in build_catalog() if e["subdomain"] == tenant]
    if not matches:
      print(f"Tenant no encontrado: {tenant}")
      return 1
    print(json.dumps(matches[0], indent=2, sort_keys=True))
    return 0


def dedicated_status_command(tenant: str) -> int:
    snapshot = get_deployment_snapshot(tenant)
    if not snapshot:
        print(json.dumps({"tenant": tenant, "error": "deployment no encontrado"}, indent=2))
        return 1
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


def linked_domains_command(tenant: str) -> int:
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.subdomain == tenant).first()
        if not customer:
            print(json.dumps({"tenant": tenant, "error": "customer no encontrado"}, indent=2))
            return 1

        deployment = (
            db.query(TenantDeployment)
            .filter(TenantDeployment.customer_id == customer.id)
            .order_by(TenantDeployment.id.desc())
            .first()
        )
        domains = [
            {
                "external_domain": d.external_domain,
                "verification_status": d.verification_status.value if d.verification_status else None,
                "is_active": bool(d.is_active),
                "is_primary": bool(d.is_primary),
                "target_node_ip": d.target_node_ip,
                "target_port": d.target_port,
            }
            for d in db.query(CustomDomain).filter(CustomDomain.customer_id == customer.id).order_by(CustomDomain.id).all()
        ]

        print(
            json.dumps(
                {
                    "tenant": tenant,
                    "customer_id": customer.id,
                    "base_domain": f"{customer.subdomain}.sajet.us",
                    "deployment_id": deployment.id if deployment else None,
                    "domains": domains,
                },
                indent=2,
            )
        )
        return 0
    finally:
        db.close()


def ensure_deployment_command(tenant: str, pct: int) -> int:
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.subdomain == tenant).first()
        if not customer:
            print(f"Customer no encontrado para tenant={tenant}")
            return 1
        subscription = (
            db.query(Subscription)
            .filter(Subscription.customer_id == customer.id)
            .order_by(Subscription.created_at.desc())
            .first()
        )
        if not subscription:
            print(f"No hay subscription para tenant={tenant}")
            return 1

        result = ensure_tenant_deployment(
            subdomain=tenant,
            subscription_id=subscription.id,
            customer_id=customer.id,
            server_id=f"pct-{pct}",
            plan_name=getattr(subscription, "plan_name", None),
            db=db,
        )
        if not result.get("success"):
            print(result.get("error") or "ensure_tenant_deployment falló")
            return 1
        db.commit()
        print(json.dumps(result, indent=2))
        return 0
    finally:
        db.close()


def refresh_dedicated_memory_command(output_path: str | None = None) -> int:
    output = Path(output_path) if output_path else DEDICATED_MEMORY_PATH
    entries = build_dedicated_catalog()
    generated_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    lines = [
        "# Inventario de Tenants Dedicados SAJET",
        "",
        f"> Generado automáticamente: {generated_at}",
        "> Fuente de verdad: `tenant_deployments` + `proxmox_nodes` en la BDA canónica de SAJET.",
        "> Regla operativa: si `runtime_mode=dedicated_service`, cualquier mantenimiento/reinicio debe usar el servicio dedicado del tenant y no `odoo.service` del nodo.",
        "",
    ]

    if not entries:
        lines.extend([
            "## Estado",
            "",
            "No hay tenants en `dedicated_service`.",
            "",
        ])
    else:
        lines.extend([
            "## Tenants Migrados",
            "",
            "| Tenant | Empresa | PCT | Servicio | HTTP | Chat | Routing | Backend | Updated |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        for entry in entries:
            lines.append(
                "| {subdomain} | {company_name} | {pct} | `{service}` | `{http}` | `{chat}` | `{routing}` | `{backend}` | {updated} |".format(
                    subdomain=entry["subdomain"],
                    company_name=entry["company_name"] or "-",
                    pct=entry["active_vmid"] or "-",
                    service=entry["service_name"] or "-",
                    http=entry["http_port"] or "-",
                    chat=entry["chat_port"] or "-",
                    routing=entry["routing_mode"] or "-",
                    backend=entry["backend_host"] or "-",
                    updated=entry["updated_at"] or "-",
                )
            )
        lines.extend(["", "## Operación", ""])
        lines.extend([
            "- Listar dedicados: `JD -D` o `JD -> DEDICATED`.",
            "- Ver estado de un dedicado: `JD -DT <tenant>`.",
            "- Reiniciar solo el tenant dedicado: `JD -R <tenant>`.",
            "- Antes de reiniciar, verificar que `runtime_mode=dedicated_service`; si no, abortar para no tocar el servicio shared del nodo.",
            "",
        ])

    output.write_text("\n".join(lines), encoding="utf-8")
    print(str(output))
    return 0


def restart_dedicated_command(tenant: str, validate: bool = True) -> int:
    snapshot = get_deployment_snapshot(tenant)
    if not snapshot:
        print(f"Tenant sin deployment: {tenant}")
        return 1
    if snapshot["runtime_mode"] != "dedicated_service":
        print(
            f"ABORT: {tenant} no está en dedicated_service "
            f"(runtime_mode={snapshot['runtime_mode'] or 'n/a'}). "
            "No se reinicia para evitar tocar el servicio shared del nodo."
        )
        return 2

    pct = snapshot["active_vmid"]
    service_name = snapshot["service_name"]
    http_port = snapshot["http_port"]
    if not pct or not service_name:
        print(f"Deployment dedicado incompleto para {tenant}: pct={pct}, service={service_name}")
        return 1

    restart_cmd = [
        "pct",
        "exec",
        str(pct),
        "--",
        "systemctl",
        "restart",
        service_name,
    ]
    restart = subprocess.run(restart_cmd, capture_output=True, text=True)
    if restart.returncode != 0:
        print((restart.stderr or restart.stdout or "restart falló").strip())
        return restart.returncode

    status_cmd = [
        "pct",
        "exec",
        str(pct),
        "--",
        "systemctl",
        "is-active",
        service_name,
    ]
    status = subprocess.run(status_cmd, capture_output=True, text=True)
    if status.returncode != 0 or status.stdout.strip() != "active":
        print((status.stderr or status.stdout or "service no activo").strip())
        return status.returncode or 1

    print(f"restarted tenant={tenant} pct={pct} service={service_name}")
    if validate and http_port:
        curl_cmd = [
            "pct",
            "exec",
            str(pct),
            "--",
            "bash",
            "-lc",
            f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{http_port}/web/login",
        ]
        curl = subprocess.run(curl_cmd, capture_output=True, text=True)
        http_code = (curl.stdout or "").strip()
        if curl.returncode != 0 or http_code not in {"200", "303"}:
            print(
                f"warning: validación HTTP falló tenant={tenant} pct={pct} "
                f"service={service_name} http_port={http_port} code={http_code or 'n/a'}"
            )
            return curl.returncode or 1
        print(f"validated tenant={tenant} http_port={http_port} code={http_code}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--search", default="")

    p_status = sub.add_parser("status")
    p_status.add_argument("tenant")

    p_domains = sub.add_parser("linked-domains")
    p_domains.add_argument("tenant")

    p_ensure = sub.add_parser("ensure-deployment")
    p_ensure.add_argument("tenant")
    p_ensure.add_argument("--pct", required=True, type=int)

    p_migratable = sub.add_parser("list-migratable")
    p_migratable.add_argument("--pct", required=True, type=int)
    p_migratable.add_argument("--search", default="")

    p_list_dedicated = sub.add_parser("list-dedicated")
    p_list_dedicated.add_argument("--search", default="")

    p_dedicated_status = sub.add_parser("dedicated-status")
    p_dedicated_status.add_argument("tenant")

    p_refresh = sub.add_parser("refresh-dedicated-memory")
    p_refresh.add_argument("--output", default=str(DEDICATED_MEMORY_PATH))

    p_restart = sub.add_parser("restart-dedicated")
    p_restart.add_argument("tenant")
    p_restart.add_argument("--no-validate", action="store_true")

    args = parser.parse_args()
    if args.cmd == "list":
        return list_command(args.search)
    if args.cmd == "status":
        return status_command(args.tenant)
    if args.cmd == "linked-domains":
        return linked_domains_command(args.tenant)
    if args.cmd == "ensure-deployment":
        return ensure_deployment_command(args.tenant, args.pct)
    if args.cmd == "list-migratable":
        return list_migratable_command(args.pct, args.search)
    if args.cmd == "list-dedicated":
        return list_dedicated_command(args.search)
    if args.cmd == "dedicated-status":
        return dedicated_status_command(args.tenant)
    if args.cmd == "refresh-dedicated-memory":
        return refresh_dedicated_memory_command(args.output)
    if args.cmd == "restart-dedicated":
        return restart_dedicated_command(args.tenant, validate=not args.no_validate)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
