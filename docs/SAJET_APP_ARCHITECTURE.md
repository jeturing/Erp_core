# SAJET ERP - Arquitectura Completa de la Aplicación

## 1. DIAGRAMA DE FLUJO GENERAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SAJET ERP PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐        │
│  │   USUARIOS NO    │   │   USUARIOS       │   │   USUARIOS       │        │
│  │   AUTENTICADOS   │   │   AUTENTICADOS   │   │   AUTENTICADOS   │        │
│  │                  │   │                  │   │                  │        │
│  │  - Público       │   │  - Tenant        │   │  - Partner       │        │
│  │  - Landing       │   │  - Admin/Gerente │   │  - Accountant    │        │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘        │
│         │                       │                       │                   │
│         ▼                       ▼                       ▼                   │
│  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐        │
│  │     LANDING      │   │  PORTAL TENANT   │   │ PARTNER PORTAL   │        │
│  │  - Marketing     │   │  - Operativo     │   │ - Affiliates     │        │
│  │  - Precios       │   │  - Reportes      │   │ - Comisiones     │        │
│  │  - Features      │   │  - Dominios      │   │ - Leads          │        │
│  └──────────────────┘   └──────────────────┘   └──────────────────┘        │
│         │                       │                       │                   │
│  ┌──────┴───────┐        ┌──────┴───────┐        ┌──────┴───────┐         │
│  │ Login         │        │ Onboarding   │        │ Accountant   │         │
│  │ Signup        │        │ Completado?  │        │ Portal       │         │
│  └──────┬───────┘        └──────┬───────┘        └──────┬───────┘         │
│         │                       │                       │                   │
│         │         ┌─────────────┘                       │                   │
│         │         │                                     │                   │
│         └─────────┼─────────────────────────────────────┘                   │
│                   │                                                         │
│                   ▼                                                         │
│          ┌─────────────────┐                                               │
│          │  ADMIN DASHBOARD│                                               │
│          │  (Super Admin)  │                                               │
│          └────────┬────────┘                                               │
│                   │                                                         │
└───────────────────┼─────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬──────────┬────────────┬──────────┬──────────┐
        │           │           │          │            │          │          │
        ▼           ▼           ▼          ▼            ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌─────┐ ┌──────┐
    │ Clientes│ │Partners│ │ Leads    │ │Billings │ │Tenants   │ │Infra│ │Otros │
    │ Config  │ │Comisio │ │Quotas    │ │Invoices │ │Dominios  │ │Túnl │ │Módls │
    └────────┘ └────────┘ └──────────┘ └─────────┘ └──────────┘ └─────┘ └──────┘
```

---

## 2. ESTRUCTURA DE RUTAS Y COMPONENTES

### 2.1 Landing Page (`Landing.svelte`)
**Ruta:** `/#/` o raíz  
**Acceso:** Público (sin autenticación)

#### Secciones del Landing:

```
┌─ LANDING PAGE ────────────────────────────────────────────┐
│                                                             │
├─ NavBar                                                    │
│  ├─ Logo + Branding                                        │
│  ├─ Nav Links: Features | Pricing | Partners | Resources  │
│  ├─ Link: Onboarding (#/customer-onboarding)              │
│  ├─ CTA: Ser Socio (#/partner-signup)                     │
│  ├─ Language Selector (EN/ES)                              │
│  ├─ Login Button                                           │
│  └─ Get Started CTA                                        │
│                                                             │
├─ Hero Section                                              │
│  ├─ Main CTA (Get Started / Start Free Trial)              │
│  └─ Stats Display (empresas, usuarios, etc.)               │
│                                                             │
├─ Social Proof                                              │
│  └─ Testimonios / Logos de clientes                        │
│                                                             │
├─ Value Proposition                                         │
│  └─ Beneficios principales                                │
│                                                             │
├─ Features Grid (#features)                                 │
│  └─ Catálogo de características                            │
│                                                             │
├─ How It Works                                              │
│  └─ Pasos del onboarding / setup                           │
│                                                             │
├─ Pricing Preview (#pricing)                                │
│  ├─ 3 Plans (Basic, Pro, Enterprise)                       │
│  └─ Features por plan                                      │
│                                                             │
├─ For Partners Section (#partners)                         │
│  ├─ Partner signup (#/partner-signup)                      │
│  ├─ Affiliate program                                      │
│  └─ Benefits                                               │
│                                                             │
├─ Accountants Summary                                       │
│  ├─ Accounting features                                    │
│  └─ CTA to Accountants Landing                             │
│                                                             │
├─ Testimonials                                              │
│  └─ Customer stories                                       │
│                                                             │
├─ Final CTA                                                 │
│  └─ Last conversion opportunity                            │
│                                                             │
└─ Footer                                                    │
   ├─ Links útiles                                           │
   ├─ Redes sociales                                         │
   └─ Legal info                                             │
└────────────────────────────────────────────────────────────┘
```

**ACTUALIZADO:** El Landing incluye enlaces directos:
- ✓ Onboarding de cliente (Customer Onboarding)
- ✓ Signup de nuevos partners

---

### 2.2 Login/Signup (`Login.svelte`)
**Ruta:** `/#/login`

```
┌─ LOGIN PAGE ──────────────────────────────────┐
│                                                │
├─ Tabs: Login | Sign Up | Forgot Password      │
│                                                │
├─ Login Tab                                    │
│  ├─ Email/Username                            │
│  ├─ Password                                  │
│  ├─ Remember Me                               │
│  └─ Login Button                              │
│                                                │
├─ Sign Up Tab                                  │
│  ├─ Nombre                                    │
│  ├─ Email                                     │
│  ├─ Password                                  │
│  ├─ Empresa                                   │
│  ├─ Plan Selection (Basic/Pro/Enterprise)     │
│  └─ Sign Up Button                            │
│                                                │
└─ Forgot Password                              │
   └─ Email recovery flow                       │
└─────────────────────────────────────────────┘
```

---

### 2.3 Customer Onboarding (`CustomerOnboarding.svelte`)
**Ruta:** `/#/customer-onboarding`  
**Acceso:** Solo Tenants con `onboarding_step < 4`

```
┌─ CUSTOMER ONBOARDING WIZARD ──────────────────────┐
│                                                    │
│ Step 1: Información de Empresa                     │
│  ├─ Nombre empresa                                │
│  ├─ RNC / Tax ID                                  │
│  └─ Sector / Industria                            │
│                                                    │
│ Step 2: Configuración Básica                      │
│  ├─ Currency                                      │
│  ├─ Timezone                                      │
│  └─ Idioma                                        │
│                                                    │
│ Step 3: Dominio                                   │
│  ├─ Asignar dominio público                       │
│  └─ Verificar DNS                                 │
│                                                    │
│ Step 4: Confirmación                              │
│  ├─ Review de configuración                       │
│  └─ Completar onboarding                          │
│                                                    │
│ ─────────────────────────────────────────────    │
│ Redirige a: TenantPortal (cuando onboarding_step = 4)
└────────────────────────────────────────────────┘
```

---

### 2.4 Tenant Portal (`TenantPortal.svelte`)
**Ruta:** `/#/portal`  
**Acceso:** Usuarios con rol `tenant`

```
┌─ TENANT PORTAL (OPERATIVO) ────────────────────┐
│                                                  │
├─ Sidebar Navigation                             │
│  ├─ Dashboard                                   │
│  ├─ Sales                                       │
│  │  ├─ Quotations                               │
│  │  ├─ Orders                                   │
│  │  └─ Customers                                │
│  ├─ Inventory                                   │
│  │  ├─ Products                                 │
│  │  └─ Stock                                    │
│  ├─ Accounting                                  │
│  │  ├─ Invoices                                 │
│  │  ├─ Bills                                    │
│  │  └─ Journal Entries                          │
│  ├─ Settings                                    │
│  │  ├─ Company                                  │
│  │  ├─ Users                                    │
│  │  └─ Domains ◄─── ONBOARDING LINK             │
│  └─ Help & Support                              │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

### 2.5 Partner Portal (`PartnerPortal.svelte`)
**Ruta:** `/#/partner-portal`  
**Acceso:** Usuarios con rol `partner`

```
┌─ PARTNER PORTAL (AFFILIATES) ─────────────────┐
│                                                │
├─ Dashboard                                    │
│  ├─ Referrals Count                            │
│  ├─ Commissions YTD                            │
│  └─ Performance Metrics                        │
│                                                │
├─ Leads Management                              │
│  ├─ My Leads                                   │
│  ├─ Lead Status                                │
│  └─ Conversion Tracking                        │
│                                                │
├─ Commissions                                  │
│  ├─ Current Period                             │
│  ├─ History                                    │
│  └─ Payout Info                                │
│                                                │
├─ Resources                                    │
│  ├─ Marketing Materials                        │
│  ├─ API Docs                                   │
│  └─ Training                                   │
│                                                │
└─────────────────────────────────────────────┘
```

---

### 2.6 Admin Dashboard (`Dashboard.svelte`)
**Ruta:** `/#/dashboard`  
**Acceso:** Solo Super Admin

```
┌─ ADMIN DASHBOARD (METRICS & ANALYTICS) ────────┐
│                                                  │
├─ Header                                         │
│  ├─ Greeting: "Welcome, {username}"             │
│  ├─ Current date                                │
│  └─ Last updated time                           │
│                                                  │
├─ KEY METRICS (Cards):                           │
│  ├─ Revenue (MRR, ARR, Pending)                 │
│  ├─ Customer Count (Active, Suspended)          │
│  ├─ Partner Count (Active, Pending)             │
│  ├─ Leads Pipeline (Value, Count)               │
│  ├─ Infrastructure Health (Nodes, Containers)   │
│  ├─ Work Orders (Open, Completed)               │
│  ├─ Settlements (Open, Closed)                  │
│  ├─ Commissions (Total, Pending, Paid)          │
│  ├─ Invoices (Paid, Pending, Total Amount)      │
│  ├─ Reconciliation (Issues, Clean)              │
│  └─ System Health (CPU, RAM, Disk)              │
│                                                  │
├─ CHARTS & TRENDS:                               │
│  ├─ Revenue Trend (MRR vs previous)             │
│  ├─ Customer Growth                             │
│  ├─ Plan Distribution (Pie chart)               │
│  ├─ CPU/RAM/Disk Usage (Gauge)                  │
│  └─ Recent Activity Log                         │
│                                                  │
└──────────────────────────────────────────────┘
```

---

## 3. MÓDULOS ADMINISTRATIVOS

### 3.1 Layout & Navigation
```
┌─ LAYOUT (Sidebar + Content) ────────────────┐
│                                              │
├─ Header                                     │
│  ├─ Logo                                    │
│  ├─ Search Bar                              │
│  └─ User Profile + Notifications            │
│                                              │
├─ Sidebar Menu                               │
│  ├─ Dashboard                               │
│  ├─ PLATFORM MANAGEMENT                     │
│  │  ├─ Tenants                              │
│  │  ├─ Domains                              │
│  │  ├─ Infrastructure                       │
│  │  ├─ Tunnels (Cloudflare)                 │
│  │  └─ Roles & Permissions                  │
│  ├─ CUSTOMER MANAGEMENT                     │
│  │  ├─ Clients (Tenants)                    │
│  │  ├─ Leads                                │
│  │  ├─ Quotations                           │
│  │  ├─ Customer Onboarding Config           │
│  │  └─ Agreements                           │
│  ├─ PARTNER MANAGEMENT                      │
│  │  ├─ Partners (Affiliates)                │
│  │  ├─ Commissions                          │
│  │  ├─ Partner Landing Pages                │
│  │  └─ Partner Branding                     │
│  ├─ BILLING & FINANCE                       │
│  │  ├─ Billing                              │
│  │  ├─ Invoices                             │
│  │  ├─ Settlements                          │
│  │  ├─ Reconciliation                       │
│  │  └─ Dispersion                           │
│  ├─ OPERATIONS                              │
│  │  ├─ Work Orders                          │
│  │  ├─ Service Catalog                      │
│  │  ├─ Blueprints                           │
│  │  └─ Communications                       │
│  ├─ REPORTING & ANALYTICS                   │
│  │  ├─ Reports                              │
│  │  ├─ Audit Logs                           │
│  │  └─ Activity Logs                        │
│  ├─ CONTENT & MARKETING                     │
│  │  ├─ Landing Sections                     │
│  │  ├─ Testimonials                         │
│  │  ├─ Branding                             │
│  │  └─ Translations (i18n)                  │
│  └─ SYSTEM                                  │
│     ├─ Plans Management                     │
│     ├─ Seats Management                     │
│     ├─ Admin Users                          │
│     ├─ Settings                             │
│     └─ Billing Settings                     │
│                                              │
├─ Main Content Area                          │
│  └─ Page-specific components                │
│                                              │
└──────────────────────────────────────────┘
```

---

### 3.2 Detalle de Módulos Principales

#### **TENANTS** (`Tenants.svelte`)
```
├─ List View
│  ├─ Name
│  ├─ Status (active, suspended, provisioning)
│  ├─ Plan
│  ├─ Domain
│  ├─ Created Date
│  └─ Actions (Edit, Suspend, Delete, View Portal)
├─ Create/Edit Form
│  ├─ Name
│  ├─ Email
│  ├─ Plan Selection
│  └─ Database Assignment
└─ Bulk Actions
   ├─ Suspend
   ├─ Activate
   └─ Export
```

#### **DOMAINS** (`Domains.svelte`)
```
├─ List View
│  ├─ Domain Name
│  ├─ Assigned Tenant
│  ├─ Status (active, pending_verification, expired)
│  ├─ Type (primary, subdomain, custom)
│  ├─ SSL Status
│  └─ Actions
├─ Register New Domain
│  ├─ Domain Name
│  ├─ Tenant Selection
│  ├─ Auto-renewal settings
│  └─ Privacy settings
└─ DNS Management
   ├─ Records viewer
   └─ Verification status
```

#### **INFRASTRUCTURE** (`Infrastructure.svelte`)
```
├─ Nodes View
│  ├─ Node Status (online, offline)
│  ├─ CPU/RAM/Disk Usage
│  ├─ Container Count
│  └─ Last Health Check
├─ Containers View
│  ├─ Container Name/ID
│  ├─ Status
│  ├─ Resource Usage
│  └─ Actions (Start, Stop, Restart, Delete)
├─ Resource Metrics
│  ├─ Total CPU (used/total)
│  ├─ Total RAM (used/total)
│  ├─ Total Disk (used/total)
│  └─ Alerts threshold settings
└─ Logs & Monitoring
   └─ Real-time system health
```

#### **CLIENTS** (`Clients.svelte`)
```
├─ Clients List
│  ├─ Company Name
│  ├─ Contact
│  ├─ Email
│  ├─ Plan
│  ├─ MRR/ARR
│  ├─ Status
│  └─ Actions
├─ Client Details
│  ├─ Company Info
│  ├─ Billing Info
│  ├─ Subscription Status
│  ├─ Usage Metrics
│  └─ Linked Tenant
└─ Client Management
   ├─ Upgrade/Downgrade
   ├─ Suspend
   ├─ Terminate
   └─ Send Communication
```

#### **PARTNERS** (`Partners.svelte`)
```
├─ Partners List
│  ├─ Partner Name
│  ├─ Contact
│  ├─ Email
│  ├─ Status (active, inactive, pending)
│  ├─ Commission Rate
│  ├─ Total Commissions YTD
│  └─ Actions
├─ Partner Details
│  ├─ Company Info
│  ├─ Banking Info
│  ├─ Commission Structure
│  ├─ Referral Links
│  ├─ Performance Metrics
│  └─ Branding Settings
└─ Partner Actions
   ├─ Create Partner
   ├─ Approve Partner
   ├─ Edit Terms
   └─ Generate Report
```

#### **LEADS** (`Leads.svelte`)
```
├─ Leads Pipeline
│  ├─ Prospecting
│  ├─ Qualified
│  ├─ Proposal Sent
│  ├─ Negotiation
│  └─ Won/Lost
├─ Lead Details
│  ├─ Company Name
│  ├─ Contact Info
│  ├─ Estimated Value
│  ├─ Probability %
│  ├─ Next Action
│  └─ Associated Partner
├─ Lead Management
│  ├─ Create Lead
│  ├─ Move between stages
│  ├─ Add Notes
│  ├─ Schedule Follow-up
│  └─ Convert to Customer
└─ Analytics
   └─ Pipeline Value, Conversion Rate
```

#### **BILLING** (`Billing.svelte`)
```
├─ Billing Summary
│  ├─ Total MRR
│  ├─ Total ARR
│  ├─ Pending Invoices
│  └─ Overdue Invoices
├─ Subscription Management
│  ├─ Active Subscriptions
│  ├─ Renewals
│  ├─ Cancellations
│  └─ Upgrade/Downgrade
├─ Payment Methods
│  ├─ Stripe Integration
│  ├─ Failed Payments
│  └─ Retry Logic
└─ Billing Settings
   └─ Invoice Templates, Tax, etc.
```

#### **INVOICES** (`Invoices.svelte`)
```
├─ Invoice List
│  ├─ Invoice Number
│  ├─ Client
│  ├─ Amount
│  ├─ Status (paid, pending, overdue)
│  ├─ Due Date
│  └─ Actions (View, Send, Void)
├─ Invoice Details
│  ├─ Line Items
│  ├─ Taxes
│  ├─ Total
│  ├─ Payment Status
│  └─ History
├─ Invoice Management
│  ├─ Create Invoice
│  ├─ Email to Client
│  ├─ Mark as Paid
│  └─ Generate Report
└─ Invoice Settings
   └─ Numbering, templates, etc.
```

#### **COMMISSIONS** (`Commissions.svelte`)
```
├─ Commission Tracking
│  ├─ Partner Name
│  ├─ Lead Source
│  ├─ Amount
│  ├─ Status (pending, approved, paid)
│  └─ Pay Date
├─ Commission Details
│  ├─ Calculation Method
│  ├─ Commission Rate %
│  ├─ Base Amount
│  ├─ Deductions
│  └─ Net Commission
├─ Commission Actions
│  ├─ Approve Commission
│  ├─ Mark as Paid
│  └─ Generate Settlement
└─ Partner Commission Summary
   └─ YTD Commissions, Pending, Paid
```

---

## 4. FLUJOS DE USUARIO (USER JOURNEYS)

### 4.1 Journey: Nuevo Cliente (Onboarding)

```
┌─ START: Landing Page ──────────────────────────────────┐
│                                                         │
│  Usuario ve landing page ──► Click "Get Started"       │
│                                ▼                       │
│                           Redirige a Login (Signup)    │
│                                ▼                       │
│  Completa signup (email, nombre, empresa, plan)       │
│           ▼                                             │
│  Sistema crea nuevo Tenant                             │
│           ▼                                             │
│  Redirige a Customer Onboarding wizard                 │
│           ▼                                             │
│  Step 1: Información de Empresa                        │
│  Step 2: Configuración Básica (Idioma, Timezone)       │
│  Step 3: Asignar Dominio                               │
│  Step 4: Confirmación                                  │
│           ▼                                             │
│  Completado ──► Redirige a TenantPortal                │
│           ▼                                             │
│  Cliente comienza a usar la plataforma                 │
│                                                         │
└─ END: Full Access ────────────────────────────────────┘
```

### 4.2 Journey: Nuevo Partner (Affiliate)

```
┌─ START: Landing Page ──────────────────────────────────┐
│                                                         │
│  ✗ NO LINK DIRECTO A PARTNER SIGNUP                    │
│                                                         │
│  Alt flujo: Admin crea partner manualmente             │
│           ▼                                             │
│  Admin ──► Dashboard ──► Partners ──► Create Partner   │
│           ▼                                             │
│  Ingresa datos (nombre, email, comisión, etc.)         │
│           ▼                                             │
│  Envía invitación al email del partner                 │
│           ▼                                             │
│  Partner recibe email y crea cuenta                    │
│           ▼                                             │
│  Partner Portal ──► Accede a dashboard y recursos      │
│                                                         │
│  MEJOR: Crear página dedicated para partner signup     │
│  Ruta: /#/partner-signup o /#/plt/{partner_code}/signup
│                                                         │
└─ END: Partner Active ─────────────────────────────────┘
```

### 4.3 Journey: Flujo de Venta (Admin)

```
┌─ START: Admin Dashboard ──────────────────────────────┐
│                                                        │
│  Admin ──► Leads ──► Crear Lead                       │
│      ▼                                                 │
│  Ingresa: Empresa, Contacto, Monto, Probabilidad     │
│      ▼                                                 │
│  Lead en estado "Prospecting"                         │
│      ▼                                                 │
│  Admin ──► Quotations ──► Crear Quotation             │
│      ▼                                                 │
│  Asocia Lead + Plan + Pricing                         │
│      ▼                                                 │
│  Envía Quotation a cliente                            │
│      ▼                                                 │
│  Lead mueve a "Proposal Sent"                         │
│      ▼                                                 │
│  Cliente acepta ──► Lead mueve a "Won"                │
│      ▼                                                 │
│  Crear Cliente (Client)                               │
│      ▼                                                 │
│  Crear Tenant                                         │
│      ▼                                                 │
│  Crear Subscription (Billing)                         │
│      ▼                                                 │
│  Generar Invoice                                      │
│                                                        │
└─ END: Nuevo cliente onboarding ─────────────────────┘
```

### 4.4 Journey: Partner Commission Tracking

```
┌─ START: Partner Referral ─────────────────────────────┐
│                                                        │
│  Partner ──► Referral Link (unique URL)               │
│      ▼                                                 │
│  Prospecto visits landing con parámetro ?partner=XX   │
│      ▼                                                 │
│  Prospecto completa signup                            │
│      ▼                                                 │
│  Sistema crea Lead + asocia a Partner                 │
│      ▼                                                 │
│  Admin ──► Leads ──► Mueve a "Won"                    │
│      ▼                                                 │
│  Sistema calcula Commission                           │
│      ▼                                                 │
│  Commission ──► Status: "Pending"                     │
│      ▼                                                 │
│  Admin aprueba Commission                             │
│      ▼                                                 │
│  Commission ──► Status: "Approved"                    │
│      ▼                                                 │
│  Sistema genera Settlement                            │
│      ▼                                                 │
│  Payout a Partner (Stripe/Manual)                     │
│      ▼                                                 │
│  Commission ──► Status: "Paid"                        │
│                                                        │
│  Partner puede ver en PartnerPortal                   │
│                                                        │
└─ END: Commission Paid ────────────────────────────────┘
```

---

## 5. COMPONENTES PRINCIPALES (MAPPING)

| Componente | Archivo | Ruta | Rol Acceso | Estado |
|---|---|---|---|---|
| Landing | `Landing.svelte` | `/#/` | Público | ✓ |
| Login/Signup | `Login.svelte` | `/#/login` | Público | ✓ |
| Customer Onboarding | `CustomerOnboarding.svelte` | `/#/customer-onboarding` | Tenant (pending) | ✓ |
| Tenant Portal | `TenantPortal.svelte` | `/#/portal` | Tenant | ✓ |
| Partner Portal | `PartnerPortal.svelte` | `/#/partner-portal` | Partner | ✓ |
| Accountant Portal | `AccountantPortal.svelte` | `/#/accountant-portal` | Accountant | ✓ |
| Admin Dashboard | `Dashboard.svelte` | `/#/dashboard` | Admin | ✓ |
| Tenants Mgmt | `Tenants.svelte` | `/#/tenants` | Admin | ✓ |
| Domains Mgmt | `Domains.svelte` | `/#/domains` | Admin | ✓ |
| Infrastructure | `Infrastructure.svelte` | `/#/infrastructure` | Admin | ✓ |
| Clients Mgmt | `Clients.svelte` | `/#/clients` | Admin | ✓ |
| Partners Mgmt | `Partners.svelte` | `/#/partners` | Admin | ✓ |
| Leads Mgmt | `Leads.svelte` | `/#/leads` | Admin | ✓ |
| Quotations | `Quotations.svelte` | `/#/quotations` | Admin | ✓ |
| Commissions | `Commissions.svelte` | `/#/commissions` | Admin | ✓ |
| Billing | `Billing.svelte` | `/#/billing` | Admin | ✓ |
| Invoices | `Invoices.svelte` | `/#/invoices` | Admin | ✓ |
| Settlements | `Settlements.svelte` | `/#/settlements` | Admin | ✓ |
| Work Orders | `WorkOrders.svelte` | `/#/workorders` | Admin | ✓ |
| Audit Logs | `Audit.svelte` | `/#/audit` | Admin | ✓ |
| Reports | `Reports.svelte` | `/#/reports` | Admin | ✓ |
| Settings | `Settings.svelte` | `/#/settings` | Admin | ✓ |
| Plans Mgmt | `Plans.svelte` | `/#/plans` | Admin | ✓ |
| Roles Mgmt | `Roles.svelte` | `/#/roles` | Admin | ✓ |

---

## 6. ISSUES ENCONTRADOS & RECOMENDACIONES

### 6.1 Enlaces Faltantes en Landing Page

#### ❌ ISSUE 1: No hay enlace directo a Customer Onboarding
**Ubicación:** `Landing.svelte`  
**Descripción:** El landing no tiene un botón/sección que lleve directamente al onboarding de clientes existentes.

**Solución:**
```svelte
<!-- En NavBar o Hero de Landing -->
<a href="#/customer-onboarding" class="btn btn-primary">
  Completa tu Onboarding
</a>

<!-- O en sección separada -->
<section id="onboarding" class="py-12 bg-gray-50">
  <div class="max-w-2xl mx-auto text-center">
    <h2>¿Ya tienes cuenta?</h2>
    <p>Completa tu configuración inicial</p>
    <a href="#/customer-onboarding" class="btn btn-primary">
      Ir al Onboarding
    </a>
  </div>
</section>
```

#### ❌ ISSUE 2: No hay enlace directo a Partner Signup
**Ubicación:** `Landing.svelte` → `ForPartners` component  
**Descripción:** La sección "For Partners" no tiene un botón de signup específico. El flujo actual requiere que un Admin cree el partner manualmente.

**Solución A - Self-Signup (Recomendado):**
```svelte
<!-- Crear nueva ruta: PartnerSignup.svelte -->
<!-- Ruta: /#/partner-signup -->

<!-- Agregar a Landing ForPartners -->
<button href="#/partner-signup" class="btn btn-primary">
  {$t('partners.become_partner')}
</button>
```

**Solución B - Redirigir a Partners con filtro:**
```svelte
<!-- Crear Landing personalizado para partners -->
<!-- Ruta: /#/plt/{partner_code}/signup -->
<!-- Archivo: PartnerLanding.svelte -->
```

---

## 7. DIAGRAM: FULL APP NAVIGATION TREE

```
SAJET_ERP
│
├─ PUBLIC ROUTES (No auth required)
│  ├─ / (Landing Page)
│  │  ├─ NavBar
│  │  ├─ Hero
│  │  ├─ Features Grid
│  │  ├─ Pricing (#pricing)
│  │  ├─ For Partners (#partners) ✓ Partner signup link
│  │  ├─ Accountants Info
│  │  └─ Testimonials
│  ├─ /login (Login/Signup)
│  ├─ /accountants (Accountants Landing)
│  └─ /plt/{slug} (Partner White-Label Landing)
│
├─ PROTECTED ROUTES (Auth required)
│  │
│  ├─ TENANT ROUTES (role: tenant)
│  │  ├─ /customer-onboarding (Wizard)
│  │  └─ /portal (Tenant Dashboard)
│  │     ├─ Sales
│  │     ├─ Inventory
│  │     ├─ Accounting
│  │     ├─ Domains ◄── Access from here
│  │     └─ Settings
│  │
│  ├─ PARTNER ROUTES (role: partner)
│  │  └─ /partner-portal
│  │     ├─ Dashboard (Metrics)
│  │     ├─ My Leads
│  │     ├─ Commissions
│  │     └─ Resources
│  │
│  ├─ ACCOUNTANT ROUTES (role: accountant)
│  │  └─ /accountant-portal
│  │     ├─ Accounting Dashboard
│  │     ├─ Reports
│  │     └─ Audit
│  │
│  └─ ADMIN ROUTES (role: admin)
│     ├─ /dashboard (Analytics)
│     ├─ PLATFORM
│     │  ├─ /tenants
│     │  ├─ /domains
│     │  ├─ /infrastructure
│     │  ├─ /tunnels
│     │  └─ /roles
│     ├─ CUSTOMERS
│     │  ├─ /clients
│     │  ├─ /leads
│     │  ├─ /quotations
│     │  ├─ /customer-onboarding-config
│     │  └─ /agreements
│     ├─ PARTNERS
│     │  ├─ /partners
│     │  ├─ /commissions
│     │  └─ /partner-landing-pages (branding)
│     ├─ BILLING
│     │  ├─ /billing
│     │  ├─ /invoices
│     │  ├─ /settlements
│     │  ├─ /reconciliation
│     │  └─ /dispersion
│     ├─ OPERATIONS
│     │  ├─ /workorders
│     │  ├─ /service-catalog
│     │  ├─ /blueprints
│     │  └─ /communications
│     ├─ REPORTS
│     │  ├─ /reports
│     │  └─ /audit
│     ├─ MARKETING
│     │  ├─ /landing-sections
│     │  ├─ /testimonials
│     │  ├─ /branding
│     │  └─ /translations
│     └─ SYSTEM
│        ├─ /plans
│        ├─ /seats
│        ├─ /admin-users
│        ├─ /settings
│        └─ /logs
│
└─ SPECIAL ROUTES
   ├─ /404 (Not Found)
   └─ /error (Error Handler)
```

---

## 8. TABLA DE CARACTERÍSTICAS POR PLAN

```
┌──────────────┬────────────┬────────────┬──────────────┐
│ Feature      │ BASIC      │ PRO        │ ENTERPRISE   │
├──────────────┼────────────┼────────────┼──────────────┤
│ Users        │ 5          │ 20         │ Unlimited    │
│ Domains      │ 1          │ 5          │ Unlimited    │
│ Storage      │ 10 GB      │ 100 GB     │ Unlimited    │
│ Support      │ Email      │ Priority   │ Dedicated    │
│ Uptime SLA   │ 99.5%      │ 99.9%      │ 99.99%       │
│ API Access   │ ✗          │ ✓          │ ✓            │
│ Custom Domain│ ✗          │ ✓          │ ✓            │
│ SSO          │ ✗          │ ✗          │ ✓            │
│ Integrations │ Basic      │ Advanced   │ Unlimited    │
│ Compliance   │ SOC2       │ SOC2       │ SOC2+Hipaa   │
└──────────────┴────────────┴────────────┴──────────────┘
```

---

## 9. STACK TÉCNICO

```
FRONTEND
├─ Framework: Svelte 4 + SvelteKit
├─ Styling: Tailwind CSS + Custom CSS
├─ Icons: lucide-svelte
├─ i18n: svelte-i18n
├─ State Management: Svelte stores
├─ HTTP: Fetch API
├─ Build: Vite
└─ Package Manager: npm

BACKEND
├─ Framework: FastAPI (Python)
├─ ORM: SQLAlchemy
├─ Database: PostgreSQL
├─ Auth: JWT + OAuth2
├─ Payment: Stripe API
├─ Email: SMTP / SendGrid
├─ Storage: Minio / S3
├─ Monitoring: Sentry
└─ Deployment: Docker + Kubernetes

INFRA
├─ Container: Docker
├─ Orchestration: Kubernetes / Proxmox
├─ DNS/CDN: Cloudflare
├─ Tunneling: Cloudflare Tunnels
├─ Reverse Proxy: Nginx
├─ Database: PostgreSQL (CT137)
├─ Nodes: CT105, CT160, etc.
└─ Monitoring: Wazuh + Prometheus
```

---

## 10. PROXIMO PASOS (TODO)

- [x] Crear diagrama completo de la arquitectura
- [x] **Agregar enlace de onboarding en Landing**
   - Botón en NavBar
   - Vinculado a /#/customer-onboarding
- [ ] **Crear Partner Signup Flow**
   - Ruta base /#/partner-signup (pendiente de formulario)
- [ ] Mejorar documentación de APIs
- [ ] Agregar logs/auditoría detallado
- [ ] Implementar webhook para eventos Stripe
- [ ] Crear tutorial onboarding interactivo
- [ ] Agregar chatbot de soporte

---

## RESUMEN

Esta es la arquitectura completa de **SAJET ERP**:

✓ **Landing Page**: Marketing, precios, features, testimonios  
✓ **Auth System**: Login, signup, roles (tenant, partner, accountant, admin)  
✓ **Tenant Portal**: Acceso al ERP para clientes  
✓ **Partner Portal**: Dashboard de affiliates y comisiones  
✓ **Admin Dashboard**: Todos los módulos de administración  
✓ **Multi-tenant**: Cada cliente con su propia instancia  
✓ **Integración Stripe**: Pagos y billing automático  
✓ **i18n**: Soporte multi-idioma (EN/ES)  

**FALTA:**
❌ Formulario de registro partner (ruta /#/partner-signup pendiente)

