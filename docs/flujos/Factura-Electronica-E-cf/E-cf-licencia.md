Documentación Técnica: Sistema e-CF Sajet + jeturing_e_nfc
Fecha: 25 de febrero 2026
Versión módulo: 17.0.2.8.3
Repositorios: jeturing/jeturing_e_nfc · jeturing/Erp_core

1. Arquitectura General
Principios clave:

Certificados X.509 → los gestiona República FEL en su infraestructura. Sajet no los toca.
Credenciales API FEL → cifradas con Fernet en tabla ecf_licenses de Erp_core.
Licencia: online-only. Sin conexión a api.sajet.us → UserError en Odoo, sin certificación.
e-CF: opcional para cualquier país. Un cliente de USA con operaciones en RD puede activarlo desde /portal/ecf-setup.
2. Infraestructura
Servicio	LXC	IP	Puerto
Erp_core API (FastAPI)	160	10.10.10.20	4443
Odoo 17	105	10.10.10.100	8069
PostgreSQL HA Primary	137	10.10.10.137	5432
Proxmox Host	—	10.10.10.1	SSH
Dominios:

API pública: https://api.sajet.us
Portal tenant: https://{subdomain}.sajet.us
Odoo por tenant: https://{subdomain}.sajet.us (vía Cloudflare Tunnel → LXC 105)
3. Estado Actual del Módulo jeturing_e_nfc
3.1 Ruta de instalación
3.2 Versión y Manifiesto
Archivo: jeturing_e_nfc/manifest.py

3.3 Modelos existentes
Archivo: models/init.py

Modelo	Archivo	Propósito
jeturing.enfc.log	ecf_log.py	Log de certificaciones
jeturing.enfc.type	ecf_type.py	Tipos e-CF (31–47)
enfc.mixin	enfc_mixin.py	Mixin compartido
account.move	account_move.py	Facturas + certificación
pos.order	pos_order.py	POS + certificación
jeturing.enfc.api.service	api_service.py	Servicio HTTP a FEL
jeturing.enfc.json.builder	json_builder.py	Construcción JSON DGII
res.config.settings	res_config_settings.py	Configuración en Ajustes
jeturing.enfc.log.handler	detailed_log_handler.py	Log detallado
payment.transaction	payment_transaction.py	Transacciones
res.partner	res_partner.py	Extensión partner
jeturing.province	province.py	Provincias RD
jeturing.municipality	municipality.py	Municipios RD
jeturing.province.municipality	province_municipality.py	Relación prov-mun
jeturing.enfc.validator	validator_mixin.py	Validaciones
jeturing.enfc.diagnostic	diagnostic.py	Diagnóstico sistema
jeturing.ecf.license.client	license_client.py ← NUEVO	Validación licencia online
3.4 Configuración en Odoo (Ajustes)
Archivo: models/res_config_settings.py

Parámetros almacenados en ir.config_parameter:

Parámetro	Clave	Default
URL API FEL	jeturing_e_nfc.api_url	—
Usuario API FEL	jeturing_e_nfc.api_user	—
Contraseña API FEL	jeturing_e_nfc.api_password	—
RNC empresa	jeturing_e_nfc.api_rnc	—
Modo Sandbox	jeturing_e_nfc.api_sandbox	False
Punto de Emisión	jeturing_e_nfc.punto_emision	"1"
Área	jeturing_e_nfc.area	"POS"
Modo Emisión	jeturing_e_nfc.modo_emision	"normal"
Auto recertificación	jeturing_e_nfc.enable_auto_recertification	True
Reintentar duplicados	jeturing_e_nfc.auto_retry_duplicates	True
Máx. reintentos	jeturing_e_nfc.max_recertification_retries	3
3.5 Tipos e-CF soportados
Código	Tipo
31	Crédito Fiscal
32	Consumo
33	Nota de Débito
34	Nota de Crédito
41	Compras
43	Gastos Menores
44	Regímenes Especiales
45	Gubernamental
46	Exportaciones
47	Pagos al Exterior
3.6 Cron Jobs existentes
Archivo: data/cron_jobs.xml

ID	Intervalo	Modelo	Método
ir_cron_ecf_auto_check	1 hora	jeturing.enfc.api.service	cron_check_pending_invoices()
ir_cron_ecf_license_check ← NUEVO	24 horas	jeturing.ecf.license.client	verify_license()
3.7 Fixes aplicados en sesión actual
Archivo	Problema	Fix
account_move.py	1692 líneas (contenido duplicado), 2 action_post	Reducido a 936 líneas, 1 action_post correcto
ecf_log.py	Campo inexistente error_message en _review_logs	Cambiado a message
detailed_log_handler.py	log_warning usaba status='error'	Corregido a status='rejected'
views/ecf_log_views.xml	ID XML duplicado action_jeturing_enfc_log	Reemplazado con contenido de jeturing_enfc_log_views.xml
views/menu.xml	Definía mismo action_jeturing_enfc_log	Vaciado (solo comentario)
static/src/xml/status_flow.xml	< y && sin escapar → XML inválido	Escapado a &lt; y &amp;&amp;
models/__init__.py	diagnostic.py no importado	Agregado from . import diagnostic
static/description/index.html	Descripción vacía	HTML completo con hero, cards, tarifario
__manifest__.py	Versión 17.0.2.8.0	Actualizado a 17.0.2.8.3
4. Erp_core — Estado Actual
4.1 Variables de entorno — .env.production
Archivo: .env.production

Variable	Valor actual	Cambio pendiente
DATABASE_URL	postgresql://jeturing:321Abcd@10.10.10.137:5432/erp_core_db	—
ODOO_DEFAULT_COUNTRY	DO	⚠️ Cambiar a "" (vacío)
FIELD_ENCRYPT_KEY	(en env pero no en archivo)	Reutilizar como Fernet para e-CF
ECF_HMAC_SECRET	NO EXISTE	➕ Agregar (32 bytes hex)
LXC_CONTAINER_ID	105	—
4.2 Modelo Customer — campos e-CF existentes
Archivo: database.py:321 (líneas 348–355)

4.3 Nueva tabla — EcfLicense (PENDIENTE)
Agregar en app/models/database.py:

Campo	Tipo	Descripción
id	Integer PK	—
customer_id	FK → customers.id	Nullable (para licencias sin tenant aún)
fingerprint_hash	String(64), unique	SHA-256 de base_url + db_uuid
is_active	Boolean, default True	Activa/revocada
tier	String(20)	sajet_managed | external
license_token	String(36), unique	UUID4 de referencia
ecf_fel_api_url	String(500)	URL API República FEL
ecf_fel_user	String(200)	Usuario API FEL
ecf_fel_password_enc	Text	Contraseña cifrada con Fernet
ecf_punto_emision	String(10), default "1"	Punto de emisión
ecf_area	String(20), default "POS"	Área de emisión
ecf_environment	String(20), default "test_ecf"	test_ecf | production
ecf_monthly_fel_cost	Float	Costo mensual República FEL
subdomain	String(100)	Subdominio del tenant
created_at	DateTime	—
updated_at	DateTime (onupdate)	—
4.4 Routers actuales en main.py
Archivo: app/main.py

44 routers registrados. Pendiente agregar:

from .routes import ecf_setup → app.include_router(ecf_setup.router)
from .routes import ecf_license → app.include_router(ecf_license.router)
4.5 Endpoints del onboarding multi-país
Archivo: app/routes/customer_onboarding.py

Método	Ruta	Descripción
GET	/api/customer-onboarding/status	Estado actual del onboarding
POST	/api/customer-onboarding/set-password	Paso 0→1
POST	/api/customer-onboarding/update-profile	Paso 1→2/3 (detecta país)
POST	/api/customer-onboarding/ecf-questionnaire	Paso 2→3 (solo DO)
POST	/api/customer-onboarding/skip-ecf	Saltar paso e-CF
POST	/api/customer-onboarding/complete	Finalizar onboarding
Lógica multi-país actual (línea 268):

⚠️ Con el fix, ODOO_DEFAULT_COUNTRY deja de ser "DO" → clientes US no ven paso e-CF. La ruta /portal/ecf-setup queda accesible independientemente del país para quienes lo activen post-onboarding.

4.6 Migraciones Alembic existentes
Directorio: alembic/versions/

Revisión	Descripción
4cdf703...	000 Baseline
e8deb7b...	001 Epic1 all new tables
a3f1c2d...	002 Partner pricing overrides
b4e2a5f...	003 Remove email unique constraint
c5f3b6d...	004 Add plan quota fields
d6a4b7c...	005 Partner portal auth
e7b5c9d...	006 Customer onboarding ECF
f8c6d1e...	007 Onboarding config table
g9d7e2f...	008 Work orders blueprint fields
h0e8f3a...	009 Security refresh tokens TOTP
i1f9g4a...	010 Partner code column
j2g0h5b...	011 Admin users table
k3h1i6c...	012 Email verify agreements
l4i2j7d...	013 Landing i18n
m5j3k8l...	014 Add missing plan/customer columns
n6k4l9m...	015 Partners slug + accountant access
o7l5m0n1...	016 EcfLicense table ← PENDIENTE
5. Plan de Implementación — Fase 8
5.1 Variables de entorno (.env.production)
Agregar al final del archivo:

Cambiar:

5.2 Nuevos archivos en Erp_core
app/routes/ecf_license.py
Endpoint exclusivo para consumo del módulo Odoo:

app/routes/ecf_setup.py
Portal del cliente para configurar e-CF:

5.3 Nuevo archivo en jeturing_e_nfc
models/license_client.py
Importar en models/init.py:

Agregar cron en data/cron_jobs.xml:

5.4 Frontend — Nueva página Svelte
Archivo a crear: frontend/src/routes/EcfSetup.svelte

Accesible en: https://{tenant}.sajet.us/portal/ecf-setup

Secciones:

Estado actual — badge activo/inactivo, tier, ambiente
Formulario configuración — RNC, URL API FEL, usuario, contraseña, punto de emisión, área, ambiente
Tabla de costos — tarifario República FEL presentado como "Costo por uso del servicio"
5.5 Tarifario República FEL (referencia para /api/ecf-setup/pricing)
Rango mensual	Costo/mes
1–1,000 docs	$50
1,001–2,000	$85
2,001–3,000	$115
3,001–4,000	$130
4,001–5,000	$152
5,001–6,000	$174
6,001–7,000	$197
7,001–8,000	$219
8,001–9,000	$236
9,001–10,000	$260
>10,000	$0.021–$0.012/doc (por volumen)
Anual: 1–3,000 docs = $100/año · 1–7,500 docs = $225/año

6. Flujo Completo de Activación e-CF
7. Secuencia de Deploy
LXC 160 (Erp_core)
LXC 105 (Odoo)
8. Dependencias Técnicas
Erp_core (requirements.txt)
cryptography>=41.0.7 ✅ ya instalada (Fernet disponible)
hashlib ✅ stdlib Python (HMAC disponible)
uuid ✅ stdlib Python
jeturing_e_nfc (Odoo)
requests ✅ disponible en Odoo 17
hashlib, hmac ✅ stdlib Python
Documento generado en sesión de desarrollo — no publicar externamente.