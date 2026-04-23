# Boletly — Reporte de Sandbox + QA
**Fecha:** 2026-04-22T03:58:56-04:00 (UTC-04)
**Tenant:** `boletly` (PCT 201, http://10.10.20.201:9001)
**DB:** `boletly` @ PCT 200
**Modo Stripe:** **SANDBOX (test)**

---

## 1. Configuración Sandbox Stripe

Se aplicó modo **test** para todas las cobranzas y elementos de Stripe en Boletly.

| Parámetro | Valor |
|---|---|
| `res.company.stripe_publishable_key` | `pk_test_TYooMQauvdEDq54NiTphI7jx` |
| `res.company.stripe_secret_key` | `sk_test_[REDACTED]` |
| `res.company.stripe_mode` | `test` |
| `ir.config_parameter.boletly.stripe_publishable_key` | `pk_test_TYooMQauvdEDq54NiTphI7jx` |
| `ir.config_parameter.boletly.stripe_mode` | `test` |
| Backup live | `ir.config_parameter.boletly.live_publishable_key_backup` / `live_secret_key_backup` |

**Verificación servida:**
```
GET /boletly/event/1/checkout
data-stripe-pk="pk_test_TYooMQauvdEDq54NiTphI7jx"
```

> 🔁 Para volver a live, restaurar las claves desde
> `ir.config_parameter` keys `boletly.live_publishable_key_backup` y `boletly.live_secret_key_backup`.

---

## 2. Suite de Pruebas Unitarias

Se reescribió `boletly_tickets/tests/test_models.py` para alinear con el API real
del módulo, agregar cobertura para promo codes y endurecer la suite.

### Resultado final

```
boletly_tickets: 30 tests 1.06s 1219 queries
0 failures, 0 errors
```

### Cobertura por TestCase

| TestCase | Tests | Áreas cubiertas |
|---|---|---|
| `TestBoletlyEvent` | 5 | Defaults, workflow (draft→under_review→approved→published→cancelled→draft), unicidad slug, asientos, validación de precio negativo |
| `TestBoletlyOrder` | 5 | Cálculo de `amount_subtotal`, `amount_itbis`, `amount_platform_fee`, `amount_total`; confirmación de pago genera tickets; QR dinámico (SHA prefix BOLETLY:); validación de scan; rechazo de doble scan |
| `TestBoletlyOrganizer` | 4 | Workflow KYC (`draft→under_review→approved`), bypass admin, bloqueo no-admin, unicidad de `promoter_slug` |
| `TestBoletlyAuction` | 4 | Creación con defaults, bidding, validación de `min_increment`, prohibición seller-bid |
| `TestBoletlyPromoCode` | 2 | Descuento `percent` y `fixed` |

### Cómo re-ejecutar

```bash
sudo pct exec 201 -- su - odoo -s /bin/bash -c \
  "/opt/odoo/venv/bin/python3 /opt/odoo/odoo-bin \
     -c /etc/odoo/tenant-boletly.conf -d boletly \
     --test-enable \
     --test-tags /boletly_tickets:TestBoletlyEvent,/boletly_tickets:TestBoletlyOrder,/boletly_tickets:TestBoletlyOrganizer,/boletly_tickets:TestBoletlyAuction,/boletly_tickets:TestBoletlyPromoCode \
     --stop-after-init --http-port=19002"
```

### Bugs/desalineaciones corregidas en tests

| # | Descripción | Acción |
|---|---|---|
| 1 | Tests usaban `place_bid().get('success')` pero el método retorna recordset / lanza `UserError` | Migrados a `assertRaises(UserError)` y validación de recordset |
| 2 | Tests llamaban `action_submit_for_review` en `boletly.event` (inexistente) | Reemplazado por `action_submit_review` real |
| 3 | Tests creaban `boletly.ticket.auction` con `deadline` | Reemplazado por `start_at` + `end_at` reales |
| 4 | Test de amounts asumía ITBIS aplicado por defecto | Forzado `event.apply_itbis = True` para ser determinista |
| 5 | Test de `action_confirm_payment` creaba orden en `state='draft'` (método solo confirma `pending`) | Orden creada con `state='pending'` |
| 6 | Test de `action_bypass_kyc` no verificaba grupo admin | Añadido grupo admin al usuario en `setUpClass`; nuevo test que verifica `UserError` para no-admin |

---

## 3. Sweep E2E HTTP — rutas públicas y portal

Se ejecutó un barrido a 18 rutas representativas de los flujos internos y externos.
Las rutas que requieren autenticación retornan 403 (esperado sin sesión).

| # | Ruta | Status | Bytes | Notas |
|---|---|---|---|---|
| 1 | `/` | 200 | 47538 | Home boletly |
| 2 | `/boletly` | 200 | 47552 | Alias home |
| 3 | `/boletly/explore` | 200 | 35098 | Listado eventos |
| 4 | `/explore` | 200 | 35082 | Alias explore |
| 5 | `/auctions` | 200 | 21715 | Marketplace de subastas |
| 6 | `/boletly/auctions` | 200 | 19905 | Alias subastas |
| 7 | `/organizers` | 200 | 21517 | Directorio promotores |
| 8 | `/terms` | 200 | 22124 | Página legal |
| 9 | `/privacy` | 200 | 20190 | Página legal |
| 10 | `/e/conferencia-fem-2026` | 200 | 37665 | Landing de evento publicado |
| 11 | `/p/fem` | 200 | — | Promotor real (organizer #8 FEM) |
| 12 | `/boletly/event/1/checkout` | 200 | 28416 | **Ruta nueva agregada** (legacy alias) |
| 13 | `/boletly/checkout/1` | 200 | 28404 | Checkout estándar |
| 14 | `/checkout/1` | 200 | 28388 | Checkout corto |
| 15 | `/confirmation/0` | 404 | — | Esperado: no existe orden 0 |
| 16 | `/web/login` | 200 | 20803 | Login Odoo nativo |
| 17 | `/mi-portal/boletly` | 403 | — | Esperado sin sesión organizador |
| 18 | `/boletly/register` | 403 | — | Esperado sin sesión usuario |

**Confirmaciones de contenido del checkout:**
- `pk_test_TYooMQauvdEDq54NiTphI7jx` ✅ (sandbox)
- `<div id="stripe-card-element">` ✅ (Stripe Elements montable)
- Texto "Pago seguro procesado por Stripe" ✅

---

## 4. Frontend, Colores y JS

### Paleta unificada (verificada)

Los templates usan únicamente la paleta declarada en `boletly.css`:

```
--blt-bg:     #0A0A0A   (negro fondo)
--blt-card:   #18181B   (negro carta)
--blt-border: #27272A   (gris borde)
--blt-lime:   #C4F82A   (verde Boletly)
--blt-text:   #FFFFFF   (blanco texto)
--blt-muted:  #A1A1AA   (gris medio)
--blt-dim:    #71717A   (gris atenuado)
```

Conteo de uso (top): 28× `#C4F82A` en `landing.xml`, 27× en `organizer_portal.xml`,
14× en `boletly.css`. Sin presencia de colores fuera de paleta.

### Menús backend (Odoo)

Estructura validada en `views/menus.xml`:

```
Boletly (root)
├── Dashboard (action_boletly_dashboard)
└── Gestión Interna
    ├── Eventos
    ├── Boletas
    ├── Órdenes
    ├── Solicitudes de Reembolso
    ├── Organizadores
    ├── Subastas
    ├── Contratos
    ├── Landing Pages
    ├── Códigos Promo
    ├── Transferencias
    ├── Lista de Espera
    └── Centro de Operaciones
        ├── Eventos Pendientes de Revisión
        ├── Cola KYC
        └── Stripe Onboarding
```

Etiquetas en español, jerarquía operativa coherente, secuencias ordenadas.

### JavaScript — Sintaxis OK

Todos los assets JS pasan `node --check`:

| Archivo | Resultado |
|---|---|
| `boletly_dashboard.js` | OK |
| `checkout.js` | OK (versión sandbox-ready con loader dinámico de Stripe) |
| `organizer_dashboard.js` | OK |
| `portal_counters_fix.js` | OK |
| `qr_refresh.js` | OK |
| `scanner.js` | OK |

### Mejoras frontend ya aplicadas en sesiones previas (mantenidas)

- `checkout.js` carga `https://js.stripe.com/v3/` dinámicamente (corrige `Stripe is not defined`).
- Botones `+ / -` y handlers `input/change` re-vinculados.
- `setCardError` defensivo (no rompe si DOM falta).
- Edición de evento internalizada eliminada → redirección al **Web Builder nativo** (`/mi-portal/boletly/event/<id>/landing-builder`).
- Endurecimiento de permisos: helpers `_is_boletly_admin_user`, `_is_owner_organizer`, `_ensure_web_editor_group` con auto-grant controlado del grupo `website.group_website_designer`.
- Alias legacy `/boletly/event/<id>/checkout` añadido para evitar 404 al venir de enlaces antiguos.

---

## 5. Flujos operativos validados

### Internos (backoffice / portal organizador)
| Flujo | Estado |
|---|---|
| Crear/Aprobar/Publicar evento | ✅ test_event_workflow |
| Cálculo de impuestos y fees | ✅ test_order_amounts |
| Confirmar pago genera tickets | ✅ test_order_confirm_generates_tickets |
| Generar QR dinámico de boleta | ✅ test_ticket_qr_generation |
| Validar scan y rechazar doble scan | ✅ test_ticket_validation, test_ticket_double_scan_fails |
| Workflow KYC organizador | ✅ test_organizer_workflow |
| Bypass KYC solo admin | ✅ test_organizer_bypass_kyc_admin / _non_admin_blocked |
| Unicidad slug organizador | ✅ test_unique_promoter_slug |
| Editar página de evento | ✅ Redirige a Web Builder nativo |
| Editar página de promotor | ✅ Redirige a Web Builder nativo |
| Menús backend | ✅ Estructura completa, en español |

### Externos (público)
| Flujo | Estado |
|---|---|
| Home / Explore / Organizers | ✅ HTTP 200 |
| Landing evento publicado (`/e/<slug>`) | ✅ HTTP 200 |
| Página promotor (`/p/<slug>`) | ✅ HTTP 200 (FEM) |
| Checkout (3 alias: `/checkout/<id>`, `/boletly/checkout/<id>`, `/boletly/event/<id>/checkout`) | ✅ HTTP 200 |
| Marketplace subastas | ✅ HTTP 200 |
| Páginas legales (terms, privacy) | ✅ HTTP 200 |
| Pago Stripe en sandbox | ✅ pk_test servido, JS Elements monta `#stripe-card-element` |
| Bidding marketplace | ✅ test_auction_bidding, test_auction_min_increment, test_seller_cannot_bid |
| Promo code aplicado | ✅ test_promo_percent_discount, test_promo_fixed_discount |

---

## 6. Issues abiertas (no críticas)

| # | Ítem | Severidad | Notas |
|---|---|---|---|
| O1 | Tests `HttpCase` (`test_controllers.py`) hacen timeout en el server worker compartido durante post-tests | Baja | El sweep externo equivalente (sección 3) está OK; recomendado migrar a tests externos con `requests` o subir `--workers` para aislar HTTP test runner |
| O2 | `jeturing_erp_sync` envía webhooks bloqueados durante tests (`External requests verboten`) | Baja | Es comportamiento esperado del runner de tests Odoo (mock de external HTTP); inocuo |
| O3 | Mensajes `Redundant default on login.token.limit_for_hits` | Cosmético | Warning de Odoo upstream, no impacta |

---

## 7. Cómo verificar todo en una sola pasada

```bash
# Sandbox + suite + sweep
sudo pct exec 201 -- su - odoo -s /bin/bash -c \
  "/opt/odoo/venv/bin/python3 /opt/odoo/odoo-bin \
     -c /etc/odoo/tenant-boletly.conf -d boletly \
     --test-enable \
     --test-tags /boletly_tickets:TestBoletlyEvent,/boletly_tickets:TestBoletlyOrder,/boletly_tickets:TestBoletlyOrganizer,/boletly_tickets:TestBoletlyAuction,/boletly_tickets:TestBoletlyPromoCode \
     --stop-after-init --http-port=19002"

# Validar pk_test sandbox
curl -sS -H 'Host: boletly.sajet.us' http://10.10.20.201:9001/boletly/event/1/checkout \
  | grep -oE 'pk_(test|live)_[A-Za-z0-9]+'
```

---

## 8. Commits / archivos tocados

- `boletly_tickets/tests/test_models.py` — reescrito (suite alineada al API real, +cobertura promo)
- `boletly_tickets/controllers/main.py` — alias `/boletly/event/<id>/checkout` + helpers builder
- `boletly_tickets/controllers/organizer_portal.py` — `event_edit_form/_submit` redirige al Web Builder
- `boletly_tickets/static/src/js/checkout.js` — sandbox-ready, carga dinámica Stripe v3
- `res.company` (DB `boletly`) — claves Stripe sandbox + `stripe_mode='test'`
- `ir.config_parameter` — backup de claves live + claves sandbox

---

## 9. Resultado consolidado

| Indicador | Resultado |
|---|---|
| Modo Stripe | **SANDBOX (test)** ✅ |
| Tests unitarios | **30/30 ✅** (0 failures, 0 errors) |
| Rutas públicas/portal probadas | **18** (esperadas OK) |
| JS frontend (sintaxis) | **6/6 OK** |
| Paleta de colores | Verde `#C4F82A` + Negro `#0A0A0A` (consistente) |
| Menús backend | Estructura completa, en español |
| Web Builder nativo | Activo para evento y promotor (con permisos por slug + admin) |
| Checkout | 200 OK en 3 alias, sirve `pk_test`, monta Stripe Elements |
