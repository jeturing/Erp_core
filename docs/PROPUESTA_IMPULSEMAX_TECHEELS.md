# PROPUESTA DE DESARROLLO — PLATAFORMA IMPULSEMAX

**Documento:** Propuesta Técnica y Económica  
**Preparado para:** Techeels  
**Preparado por:** Equipo de Desarrollo  
**Fecha:** 8 de marzo de 2026  
**Versión:** 2.0 — Final (Mercado RD/US)  
**Moneda:** USD  
**Confidencialidad:** Documento confidencial — Solo para uso interno entre las partes

---

## ÍNDICE

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Visión del Producto](#2-visión-del-producto)
3. [Alcance Funcional Detallado](#3-alcance-funcional-detallado)
4. [Arquitectura Técnica](#4-arquitectura-técnica)
5. [Desglose de Módulos y Estimación de Horas](#5-desglose-de-módulos-y-estimación-de-horas)
6. [Cronograma de Implementación](#6-cronograma-de-implementación)
7. [Propuesta Económica](#7-propuesta-económica)
8. [Entregables por Fase](#8-entregables-por-fase)
9. [Stack Tecnológico](#9-stack-tecnológico)
10. [Garantías y Soporte Post-Lanzamiento](#10-garantías-y-soporte-post-lanzamiento)
11. [Términos y Condiciones Sugeridos](#11-términos-y-condiciones-sugeridos)
12. [Anexos](#12-anexos)

---

## 1. RESUMEN EJECUTIVO

### Contexto

Techeels busca desplegar una **plataforma SaaS marca blanca** bajo el nombre **ImpulseMax**, diseñada para ofrecer soluciones empresariales a medida a múltiples clientes (tenants) desde una infraestructura centralizada y escalable.

### Propuesta de Valor

ImpulseMax será una plataforma **multi-tenant, white-label y completamente modular** que permitirá:

- **Desplegar instancias ERP/CRM personalizadas** para cada cliente final
- **Gestionar suscripciones, facturación y cobros** de forma automatizada
- **Ofrecer dominios personalizados** con SSL automático para cada tenant
- **Administrar partners y afiliados** con tracking de comisiones
- **Escalar infraestructura** de manera dinámica según demanda
- **Operar en múltiples idiomas** (español/inglés) con soporte i18n nativo

### Diferenciador Clave

ImpulseMax se construye sobre **arquitecturas y componentes probados en producción**, lo que permite acelerar significativamente los tiempos de entrega sin sacrificar calidad. Techeels podrá:

1. Vender licencias SaaS bajo su propia marca
2. Gestionar todo el ciclo de vida del cliente (onboarding → operación → facturación)
3. Crear ecosistemas de partners con comisiones automatizadas
4. Operar múltiples marcas simultáneamente desde un solo panel administrativo

### Ventaja Competitiva del Equipo

Nuestro equipo opera desde **República Dominicana con presencia en Estados Unidos**, lo que ofrece:
- **Zona horaria alineada** (EST/AST) — comunicación en tiempo real, sin desfase
- **Costos competitivos nearshore** — calidad US a tarifas Latam
- **Bilingüe nativo** (ES/EN) — ideal para plataformas multi-idioma
- **Conocimiento regulatorio** — compliance US (ACH, KYC, Stripe) + mercado Latam

---

## 2. VISIÓN DEL PRODUCTO

### 2.1 Modelo de Negocio Soportado

```
┌───────────────────────────────────────────────────────────────────┐
│                      IMPULSEMAX PLATFORM                          │
│                    (Propiedad de Techeels)                        │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│   │  CLIENTES     │   │  PARTNERS    │   │  CONTADORES  │        │
│   │  DIRECTOS     │   │  AFILIADOS   │   │  FIRMAS CPA  │        │
│   │              │   │              │   │              │        │
│   │  Pagan       │   │  Refieren    │   │  Multi-      │        │
│   │  suscripción │   │  clientes    │   │  empresa     │        │
│   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘        │
│          │                  │                  │                  │
│          ▼                  ▼                  ▼                  │
│   ┌─────────────────────────────────────────────────────┐        │
│   │              PANEL ADMINISTRATIVO                    │        │
│   │   Tenants · Billing · Domains · Infrastructure      │        │
│   │   Partners · Comisiones · Reportes · Analytics       │        │
│   └─────────────────────────────────────────────────────┘        │
│          │                                                        │
│          ▼                                                        │
│   ┌─────────────────────────────────────────────────────┐        │
│   │            INSTANCIAS POR CLIENTE                    │        │
│   │   ERP · CRM · Inventario · Contabilidad · POS       │        │
│   │   Cada uno con dominio propio y branding             │        │
│   └─────────────────────────────────────────────────────┘        │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### 2.2 Flujos de Ingreso Soportados

| Canal | Descripción | Automatización |
|-------|-------------|----------------|
| **Suscripciones directas** | Clientes contratan planes desde el landing | Checkout + provisioning automático |
| **Partners / Afiliados** | Socios refieren clientes y ganan comisiones | Tracking + dispersión automática |
| **Upselling automático** | Migración de plan por consumo de recursos | Alertas + recomendación inteligente |
| **Servicios adicionales** | Catálogo de servicios y blueprints | Cotización + órdenes de trabajo |
| **Contadores** | Acceso multi-empresa para firmas contables | Portal dedicado con KPIs |

---

## 3. ALCANCE FUNCIONAL DETALLADO

### MÓDULO 1 — Landing Page Dinámica y Marketing

| Feature | Descripción |
|---------|-------------|
| Landing principal | 11 secciones completamente dinámicas (Hero, Features, Pricing, Partners, Testimonios, etc.) |
| Design System | Sistema de diseño consistente con tokens de color, tipografía y componentes reutilizables |
| Landing de Partners | URLs personalizadas por partner (`/plt/{slug}`) con branding propio |
| Landing de Contadores | Página dedicada para firmas CPA con propuesta de valor diferenciada |
| SEO & Meta Tags | Open Graph, Twitter Cards, Schema.org JSON-LD, hreflang multi-idioma |
| CMS Backend | Gestión de secciones, testimonios y traducciones desde el admin |
| Calculadora de Precios | Widget interactivo de estimación de costos con selección de usuarios y período |

### MÓDULO 2 — Sistema de Autenticación y Seguridad

| Feature | Descripción |
|---------|-------------|
| Autenticación JWT | Access + Refresh tokens con rotación automática |
| Roles y Permisos | 4 roles base: Admin, Tenant, Partner, Accountant |
| Login diferenciado | Portales separados por tipo de usuario |
| OAuth2 | Estándar de autenticación industria |
| Auditoría | Log completo de accesos, acciones y cambios |
| Validación de parámetros | Sanitización y validación en todos los endpoints |

### MÓDULO 3 — Gestión Multi-Tenant

| Feature | Descripción |
|---------|-------------|
| Provisioning automático | Creación de instancias desde template en segundos |
| Aislamiento de datos | Cada tenant con base de datos independiente |
| Gestión de ciclo de vida | Crear, suspender, reactivar, eliminar tenants |
| Configuración por tenant | Moneda, timezone, idioma, personalización |
| Onboarding wizard | Asistente de 4 pasos para nuevos clientes |
| Migración de planes | Sistema automático de evaluación y upgrade por consumo |

### MÓDULO 4 — Portal del Tenant (Cliente Final)

| Feature | Descripción |
|---------|-------------|
| Dashboard operativo | Métricas de negocio del tenant |
| Módulo de Ventas | Cotizaciones, órdenes, clientes |
| Inventario | Productos, stock, movimientos |
| Contabilidad | Facturas, cuentas por pagar/cobrar, asientos contables |
| Configuración | Empresa, usuarios, dominios |
| Soporte | Help desk integrado |

### MÓDULO 5 — Dominios Personalizados y Cloudflare

| Feature | Descripción |
|---------|-------------|
| Registro de dominios | Asignar dominios propios a cada tenant |
| Verificación DNS | Validación automática de registros DNS |
| SSL automático | Certificados SSL gestionados por Cloudflare |
| Proxy reverso | Enrutamiento inteligente multi-tenant con Nginx |
| CDN integrado | Distribución de contenido via Cloudflare |
| Tunnel management | Gestión de túneles Cloudflare para infraestructura interna |

### MÓDULO 6 — Facturación y Pagos (Stripe)

| Feature | Descripción |
|---------|-------------|
| Checkout integrado | Flujo de pago con Stripe Checkout |
| Suscripciones recurrentes | Cobro automático mensual/anual |
| Webhooks de pago | Procesamiento automático de eventos (pagos, fallos, cancelaciones) |
| Facturas automáticas | Generación y envío de facturas |
| Múltiples planes | Basic, Professional, Enterprise con precios por usuario |
| Descuentos anuales | Configuración de descuentos por período de facturación |
| Periodo de prueba | Trial configurable por plan (7, 14, 30 días) |

### MÓDULO 7 — Sistema de Pagos y Dispersión a Proveedores

| Feature | Descripción |
|---------|-------------|
| Gestión bancaria dual | Cuenta de ahorros (reserva) + cuenta operativa (pagos) |
| Transferencias ACH | Pagos domésticos a proveedores sin costo |
| Transferencias Wire | Pagos internacionales |
| KYC de proveedores | Validación de cuentas bancarias de beneficiarios |
| Auto-replenish | Recarga automática de cuenta operativa desde reserva |
| Reconciliación | Sincronización automática Stripe ↔ Banco |
| Tesorería | Dashboard de flujo de caja, forecasting y alertas |
| Auditoría financiera | Log completo de cada transacción |

### MÓDULO 8 — Ecosistema de Partners y Afiliados

| Feature | Descripción |
|---------|-------------|
| Portal de Partners | Dashboard con métricas, leads, comisiones y recursos |
| Gestión de Leads | Pipeline completo (Prospecting → Won/Lost) |
| Comisiones automáticas | Cálculo, aprobación y dispersión de comisiones |
| Referral tracking | URLs únicas con parámetro de partner |
| Branding personalizado | Landing page con marca del partner |
| Liquidaciones | Settlements periódicos con detalle de pagos |
| Cotizaciones | Generación de quotes vinculadas a leads |

### MÓDULO 9 — Portal de Contadores

| Feature | Descripción |
|---------|-------------|
| Acceso multi-empresa | Un contador accede a múltiples tenants |
| Dashboard consolidado | KPIs financieros agregados de todos sus clientes |
| Cambio de contexto | Switch seamless entre empresas asignadas |
| Niveles de acceso | Readonly, Read/Write, Full por empresa |
| Invitación de clientes | Solicitar acceso a empresas por email |

### MÓDULO 10 — Infraestructura y Monitoreo

| Feature | Descripción |
|---------|-------------|
| Gestión de nodos | Visualización de servidores (status, CPU, RAM, disco) |
| Gestión de contenedores | Start, stop, restart, delete de containers |
| Métricas en tiempo real | CPU, RAM, disco con alertas por umbral |
| Logs centralizados | Acceso a logs de sistema y aplicación |
| Health checks | Verificación automática de salud de servicios |

### MÓDULO 11 — Internacionalización (i18n)

| Feature | Descripción |
|---------|-------------|
| Soporte bilingüe | Español e inglés completo en toda la plataforma |
| Detección automática | Auto-detect del idioma del navegador |
| Gestión de traducciones | CMS para administrar strings desde el admin |
| API con locale | Todos los endpoints públicos soportan filtro por idioma |
| Persistencia | Preferencia de idioma guardada en localStorage |

### MÓDULO 12 — Panel de Administración

| Feature | Descripción |
|---------|-------------|
| Dashboard de métricas | Revenue (MRR/ARR), clientes, partners, leads, infraestructura |
| CRUD completo | Gestión de todas las entidades del sistema |
| Gestión de planes | Crear, editar, activar/desactivar planes y precios |
| Gestión de usuarios | Administradores, roles, permisos |
| Configuración global | Settings de la plataforma, billing, notificaciones |
| Reportes | Generación de reportes operativos y financieros |
| Audit logs | Registro inmutable de todas las acciones administrativas |

---

## 4. ARQUITECTURA TÉCNICA

### 4.1 Diagrama de Alto Nivel

```
┌──────────────────────────────────────────────────────────────────┐
│                         CAPA DE PRESENTACIÓN                      │
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Landing   │  │ Portal   │  │ Portal   │  │ Admin    │        │
│  │ Pages     │  │ Tenant   │  │ Partner  │  │ Dashboard│        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│           SPA (Svelte/SvelteKit + Tailwind CSS)                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS / REST API
┌──────────────────────────┼───────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                             │
│                                                                    │
│  ┌───────────────────────────────────────────────────────┐       │
│  │  API Gateway (FastAPI + Python)                        │       │
│  │  • Auth (JWT + OAuth2)                                │       │
│  │  • Routing por roles                                  │       │
│  │  • Rate limiting                                      │       │
│  │  • Validación y sanitización                          │       │
│  └───────────────────────────────────────────────────────┘       │
│                                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐       │
│  │ Tenants  │ │ Billing  │ │ Partners │ │ Treasury     │       │
│  │ Service  │ │ Service  │ │ Service  │ │ Manager      │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐       │
│  │ Domains  │ │ Infra    │ │ Payments │ │ Plan         │       │
│  │ Service  │ │ Service  │ │ Processor│ │ Migration    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘       │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                   CAPA DE DATOS E INTEGRACIONES                   │
│                                                                    │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────┐     │
│  │PostgreSQL │  │ Stripe    │  │ Mercury   │  │Cloudflare│     │
│  │(Multi-DB) │  │ (Pagos)   │  │ (Banking) │  │(DNS/CDN) │     │
│  └───────────┘  └───────────┘  └───────────┘  └──────────┘     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐                    │
│  │ Nginx     │  │ SMTP      │  │ S3/Minio  │                    │
│  │ (Proxy)   │  │ (Email)   │  │ (Storage) │                    │
│  └───────────┘  └───────────┘  └───────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Multi-Tenancy

Cada cliente final recibe:
- **Base de datos aislada** (PostgreSQL individual)
- **Dominio personalizado** (con SSL automático)
- **Configuración independiente** (moneda, idioma, timezone, branding)
- **Recursos monitoreados** (storage, usuarios, conexiones)

### 4.3 Seguridad

| Capa | Implementación |
|------|----------------|
| Transporte | HTTPS/TLS 1.2+ via Cloudflare |
| Autenticación | JWT con rotación + OAuth2 |
| Autorización | RBAC (Role-Based Access Control) |
| Datos sensibles | Encriptación AES-256 para datos bancarios |
| API | Rate limiting, validación de inputs, CORS |
| Auditoría | Log inmutable de todas las operaciones |
| Infraestructura | Firewall, IP blocking, segmentación de red |

---

## 5. DESGLOSE DE MÓDULOS Y ESTIMACIÓN DE HORAS

> **Nota de eficiencia:** Las horas reflejan un equipo con experiencia comprobada en este tipo de plataformas, utilizando componentes y patrones de arquitectura previamente validados en producción. Esto permite entregar en tiempos significativamente menores a un desarrollo "desde cero".

### Resumen General

| # | Módulo | Horas Estimadas | Complejidad |
|---|--------|----------------|-------------|
| 1 | Landing Page Dinámica y Marketing | 56 h | Media |
| 2 | Sistema de Autenticación y Seguridad | 36 h | Alta |
| 3 | Gestión Multi-Tenant y Provisioning | 72 h | Alta |
| 4 | Portal del Tenant (Cliente Final) | 80 h | Alta |
| 5 | Dominios Personalizados y Cloudflare | 40 h | Media-Alta |
| 6 | Facturación y Pagos (Stripe) | 48 h | Alta |
| 7 | Sistema de Pagos y Dispersión | 56 h | Alta |
| 8 | Ecosistema de Partners y Afiliados | 48 h | Media-Alta |
| 9 | Portal de Contadores | 28 h | Media |
| 10 | Infraestructura y Monitoreo | 32 h | Media-Alta |
| 11 | Internacionalización (i18n) | 24 h | Media |
| 12 | Panel de Administración | 68 h | Alta |
| — | **Testing, QA y Documentación** | **48 h** | — |
| — | **DevOps, CI/CD y Deployment** | **32 h** | Media |
| — | **Gestión de Proyecto y Reuniones** | **32 h** | — |
| | **TOTAL** | **700 h** | |

---

### Detalle por Módulo

#### MÓDULO 1 — Landing Page Dinámica y Marketing (56 h)

| Tarea | Horas | Detalle |
|-------|-------|---------||
| Design System + branding ImpulseMax | 6 h | Tokens, paleta, tipografía, componentes Tailwind |
| NavBar + Hero + Stats dinámicas | 6 h | Responsive, language toggle, API stats |
| Secciones centrales (Social Proof, Features, How It Works) | 8 h | 4 secciones con componentes reutilizables |
| Pricing Preview + Calculadora | 8 h | Selector usuarios, toggle período, API de cálculo |
| Partners + Testimonios + Footer + CTA | 8 h | Secciones finales del landing |
| Landing de Partners (white-label) | 8 h | Rutas dinámicas `/plt/{slug}`, branding |
| Landing de Contadores | 4 h | Secciones específicas para CPAs |
| SEO + CMS Backend | 8 h | Meta tags dinámicos, admin de contenido |

#### MÓDULO 2 — Autenticación y Seguridad (36 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Sistema JWT (access + refresh tokens) | 8 h | Generación, validación, rotación |
| Login/Signup UI (3 tabs) | 8 h | Login, registro, recuperación |
| Middleware + RBAC (4 roles) | 8 h | Guards, decoradores, permisos |
| OAuth2 + Validación de inputs | 6 h | Estándar industry + sanitización |
| Auditoría de accesos | 6 h | Logs, IP, user-agent |

#### MÓDULO 3 — Gestión Multi-Tenant (72 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Motor de provisioning + scripts | 14 h | Clonado DB template, post-config, shell scripts |
| CRUD Tenants + ciclo de vida | 12 h | Crear, listar, suspender, eliminar, estados |
| Onboarding Wizard (4 pasos) | 10 h | UI + lógica de flujo + validaciones |
| Aislamiento de datos + config por tenant | 10 h | Conexiones dinámicas, moneda, timezone, idioma |
| Migración de planes + storage monitor | 10 h | Evaluación consumo, umbrales, auto-upgrade |
| Integración con ERP backend | 8 h | dbfilter, proxy_mode, multi-DB |
| API de configuración | 8 h | Endpoints REST de configuración |

#### MÓDULO 4 — Portal del Tenant (80 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Dashboard operativo + KPIs | 10 h | Métricas de negocio, gráficos |
| Módulo de Ventas (cotizaciones, órdenes, clientes) | 16 h | Pipeline completo |
| Módulo de Inventario (productos, stock) | 12 h | Productos, categorías, movimientos |
| Módulo de Contabilidad (facturas, CxP, CxC) | 16 h | Asientos, reportes básicos |
| Configuración + usuarios + dominios | 10 h | Empresa, roles internos, DNS |
| Layout, navegación y responsive | 10 h | Sidebar, breadcrumbs, mobile |
| Help & Support | 6 h | FAQ, documentación integrada |

#### MÓDULO 5 — Dominios y Cloudflare (40 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| API dominios + Cloudflare integration | 10 h | CRUD, DNS, zonas, SSL automático |
| Proxy reverso multi-tenant (Nginx) | 10 h | Server blocks, maps, rewrites |
| Tunnel management + CDN | 10 h | Cloudflare Tunnels, cache headers |
| Scripts de sync + verificación | 10 h | DNS propagation, health checks |

#### MÓDULO 6 — Facturación y Stripe (48 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Stripe Checkout + suscripciones | 10 h | Sessions, crear/actualizar/cancelar |
| Webhook handlers | 10 h | payment_intent, invoice, subscription events |
| UI facturación + planes | 10 h | Admin de facturas, CRUD planes, sync Stripe |
| Métricas financieras (MRR/ARR/churn) | 8 h | Dashboard financiero |
| Fallos de pago + config billing | 10 h | Reintentos, dunning, templates |

#### MÓDULO 7 — Pagos y Dispersión (56 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Cliente bancario + dual accounts | 12 h | Mercury API, Savings + Checking, auto-replenish |
| Orquestador + endpoints REST | 14 h | Routing, comisiones, 25 endpoints |
| KYC proveedores + validaciones | 10 h | Cuentas bancarias, estados, ACH/Wire |
| Reconciliación + tesorería | 10 h | Sync Stripe↔Mercury, cash flow, forecasting |
| Auditoría financiera | 10 h | Log inmutable, alertas de balance |

#### MÓDULO 8 — Partners y Afiliados (48 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Portal Partners (Dashboard + métricas) | 10 h | Referrals, performance, comisiones |
| Leads Pipeline (5 etapas) | 10 h | Drag & drop, notas, follow-ups |
| Comisiones + referral tracking | 10 h | Cálculo, aprobación, URLs únicas |
| CRUD Partners + branding | 10 h | Admin, logo, colores, landing |
| Cotizaciones + dispersión | 8 h | Quotes, integración con pagos |

#### MÓDULO 9 — Portal de Contadores (28 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Landing + Dashboard multi-empresa | 10 h | KPIs consolidados, switch contexto |
| Gestión de accesos + niveles | 10 h | Readonly, readwrite, full + invitaciones |
| Endpoints + UI del portal | 8 h | REST API + lista empresas, navegación |

#### MÓDULO 10 — Infraestructura y Monitoreo (32 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Dashboard nodos + contenedores | 10 h | Status, CRUD, start/stop/restart |
| Métricas tiempo real + Proxmox | 12 h | CPU, RAM, disco, gauges, API Proxmox |
| Alertas de storage + logs | 10 h | Umbrales, notificaciones, centralized logs |

#### MÓDULO 11 — Internacionalización (24 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Framework i18n + diccionarios EN/ES | 8 h | 185+ keys, auto-detect, persistencia |
| API locale + migraciones BD | 8 h | Query params, modelos con locale |
| Admin traducciones + testing | 8 h | CRUD strings, aprobación, verificación |

#### MÓDULO 12 — Panel de Administración (68 h)

| Tarea | Horas | Detalle |
|-------|-------|---------|
| Dashboard métricas (Revenue, KPIs) | 12 h | MRR/ARR, clientes, partners, pipeline |
| CRUDs core (Tenants + Clients + Partners) | 14 h | Lista, crear, editar, suspender |
| Leads + Quotations + Billing | 14 h | Pipeline, facturas, settlements |
| Work Orders + Reports + Audit | 10 h | Órdenes, reportes, logs auditoría |
| Settings + Plans + Roles | 10 h | Config global, planes, permisos |
| CMS (Landing Sections + Testimonials) | 8 h | Contenido dinámico del landing |

---

## 6. CRONOGRAMA DE IMPLEMENTACIÓN

### Vista General (5 Fases — 24 semanas / 6 meses)

```
MES        1           2           3           4           5           6
SEMANA   1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
─────────────────────────────────────────────────────────────────────────────────────
FASE 1   ████████████████████                         Core + Auth + Tenants + Landing
FASE 2                     ████████████████████        Billing + Payments + Domains
FASE 3                                        ████████████████  Partners + Portales
FASE 4                                                       ████████  Admin + i18n
FASE 5                                                              ████  QA + Deploy
```

> **Ritmo sostenible:** El cronograma de 6 meses permite un desarrollo a ritmo constante (~29 h/semana), asegurando calidad sin burnout del equipo y espacio para iteraciones con feedback de Techeels.

### Fase 1: Fundamentos (Semanas 1-6 / Mes 1-1.5) — 196 h
- Setup de proyecto y arquitectura base
- Sistema de autenticación JWT + RBAC
- Motor de provisioning multi-tenant
- Onboarding wizard + Portal básico del tenant
- Landing page principal + Design System

### Fase 2: Monetización (Semanas 7-12 / Mes 2-3) — 184 h
- Integración completa Stripe (checkout, suscripciones, webhooks)
- Sistema bancario dual (Mercury)
- Pagos y dispersión a proveedores
- Tesorería y reconciliación
- Dominios personalizados + Cloudflare

### Fase 3: Ecosistema (Semanas 13-18 / Mes 3.5-4.5) — 156 h
- Portal de Partners completo + leads pipeline
- Motor de comisiones y referral tracking
- Portal de Contadores multi-empresa
- Portal del Tenant avanzado (Ventas, Inventario, Contabilidad)

### Fase 4: Administración y Pulido (Semanas 19-22 / Mes 5) — 100 h
- Panel de administración completo
- Infraestructura y monitoreo
- Internacionalización (EN/ES)
- CMS, SEO y optimización

### Fase 5: Lanzamiento (Semanas 23-24 / Mes 6) — 64 h
- Testing integral (unit, integration, E2E)
- QA y corrección de bugs
- Documentación técnica y de usuario
- CI/CD pipeline + deployment a producción
- Training y handover

---

## 7. PROPUESTA ECONÓMICA

### Tarifa y Modelo de Costos

> **Modelo nearshore (RD → US):** Nuestro equipo opera desde República Dominicana con estándares de calidad US, lo que permite ofrecer tarifas altamente competitivas sin comprometer la calidad ni la comunicación.

### Opción A — Proyecto Completo (Recomendada)

| Concepto | Detalle |
|----------|---------|
| **Total de Horas** | 700 horas |
| **Tarifa por Hora** | $30 USD |
| **Costo Total del Proyecto** | **$21,000 USD** |
| **Duración Estimada** | 24 semanas (6 meses) |
| **Equipo** | 2 desarrolladores full-stack + 1 DevOps parcial |
| **Ritmo de trabajo** | ~29 horas/semana |

### Esquema de Pagos Sugerido (5 hitos)

| Hito | % | Monto | Trigger |
|------|---|-------|---------|
| Firma del contrato | 20% | $4,200 | Al inicio del proyecto |
| Entrega Fase 1 (Fundamentos) | 20% | $4,200 | Semana 6 — Auth + Tenants + Landing funcional |
| Entrega Fase 2 (Monetización) | 20% | $4,200 | Semana 12 — Billing + Pagos + Dominios |
| Entrega Fase 3 (Ecosistema) | 20% | $4,200 | Semana 18 — Partners + Portales |
| Go-Live (Producción) | 20% | $4,200 | Semana 24 — Plataforma en producción |
| | **100%** | **$21,000** | |

> **Ventaja:** Pagos distribuidos equitativamente cada ~6 semanas, facilitando la planificación financiera de ambas partes.

### Opción B — Por Fases (Flexible)

Para mayor flexibilidad, se puede contratar fase por fase:

| Fase | Horas | Costo |
|------|-------|-------|
| Fase 1: Fundamentos | 196 h | $5,880 |
| Fase 2: Monetización | 184 h | $5,520 |
| Fase 3: Ecosistema | 156 h | $4,680 |
| Fase 4: Admin + Pulido | 100 h | $3,000 |
| Fase 5: Lanzamiento | 64 h | $1,920 |
| **Total** | **700 h** | **$21,000** |

> **Nota:** La contratación por fases individuales puede resultar en un costo total ligeramente superior ($35 USD/h = $24,500 USD) debido a la carga administrativa de gestionar contratos separados.

### Opción C — MVP (Mínimo Viable)

Para un lanzamiento rápido con funcionalidad esencial:

| Módulo | Horas | Incluye |
|--------|-------|---------|
| Auth + Tenants + Onboarding | 108 h | Login, provisioning, wizard |
| Billing (Stripe) | 48 h | Checkout, suscripciones, facturas |
| Landing Page | 40 h | Landing principal, pricing, SEO |
| Admin básico | 50 h | Dashboard, CRUD tenants y clientes |
| Deployment | 34 h | CI/CD, producción, docs |
| **Total MVP** | **280 h** | **$8,400 USD** |
| **Duración** | **10 semanas** | |

> El MVP puede extenderse progresivamente con los módulos restantes.

### Comparativa de Opciones

| | Opción A (Completa) | Opción B (Fases) | Opción C (MVP) |
|---|---|---|---|
| **Inversión** | $21,000 | $21,000 - $24,500 | $8,400 |
| **Tiempo** | 6 meses | 6-7 meses | 10 semanas |
| **Módulos** | 12 completos | 12 (gradual) | 4 esenciales |
| **Pago mensual aprox.** | $3,500/mes | $3,500/mes | $3,360/mes |
| **ROI estimado** | Mes 7 | Mes 8-9 | Mes 3-4 |

---

## 8. ENTREGABLES POR FASE

### Fase 1 — Fundamentos (Semanas 1-6 / Mes 1-1.5)
- [ ] Código fuente del backend (FastAPI + SQLAlchemy)
- [ ] Código fuente del frontend (Svelte + Tailwind)
- [ ] Sistema de autenticación JWT funcional
- [ ] Motor de provisioning multi-tenant
- [ ] Onboarding wizard de 4 pasos
- [ ] Landing page principal con Design System
- [ ] Migraciones de base de datos (Alembic)
- [ ] Documentación de API (OpenAPI/Swagger)

### Fase 2 — Monetización (Semanas 7-12 / Mes 2-3)
- [ ] Integración Stripe completa (checkout + suscripciones)
- [ ] Webhook handlers (pagos, facturas, suscripciones)
- [ ] Sistema bancario dual (Mercury)
- [ ] Módulo de dispersión a proveedores
- [ ] KYC de proveedores + reconciliación
- [ ] Gestión de dominios + Cloudflare + SSL automático

### Fase 3 — Ecosistema (Semanas 13-18 / Mes 3.5-4.5)
- [ ] Portal de Partners completo + leads pipeline
- [ ] Motor de comisiones y referral tracking
- [ ] Portal de Contadores multi-empresa
- [ ] Portal del Tenant mejorado (Ventas, Inventario, Contabilidad)

### Fase 4 — Administración y Pulido (Semanas 19-22 / Mes 5)
- [ ] Panel de administración completo (15+ CRUDs)
- [ ] Dashboard de métricas y analytics
- [ ] Infraestructura y monitoreo
- [ ] i18n completo (EN/ES)
- [ ] CMS, SEO, optimización de performance

### Fase 5 — Lanzamiento (Semanas 23-24 / Mes 6)
- [ ] Suite de tests (unit, integration, E2E)
- [ ] Pipeline CI/CD configurado
- [ ] Deployment a producción
- [ ] Documentación técnica completa
- [ ] Manual de usuario y administrador
- [ ] Training session (2 horas)
- [ ] Handover completo del proyecto

---

## 9. STACK TECNOLÓGICO

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Frontend** | Svelte 4 + SvelteKit | Framework moderno, reactive, excelente performance |
| **Styling** | Tailwind CSS | Utility-first, consistencia, responsive nativo |
| **Backend** | FastAPI (Python 3.11+) | Async, auto-documentación, alto rendimiento |
| **ORM** | SQLAlchemy 2.0 | Madurez, soporte multi-DB, migrations |
| **Base de Datos** | PostgreSQL 15+ | Multi-tenant, JSONB, extensible, enterprise-grade |
| **Migraciones** | Alembic | Versionado de schema, rollbacks |
| **Autenticación** | JWT + OAuth2 | Estándar industria, stateless |
| **Pagos** | Stripe API | Líder en procesamiento de pagos SaaS |
| **Banking** | Mercury Banking API | Cuentas business US, ACH/Wire nativo |
| **DNS/CDN** | Cloudflare | SSL, proxy, tunnels, edge performance |
| **Proxy** | Nginx | Reverse proxy, load balancing, SSL termination |
| **Email** | SMTP / SendGrid | Transaccional + marketing |
| **Storage** | S3 / Minio | Object storage escalable |
| **Monitoreo** | Sentry + Prometheus | Error tracking + métricas |
| **Containerización** | Docker | Aislamiento, reproducibilidad |
| **Orquestación** | Proxmox / Kubernetes | Gestión de infraestructura |
| **CI/CD** | GitHub Actions | Automatización de builds y deploys |

---

## 10. GARANTÍAS Y SOPORTE POST-LANZAMIENTO

### Garantía Incluida

| Elemento | Detalle |
|----------|---------|
| **Período de garantía** | 90 días posterior al go-live |
| **Cobertura** | Corrección de bugs y defectos de desarrollo |
| **Tiempo de respuesta** | Críticos: 4 horas / Altos: 24 horas / Medios: 48 horas |
| **Canal** | Ticket system + comunicación directa |

### Soporte Post-Garantía (Opcional)

| Plan | Horas/Mes | Costo Mensual | Incluye |
|------|-----------|---------------|---------|
| **Básico** | 10 h | $300 USD | Mantenimiento, bug fixes, actualizaciones menores |
| **Profesional** | 20 h | $550 USD | Lo anterior + nuevas features menores + optimización |
| **Enterprise** | 40 h | $1,000 USD | Lo anterior + desarrollo de nuevos módulos + soporte prioritario |

---

## 11. TÉRMINOS Y CONDICIONES SUGERIDOS

### Propiedad Intelectual
- El código fuente desarrollado será **propiedad de Techeels** una vez completado el pago total
- Se entregará acceso completo al repositorio de código
- Licencias de terceros (Stripe, Cloudflare, etc.) son responsabilidad del cliente

### Confidencialidad
- Ambas partes firmarán NDA previo al inicio del proyecto
- No se divulgará información propietaria de ninguna de las partes

### Cambios de Alcance
- Cambios dentro del ±10% del alcance original se absorben sin costo adicional
- Cambios superiores al 10% se cotizarán como addendum al contrato
- Todo cambio de alcance debe ser aprobado por ambas partes por escrito

### Cancelación
- En caso de cancelación, se factura el trabajo completado hasta la fecha
- Entregables completados se entregan al cliente

---

## 12. ANEXOS

### Anexo A — Glosario

| Término | Definición |
|---------|------------|
| **Tenant** | Instancia aislada de la plataforma para un cliente final |
| **Provisioning** | Proceso de creación automática de un nuevo tenant |
| **White-Label** | Plataforma sin marca del desarrollador, personalizable por el operador |
| **MRR** | Monthly Recurring Revenue — Ingreso recurrente mensual |
| **ARR** | Annual Recurring Revenue — Ingreso recurrente anual |
| **ACH** | Automated Clearing House — Transferencia bancaria doméstica (US) |
| **KYC** | Know Your Customer — Validación de identidad de proveedor/beneficiario |
| **SPA** | Single Page Application — Aplicación web de una sola página |
| **JWT** | JSON Web Token — Estándar de autenticación basado en tokens |
| **RBAC** | Role-Based Access Control — Control de acceso basado en roles |
| **i18n** | Internationalization — Soporte multi-idioma |

### Anexo B — Métricas de Complejidad

| Métrica | Valor |
|---------|-------|
| Endpoints REST totales | 80+ |
| Modelos de base de datos | 25+ |
| Componentes de frontend | 50+ |
| Páginas/Vistas | 30+ |
| Integraciones externas | 6 (Stripe, Mercury, Cloudflare, SMTP, S3, Proxmox) |
| Roles de usuario | 4 (Admin, Tenant, Partner, Accountant) |
| Idiomas soportados | 2 (EN, ES) |

### Anexo C — Supuestos

1. Techeels proporcionará acceso a cuentas de servicios terceros (Stripe, Cloudflare, Mercury)
2. La infraestructura de servidores será provista por Techeels o gestionada conjuntamente
3. Los contenidos de marketing (textos, imágenes, testimonios) serán provistos por Techeels
4. Las revisiones de diseño tendrán un máximo de 2 rondas de iteración por entregable
5. La comunicación será fluida con reuniones semanales de seguimiento

---

## CONTACTO

**Equipo de Desarrollo**  
📧 Disponible bajo solicitud  
📅 Inicio disponible: Inmediato, sujeto a firma de contrato

---

*Este documento es una propuesta ajustada al mercado nearshore RD/US. Los valores, tiempos y alcances son estimaciones optimizadas basadas en componentes probados en producción y están sujetos a ajuste tras la validación técnica detallada con Techeels.*
