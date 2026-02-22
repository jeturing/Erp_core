# Combinaciones de Paquetes por Industria y Mercado (Odoo 17)

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


- Fecha de generacion: 2026-02-18
- Fuente: `/opt/extra-addons/V17` (inventario de modulos por `__manifest__.py`)
- Objetivo: definir combinaciones comerciales de lo que ya tenemos disponible para salir a mercado por vertical.

## Paquetes Base Reutilizables

### 1) Paquete Core de Plataforma
Modulos:
- `web`
- `portal`
- `dynamic_odoo`
- `queue_job`
- `document_management_system`

### 2) Paquete Comercial y CRM
Modulos:
- `crm_dashboard`
- `kw_crm_lead_search_panel`
- `sale_mini_dashboard`
- `sale_report_generator`
- `pways_commission_mgmt`
- `product_warranty_management_odoo`

### 3) Paquete POS y Punto de Venta
Modulos:
- `point_of_sale`
- `pos_sale`
- `pos_posagent`
- `bi_pos_stripe_payment`
- `barcode_scanning_sale_purchase`
- `pos_refund_password`

### 4) Paquete Finanzas y Control
Modulos:
- `jeturing_finance_core`
- `jeturing_e_nfc`
- `base_accounting_kit`
- `dynamic_accounts_report`
- `accounting_pdf_reports`
- `invoice_multi_approval`
- `account_payment_approval`
- `om_account_accountant`
- `om_fiscal_year`
- `om_account_followup`

### 5) Paquete RRHH y Nomina
Modulos:
- `ohrms_core`
- `hr_payroll_community`
- `hr_payroll_account_community`
- `ohrms_loan`
- `ohrms_salary_advance`
- `hrms_dashboard`
- `hr_employee_shift`
- `hr_vacation_mngmt`

### 6) Paquete Soporte y Experiencia Cliente
Modulos:
- `odoo_website_helpdesk`
- `lt_helpdesk_esign`
- `enhanced_survey_management`
- `customer_product_qrcode`

### 7) Paquete Omnicanal y Mensajeria
Modulos:
- `us_multichat`
- `us_messenger`
- `whatsapp_mail_messaging`
- `whatsapp_redirect`
- `sh_whatsapp_integration`
- `odoo_twilio_sms`

### 8) Paquete Analitica y Productividad
Modulos:
- `advanced_dynamic_dashboard`
- `activity_dashboard_mngmnt`
- `google_analytics_odoo`
- `excel_report_designer`
- `inventory_advanced_reports`

### 9) Paquete Operacion TI / SaaS
Modulos:
- `odoo_saas_kit`
- `cetmix_tower`
- `cetmix_tower_server`
- `cetmix_tower_git`
- `cetmix_tower_yaml`
- `odoo_rest`

## Combinaciones por Industria y Mercado

## A) Restaurantes, Cafeterias y Dark Kitchens
Mercados objetivo:
- Restaurantes independientes
- Cadenas pequenas de comida rapida
- Dark kitchens y delivery-first

Combinacion recomendada:
- Base: Paquete Core + Paquete POS
- Vertical: `pos_kitchen_screen_odoo`, `table_reservation_in_pos`, `table_reservation_on_website`, `pos_takeaway`, `theme_the_chef`
- Escala: Paquete Omnicanal + Paquete Analitica

## B) Hoteleria y Alojamiento
Mercados objetivo:
- Hoteles boutique
- Hostales y apartahoteles
- Operadores de alojamiento con restaurante propio

Combinacion recomendada:
- Base: Paquete Core + Paquete Finanzas
- Vertical: `hotel_management_odoo`, `front_office_management`, `event_management`
- Escala: Paquete POS + Paquete Soporte

## C) Salud (Clinicas y Laboratorios)
Mercados objetivo:
- Clinicas privadas medianas
- Laboratorios de diagnostico
- Centros medicos ambulatorios

Combinacion recomendada:
- Base: Paquete Core + Paquete Finanzas
- Vertical: `base_hospital_management`, `medical_lab_management`
- Escala: `document_management_system` + Paquete Soporte + Paquete Omnicanal

## D) Educacion (Universidades e Institutos)
Mercados objetivo:
- Universidades privadas
- Institutos tecnicos
- Centros de capacitacion corporativa

Combinacion recomendada:
- Base: Paquete Core + Paquete Comercial
- Vertical: `education_university_management`, `event_management`, `enhanced_survey_management`
- Escala: Paquete Finanzas + Paquete Omnicanal

## E) Gimnasios y Centros Fitness
Mercados objetivo:
- Gimnasios independientes
- Cadenas fitness regionales
- Estudios boutique (crossfit, yoga, indoor cycling)

Combinacion recomendada:
- Base: Paquete Core + Paquete Comercial
- Vertical: `gym_mgmt_system`, `subscription_package`, `website_subscription_package`
- Escala: Paquete POS + Paquete Omnicanal

## F) Belleza, Spa y Barberia
Mercados objetivo:
- Salones de belleza independientes
- Cadenas pequenas de barberia
- Centros de bienestar con reservas online

Combinacion recomendada:
- Base: Paquete Core + Paquete Comercial
- Vertical: `salon_management`, `table_reservation_on_website`
- Escala: Paquete POS + Paquete Omnicanal + Paquete Analitica

## G) Flotas, Rent-a-Car y Movilidad
Mercados objetivo:
- Empresas locales de alquiler de vehiculos
- Flotas corporativas de operacion
- Operadores de movilidad con mantenimiento interno

Combinacion recomendada:
- Base: Paquete Core + Paquete Finanzas
- Vertical: `fleet_rental`, `advanced_fleet_rental`, `fleet_rental_dashboard`, `fleet_vehicle_inspection_management`
- Escala: Paquete Comercial + Paquete Analitica

## H) Eventos y Venue Management
Mercados objetivo:
- Centros de eventos
- Organizadores de bodas y eventos empresariales
- Operadores de venue con venta de tickets

Combinacion recomendada:
- Base: Paquete Core + Paquete Comercial
- Vertical: `venue_booking_management`, `event_management`, `event_ticket_qr_scanner`
- Escala: Paquete POS + Paquete Omnicanal + Paquete Soporte

## I) Parking y Operaciones Urbanas
Mercados objetivo:
- Administradores de parqueaderos privados
- Centros comerciales con parking propio
- Corporativos con estacionamiento de empleados y visitas

Combinacion recomendada:
- Base: Paquete Core + Paquete Finanzas
- Vertical: `odoo_parking_management`, `barcode_scanning_sale_purchase`
- Escala: Paquete POS + Paquete Omnicanal

## J) Retail Omnicanal (Tienda + Web)
Mercados objetivo:
- Retail fisico con expansion digital
- Tiendas de nicho con multiples sucursales
- Comercio con necesidad de postventa y garantia

Combinacion recomendada:
- Base: Paquete Core + Paquete POS + Paquete Comercial
- Vertical: `theme_shopping`, `theme_voltro`, `product_warranty_management_odoo`
- Escala: Paquete Analitica + Paquete Omnicanal + Paquete Soporte

## K) Servicios Profesionales y BPO
Mercados objetivo:
- Consultoras
- Despachos contables
- Empresas de servicios recurrentes

Combinacion recomendada:
- Base: Paquete Core + Paquete Finanzas + Paquete Comercial
- Vertical: `om_recurring_payments`, `invoice_design`, `om_account_daily_reports`
- Escala: Paquete RRHH + `odoo_website_helpdesk`

## L) Oferta SaaS / Odoo as a Service
Mercados objetivo:
- Partners Odoo
- Integradores regionales
- MSP/hosters que venden entornos Odoo gestionados

Combinacion recomendada:
- Base: Paquete Core + Paquete Operacion TI / SaaS
- Vertical: `odoo_saas_kit`, `cetmix_tower_server_queue`, `web_notify`
- Escala: Paquete Comercial + Paquete Finanzas + Paquete Omnicanal

## Matriz Rapida de Go-To-Market

| Industria | Entrada (SMB) | Escalado (Mid-Market) | Alto Valor (Enterprise/Grupo) |
|---|---|---|---|
| Restaurantes | Core + POS | + Reservas + Kitchen | + Omnicanal + Analitica |
| Hoteleria | Core + Finanzas | + Hotel + Front Office | + POS + Soporte |
| Salud | Core + Finanzas | + Hospital/Lab | + Soporte + Omnicanal |
| Educacion | Core + Comercial | + Education + Events | + Finanzas + Omnicanal |
| Fitness/Belleza | Core + Comercial | + Modulo vertical | + POS + Analitica |
| Flotas | Core + Finanzas | + Rental + Inspection | + Comercial + Analitica |
| Eventos/Venues | Core + Comercial | + Booking + Ticket QR | + POS + Omnicanal |
| Retail | Core + POS + Comercial | + Garantias + Tema web | + Analitica + Soporte |
| SaaS Odoo | Core + SaaS Ops | + Tower + REST | + Comercial + Finanzas |

## Notas de Uso Comercial

- Estas combinaciones solo usan modulos presentes en `/opt/extra-addons/V17`.
- Hay modulos duplicados por version/paquete; para implementacion se debe fijar una sola variante por modulo tecnico.
- Recomendacion de preventa: vender por bloques (Base + Vertical + Escala) para simplificar propuesta y pricing.
