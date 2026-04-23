# Boletly Sandbox y Validacion Operativa

Fecha: 2026-04-22

## Objetivo

Dejar `boletly` en una base mas consistente para:

- usar Stripe respetando el modo activo de la compania, incluyendo `sandbox`
- alinear checkout XML + JS + backend
- corregir visibilidad y estructura de menus internos
- endurecer JS de scanner para evitar fallos por elementos faltantes
- dejar evidencia de validacion web y revisiones locales

## Cambios aplicados

Archivos tocados:

- `/opt/odoo/Extra/boletly_tickets/controllers/main.py`
- `/opt/odoo/Extra/boletly_tickets/views/templates/checkout.xml`
- `/opt/odoo/Extra/boletly_tickets/views/menus.xml`
- `/opt/odoo/Extra/boletly_tickets/static/src/css/boletly.css`
- `/opt/odoo/Extra/boletly_tickets/static/src/js/scanner.js`
- `/opt/odoo/Extra/boletly_tickets/tests/test_controllers.py`

## Ajuste adicional de integracion Stripe

Se redefinio el stack objetivo para Boletly:

- Pagos y configuracion Stripe: `jeturing_event_stripe`
- Onboarding portal: `jeturing_stripe_portal_onb`

Cambios concretos:

- `boletly_tickets` ahora declara dependencia directa de `jeturing_stripe_portal_onb`.
- El facade `/mi-portal/boletly/stripe/onboard` ya no renderiza onboarding propio; ahora prepara los flags del portal y redirige a `/my/onboarding`.
- El menu interno de operaciones Stripe ahora abre la configuracion de `jeturing_event_stripe`.
- Se agrego acceso interno a `Transacciones Stripe Portal`.

## Ajuste adicional solicitado

1. Creacion de eventos desde `/my/`

- El formulario de `Nueva publicacion de evento` ahora expone:
  - venue address y maps URL
  - fee de plataforma
  - payout hold days
  - refund policy y deadline
  - ITBIS
  - ticket type general
  - ticket type VIP opcional
  - promo code / descuento aplicable desde checkout

2. Modo Stripe sandbox

- Se corrigio la resolucion de llaves en `jeturing_stripe_onboarding` para que `stripe_mode = sandbox` deje de resolver automaticamente al slot `test`.
- En sandbox ahora se prioriza:
  - `sandbox_*` en config si existen
  - las llaves activas actuales de la compania si son compatibles con sandbox
  - el slot `test` solo como fallback controlado

Esto corrige el sintoma observado donde checkout terminaba usando una `sk_test` expirada de pruebas legacy en vez de la configuracion sandbox vigente.

Resumen:

1. Stripe / sandbox

- `main.py` ahora usa `company.stripe_secret_key_safe` antes de caer al campo legacy.
- El checkout no se marca como disponible si falta la llave secreta.
- `create_order` devuelve error claro si Stripe Connect del organizador no esta listo o si falta la llave secreta.

2. Checkout

- `checkout.xml` fue actualizado al flujo real que espera `static/src/js/checkout.js`.
- Se agregaron `data-payment-available`, `data-apply-itbis`, `data-itbis-rate` y `data-payment-message`.
- Se reemplazo el contenedor viejo `stripe-card-element` por `stripe-payment-element`.
- Se agregaron `payment-hint` y `selection-lock-hint`.
- Se mejoro el layout visual para el flujo de Payment Element.

3. Menus

- `Tipos de Boleta` se movio debajo de `Configuracion` de Boletly.
- Se elimino la desactivacion del menu `Configuracion`, que hacia invisible una parte importante del arbol.

4. JS operativos

- `scanner.js` ahora valida la existencia de nodos antes de escribir resultados y estadisticas.
- Se evita que el scanner falle por `null.textContent` si el DOM cambia o no termina de montar.

5. Colores / header

- Se reforzaron selectores CSS para ocultar telefono, carrito y CTA generica `Contact Us` en header.
- Se preserva el estilo oscuro Boletly y el CTA de login.

6. Pruebas

- Se agregaron validaciones HTTP para hooks de checkout y paginas legales en `tests/test_controllers.py`.

## Validacion local realizada

Validaciones ejecutadas:

- `python3 -m py_compile` sobre controladores y pruebas modificadas: OK
- parse XML de:
  - `/opt/odoo/Extra/boletly_tickets/views/templates/checkout.xml`
  - `/opt/odoo/Extra/boletly_tickets/views/menus.xml`
  Resultado: OK
- `node --check` sobre:
  - `/opt/odoo/Extra/boletly_tickets/static/src/js/checkout.js`
  - `/opt/odoo/Extra/boletly_tickets/static/src/js/scanner.js`
  Resultado: OK

## Validacion web en boletly.com

Pruebas manuales por HTTP/curl:

1. Sitio publico

- `https://boletly.com/` responde `HTTP/2 200`
- `https://boletly.com/terms` responde `HTTP/2 200`
- `https://boletly.com/privacy` responde `HTTP/2 200`

2. Login con credenciales provistas

- `GET /web/login`: OK
- `POST /web/login` con usuario provisto: login exitoso
- Redireccion observada: `/web`
- Sesion autenticada observada en respuesta de `/web`:
  - `db`: `boletly`
  - `username`: `boletly`
  - `uid`: `11`

## Hallazgos en produccion observados desde la web

El sitio actual en `boletly.com` todavia expone elementos legacy de header:

- carrito de ecommerce
- telefono placeholder `+1 555-555-5556`
- CTA duplicada `Contact Us`

Eso confirma que la version servida en web aun no refleja por completo las correcciones locales, o que el header actual del sitio necesita un despliegue/actualizacion de assets para tomar los selectores reforzados.

## Limitaciones de esta validacion

- No fue posible ejecutar el suite completo de Odoo desde este workspace porque aqui no esta disponible el runtime completo de Odoo usado por la instancia viva.
- Por eso la evidencia tecnica se deja en dos niveles:
  - validacion estatica local de Python/XML/JS
  - validacion remota del sitio real y del login en `boletly.com`

## Siguiente paso recomendado

1. Actualizar el modulo `boletly_tickets` en la instancia de `boletly`.
2. Regenerar assets frontend.
3. Reprobar:
   - `/boletly/checkout/<event_id>`
   - homepage header
   - `/terms`
   - `/privacy`
   - flujo de compra hasta `PaymentIntent`
