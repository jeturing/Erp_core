z# 🌐 Arquitectura de Dominios Personalizados - ERP Core

## Resumen Ejecutivo

Este documento describe la arquitectura para soportar dominios personalizados de clientes como:
- **ImpulseMax** → `impulse-max.sajet.us` (CNAME externo: `www.impulse-max.com`)
- **EvolucionaMujer** → `evolucionamujer.sajet.us` (CNAME externo: `www.evolucionamujer.com`)  
- **TecHeels** → `techeels.sajet.us` (CNAME externo: `www.techeels.io`)

---

## 📊 Arquitectura Seleccionada

### Opción Elegida: Subdominios de sajet.us + CNAME Externo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE DOMINIOS PERSONALIZADOS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   Cliente escribe: www.impulse-max.com                                       │
│          │                                                                    │
│          ▼                                                                    │
│   ┌─────────────────┐                                                        │
│   │  DNS Externo    │  CNAME → impulse-max.sajet.us                         │
│   │  (GoDaddy, etc) │                                                        │
│   └────────┬────────┘                                                        │
│            │                                                                  │
│            ▼                                                                  │
│   ┌─────────────────────────────────────────┐                                │
│   │     Cloudflare (Zone: sajet.us)         │                                │
│   │     Zone ID: 4a83b88793ac3688486ace69b6ae80f9                            │
│   │                                          │                                │
│   │  *.sajet.us → Tunnel: tcs-sajet-tunnel  │                                │
│   └────────────────┬────────────────────────┘                                │
│                    │                                                          │
│                    ▼                                                          │
│   ┌─────────────────────────────────────────┐                                │
│   │   Cloudflare Tunnel (cloudflared)       │                                │
│   │   Tunnel: tcs-sajet-tunnel              │                                │
│   │   Corriendo en: PCT 105 (10.10.10.100)  │                                │
│   └────────────────┬────────────────────────┘                                │
│                    │                                                          │
│                    ▼                                                          │
│   ┌─────────────────────────────────────────┐                                │
│   │   /etc/cloudflared/config.yml           │                                │
│   │                                          │                                │
│   │   ingress:                               │                                │
│   │     - hostname: impulse-max.sajet.us    │                                │
│   │       service: http://10.10.10.X:8069   │                                │
│   │     - hostname: evolucionamujer.sajet.us│                                │
│   │       service: http://10.10.10.Y:8069   │                                │
│   │     - service: http_status:404          │                                │
│   └────────────────┬────────────────────────┘                                │
│                    │                                                          │
│                    ▼                                                          │
│   ┌─────────────────────────────────────────┐                                │
│   │   LXC Container (Odoo Tenant)           │                                │
│   │   Contenedor específico del cliente     │                                │
│   └─────────────────────────────────────────┘                                │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuración de DNS

### IP de sajet.us para apuntar dominios externos

**sajet.us NO tiene IP pública directa** - usa Cloudflare Tunnels.

Para que dominios externos funcionen, el cliente debe configurar un **CNAME**, no un A record:

```dns
; En el DNS del cliente (GoDaddy, Namecheap, etc)
;
; Opción 1: CNAME al subdominio de sajet.us (RECOMENDADO)
www.impulse-max.com.    CNAME   impulse-max.sajet.us.
impulse-max.com.        CNAME   impulse-max.sajet.us.   ; Si soporta CNAME flattening

; Opción 2: CNAME directo al tunnel (alternativa)
www.impulse-max.com.    CNAME   tcs-sajet-tunnel.cfargotunnel.com.
```

### IPs Públicas Disponibles (si se necesita en futuro)

| IP | Estado | Asignación |
|----|--------|------------|
| 208.115.125.26 | 🟢 LIBRE | no usar pertenece a proxmox |
| 208.115.125.27 | 🔴 En uso | LXC 146 (WL-DEPLOY) |
| 208.115.125.28 | 🔴 En uso | LXC 154 (mcp-forensics) |
| 208.115.125.29 | 🔴 En uso | LXC 160 (SRV-Sajet) |
| 208.115.125.30 | 🟢 LIBRE | Reservada para expansión |

---

## 📋 Modelo de Datos: custom_domains

### Nueva Tabla en erp_core_db (PCT 160 - 10.10.10.20)

```sql
CREATE TABLE custom_domains (
    id SERIAL PRIMARY KEY,
    
    -- Relaciones
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    tenant_deployment_id INTEGER REFERENCES tenant_deployments(id) ON DELETE SET NULL,
    
    -- Dominio externo del cliente
    external_domain VARCHAR(255) NOT NULL,           -- ej: "www.impulse-max.com"
    
    -- Subdominio interno de sajet.us (generado automáticamente)
    sajet_subdomain VARCHAR(100) NOT NULL UNIQUE,    -- ej: "impulse-max"
    sajet_full_domain VARCHAR(255) GENERATED ALWAYS AS (sajet_subdomain || '.sajet.us') STORED,
    
    -- Estado de verificación
    verification_status VARCHAR(20) DEFAULT 'pending',  -- pending, verified, failed
    verification_token VARCHAR(64),                     -- Token TXT para verificar propiedad
    verified_at TIMESTAMP,
    
    -- Configuración Cloudflare
    cloudflare_dns_record_id VARCHAR(50),              -- ID del registro DNS en Cloudflare
    cloudflare_configured BOOLEAN DEFAULT FALSE,
    tunnel_ingress_configured BOOLEAN DEFAULT FALSE,
    
    -- SSL (manejado automáticamente por Cloudflare)
    ssl_status VARCHAR(20) DEFAULT 'active',           -- Cloudflare maneja SSL
    
    -- Estado
    is_active BOOLEAN DEFAULT FALSE,
    is_primary BOOLEAN DEFAULT FALSE,                  -- Dominio principal del tenant
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    -- Constraints
    CONSTRAINT unique_external_domain UNIQUE (external_domain),
    CONSTRAINT unique_sajet_subdomain UNIQUE (sajet_subdomain)
);

-- Índices
CREATE INDEX idx_custom_domains_customer ON custom_domains(customer_id);
CREATE INDEX idx_custom_domains_tenant ON custom_domains(tenant_deployment_id);
CREATE INDEX idx_custom_domains_status ON custom_domains(verification_status, is_active);

-- Enum para estados
CREATE TYPE domain_verification_status AS ENUM ('pending', 'verifying', 'verified', 'failed');
```

### Relación con Tablas Existentes

```
┌─────────────┐       ┌──────────────────┐       ┌───────────────────┐
│  customers  │──1:N──│  custom_domains  │──N:1──│ tenant_deployments│
└─────────────┘       └──────────────────┘       └───────────────────┘
     │                        │
     │                        │
     │ id                     │ external_domain: "www.impulse-max.com"
     │ email                  │ sajet_subdomain: "impulse-max"
     │ company_name           │ sajet_full_domain: "impulse-max.sajet.us"
     │                        │ verification_status: "verified"
     └────────────────────────┘
```

---

## 🔄 Flujo de Provisioning de Dominio Personalizado

### Paso 1: Cliente registra dominio en ERP Core

```
POST /api/domains
{
    "external_domain": "www.impulse-max.com",
    "customer_id": 123
}
```

**Backend genera:**
- `sajet_subdomain`: "impulse-max" (sanitizado del dominio)
- `verification_token`: "jeturing-verify-abc123def456"

### Paso 2: Verificación de propiedad (Opcional según plan)

Cliente debe agregar registro TXT en su DNS:
```dns
_jeturing-verify.impulse-max.com.  TXT  "jeturing-verify-abc123def456"
```

ERP Core verifica:
```
POST /api/domains/www.impulse-max.com/verify
```

### Paso 3: Configuración automática en Cloudflare

**3.1 Crear DNS record en zona sajet.us:**
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/4a83b88793ac3688486ace69b6ae80f9/dns_records" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "CNAME",
    "name": "impulse-max",
    "content": "tcs-sajet-tunnel.cfargotunnel.com",
    "proxied": true
  }'
```

**3.2 Agregar ingress rule al tunnel:**
Actualizar `/etc/cloudflared/config.yml` en PCT 105:
```yaml
ingress:
  # ... reglas existentes ...
  - hostname: impulse-max.sajet.us
    service: http://10.10.10.105:8069  # IP del contenedor del tenant
  - service: http_status:404
```

**3.3 Recargar tunnel:**
```bash
systemctl restart cloudflared
```

### Paso 4: Cliente configura CNAME

Cliente agrega en su DNS externo:
```dns
www.impulse-max.com.  CNAME  impulse-max.sajet.us.
```

### Paso 5: Verificación final y activación

```
POST /api/domains/www.impulse-max.com/activate
```

---

## 🗂️ Endpoints API: /api/domains

### Crear dominio personalizado
```http
POST /api/domains
Content-Type: application/json
Authorization: Bearer <token>

{
    "external_domain": "www.impulse-max.com",
    "customer_id": 123,
    "tenant_deployment_id": 45  // opcional
}

Response 201:
{
    "id": 1,
    "external_domain": "www.impulse-max.com",
    "sajet_subdomain": "impulse-max",
    "sajet_full_domain": "impulse-max.sajet.us",
    "verification_status": "pending",
    "verification_token": "jeturing-verify-abc123",
    "verification_instructions": {
        "type": "CNAME",
        "record": "www.impulse-max.com",
        "value": "impulse-max.sajet.us",
        "note": "Configure este CNAME en su proveedor DNS"
    }
}
```

### Listar dominios
```http
GET /api/domains?customer_id=123&status=verified

Response 200:
{
    "items": [
        {
            "id": 1,
            "external_domain": "www.impulse-max.com",
            "sajet_full_domain": "impulse-max.sajet.us",
            "verification_status": "verified",
            "is_active": true,
            "is_primary": true
        }
    ],
    "total": 1
}
```

### Verificar dominio
```http
POST /api/domains/www.impulse-max.com/verify

Response 200:
{
    "status": "verified",
    "message": "Dominio verificado correctamente",
    "cname_detected": "impulse-max.sajet.us",
    "next_step": "El dominio está activo y funcionando"
}

Response 400:
{
    "status": "failed",
    "message": "CNAME no detectado",
    "expected": "impulse-max.sajet.us",
    "found": null,
    "instructions": "Configure el CNAME www.impulse-max.com → impulse-max.sajet.us"
}
```

### Eliminar dominio
```http
DELETE /api/domains/www.impulse-max.com
Authorization: Bearer <token>

Response 204: No Content
```

---

## 📁 Estructura de Archivos a Crear

```
/opt/Erp_core/
├── app/
│   ├── models/
│   │   └── database.py          # + CustomDomain model
│   ├── routes/
│   │   └── domains.py           # NUEVO: CRUD de dominios
│   └── services/
│       └── domain_manager.py    # NUEVO: Lógica de provisioning
│
├── scripts/
│   └── domain_provisioner.py    # NUEVO: Script de configuración CF
│
└── docs/
    └── CUSTOM_DOMAINS_ARCHITECTURE.md  # Este documento
```

---

## 🖥️ Páginas Frontend Svelte

### Nueva página: Domains.svelte

Ubicación: `/opt/Erp_core/frontend/src/routes/Domains.svelte`

**Funcionalidades:**
- Tabla de dominios del cliente
- Modal para agregar nuevo dominio
- Estado de verificación con iconos
- Botón para copiar instrucciones DNS
- Acciones: Verificar, Activar, Eliminar

### Integración en CustomerDetail.svelte

Tab "Dominios" mostrando:
- Dominios personalizados del cliente
- Subdominio sajet.us principal
- Estado de cada dominio

---

## 📊 Casos de Uso por Tenant TecHeels

### Clientes de TecHeels (base de datos techeels en PCT 105)

| Cliente | Dominio Externo | Subdominio Sajet | Estado |
|---------|-----------------|------------------|--------|
| ImpulseMax | www.impulse-max.com | impulse-max.sajet.us | ✅ Activo |
| EvolucionaMujer | www.evolucionamujer.com | evolucionamujer.sajet.us | ✅ Activo |
| TecHeels | www.techeels.io | techeels.sajet.us | ✅ Activo |

### Configuración DNS requerida por cada cliente

```dns
; ImpulseMax (en su registrador DNS)
www.impulse-max.com.     CNAME  impulse-max.sajet.us.
impulse-max.com.         CNAME  impulse-max.sajet.us.  ; o redirect

; EvolucionaMujer
www.evolucionamujer.com. CNAME  evolucionamujer.sajet.us.
evolucionamujer.com.     CNAME  evolucionamujer.sajet.us.

; TecHeels
www.techeels.io.         CNAME  techeels.sajet.us.
techeels.io.             CNAME  techeels.sajet.us.
```

---

## 🔐 Seguridad

### Validaciones requeridas

1. **Sanitización de subdominios:**
   - Solo alfanuméricos y guiones
   - Máximo 63 caracteres
   - No puede empezar/terminar con guión
   - Lista negra: admin, api, www, mail, ftp, etc.

2. **Verificación de propiedad:**
   - Por defecto: verificar CNAME apunta a sajet.us
   - Opcional: TXT record con token

3. **Rate limiting:**
   - Máximo 10 dominios por cliente (plan básico)
   - Máximo 50 dominios por cliente (plan enterprise)

4. **SSL:**
   - Manejado automáticamente por Cloudflare
   - Full (strict) mode habilitado

---

## 📈 Métricas y Monitoreo

### Dashboard de dominios

- Total dominios registrados
- Dominios pendientes de verificación
- Dominios activos vs inactivos
- Errores de configuración

### Alertas

- Dominio sin verificar > 7 días
- Error en propagación DNS
- Certificado SSL por expirar (si aplica)

---

## 🚀 Implementación por Fases

### Fase 1: Backend (Semana 1)
- [ ] Crear tabla custom_domains
- [ ] Implementar endpoints /api/domains
- [ ] Integrar con Cloudflare API
- [ ] Script de configuración de tunnel

### Fase 2: Frontend (Semana 2)
- [ ] Página Domains.svelte
- [ ] Tab de dominios en CustomerDetail
- [ ] Wizard de configuración DNS

### Fase 3: Automatización (Semana 3)
- [ ] Verificación automática de CNAME
- [ ] Webhook de estado de dominio
- [ ] Notificaciones por email

---

## 📞 Contacto y Soporte

Para issues relacionados con dominios:
- **Email:** soporte@jeturing.net
- **Docs:** https://docs.jeturing.net/dominios

---

*Documento creado: Febrero 2026*
*Última actualización: {{ date }}*
*Versión: 1.0*
