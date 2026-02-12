#!/bin/bash
# Comandos de ejemplo para gestión de tenants

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════════════╗
║                   EJEMPLOS DE USO - GESTIÓN DE TENANTS                    ║
╚════════════════════════════════════════════════════════════════════════════╝

═════════════════════════════════════════════════════════════════════════════
1. CREAR TENANT "TECHEELS"
═════════════════════════════════════════════════════════════════════════════

bash /opt/Erp_core/scripts/create_techeels.sh

O manualmente con curl:

curl -X POST https://sajet.us/api/provisioning/tenant \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "admin_password": "Techeels2026!",
    "domain": "sajet.us"
  }'

Respuesta esperada:
{
  "success": true,
  "subdomain": "techeels",
  "url": "https://techeels.sajet.us",
  "database": "techeels",
  "dns_created": true
}

═════════════════════════════════════════════════════════════════════════════
2. LISTAR TODOS LOS TENANTS
═════════════════════════════════════════════════════════════════════════════

curl -X GET https://sajet.us/api/tenants

Muestra todos los tenants con:
- Nombre de empresa
- Email
- Subdominio
- Plan (basic, pro, enterprise)
- Estado (active, suspended, pending, etc)
- Nodo donde está alojado

═════════════════════════════════════════════════════════════════════════════
3. CAMBIAR CONTRASEÑA ADMIN DE TECHEELS
═════════════════════════════════════════════════════════════════════════════

Via API:

curl -X PUT https://sajet.us/api/provisioning/tenant/password \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "new_password": "TecheelsNueva2026!"
  }'

Via Panel Admin:
1. Accede a https://sajet.us/admin/tenants
2. Busca "Techeels" en la tabla
3. Haz clic en el menú ⋮ (tres puntos)
4. Se abre modal de gestión
5. Ingresa nueva contraseña en campo "Nueva Contraseña Admin"
6. Haz clic en botón "Cambiar"
7. Confirmación: "Contraseña actualizada exitosamente"

Respuesta API:
{
  "success": true,
  "subdomain": "techeels",
  "message": "Contraseña actualizada exitosamente"
}

═════════════════════════════════════════════════════════════════════════════
4. SUSPENDER TENANT (POR FALTA DE PAGO)
═════════════════════════════════════════════════════════════════════════════

Via API:

curl -X PUT https://sajet.us/api/provisioning/tenant/suspend \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "suspend": true,
    "reason": "Suspensión por falta de pago - Factura vencida hace 30 días"
  }'

Via Panel Admin:
1. Accede a https://sajet.us/admin/tenants
2. Busca "Techeels"
3. Abre menú ⋮
4. Botón rojo "Suspender"
5. Confirmación: "¿Suspender el servicio? Los usuarios no podrán acceder"
6. Click aceptar
7. Status cambia a "Suspendido" (rojo)

Respuesta API:
{
  "success": true,
  "subdomain": "techeels",
  "suspended": true,
  "reason": "Suspensión por falta de pago - Factura vencida hace 30 días",
  "message": "Tenant suspendido exitosamente"
}

QUÉ SUCEDE EN LA BD:
- UPDATE res_users SET active = false (usuarios no pueden acceder)
- INSERT ir_config_parameter: tenant.suspended = true
- INSERT ir_config_parameter: tenant.suspend_reason = '...'
- Datos íntegros, solo acceso bloqueado
- Admin puede acceder (usuario 1 no es desactivado)

═════════════════════════════════════════════════════════════════════════════
5. REACTIVAR TENANT (DESPUÉS DEL PAGO)
═════════════════════════════════════════════════════════════════════════════

Via API:

curl -X PUT https://sajet.us/api/provisioning/tenant/suspend \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels",
    "suspend": false
  }'

Via Panel Admin:
1. Accede a https://sajet.us/admin/tenants
2. Filtra por "Suspendidos"
3. Busca "Techeels"
4. Abre menú ⋮
5. Botón verde "Reactivar"
6. Confirmación: "¿Reactivar? Los usuarios podrán acceder nuevamente"
7. Click aceptar
8. Status cambia a "Activo" (verde)

Respuesta API:
{
  "success": true,
  "subdomain": "techeels",
  "suspended": false,
  "message": "Tenant reactivado exitosamente"
}

QUÉ SUCEDE EN LA BD:
- UPDATE res_users SET active = true (usuarios pueden acceder nuevamente)
- UPDATE ir_config_parameter SET value = 'false' WHERE key = 'tenant.suspended'
- Todas las aplicaciones siguen funcionando
- Sin pérdida de datos
- Sin reconfiguraciones

═════════════════════════════════════════════════════════════════════════════
6. ELIMINAR TENANT COMPLETAMENTE
═════════════════════════════════════════════════════════════════════════════

ADVERTENCIA: Esta acción es irreversible - elimina toda la BD

curl -X DELETE https://sajet.us/api/provisioning/tenant \
  -H "X-API-KEY: prov-key-2026-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "techeels"
  }'

Respuesta:
{
  "success": true,
  "database_deleted": true,
  "dns_deleted": true
}

═════════════════════════════════════════════════════════════════════════════
CASOS DE USO PRÁCTICOS
═════════════════════════════════════════════════════════════════════════════

CASO 1: Cliente nuevo
→ Panel admin → "Nuevo Tenant"
→ Llena formulario (empresa, email, subdominio, plan)
→ Click "Crear"
→ Sistema: crea BD, DNS, configura Odoo
→ 2-3 minutos → Estado "Activo"
→ Email a cliente con URL y contraseña

CASO 2: Cliente olvida contraseña
→ Admin: Cambiar contraseña desde panel
→ Nueva clave temporal
→ Email al cliente
→ Cliente accede con clave temporal
→ Cambia su propia contraseña en Odoo

CASO 3: Cliente no paga a los 30 días
→ Sistema detecta vencimiento
→ Admin abre panel admin
→ Busca cliente vencido
→ Click menú → "Suspender"
→ Razón: "Factura vencida desde hace 30 días"
→ Click confirmar
→ Cliente intenta acceder → "Servicio suspendido"
→ Cliente no puede ver sus datos
→ Datos conservados en BD

CASO 4: Cliente paga después de 15 días
→ Admin ve pago en sistema de facturación
→ Abre panel admin
→ Filtro: "Suspendidos"
→ Busca cliente
→ Click menú → "Reactivar"
→ Confirmación
→ Cliente accede nuevamente sin problemas
→ Todos sus datos intactos
→ Como si nunca hubiera estado suspendido

═════════════════════════════════════════════════════════════════════════════
ESTADO DE TENANTS EN PANEL ADMIN
═════════════════════════════════════════════════════════════════════════════

Estado           Color      Significado
─────────────────────────────────────────
✅ Activo        Verde      Operativo, usuarios accediendo
⏳ Provisionando Azul       En creación, esperar 1-2 minutos
❌ Suspendido    Rojo       Bloqueado por falta de pago
⏸️  Pendiente     Amarillo   En proceso de configuración
❌ Cancelado     Gris       Eliminado del sistema

═════════════════════════════════════════════════════════════════════════════
FILTROS DEL PANEL ADMIN
═════════════════════════════════════════════════════════════════════════════

Filtro por estado:
  Todos → muestra todos
  Activos → solo operativos
  Pendientes → en creación
  Suspendidos → bloqueados por pago

Filtro por plan:
  Todos los planes
  Basic ($29/mes)
  Pro ($49/mes)
  Enterprise ($99/mes)

Filtro por nodo:
  Todos los nodos
  Node 1 (LXC 105)
  Node 2 (LXC 106)
  Node N (cuando se agregue)

Búsqueda:
  Por nombre empresa: "Techeels"
  Por email: "admin@techeels.com"
  Por subdominio: "techeels"

═════════════════════════════════════════════════════════════════════════════
LOGS Y MONITOREO
═════════════════════════════════════════════════════════════════════════════

Ver logs de API (PCT 160):
  tail -f /var/log/supervisor/fastapi-app-stderr.log
  tail -f /var/log/supervisor/fastapi-app-stdout.log

Ver logs de nodo (PCT 105):
  tail -f /var/log/supervisor/odoo-local-api-stderr.log
  systemctl status odoo-local-api

Ver logs de BD Watcher (PCT 105):
  systemctl status odoo-db-watcher
  journalctl -u odoo-db-watcher -f

═════════════════════════════════════════════════════════════════════════════
AUTOMATIZACIÓN CON SCRIPTS
═════════════════════════════════════════════════════════════════════════════

Crear múltiples tenants:

for i in {1..5}; do
  curl -X POST https://sajet.us/api/provisioning/tenant \
    -H "X-API-KEY: prov-key-2026-secure" \
    -H "Content-Type: application/json" \
    -d "{
      \"subdomain\": \"cliente$i\",
      \"admin_password\": \"ClaveSegura$i!\"
    }"
  sleep 2  # Esperar entre creaciones
done

Suspender todos los tenants de un plan:

TENANTS=$(curl -s https://sajet.us/api/tenants | jq -r '.items[] | select(.plan=="basic") | .subdomain')

for TENANT in $TENANTS; do
  curl -X PUT https://sajet.us/api/provisioning/tenant/suspend \
    -H "X-API-KEY: prov-key-2026-secure" \
    -H "Content-Type: application/json" \
    -d "{
      \"subdomain\": \"$TENANT\",
      \"suspend\": true,
      \"reason\": \"Falta de pago - Plan Basic vencido\"
    }"
done

═════════════════════════════════════════════════════════════════════════════

¿Dudas? Ver documentación:
  /opt/Erp_core/nodo/docs/TENANT_MANAGEMENT.md
  /opt/Erp_core/TENANT_MANAGEMENT_README.md

EOF
