# Extra Addons - Plan de Migración Odoo 17 → 19

Este directorio contiene:

- `V17/`: módulos fuente (base actual en Odoo 17)
- `V19/`: destino de migración (actualmente vacío)

## Objetivo

Migrar de forma incremental los módulos de `V17` a `V19`, priorizando continuidad operativa y reducción de riesgo.

## Enfoque simple (por etapas)

### Etapa 1: Inventario y priorización

- Confirmar módulos activos en producción
- Agrupar por dominio (Contabilidad, RRHH, Ventas/CRM, POS, Website, Integraciones)
- Definir prioridad: Alta / Media / Baja

**Salida:** backlog priorizado y alcance aprobado.

### Etapa 2: Migración núcleo (Alta prioridad)

- Migrar primero módulos críticos de negocio
- Ajustar `__manifest__.py`, dependencias y seguridad
- Corregir vistas XML y assets web incompatibles

**Salida:** módulos críticos instalables y funcionales en Odoo 19.

### Etapa 3: Migración funcional (Media prioridad)

- Migrar reportes, dashboards y automatizaciones
- Migrar integraciones externas (ej. WhatsApp, Stripe, API REST)
- Validar permisos, flujos y datos

**Salida:** operación completa del core + soporte funcional ampliado.

### Etapa 4: Estabilización y cierre

- QA final por dominio
- Hardening de seguridad y rendimiento
- Documentación final y handoff

**Salida:** release candidata de `V19` lista para despliegue.

## Criterios mínimos por módulo

Un módulo se considera "migrado" cuando cumple:

1. Instala sin errores en Odoo 19
2. Sus menús/vistas principales cargan
3. Seguridad (`ir.model.access.csv`) válida
4. Flujo principal probado de extremo a extremo
5. Sin dependencias rotas

## Convención recomendada

- Mantener en `V19` un módulo por carpeta
- Evitar duplicados/versionados mezclados en nombre
- Registrar estado en `Migration.md`

## Próximo paso

Usar `Migration.md` como tablero vivo y avanzar por oleadas (Alta → Media → Baja).