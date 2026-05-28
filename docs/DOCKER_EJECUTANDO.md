# 🐳 BARBERPRO EJECUTÁNDOSE EN DOCKER

**Estado:** ✅ **COMPLETAMENTE OPERATIVO**  
**Fecha:** 17 de Mayo de 2026  
**Plataforma:** Windows WSL + Docker Compose

---

## 🎉 ¡ÉXITO!

BarberPro ahora está ejecutándose **100% en Docker** con todos los servicios saludables y funcionales.

---

## 📊 SERVICIOS EN LÍNEA

```
✅ barberpro-app      - FastAPI Application (HEALTHY)
✅ barberpro-web      - Nginx Reverse Proxy (UP)
✅ barberpro-redis    - Redis Cache (HEALTHY)
✅ barberpro-mongodb  - MongoDB Database (HEALTHY)
✅ barberpro-mailpit  - Email Testing (HEALTHY)
```

---

## 🌐 ACCESO INMEDIATO

### API REST
```
🔗 Swagger UI:  http://localhost:8000/docs
📚 ReDoc:       http://localhost:8000/redoc
❤️  Health:     http://localhost:8000/health
```

### Otras Herramientas
```
🌍 Nginx Web:   http://localhost
📧 Mailpit:     http://localhost:8025
```

---

## 🔧 CAMBIOS REALIZADOS PARA DOCKER

### 1. Error Inicial: Puerto 1025 Ocupado
**Problema:**
```
Error response from daemon: 
Bind for 0.0.0.0:1025 failed: port is already allocated
```

**Solución:**
- Cambié el puerto SMTP de Mailpit de `1025` → `1125`
- Actualicé `docker-compose.yml`

### 2. Error de Recursión en Pydantic
**Problema:**
```
RecursionError: maximum recursion depth exceeded
```

**Causa:**
- Pydantic v2 tiene problemas de representación con algunos modelos
- BaseDocument usaba sintaxis de Pydantic v1

**Solución:**
- Actualicé `app/models/base.py` a sintaxis Pydantic v2
- Cambié `class Config` → `model_config = ConfigDict(...)`
- Cambié `super().dict()` → `super().model_dump()`
- Simplifiqué modelo `SpecialHours` en `schedule.py`

---

## 📝 ARCHIVOS MODIFICADOS

### docker-compose.yml
```yaml
# Cambio en el puerto de Mailpit
mailpit:
  ports:
    - "8025:8025"    # Web UI
    - "1125:1025"    # SMTP (changed from 1025 to avoid conflicts)
```

### app/models/base.py
```python
# Actualizado a Pydantic v2 syntax
class BaseDocument(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={...}
    )
```

### Dockerfile
```dockerfile
# Simplificado: removido entrypoint.sh para evitar problemas de formato
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## ⚙️ COMANDOS DOCKER ÚTILES

### Ver Estado
```bash
docker-compose ps
docker ps
```

### Ver Logs
```bash
# Todos los servicios
docker-compose logs

# Solo la aplicación
docker-compose logs -f app

# Con límite de líneas
docker-compose logs --tail=50 app
```

### Controlar Servicios
```bash
# Detener todo
docker-compose down

# Detener con volúmenes
docker-compose down -v

# Reiniciar un servicio
docker-compose restart app

# Reconstruir y levantar
docker-compose up -d --build

# Levantar sin reconstruir
docker-compose up -d
```

### Debugging
```bash
# Acceder a bash del contenedor
docker exec -it barberpro-app bash

# Ver variables de entorno
docker exec barberpro-app env

# Ejecutar comando en contenedor
docker exec barberpro-app python -m pytest
```

---

## 🔗 ARQUITECTURA DOCKER

```
┌─────────────────────────────────────────┐
│        Windows WSL2 / Linux             │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │    Docker Engine                 │   │
│  │                                  │   │
│  │  ┌──────────────────────────┐   │   │
│  │  │ barberpro-app (FastAPI)  │   │   │
│  │  │ Port 8000                │   │   │
│  │  └──────────────────────────┘   │   │
│  │            ↓                     │   │
│  │  ┌──────────────────────────┐   │   │
│  │  │ barberpro-web (Nginx)    │   │   │
│  │  │ Port 80                  │   │   │
│  │  └──────────────────────────┘   │   │
│  │                                  │   │
│  │  ┌──────────────────────────┐   │   │
│  │  │ barberpro-redis          │   │   │
│  │  │ Port 6379 (interno)      │   │   │
│  │  └──────────────────────────┘   │   │
│  │                                  │   │
│  │  ┌──────────────────────────┐   │   │
│  │  │ barberpro-mongodb        │   │   │
│  │  │ Port 27017 (interno)     │   │   │
│  │  └──────────────────────────┘   │   │
│  │                                  │   │
│  │  ┌──────────────────────────┐   │   │
│  │  │ barberpro-mailpit        │   │   │
│  │  │ SMTP 1125 / Web 8025     │   │   │
│  │  └──────────────────────────┘   │   │
│  │                                  │   │
│  └──────────────────────────────────┘   │
│                                         │
│  Nginx Network: barberpro-python_internal
└─────────────────────────────────────────┘
         ↓↓↓
┌─────────────────────────────────────────┐
│      Host (Windows)                     │
│                                         │
│  http://localhost:8000    → FastAPI    │
│  http://localhost:80      → Nginx      │
│  http://localhost:8025    → Mailpit    │
│                                         │
└─────────────────────────────────────────┘
```

---

## 📊 PUERTOS

| Servicio | Contenedor | Host | Propósito |
|----------|-----------|------|-----------|
| FastAPI | 8000 | 8000 | API REST |
| Nginx | 80 | 80 | Web Server |
| Nginx | 443 | 443 | HTTPS (opcional) |
| MongoDB | 27017 | - | Base de datos (interno) |
| Redis | 6379 | - | Cache (interno) |
| Mailpit SMTP | 1025 | 1125 | Email SMTP |
| Mailpit Web | 8025 | 8025 | Email UI |

---

## 🧪 PROBAR DESPUÉS DE INICIAR DOCKER

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 2. Ver Documentación API
Abre en tu navegador:
```
http://localhost:8000/docs
```

### 3. Registrar Usuario
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

### 4. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test@1234"
  }'
```

---

## 🐛 TROUBLESHOOTING

### El contenedor app no inicia
```bash
# Ver los logs
docker-compose logs app

# Verificar si hay errores de Pydantic
docker logs barberpro-app | grep -i error
```

### Puerto ya en uso
```bash
# Si el puerto 8000 está en uso (FastAPI)
# Cambiar en docker-compose.yml:
ports:
  - "8001:8000"  # Puerto local → Puerto interno

# Si el puerto 80 está en uso (Nginx)
ports:
  - "8080:80"    # Puerto local → Puerto interno
```

### MongoDB no conecta
```bash
# Verificar que MongoDB esté corriendo
docker-compose ps mongodb

# Ver logs de MongoDB
docker-compose logs mongodb

# Forzar recreación
docker-compose down -v
docker-compose up -d
```

### Limpiar completamente
```bash
# Detener y remover todo
docker-compose down -v --remove-orphans

# Eliminar imagen
docker rmi barberpro-python-app

# Levantar nuevamente
docker-compose up -d --build
```

---

## 📚 VARIABLES DE ENTORNO

Las variables están en `.env`:

```env
APP_ENV=development
MONGO_HOST=mongodb://mongodb:27017
MONGO_DATABASE=barberpro
REDIS_URL=redis://redis:6379/0
JWT_SECRET=your_secret_key
```

**Nota:** En Docker, `MONGO_HOST` apunta a `mongodb` (nombre del servicio), no a `localhost`.

---

## 🎯 PRÓXIMOS PASOS

1. **Verifica que todo funciona:**
   ```bash
   docker-compose ps
   ```

2. **Abre la API en tu navegador:**
   ```
   http://localhost:8000/docs
   ```

3. **Prueba un endpoint:**
   - Haz clic en "Try it out"
   - Prueba `/api/health`

4. **Crea un usuario y haz login**

5. **Continúa desarrollando**

---

## 📚 DOCUMENTACIÓN RELACIONADA

- **QUICK_START.md** - Inicio rápido
- **README.md** - Overview del proyecto
- **PRUEBAS_RAPIDAS.md** - Cómo probar endpoints
- **ARQUITECTURA.md** - Decisiones técnicas

---

## ✨ ESTADO FINAL

```
✅ Docker: OPERATIVO
✅ Todos los servicios: HEALTHY
✅ API: ACCESIBLE en http://localhost:8000
✅ Base de datos: CONECTADA
✅ Cache: FUNCIONAL
✅ Email testing: DISPONIBLE
```

**¡BarberPro está 100% operativo en Docker!**

---

**Último actualizado:** 17 de Mayo de 2026

