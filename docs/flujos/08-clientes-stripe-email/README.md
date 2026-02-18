# 08 - Clientes: Stripe Customer + Email

## Objetivo
Automatizar alta de Stripe Customer y envío de credenciales/reset por email.

## Disparador
- Frontend: `#/clients`
- Botones por fila en clientes

## Secuencia ASCII

```text
[SPA Clients]
   |
   +--> POST /api/customers/{id}/create-stripe-customer
   |       -> crea customer en Stripe -> guarda stripe_customer_id
   |
   +--> POST /api/customers/{id}/send-credentials
   |       -> compone credenciales tenant -> SMTP send
   |
   +--> POST /api/customers/{id}/reset-password
           -> genera password -> SQL en Odoo tenant -> email notify
```

## Endpoints
- `POST /api/customers/{customer_id}/create-stripe-customer`
- `POST /api/customers/{customer_id}/send-credentials`
- `POST /api/customers/{customer_id}/reset-password`
- `POST /api/customers/bulk-create-stripe`

## Servicios
- `app/services/email_service.py`
- `app/services/stripe_connect.py` (cuando aplica split/comisiones)

## Errores típicos
- SMTP credenciales inválidas
- Stripe key sin alcance
- fallo SQL remoto en tenant Odoo
