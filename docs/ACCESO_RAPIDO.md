# 🚀 ACCESO RÁPIDO - BarberPro Python Edition

## 📍 ESTADO ACTUAL

✅ **Servidor FastAPI en inicio...**  
⏳ **Espera 20-30 segundos para que esté completamente listo**

---

## 🌐 ACCESOS INMEDIATOS (Cuando esté listo)

### Interfaz Web
```
Swagger UI:  http://localhost:8000/docs
ReDoc:       http://localhost:8000/redoc
```

### API Health
```
GET http://localhost:8000/api/health
```

---

## 🐛 RESOLVIENDO PROBLEMAS

### Error: "Docker requires elevation"
**Solución:** Este error NO afecta al desarrollo. El servidor FastAPI funciona sin Docker.

Ver: `EMERGENCIA_SIN_DOCKER.md`

### Si el servidor no inicia en 30 segundos
1. Abre una nueva terminal PowerShell
2. Navega a: `C:\Users\luis1\Desktop\BarberPro-Python`
3. Ejecuta:
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Error: "Python no encontrado"
Instala Python desde: https://www.python.org/downloads/

---

## 📚 DOCUMENTACIÓN

| Archivo | Propósito |
|---------|----------|
| `README.md` | Overview del proyecto |
| `QUICK_START.md` | Inicio rápido (5-10 min) |
| `API.md` | Referencia de endpoints |
| `EMERGENCIA_SIN_DOCKER.md` | Soluciones Docker |
| `DOCKER_QUICK_FIX.md` | Fix rápido Docker |

---

## 🧪 PRIMEROS PASOS

### 1. Verifica que está corriendo
```bash
curl http://localhost:8000/api/health
```

### 2. Registra un usuario (en Swagger)
```
POST /api/auth/register
{
  "email": "test@example.com",
  "password": "Test@1234",
  "name": "Test User",
  "role": "client"
}
```

### 3. Login
```
POST /api/auth/login
{
  "email": "test@example.com",
  "password": "Test@1234"
}
```

### 4. Explora otros 85+ endpoints
Ve a http://localhost:8000/docs

---

## ⚡ COMANDOS ÚTILES

### Detener el servidor
```
Ctrl + C (en la ventana del servidor)
```

### Reiniciar dependencias
```powershell
python -m pip install -r requirements.txt
```

### Ejecutar tests
```powershell
python -m pytest tests/ -v
```

### Limpiar caché Python
```powershell
Remove-Item -Recurse -Force .\__pycache__
```

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Espera a que el servidor esté listo
2. ✅ Abre http://localhost:8000/docs
3. ✅ Prueba los endpoints en Swagger
4. ✅ Lee `QUICK_START.md` para más detalles

---

## ✨ IMPORTANTE

- **Docker NO es necesario para desarrollo**
- El servidor funciona perfectamente sin Docker
- Docker solo es para producción/deployment
- Toda la funcionalidad está disponible vía API REST

---

**Última actualización:** 17 de Mayo de 2026

