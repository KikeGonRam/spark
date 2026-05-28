# 🚀 GUÍA RÁPIDA DE INICIO - BarberPro Elite Python

**Tiempo estimado: 5-10 minutos**

---

## ⚡ Inicio Rápido (Local)

### Paso 1: Preparar Entorno
```bash
# Navegar al proyecto
cd C:\Users\luis1\Desktop\BarberPro-Python

# Crear virtual environment
python -m venv venv

# Activar
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Paso 2: Instalar Dependencias
```bash
# Backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend
npm install
```

### Paso 3: Configurar Variables
```bash
# Copiar template
cp .env.example .env

# Editar si es necesario (defaults funcionan para desarrollo local)
```

### Paso 4: Iniciar MongoDB (si no está corriendo)
```bash
# En otra terminal
mongod

# O si está instalado como servicio
# Windows: net start MongoDB
# Linux: sudo systemctl start mongod
```

### Paso 5: Ejecutar la App
```bash
# Terminal 1: Backend
uvicorn app.main:app --reload

# Terminal 2 (opcional): Frontend dev
npm run dev

# Terminal 3 (opcional): Tailwind watch
npm run watch:css
```

### Acceder
```
API:           http://localhost:8000
Docs (Swagger):http://localhost:8000/docs
ReDoc:         http://localhost:8000/redoc
```

---

## 🐳 Con Docker (Recomendado para Producción)

### Paso 1: Preparar
```bash
cd C:\Users\luis1\Desktop\BarberPro-Python
cp .env.example .env
```

### Paso 2: Iniciar Servicios
```bash
# Con MongoDB corriendo en PC
docker-compose up -d

# Esperar ~20 segundos para que todo esté listo
```

### Paso 3: Verificar
```bash
# Ver estado
docker-compose ps

# Ver logs
docker-compose logs -f app

# Health check
curl http://localhost:8000/api/health
```

### Acceder
```
API:     http://localhost:8000
Nginx:   http://localhost:80
Mailpit: http://localhost:8001
Docs:    http://localhost:8000/docs
```

### Detener
```bash
docker-compose down
```

---

## 🧪 Ejecutar Tests

```bash
# Todos los tests
pytest

# Específico
pytest tests/unit/test_auth.py -v

# Con coverage
pytest --cov=app --cov-report=html
# Ver: htmlcov/index.html

# Solo tests de integración
pytest tests/integration -v -s
```

---

## 📝 Estructura Rápida

```
app/                    # Backend
├── main.py             # FastAPI app
├── routes/             # Endpoints (87+)
├── services/           # Lógica de negocio
├── models/             # Pydantic models
├── repositories/       # BD access
└── utils/              # Helpers

templates/              # HTML (Jinja2)
├── base.html           # Layout principal
├── pages/login.html    # Login
└── pages/register.html # Registro

resources/              # Frontend assets
├── css/styles.css      # TailwindCSS
├── js/main.js          # Alpine.js
└── img/                # Imágenes

tests/                  # 240+ tests
├── conftest.py         # Fixtures
├── unit/               # Unit tests
└── integration/        # Integration tests
```

---

## 🔑 Variables Importantes en .env

```env
# Para que funcione localmente:

MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=barberpro

# JWT (cambiar en producción)
JWT_SECRET=your-secret-key-change-in-production

# Email (Mailpit en docker)
SMTP_HOST=mailpit
SMTP_PORT=1025

# Gemini API (opcional)
GEMINI_API_KEY=tu-api-key-aqui
```

---

## 🐛 Troubleshooting Rápido

### "Connection refused" MongoDB
```bash
# Solución: Iniciar MongoDB
mongod
```

### "Address already in use" Puerto 8000
```bash
# Cambiar puerto en uvicorn
uvicorn app.main:app --reload --port 9000
```

### Tests fallan
```bash
# Limpiar cache
rm -rf .pytest_cache __pycache__
pytest --cache-clear
```

### Docker no inicia
```bash
# Rebuild
docker-compose build --no-cache

# Limpiar
docker-compose down -v
docker system prune -a
```

---

## 📚 Documentación Completa

- **README.md** - Overview
- **SETUP.md** - Instalación detallada
- **ARQUITECTURA.md** - Diseño
- **API.md** - Endpoints (87+)
- **DEPLOY.md** - Producción
- **FASE_*.md** - Por fase
- **RESUMEN_MIGRACION.md** - Estadísticas

---

## ✅ Checklist Inicio

- [ ] MongoDB corriendo
- [ ] Python 3.11+ instalado
- [ ] venv creado y activado
- [ ] Dependencias instaladas
- [ ] .env configurado
- [ ] App iniciada sin errores
- [ ] API accesible en /docs
- [ ] Tests pasando

---

## 🎯 Próximos Pasos

1. **Explorar API**
   ```bash
   # Abrir http://localhost:8000/docs
   # Probar endpoints
   ```

2. **Entender Estructura**
   - Leer `ARQUITECTURA.md`
   - Explorar `/app` directory

3. **Ejecutar Tests**
   ```bash
   pytest -v
   ```

4. **Hacer Cambios**
   - Edit código
   - Servidor recarga automático
   - Tests verifican cambios

---

## 📞 Ayuda

- Docs: `/docs` o `/redoc`
- Issues: Revisar documentación por fase
- Code: Comentarios explicativos incluidos

---

**¡Listo para empezar!** 🎉

*Última actualización: 17 de Mayo de 2026*
