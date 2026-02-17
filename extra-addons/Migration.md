# Migration Tracker - Odoo 17 → 19

Documento operativo para ejecutar la migración por etapas.

## Estado actual (baseline)

- Fuente: `extra-addons/V17`
- Destino: `extra-addons/V19`
- Estado destino: sin módulos migrados aún

## Flujo de trabajo por módulo

1. Seleccionar módulo del backlog
2. Copiar a `V19` y normalizar estructura
3. Ajustar `__manifest__.py` y dependencias
4. Corregir Python/ORM si aplica
5. Corregir XML/QWeb/assets JS
6. Revisar seguridad (`security/ir.model.access.csv`, reglas)
7. Probar instalación y flujo principal
8. Marcar estado y evidencias

## Checklist técnico rápido

- [ ] `__manifest__.py` compatible con Odoo 19
- [ ] Dependencias disponibles en Odoo 19
- [ ] Vistas XML sin errores de carga
- [ ] Assets web y JS compatibles
- [ ] ACLs y reglas de seguridad válidas
- [ ] Datos demo/init sin romper instalación
- [ ] Prueba funcional principal completada

## Matriz simple de seguimiento

| Grupo | Prioridad | Estado | Owner | Bloqueos | Evidencia |
|---|---|---|---|---|---|
| Contabilidad y facturación | Alta | Pendiente | Por asignar | N/A | N/A |
| RRHH y nómina | Alta | Pendiente | Por asignar | N/A | N/A |
| Ventas / CRM | Alta | Pendiente | Por asignar | N/A | N/A |
| POS y restaurante | Media | Pendiente | Por asignar | N/A | N/A |
| Website / Portal / Themes | Media | Pendiente | Por asignar | N/A | N/A |
| Integraciones (WhatsApp/Stripe/API) | Alta | Pendiente | Por asignar | N/A | N/A |
| Verticales (hotel, gym, salud, educación) | Baja | Pendiente | Por asignar | N/A | N/A |
| Utilidades técnicas (queue, web helpers) | Alta | Pendiente | Por asignar | N/A | N/A |

## Estados permitidos

- `Pendiente`
- `En análisis`
- `En migración`
- `En pruebas`
- `Listo`
- `Bloqueado`

## Criterio de cierre por etapa

Una etapa se cierra cuando:

- Todos los módulos de esa etapa están en estado `Listo`
- No hay bloqueos críticos abiertos
- QA funcional mínima aprobada

## Decisiones pendientes

- Confirmar lista de módulos realmente activos en producción
- Definir owners técnicos por grupo
- Definir entorno de pruebas Odoo 19
- Definir política de módulos deprecados/no migrables
