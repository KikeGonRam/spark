# 🔐 FASE 6: AUTENTICACIÓN Y SEGURIDAD

**Estimado:** 2 horas  
**Prioridad:** ALTA  
**Prerequisito:** FASE 5 completada ✅

---

## 📋 TAREAS A REALIZAR

### 1. CREAR MIDDLEWARE DE AUTENTICACIÓN ⭐

**Archivo:** `app/middleware/auth_middleware.py`

**Funcionalidad:**
```python
# Validar JWT en cada request (excepto /health, /docs, /api)
# Extraer user_id del token
# Agregar user context a request state
# Manejo de token expirado
# Logging de autenticación
```

**Endpoints Públicos (Sin autenticación):**
- GET /health
- GET /health/ready
- GET /health/live
- GET /docs
- GET /redoc
- GET /openapi.json
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/refresh

**Endpoints Privados (Requieren JWT):**
- Todos los demás en /api/

---

### 2. CREAR DECORADOR DE PERMISOS 🔒

**Archivo:** `app/utils/permissions.py`

**Decorador para proteger endpoints:**
```python
@require_role("admin")
async def admin_only_endpoint(...):
    ...

@require_permission("appointments.delete")
async def delete_appointment(...):
    ...

@require_roles(["admin", "barber"])
async def barber_operations(...):
    ...
```

**Permisos a definir:**
- appointments.read
- appointments.create
- appointments.update
- appointments.delete
- appointments.confirm
- appointments.complete
- payments.read
- payments.create
- payments.refund
- reports.read
- reports.export
- clients.read
- clients.create
- clients.update
- barbers.read
- barbers.create
- barbers.update
- etc.

---

### 3. IMPLEMENTAR RATE LIMITING 🚫

**Librería:** `slowapi`

**Instalación:**
```bash
pip install slowapi
```

**Endpoints con Rate Limit:**
- POST /api/auth/login (10 por minuto)
- POST /api/auth/register (5 por minuto)
- POST /api/auth/request-password-reset (3 por minuto)
- GET /api/appointments (100 por minuto)
- POST /api/payments (50 por minuto)
- etc.

**Respuesta 429:**
```json
{
  "success": false,
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Ha excedido el límite de intentos. Intente en 60 segundos"
}
```

---

### 4. PASSWORD RESET TOKENS 🔑

**Funcionalidad:**
- Generar token de reset único
- Almacenar con expiración (15 minutos)
- Validar token antes de reset
- Invalidar token después de uso

**Flujo:**
```
1. User: POST /auth/request-password-reset {email}
2. API: Generar token, guardar en DB con TTL
3. API: Enviar email con reset link
4. User: GET /auth/reset-password?token=XXX
5. User: POST /auth/reset-password {token, new_password}
6. API: Validar token, actualizar password, invalidar token
```

---

### 5. EMAIL VERIFICATION 📧

**Funcionalidad:**
- Enviar email de verificación después de register
- Generar token único
- Validar email antes de acciones sensibles
- Re-enviar verification email

**Flujo:**
```
1. User: POST /auth/register
2. API: Guardar user con verified=false
3. API: Enviar email con verification link
4. User: GET /auth/verify-email?token=XXX
5. API: Validar token, actualizar verified=true
```

---

### 6. CORS CONFIGURATION REFINEMENT 🌐

**Archivo:** `app/config.py` (actualizar)

**Orígenes permitidos:**
- Desarrollo: http://localhost:3000, http://localhost:5173
- Producción: https://barberpro.com

**Headers permitidos:**
- Content-Type
- Authorization
- X-Requested-With
- Accept
- Origin

**Métodos permitidos:**
- GET, POST, PUT, PATCH, DELETE, OPTIONS

---

### 7. REQUEST/RESPONSE LOGGING 📝

**Crear:** `app/middleware/logging_middleware.py`

**Información a loguear:**
- Request ID (único)
- Method + Path
- User ID (si autenticado)
- Query parameters
- Response status
- Tiempo de ejecución
- Errores (si es error)

**Ejemplo de log:**
```
[2026-05-13 14:30:45] REQ-abc123 POST /api/appointments 
  User: usr_507f1f77bcf86cd799439011
  Status: 201 (Created)
  Duration: 145ms
```

---

### 8. ACTUALIZAR RUTAS PARA USAR SEGURIDAD 🔐

**Archivos a actualizar:**

1. **app/routes/auth.py**
   - LOGIN: Validar email/password
   - REGISTER: Generar verification token
   - REFRESH: Validar refresh token
   - VERIFY-EMAIL: Usar verification token

2. **app/routes/appointments.py**
   - Todos con @require_authentication
   - DELETE con @require_role("admin")
   - PATCH con validación de owner

3. **app/routes/payments.py**
   - REFUND con @require_permission("payments.refund")
   - Logging de transacciones

4. **app/routes/reports.py**
   - EXPORT con @require_role("admin")
   - Rate limiting aumentado

5. **Otros routes**
   - Agregar decoradores según sea necesario

---

## 🛠️ IMPLEMENTACIÓN RECOMENDADA

### Paso 1: Middleware (30 min)

```bash
1. Crear app/middleware/__init__.py
2. Crear app/middleware/auth_middleware.py
3. Crear app/middleware/logging_middleware.py
4. Registrar en main.py con app.add_middleware()
```

### Paso 2: Utilities (30 min)

```bash
1. Crear app/utils/permissions.py (decoradores)
2. Crear app/utils/security.py (utilidades JWT/password)
3. Crear app/utils/validators.py (validadores)
```

### Paso 3: Rate Limiting (20 min)

```bash
1. Instalar slowapi
2. Configurar en main.py
3. Aplicar a endpoints sensibles
```

### Paso 4: Actualizar Routes (20 min)

```bash
1. Agregar decoradores de autenticación
2. Actualizar lógica de registro/login
3. Implementar reset password
4. Implementar verify email
```

### Paso 5: Documentación (10 min)

```bash
1. Actualizar FASE_6_SECURITY.md
2. Crear guía de autenticación
3. Ejemplos de requests con tokens
```

---

## 🧪 PRUEBAS NECESARIAS

### Test Suite Básica

```python
# tests/test_auth.py
- test_register_success
- test_register_email_exists
- test_login_success
- test_login_invalid_credentials
- test_refresh_token
- test_logout
- test_verify_email
- test_reset_password

# tests/test_permissions.py
- test_admin_only_endpoint
- test_permission_denied
- test_role_based_access

# tests/test_rate_limiting.py
- test_rate_limit_exceeded
- test_rate_limit_reset
```

---

## 📦 DEPENDENCIAS A INSTALAR

```bash
# Rate limiting
pip install slowapi

# JWT (ya debe estar)
pip install PyJWT

# Password hashing (ya debe estar)
pip install bcrypt

# Email (para producción)
pip install aiosmtplib
pip install email-validator

# Token generation
pip install secrets (built-in)
```

---

## 📚 ARCHIVOS A CREAR/MODIFICAR

### Nuevos Archivos
```
✏️ app/middleware/
  ├── __init__.py
  ├── auth_middleware.py
  └── logging_middleware.py

✏️ app/utils/
  ├── __init__.py (actualizar)
  ├── permissions.py (NEW)
  ├── security.py (NEW)
  └── validators.py (NEW)

✏️ app/security/ (alternativa)
  ├── __init__.py
  ├── jwt.py
  ├── passwords.py
  └── permissions.py
```

### Archivos a Modificar
```
✏️ app/main.py (agregar middleware)
✏️ app/config.py (refinar CORS)
✏️ app/routes/auth.py (agregar verificación)
✏️ app/routes/*.py (agregar decoradores)
✏️ app/dependencies.py (mejorar validación)
```

---

## ✅ CHECKLIST PRE-FASE 6

Antes de comenzar, verificar:

- [ ] FASE 5 100% completada
- [ ] app/routes/ tiene 8 módulos
- [ ] app/services/ tiene 8 servicios
- [ ] app/exceptions.py existe
- [ ] app/dependencies.py existe
- [ ] app/main.py integra todos los routers
- [ ] requirements.txt tiene todas las dependencias
- [ ] main.py puede correr sin errores

---

## 🚀 SIGUIENTE FASE

Después de FASE 6:
- [ ] Todas las rutas protegidas
- [ ] Rate limiting activo
- [ ] Logging completo
- [ ] Password reset funcional
- [ ] Email verification funcional
- [ ] Permisos implementados

---

## 📞 NOTAS IMPORTANTES

### Tokens JWT
- Experación: 1 hora
- Refresh token: 7 días
- Secret key en .env
- Algoritmo: HS256

### Passwords
- Mínimo 8 caracteres
- Debe contener: mayúscula, minúscula, número, especial
- Guardados con bcrypt (rounds: 12)

### Rate Limiting
- Login: 10/minuto
- Register: 5/minuto
- Password reset: 3/minuto
- API general: 100/minuto

### Emails
- Usar template system (Jinja2)
- Guardar templates en app/templates/
- Usar aiosmtplib para async

---

## 🎯 RESUMEN

FASE 6 preparará la aplicación para ser deployment-ready:
- ✅ Seguridad robusta
- ✅ Protección contra abuse
- ✅ Logging completo
- ✅ Manejo de credenciales
- ✅ Recovery flows

Después: FASE 7 (Frontend)

---

*Próxima fase: Autenticación y Seguridad*  
*Estimado: 2 horas*  
*Complejidad: Media*
