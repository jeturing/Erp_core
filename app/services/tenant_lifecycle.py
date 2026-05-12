"""
TenantLifecycleOrchestrator — Orquestador único para alta y baja de tenants.

Aplica el mismo flujo, sin importar si la solicitud viene del:
  - Admin SPA       (POST/DELETE /api/tenants)
  - Onboarding      (Stripe checkout completed → background task)
  - Customers API   (POST /api/customers con auto_provision=true)
  - Stripe webhook  (subscription canceled → deprovision)

Patrón saga: cada paso registra una compensación; ante fallo, se ejecutan
las compensaciones en orden inverso (best-effort) y se devuelve un
TenantOpResult con el detalle del fallo y de la compensación.

Pasos canónicos de ALTA:
  1. validate_spec
  2. resolve_target_node            (server_id / IP / puertos según capacity)
  3. upsert_customer_subscription   (idempotente)
  4. create_database                (SQL fast-path → HTTP fallback)
  5. write_deployment               (TenantDeployment con campos multi-nodo)
  6. configure_nginx                (en el nodo Odoo elegido)
  7. configure_cloudflared          (PCT 205: añadir route + restart)
  8. send_credentials               (opcional según source)
  9. audit

Pasos canónicos de BAJA:
  1. resolve_existing
  2. backup_database                (opcional)
  3. notify_email                   (con backup adjunto si aplica)
  4. delete_database                (Odoo)
  5. remove_nginx
  6. remove_cloudflared             (PCT 205: quitar route + restart)
  7. remove_dns                     (Cloudflare CNAME)
  8. delete_local_records           (customer + subscription + deployment)
  9. audit
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

LifecycleSource = Literal["admin", "onboarding", "customers_api", "stripe_webhook", "internal"]


@dataclass
class TenantSpec:
    """Solicitud de alta normalizada."""
    subdomain: str
    company_name: Optional[str] = None
    admin_email: Optional[str] = None
    admin_login: Optional[str] = None
    admin_password: Optional[str] = None
    plan_name: str = "basic"
    server_id: Optional[str] = None
    partner_id: Optional[int] = None
    country_code: Optional[str] = None
    blueprint_package_name: Optional[str] = None
    use_fast_method: bool = True
    customer_id: Optional[int] = None        # si ya existe en BD local
    subscription_id: Optional[int] = None    # si ya existe en BD local
    send_credentials_email: bool = False
    base_domain: str = "sajet.us"


@dataclass
class StepResult:
    name: str
    success: bool
    detail: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class TenantOpResult:
    success: bool
    subdomain: str
    operation: Literal["provision", "deprovision"]
    source: LifecycleSource
    steps: list[StepResult] = field(default_factory=list)
    compensations: list[StepResult] = field(default_factory=list)
    customer_id: Optional[int] = None
    subscription_id: Optional[int] = None
    deployment_id: Optional[int] = None
    admin_login: Optional[str] = None
    admin_password: Optional[str] = None
    backend_host: Optional[str] = None
    http_port: Optional[int] = None
    chat_port: Optional[int] = None
    error: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "subdomain": self.subdomain,
            "operation": self.operation,
            "source": self.source,
            "customer_id": self.customer_id,
            "subscription_id": self.subscription_id,
            "deployment_id": self.deployment_id,
            "admin_login": self.admin_login,
            "admin_password": self.admin_password,
            "backend_host": self.backend_host,
            "http_port": self.http_port,
            "chat_port": self.chat_port,
            "error": self.error,
            "steps": [
                {"name": s.name, "success": s.success, "detail": s.detail, "error": s.error}
                for s in self.steps
            ],
            "compensations": [
                {"name": c.name, "success": c.success, "detail": c.detail, "error": c.error}
                for c in self.compensations
            ],
        }


# ─── Saga runner ───────────────────────────────────────────────────

class _Saga:
    """Helper para registrar pasos + compensaciones."""

    def __init__(self, op_result: TenantOpResult):
        self.op_result = op_result
        self._compensations: list[tuple[str, Callable[[], Awaitable[StepResult] | StepResult]]] = []

    async def step(
        self,
        name: str,
        run: Callable[[], Awaitable[StepResult] | StepResult],
        *,
        compensate: Optional[Callable[[], Awaitable[StepResult] | StepResult]] = None,
        critical: bool = True,
    ) -> StepResult:
        try:
            result = run()
            if hasattr(result, "__await__"):
                result = await result  # type: ignore[assignment]
        except Exception as exc:
            logger.exception("[saga:%s] step '%s' raised", self.op_result.subdomain, name)
            result = StepResult(name=name, success=False, error=str(exc))
        if not isinstance(result, StepResult):
            result = StepResult(name=name, success=True, detail=dict(result or {}))
        self.op_result.steps.append(result)
        if result.success and compensate is not None:
            self._compensations.append((name, compensate))
        if not result.success and critical:
            await self.run_compensations()
            self.op_result.success = False
            self.op_result.error = result.error or f"Step '{name}' falló"
            raise _SagaAbort(self.op_result.error)
        return result

    async def run_compensations(self) -> None:
        for name, comp in reversed(self._compensations):
            try:
                cresult = comp()
                if hasattr(cresult, "__await__"):
                    cresult = await cresult  # type: ignore[assignment]
            except Exception as exc:
                cresult = StepResult(name=f"compensate:{name}", success=False, error=str(exc))
            if not isinstance(cresult, StepResult):
                cresult = StepResult(name=f"compensate:{name}", success=True, detail=dict(cresult or {}))
            else:
                cresult.name = f"compensate:{name}"
            self.op_result.compensations.append(cresult)


class _SagaAbort(Exception):
    pass


# ─── Orquestador ───────────────────────────────────────────────────

class TenantLifecycleOrchestrator:
    """
    API pública:
        await orchestrator.provision(spec, source=...)
        await orchestrator.deprovision(subdomain, source=..., backup=True, requested_by=...)
    """

    async def provision(self, spec: TenantSpec, *, source: LifecycleSource) -> TenantOpResult:
        from ..models.database import (
            SessionLocal, Customer, Subscription, SubscriptionStatus,
            BillingMode, PayerType, CollectorType, InvoiceIssuer, TenantDeployment,
        )
        from ..services.odoo_database_manager import (
            create_tenant_from_template, provision_tenant as provision_tenant_standard,
            COUNTRY_LOCALIZATION,
        )
        from ..services.deployment_writer import ensure_tenant_deployment
        from ..services.nginx_domain_configurator import provision_sajet_subdomain, remove_sajet_subdomain
        from ..services.tenant_credentials import build_tenant_admin_credentials
        from ..services.cloudflare_tunnel_gate import add_tenant_route, remove_tenant_route
        from ..config import ODOO_PRIMARY_IP

        result = TenantOpResult(
            success=True,
            subdomain=spec.subdomain,
            operation="provision",
            source=source,
        )
        saga = _Saga(result)

        try:
            # 1. Validate
            await saga.step("validate_spec", lambda: self._validate_spec(spec))

            # 2. Credenciales
            if not spec.admin_login or not spec.admin_password:
                login, password = build_tenant_admin_credentials(spec.subdomain)
                spec.admin_login = spec.admin_login or login
                spec.admin_password = spec.admin_password or password
            result.admin_login = spec.admin_login
            result.admin_password = spec.admin_password

            # 3. Crear BD (fast-path → fallback HTTP)
            loc = COUNTRY_LOCALIZATION.get((spec.country_code or "US").upper(), COUNTRY_LOCALIZATION["US"])
            creation_state: dict[str, Any] = {}

            async def _create_db() -> StepResult:
                if spec.use_fast_method:
                    fast = await create_tenant_from_template(
                        subdomain=spec.subdomain,
                        company_name=spec.company_name,
                        server_id=spec.server_id,
                        admin_login=spec.admin_login,
                        admin_password=spec.admin_password,
                        partner_id=spec.partner_id,
                        country_code=(spec.country_code or "US").upper(),
                        blueprint_package_name=spec.blueprint_package_name,
                    )
                    if fast and fast.get("success"):
                        creation_state["mode"] = "fast"
                        creation_state["server"] = fast.get("server")
                        creation_state["already_existed"] = fast.get("already_existed", False)
                        return StepResult(name="create_database", success=True, detail={
                            "mode": "fast", "server": fast.get("server"),
                            "already_existed": fast.get("already_existed", False),
                        })
                    fast_error = (fast or {}).get("error_code") or ""
                    if fast_error not in {
                        "template_missing", "template_check_failed",
                        "proxmox_ssh_unavailable", "fast_path_unavailable", "filestore_sync_failed",
                    }:
                        return StepResult(name="create_database", success=False,
                                          error=(fast or {}).get("error", "fast-path failed"))
                # fallback estándar
                std = await provision_tenant_standard(
                    subdomain=spec.subdomain,
                    company_name=spec.company_name,
                    admin_login=spec.admin_login,
                    admin_password=spec.admin_password,
                    server_id=spec.server_id,
                    country_code=(spec.country_code or "US").upper(),
                    lang=loc.get("lang", "en_US"),
                    blueprint_package_name=spec.blueprint_package_name,
                )
                if not std.get("success"):
                    return StepResult(name="create_database", success=False,
                                      error=std.get("error", "fallback HTTP failed"))
                creation_state["mode"] = "fallback_standard"
                creation_state["server"] = std.get("server")
                return StepResult(name="create_database", success=True, detail={
                    "mode": "fallback_standard", "server": std.get("server"),
                })

            async def _drop_db() -> StepResult:
                from ..services.odoo_database_manager import delete_tenant as _drop
                d = await _drop(spec.subdomain, creation_state.get("server"))
                return StepResult(name="rollback_db", success=bool(d.get("success")), detail=d)

            await saga.step("create_database", _create_db, compensate=_drop_db)

            # 3b. Provisionar servicio Odoo (config, puertos, cloudflared, DNS)
            odoo_service_state: dict[str, Any] = {}

            async def _provision_odoo_service() -> StepResult:
                from ..services.odoo_tenant_provisioner import provision_odoo_service
                loc = COUNTRY_LOCALIZATION.get((spec.country_code or "US").upper(), COUNTRY_LOCALIZATION["US"])
                template = loc.get("template_db", "tenant_do")
                # Resolve template from country
                from ..services.odoo_database_manager import resolve_template_db_for_country
                resolved_template = resolve_template_db_for_country(
                    (spec.country_code or "US").upper()
                )
                svc = await provision_odoo_service(
                    subdomain=spec.subdomain,
                    template_db=resolved_template,
                    base_domain=spec.base_domain,
                )
                if svc.get("success"):
                    odoo_service_state["http_port"] = svc["http_port"]
                    odoo_service_state["ws_port"] = svc["ws_port"]
                    odoo_service_state["backend_host"] = svc.get("backend_host", "10.10.20.201")
                    return StepResult(name="provision_odoo_service", success=True, detail=svc)
                return StepResult(name="provision_odoo_service", success=False,
                                  error=svc.get("error", "odoo service provisioning failed"))

            async def _deprovision_odoo_service() -> StepResult:
                from ..services.odoo_tenant_provisioner import deprovision_odoo_service
                d = await deprovision_odoo_service(spec.subdomain, spec.base_domain)
                return StepResult(name="rollback_odoo_service", success=True, detail=d)

            await saga.step("provision_odoo_service", _provision_odoo_service,
                            compensate=_deprovision_odoo_service, critical=False)

            # 4. Customer + Subscription (idempotente)
            def _upsert_customer() -> StepResult:
                db = SessionLocal()
                try:
                    customer = None
                    if spec.customer_id:
                        customer = db.query(Customer).filter_by(id=spec.customer_id).first()
                    if not customer:
                        customer = db.query(Customer).filter_by(subdomain=spec.subdomain).first()
                    if not customer:
                        customer = Customer(
                            company_name=spec.company_name or spec.subdomain.title(),
                            full_name=spec.company_name or spec.subdomain.title(),
                            email=spec.admin_login,
                            subdomain=spec.subdomain,
                        )
                        db.add(customer); db.commit(); db.refresh(customer)
                    result.customer_id = customer.id

                    subscription = None
                    if spec.subscription_id:
                        subscription = db.query(Subscription).filter_by(id=spec.subscription_id).first()
                    if not subscription:
                        subscription = db.query(Subscription).filter(
                            Subscription.customer_id == customer.id,
                            Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.trialing]),
                        ).first()
                    if not subscription:
                        subscription = Subscription(
                            customer_id=customer.id,
                            plan_name=spec.plan_name,
                            status=SubscriptionStatus.active,
                            owner_partner_id=spec.partner_id,
                            billing_mode=BillingMode.PARTNER_DIRECT if spec.partner_id else BillingMode.JETURING_DIRECT_SUBSCRIPTION,
                            payer_type=PayerType.PARTNER if spec.partner_id else PayerType.CLIENT,
                            collector=CollectorType.STRIPE_CONNECT if spec.partner_id else CollectorType.STRIPE_DIRECT,
                            invoice_issuer=InvoiceIssuer.JETURING,
                        )
                        db.add(subscription); db.commit(); db.refresh(subscription)
                    result.subscription_id = subscription.id
                    return StepResult(name="upsert_customer", success=True, detail={
                        "customer_id": customer.id, "subscription_id": subscription.id,
                    })
                finally:
                    db.close()

            await saga.step("upsert_customer", _upsert_customer, critical=False)

            # 5. TenantDeployment
            deployment_state: dict[str, Any] = {}

            def _write_deployment() -> StepResult:
                db = SessionLocal()
                try:
                    if not result.subscription_id:
                        return StepResult(name="write_deployment", success=False, error="subscription_id ausente")
                    dep_res = ensure_tenant_deployment(
                        subdomain=spec.subdomain,
                        subscription_id=result.subscription_id,
                        customer_id=result.customer_id,
                        server_id=creation_state.get("server"),
                        plan_name=spec.plan_name,
                        http_port=odoo_service_state.get("http_port"),
                        chat_port=odoo_service_state.get("ws_port"),
                        db=db,
                    )
                    if not dep_res.get("success"):
                        return StepResult(name="write_deployment", success=False, error=dep_res.get("error"))
                    db.commit()
                    result.deployment_id = dep_res["deployment_id"]
                    # Releer para puertos/host reales
                    dep = db.query(TenantDeployment).filter_by(id=result.deployment_id).first()
                    if dep:
                        result.backend_host = dep.backend_host or ODOO_PRIMARY_IP
                        result.http_port = dep.http_port or 8080
                        result.chat_port = dep.chat_port or 8072
                        deployment_state["backend_host"] = result.backend_host
                        deployment_state["http_port"] = result.http_port
                        deployment_state["chat_port"] = result.chat_port
                    return StepResult(name="write_deployment", success=True, detail=dep_res)
                finally:
                    db.close()

            await saga.step("write_deployment", _write_deployment, critical=False)

            backend_host = odoo_service_state.get("backend_host") or deployment_state.get("backend_host") or ODOO_PRIMARY_IP
            http_port = int(odoo_service_state.get("http_port") or deployment_state.get("http_port") or 8080)
            chat_port = int(odoo_service_state.get("ws_port") or deployment_state.get("chat_port") or 8072)

            # 6. Nginx
            def _configure_nginx() -> StepResult:
                ng = provision_sajet_subdomain(
                    subdomain=spec.subdomain,
                    node_ip=backend_host,
                    http_port=http_port,
                    chat_port=chat_port,
                )
                ok = bool(ng.get("success"))
                return StepResult(name="configure_nginx", success=ok,
                                  detail=ng, error=None if ok else ng.get("error"))

            def _remove_nginx() -> StepResult:
                ng = remove_sajet_subdomain(spec.subdomain, node_ip=backend_host)
                return StepResult(name="rollback_nginx", success=bool(ng.get("success")), detail=ng)

            await saga.step("configure_nginx", _configure_nginx, compensate=_remove_nginx, critical=False)

            # 7. Cloudflared (PCT 205) — manejado por provision_odoo_service en paso 3b
            #    Si odoo_service_state tiene datos, las rutas ya fueron creadas.
            #    Solo ejecutar si el paso 3b no lo hizo (fallback).
            if not odoo_service_state.get("http_port"):
                def _configure_cloudflared() -> StepResult:
                    from ..config import get_runtime_setting, get_runtime_int

                    tunnel_edge_host = get_runtime_setting("TUNNEL_EDGE_HOST", "10.10.20.205")
                    tunnel_edge_port = get_runtime_int("TUNNEL_EDGE_PORT", 80)
                    gate = add_tenant_route(
                        subdomain=spec.subdomain,
                        node_ip=tunnel_edge_host,
                        http_port=tunnel_edge_port,
                        chat_port=tunnel_edge_port,
                        base_domain=spec.base_domain,
                    )
                    ok = bool(gate.get("success"))
                    return StepResult(name="configure_cloudflared", success=ok,
                                      detail=gate, error=None if ok else gate.get("error"))

                def _remove_cloudflared() -> StepResult:
                    gate = remove_tenant_route(spec.subdomain, base_domain=spec.base_domain)
                    return StepResult(name="rollback_cloudflared", success=bool(gate.get("success")), detail=gate)

                await saga.step("configure_cloudflared", _configure_cloudflared,
                                compensate=_remove_cloudflared, critical=False)

            # 8. Email credenciales (opcional)
            if spec.send_credentials_email and spec.admin_email:
                from ..services.email_service import send_tenant_credentials

                def _send_email() -> StepResult:
                    try:
                        send_tenant_credentials(
                            to_email=spec.admin_email,
                            company_name=spec.company_name or spec.subdomain.title(),
                            subdomain=spec.subdomain,
                            admin_login=spec.admin_login,
                            admin_password=spec.admin_password,
                            plan_name=spec.plan_name,
                        )
                        return StepResult(name="send_credentials", success=True)
                    except Exception as e:
                        return StepResult(name="send_credentials", success=False, error=str(e))

                await saga.step("send_credentials", _send_email, critical=False)

            # 9. Audit
            await saga.step("audit", lambda: self._audit_provision(spec, source, result), critical=False)

            return result

        except _SagaAbort:
            return result

    # ────────── Deprovision ──────────

    async def deprovision(
        self,
        subdomain: str,
        *,
        source: LifecycleSource,
        backup: bool = True,
        purge_local: bool = True,
    ) -> TenantOpResult:
        from ..models.database import SessionLocal, Customer, Subscription, TenantDeployment
        from ..services.odoo_database_manager import delete_tenant as _drop_db, backup_tenant
        from ..services.nginx_domain_configurator import remove_sajet_subdomain
        from ..services.cloudflare_tunnel_gate import remove_tenant_route
        from ..services.cloudflare_manager import CloudflareManager

        result = TenantOpResult(
            success=True,
            subdomain=subdomain,
            operation="deprovision",
            source=source,
        )
        saga = _Saga(result)

        # Resolver datos del deployment para conocer node_ip
        ctx: dict[str, Any] = {"backend_host": None, "server_id": None, "tenant_email": None, "company": subdomain}
        db = SessionLocal()
        try:
            customer = db.query(Customer).filter_by(subdomain=subdomain).first()
            if customer:
                ctx["customer_id"] = customer.id
                ctx["tenant_email"] = customer.email
                ctx["company"] = customer.company_name or subdomain
            dep = db.query(TenantDeployment).filter_by(subdomain=subdomain).first()
            if dep:
                ctx["backend_host"] = dep.backend_host
                ctx["deployment_id"] = dep.id
        finally:
            db.close()

        try:
            # 1. Backup (opcional)
            if backup:
                async def _backup() -> StepResult:
                    bk = await backup_tenant(subdomain, ctx.get("server_id"))
                    return StepResult(name="backup_database", success=bool(bk.get("success")), detail=bk,
                                      error=None if bk.get("success") else bk.get("error"))
                await saga.step("backup_database", _backup, critical=False)

            # 2. Drop BD Odoo
            async def _drop() -> StepResult:
                d = await _drop_db(subdomain, ctx.get("server_id"))
                return StepResult(name="delete_database", success=bool(d.get("success")), detail=d,
                                  error=None if d.get("success") else d.get("error"))
            await saga.step("delete_database", _drop, critical=False)

            # 3. Quitar nginx
            def _rm_nginx() -> StepResult:
                ng = remove_sajet_subdomain(subdomain, node_ip=ctx.get("backend_host") or "10.10.20.201")
                return StepResult(name="remove_nginx", success=bool(ng.get("success")), detail=ng)
            await saga.step("remove_nginx", _rm_nginx, critical=False)

            # 4. Quitar cloudflared
            def _rm_cf() -> StepResult:
                g = remove_tenant_route(subdomain)
                return StepResult(name="remove_cloudflared", success=bool(g.get("success")), detail=g)
            await saga.step("remove_cloudflared", _rm_cf, critical=False)

            # 5. Remove DNS Cloudflare
            async def _rm_dns() -> StepResult:
                try:
                    cf = await CloudflareManager.delete_subdomain_dns(subdomain=subdomain, domain="sajet.us")
                    return StepResult(name="remove_dns", success=True, detail=cf)
                except Exception as e:
                    return StepResult(name="remove_dns", success=False, error=str(e))
            await saga.step("remove_dns", _rm_dns, critical=False)

            # 6. Limpiar registros locales
            if purge_local:
                def _purge_local() -> StepResult:
                    db2 = SessionLocal()
                    try:
                        c = db2.query(Customer).filter_by(subdomain=subdomain).first()
                        if c:
                            db2.query(Subscription).filter(Subscription.customer_id == c.id).delete()
                            db2.query(TenantDeployment).filter(TenantDeployment.subdomain == subdomain).delete()
                            db2.delete(c)
                            db2.commit()
                            return StepResult(name="purge_local", success=True, detail={"customer_id": c.id})
                        return StepResult(name="purge_local", success=True, detail={"note": "no local record"})
                    finally:
                        db2.close()
                await saga.step("purge_local", _purge_local, critical=False)

            await saga.step("audit", lambda: self._audit_deprovision(subdomain, source, result), critical=False)
            return result
        except _SagaAbort:
            return result

    # ────────── Helpers ──────────

    def _validate_spec(self, spec: TenantSpec) -> StepResult:
        sub = (spec.subdomain or "").strip().lower()
        if len(sub) < 3 or len(sub) > 30:
            return StepResult(name="validate_spec", success=False, error="subdomain debe tener 3..30 chars")
        if any(c not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for c in sub):
            return StepResult(name="validate_spec", success=False, error="subdomain inválido")
        if sub in {"admin", "api", "www", "mail", "postgres", "template", "template_tenant", "root"}:
            return StepResult(name="validate_spec", success=False, error=f"'{sub}' es reservado")
        spec.subdomain = sub
        return StepResult(name="validate_spec", success=True)

    def _audit_provision(self, spec: TenantSpec, source: LifecycleSource, op: TenantOpResult) -> StepResult:
        logger.info(
            "[lifecycle] PROVISION subdomain=%s source=%s success=%s customer_id=%s subscription_id=%s deployment_id=%s",
            spec.subdomain, source, op.success, op.customer_id, op.subscription_id, op.deployment_id,
        )
        return StepResult(name="audit", success=True, detail={"source": source})

    def _audit_deprovision(self, subdomain: str, source: LifecycleSource, op: TenantOpResult) -> StepResult:
        logger.info(
            "[lifecycle] DEPROVISION subdomain=%s source=%s success=%s",
            subdomain, source, op.success,
        )
        return StepResult(name="audit", success=True, detail={"source": source})


# Instancia singleton para inyección directa
orchestrator = TenantLifecycleOrchestrator()
