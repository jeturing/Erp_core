# 🧩 Análisis Técnico: SAJET ERP Core (v2.1.0)

Este documento proporciona una visión técnica profunda del repositorio Erp_core para que otros modelos de IA o desarrolladores puedan comprender rápidamente su arquitectura, flujo de datos y lógica de negocio.

## 🏗️ 1. Arquitectura del Sistema

SAJET es una plataforma **SaaS Multi-tenant** orquestadora de instancias Odoo. No es solo un ERP, sino el "Cerebro" que gestiona la vida de otros ERPs.

### Capas Principales:
- **Backend**: FastAPI (Python 3.11+). Basado en una arquitectura de servicios y rutas asíncronas.
- **Frontend**: Svelte 5 (Runes mode). Uso intensivo de reactividad moderna y TypeScript.
- **Base de Datos**: PostgreSQL 15/16. Estructura relacional compleja con soporte para i18n dinámico.
- **Orquestación**: Integración con Proxmox (PCT), Cloudflare Tunnels y Stripe.

---

## 📊 2. Modelo de Datos (Principales Entidades)

El archivo maestro es \`app/models/database.py\`. Las entidades se agrupan por "Épicas":

### Core y Tenants:
- **Tenant (\`tenants\`)**: La entidad central. Representa una instancia corporativa.
  - Campos clave: \`subdomain\`, \`db_name\`, \`plan_id\`, \`status\`.
  - Relaciones: \`owner_id\`, \`node_id\`.
- **Node (\`nodes\`)**: Representa un servidor físico o LXC (PCT en Proxmox) donde viven los contenedores Odoo.
- **TenantDeployment (\`tenant_deployments\`)**: Historial y estado técnico del despliegue (IP, puerto, container_id).

### Billing & Partners:
- **Partner (\`partners\`)**: Revendedores o consultores que gestionan múltiples tenants.
- **Subscription (\`subscriptions\`)**: Vincula tenants con planes de Stripe.
- **StripeCustomer / StripeAccount**: Mapeo con el ecosistema de pagos.

### Internacionalización (v2.1.0):
- **Translation (\`translations\`)**: Strings dinámicos traducibles desde el Admin Panel.
- **LandingSection (\`landing_sections\`)**: Contenido de la web pública (Hero, Features) segmentado por \`locale\`.
- **Testimonial (\`testimonials\`)**: Testimonios multiidioma.

### Seguridad y Firma:
- **Agreement (\`agreements\`)**: Plantillas HTML de NDA/TOS con variables dinámicas.
- **SignedAgreement (\`signed_agreements\`)**: Registro de firmas digitales (ID, IP, User-Agent, Hash SHA256).

---

## ⚡ 3. Flujos de Funcionalidad Clave

### A. Onboarding de Tenant (Self-Service)
1. Usuario elige Plan (\`app/routes/plans.py\`).
2. Introducción de datos y validación de subdominio (Cloudflare API).
3. Verificación de Email (Steam-style, \`app/security/email_verify.py\`).
4. Firma de contratos (\`app/routes/agreements.py\`).
5. Pago vía Stripe Checkout.
6. **Provisioning**: Llamada al orquestador para crear base de datos y container Odoo (\`app/services/provisioning.py\`).

### B. Internacionalización Híbrida
- **Estática**: \`frontend/src/lib/i18n/*.json\` (UI básica).
- **Dinámica**: El backend sirve traducciones desde la BD basadas en el header \`Accept-Language\` o parámetro \`locale\`. El Admin Panel permite editar estas keys sin redespachar código.

### C. Seguridad Multi-Tenant
- **CORS Dinámico**: \`app/security/cors_dynamic.py\` carga orígenes permitidos desde la BD (\`custom_domains\`).
- **Roles**: Admin, Operator, Viewer, Partner, Tenant Admin.

---

## 🛠️ 4. Estructura de Rutas (API)

Ubicación: \`app/routes/\`
- \`public_landing.py\`: Endpoints para el frontend sin auth (Testimonios, Planes, Secciones).
- \`admin_control_panel.py\`: Gestión total del sistema.
- \`onboarding.py\`: Flujo de registro de nuevos clientes/partners.
- \`session_monitoring.py\`: (DSAM) Monitoreo de sesiones activas en tiempo real.
- \`branding.py\`: Configuración de Marca Blanca (Logos/Colores por Partner).

---

## 🎨 5. Interfaz de Usuario (Svelte 5)

Ubicación: \`frontend/src/\`
- **Runes**: Uso de \`$state\`, \`$derived\`, \`$effect\` para una gestión de estado ultra-eficiente.
- **Layouts**: \`lib/components/Layout.svelte\` gestiona la persistencia de la barra lateral y navegación.
- **i18n Store**: \`lib/stores/locale.ts\` sincroniza el idioma entre el navegador, la BD y la UI.
- **Branding dinámico**: La UI inyecta variables CSS basadas en la configuración del Partner (\`--primary-color\`, etc.).

---

## 🚀 6. Operación y Despliegue

- **Entorno Productivo**: PCT 160 (App) + PCT 137 (DB).
- **Herramientas de Validación**: \`/opt/tools/validate_deploy.py\` realiza tests E2E y visuales.
- **Migraciones**: \`alembic upgrade head\` gestiona cambios en el esquema.

