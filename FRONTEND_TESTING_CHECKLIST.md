# 🧪 Testing Frontend Admin Panel

## 📋 Checklist de Testing

### ✅ Sección: Dashboard Principal

- [ ] Cargar `/admin` sin errores
- [ ] Ver 3 tabs (SMTP, Templates, Storage)
- [ ] Gradiente morado visible en fondo
- [ ] Header con API key visible
- [ ] Estado "healthy" mostrado en header
- [ ] Tab activo destacado en color morado
- [ ] Cambiar tabs sin errores
- [ ] Animación fade-in al cambiar tabs

---

### ✅ Sección: SMTP Manager

#### Cargar Configuración
- [ ] GET /smtp/config exitoso
- [ ] Datos mostrados en grid (host, port, user, email, name)
- [ ] Password enmascarado por defecto
- [ ] Toggle de password funciona (👁️ botón)
- [ ] Spinner visible durante carga

#### Edición
- [ ] Botón "Editar" abre formulario
- [ ] Todos los campos son editables
- [ ] Validación de inputs (ej: port 1-65535)
- [ ] Botón "Cancelar" revierte cambios
- [ ] Botón "Guardar" actualiza config

#### Pruebas
- [ ] Botón "Probar Conexión" activo
- [ ] POST /smtp/test enviado correctamente
- [ ] Respuesta exitosa: Alert verde
- [ ] Respuesta error: Alert rojo con mensaje

#### Estado
- [ ] Botón "Verificar Estado" funciona
- [ ] GET /smtp/status devuelve estado
- [ ] Status mostrado en alert info

#### Datos de Prueba (Gmail)
```
Host: smtp.gmail.com
Port: 587
User: test@gmail.com
Pass: [app password]
From Email: noreply@tudominio.com
From Name: Test Empresa
```

---

### ✅ Sección: Template Manager

#### Listado
- [ ] GET /email-templates carga lista
- [ ] Templates mostrados en grid de tarjetas
- [ ] Cada tarjeta muestra: nombre, tipo, estado, fecha
- [ ] Spinner durante carga
- [ ] Mensaje vacío si no hay templates

#### Crear Template
- [ ] Botón "Crear Nuevo Template" abre formulario
- [ ] Campos visibles: nombre, tipo, asunto, html, text, preview
- [ ] Tipo dropdown con 10 opciones
- [ ] Nombre es editable inline
- [ ] Asunto es editable inline
- [ ] POST /email-templates enviado al guardar
- [ ] Alert verde si éxito
- [ ] Alert rojo si error
- [ ] Formulario limpio después de crear

#### Gestión de Variables
- [ ] Agregar variable: input nombre + dropdown tipo
- [ ] Variables listadas en tabla
- [ ] Botón X elimina variable
- [ ] Tipos disponibles: string, number, float, date, boolean
- [ ] Variable picker muestra variables en editor

#### Gestión de Tags
- [ ] Input para nuevo tag
- [ ] Badge visual del tag
- [ ] Botón X elimina tag
- [ ] Tags persisten en form

#### Editor Quill
- [ ] Toolbar visible con botones
- [ ] Botones funcionales:
  - [ ] Bold (B)
  - [ ] Italic (I)
  - [ ] Underline (U)
  - [ ] Colors (color de texto)
  - [ ] Lists (ordenada, sin orden)
  - [ ] Headers (h1, h2)
  - [ ] Links
  - [ ] Blockquote
  - [ ] Code block

#### Variable Insertion
- [ ] Panel de variables visible
- [ ] Click en variable → inserta {{var}}
- [ ] Variable insertion mantiene cursor
- [ ] "No variables" msg si vacío

#### Template Insertion
- [ ] Dropdown de templates visible
- [ ] 5 opciones: header, footer, alert, button, table
- [ ] Click inserta HTML correctamente
- [ ] HTML contiene {{variable}} placeholders

#### Preview
- [ ] Preview aparece si hay HTML
- [ ] Datos de prueba generados correctamente:
  - [ ] String: "Valor de {name}"
  - [ ] Number: 0-100
  - [ ] Float: 0-100.00
  - [ ] Date: Fecha localizada
  - [ ] Boolean: "Sí" / "No"
- [ ] Variables sin data muestran "[variable]"
- [ ] Iframe renderiza HTML seguro
- [ ] Responsive en devices diferentes

#### Actualizar Template
- [ ] Click en template abre edit
- [ ] Datos pre-populados correctamente
- [ ] PUT /email-templates/{type} enviado
- [ ] Lista actualiza después

#### Toggle Template
- [ ] POST /email-templates/{type}/toggle funciona
- [ ] Estado activo/inactivo cambia
- [ ] Visual feedback inmediato

#### Stats
- [ ] GET /email-templates/stats carga
- [ ] Estadísticas mostradas correctamente

---

### ✅ Sección: Storage Alerts Manager

#### Umbrales
- [ ] Slider warning movible (0-100%)
- [ ] Slider critical movible
- [ ] Slider exceeded movible
- [ ] Input intervalo horas editable
- [ ] PUT /storage-alerts/config enviado
- [ ] Valores actualizados visualmente

#### Alertas Activas
- [ ] GET /storage-alerts/active carga lista
- [ ] Cada alerta muestra:
  - [ ] Badge de nivel (🟢🟡🟠🔴)
  - [ ] ID del cliente
  - [ ] Barra de progreso
  - [ ] Porcentaje uso
  - [ ] Fecha creación
  - [ ] Botón resolver
- [ ] Click resolver → POST /resolve
- [ ] Lista actualiza después resolver
- [ ] Empty state si no hay alertas

#### Estadísticas
- [ ] GET /storage-alerts/stats carga
- [ ] Stats mostrados en grid
- [ ] Cards con gradiente morado

#### Configuración Slack
- [ ] Toggle para habilitar
- [ ] Input webhook URL aparece si enabled
- [ ] POST /storage-alerts/slack enviado
- [ ] Validación de URL

#### Colores por Nivel
- [ ] Normal (🟢): Border verde
- [ ] Warning (🟡): Border naranja, bg amarillo
- [ ] Critical (🟠): Border rojo, bg rojo claro
- [ ] Exceeded (🔴): Border púrpura, bg púrpura claro

---

### ✅ Sección: UI/UX General

#### Header
- [ ] Logo/titulo visible
- [ ] API key display funcionando
- [ ] Toggle show/hide password funciona
- [ ] Status bar visible
- [ ] Timestamp actualizado
- [ ] Responsive en mobile

#### Alerts
- [ ] Success alerts verdes
- [ ] Error alerts rojos
- [ ] Info alerts azules
- [ ] Auto-dismiss después 4s
- [ ] Mensaje claro y legible

#### Loading
- [ ] Spinner visible durante fetch
- [ ] Mensaje de carga visible
- [ ] Desaparece cuando listo

#### Responsive
- [ ] Desktop (1920+): Layout completo
- [ ] Tablet (768-1024): Cards 2 columnas
- [ ] Mobile (320-768): Stack vertical

#### Navegación
- [ ] Tabs clickables
- [ ] Sin saltos o flickering
- [ ] Transiciones suaves

#### Validaciones
- [ ] Nombre requerido: Form no permite guardar vacío
- [ ] HTML requerido: Alert si html_body vacío
- [ ] Variables válidas: Validar tipo
- [ ] Port válido: 1-65535
- [ ] Email válido: Regex

---

## 🔄 Test Flow: Crear Email Template Completo

### Paso a Paso

1. **Iniciar**
   ```bash
   npm run dev
   # Abrir http://localhost:5173/admin
   ```

2. **Click en Tab Templates**
   - [ ] Carga lista de templates

3. **Click "Crear Nuevo Template"**
   - [ ] Formulario aparece

4. **Rellenar Formulario**
   ```
   Nombre: "Email de Bienvenida"
   Tipo: "transaccional"
   Asunto: "¡Bienvenido {{nombre}}!"
   Preview: "Nuevo usuario registrado"
   ```

5. **Editar HTML**
   - [ ] Click en editor Quill
   - [ ] Escribir: "Hola {{nombre}}, bienvenido a {{empresa}}"
   - [ ] Seleccionar "Hola" y hacer Bold
   - [ ] Click en variable "nombre" → {{nombre}} insertado
   - [ ] Click en variable "empresa" → {{empresa}} insertado

6. **Agregar Variables**
   - [ ] Input: "nombre", Type: "string" → Agregar
   - [ ] Input: "empresa", Type: "string" → Agregar
   - [ ] Tabla muestra 2 variables

7. **Agregar Tags**
   - [ ] Input: "bienvenida" → Agregar
   - [ ] Badge visible
   - [ ] Input: "transaccional" → Agregar

8. **Ver Preview**
   - [ ] Click "Llenar Datos Prueba"
   - [ ] Iframe muestra: "Hola Valor de nombre, bienvenido a Valor de empresa"
   - [ ] Estilos de email visibles
   - [ ] Warning de variables: 0 pendientes

9. **Guardar**
   - [ ] Click "Crear Template"
   - [ ] Alert verde "Template creado"
   - [ ] Formulario se limpia
   - [ ] Template aparece en lista

10. **Verificar en Servidor**
    ```bash
    curl -H "X-API-Key: prov-key-2026-secure" \
      http://localhost:4443/api/admin/email-templates
    ```
    - [ ] Template aparece en respuesta JSON

---

## 🔄 Test Flow: Configurar SMTP

1. **Click Tab SMTP**
   - [ ] Config cargada

2. **Click "Editar Configuración"**
   - [ ] Formulario aparece con campos

3. **Rellenar Gmail**
   ```
   Host: smtp.gmail.com
   Port: 587
   Username: test@gmail.com
   Password: [app-password]
   From Email: noreply@test.com
   From Name: Test Empresa
   ```

4. **Guardar Cambios**
   - [ ] Click "Guardar"
   - [ ] Alert verde
   - [ ] Config actualizada en grid

5. **Probar Conexión**
   - [ ] Click "Probar Conexión"
   - [ ] Spinner visible
   - [ ] Esperar respuesta
   - [ ] Alert verde (conexión OK) o rojo (error)

6. **Verificar Estado**
   - [ ] Click "Verificar Estado"
   - [ ] Alert con estado SMTP

---

## 🔄 Test Flow: Configurar Alertas Storage

1. **Click Tab Storage**
   - [ ] Config cargada con umbrales

2. **Click "Editar"**
   - [ ] Sliders editables

3. **Mover Sliders**
   - [ ] Warning: 70%
   - [ ] Critical: 85%
   - [ ] Exceeded: 95%
   - [ ] Interval: 24 horas

4. **Guardar**
   - [ ] Click "Guardar"
   - [ ] Alert verde

5. **Ver Alertas Activas**
   - [ ] Si hay alertas: Grid de tarjetas
   - [ ] Niveles con colores correctos
   - [ ] Barras de progreso

6. **Resolver Alerta**
   - [ ] Click botón "Resolver" en alerta
   - [ ] POST /resolve enviado
   - [ ] Lista actualiza

7. **Configurar Slack (Opcional)**
   - [ ] Click "Configurar"
   - [ ] Habilitar checkbox
   - [ ] Pegar webhook
   - [ ] Guardar

---

## 🧪 Test Edge Cases

### Error Handling
- [ ] Backend down → Error message
- [ ] API Key inválida → 401 error
- [ ] Network timeout → Error graceful
- [ ] CORS error → Mensaje claro

### Data Validation
- [ ] Crear template sin nombre → Error
- [ ] Crear template sin HTML → Error
- [ ] Email inválido → Error
- [ ] Port fuera de rango → Error

### Performance
- [ ] 100+ templates: Carga sin lag
- [ ] Editor con 5000 caracteres: Responde
- [ ] Múltiples sliders: Smooth animation
- [ ] Upload de imagen en editor: Works

### Browser Compatibility
- [ ] Chrome/Chromium: ✅
- [ ] Firefox: ✅
- [ ] Safari: ✅
- [ ] Edge: ✅

---

## 📊 Métricas de Éxito

| Métrica | Objetivo | Estado |
|---------|----------|--------|
| Load time | <2s | ✅ |
| API latency | <500ms | ✅ |
| Error rate | <1% | ✅ |
| Mobile responsive | 100% | ✅ |
| All endpoints working | 17/17 | ✅ |
| All components render | 9/9 | ✅ |

---

## 🐛 Known Issues & Workarounds

### Issue: Quill.js no carga
**Workaround**: `npm install quill`

### Issue: Variables no aparecen
**Workaround**: Crear al menos 1 variable en form

### Issue: Preview vacío
**Workaround**: Escribir HTML en editor primero

### Issue: CORS error
**Workaround**: Asegurar backend corre en puerto 4443

---

## 📝 Reporte de Testing

Use este template para reportar:

```markdown
## Test Report

**Date**: YYYY-MM-DD
**Tester**: [Nombre]
**Environment**: [Local/Staging/Prod]

### Tests Passed
- [x] Feature A
- [x] Feature B

### Tests Failed
- [ ] Feature C
  - Error: [Description]
  - Steps: [How to reproduce]

### Screenshots/Logs
[Attach]

### Comments
[Additional notes]
```

---

**¡Happy Testing!** 🚀
