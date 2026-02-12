📋 ÍNDICE DE DOCUMENTACIÓN - GESTIÓN DE TENANTS
═════════════════════════════════════════════════════════════════════════════

INICIO RÁPIDO
═════════════════════════════════════════════════════════════════════════════

👉 Si NO sabes qué es esto:
   → Lee: IMPLEMENTATION_SUMMARY.md (resumen ejecutivo)
   → Mira: Panel admin en https://sajet.us/admin/tenants

👉 Si quieres USAR el panel admin:
   → Ve a: https://sajet.us/admin/tenants
   → Lee: EJEMPLOS_USO.md (casos prácticos)

👉 Si quieres USAR la API REST:
   → Lee: nodo/docs/TENANT_MANAGEMENT.md (endpoints)
   → Copia comandos de: EJEMPLOS_USO.md

👉 Si eres DESARROLLADOR:
   → Lee: nodo/docs/TENANT_MANAGEMENT.md (técnico)
   → Revisa código en: app/routes/

═════════════════════════════════════════════════════════════════════════════

GUÍAS PRINCIPALES
═════════════════════════════════════════════════════════════════════════════

1. IMPLEMENTATION_SUMMARY.md
   ├─ Qué se implementó (visión ejecutiva)
   ├─ Archivos modificados (qué cambió)
   ├─ Arquitectura (cómo funciona)
   ├─ Características (qué se puede hacer)
   ├─ Próximos pasos (recomendaciones)
   └─ Tiempo lectura: 10 minutos

2. TENANT_MANAGEMENT_README.md
   ├─ Funcionalidades detalladas
   ├─ Estructura técnica completa
   ├─ Archivo por archivo
   ├─ API Keys y configuración
   ├─ Endpoints disponibles
   ├─ Panel admin (características)
   ├─ Flujo de suspensión paso a paso
   ├─ Troubleshooting
   └─ Tiempo lectura: 15 minutos

3. nodo/docs/TENANT_MANAGEMENT.md
   ├─ Referencia técnica de API
   ├─ Todos los endpoints con ejemplos
   ├─ Parámetros requeridos
   ├─ Respuestas esperadas
   ├─ Códigos de error
   ├─ Ejemplos en curl
   ├─ Flujos completos
   └─ Tiempo lectura: 20 minutos

4. EJEMPLOS_USO.md
   ├─ Casos de uso prácticos
   ├─ Comandos listos para copiar
   ├─ Scripts de automatización
   ├─ Estados de tenants explicados
   ├─ Filtros disponibles
   ├─ Logs y monitoreo
   └─ Tiempo lectura: 10 minutos

═════════════════════════════════════════════════════════════════════════════

POR ROL
═════════════════════════════════════════════════════════════════════════════

SOY ADMINISTRADOR (uso panel web):
→ IMPLEMENTATION_SUMMARY.md       (visión general)
→ EJEMPLOS_USO.md                 (casos prácticos)
→ Panel: https://sajet.us/admin/tenants

SOY DEVELOPER (integración API):
→ nodo/docs/TENANT_MANAGEMENT.md  (referencia técnica)
→ EJEMPLOS_USO.md                 (comandos curl)
→ app/routes/provisioning.py      (código fuente)

SOY DEVOPS (deployment):
→ TENANT_MANAGEMENT_README.md     (configuración)
→ nodo/scripts/                    (scripts disponibles)
→ systemctl status odoo-*         (servicios)

SOY STAKEHOLDER (reporte ejecutivo):
→ IMPLEMENTATION_SUMMARY.md       (resumen 1 página)
→ EJEMPLOS_USO.md                 (casos de uso)

═════════════════════════════════════════════════════════════════════════════

POR TAREA
═════════════════════════════════════════════════════════════════════════════

QUIERO VER LOS TENANTS:
→ Panel: https://sajet.us/admin/tenants
→ O API: curl http://localhost:4443/api/tenants
→ Lee: EJEMPLOS_USO.md → "1. CREAR TENANT TECHEELS"

QUIERO CAMBIAR CONTRASEÑA:
→ Panel: Busca tenant → Menú ⋮ → Nueva contraseña
→ O API: curl ... PUT /provisioning/tenant/password
→ Lee: EJEMPLOS_USO.md → "3. CAMBIAR CONTRASEÑA"

QUIERO SUSPENDER POR FALTA DE PAGO:
→ Panel: Busca tenant → Menú ⋮ → Suspender
→ O API: curl ... PUT /provisioning/tenant/suspend {suspend: true}
→ Lee: EJEMPLOS_USO.md → "4. SUSPENDER TENANT"

QUIERO REACTIVAR DESPUÉS DEL PAGO:
→ Panel: Filtra suspendidos → Menú ⋮ → Reactivar
→ O API: curl ... PUT /provisioning/tenant/suspend {suspend: false}
→ Lee: EJEMPLOS_USO.md → "5. REACTIVAR TENANT"

QUIERO AUTOMATIZAR:
→ Scripts en: /opt/Erp_core/scripts/
→ O curl en loop: EJEMPLOS_USO.md → "AUTOMATIZACIÓN"
→ Lee: nodo/docs/TENANT_MANAGEMENT.md → "Ejemplos Prácticos"

═════════════════════════════════════════════════════════════════════════════

CÓDIGO FUENTE
═════════════════════════════════════════════════════════════════════════════

BACKEND (Endpoints):
├─ app/routes/tenants.py
│  └─ GET /api/tenants (lista en tiempo real desde nodos)
│
├─ app/routes/provisioning.py
│  ├─ PUT /api/provisioning/tenant/password (cambiar clave)
│  └─ PUT /api/provisioning/tenant/suspend (suspender/reactivar)
│
└─ nodo/scripts/odoo_local_api.py
   ├─ PUT /api/tenant/password (en base de datos)
   └─ PUT /api/tenant/suspend (en base de datos)

FRONTEND (Templates):
├─ templates/admin_tenants.html
│  ├─ Panel con tabla de tenants
│  ├─ Modal: Crear tenant
│  ├─ Modal: Gestionar tenant (clave + suspensión)
│  └─ Filtros y búsqueda

JAVASCRIPT (Funciones):
├─ changeAdminPassword() - Cambiar contraseña
├─ suspendTenant() - Suspender tenant
├─ reactivateTenant() - Reactivar tenant
└─ openTenantMenu(tenantId) - Abrir menú contextual

═════════════════════════════════════════════════════════════════════════════

ARCHIVOS CREADOS
═════════════════════════════════════════════════════════════════════════════

Documentación (en raíz /opt/Erp_core/):
├─ IMPLEMENTATION_SUMMARY.md       ← Resumen ejecutivo
├─ TENANT_MANAGEMENT_README.md     ← Guía completa
├─ EJEMPLOS_USO.md                 ← Casos prácticos
└─ INDICES.md                       ← Este archivo

Documentación (en nodo):
└─ nodo/docs/TENANT_MANAGEMENT.md  ← Referencia técnica

Scripts:
├─ scripts/create_techeels.sh      ← Crear tenant "Techeels"
└─ scripts/test_tenant_management.sh ← Probar funcionalidades

═════════════════════════════════════════════════════════════════════════════

ARCHIVOS MODIFICADOS
═════════════════════════════════════════════════════════════════════════════

✏️ nodo/scripts/odoo_local_api.py
   + Clase TenantPasswordRequest
   + Clase TenantSuspendRequest
   + Endpoint PUT /api/tenant/password
   + Endpoint PUT /api/tenant/suspend

✏️ app/routes/tenants.py
   + Import httpx y logging
   + ODOO_NODES dictionary
   + Función get_all_tenants_from_nodes()
   + Endpoint GET /api/tenants mejorado

✏️ app/routes/provisioning.py
   + Clase TenantPasswordChangeRequest
   + Clase TenantSuspensionRequest
   + Endpoint PUT /api/provisioning/tenant/password
   + Endpoint PUT /api/provisioning/tenant/suspend

✏️ templates/admin_tenants.html
   + Modal #tenantActionsModal
   + Función openTenantMenu(tenantId)
   + Función changeAdminPassword()
   + Función suspendTenant()
   + Función reactivateTenant()
   + Búsqueda mejorada

═════════════════════════════════════════════════════════════════════════════

FLUJOS PRINCIPALES
═════════════════════════════════════════════════════════════════════════════

FLUJO 1: Ver Todos los Tenants
┌─────────────────────────────────────────────────────────────────┐
│ 1. Admin abre: https://sajet.us/admin/tenants                   │
│ 2. Frontend carga y ejecuta: GET /api/tenants                   │
│ 3. tenants.py consulta todos los nodos:                         │
│    → Llama GET http://10.10.10.100:8070/api/tenants             │
│ 4. odoo_local_api.py retorna lista de BDs                       │
│ 5. tenants.py enriquece con datos de BD local                   │
│ 6. Frontend renderiza tabla con todos los tenants               │
│ 7. Admin ve tenants en tiempo real                              │
└─────────────────────────────────────────────────────────────────┘

FLUJO 2: Cambiar Contraseña de Admin
┌─────────────────────────────────────────────────────────────────┐
│ 1. Admin abre menú ⋮ de un tenant                                │
│ 2. Modal muestra campo "Nueva Contraseña Admin"                  │
│ 3. Admin ingresa contraseña (mínimo 6 caracteres)                │
│ 4. Admin hace click en "Cambiar contraseña"                      │
│ 5. Frontend: PUT /api/provisioning/tenant/password               │
│ 6. provisioning.py valida API key y parámetros                   │
│ 7. provisioning.py llama: PUT http://10.10.10.100:8070/...      │
│ 8. odoo_local_api.py ejecuta SQL:                                │
│    → UPDATE res_users SET password = '...'                       │
│ 9. BD actualizada                                                │
│ 10. Respuesta "Exitoso"                                          │
│ 11. Admin puede usar nueva contraseña en Odoo                    │
└─────────────────────────────────────────────────────────────────┘

FLUJO 3: Suspender por Falta de Pago
┌─────────────────────────────────────────────────────────────────┐
│ 1. Admin abre menú ⋮ de un tenant vencido                        │
│ 2. Botón rojo "Suspender"                                        │
│ 3. Confirmación: "¿Suspender? Usuarios no podrán acceder"       │
│ 4. Admin confirma                                                │
│ 5. Frontend: PUT /api/provisioning/tenant/suspend {suspend:true} │
│ 6. provisioning.py llama: PUT http://10.10.10.100:8070/...      │
│ 7. odoo_local_api.py ejecuta:                                    │
│    → UPDATE res_users SET active = false                         │
│    → INSERT ir_config_parameter: tenant.suspended = true         │
│    → INSERT ir_config_parameter: reason = '...'                  │
│ 8. BD actualizada                                                │
│ 9. Status en tabla cambia a "Suspendido" (rojo)                  │
│ 10. Usuarios no pueden acceder a Odoo                            │
│ 11. Datos preservados íntegramente                               │
└─────────────────────────────────────────────────────────────────┘

FLUJO 4: Reactivar Después del Pago
┌─────────────────────────────────────────────────────────────────┐
│ 1. Admin abre menú ⋮ de un tenant suspendido                     │
│ 2. Botón verde "Reactivar"                                       │
│ 3. Confirmación: "¿Reactivar? Usuarios accederán nuevamente"    │
│ 4. Admin confirma                                                │
│ 5. Frontend: PUT /api/provisioning/tenant/suspend {suspend:false}│
│ 6. provisioning.py llama: PUT http://10.10.10.100:8070/...      │
│ 7. odoo_local_api.py ejecuta:                                    │
│    → UPDATE res_users SET active = true                          │
│    → UPDATE ir_config_parameter SET value = 'false' ...          │
│ 8. BD actualizada                                                │
│ 9. Status en tabla cambia a "Activo" (verde)                     │
│ 10. Usuarios pueden acceder nuevamente                           │
│ 11. Todo funciona como antes (sin pérdida de datos)              │
└─────────────────────────────────────────────────────────────────┘

═════════════════════════════════════════════════════════════════════════════

PREGUNTAS FRECUENTES
═════════════════════════════════════════════════════════════════════════════

P: ¿Dónde accedo al panel admin?
R: https://sajet.us/admin/tenants (requiere login)

P: ¿Se pierden datos al suspender?
R: NO, los datos se conservan íntegramente. Solo se bloquea el acceso.

P: ¿Cuánto tiempo tarda en suspender?
R: Inmediato (< 1 segundo)

P: ¿Se puede reactivar después de suspender?
R: SÍ, sin limitaciones. Los datos estarán exactamente como estaban.

P: ¿Qué pasa si cambio la contraseña mientras un usuario está accediendo?
R: El usuario actual sigue accediendo. Próximo login requiere nueva contraseña.

P: ¿Puedo suspender múltiples tenants a la vez?
R: SÍ, con un script loop usando la API.

P: ¿Dónde están los tenants en la BD?
R: Cada tenant es una BD separada en PostgreSQL con nombre = subdomain

P: ¿Qué API key debo usar?
R: "prov-key-2026-secure" (cambiar en PRODUCCIÓN)

P: ¿Puedo agregar más nodos?
R: SÍ, añade en ODOO_NODES en app/routes/provisioning.py

═════════════════════════════════════════════════════════════════════════════

ATAJOS ÚTILES
═════════════════════════════════════════════════════════════════════════════

Abrir panel admin:
→ https://sajet.us/admin/tenants

Ver todos los tenants (API):
→ curl http://localhost:4443/api/tenants | jq

Revisar logs:
→ tail -f /var/log/supervisor/fastapi-app-stderr.log

Reiniciar API:
→ systemctl restart fastapi-app

Conectar a BD de un tenant:
→ sudo -u postgres psql -d techeels

Ver servicios Odoo en PCT 105:
→ systemctl status odoo-local-api

═════════════════════════════════════════════════════════════════════════════

SIGUIENTE LECTURA RECOMENDADA
═════════════════════════════════════════════════════════════════════════════

1️⃣  Lectura rápida (5 min):
    → IMPLEMENTATION_SUMMARY.md

2️⃣  Usar panel admin (10 min):
    → EJEMPLOS_USO.md → "CÓMO USAR (Paso a Paso)"

3️⃣  Profundizar técnico (20 min):
    → nodo/docs/TENANT_MANAGEMENT.md

4️⃣  Automatizar (30 min):
    → EJEMPLOS_USO.md → "AUTOMATIZACIÓN"
    → app/routes/provisioning.py (código)

═════════════════════════════════════════════════════════════════════════════

¿NECESITAS AYUDA?
═════════════════════════════════════════════════════════════════════════════

Problema:          Revisar:
────────────────────────────────────────
No ves tenants     nodo/docs/TENANT_MANAGEMENT.md → Troubleshooting
API retorna error  EJEMPLOS_USO.md → Errores esperados
No funciona cambio TENANT_MANAGEMENT_README.md → Troubleshooting
Quiero automatizar EJEMPLOS_USO.md → AUTOMATIZACIÓN

═════════════════════════════════════════════════════════════════════════════

Última actualización: 2026-02-10
Versión: 1.0 (Producción)
Estado: ✅ Completo y funcional
