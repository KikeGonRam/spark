# 🧪 PRUEBAS RÁPIDAS - BARBERPRO API

**Servidor:** http://localhost:8000  
**Documentación interactiva:** http://localhost:8000/docs

---

## ✅ OPCIÓN 1: USAR SWAGGER UI (MÁS FÁCIL)

### Pasos:
1. Abre tu navegador
2. Ve a: **http://localhost:8000/docs**
3. ¡Prueba los endpoints directamente!

**Ventajas:**
- ✅ Interfaz gráfica
- ✅ Documentación integrada
- ✅ Prueba con un clic
- ✅ Ve respuestas formateadas

---

## ✅ OPCIÓN 2: USAR CURL (Línea de comandos)

### Verificar que el servidor está corriendo
```bash
curl http://localhost:8000/api/health
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Registrar un nuevo usuario
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@1234",
    "name": "Test User",
    "role": "client"
  }'
```

**Respuesta esperada:**
```json
{
  "id": "usuario_id",
  "email": "test@example.com",
  "name": "Test User",
  "role": "client",
  "created_at": "2026-05-17T02:30:00Z"
}
```

### Login (obtener token)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@1234"
  }'
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Usar el token en siguientes peticiones
```bash
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer tu_token_aqui"
```

---

## 🎨 OPCIÓN 3: USAR POSTMAN/INSOMNIA

### Importar desde Swagger
1. Abre Postman o Insomnia
2. Selecciona "Import from URL"
3. URL: `http://localhost:8000/openapi.json`
4. ¡Todos los endpoints se importan automáticamente!

---

## 📋 ENDPOINTS PRINCIPALES

### Autenticación
```
POST   /api/auth/register          - Registrar usuario
POST   /api/auth/login              - Login
POST   /api/auth/logout             - Logout
POST   /api/auth/refresh            - Refrescar token
```

### Usuarios
```
GET    /api/users/me                - Tu perfil
PUT    /api/users/me                - Actualizar perfil
GET    /api/users                   - Listar usuarios (admin)
GET    /api/users/{id}              - Ver usuario
```

### Citas
```
GET    /api/appointments            - Mis citas
POST   /api/appointments            - Crear cita
GET    /api/appointments/{id}       - Ver cita
PUT    /api/appointments/{id}       - Actualizar cita
DELETE /api/appointments/{id}       - Cancelar cita
```

### Barberos
```
GET    /api/barbers                 - Listar barberos
GET    /api/barbers/{id}            - Ver barbero
POST   /api/barbers                 - Crear barbero (admin)
```

### Servicios
```
GET    /api/services                - Listar servicios
GET    /api/services/{id}           - Ver servicio
```

### Dashboard
```
GET    /api/dashboard/stats         - Estadísticas
GET    /api/dashboard/appointments  - Citas próximas
GET    /api/dashboard/revenue       - Ingresos
```

### Reportes
```
GET    /api/reports/appointments    - Reporte citas
GET    /api/reports/revenue         - Reporte ingresos
GET    /api/reports/export          - Exportar PDF
```

---

## 🔑 OBTENER UN TOKEN DE PRUEBA

### Método 1: Desde Swagger UI
1. Abre http://localhost:8000/docs
2. Expande "POST /api/auth/login"
3. Haz clic en "Try it out"
4. Usa credenciales:
   - Email: `test@example.com`
   - Password: `Test@1234`
5. Copia el `access_token`

### Método 2: Con Curl
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@1234"
  }' | jq '.access_token'
```

---

## 🧪 CASO DE USO COMPLETO

### 1. Registrar usuario
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@example.com",
    "password": "Juan@2024",
    "name": "Juan García",
    "role": "client"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "juan@example.com",
    "password": "Juan@2024"
  }' > token.json

export TOKEN=$(cat token.json | jq -r '.access_token')
```

### 3. Obtener perfil
```bash
curl -X GET http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Ver citas
```bash
curl -X GET http://localhost:8000/api/appointments \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Crear cita
```bash
curl -X POST http://localhost:8000/api/appointments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "barber_id": "id_del_barbero",
    "service_id": "id_del_servicio",
    "appointment_date": "2026-05-20T14:00:00"
  }'
```

---

## 📊 VERIFICAR BASE DE DATOS

### Conectar a MongoDB
```bash
mongosh mongodb://localhost:27017/barberpro
```

### Comandos útiles
```javascript
// Ver colecciones
show collections

// Contar usuarios
db.users.countDocuments()

// Listar usuarios
db.users.find().pretty()

// Ver citas
db.appointments.find().pretty()
```

---

## 🔍 SOLUCIONAR PROBLEMAS

### Error: "Connection refused"
```
El servidor no está corriendo
Solución: Inicia el servidor (ver ACCESO_RAPIDO.md)
```

### Error: "401 Unauthorized"
```
El token expiró o es inválido
Solución: Obtén un nuevo token con login
```

### Error: "403 Forbidden"
```
No tienes permisos para esa acción
Solución: Verifica tu rol (admin, barbero, cliente)
```

### Error: "404 Not Found"
```
El recurso no existe
Solución: Verifica el ID en la base de datos
```

---

## 📚 MÁS INFORMACIÓN

- **Documentación completa:** http://localhost:8000/docs
- **ReDoc (alternativa):** http://localhost:8000/redoc
- **OpenAPI schema:** http://localhost:8000/openapi.json

---

## ✨ ¡DISFRUTA PROBANDO!

Usa cualquiera de los métodos arriba para explorar la API. ¡Tienes 87+ endpoints disponibles!

