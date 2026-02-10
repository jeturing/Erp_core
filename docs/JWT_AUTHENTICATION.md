# JWT Authentication - Admin Dashboard

## Overview
El dashboard administrativo ahora está protegido con autenticación JWT (JSON Web Token). Los administradores deben iniciar sesión con credenciales válidas para acceder al dashboard.

## Architecture

### Flow Diagram
```
┌──────────────────┐
│  /login          │  Usuario accede a página de login
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│  POST /api/admin/login│  Envía username + password
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  JWT Token Created   │  Token guardado en localStorage
└────────┬─────────────┘
         │
         ▼
┌──────────────────┐
│  /admin          │  Redirige al dashboard
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────┐
│  /api/dashboard/metrics     │  Cada request incluye
│  /api/tenants               │  Authorization: Bearer {token}
│  /api/tenants POST          │
└─────────────────────────────┘
```

## Endpoints

### 1. GET `/login` - Login Page
Renderiza la página de login con formulario de credenciales.

**Response**: HTML (admin_login.html)

```bash
curl -X GET http://localhost:4443/login
```

### 2. POST `/api/admin/login` - Authenticate User
Valida credenciales y retorna JWT token.

**Request Body**:
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**Success Response (200)**:
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
}
```

**Error Response (401)**:
```json
{
    "detail": "Credenciales inválidas"
}
```

**Example**:
```bash
curl -X POST http://localhost:4443/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 3. GET `/admin` - Dashboard
Renderiza el dashboard administrativo. Requiere JWT token válido.

**Headers Requeridos**:
- `Authorization: Bearer {token}` (en el header)
- O `auth_token` cookie (como alternativa)

**Response**: HTML (admin_dashboard.html con JavaScript inyectado)

```bash
curl -X GET http://localhost:4443/admin \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. GET `/api/dashboard/metrics` - Metrics (Protected)
Retorna métricas del dashboard. Requiere JWT token.

**Headers Requeridos**:
- `Authorization: Bearer {token}`

**Response**:
```json
{
    "total_revenue": 177,
    "active_tenants": 1,
    "pending_setup": 1,
    "cluster_load": {"cpu": 42, "ram": 64}
}
```

### 5. GET `/api/tenants` - Tenant List (Protected)
Retorna listado de tenants. Requiere JWT token.

**Response**:
```json
{
    "items": [
        {
            "id": 1,
            "company_name": "Test Corp",
            "email": "admin@test.com",
            "subdomain": "test",
            "plan": "enterprise",
            "status": "active",
            "tunnel_active": true,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total": 1
}
```

## Configuration

### Environment Variables
```bash
# .env file

# JWT Secret (cambiar en producción)
JWT_SECRET_KEY=your-secret-key-change-in-production

# JWT Algorithm (HS256 recomendado)
JWT_ALGORITHM=HS256

# Duración del token en horas
JWT_EXPIRATION_HOURS=24

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### Default Credentials (Development)
```
Username: admin
Password: admin123
```

⚠️ **IMPORTANTE**: Cambiar estas credenciales en producción.

## Client-Side JWT Handling

### 1. Token Storage
El token se almacena en `localStorage` bajo la clave `admin_token`:

```javascript
// Guardar token
localStorage.setItem('admin_token', token);

// Obtener token
const token = localStorage.getItem('admin_token');

// Eliminar token (logout)
localStorage.removeItem('admin_token');
```

### 2. Incluir Token en Requests
El dashboard intercepta todos los fetch calls a `/api/*` y automáticamente agrega el header:

```javascript
// Interceptor global
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const [resource, config] = args;
    
    if (typeof resource === 'string' && resource.startsWith('/api/')) {
        const token = getToken();
        if (token) {
            if (!config) args[1] = {};
            if (!args[1].headers) args[1].headers = {};
            args[1].headers['Authorization'] = `Bearer ${token}`;
        }
    }
    
    return originalFetch.apply(this, args);
};
```

### 3. Token Validation
Si el token expira, la API retorna `401 Unauthorized` y el usuario es redirigido a `/login`.

## JWT Token Structure

### Header
```json
{
    "alg": "HS256",
    "typ": "JWT"
}
```

### Payload
```json
{
    "sub": "admin",
    "exp": 1705334400,
    "iat": 1705248000
}
```

### Signature
```
HMACSHA256(
    base64UrlEncode(header) + "." +
    base64UrlEncode(payload),
    secret
)
```

## Testing

### Test Login Flow

**1. Obtener token**:
```bash
RESPONSE=$(curl -s -X POST http://localhost:4443/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo $RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"
```

**2. Acceder al dashboard**:
```bash
curl -X GET http://localhost:4443/admin \
  -H "Authorization: Bearer $TOKEN"
```

**3. Consumir API protegida**:
```bash
curl -X GET http://localhost:4443/api/dashboard/metrics \
  -H "Authorization: Bearer $TOKEN"
```

**4. Probar con token inválido**:
```bash
curl -X GET http://localhost:4443/api/dashboard/metrics \
  -H "Authorization: Bearer invalid_token"
# Respuesta: 401 Unauthorized
```

### Integration Test Script

```bash
#!/bin/bash

BASE_URL="http://localhost:4443"

# Login
echo "🔐 Attempting login..."
RESPONSE=$(curl -s -X POST $BASE_URL/api/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo $RESPONSE | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "❌ Login failed"
    echo $RESPONSE
    exit 1
fi

echo "✅ Login successful"
echo "Token: ${TOKEN:0:20}..."

# Fetch metrics
echo "📊 Fetching metrics..."
curl -s -X GET $BASE_URL/api/dashboard/metrics \
  -H "Authorization: Bearer $TOKEN" | jq .

# Fetch tenants
echo "🏢 Fetching tenants..."
curl -s -X GET $BASE_URL/api/tenants \
  -H "Authorization: Bearer $TOKEN" | jq .

echo "✅ All tests passed!"
```

## Security Considerations

### Production Checklist
- [ ] Cambiar `JWT_SECRET_KEY` a un valor fuerte y aleatorio
- [ ] Cambiar `ADMIN_USERNAME` y `ADMIN_PASSWORD` en `.env`
- [ ] Usar HTTPS (no HTTP) en producción
- [ ] Implementar rate limiting en `/api/admin/login`
- [ ] Implementar 2FA (two-factor authentication)
- [ ] Agregar logging de intentos fallidos de login
- [ ] Considerar usar refresh tokens (expiración corta en access token)
- [ ] Implementar CSRF protection

### Token Security
- Token expira después de 24 horas (configurable)
- Token se valida con HMAC-SHA256
- Token se almacena en localStorage (vulnerable a XSS - considerar usar httpOnly cookies en producción)
- No incluir información sensible en el payload

### Recommendations for Production
1. **Use HTTPS**: Todos los requests deben ser sobre TLS/SSL
2. **HttpOnly Cookies**: Guardar token en `httpOnly` cookie en lugar de localStorage
3. **Refresh Tokens**: Implementar token refresh para reducir ventana de exposición
4. **Rate Limiting**: Limitar intentos de login (ej: 5 intentos/15 minutos)
5. **Logging**: Registrar todos los intentos de login (exitosos y fallidos)
6. **Monitoring**: Alertar sobre múltiples intentos fallidos desde misma IP

## Logout

El usuario puede cerrar sesión haciendo click en el botón logout (icono de exit) en la esquina superior derecha del dashboard.

```javascript
async function logout() {
    if (confirm('¿Estás seguro de que deseas cerrar sesión?')) {
        removeToken();
        window.location.href = '/login';
    }
}
```

## Files Modified

1. **app/main.py**
   - Added JWT imports (`jwt`, `timedelta`, `lru_cache`, `Depends`, `status`, `Cookie`)
   - Added JWT configuration (SECRET_KEY, ALGORITHM, EXPIRATION_HOURS)
   - Added JWT utility functions (`create_access_token`, `verify_token`)
   - Added DTOs (`LoginRequest`, `TokenResponse`, `TokenData`)
   - Added POST `/api/admin/login` endpoint
   - Protected GET `/admin` route with token validation
   - Protected `/api/dashboard/metrics`, `/api/tenants`, POST `/api/tenants` with token validation
   - Added GET `/login` route to serve login page

2. **templates/admin_login.html** (NEW)
   - Login form with username/password
   - Client-side validation
   - Error handling
   - Token storage in localStorage
   - Redirect to `/admin` on success

3. **templates/admin_dashboard.html**
   - Added logout button to header
   - Added JWT token management functions
   - Added fetch interceptor to include Authorization header
   - Added authentication check on page load
   - Redirect to `/login` if token is missing

## Next Steps

### Phase 2 (Planned)
- [ ] Implement 2FA (two-factor authentication)
- [ ] Add refresh token mechanism
- [ ] Add role-based access control (RBAC)
- [ ] Implement admin audit logging
- [ ] Add rate limiting to login endpoint

### Phase 3 (Planned)
- [ ] Integrate Billing template
- [ ] Integrate Reports template
- [ ] Integrate Logs template
- [ ] Add PATCH/DELETE endpoints for tenant management

## Troubleshooting

### "Token inválido" Error
- Asegúrate que el token se incluya correctamente en el header: `Authorization: Bearer {token}`
- Verifica que el token no esté expirado (exp claim en el payload)
- Confirma que `JWT_SECRET_KEY` sea el mismo en cliente y servidor

### "No autorizado" en /admin
- El token no se está guardando en localStorage correctamente
- Abre la consola del navegador (F12) y verifica: `localStorage.getItem('admin_token')`
- Confirma que estés siendo redirigido correctamente a `/login`

### Login fallido
- Verifica credenciales: usuario `admin` / contraseña `admin123`
- Comprueba que el servidor está ejecutándose en puerto 4443
- Revisa los logs del servidor para mensajes de error

