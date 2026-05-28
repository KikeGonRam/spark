# 🔧 GUÍA DE SOLUCIÓN: PROBLEMA CON DOCKER

## 📌 El Problema

Cuando intentas ejecutar `docker ps` o `docker-compose up`, recibes:
```
Error 500: request returned 500 Internal Server Error for API route and version 
http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/v1.54/...
```

**Causa:** Docker Engine está corriendo pero tiene problemas internos con la comunicación.

---

## ✅ SOLUCIONES (En Orden de Prioridad)

### SOLUCIÓN 1: Reiniciar Docker Desktop (RECOMENDADO)

**Paso 1:** Busca el ícono de Docker en la bandeja del sistema (abajo a la derecha)

**Paso 2:** Haz clic derecho y selecciona "Quit Docker Desktop"

**Paso 3:** Espera a que se cierre completamente (hasta 1 minuto)

**Paso 4:** Haz clic en Docker Desktop desde el Menú Inicio para reabrirlo

**Paso 5:** Espera hasta que veas:
```
Docker is running
```

**Paso 6:** Verifica en PowerShell:
```powershell
docker ps
docker-compose --version
```

---

### SOLUCIÓN 2: Reset de Docker Service (Si SOLUCIÓN 1 No Funciona)

**⚠️ Requiere PowerShell como Administrador**

**Paso 1:** Abre PowerShell como Administrador
- Presiona `Win + X`
- Selecciona "Windows PowerShell (Administrador)"

**Paso 2:** Ejecuta estos comandos:

```powershell
# Detener servicio de Docker
net stop com.docker.service

# Esperar 10 segundos
Start-Sleep -Seconds 10

# Iniciar servicio de Docker
net start com.docker.service

# Esperar 30 segundos para que se inicie
Start-Sleep -Seconds 30
```

**Paso 3:** Verifica:
```powershell
docker ps
```

---

### SOLUCIÓN 3: Limpiar y Reiniciar Docker

**Paso 1:** Abre Docker Desktop

**Paso 2:** Ve a **Settings** → **Troubleshoot**

**Paso 3:** Haz clic en **"Reset to factory defaults"**

**Paso 4:** Confirma que deseas resetear

**Paso 5:** Espera a que se reinicie (2-3 minutos)

**Paso 6:** Verifica:
```powershell
docker ps
```

---

### SOLUCIÓN 4: Verificar que Docker Desktop esté habilitado

**En Windows, Docker Desktop se ejecuta en WSL2 (Windows Subsystem for Linux 2)**

**Verifica:**

```powershell
# Comprobar que WSL2 está habilitado
wsl -l -v

# Debería mostrar una distribución con VERSION 2
```

Si ves `VERSION 1`, necesitas actualizar:
```powershell
# Actualizar WSL a versión 2
wsl --set-default-version 2
```

---

## 🧪 Mientras se Resuelve Docker...

### ✅ La Aplicación YA ESTÁ FUNCIONANDO

**SIN necesidad de Docker**, el servidor FastAPI está corriendo en:

```
🔗 http://localhost:8000/docs
```

### Prueba la Aplicación Ahora:

1. **Abre tu navegador**
2. **Ve a:** http://localhost:8000/docs
3. **Verás:** Swagger UI con todos los endpoints

### Probar Endpoints en Swagger:

1. Haz clic en cualquier endpoint (ej: `GET /api/health`)
2. Haz clic en "Try it out"
3. Haz clic en "Execute"
4. Verás la respuesta en JSON

---

## 📊 Comprobaciones de Diagnóstico

### ¿Docker está instalado?
```powershell
docker --version
# Debería mostrar: Docker version 29.4.1, build 055a4782
```

### ¿Docker Compose está instalado?
```powershell
docker-compose --version
# Debería mostrar: Docker Compose version v5.1.3
```

### ¿Docker está corriendo?
```powershell
docker ps
# Si funciona: Debería mostrar tabla de contenedores
# Si falla: Error 500 = necesita reinicio
```

### ¿FastAPI está corriendo?
```powershell
curl http://localhost:8000/api/health

# O en PowerShell:
Invoke-WebRequest -Uri "http://localhost:8000/api/health"
```

---

## 🎯 Una Vez Que Docker Esté Funcionando

### Iniciar los Servicios:

```bash
cd C:\Users\luis1\Desktop\BarberPro-Python
docker-compose up -d
```

### Ver Estado:
```bash
docker-compose ps
```

### Ver Logs:
```bash
docker-compose logs -f app
```

### Detener:
```bash
docker-compose down
```

---

## 📚 Referencia: Qué Hace Docker-Compose

El archivo `docker-compose.yml` levanta estos servicios:

| Servicio | Puerto | Función |
|----------|--------|---------|
| **FastAPI** | 8000 | Servidor principal |
| **Nginx** | 80, 443 | Reverse proxy |
| **Redis** | 6379 | Caché |
| **Mailpit** | 1025, 8025 | Email testing |
| **PostgreSQL** | 5432 | Base de datos (opcional) |

---

## ⚠️ Si Nada de Esto Funciona

### Opción 1: Reinstalar Docker

1. **Desinstala Docker Desktop**
   - Control Panel → Programas → Desinstalar

2. **Elimina archivos residuales**
   - Elimina: `C:\ProgramData\Docker`
   - Elimina: `C:\Users\<tu_usuario>\AppData\Local\Docker`

3. **Reinicia la computadora**

4. **Descarga e instala** de nuevo:
   - https://www.docker.com/products/docker-desktop

### Opción 2: Usar Podman (Alternativa a Docker)

Si Docker sigue dando problemas, puedes usar **Podman**:
```powershell
# Instalar con Chocolatey
choco install podman-desktop

# Funciona similar a Docker
podman ps
podman-compose up
```

---

## ✅ Resumen Rápido

| Paso | Acción |
|------|--------|
| 1 | Cierra Docker Desktop completamente |
| 2 | Espera 1 minuto |
| 3 | Abre Docker Desktop nuevamente |
| 4 | Espera hasta que diga "Docker is running" |
| 5 | Ejecuta `docker ps` en PowerShell |
| 6 | Si funciona, ejecuta `docker-compose up -d` |

---

## 🎉 Una Vez Que Funcione

```bash
# Ver que todo está corriendo
docker-compose ps

# Acceso a la aplicación
# - Swagger: http://localhost/docs
# - Nginx: http://localhost
# - Mailpit: http://localhost:8025
```

---

**Fecha:** 17 de Mayo de 2026  
**Última actualización:** 02:07 AM

