# Plan de Implementación de Correcciones

## ✅ Lo que ya está HECHO

1. **Backend - secure_auth.py**
   - ✅ Endpoint `/api/auth/login` ahora devuelve token en JSON + Cookie
   - ✅ Endpoint `/api/auth/refresh` ahora devuelve token en JSON + Cookie

2. **Backend - roles.py**
   - ✅ Función `_extract_token()` mejorada para intentar múltiples fuentes

3. **Backend - tenants.py**
   - ✅ 4 endpoints actualizados para usar Cookie(access_token) 
   - ✅ Importa `_require_admin` de roles.py

4. **Frontend - client.ts**
   - ✅ `tryRefresh()` ahora guarda token de respuesta JSON

5. **Frontend - auth.ts**
   - ✅ `login()` ahora guarda token de respuesta JSON

6. **Compilación**
   - ✅ Frontend compilado sin errores
   - ✅ Python sin errores de sintaxis

## 🚀 Qué hacer AHORA (Pasos para Production)

### Paso 1: Restart Backend (INMEDIATO)

```bash
# Si estás usando PM2:
pm2 stop erp_core
pm2 start /opt/Erp_core/app/main.py --name erp_core --interpreter python3

# O si usas supervisor/systemd:
sudo systemctl restart erp_core

# O si estás desarrollando:
# Ctrl+C en la terminal
# Luego: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 2: Deploy Frontend (si cambió el dist/)

```bash
# Copiar el nuevo dist/ a tu servidor
cd /opt/Erp_core/frontend
npm run build  # Ya compilado, pero para confirmar
# Copiar dist/ al servidor web (nginx, S3, etc.)
```

### Paso 3: Test rápido en desarrollo

```bash
# Opción A: Usar el script de test
cd /opt/Erp_core
bash test_tenants_auth.sh

# Opción B: Test manual en browser
# 1. Ir a https://sajet.us
# 2. Iniciar sesión como admin
# 3. Ir a https://sajet.us/#/tenants
# 4. Debería cargar lista de tenants (antes daba 401)
# 5. Intentar crear un nuevo tenant
```

### Paso 4: Verificar logs

```bash
# Si usas PM2:
pm2 logs erp_core | grep -i "tenant\|401\|error"

# Si usas journalctl:
journalctl -u erp_core -n 100 -f

# Ver logs en /opt/Erp_core/logs/:
tail -f /opt/Erp_core/logs/*.log
```

## 📋 Checklist Final

- [ ] Backend reiniciado
- [ ] Frontend nuevamente buildado/deployado
- [ ] Puedo loguearme como admin
- [ ] GET /api/tenants funciona (no da 401)
- [ ] Puedo ver lista de tenants en https://sajet.us/#/tenants
- [ ] Puedo intentar crear un nuevo tenant
- [ ] Partner selector aparece en creación de tenant (si es Partner)
- [ ] No hay errores en console del navegador
- [ ] No hay errores en logs del backend

## 🔍 Troubleshooting

### Si aún da 401:

```bash
# 1. Verificar que el token está en la cookie:
curl -v https://sajet.us/api/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin","password":"tu_password"}' 2>&1 | grep -i "set-cookie"

# Debería ver: set-cookie: access_token=...

# 2. Verificar que _extract_token está siendo usado:
# (Ver /opt/Erp_core/app/routes/roles.py línea 374+)

# 3. Verificar que tenants.py importa _require_admin_base:
grep "_require_admin_base" /opt/Erp_core/app/routes/tenants.py

# Debería ver: _require_admin_base(request, access_token)
```

### Si el token no viene en JSON:

```bash
# Verificar secure_auth.py tiene "access_token" en response:
grep -A5 "Crear respuesta con cookies" /opt/Erp_core/app/routes/secure_auth.py

# Debería ver:
# response = JSONResponse(content={
#     ...
#     "access_token": access_token,
```

### Si Partner selector no aparece:

```bash
# Verificar que el endpoint devuelve partner_id:
curl -s https://sajet.us/api/tenants \
  -b cookies.txt | jq '.[0].partner_id'

# Si es null, el Partner selector no aparecerá (es optional)
```

## 📝 Notas importantes

- **Seguridad:** Las cookies son httpOnly (no se pueden acceder desde JavaScript), pero se envían automáticamente
- **Backward compatibility:** El header Bearer sigue funcionando como fallback
- **localStorage:** Se mantiene sincronizado opcionalmente (no es requerido)
- **Refresh:** Se mantiene funcional tanto con cookies como con localStorage

## 📚 Documentación

Documentos relacionados en `/opt/Erp_core/`:
- `TENANTS_401_FIX_SUMMARY.md` — Explicación técnica completa
- `test_tenants_auth.sh` — Script de testing
- `app/routes/tenants.py` — Endpoints de tenants (líneas 356-572)
- `app/routes/secure_auth.py` — Login y refresh (líneas 91-540)
- `app/routes/roles.py` — _extract_token (líneas 374-394)

---

**Versión:** v1.0
**Fecha:** 2026-02-23
**Status:** ✅ Listo para deploy
