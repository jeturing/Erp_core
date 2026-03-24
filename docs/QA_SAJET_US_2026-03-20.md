# QA SAJET.US — Validación de rutas, usabilidad y flujos (2026-03-20)

## Contexto aplicado

- Referencia operativa leída desde [AGENTE.md](../AGENTE.md).
- Objetivo: validar rutas web y usabilidad, ejecutar flujo demo (cliente/socio/tenant), limpiar al finalizar, y correr pruebas unitarias del flujo cliente.
- Restricción solicitada: **sin eliminar datos productivos**.

---

## 1) Validación de rutas web públicas (real en producción)

Base probada: `https://sajet.us`

| Ruta            | Resultado | Observación                             |
| --------------- | --------: | --------------------------------------- |
| `/`             |       200 | Landing carga correctamente             |
| `/signup`       |       200 | Formulario visible                      |
| `/onboarding`   |       200 | Alias funcional de signup               |
| `/login`        |       200 | Redirige a `/login/admin`               |
| `/login/tenant` |       200 | Página visible                          |
| `/admin`        |       200 | Redirige a login admin si no hay sesión |

**Usabilidad (Playwright, headless):**

- Formularios, botones e inputs renderizados correctamente en `/signup`, `/onboarding`, `/login/admin`, `/login/tenant`.
- Screenshots generados en:
  - `/tmp/sajet_qa_home.png`
  - `/tmp/sajet_qa_signup.png`
  - `/tmp/sajet_qa_onboarding.png`
  - `/tmp/sajet_qa_login_admin.png`
  - `/tmp/sajet_qa_login_tenant.png`
- Se observaron errores 401 en consola para recursos protegidos (esperado sin sesión en algunos llamados internos).

---

## 2) Flujo demo documentado (API real)

### 2.1 Login admin

- Login exitoso con `admin@sajet.us`.

### 2.2 Socio comercial (partner)

- `POST /api/partners` ✅ **creado** partner demo.
- `DELETE /api/partners/{id}` ✅ **limpieza ejecutada** (quedó desactivado, no activo).

### 2.3 Creación de tenant en Odoo 17 (web)

- `POST /api/tenants` con `server_id=pct-105` ❌ falló por bloqueo técnico:
  - `Odoo DB manager deshabilitado o master password inválido`
  - y luego: `No se pudo copiar filestore desde 'template_tenant'`.

### 2.4 Creación de tenant en Odoo 19 (web)

- `POST /api/tenants` con `server_id=pct-161` ❌ falló por diseño actual:
  - `Servidor no disponible`.

---

## 3) Hallazgos clave

1. **La capa web de tenants hoy solo expone 1 servidor** en `/api/tenants/servers`:
   - `pct-105` (Odoo 17).
2. **PCT 161 (Odoo 19) no está integrado** aún al selector web de provisioning multi-servidor.
3. El flujo fast-path SQL depende de:
   - template DB + template filestore consistentes,
   - credenciales DB Odoo correctas,
   - y operación de copia de filestore disponible.
4. Se corrigió despliegue runtime para que el backend use `.env.production` actualizado en `/var/www/html/.env.production` y `/var/www/html/.env`.

---

## 4) Pruebas unitarias ejecutadas

Comando ejecutado:

- `pytest -q tests/test_onboarding.py tests/test_tenants.py tests/test_tenant_portal.py tests/test_auth.py`

Resultado:

- **34 passed**, **17 failed**, **2 skipped**.

Patrones de fallo:

- Múltiples tests esperan 200 en páginas que devuelven 503 en entorno de test (templates/servicio no listos en ese contexto).
- Tests de auth usan credenciales antiguas (`admin` / `testpass123`) y hoy el admin válido es `admin@sajet.us`.
- Rate limiting en `/api/auth/login` genera 429 en varios casos de test encadenados.

---

## 5) Estado respecto al requerimiento

### Cumplido

- Validación completa de rutas web y usabilidad real.
- Flujo demo de socio comercial ejecutado y limpiado.
- Ejecución de suite unitaria relevante y documentación de resultados.

### Pendiente para cerrar 100%

- Habilitar creación tenant web estable en Odoo 17 (resolver filestore/template).
- Integrar Odoo 19 (`pct-161`) y nodos adicionales en provisioning web (no solo servidor primario).

---

## 6) Recomendación inmediata

1. Implementar catálogo multi-servidor configurable (DB/UI) para provisioning (`pct-105`, `pct-161`, futuros nodos).
2. Validación de preflight obligatoria en UI para:
   - template DB,
   - template filestore,
   - salud de conexión SQL.
3. Ajustar tests de auth a credenciales actuales y aislar rate-limiter en entorno de pruebas.
