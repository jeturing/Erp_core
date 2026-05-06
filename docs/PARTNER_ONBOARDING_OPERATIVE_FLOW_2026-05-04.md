# Plan + Diagramas Operativos — Partner Onboarding y Gestión de Socios

Fecha: 2026-05-04

## Objetivo
Identificar con precisión dónde se rompe el flujo operativo cuando un socio crea cliente/tenant desde Partner Portal y alinear provisioning, Stripe Connect, credenciales y publicación del tenant.

---

## Resumen Ejecutivo (hallazgos)

Caso validado: `vce` (Vitalina Clínica de Estética)

- Cliente y suscripción se crearon en BDA (`customers.id=63`, `subscriptions.id=53`) ✅
- Tenant público `vce.sajet.us` devolvió 502 ❌
- En el primer intento no existía BD `vce` en PostgreSQL ❌
- No había `tenant_deployments` para `customer_id=63` al inicio ❌
- No existía entrada `vce.sajet.us` en `/root/.cloudflared/config.yml` (PCT 205) ❌
- El flujo de create devolvió éxito visual aunque provisioning no quedó operativo ❌

---

## Diagrama 1 — Flujo actual (AS-IS) Partner → Tenant

```text
Socio (Partner Portal)
   |
   | POST /api/partner-portal/clients
   v
SAJET API (partner_portal.create_partner_client)
   |
   | 1) crea Customer + Subscription (status=active)
   | 2) intenta _auto_provision_tenant(...)
   v
Provisioning (customers._auto_provision_tenant)
   |
   |--> create_tenant_from_template (DB + filestore)
   |--> provision_sajet_subdomain (nginx)
   |--> add_tenant_route (cloudflared)
   |--> ensure_tenant_deployment
   v
Respuesta API
   |
   | success=true (aunque haya fallas parciales)
   v
UI muestra cliente + dominio base "subdomain.sajet.us"
   |
   v
Usuario abre dominio
   |
   v
Cloudflare 502 (si publishing/routing/backend no quedó completo)
```

---

## Diagrama 2 — Flujo Stripe Connect (AS-IS)

```text
Partner Portal
   |
   | POST /api/partner-portal/onboarding/start-stripe
   v
SAJET (partner_portal)
   |
   | create/reuse connected account
   | genera onboarding link
   v
Stripe Connect Express (KYC)
   |
   | webhooks account.updated
   v
SAJET actualiza flags partner (charges_enabled / onboarding_complete)
   |
   v
Tabs Stripe/Facturas/Comisiones dependen de esos flags + estado de facturas
```

---

## Diagrama 3 — Flujo objetivo (TO-BE) con temporizador y estado real

```text
POST /clients
  -> crea registro de "deployment_job" (status=queued)
  -> customer/subscription en estado PENDING (no ACTIVE)
  -> responde 202 + job_id + ETA + countdown

UI (timer + polling cada 5s)
  -> GET /deployments/{job_id}/status
  -> fases: db_clone -> filestore -> route -> healthcheck -> credentials

Si OK:
  -> activa subscription
  -> publica credenciales (partner + tenant + soporte Jeturing)
  -> habilita dominio click (healthcheck=pass)

Si FAIL:
  -> status=failed + reason técnico + acción sugerida
  -> NO mostrar dominio como activo
  -> botón "Reintentar" idempotente
```

---

## Puntos de ruptura detectados (con evidencia técnica)

1. **Éxito funcional prematuro**
   - En [app/routes/partner_portal.py](app/routes/partner_portal.py) y [app/routes/customers.py](app/routes/customers.py), se retorna éxito de creación aunque provisioning pueda quedar incompleto.

2. **Subscription activa antes de validación de tenant**
   - En [app/routes/partner_portal.py](app/routes/partner_portal.py), la `Subscription` nace activa antes de confirmar publicación/healthcheck del tenant.

3. **Dominio base se muestra aunque no esté operativo**
   - En [app/routes/partner_portal.py](app/routes/partner_portal.py), el endpoint de dominios agrega `subdomain.sajet.us` como base sin validar reachability real.

4. **Selección de servidor rota por NodeRegistry legacy**
   - En [app/services/odoo_database_manager.py](app/services/odoo_database_manager.py), `select_best_server()` dependía de NodeRegistry con nodos legacy/offline y devolvía `None`.
   - Se aplicó corrección local para fallback cuando NodeRegistry no retorna nodo elegible.

5. **Clasificación de estado de nodo con bug de Enum**
   - En [app/services/odoo_database_manager.py](app/services/odoo_database_manager.py), parse de `status` trataba `Enum` como texto no válido y degradaba decisiones.
   - Se aplicó corrección local para usar `value` del enum.

6. **Conectividad Odoo HTTP no disponible desde PCT 202**
   - El check `/web/database/list` a `10.10.20.201:8069` falla, por lo que la selección por salud HTTP no es suficiente para fast-path SQL.

7. **Canal SSH restringido (forced command) bloquea filestore/nginx**
   - Desde PCT 202, la llave SSH ejecuta comando forzado `tenant-web-gate`, impidiendo shell remoto general.
   - Impacta pasos que requieren `pct exec`/copiado de filestore.

8. **Mapa de nodos y puertos legacy en writer**
   - En [app/services/deployment_writer.py](app/services/deployment_writer.py) aún existen defaults de nodos `105/161`.
   - Riesgo de puertos/host inconsistentes para infraestructura actual `201/204`.

9. **Country template en create partner no explícito en runtime activo**
   - Runtime activo no pasaba `country_code` en `_auto_provision_tenant`; dependía de default.
   - Requisito de negocio: partner DO debe forzar `tenant_do`.

---

## Plan de corrección (orden recomendado)

### Fase 0 — Contención inmediata (hoy)
1. Cambiar `create_partner_client` a respuesta `202 Accepted` con `deployment_job_id`.
2. Crear estado `provisioning_pending` para `Subscription` y `Customer` hasta healthcheck final.
3. Ocultar dominio base en UI cuando `tenant_ready=false`.
4. Activar botón `Reintentar provisioning` por cliente.

### Fase 1 — Infra y provisioning core
1. Desacoplar `select_best_server` de disponibilidad HTTP para fast-path SQL.
2. Introducir `ProvisioningTransport`:
   - modo A: `pct exec` directo (host)
   - modo B: helper privilegiado (`sajet-proxmox-admin`)
   - modo C: API interna de provisioning (recomendado)
3. Corregir mapeo de nodos/puertos actuales (`201/204`) en writer.
4. Healthcheck obligatorio post-publish (`GET /web/login` del tenant).

### Fase 2 — UX operacional (temporizador + credenciales)
1. Nuevo endpoint `GET /api/partner-portal/deployments/{id}/status` con fases y ETA.
2. En UI, timer/countdown + barra por fase.
3. Panel “Credenciales creadas”:
   - credenciales tenant admin
   - credenciales operativas del socio
   - credencial de gestión Jeturing (solo rol autorizado)
4. Registro auditable de entrega (`credential_delivery_log`).

### Fase 3 — Regla país/plantilla (DO y futuras)
1. Forzar `country_code` en wizard de creación (obligatorio).
2. Resolver plantilla por mapa: `ODOO_TEMPLATE_DB_BY_COUNTRY`.
3. Política actual: DO -> `tenant_do`.
4. Soporte futuro: tablas de asignación por partner (`partner_country_template_policy`).

### Fase 4 — Stripe Connect + pagos partner
1. Validar consistencia SAJET ↔ Odoo módulo Stripe onboarding.
2. Unificar estados de onboarding (`eligible/started/pending/verified/restricted/disabled`).
3. En facturas: separar estado manual vs estado sincronizado Stripe para evitar reversión silenciosa.
4. Confirmar payout transfronterizo con cuenta Express conectada y capability real.

---

## Matriz de responsabilidades operativas

- **SAJET Backend**: estado de negocio, jobs, facturación, polling API.
- **Provisioning Engine**: DB clone, filestore, publish, healthchecks, rollback.
- **Infra (PCT 201/202/205/200)**: rutas, túneles, puertos, observabilidad.
- **Stripe/Odoo Module**: onboarding Connect, webhooks, ledger y transferencias.

---

## Checklist de aceptación

1. Crear cliente partner devuelve `job_id` y no marca activo hasta `healthcheck=pass`.
2. `vce.sajet.us` responde 200 en login Odoo.
3. Dominio no se muestra “activo” mientras esté en `provisioning_pending`.
4. Partner DO usa `tenant_do` de forma determinística.
5. UI muestra timer + fases + errores accionables.
6. Stripe status en portal refleja estado real en vivo.

---

## Riesgos actuales si no se corrige

- Falsos positivos operativos (cliente "activo" sin tenant operativo).
- 502 repetidos y pérdida de confianza del partner.
- Inconsistencias contables si se facturan tenants no publicados.
- Fragilidad por dependencia de nodos legacy/offline en selección.

---

## Próxima ejecución sugerida

1. Aplicar hotfix de estado `pending` + `202/job_id`.
2. Corregir transporte de provisioning (sin dependencia SSH restringida).
3. Reprocesar `vce` con pipeline controlado y healthcheck final.
4. Activar dashboard de observabilidad de jobs de tenant.
