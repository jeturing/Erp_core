#!/opt/bin/bash
#
# README - Gestión Completa de Tenants
#

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                   ✨ GESTIÓN COMPLETA DE TENANTS ✨                      ║
║                                                                            ║
║                    Panel Admin + API de Provisioning                     ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝

FUNCIONALIDADES IMPLEMENTADAS
══════════════════════════════════════════════════════════════════════════════

✅ Ver todos los tenants en tiempo real
   • Panel admin en https://sajet.us/admin/tenants
   • Listado con filtros y búsqueda
   • Estadísticas en tiempo real

✅ Crear nuevos tenants
   • Interfaz web en panel admin
   • API en POST /api/provisioning/tenant
   • Auto-provisioning de DNS en Cloudflare

✅ Cambiar contraseña de admin
   • Desde panel admin (modal de gestión)
   • API en PUT /api/provisioning/tenant/password
   • Actualización en BD automática

✅ Suspender/reactivar tenants
   • Por falta de pago
   • Usuarios no pueden acceder (excepto admin)
   • Datos se conservan en BD
   • Reactivación sin pérdida de información

✅ Panel Admin intuitivo
   • Ver todos los tenants con detalles
   • Filtrar por estado, plan, nodo
   • Buscar por empresa, email, subdominio
   • Crear, suspender, cambiar clave
   • Acceso directo a instancias Odoo

ESTRUCTURA TÉCNICA
══════════════════════════════════════════════════════════════════════════════

BACKEND (PCT 160 - App Server)
┌─────────────────────────────────────────────────────────────────────────┐
│ FastAPI en puerto 4443                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ • app/routes/tenants.py                                                 │
│   GET /api/tenants - Lista desde todos los nodos                        │
│                                                                          │
│ • app/routes/provisioning.py                                            │
│   PUT /api/provisioning/tenant/password - Cambiar clave               │
│   PUT /api/provisioning/tenant/suspend - Suspender/reactivar           │
│   POST /api/provisioning/tenant - Crear tenant                         │
│   DELETE /api/provisioning/tenant - Eliminar tenant                    │
│                                                                          │
│ • templates/admin_tenants.html                                          │
│   Panel web en https://sajet.us/admin/tenants                          │
│   UI con modales para gestión                                           │
└─────────────────────────────────────────────────────────────────────────┘

BACKEND (PCT 105 - Nodo Odoo)
┌─────────────────────────────────────────────────────────────────────────┐
│ FastAPI en puerto 8070                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ • nodo/scripts/odoo_local_api.py                                        │
│   PUT /api/tenant/password - Actualizar clave en BD                    │
│   PUT /api/tenant/suspend - Suspender/reactivar en BD                  │
│   POST /api/tenant - Crear BD                                          │
│   DELETE /api/tenant - Eliminar BD                                     │
│   GET /api/tenants - Listar BDs                                        │
│                                                                          │
│ • nodo/scripts/odoo_db_watcher.py                                       │
│   Monitorea BDs nuevas                                                  │
│   Auto-crea DNS en Cloudflare                                          │
└─────────────────────────────────────────────────────────────────────────┘

API KEYS & CONFIGURACIÓN
══════════════════════════════════════════════════════════════════════════════

Ubicación: /opt/Erp_core/app/routes/provisioning.py
Línea: ~20

ODOO_SERVERS = {
    "primary": {
        "ip": "10.10.10.100",          # PCT 105
        "api_port": 8070,              # Puerto API local
        "domain": "sajet.us"
    }
}

PROVISIONING_API_KEY = "prov-key-2026-secure"

Para cambiar en PRODUCCIÓN:
sed -i 's/prov-key-2026-secure/tu_clave_nueva/g' /opt/Erp_core/app/routes/*.py

ENDPOINTS DISPONIBLES
══════════════════════════════════════════════════════════════════════════════

1. LISTAR TENANTS
   GET /api/tenants
   
   curl -X GET https://sajet.us/api/tenants

2. CREAR TENANT
   POST /api/provisioning/tenant
   
   curl -X POST https://sajet.us/api/provisioning/tenant \
     -H "X-API-KEY: prov-key-2026-secure" \
     -d '{"subdomain":"techeels"}'

3. CAMBIAR CONTRASEÑA
   PUT /api/provisioning/tenant/password
   
   curl -X PUT https://sajet.us/api/provisioning/tenant/password \
     -H "X-API-KEY: prov-key-2026-secure" \
     -d '{"subdomain":"techeels","new_password":"Nueva123!"}'

4. SUSPENDER
   PUT /api/provisioning/tenant/suspend
   
   curl -X PUT https://sajet.us/api/provisioning/tenant/suspend \
     -H "X-API-KEY: prov-key-2026-secure" \
     -d '{"subdomain":"techeels","suspend":true,"reason":"Falta de pago"}'

5. REACTIVAR
   PUT /api/provisioning/tenant/suspend
   
   curl -X PUT https://sajet.us/api/provisioning/tenant/suspend \
     -H "X-API-KEY: prov-key-2026-secure" \
     -d '{"subdomain":"techeels","suspend":false}'

6. ELIMINAR
   DELETE /api/provisioning/tenant
   
   curl -X DELETE https://sajet.us/api/provisioning/tenant \
     -H "X-API-KEY: prov-key-2026-secure" \
     -d '{"subdomain":"techeels"}'

PANEL ADMIN
══════════════════════════════════════════════════════════════════════════════

URL: https://sajet.us/admin/tenants

Acciones disponibles:
✅ Ver todos los tenants con estadísticas
✅ Filtrar por estado (activos, pendientes, suspendidos)
✅ Buscar por empresa, email, subdominio
✅ Crear nuevo tenant (modal con formulario)
✅ Cambiar contraseña admin
✅ Suspender por falta de pago
✅ Reactivar tenant
✅ Acceso directo a Odoo

Características UI:
• Tabla con paginación (10 por página)
• Cards con estadísticas en tiempo real
• Filtros combinables
• Modal para crear tenant
• Modal para gestionar tenant (clave + suspensión)
• Iconos de estado y estado de túnel
• Dark mode soportado

FLUJO DE SUSPENSIÓN POR FALTA DE PAGO
══════════════════════════════════════════════════════════════════════════════

1. Cliente no paga a tiempo
2. Admin abre panel en https://sajet.us/admin/tenants
3. Admin busca el tenant y abre menú (⋮)
4. Admin selecciona "Suspender"
5. Sistema ejecuta:
   - PUT /api/provisioning/tenant/suspend
   - Desactiva usuarios en BD (res_users.active = false)
   - Guarda razón en ir_config_parameter
   - Usuario intenta acceder → "Su servicio está suspendido"

6. Cuando paga:
   - Admin selecciona "Reactivar"
   - Sistema ejecuta PUT /api/provisioning/tenant/suspend {suspend: false}
   - Activa usuarios nuevamente
   - Cliente puede acceder inmediatamente

DATOS CONSERVADOS
══════════════════════════════════════════════════════════════════════════════

Al suspender un tenant:
✅ Base de datos íntegra
✅ Todos los datos del cliente
✅ Configuración de Odoo
✅ Registro de transacciones
❌ Acceso de usuarios bloqueado
❌ API accesible (pero con restricción)

Al reactivar:
✅ Todo vuelve a funcionar como antes
✅ Sin pérdida de datos
✅ Sin reconfiguraciones
✅ Acceso inmediato

ARCHIVOS MODIFICADOS
══════════════════════════════════════════════════════════════════════════════

/opt/Erp_core/nodo/scripts/odoo_local_api.py
  + PUT /api/tenant/password
  + PUT /api/tenant/suspend

/opt/Erp_core/app/routes/tenants.py
  + Consulta API real en lugar de datos mock
  + Soporte para múltiples nodos
  + Integración con BD local

/opt/Erp_core/app/routes/provisioning.py
  + PUT /api/provisioning/tenant/password
  + PUT /api/provisioning/tenant/suspend

/opt/Erp_core/templates/admin_tenants.html
  + Modal de gestión de tenant
  + Funciones: changeAdminPassword(), suspendTenant(), reactivateTenant()
  + Búsqueda e filtros mejorados

NUEVOS ARCHIVOS
══════════════════════════════════════════════════════════════════════════════

/opt/Erp_core/nodo/docs/TENANT_MANAGEMENT.md
  Documentación completa de API y gestión

/opt/Erp_core/scripts/create_techeels.sh
  Script para crear tenant "Techeels"

/opt/Erp_core/scripts/test_tenant_management.sh
  Script para probar todas las funcionalidades

PRÓXIMOS PASOS
══════════════════════════════════════════════════════════════════════════════

1. Crear tenant de prueba:
   bash /opt/Erp_core/scripts/create_techeels.sh

2. Acceder al panel admin:
   https://sajet.us/admin/tenants

3. Probar funcionalidades:
   • Buscar "Techeels" en la tabla
   • Abrir menú (⋮)
   • Cambiar contraseña
   • Suspender/reactivar

4. Validar en API:
   bash /opt/Erp_core/scripts/test_tenant_management.sh

5. Monitorear logs:
   tail -f /opt/Erp_core/logs/api.log

SEGURIDAD
══════════════════════════════════════════════════════════════════════════════

IMPORTANTE: En PRODUCCIÓN cambiar:

1. API Key (línea 28 provisioning.py)
2. Credenciales Cloudflare
3. Contraseña de plantilla
4. Acceso al panel admin (requiere JWT)

Restricciones implementadas:
✅ X-API-KEY requerida para endpoints sensibles
✅ JWT para acceso al panel admin
✅ HTTPS obligatorio
✅ CORS configurado
✅ Rate limiting en proxys

TROUBLESHOOTING
══════════════════════════════════════════════════════════════════════════════

Panel admin no carga tenants:
→ Verificar /api/tenants en navegador console
→ Revisar conectividad a 10.10.10.100:8070
→ Ver logs en /var/log/odoo/odoo.log (PCT 105)

Cambio de contraseña falla:
→ Contraseña < 6 caracteres
→ Tenant no existe
→ API Key incorrecta

Suspensión no funciona:
→ Verificar firewall PCT 160 ↔ PCT 105
→ Revisar estado de servicios:
   systemctl status odoo-local-api (PCT 105)

DNS no se crea:
→ Verificar CF_API_TOKEN en nodo.env
→ Comprobar zone_id en domains.json
→ Ver logs del db_watcher

SOPORTE
══════════════════════════════════════════════════════════════════════════════

Documentación: /opt/Erp_core/nodo/docs/TENANT_MANAGEMENT.md
Guía rápida: /opt/Erp_core/nodo/REFERENCIA_RAPIDA.md
API Reference: /opt/Erp_core/nodo/docs/API.md

═════════════════════════════════════════════════════════════════════════════
EOF
