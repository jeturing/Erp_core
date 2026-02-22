# 09 - Ecosistema Partners (Leads/Comisiones/Cotizaciones)

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


## Objetivo
Gestionar ciclo comercial de partners: leads, comisiones y cotizaciones con integración de cobro.

## Disparador
- Frontend:
  - `#/partners`
  - `#/leads`
  - `#/commissions`
  - `#/quotations`

## Secuencia ASCII

```text
[Partner/Admin en SPA]
   |
   +--> CRUD Partners (/api/partners)
   +--> CRUD Leads (/api/leads)
   +--> CRUD Commissions (/api/commissions)
   +--> CRUD Quotations (/api/quotations)
   v
[Backend routes]
   |
   +--> persistencia SQLAlchemy
   +--> reglas de estado/pipeline
   +--> notificaciones (email)
   +--> opcional Stripe Connect (split/payout)
   v
[Reportes y operación comercial]
```

## Stripe Connect (resumen)
- `/api/stripe-connect/create-account`
- `/api/stripe-connect/{partner_id}/onboarding-link`
- `/api/stripe-connect/{partner_id}/status`
- `/api/stripe-connect/transfer`

## Errores típicos
- Partner sin onboarding completo
- comisión en estado no transferible
- tasas/fees mal configuradas
