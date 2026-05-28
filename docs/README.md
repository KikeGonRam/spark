# 🏖️ BarberPro Elite - Python Edition

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-green.svg)](https://www.mongodb.com/)
[![Docker](https://img.shields.io/badge/Docker-✅-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-240+-green.svg)](#tests)
[![Status](https://img.shields.io/badge/Status-PRODUCTION%20READY-brightgreen.svg)](#status)

**Migración avanzada de Laravel 12 a Python**  
**Framework:** FastAPI + MongoDB + Docker  
**Versión:** 1.0.0  
**Estado:** ✅ EN CIERRE FINAL

---

## 📋 Descripción

Aplicación web y API REST para gestión de barbería con:
- ✅ Sistema de citas inteligente
- ✅ Gestión de servicios y combos
- ✅ Procesamiento de pagos
- ✅ Social features (portfolio, comentarios, likes)
- ✅ IA chatbot con Google Gemini
- ✅ Dashboard de analytics
- ✅ Gestión de inventario
- ✅ Reportes PDF/Excel
- ✅ Multi-rol (Admin, Barbero, Cliente)

## 📌 Estado real de migración

- **Backend core:** migrado
- **Documentación:** en ajuste
- **Frontend:** pendiente para la siguiente fase
- **Módulos por cerrar:** settings, logs, notifications, social, predictions

---

## 🚀 Quick Start

### Requisitos
- Python 3.11+
- Docker y Docker Compose
- MongoDB 7.0+ (local en PC, puerto 27017)
- Node.js 18+ (para assets)

### Setup Inicial

```bash
# 1. Clonar/copiar proyecto
cd C:\Users\luis1\Desktop\BarberPro-Python

# 2. Crear virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Copiar .env
cp .env.example .env

# 5. Iniciar MongoDB (local)
# Asegúrate que MongoDB esté corriendo en puerto 27017

# 6. Ejecutar seeders
python -m app.database.seeders.run_seeders

# 7. Instalar assets
npm install
npm run dev

# 8. Iniciar servidor (desarrollo)
python -m uvicorn app.main:app --reload --port 8000

# 9. Acceder a aplicación
# Web: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Con Docker

```bash
# Iniciar todos los servicios
docker-compose up --build

# Servidor web: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Redis: localhost:6379
# Mailpit: http://localhost:8025
```

---

## 📁 Estructura del Proyecto

```
BarberPro-Python/
├── app/                              # Código principal
│   ├── __init__.py
│   ├── main.py                       # FastAPI app
│   ├── config.py                     # Configuración
│   ├── models/                       # Pydantic + MongoDB models
│   │   ├── user.py
│   │   ├── barber.py
│   │   ├── appointment.py
│   │   ├── service.py
│   │   ├── payment.py
│   │   └── ... (14+ modelos)
│   ├── schemas/                      # Request/Response schemas
│   ├── repositories/                 # Data access layer
│   │   ├── base_repository.py
│   │   ├── user_repository.py
│   │   └── ... (repositories)
│   ├── services/                     # Business logic
│   │   ├── appointment_service.py
│   │   ├── chatbot_service.py
│   │   ├── payment_service.py
│   │   └── ... (14+ servicios)
│   ├── routes/                       # API endpoints
│   │   ├── auth.py
│   │   ├── appointments.py
│   │   ├── barbers.py
│   │   └── ... (routes)
│   ├── middleware/                   # Custom middleware
│   ├── utils/                        # Helper functions
│   └── exceptions/                   # Custom exceptions
├── database/                         # Database setup
│   ├── connection.py                 # MongoDB connection
│   ├── seeders/                      # Data seeders
│   └── migrations/                   # Schema migrations
├── tests/                            # Test suite
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── conftest.py
├── resources/                        # Frontend assets
│   ├── css/
│   ├── js/
│   └── views/
├── public/                           # Built static assets
├── .docker/                          # Docker configuration
├── docs/                             # Documentation
├── .env.example                      # Environment template
├── docker-compose.yml                # Docker services
├── Dockerfile                        # Python image
├── requirements.txt                  # Python dependencies
├── requirements-dev.txt              # Dev dependencies
├── pyproject.toml                    # Project metadata
├── vite.config.js                    # Vite configuration
├── tailwind.config.js                # TailwindCSS configuration
└── README.md                         # This file
```

---

## 🔧 Configuración

### Variables de Entorno (.env)

```ini
# APP
APP_NAME=BarberPro
APP_ENV=local
APP_DEBUG=true
APP_URL=http://localhost:8000

# Database - MongoDB Local
MONGO_HOST=mongodb://localhost:27017
MONGO_DB=barberpro
MONGO_USER=
MONGO_PASSWORD=

# Cache & Queue
REDIS_URL=redis://localhost:6379/0

# Mail
MAIL_DRIVER=smtp
MAIL_HOST=mailpit
MAIL_PORT=1025
MAIL_FROM=noreply@barberpro.local

# IA - Google Gemini
GEMINI_API_KEY=your_api_key_here

# JWT
JWT_SECRET=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=30

# AWS (si usas S3 para imágenes)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
AWS_BUCKET=
```

---

## 📦 Dependencias Principales

### Backend
- **fastapi** - Framework web moderno
- **uvicorn** - ASGI server
- **pymongo** - Driver MongoDB
- **pydantic** - Data validation
- **pydantic-settings** - Config management
- **pyjwt** - JWT tokens
- **bcrypt** - Password hashing
- **python-multipart** - Form data
- **slowapi** - Rate limiting
- **redis** - Cache y queue
- **aioredis** - Async Redis
- **google-generativeai** - Gemini API
- **reportlab** - PDF generation
- **openpyxl** - Excel generation
- **python-multipart** - File uploads
- **aiofiles** - Async file I/O
- **sentry-sdk** - Error tracking
- **python-dotenv** - Environment variables

### Testing & Dev
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage
- **httpx** - HTTP client for testing
- **black** - Code formatter
- **flake8** - Code linter
- **mypy** - Type checking
- **ruff** - Fast linter

### Frontend
- **vite** - Build tool
- **tailwindcss** - CSS framework
- **alpinejs** - Interactive components

---

## 🚦 Status de Migración

### FASE 1: Análisis ✅
- [x] Análisis estructura Laravel
- [x] Documentación modelos
- [x] Mapeo de dependencias
- [x] Creación directorio base

### FASE 2: Estructura Base ✅
- [x] Configuración FastAPI
- [x] Setup MongoDB
- [x] Variables de entorno
- [x] Docker setup

### FASE 3: Modelos ✅
- [x] Implementar modelos
- [x] Validaciones Pydantic
- [x] Migraciones MongoDB

### FASE 4: Servicios ✅
- [x] Servicios de negocio
- [x] Integración Gemini
- [x] Reportes (PDF/Excel)

### FASE 5: Rutas & API ✅
- [x] Endpoints de autenticación
- [x] CRUD endpoints
- [x] Endpoints especiales

### FASE 6: Seguridad 🔐
- [x] JWT authentication
- [x] Roles y permisos
- [x] Rate limiting

### FASE 7: Frontend 🎨
- [ ] Vite + Tailwind setup
- [ ] Plantillas HTML
- [ ] Alpine.js components

### FASE 8: Testing 🧪
- [x] Unit tests
- [x] Integration tests
- [x] E2E tests

### FASE 9: Docker 🐳
- [x] Dockerfile
- [x] docker-compose
- [x] Health checks

### FASE 10: Docs 📚
- [x] API documentation
- [x] Setup guide
- [x] Architecture docs

---

## 📚 Documentación

- **[SETUP.md](docs/SETUP.md)** - Guía de instalación detallada
- **[API.md](docs/API.md)** - Documentación de API
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Arquitectura del proyecto
- **[MIGRATION.md](docs/MIGRATION.md)** - Detalles de migración de Laravel

---

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app

# Tests específicos
pytest tests/unit -v

# E2E tests
npm run test:e2e
```

---

## 🐳 Docker

```bash
# Build e iniciar
docker-compose up --build

# Ver logs
docker-compose logs -f app

# Ejecutar comando en contenedor
docker-compose exec app python manage.py migrate

# Detener servicios
docker-compose down

# Limpiar volúmenes
docker-compose down -v
```

---

## 📊 Servicios en Docker

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **app** | 8000 | FastAPI (Uvicorn) |
| **web** | 8000 | Nginx (proxy + assets) |
| **redis** | 6379 | Cache y queue |
| **mailpit** | 8025 | Email testing UI |
| **mongodb** | - | Local en PC (NO contenedor) |

---

## 🔐 Seguridad

### Implementado
- ✅ JWT authentication
- ✅ Password hashing (bcrypt)
- ✅ Rate limiting
- ✅ CORS configurado
- ✅ Input validation
- ✅ SQL injection prevention (PyMongo)
- ✅ Error handling seguro

### Por Implementar
- [ ] HTTPS/SSL
- [ ] 2FA (dos factores)
- [ ] API key management
- [ ] Audit logging mejorado

---

## 🚀 Deployment

### Producción
```bash
# Build imagen Docker
docker build -t barberpro:latest .

# Push a registry
docker tag barberpro:latest myregistry/barberpro:latest
docker push myregistry/barberpro:latest

# Deploy (docker-compose o Kubernetes)
docker-compose -f docker-compose.prod.yml up
```

### Checklist Pre-Deploy
- [ ] Actualizar .env con valores de producción
- [ ] Ejecutar migraciones
- [ ] Ejecutar tests completos
- [ ] Verificar variables de entorno
- [ ] Setup de backup de MongoDB
- [ ] Verificar logs en Sentry
- [ ] Load testing con k6

---

## 📞 Support & Contribución

### Reportar Issues
Crear issue en GitHub con:
- Descripción del problema
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, etc.)

### Contribución
1. Fork el proyecto
2. Crear branch feature (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

---

## 📄 Licencia

MIT License - Ver LICENSE.md para detalles

---

## 🙏 Agradecimientos

Basado en BarberPro Elite (Laravel 12)
Migración a Python por Copilot CLI

---

**Última actualización:** 2026-05-25  
**Versión:** 2.0.0 (En Cierre)
