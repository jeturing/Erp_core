# 🚀 GUÍA RÁPIDA - Frontend Admin Panel

## ⚡ Inicio Rápido (5 minutos)

### Paso 1: Instalar Dependencias
```bash
cd /opt/Erp_core/frontend
npm install
```

### Paso 2: Verificar que el Backend esté activo
```bash
curl -H "X-API-Key: prov-key-2026-secure" \
  http://localhost:4443/api/admin/health
```

Respuesta esperada: `{"status":"healthy"}`

### Paso 3: Iniciar Frontend
```bash
npm run dev
```

### Paso 4: Abrir en navegador
```
http://localhost:5173/admin
```

---

## 🎯 Estructura de Tabs

### 📧 Tab SMTP
- ✅ Ver configuración actual
- ✅ Editar credenciales (host, port, user, pass, from)
- ✅ Probar conexión SMTP
- ✅ Verificar estado
- **Ayuda**: Gmail, Outlook, SendGrid

### 📝 Tab Templates
- ✅ Listar templates activos/inactivos
- ✅ Crear nuevos templates
- ✅ Editar templates existentes
- ✅ Editor HTML enriquecido con Quill.js
- ✅ Insertar variables dinámicas {{var}}
- ✅ Usar plantillas predefinidas (header, footer, alert, button, table)
- ✅ Gestionar tags y variables
- ✅ Vista previa con datos de prueba
- ✅ Activar/desactivar templates

### 💾 Tab Storage
- ✅ Ver umbrales actuales (warning, critical, exceeded)
- ✅ Editar umbrales con sliders
- ✅ Ver alertas activas
- ✅ Resolver alertas
- ✅ Ver estadísticas
- ✅ Configurar notificaciones Slack

---

## 🔑 API Key Management

**Key actual**: `prov-key-2026-secure`

**En el Header**:
- Mostrar/ocultar key con botón 👁️
- Editar key si es necesario
- Estado de conexión

---

## 📝 Flujo: Crear Template

1. **Click** en tab "Templates"
2. **Click** en "Crear Nuevo Template"
3. **Rellenar**:
   - Nombre: "Bienvenida Usuario"
   - Tipo: "transaccional"
   - Asunto: "Bienvenido {{nombre}}"
   - Cuerpo: Click en Rich Editor
4. **En el Editor**:
   - Escribir contenido del email
   - Click en variable "nombre" → Inserta {{nombre}}
   - O usar Plantilla Predefinida → "header" → Inserta HTML
5. **Gestionar Variables**:
   - Input de variable
   - Select de tipo (string, number, float, date, boolean)
   - Click "Agregar Variable"
6. **Gestionar Tags**:
   - Input de tag
   - Click "Agregar Tag"
7. **Vista Previa**:
   - Automática si hay HTML
   - Click "Llenar Datos Prueba" para ver con valores
8. **Guardar**: Click "Crear Template"

---

## 🔧 Configurar SMTP

### Gmail
```
Host: smtp.gmail.com
Puerto: 587
Usuario: tu-email@gmail.com
Contraseña: [App Password generada en https://myaccount.google.com]
De Email: noreply@tudominio.com
De Nombre: Tu Empresa
```

Luego: 🧪 "Probar Conexión"

### Outlook
```
Host: smtp-mail.outlook.com
Puerto: 587
Usuario: tu-email@outlook.com
Contraseña: Tu contraseña
De Email: tu-email@outlook.com
De Nombre: Tu Nombre
```

### SendGrid
```
Host: smtp.sendgrid.net
Puerto: 587
Usuario: apikey
Contraseña: SG.xxxxxxxxxxxxxxxxxxxxxxxxxx
De Email: noreply@tudominio.com
De Nombre: Tu Empresa
```

---

## 📊 Configurar Alertas Storage

### Umbrales
- **Advertencia** (🟡): Usar 70-75%
- **Crítico** (🟠): Usar 85-90%
- **Excedido** (🔴): Usar 95-100%

### Intervalo
- Default: 24 horas
- Min: 1 hora
- Max: 7 días

### Slack (Opcional)
1. Crear webhook en https://api.slack.com/messaging/webhooks
2. Copiar URL: `https://hooks.slack.com/services/...`
3. Habilitar checkbox en Storage
4. Pegar webhook
5. Guardar

---

## 🐛 Troubleshooting

### Error: "Cannot GET /admin"
✅ Solución: Asegúrate que `/opt/Erp_core/frontend/src/routes/admin/+page.svelte` existe

### Error: "API Key inválida"
✅ Solución: Verifica la key en AdminHeader: `prov-key-2026-secure`

### Error: "Cannot find Quill"
✅ Solución: `npm install quill` en el directorio frontend

### Error: "Connection refused 4443"
✅ Solución: Backend no está corriendo
```bash
cd /opt/Erp_core
python -m app.main
# o
uvicorn app.main:app --host 0.0.0.0 --port 4443 --workers 2
```

### Los cambios no aparecen en preview
✅ Solución: Hacer refresh en navegador (F5)

### Variable picker no funciona
✅ Solución: Añadir al menos 1 variable en TemplateManager

---

## 📖 Comandos Útiles

```bash
# Instalar deps
npm install

# Desarrollo (hot reload)
npm run dev

# Build producción
npm run build

# Preview build
npm run preview

# Type check
npm run check

# Limpiar (node_modules)
rm -rf node_modules && npm install
```

---

## 🔗 URLs Importantes

| Recurso | URL |
|---------|-----|
| Frontend | http://localhost:5173/admin |
| Backend API | http://localhost:4443/api/admin |
| Documentación API | /opt/Erp_core/ADMIN_PANEL_TESTS.md |
| Componentes | /opt/Erp_core/frontend/src/routes/admin/components/ |

---

## 📱 Responsive Design

✅ Desktop (1920+px): Todos los componentes
✅ Tablet (768-1024px): Tabs en scroll horizontal, cards en 2 columnas
✅ Mobile (320-768px): Stack vertical, single column, tabs en acordeón

---

## 🔒 Seguridad (Desarrollo)

⚠️ **Nota**: Las siguientes configuraciones son para DESARROLLO

Para PRODUCCIÓN:
1. Usar variables de entorno para API key
2. Implementar Bearer tokens con expiración
3. Usar HTTPS en lugar de HTTP
4. Ocultar endpoints de admin detrás de autenticación
5. Validar CORS apropiadamente
6. Usar Rate limiting

---

## 📝 Archivos Creados

```
/opt/Erp_core/frontend/
├── src/routes/admin/
│   ├── +page.svelte (Dashboard)
│   └── components/
│       ├── AdminHeader.svelte
│       ├── TemplateManager.svelte
│       ├── RichTextEditor.svelte
│       ├── TemplatePreview.svelte
│       ├── SmtpManager.svelte
│       ├── StorageAlertsManager.svelte
│       ├── InlineEdit.svelte
│       └── VariablePicker.svelte
│
├── package.json (con Quill.js añadido)
└── ... resto de archivos SvelteKit
```

---

## ✨ Features Destacados

✅ **Editor Enriquecido**: Quill.js con toolbar completo
✅ **Variables Dinámicas**: Insertar {{var}} automáticamente
✅ **Plantillas Predefinidas**: 5 templates HTML listos
✅ **Vista Previa**: Render en iframe con datos de prueba
✅ **Edición Inline**: Click-to-edit en campos simples
✅ **Validación**: En tiempo real con feedback
✅ **API Integration**: 17 endpoints completamente integrados
✅ **Responsive**: Mobile, tablet, desktop
✅ **Dark Alerts**: Sistema de notificaciones elegante
✅ **TypeScript Ready**: Preparado para tipos

---

## 📊 Status Check

```bash
# Ver si backend está activo
curl http://localhost:4443/api/admin/health

# Ver templates
curl -H "X-API-Key: prov-key-2026-secure" \
  http://localhost:4443/api/admin/email-templates

# Ver config SMTP
curl -H "X-API-Key: prov-key-2026-secure" \
  http://localhost:4443/api/admin/smtp/config

# Ver alertas storage
curl -H "X-API-Key: prov-key-2026-secure" \
  http://localhost:4443/api/admin/storage-alerts/config
```

---

## 🎓 Notas Finales

1. **Backend y Frontend son independientes**: Se comunican vía API REST
2. **API Key en header**: `X-API-Key: prov-key-2026-secure`
3. **Todos los endpoints son GET/POST/PUT**: Sin DELETE (soft delete)
4. **Variables son globales**: Se comparten entre templates
5. **Tags son locales**: Cada template tiene sus propios tags
6. **Preview es sandbox**: No ejecuta código, solo HTML seguro

---

**¡Listo para usar!** 🚀
