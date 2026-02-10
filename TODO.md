# 📋 TODO - Sistema de Onboarding SaaS Multitenant

> **Última actualización:** 2026-01-31
> **Estado:** En desarrollo activo
> **Servidor:** http://127.0.0.1:4443

---

## 🎯 Resumen Ejecutivo

Sistema de onboarding SaaS que automatiza el registro de clientes, pagos con Stripe, y provisioning de instancias Odoo multitenant en contenedores LXC. El objetivo es evolucionar hacia un **sistema distribuido multi-Proxmox** con monitoreo de recursos y planes diferenciados.

---

## ✅ Completado

### Infraestructura Base
- [x] FastAPI configurado con modular architecture
- [x] PostgreSQL con modelos Customer, Subscription, StripeEvent
- [x] Integración Stripe (checkout, webhooks)
- [x] Sistema JWT con cookies httpOnly
- [x] 2FA opcional con TOTP
- [x] WAF y middleware de seguridad
- [x] Templates Jinja2 con modo claro/oscuro
- [x] Variables de entorno documentadas (.env)

### Rutas Funcionales
- [x] `/` - Landing page
- [x] `/signup` - Formulario de registro
- [x] `/success` - Página post-checkout
- [x] `/login/admin` y `/login/tenant` - Login unificado
- [x] `/admin` - Dashboard administrativo
- [x] `/admin/tenants` - Gestión de tenants ✨ NUEVO
- [x] `/admin/settings` - Configuración del sistema
- [x] `/admin/logs` - Logs del sistema
- [x] `/admin/billing` - Facturación
- [x] `/tenant/portal` - Portal del cliente
- [x] `/api/auth/login` - Autenticación segura

---

## 🔄 En Progreso

### 3. Actualizar estado post-provisioning
**Archivo:** `app/services/odoo_provisioner.py`

```python
# ANTES: El provisioner no actualiza la BD después del éxito
# DESPUÉS: Debe cambiar subscription.status = active y tenant_provisioned = True
```

**Cambios necesarios:**
- [ ] Importar SessionLocal y modelos en odoo_provisioner.py
- [ ] Añadir parámetro `subscription_id` a provision_tenant()
- [ ] Actualizar status después de éxito del script
- [ ] Enviar notificación al cliente (email opcional)

---

## 📝 Pendiente - Fase 1: Correcciones Críticas

### 4. Eliminar endpoints deprecated
**Archivos:** `app/routes/auth.py`, `app/routes/roles.py`

Los siguientes endpoints generan confusión y deben eliminarse o marcarse claramente:
- [ ] `/api/admin/login` (usar `/api/auth/login`)
- [ ] `/api/login/unified` (deprecated)

---

## 🚀 Pendiente - Fase 2: Sistema Multi-Proxmox

### 5. Diseñar sistema multi-Proxmox
**Objetivo:** Desplegar en múltiples nodos Proxmox para servicio distribuido

**Arquitectura propuesta:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE (FastAPI)                         │
│                     http://central.sajet.us                          │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │  PROXMOX 1   │ │  PROXMOX 2   │ │  PROXMOX 3   │
   │  Node: pve1  │ │  Node: pve2  │ │  Node: pve3  │
   │  IP: x.x.x.1 │ │  IP: x.x.x.2 │ │  IP: x.x.x.3 │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
   ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
   │ LXC 105     │  │ LXC 105     │  │ LXC 105     │
   │ LXC 106     │  │ LXC 106     │  │ LXC 106     │
   │ ...         │  │ ...         │  │ ...         │
   │ (Odoo DBs)  │  │ (Odoo DBs)  │  │ (Odoo DBs)  │
   └─────────────┘  └─────────────┘  └─────────────┘
```

**Tareas:**
- [ ] Crear modelo `ProxmoxNode` en database.py
- [ ] Crear modelo `LXCContainer` para tracking de contenedores
- [ ] API para registrar/desregistrar nodos Proxmox
- [ ] Almacenar credenciales de acceso (API token Proxmox)
- [ ] Healthcheck periódico de nodos

### 6. Crear modelo de nodos distribuidos
**Archivo:** `app/models/database.py`

```python
# Nuevos modelos propuestos:

class ProxmoxNode(Base):
    __tablename__ = "proxmox_nodes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # "pve1", "pve2"
    hostname = Column(String)            # "172.16.16.100"
    api_url = Column(String)             # "https://172.16.16.100:8006"
    api_token = Column(String)           # Token encriptado
    proxmox_version = Column(String)     # "8.1.3"
    status = Column(String)              # "online", "offline", "maintenance"
    max_lxc_containers = Column(Integer) # Límite de contenedores
    created_at = Column(DateTime)

class LXCContainer(Base):
    __tablename__ = "lxc_containers"
    
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("proxmox_nodes.id"))
    lxc_id = Column(Integer)             # 105, 106, etc.
    purpose = Column(String)             # "odoo", "postgres", "shared"
    odoo_version = Column(String)        # "17.0"
    packages_path = Column(String)       # "/opt/odoo/packages"
    cpu_limit = Column(Integer)          # cores
    ram_limit = Column(Integer)          # MB
    storage_limit = Column(Integer)      # GB
    status = Column(String)              # "running", "stopped"
    
class TenantDeployment(Base):
    __tablename__ = "tenant_deployments"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("customers.id"))
    container_id = Column(Integer, ForeignKey("lxc_containers.id"))
    database_name = Column(String)
    cpu_usage = Column(Float)            # % actual
    ram_usage = Column(Float)            # % actual  
    storage_used = Column(Integer)       # GB usado
    deployed_at = Column(DateTime)
```

### 7. Implementar monitoreo de recursos
**Objetivo:** Saber cuándo un servidor está lleno y balancear carga

**Métricas a monitorear:**
- [ ] CPU por contenedor LXC
- [ ] RAM por contenedor LXC
- [ ] Almacenamiento usado vs disponible
- [ ] Número de tenants por contenedor
- [ ] Latencia de respuesta Odoo

**Implementación:**
- [ ] Endpoint `/api/nodes/{node_id}/metrics`
- [ ] Background task que recolecta métricas cada 5 min
- [ ] Alertas cuando recursos > 80%
- [ ] Dashboard de monitoreo en `/admin/nodes`

### 8. Crear planes por entorno
**Objetivo:** Diferenciar entre shared, professional, enterprise

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PLANES DE SERVICIO                          │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│              │    BASIC     │     PRO      │     ENTERPRISE        │
│              │   $29/mes    │   $49/mes    │      $99/mes          │
├──────────────┼──────────────┼──────────────┼───────────────────────┤
│ Tipo         │   Shared     │  Dedicated   │   Dedicated HA        │
│ LXC          │ Compartido   │  Exclusivo   │   Exclusivo + Backup  │
│ CPU          │   1 core     │   2 cores    │      4 cores          │
│ RAM          │   2 GB       │   4 GB       │      8 GB             │
│ Storage      │   10 GB      │   50 GB      │     100 GB            │
│ Backups      │   Semanal    │   Diario     │   Cada 6 horas        │
│ Soporte      │   Email      │   Chat       │   Telefónico 24/7     │
│ SLA          │   99%        │   99.5%      │      99.9%            │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
```

**Tareas:**
- [ ] Crear modelo `Plan` con configuraciones de recursos
- [ ] Modificar provisioner para aplicar límites según plan
- [ ] UI para upgrade/downgrade de plan
- [ ] Billing diferenciado en Stripe

---

## 🔮 Fase 3: Provisioning Interactivo

### 9. Provisioning interactivo de Odoo
**Objetivo:** Cuando se llene un servidor, ofrecer opciones al admin

**Flujo propuesto:**
```
1. Nuevo tenant solicita provisioning
2. Sistema verifica recursos en todos los nodos
3. Si hay espacio → Auto-provision en nodo menos cargado
4. Si NO hay espacio:
   a. Notificar al admin
   b. Mostrar dashboard con opciones:
      - Añadir nuevo nodo Proxmox
      - Migrar tenants a otro nodo
      - Expandir recursos de nodo existente
      - Poner tenant en cola de espera
```

**Tareas:**
- [ ] Endpoint `/api/provision/check-capacity`
- [ ] WebSocket para notificaciones en tiempo real
- [ ] UI de wizard de provisioning en `/admin/provision`
- [ ] Script de migración de tenant entre nodos

### 10. Despliegue en LXC limpio
**Objetivo:** Automatizar el setup de nuevos LXC desde cero

# 📋 TODO - Sistema de Onboarding SaaS Multitenant

**Última actualización:** 2026-01-31

**Estado:** En desarrollo activo

**Servidor:** [http://127.0.0.1:4443](http://127.0.0.1:4443)

---

## 🎯 Resumen Ejecutivo

Sistema de onboarding SaaS que automatiza el registro de clientes, pagos con Stripe, y provisioning de instancias Odoo multitenant en contenedores LXC. El objetivo es evolucionar hacia un **sistema distribuido multi-Proxmox** con monitoreo de recursos y planes diferenciados.

---

## ✅ Completado

### Infraestructura Base
- [x] FastAPI configurado con modular architecture
- [x] PostgreSQL con modelos Customer, Subscription, StripeEvent
- [x] Integración Stripe (checkout, webhooks)
- [x] Sistema JWT con cookies httpOnly
- [x] 2FA opcional con TOTP
- [x] WAF y middleware de seguridad
- [x] Templates Jinja2 con modo claro/oscuro
- [x] Variables de entorno documentadas (.env)

### Rutas Funcionales
- [x] `/` - Landing page
- [x] `/signup` - Formulario de registro
- [x] `/success` - Página post-checkout
- [x] `/login/admin` y `/login/tenant` - Login unificado
- [x] `/admin` - Dashboard administrativo
- [x] `/admin/tenants` - Gestión de tenants ✨ NUEVO
- [x] `/admin/settings` - Configuración del sistema
- [x] `/admin/logs` - Logs del sistema
- [x] `/admin/billing` - Facturación
- [x] `/tenant/portal` - Portal del cliente
- [x] `/api/auth/login` - Autenticación segura

---

## 🔄 En Progreso

### 3. Actualizar estado post-provisioning
**Archivo:** `app/services/odoo_provisioner.py`

```python
# ANTES: El provisioner no actualiza la BD después del éxito
# DESPUÉS: Debe cambiar subscription.status = active y tenant_provisioned = True
```

**Cambios necesarios:**
- [ ] Importar SessionLocal y modelos en odoo_provisioner.py
- [ ] Añadir parámetro `subscription_id` a provision_tenant()
- [ ] Actualizar status después de éxito del script
- [ ] Enviar notificación al cliente (email opcional)

---

## 📝 Pendiente - Fase 1: Correcciones Críticas

### 4. Eliminar endpoints deprecated
**Archivos:** `app/routes/auth.py`, `app/routes/roles.py`

Los siguientes endpoints generan confusión y deben eliminarse o marcarse claramente:
- [ ] `/api/admin/login` (usar `/api/auth/login`)
- [ ] `/api/login/unified` (deprecated)

---

## 🚀 Pendiente - Fase 2: Sistema Multi-Proxmox

### 5. Diseñar sistema multi-Proxmox
**Objetivo:** Desplegar en múltiples nodos Proxmox para servicio distribuido

**Arquitectura propuesta:**
```text
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE (FastAPI)                         │
│                     http://central.sajet.us                          │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │  PROXMOX 1   │ │  PROXMOX 2   │ │  PROXMOX 3   │
   │  Node: pve1  │ │  Node: pve2  │ │  Node: pve3  │
   │  IP: x.x.x.1 │ │  IP: x.x.x.2 │ │  IP: x.x.x.3 │
   └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
   ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
   │ LXC 105     │  │ LXC 105     │  │ LXC 105     │
   │ LXC 106     │  │ LXC 106     │  │ LXC 106     │
   │ ...         │  │ ...         │  │ ...         │
   │ (Odoo DBs)  │  │ (Odoo DBs)  │  │ (Odoo DBs)  │
   └─────────────┘  └─────────────┘  └─────────────┘
```

**Tareas:**
- [ ] Crear modelo `ProxmoxNode` en database.py
- [ ] Crear modelo `LXCContainer` para tracking de contenedores
- [ ] API para registrar/desregistrar nodos Proxmox
- [ ] Almacenar credenciales de acceso (API token Proxmox)
- [ ] Healthcheck periódico de nodos

### 6. Crear modelo de nodos distribuidos
**Archivo:** `app/models/database.py`

```python
# Nuevos modelos propuestos:

class ProxmoxNode(Base):
    __tablename__ = "proxmox_nodes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)  # "pve1", "pve2"
    hostname = Column(String)            # "172.16.16.100"
    api_url = Column(String)             # "https://172.16.16.100:8006"
    api_token = Column(String)           # Token encriptado
    proxmox_version = Column(String)     # "8.1.3"
    status = Column(String)              # "online", "offline", "maintenance"
    max_lxc_containers = Column(Integer) # Límite de contenedores
    created_at = Column(DateTime)

class LXCContainer(Base):
    __tablename__ = "lxc_containers"
    
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("proxmox_nodes.id"))
    lxc_id = Column(Integer)             # 105, 106, etc.
    purpose = Column(String)             # "odoo", "postgres", "shared"
    odoo_version = Column(String)        # "17.0"
    packages_path = Column(String)       # "/opt/odoo/packages"
    cpu_limit = Column(Integer)          # cores
    ram_limit = Column(Integer)          # MB
    storage_limit = Column(Integer)      # GB
    status = Column(String)              # "running", "stopped"
    
class TenantDeployment(Base):
    __tablename__ = "tenant_deployments"
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("customers.id"))
    container_id = Column(Integer, ForeignKey("lxc_containers.id"))
    database_name = Column(String)
    cpu_usage = Column(Float)            # % actual
    ram_usage = Column(Float)            # % actual  
    storage_used = Column(Integer)       # GB usado
    deployed_at = Column(DateTime)
```

### 7. Implementar monitoreo de recursos
**Objetivo:** Saber cuándo un servidor está lleno y balancear carga

**Métricas a monitorear:**
- [ ] CPU por contenedor LXC
- [ ] RAM por contenedor LXC
- [ ] Almacenamiento usado vs disponible
- [ ] Número de tenants por contenedor
- [ ] Latencia de respuesta Odoo

**Implementación:**
- [ ] Endpoint `/api/nodes/{node_id}/metrics`
- [ ] Background task que recolecta métricas cada 5 min
- [ ] Alertas cuando recursos > 80%
- [ ] Dashboard de monitoreo en `/admin/nodes`

### 8. Crear planes por entorno
**Objetivo:** Diferenciar entre shared, professional, enterprise

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         PLANES DE SERVICIO                          │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│              │    BASIC     │     PRO      │     ENTERPRISE        │
│              │   $29/mes    │   $49/mes    │      $99/mes          │
├──────────────┼──────────────┼──────────────┼───────────────────────┤
│ Tipo         │   Shared     │  Dedicated   │   Dedicated HA        │
│ LXC          │ Compartido   │  Exclusivo   │   Exclusivo + Backup  │
│ CPU          │   1 core     │   2 cores    │      4 cores          │
│ RAM          │   2 GB       │   4 GB       │      8 GB             │
│ Storage      │   10 GB      │   50 GB      │     100 GB            │
│ Backups      │   Semanal    │   Diario     │   Cada 6 horas        │
│ Soporte      │   Email      │   Chat       │   Telefónico 24/7     │
│ SLA          │   99%        │   99.5%      │      99.9%            │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
```

**Tareas:**
- [ ] Crear modelo `Plan` con configuraciones de recursos
- [ ] Modificar provisioner para aplicar límites según plan
- [ ] UI para upgrade/downgrade de plan
- [ ] Billing diferenciado en Stripe

---

## 🔮 Fase 3: Provisioning Interactivo

### 9. Provisioning interactivo de Odoo
**Objetivo:** Cuando se llene un servidor, ofrecer opciones al admin

**Flujo propuesto:**
```
1. Nuevo tenant solicita provisioning
2. Sistema verifica recursos en todos los nodos
3. Si hay espacio → Auto-provision en nodo menos cargado
4. Si NO hay espacio:
   a. Notificar al admin
   b. Mostrar dashboard con opciones:
      - Añadir nuevo nodo Proxmox
      - Migrar tenants a otro nodo
      - Expandir recursos de nodo existente
      - Poner tenant en cola de espera
```

**Tareas:**
- [ ] Endpoint `/api/provision/check-capacity`
- [ ] WebSocket para notificaciones en tiempo real
- [ ] UI de wizard de provisioning en `/admin/provision`
- [ ] Script de migración de tenant entre nodos

### 10. Despliegue en LXC limpio
**Objetivo:** Automatizar el setup de nuevos LXC desde cero

**Script propuesto:** `setup_odoo_lxc.sh`
```bash
#!/bin/bash
# Uso: ./setup_odoo_lxc.sh <lxc_id> <odoo_version> <packages_path>

# 1. Crear LXC desde template Debian 12
# 2. Instalar dependencias (PostgreSQL client, Python 3.11, wkhtmltopdf)
# 3. Clonar Odoo desde packages_path o GitHub
# 4. Configurar systemd service
# 5. Configurar Nginx reverse proxy
# 6. Registrar en base de datos central
```

---

## 📊 Métricas del Proyecto

| Categoría | Estado | Porcentaje |
|-----------|--------|------------|
| Rutas Backend | ✅ Completo | 100% |
| Templates UI | ✅ Completo | 100% |
| Autenticación | ✅ Completo | 100% |
| Stripe Integration | ✅ Completo | 95% |
| Tenant Provisioning | 🔄 En progreso | 60% |
| Multi-Proxmox | ⏳ Pendiente | 0% |
| Monitoreo | ⏳ Pendiente | 0% |
| Planes Diferenciados | ⏳ Pendiente | 10% |

---

## 🔧 Comandos Útiles

```bash
# Activar entorno
source /opt/onboarding-system/venv/bin/activate

# Iniciar servidor desarrollo
uvicorn app.main:app --host 0.0.0.0 --port 4443 --reload

# Verificar salud
curl http://127.0.0.1:4443/health

# Login admin
curl -X POST http://127.0.0.1:4443/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"SecurePass2026!","role":"admin"}'

# Ver logs
tail -f logs/security_audit.log
```

---

## 📞 Contacto

Para dudas sobre este proyecto, revisar:
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - Contexto del proyecto
- [docs/MODULAR_ARCHITECTURE.md](docs/MODULAR_ARCHITECTURE.md) - Arquitectura modular
- [docs/JWT_AUTHENTICATION.md](docs/JWT_AUTHENTICATION.md) - Sistema de autenticación
