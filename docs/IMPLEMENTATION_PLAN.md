# 📋 Plan de Implementación - ERP Core Frontend & Dominios

## Estado Actual (Febrero 2026)

### ✅ Completado
- [x] Proyecto Svelte + Vite + TypeScript + Tailwind
- [x] Colores corporativos Jeturing (#003B73, #00FF9F)
- [x] Componentes base (Button, Card, Badge, Input, StatCard, Spinner)
- [x] Layout con Sidebar responsive
- [x] Página Login funcional
- [x] Página Dashboard con métricas reales
- [x] Stores (auth, dashboard)
- [x] API Client con autenticación JWT
- [x] Servicios API (dashboard, customers, infrastructure)

### ⏳ Pendiente
- [ ] Páginas CRUD completas
- [ ] Sistema de dominios personalizados
- [ ] Integración con PCT 105 para túneles

---

## 🗂️ Páginas a Implementar

### 1. Customers (Clientes)

**Ruta:** `#/customers`  
**Archivo:** `src/routes/Customers.svelte`

**Funcionalidades:**
- Tabla con paginación y búsqueda
- Filtros: Plan (basic/pro/enterprise), Estado (active/inactive)
- Columnas: Nombre, Email, Empresa, Plan, Estado, Fecha registro
- Acciones: Ver, Editar, Eliminar
- Modal para crear nuevo cliente
- Exportar a CSV

**Sub-página:** `CustomerDetail.svelte`
- Tabs: Información, Dominios, Suscripción, Deployment, Actividad
- Edición inline de datos
- Historial de cambios

---

### 2. Domains (Dominios) ⭐ NUEVO

**Ruta:** `#/domains`  
**Archivo:** `src/routes/Domains.svelte`

**Funcionalidades:**
- Tabla de dominios personalizados
- Columnas: Dominio externo, Subdominio Sajet, Cliente, Estado, SSL
- Estado visual: 🟢 Activo, 🟡 Pendiente, 🔴 Error
- Modal para agregar dominio
- Wizard de configuración DNS con instrucciones copiables
- Verificación de CNAME en tiempo real
- Acciones: Verificar, Activar, Desactivar, Eliminar

**Wizard de nuevo dominio:**
1. Ingresar dominio externo (ej: www.impulse-max.com)
2. Seleccionar cliente asociado
3. Sistema genera subdominio sajet.us automáticamente
4. Mostrar instrucciones DNS para copiar
5. Botón "Verificar configuración"
6. Activación automática al verificar

---

### 3. Infrastructure (Infraestructura)

**Ruta:** `#/infrastructure`  
**Archivo:** `src/routes/Infrastructure.svelte`

**Sub-secciones:**

#### 3.1 Nodes (Nodos Proxmox)
- Cards con métricas de cada nodo
- CPU, RAM, Storage en barras de progreso
- Estado: Online/Offline/Mantenimiento
- Mapa de cluster (visual)

#### 3.2 Containers (Contenedores LXC)
- Tabla de contenedores
- Filtro por nodo
- Estado: Running/Stopped/Paused
- Acciones: Start, Stop, Restart, Console

#### 3.3 Deployments (Despliegues)
- Lista de tenants desplegados
- Subdominio, Contenedor, Nodo, Estado
- Logs de provisioning
- Acciones: Suspender, Reactivar, Eliminar

---

### 4. Billing (Facturación)

**Ruta:** `#/billing`  
**Archivo:** `src/routes/Billing.svelte`

**Funcionalidades:**
- Métricas principales: MRR, ARR, Churn Rate
- Gráfico de ingresos por mes
- Tabla de facturas con filtros
- Eventos de Stripe en tiempo real
- Acciones: Descargar PDF, Reintentar cobro
- Breakdown por plan

**Sub-página:** `InvoiceDetail.svelte`
- Detalle de factura
- Items facturados
- Estado de pago
- Historial de intentos

---

### 5. Tunnels (Cloudflare Tunnels)

**Ruta:** `#/tunnels`  
**Archivo:** `src/routes/Tunnels.svelte`

**Funcionalidades:**
- Lista de túneles activos
- Estado de conexión en tiempo real
- Hostnames asociados
- Acciones: Crear, Reiniciar, Eliminar
- Logs del túnel

---

### 6. Settings (Configuración)

**Ruta:** `#/settings`  
**Archivo:** `src/routes/Settings.svelte`

**Secciones:**

#### 6.1 General
- Nombre de la plataforma
- Logo
- Timezone
- Idioma

#### 6.2 Odoo
- Servidor Odoo por defecto
- Master password
- Versión de Odoo

#### 6.3 Cloudflare
- API Token (masked)
- Zone ID
- Account ID
- Tunnel por defecto

#### 6.4 Stripe
- API Keys (masked)
- Webhook secret
- Precios por plan

#### 6.5 Notificaciones
- Email SMTP
- Templates de email
- Alertas

---

### 7. Logs (Registros)

**Ruta:** `#/logs`  
**Archivo:** `src/routes/Logs.svelte`

**Funcionalidades:**
- Tabs: Provisioning, Application, System
- Filtros por fecha, nivel (info/warning/error)
- Búsqueda en logs
- Auto-refresh cada 5 segundos
- Exportar logs

---

## 🔌 Endpoints API a Implementar

### Dominios (NUEVO)
```
GET    /api/domains                     # Listar dominios
POST   /api/domains                     # Crear dominio
GET    /api/domains/{domain}            # Detalle
DELETE /api/domains/{domain}            # Eliminar
POST   /api/domains/{domain}/verify     # Verificar DNS
POST   /api/domains/{domain}/activate   # Activar
POST   /api/domains/{domain}/deactivate # Desactivar
GET    /api/domains/check/{domain}      # Verificar disponibilidad
```

### Customers (Completar CRUD)
```
GET    /api/customers                   # Listar con paginación
GET    /api/customers/{id}              # Detalle
POST   /api/customers                   # Crear
PATCH  /api/customers/{id}              # Actualizar
DELETE /api/customers/{id}              # Eliminar
GET    /api/customers/{id}/domains      # Dominios del cliente
GET    /api/customers/{id}/invoices     # Facturas del cliente
```

### Subscriptions
```
GET    /api/subscriptions               # Listar
GET    /api/subscriptions/{id}          # Detalle
PATCH  /api/subscriptions/{id}          # Actualizar
POST   /api/subscriptions/{id}/upgrade  # Upgrade de plan
POST   /api/subscriptions/{id}/cancel   # Cancelar
```

### Invoices
```
GET    /api/invoices                    # Listar
GET    /api/invoices/{id}               # Detalle
GET    /api/invoices/{id}/pdf           # Descargar PDF
POST   /api/invoices/{id}/retry         # Reintentar cobro
```

---

## 📊 Modelo de Datos Actualizado

### Nueva tabla: custom_domains

```sql
CREATE TABLE custom_domains (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    tenant_deployment_id INTEGER REFERENCES tenant_deployments(id),
    
    -- Dominios
    external_domain VARCHAR(255) UNIQUE NOT NULL,
    sajet_subdomain VARCHAR(100) UNIQUE NOT NULL,
    
    -- Estado
    verification_status VARCHAR(20) DEFAULT 'pending',
    verification_token VARCHAR(64),
    verified_at TIMESTAMP,
    
    -- Cloudflare
    cloudflare_dns_record_id VARCHAR(50),
    cloudflare_configured BOOLEAN DEFAULT FALSE,
    tunnel_ingress_configured BOOLEAN DEFAULT FALSE,
    
    -- Flags
    is_active BOOLEAN DEFAULT FALSE,
    is_primary BOOLEAN DEFAULT FALSE,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔄 Flujo de Integración PCT 105

### Al crear dominio personalizado:

```
1. POST /api/domains (ERP Core en atenea)
   ↓
2. Validar dominio y generar subdominio
   ↓
3. INSERT en custom_domains (PCT 160)
   ↓
4. Crear DNS record en Cloudflare
   - CNAME: {subdomain}.sajet.us → tunnel.cfargotunnel.com
   ↓
5. Actualizar /etc/cloudflared/config.yml (PCT 105)
   - Agregar ingress rule
   ↓
6. systemctl restart cloudflared (PCT 105)
   ↓
7. Esperar verificación CNAME del cliente
   ↓
8. Activar dominio (is_active = true)
```

### Script de sincronización (cron en PCT 105)

```bash
#!/bin/bash
# /opt/scripts/sync_domains.sh
# Ejecutar cada minuto via cron

# Leer dominios no configurados de la BD
psql -h 10.10.10.20 -U jeturing -d erp_core_db -t -c \
  "SELECT sajet_subdomain, external_domain 
   FROM custom_domains 
   WHERE cloudflare_configured = true 
   AND tunnel_ingress_configured = false"

# Por cada dominio, agregar ingress rule y recargar
```

---

## 📁 Estructura de Archivos Final

```
/opt/Erp_core/frontend/src/
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── customers.ts
│   │   ├── dashboard.ts
│   │   ├── domains.ts          # NUEVO
│   │   ├── infrastructure.ts
│   │   ├── billing.ts          # NUEVO
│   │   └── index.ts
│   ├── components/
│   │   ├── Badge.svelte
│   │   ├── Button.svelte
│   │   ├── Card.svelte
│   │   ├── DataTable.svelte    # NUEVO
│   │   ├── Input.svelte
│   │   ├── Layout.svelte
│   │   ├── Modal.svelte        # NUEVO
│   │   ├── Pagination.svelte   # NUEVO
│   │   ├── Select.svelte       # NUEVO
│   │   ├── StatCard.svelte
│   │   ├── Spinner.svelte
│   │   ├── Tabs.svelte         # NUEVO
│   │   └── index.ts
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── dashboard.ts
│   │   ├── customers.ts        # NUEVO
│   │   ├── domains.ts          # NUEVO
│   │   └── index.ts
│   └── types/
│       └── index.ts
├── routes/
│   ├── Login.svelte
│   ├── Dashboard.svelte
│   ├── Customers.svelte        # NUEVO
│   ├── CustomerDetail.svelte   # NUEVO
│   ├── Domains.svelte          # NUEVO
│   ├── Infrastructure.svelte   # NUEVO
│   ├── Billing.svelte          # NUEVO
│   ├── Tunnels.svelte          # NUEVO
│   ├── Settings.svelte         # NUEVO
│   └── Logs.svelte             # NUEVO
└── App.svelte
```

---

## ⏱️ Cronograma Estimado

| Fase | Tarea | Duración |
|------|-------|----------|
| 1 | Componentes compartidos (Modal, DataTable, etc) | 2 días |
| 2 | Customers CRUD completo | 2 días |
| 3 | Domains (backend + frontend) | 3 días |
| 4 | Infrastructure | 2 días |
| 5 | Billing | 2 días |
| 6 | Settings & Logs | 2 días |
| 7 | Testing & Polish | 2 días |
| **Total** | | **15 días** |

---

## 🎯 Prioridades

1. **ALTA:** Sistema de dominios personalizados (crítico para TecHeels)
2. **ALTA:** CRUD de Customers (base para todo)
3. **MEDIA:** Infrastructure (monitoreo)
4. **MEDIA:** Billing (ingresos)
5. **BAJA:** Settings & Logs (operacional)

---

*Plan creado: Febrero 2026*
*Próxima revisión: Al completar Fase 1*
