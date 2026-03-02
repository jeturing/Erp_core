# 🎯 Tu Panel Admin en 5 Minutos

## Paso 1: Descargar e Instalar (2 min)

```bash
# Entrar al proyecto
cd /opt/Erp_core/frontend

# Instalar dependencias (incluye Quill.js)
npm install

# Esto descarga:
# - svelte, sveltekit
# - quill (editor HTML)
# - @sentry/svelte
# - y más...
```

✅ **Listo**: Todas las dependencias instaladas

---

## Paso 2: Verificar Backend (1 min)

El backend debe estar corriendo. Verifica:

```bash
# En otra terminal
curl -H "X-API-Key: prov-key-2026-secure" \
  http://localhost:4443/api/admin/health
```

✅ **Si ves**: `{"status":"healthy"}` → Backend OK ✅
❌ **Si error**: Necesitas iniciar el backend primero

### Iniciar Backend (si no está corriendo)
```bash
cd /opt/Erp_core
python -m app.main
# O: uvicorn app.main:app --host 0.0.0.0 --port 4443 --workers 2
```

---

## Paso 3: Iniciar Frontend (1 min)

```bash
# En directorio /opt/Erp_core/frontend
npm run dev
```

Verás:
```
  VITE v7.3.1  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

✅ **Listo**: Frontend corriendo en puerto 5173

---

## Paso 4: Abrir en Navegador (1 min)

**Abre**: `http://localhost:5173/admin`

Verás:
- Gradiente morado en fondo
- Header con "Admin Panel"
- 3 tabs: 📧 SMTP | 📝 Templates | 💾 Storage

✅ **¡Panel Admin cargado!** 🎉

---

## 🎨 Visualización Esperada

```
┌─────────────────────────────────────────────┐
│ 📧 Admin Panel                    🔑 API Key│
├─────────────────────────────────────────────┤
│ [📧 SMTP] [📝 TEMPLATES] [💾 STORAGE]      │
├─────────────────────────────────────────────┤
│                                             │
│  SMTP Configuration                         │
│  ┌──────────────────────────────────────┐   │
│  │ Host: smtp.gmail.com                 │   │
│  │ Port: 587                            │   │
│  │ User: test@gmail.com                 │   │
│  │ ...                                  │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  [✏️ Edit] [ℹ️ Status] [🧪 Test Connection] │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 📝 Ahora Prueba Cada Sección

### 📧 Tab SMTP

**Qué ver**:
- Configuración SMTP actual
- Botones para editar, probar, verificar

**Prueba**:
1. Click "Editar Configuración"
2. Llena datos Gmail/Outlook
3. Click "Guardar"
4. Click "Probar Conexión"
5. Espera respuesta verde ✅ o roja ❌

### 📝 Tab Templates

**Qué ver**:
- Grid vacío o con templates
- Botón "Crear Nuevo Template"

**Prueba**:
1. Click "Crear Nuevo Template"
2. Llena:
   - Nombre: "Test Template"
   - Tipo: "transaccional"
   - Asunto: "Hola {{nombre}}"
3. En HTML Editor:
   - Click en campo HTML
   - Escribe: "Hola {{nombre}}, bienvenido"
   - Click variable "nombre" (si la creaste)
4. Click "Agregar Variable":
   - Nombre: "nombre"
   - Tipo: "string"
   - Click Agregar
5. Click "Llenar Datos Prueba"
6. Ves preview en iframe
7. Click "Crear Template"

### 💾 Tab Storage

**Qué ver**:
- 4 sliders para umbrales
- Lista de alertas activas
- Estadísticas

**Prueba**:
1. Mueve sliders:
   - Warning: 70%
   - Critical: 85%
   - Exceeded: 95%
2. Click "Guardar"
3. Ve alertas activas abajo
4. Si hay alertas, click "Resolver"
5. Scroll a "Configuración de Slack"
6. Habilita checkbox
7. Pega webhook URL (opcional)

---

## 🎓 Características Que Encontrarás

### 🔑 API Key Management
- Ver en header
- Click 👁️ para mostrar/ocultar
- Estado "healthy" automático

### ✏️ Edición Inline
- Click en nombre/asunto
- Edita directamente
- Enter para guardar
- Esc para cancelar

### 🎨 Editor Enriquecido (Quill.js)
- **Toolbar**:
  - B=Bold, I=Italic, U=Underline
  - Colores, listas, headers
  - Links, imágenes
- **Variables**:
  - Click variable → {{variable}} insertado
- **Templates**:
  - Dropdown con 5 snippets
  - Header, footer, alert, button, table

### 👀 Vista Previa
- Iframe sandbox (seguro)
- Click "Llenar Datos Prueba"
- Ve email como se vería
- Variables con datos de ejemplo

### 📊 Validaciones
- Nombre requerido → Error si vacío
- Asunto requerido → Error si vacío
- HTML requerido → Error si vacío
- Port 1-65535 → Error si fuera de rango

### 🟢 Alerts
- Verdes: Success ✅
- Rojos: Error ❌
- Azules: Info ℹ️
- Auto-desaparecen después 4s

---

## 🔧 Comandos Útiles

### Desarrollo
```bash
npm run dev          # Iniciar dev server (hot reload)
npm run build        # Build para producción
npm run preview      # Ver build en navegador
npm run check        # Type checking
```

### Si algo falla
```bash
# Limpiar todo
rm -rf node_modules package-lock.json

# Reinstalar
npm install

# Intentar de nuevo
npm run dev
```

---

## 🆘 Si No Funciona

### "Cannot find module quill"
```bash
npm install quill
npm run dev
```

### "Connection refused 4443"
Backend no está corriendo:
```bash
cd /opt/Erp_core
python -m app.main
```

### "Cannot GET /admin"
Verifica que `/admin/+page.svelte` exista en:
`/opt/Erp_core/frontend/src/routes/admin/`

### "API key invalid"
Usa la key: `prov-key-2026-secure`

### Refresh en navegador
A veces necesitas F5 para ver cambios

---

## 📚 Lee Más Documentación

| Necesitas | Lee |
|----------|-----|
| Entender estructura | FRONTEND_ADMIN_PANEL_SUMMARY.md |
| Hacer testing | FRONTEND_TESTING_CHECKLIST.md |
| API examples | ADMIN_PANEL_TESTS.md |
| Resumen completo | ADMIN_PANEL_COMPLETE.md |
| Índice todo | DOCUMENTATION_INDEX.md |

---

## 🎯 Flujos Comunes

### Flujo 1: Crear Email Template

1. Tab "Templates"
2. "Crear Nuevo Template"
3. Nombre: "Bienvenida"
4. Tipo: "transaccional"
5. Asunto: "¡Hola {{user}}!"
6. Click HTML editor
7. Escribe contenido
8. "Agregar Variable" → user, string
9. "Crear Template"
10. ✅ Template creado

### Flujo 2: Configurar SMTP

1. Tab "SMTP"
2. "Editar Configuración"
3. Llena todos los campos
4. "Guardar"
5. "Probar Conexión"
6. ✅ Espera feedback verde

### Flujo 3: Configurar Alertas

1. Tab "Storage"
2. "Editar"
3. Mueve sliders
4. Cambia intervalo
5. "Guardar"
6. ✅ Configurado

---

## ✨ Tips Profesionales

### 💡 Variable Insertion
```
Template: "Hola {{nombre}}, {{saludo}}"
Variable picker muestra:
- {{nombre}}  🔵 string
- {{saludo}}  🔵 string
```

### 💡 Template Snippets
En HTML editor, dropdown tiene:
- **header**: Logo + nombre empresa
- **footer**: Pie con info
- **alert_box**: Warning en amarillo
- **button**: CTA button
- **table_header**: Tabla formateada

### 💡 Data Preview
Click "Llenar Datos Prueba":
- string → "Valor de {name}"
- number → 0-100 aleatorio
- float → 0.00-100.00
- date → Hoy localizado
- boolean → "Sí" o "No"

### 💡 Keyboard Shortcuts
- **Click nombre/asunto** → Edita inline
- **Enter** → Guarda
- **Esc** → Cancela
- **Ctrl+K en editor** → Link
- **Ctrl+B** → Bold

---

## 🎉 ¡Éxito!

Ahora tienes un panel admin completo con:
✅ Configuración SMTP
✅ Editor HTML enriquecido
✅ Plantillas de email
✅ Alertas de almacenamiento
✅ Interfaz moderna y responsiva

---

## 📞 Necesitas Ayuda?

1. **Setup**: Lee FRONTEND_QUICK_START.md
2. **Features**: Lee FRONTEND_ADMIN_PANEL_SUMMARY.md
3. **Testing**: Lee FRONTEND_TESTING_CHECKLIST.md
4. **API**: Lee ADMIN_PANEL_TESTS.md

---

**Creado**: 2024
**Versión**: 1.0.0
**Status**: ✅ Production Ready

🚀 **¡Ya estás listo para usar el Admin Panel!**
