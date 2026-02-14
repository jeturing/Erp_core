# Matriz de Roles y Permisos – Sajet.us (Admin / Tenant / Proveedor)

## Resumen Ejecutivo

Se definen 3 roles principales en la plataforma Sajet.us para alinear con el acuerdo de partnership (Palm Innovation Services + otros partners) y la operación SaaS multi-tenant.

| Rol | Descripción | Scope | Acceso Datos |
|-----|-------------|-------|--------------|
| **Admin (Jeturing)** | Operador central de la plataforma | Todos los tenants, partners, billing, custom | Global |
| **Tenant (Cliente Final)** | Usuario dentro de su tenant Odoo | Solo su tenant + Odoo modules | Isolado por subdomain |
| **Proveedor de Servicio (Partner)** | Implementador / Go-live manager | Sus leads, sus tenants (creados), portal | Restringido a leads asignados |

---

## 1. Rol: ADMIN (Jeturing)

### Quién
- Equipo interno de Jeturing (operaciones, soporte, billing, producto).
- Acceso >= 2FA.

### Permisos en Portal Admin (https://sajet.us/admin)

#### Leads & Pipeline
- ✅ Ver todos los leads (filtros: status, partner, country, volumen, complejidad)
- ✅ Asignar partner a lead (dropdown de partners activos)
- ✅ Calificar lead (cambiar status: nuevo → calificado)
- ✅ Marcar "Requiere Jeturing" (si custom detectado)
- ✅ Crear Work Order (para desarrollos/integraciones)
- ✅ Ver cotización dimensionamiento (lectura)
- ✅ Notas / historial de cambios

#### Tenants
- ✅ Ver todos los tenants (listado real desde PCT 105)
- ✅ Crear tenant manual (si no es por partner)
- ✅ Cambiar contraseña admin del tenant
- ✅ Suspender / Reactivar por falta de pago
- ✅ Ver módulos habilitados
- ✅ Agregar módulos (en tenants activos)
- ✅ Ver logs de provisioning
- ✅ Acceder a cualquier tenant como "Inspector" (view-only o admin delegado)

#### Partners
- ✅ Listar partners (activos, pendientes, suspendidos)
- ✅ Ver performance (leads asignados, closed, MRR, comisión pendiente)
- ✅ Activar/suspender partner (si incumple)
- ✅ Editar datos partner (legal_name, contact, especialidades)
- ✅ Ver documentos NDA / acuerdos (S3 links)

#### Facturación
- ✅ Ver facturas (todas, por partner, por tenant)
- ✅ Registrar pago de factura (marcar pagada)
- ✅ Calcular comisiones (50/50 automático)
- ✅ Enviar liquidación mensual a partners
- ✅ Generar reportes de ingresos (MRR, churn, etc.)

#### Configuración
- ✅ Editar catálogo de planes / módulos
- ✅ Cambiar precios (si aplica)
- ✅ Gestionar dominios (Cloudflare tokens, DNS)
- ✅ Ver logs de sistema (provisioning, webhooks, errores)
- ✅ Configurar integraciones (Stripe keys, email, etc.)

#### Acción Crítica: No puede
- ❌ Crear leads (solo calificar)
- ❌ Cambiar comisiones de un partner específico sin auditoría
- ❌ Eliminar leads (soft-delete solo, con motivo)
- ❌ Acceder a datos de otros portales (ej. SEGRD, sin permiso explicit)

---

## 2. Rol: TENANT (Cliente Final / Usuario dentro del Tenant)

### Quién
- Empleados del cliente final autenticados en su tenant Odoo.
- Acceso según rol Odoo (Ventas, Compras, Almacén, Admin, etc.).

### Permisos en Tenant Odoo (https://{subdomain}.sajet.us)

#### Datos del Negocio
- ✅ Crear / editar / ver documentos según módulo habilitado (pedidos, facturas, productos, etc.)
- ✅ Reportes y análisis (dentro del tenant)
- ✅ Colaboración interna (mensajes, tareas, etc.)

#### Configuración del Tenant
- ✅ Cambiar propia contraseña
- ✅ Crear usuarios adicionales (si es admin)
- ✅ Editar parámetros de módulo (si es admin)
- ✅ Cambiar logo / datos de empresa (si es admin)

#### Facturación / Suscripción (si aplica)
- ✅ Ver su suscripción actual (plan, precio, renovación)
- ✅ Descargar facturas de suscripción
- ✅ Cambiar método de pago (si es Stripe)
- ✅ Contactar soporte

#### Acción Crítica: No puede
- ❌ Ver otros tenants
- ❌ Ver datos de otros clientes
- ❌ Cambiar plan (solo Jeturing/Partner)
- ❌ Suspender su propia suscripción sin aprobación
- ❌ Acceder a portal de partners
- ❌ Ver comisiones o facturación interna

---

## 3. Rol: PROVEEDOR DE SERVICIO (Partner)

### Quién
- Socio implementador (ej. Palm Innovation Services).
- Autenticado con JWT + API Key (único por partner).
- Acceso solo a leads/tenants asignados.

### Permisos en Portal de Socios (https://sajet.us/partners)

#### Leads & Oportunidades
- ✅ Ver leads propios (asignados por Jeturing admin)
- ✅ Cambiar status interno (en_calificacion → calificado)
- ✅ Adjuntar documentos (SOW, minutas de levantamiento, propuesta)
- ✅ Notas internas (comunicación con cliente, sin modificar lead público)
- ✅ Ver contacto del cliente (email, teléfono)
- ✅ Ver datos del formulario (volúmenes, requerimientos)

#### Tenant & Provisioning
- ✅ Botón "Crear tenant" (si lead status = 'calificado')
- ✅ Ver tenant creado (URL, módulos, credenciales admin)
- ✅ Descargar credenciales en PDF (para cliente)
- ✅ Ver estado de factura (emitida, pagada, vencida)
- ✅ Descargar factura en PDF

#### Work Orders (Custom)
- ✅ Solicitar "Work Order" a Jeturing (formulario con detalle)
- ✅ Ver estado de Work Order (pendiente, aprobado, rechazado)
- ✅ Ver presupuesto aprobado (si aplica)
- ✅ Ver timeline estimado

#### Comisiones & Pagos
- ✅ Ver comisiones pendientes (leads propios convertidos en tenants)
- ✅ Ver comisiones pagadas (historial)
- ✅ Ver detalles de cálculo (Ingresos Netos, comisión 50%, impuestos)
- ✅ Descargar comprobante de pago

#### Documentos & Compliance
- ✅ Subir/descargar NDA (si no ya firmado)
- ✅ Ver acuerdo de partnership vigente
- ✅ Actualizar datos de contacto / dirección

#### Acción Crítica: No puede
- ❌ Ver leads de otros partners
- ❌ Acceder a tenants que no creó
- ❌ Ver datos de otros clientes (privacidad)
- ❌ Cambiar precios / catálogo
- ❌ Prometer SLA / términos fuera de contrato
- ❌ Ver IP de Jeturing (código, arquitectura, secretos)
- ❌ Acceder a admin panel de Jeturing
- ❌ Cambiar comisiones propias
- ❌ Crear usuarios "consultor" dentro de los tenants
- ❌ Modificar factura emitida (read-only)

---

## 4. Control de Acceso (ACL) – Implementación Técnica

### 4.1 JWT Claims (Authentication)

```json
{
  "sub": "user_123",
  "email": "juan@acme.mx",
  "role": "admin|tenant|partner",
  "tenant_id": 42,               // null si admin o partner
  "partner_id": 5,               // null si admin o tenant
  "org_id": "jeturing",          // Jeturing org
  "permissions": ["lead:read", "tenant:create", ...],
  "iat": 1707901200,
  "exp": 1707987600,
  "iss": "sajet.us",
  "aud": "sajet.us"
}
```

### 4.2 Middleware de Autorización (FastAPI)

```python
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return {"user_id": user_id, "role": role, "payload": payload}

def check_role(required_roles: list[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return current_user
    return role_checker

# Uso:
@app.post("/api/admin/leads/{lead_id}/qualify")
async def qualify_lead(
    lead_id: int,
    user = Depends(check_role(["admin"]))
):
    # Solo admin puede calificar
    ...
```

### 4.3 Query-level Isolation (Tenant Data)

```python
# Para TENANT: solo ve su tenant
@app.get("/api/tenant/info")
async def get_tenant_info(current_user: dict = Depends(get_current_user)):
    tenant_id = current_user["payload"]["tenant_id"]
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return tenant

# Para PARTNER: solo ve sus leads/tenants
@app.get("/api/partners/leads")
async def list_partner_leads(current_user: dict = Depends(get_current_user)):
    partner_id = current_user["payload"]["partner_id"]
    leads = db.query(Lead).filter(Lead.assigned_partner_id == partner_id).all()
    return leads

# Para ADMIN: ve todo
@app.get("/api/admin/leads")
async def list_all_leads(current_user: dict = Depends(check_role(["admin"]))):
    leads = db.query(Lead).all()  # Sin filtro
    return leads
```

---

## 5. Tabla de Transiciones de Estado (Lead)

| De Estado | Hacia Estado | Quién | Condición |
|-----------|--------------|-------|-----------|
| `nuevo` | `en_calificacion` | Admin o Partner | Lead completado |
| `en_calificacion` | `calificado` | Admin | Volúmenes validados |
| `en_calificacion` | `rechazado` | Admin | Duplicado, spam, inválido |
| `calificado` | `tenant_crear` | Partner | Clic "Crear tenant" |
| `calificado` | `jeturing_work_order` | Admin | Custom detectado |
| `calificado` | `propuesta_especial` | Admin o Partner | Negociación |
| `tenant_crear` | `facturado` | Sistema (automático) | Factura emitida |
| `facturado` | `activo` | Sistema (automático) | Tenant provisioned |
| `activo` | `suspendido` | Admin o Partner | Por falta de pago |
| `suspendido` | `activo` | Admin | Pago recibido |
| `propuesta_especial` | `facturado` | Sistema (custom) | Order Form ejecutado |

---

## 6. Ejemplos de Integración por Rol

### Ejemplo 1: Partner crea tenant
```
1. Partner logueado (JWT con partner_id = 5)
2. Ve leads asignados: [Lead 42, 43, 45]
3. Abre Lead 42, status = "calificado"
4. Click "Crear tenant"
5. Sistema valida: Partner JWT + lead.assigned_partner_id == 5 ✅
6. Sistema genera factura, crea tenant
7. Sistema retorna URL + credenciales admin
8. Partner copia creds → envía a cliente por email
9. Lead status → "facturado" → "activo"
```

### Ejemplo 2: Admin maneja Work Order
```
1. Admin revisa Lead 42, cotización indica requires_jeturing = true
2. Lead status → "jeturing_work_order"
3. Admin crea Work Order: "Integración SAP + contabilidad paramétrica"
4. Asigna a dev team, presupuesto, timeline
5. Partner ve Work Order en portal (read-only con presupuesto)
6. Partner confirma o negocia
7. Una vez completado, Invoice adicional se genera
8. Partner recibe su 50% de comisión por custom
```

### Ejemplo 3: Tenant admin gestiona usuarios
```
1. Cliente (Tenant) logueado en https://acme-corporation.sajet.us
2. Accede a /admin/users
3. Sistema valida: tenant_id en JWT == tenant del acceso
4. Puede crear/editar usuarios, pero NO puede:
   - Cambiar plan
   - Suspender suscripción
   - Ver facturación interna
5. Si quiere cambiar plan, contacta Partner o Jeturing soporte
```

---

## 7. Seguridad: Checklist de Implementación

- [ ] JWT firmado con clave privada (RS256 o HS256)
- [ ] Tokens con expiración (24h para admin, 7d para partner/tenant)
- [ ] Refresh tokens para sesiones largas
- [ ] Rate limiting en login (5 intentos fallidos = bloqueo 15 min)
- [ ] 2FA obligatorio para admin y partner
- [ ] Logs de auditoría (quién cambió qué, cuándo)
- [ ] CORS configurado (solo sajet.us + partners autorizados)
- [ ] HTTPS obligatorio (443, certificado válido)
- [ ] Cookies httpOnly + SameSite=Strict
- [ ] No exponer IDs internos en URLs (usar slugs o UUIDs)
- [ ] SQL injection prevention (SQLAlchemy ORM)
- [ ] CSRF token en formularios (POST/PUT/DELETE)
- [ ] Encriptación de datos sensibles en BD (encrypt at rest si aplica)
- [ ] Backup y disaster recovery plan

---

## 8. Diagrama de Flujo de Autorización

```
Usuario accede a /api/admin/leads
    │
    ├─ Token ausente?
    │  └─ 401 Unauthorized
    │
    ├─ Token inválido/expirado?
    │  └─ 401 Unauthorized
    │
    ├─ Token válido? Extraer claims
    │  └─ role = ? (admin / tenant / partner)
    │
    ├─ role != "admin"?
    │  └─ 403 Forbidden (endpoint requiere admin)
    │
    └─ role == "admin"? ✅
       └─ Query: SELECT * FROM leads
          └─ Retorna todos los leads
```

---

## 9. Próximas Fases

### MVP (Fase 1)
- [ ] JWT + login diferenciado (admin / tenant / partner)
- [ ] ACL básico (admin ve todo, tenant ve su tenant, partner ve sus leads)
- [ ] Transiciones de estado validadas

### Fase 2
- [ ] 2FA para admin y partner
- [ ] Audit logs completos
- [ ] Roles granulares dentro de cada rol (p. ej. "Partner Sales" vs "Partner Tech")

### Fase 3
- [ ] SSO (Google, Microsoft, Okta) para admin/partner
- [ ] Delegación de permisos (admin delega a staff)
- [ ] Role-based UI (mostrar/ocultar botones según permisos)

