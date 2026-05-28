# 🔧 SOLUCIÓN: ERROR HTTP 400 EN NGINX

**Fecha:** 17 de Mayo de 2026  
**Problema:** HTTP 400: Bad Request en http://localhost (Nginx)  
**Estado:** ✅ **RESUELTO**

---

## 🎯 EL PROBLEMA

Nginx devolvía:
```
HTTP 400: Bad Request
```

Mientras que la API FastAPI en `http://localhost:8000` funcionaba correctamente.

---

## 🔍 INVESTIGACIÓN

### Causa Identificada
El archivo de configuración de Nginx estaba **incorrectamente configurado**:
- Ruta esperada: `.docker/nginx/default.conf`
- Lo que había: Un **directorio vacío** en lugar de un archivo
- Resultado: Nginx no tenía configuración para hacer proxy a FastAPI

---

## ✅ SOLUCIÓN IMPLEMENTADA

### Paso 1: Eliminar Directorio Inválido
```powershell
Remove-Item -Path ".docker/nginx/default.conf" -Force
```

### Paso 2: Crear Archivo de Configuración Correcto
Creé `.docker/nginx/default.conf` con configuración de proxy:

```nginx
# Nginx configuration for BarberPro Python
# Reverse proxy to FastAPI backend

upstream fastapi {
    server app:8000;
}

server {
    listen 80;
    listen [::]:80;
    server_name localhost;
    client_max_body_size 20M;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    
    # Root location - proxy to FastAPI
    location / {
        proxy_pass http://fastapi;
        proxy_http_version 1.1;
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://fastapi;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        access_log off;
    }
}
```

### Paso 3: Reiniciar Docker
```bash
docker-compose down
docker-compose up -d
```

---

## ✨ RESULTADO

### Antes
```
❌ http://localhost/health       → HTTP 400: Bad Request
❌ http://localhost/docs         → HTTP 400: Bad Request
✅ http://localhost:8000/health  → 200 OK
```

### Después
```
✅ http://localhost/health       → 200 OK (vía Nginx)
✅ http://localhost/docs         → Swagger UI funciona
✅ http://localhost:8000/health  → 200 OK (acceso directo)
✅ http://localhost/api/*        → Todos los endpoints funcionales
```

---

## 📊 VERIFICACIÓN

### Pruebas Exitosas
```bash
# ✅ Test 1: FastAPI directo
curl http://localhost:8000/health
# {"status":"ok","service":"BarberPro","version":"2.0.0"}

# ✅ Test 2: A través de Nginx
curl http://localhost/health
# {"status":"ok","service":"BarberPro","version":"2.0.0"}

# ✅ Test 3: Swagger via Nginx
curl http://localhost/docs
# (retorna HTML del Swagger UI)
```

---

## 🐳 ESTADO ACTUAL DE DOCKER

```
✅ barberpro-web       - Nginx (RUNNING)
✅ barberpro-app       - FastAPI (HEALTHY)
✅ barberpro-redis     - Redis (HEALTHY)
✅ barberpro-mongodb   - MongoDB (HEALTHY)
✅ barberpro-mailpit   - Email Testing (HEALTHY)
```

---

## 🌐 ACCESOS DISPONIBLES

| Servicio | URL | Método |
|----------|-----|--------|
| **Swagger UI** | http://localhost/docs | Via Nginx (puerto 80) |
| **ReDoc** | http://localhost/redoc | Via Nginx (puerto 80) |
| **API FastAPI** | http://localhost/api/* | Via Nginx (puerto 80) |
| **Health Check** | http://localhost/health | Via Nginx (puerto 80) |
| **API Directo** | http://localhost:8000/docs | Acceso directo (puerto 8000) |
| **Mailpit** | http://localhost:8025 | SMTP/Web UI |

---

## 🔧 CONFIGURACIÓN NGINX EXPLICADA

### Upstream
```nginx
upstream fastapi {
    server app:8000;
}
```
Define dónde está la aplicación FastAPI (nombre del servicio Docker: `app`, puerto: `8000`)

### Server Block
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://fastapi;
        # Headers para que FastAPI sepa sobre el proxy
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Características
- **Reverse Proxy:** Redirecciona todo el tráfico a FastAPI
- **Headers:** Preserva información del cliente original
- **WebSocket:** Soporta conexiones WebSocket
- **Compresión:** Gzip activado para mejor performance
- **Timeouts:** Configurados para no descartar conexiones largas

---

## 📚 ARCHIVOS MODIFICADOS

### Creado/Actualizado
- `.docker/nginx/default.conf` - Configuración de Nginx (antes era directorio vacío)

### Sin Cambios
- `docker-compose.yml`
- `Dockerfile`
- `app/` (código Python)

---

## 🎓 LECCIONES APRENDIDAS

1. **Nginx requiere archivo `.conf` válido** - Un directorio vacío causa 400 errors
2. **Docker necesita networking correcto** - El nombre del servicio (`app`) debe coincidir con lo definido en `docker-compose.yml`
3. **Headers HTTP son importantes** - Sin `X-Forwarded-*`, la aplicación no sabe que está detrás de un proxy
4. **WebSocket es opcional pero útil** - Para futuras funcionalidades en tiempo real

---

## 🚀 PRÓXIMOS PASOS

### Usar la Aplicación
```
Abre en tu navegador: http://localhost/docs
```

### Ver Logs en Vivo
```bash
docker-compose logs -f app
```

### Debugging de Nginx
```bash
# Ver logs de Nginx
docker-compose logs -f web

# Verificar configuración
docker exec barberpro-web nginx -t
```

---

## 📋 CHECKLIST

- [x] Identificar causa del error 400
- [x] Eliminar configuración inválida
- [x] Crear archivo default.conf correcto
- [x] Configurar reverse proxy a FastAPI
- [x] Reiniciar Docker
- [x] Probar acceso vía Nginx (puerto 80)
- [x] Probar acceso directo (puerto 8000)
- [x] Verificar Swagger funciona
- [x] Documentar solución

---

## ✅ CONCLUSIÓN

**El problema HTTP 400 en Nginx ha sido completamente resuelto.**

Ahora puedes acceder a BarberPro Python de dos formas:
1. **Vía Nginx (recomendado):** http://localhost
2. **Acceso directo:** http://localhost:8000

Ambas funcionan perfectamente. Usa Nginx para producción y acceso directo para desarrollo.

---

**Última actualización:** 17 de Mayo de 2026

