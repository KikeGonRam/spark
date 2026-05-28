# 📖 DOCUMENTACIÓN DE MIGRACIÓN: Laravel → Python

**Fecha de Inicio:** 2026-05-16  
**Estado:** Migración avanzada, en cierre funcional  
**Próxima Fase:** Cierre de módulos faltantes y documentación final

---

## 📋 Índice

1. [Resumen de Migración](#resumen)
2. [Mapeo de Componentes](#mapeo)
3. [Cambios Principales](#cambios)
4. [Equivalencias de Código](#equivalencias)
5. [Estructura de Proyecto](#estructura)
6. [Stack Técnico](#stack)
7. [Plan de Implementación](#plan)
8. [Notas Importantes](#notas)

---

## 📌 Resumen de Migración {#resumen}

### Proyecto Original (Laravel 12)
- **Tipo:** Monolítico con frontend integrado
- **Framework:** Laravel 12 (PHP)
- **Database:** MySQL 8.0
- **Frontend:** Blade templates + TailwindCSS 4 + Alpine.js
- **Assets:** Vite 7
- **Deployement:** Docker (7 servicios)
- **Features:** 14+ servicios, 18 modelos, 15+ controllers

### Proyecto Destino (Python)
- **Tipo:** API-First (Backend + Frontend separables)
- **Framework:** FastAPI + PyMongo
- **Database:** MongoDB 7.0 (local en PC)
- **Frontend:** HTML5 + Vite 7 + TailwindCSS 4 + Alpine.js (IGUAL)
- **Assets:** Vite 7 (IGUAL)
- **Deployment:** Docker (5 servicios: app, web, redis, mailpit; MongoDB local)
- **Features:** 14+ servicios Python, 18 modelos Pydantic, FastAPI routes

### Ventajas de Migración a Python
✅ **Performance:** FastAPI es más rápido que Laravel (async)  
✅ **Ecosistema:** Mejor para ML/AI (Gemini, pandas, numpy)  
✅ **Flexibilidad:** Python es más flexible y expresivo  
✅ **DevOps:** Contenedores más ligeros  
✅ **Comunidad:** Gran comunidad para FastAPI  
✅ **Escalabilidad:** Mejor soporte para microservicios  

### Desafíos de Migración
⚠️ **Base de Datos:** MySQL → MongoDB (cambio arquitectural)  
⚠️ **ORM:** Eloquent → PyMongo (syntaxis diferente)  
⚠️ **Validaciones:** Laravel validators → Pydantic models  
⚠️ **Autenticación:** Breeze → JWT manual  
⚠️ **Permisos:** Spatie → Role-based access control manual  
⚠️ **Migraciones:** Laravel migrations → MongoDB seeders  

---

## 🔄 Mapeo de Componentes {#mapeo}

### Arquitectura de Aplicación

| Laravel | Python | Equivalencia |
|---------|--------|-------------|
| **Controllers** | **FastAPI Routes** | Ambos manejan HTTP requests |
| `app/Http/Controllers` | `app/routes/` | Endpoint functions |
| Route handlers | APIRouter | Definición de rutas |
| **Models** | **Pydantic Models** | Definición de datos |
| `app/Models/User` | `app/models/user.py` | Entity representation |
| Relationships | Nested models | Relaciones entre datos |
| **Middleware** | **Middleware** | Same concept |
| Auth middleware | JWT middleware | Authorization |
| **Services** | **Services** | Business logic (igual) |
| `app/Services/` | `app/services/` | Reutilizable functions |
| **Repositories** | **Repositories** | Data access layer |
| Repository pattern | Same pattern | Abstracción de DB |
| **Exceptions** | **Custom Exceptions** | Error handling |
| Custom exceptions | Python exceptions | Error responses |
| **Policies** | **Role/Permission system** | Authorization |
| Gate/Policy | Roles + Permissions | Access control |
| **Traits** | **Mixins/Base classes** | Code reuse |
| Traits | Inheritance | Shared functionality |

### Capa de Presentación

| Laravel | Python | Equivalencia |
|---------|--------|-------------|
| **Blade templates** | **Jinja2 templates** | Server-side rendering |
| `resources/views/` | `resources/views/` | HTML templates |
| **Assets** | **Assets** | CSS/JS/Images |
| Vite + npm | Vite + npm | Same build process |
| **Frontend Framework** | **Frontend Framework** | IGUAL |
| TailwindCSS 4 | TailwindCSS 4 | Same styling |
| Alpine.js | Alpine.js | Same interactivity |

### Base de Datos

| Laravel | Python | Equivalencia |
|---------|--------|-------------|
| **MySQL 8.0** | **MongoDB 7.0** | CAMBIO ARQUITECTURAL |
| Tables | Collections | Data storage |
| Migrations | Seeders | Schema setup |
| Eloquent ORM | PyMongo | Data abstraction |
| Relationships | Nested documents | Data relationships |
| Transactions | Transactions | ACID properties |

### Testing

| Laravel | Python | Equivalencia |
|---------|--------|-------------|
| **PHPUnit** | **pytest** | Testing framework |
| Feature tests | Integration tests | Full feature testing |
| Unit tests | Unit tests | Component testing |
| **Cypress** | **Cypress** | E2E testing (IGUAL) |

---

## 🔄 Cambios Principales {#cambios}

### 1. Framework Web

**Laravel (PHP):**
```php
// routes/api.php
Route::post('/appointments', [AppointmentController::class, 'store']);
```

**FastAPI (Python):**
```python
# app/routes/appointments.py
@router.post('/appointments')
async def create_appointment(appointment: AppointmentSchema):
    return await appointment_service.create(appointment)
```

**Cambios:**
- Routing más explícito
- Async/await for I/O
- Type hints con Pydantic

### 2. Base de Datos

**Laravel (Eloquent/MySQL):**
```php
// app/Models/User.php
class User extends Model {
    public function appointments() {
        return $this->hasMany(Appointment::class);
    }
}

// En código
$user = User::find($id);
$appointments = $user->appointments;
```

**PyMongo (MongoDB):**
```python
# app/models/user.py
class User(BaseModel):
    id: Optional[ObjectId] = Field(alias="_id")
    name: str
    email: str
    appointments: List[Appointment] = []

# En código
user = await user_repository.find_by_id(user_id)
appointments = user.get('appointments', [])
```

**Cambios:**
- No hay relaciones automáticas (nested documents)
- Queries más explícitas
- Mejor para datos denormalizados

### 3. Validaciones

**Laravel (Form Requests):**
```php
// app/Http/Requests/CreateAppointmentRequest.php
public function rules() {
    return [
        'appointment_date' => 'required|date|after:today',
        'service_id' => 'required|exists:services,id',
    ];
}
```

**Pydantic (Python):**
```python
# app/schemas/appointment.py
class CreateAppointmentSchema(BaseModel):
    appointment_date: date = Field(..., gt=date.today())
    service_id: str = Field(..., min_length=24)  # MongoDB ObjectId
```

**Cambios:**
- Decoradores Pydantic
- Type hints obligatorios
- Validadores custom con `@validator`

### 4. Autenticación

**Laravel Breeze (Sessions + CSRF):**
```php
// Routing automático
Route::middleware('auth')->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'show']);
});
```

**FastAPI (JWT + Token):**
```python
# Manejo manual
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    return await user_repository.find_by_id(user_id)

@router.get('/dashboard')
async def dashboard(current_user: User = Depends(get_current_user)):
    return {"user": current_user}
```

**Cambios:**
- Tokens en lugar de sesiones
- Stateless authentication
- JWT payload custom

### 5. Servicios

**Laravel Service (igual concepto):**
```php
// app/Services/AppointmentService.php
class AppointmentService {
    public function createAppointment($data) {
        // Lógica de negocio
    }
}
```

**Python Service (igual concepto):**
```python
# app/services/appointment_service.py
class AppointmentService:
    async def create_appointment(self, data: dict):
        # Lógica de negocio
```

**Cambios:**
- Métodos async
- Inyección de dependencias explícita
- Type hints obligatorios

---

## 💻 Equivalencias de Código {#equivalencias}

### Controllers → FastAPI Routes

**Laravel Controller:**
```php
namespace App\Http\Controllers;

use App\Models\Appointment;
use App\Services\AppointmentService;

class AppointmentController extends Controller {
    public function __construct(private AppointmentService $service) {}
    
    public function index() {
        return Appointment::paginate(15);
    }
    
    public function store(CreateAppointmentRequest $request) {
        return $this->service->create($request->validated());
    }
    
    public function show(Appointment $appointment) {
        return $appointment;
    }
}
```

**FastAPI Routes:**
```python
from fastapi import APIRouter, Depends
from app.schemas.appointment import AppointmentSchema
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/appointments")
service = AppointmentService()

@router.get("/")
async def list_appointments(skip: int = 0, limit: int = 15):
    return await service.list(skip, limit)

@router.post("/")
async def create_appointment(data: AppointmentSchema):
    return await service.create(data.dict())

@router.get("/{appointment_id}")
async def get_appointment(appointment_id: str):
    return await service.get(appointment_id)
```

### Models → Pydantic Models

**Laravel Model:**
```php
class Appointment extends Model {
    protected $fillable = ['barber_id', 'client_id', 'appointment_date'];
    
    public function barber() {
        return $this->belongsTo(Barber::class);
    }
}
```

**Pydantic Model:**
```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Appointment(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    barber_id: str
    client_id: str
    appointment_date: datetime
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "barber_id": "123...",
                "client_id": "456...",
                "appointment_date": "2026-05-20T10:00:00"
            }
        }
```

### Eloquent Relationships → MongoDB Documents

**Laravel Eloquent:**
```php
// One-to-Many
$user->appointments()->get();

// Many-to-Many
$appointment->services()->get();

// Polymorphic
$comment->commentable()->get();
```

**MongoDB/PyMongo:**
```python
# One-to-Many (nested array)
user_doc = {
    "_id": ObjectId(...),
    "appointments": [
        {"id": ObjectId(...), "date": "..."},
        # ...
    ]
}

# Many-to-Many (array de IDs)
appointment_doc = {
    "_id": ObjectId(...),
    "service_ids": [ObjectId(...), ObjectId(...)]
}

# Polymorphic (type field)
comment_doc = {
    "_id": ObjectId(...),
    "commentable_type": "Work",  # o "Appointment", etc.
    "commentable_id": ObjectId(...)
}
```

### Migrations → Seeders

**Laravel Migration:**
```php
Schema::create('appointments', function (Blueprint $table) {
    $table->id();
    $table->foreignId('barber_id');
    $table->foreignId('client_id');
    $table->dateTime('appointment_date');
    $table->timestamps();
});
```

**MongoDB Seeder:**
```python
# database/seeders/appointments_seeder.py
async def seed_appointments(db):
    collection = db['appointments']
    
    # Crear índices
    await collection.create_index('barber_id')
    await collection.create_index('client_id')
    await collection.create_index('appointment_date')
    
    # Insertar datos
    documents = [
        {
            "barber_id": ObjectId(...),
            "client_id": ObjectId(...),
            "appointment_date": datetime(2026, 5, 20, 10, 0),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    ]
    
    await collection.insert_many(documents)
```

---

## 📁 Estructura de Proyecto {#estructura}

### Comparación: Laravel vs Python

**Laravel:**
```
laravel/
├── app/
│   ├── Http/Controllers/
│   ├── Models/
│   ├── Services/
│   ├── Repositories/
│   └── Notifications/
├── routes/
│   ├── api.php
│   ├── web.php
│   └── auth.php
├── database/
│   ├── migrations/
│   └── seeders/
├── resources/
│   ├── views/
│   ├── css/
│   └── js/
└── tests/
    ├── Unit/
    └── Feature/
```

**Python:**
```
BarberPro-Python/
├── app/
│   ├── models/              # Pydantic + MongoDB
│   ├── schemas/             # Request/Response
│   ├── repositories/        # Data access
│   ├── services/            # Business logic
│   ├── routes/              # API endpoints
│   ├── middleware/          # Auth, logging, etc.
│   ├── utils/               # Helpers
│   └── exceptions/          # Custom exceptions
├── database/
│   ├── connection.py        # MongoDB setup
│   ├── seeders/             # Data seeders
│   └── migrations/          # Schema setup
├── resources/               # Frontend (igual)
│   ├── views/
│   ├── css/
│   ├── js/
│   └── images/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
└── .docker/                 # Docker config
```

---

## 🔧 Stack Técnico {#stack}

### Backend Stack

| Capa | Laravel | Python |
|------|---------|--------|
| **Web Framework** | Laravel 12 | FastAPI |
| **ASGI/HTTP** | Built-in | Uvicorn |
| **Database** | MySQL 8.0 | MongoDB 7.0 |
| **ORM/ODM** | Eloquent | PyMongo + Pydantic |
| **Auth** | Breeze/Sessions | JWT |
| **Validation** | Form Requests | Pydantic |
| **Caching** | Redis | Redis (mismo) |
| **Queues** | Redis | Celery (optional) |
| **Logging** | Sentry | Sentry SDK |
| **Testing** | PHPUnit | pytest |

### Frontend Stack (SIN CAMBIOS)

| Componente | Versión | Nota |
|-----------|---------|------|
| **HTML** | HTML5 | Templates Jinja2 |
| **Build Tool** | Vite 7 | Igual |
| **Styling** | TailwindCSS 4 | Igual |
| **JS Framework** | Alpine.js 3 | Igual |
| **Node Packages** | npm | Igual |

### DevOps Stack

| Herramienta | Laravel | Python |
|----------|---------|--------|
| **Containerización** | Docker | Docker (igual) |
| **Orquestación** | docker-compose | docker-compose (igual) |
| **Web Server** | Nginx | Nginx (igual) |
| **Cache** | Redis | Redis (igual) |
| **Email** | Mailpit | Mailpit (igual) |
| **Database** | MySQL container | Local MongoDB |

---

## 📅 Plan de Implementación {#plan}

### FASE 2: Estructura Base (1.5 horas)
**Objetivo:** Setup inicial de FastAPI y MongoDB

**Tareas:**
- [ ] Crear `app/main.py` con FastAPI app
- [ ] Setup `app/config.py` con variables de entorno
- [ ] Crear `database/connection.py` para MongoDB
- [ ] Implementar `app/__init__.py`
- [ ] Dockerfile y docker-compose.yml
- [ ] Health checks

**Deliverables:**
- FastAPI app funcional
- MongoDB connection working
- Docker services running

### FASE 3: Modelos (3 horas)
**Objetivo:** Todos los 18 modelos Pydantic + MongoDB

**Modelos:**
1. User
2. Barber
3. Client
4. Appointment
5. Service
6. ServiceCombo
7. Payment
8. Product
9. Inventory
10. InventoryMovement
11. BarberSchedule
12. Work
13. WorkImage
14. Comment
15. Reaction
16. SavedWork
17. BarbershopSetting
18. Notification

**Por cada modelo:**
- [ ] Definición Pydantic
- [ ] MongoDB schema
- [ ] Validaciones
- [ ] Índices

### FASE 4: Repositories (2 horas)
**Objetivo:** Data access layer completo

**Tareas:**
- [ ] `repositories/base_repository.py` - Base class
- [ ] Repository para cada modelo (18 total)
- [ ] Métodos CRUD básicos
- [ ] Métodos de query complejos

### FASE 5: Servicios (4 horas)
**Objetivo:** Business logic de 14 servicios

**Servicios:**
1. AppointmentService
2. BusinessEventService
3. ChatbotContextService
4. ChatbotExternalDataService
5. ChatbotIntelligenceService
6. ChatbotLearningService
7. ChatbotUserProfileService
8. DashboardService
9. GeminiService
10. MessagingService
11. PaymentService
12. PredictionService
13. ReportService
14. ServiceService

**Por cada servicio:**
- [ ] Definición de clase
- [ ] Métodos principales
- [ ] Integración de dependencias
- [ ] Manejo de errores

### FASE 6: Autenticación (2 horas)
**Objetivo:** JWT + Roles + Permissions

**Tareas:**
- [ ] `utils/jwt.py` - JWT utilities
- [ ] `middleware/auth.py` - Auth middleware
- [ ] Role-based access control
- [ ] Login/Register endpoints
- [ ] Token refresh logic

**Roles:**
- admin
- recepcionista
- barbero
- cliente

### FASE 7: Rutas/API (4 horas)
**Objetivo:** Todos los endpoints funcionales

**Rutas:**
- [ ] `routes/auth.py` - Login, register, logout
- [ ] `routes/appointments.py` - CRUD citas
- [ ] `routes/barbers.py` - Barberos
- [ ] `routes/clients.py` - Clientes
- [ ] `routes/services.py` - Servicios
- [ ] `routes/payments.py` - Pagos
- [ ] `routes/inventory.py` - Inventario
- [ ] `routes/reports.py` - Reportes
- [ ] `routes/social.py` - Works, comments, likes
- [ ] `routes/dashboard.py` - Analytics
- [ ] `routes/chatbot.py` - IA

### FASE 8: Frontend (2 horas)
**Objetivo:** Setup Vite + Templates

**Tareas:**
- [ ] Configurar Vite
- [ ] Setup TailwindCSS
- [ ] Templates Jinja2 básicos
- [ ] Alpine.js components

### FASE 9: Testing (2.5 horas)
**Objetivo:** Suite de tests

**Tareas:**
- [ ] Unit tests (servicios)
- [ ] Integration tests (repositories)
- [ ] API tests (endpoints)
- [ ] E2E tests (Cypress)
- [ ] Min 50% coverage

### FASE 10: Docker (2 horas)
**Objetivo:** Production-ready Docker setup

**Tareas:**
- [ ] Dockerfile multi-stage
- [ ] docker-compose.yml (5 servicios)
- [ ] Health checks
- [ ] Volumes y networking
- [ ] Entrypoint script

### FASE 11: Documentación (2 horas)
**Objetivo:** Docs completa

**Tareas:**
- [ ] API documentation (FastAPI Docs)
- [ ] Setup guide
- [ ] Architecture documentation
- [ ] Migration notes
- [ ] Troubleshooting guide

---

## 📝 Notas Importantes {#notas}

### 1. MongoDB vs MySQL

**Consideraciones:**
- MongoDB es NoSQL (flexible schema)
- Mejor para datos denormalizados
- No hay foreign keys automáticas
- Necesita índices explícitos
- Transactions requieren setup especial

**Estrategia:**
- Usar nested documents donde sea posible
- Mantener IDs explícitos para relaciones
- Crear índices en seeders
- Usar Pydantic para validación

### 2. Async/Await

**FastAPI es async por defecto:**
```python
# Siempre usar async
@router.get("/")
async def list_items():
    return await repository.list()  # await necesario

# No hacer esto (síncono)
@router.get("/")
def list_items():  # ❌ No usar
    return repository.list()
```

### 3. Type Hints

**Obligatorios en Python:**
```python
# Correcto
async def get_user(user_id: str) -> User:
    return await repository.find_by_id(user_id)

# Incompleto (pero funciona)
async def get_user(user_id):
    return await repository.find_by_id(user_id)
```

### 4. Dependency Injection

**FastAPI usa Depends():**
```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    # Validar token
    return user

@router.get("/dashboard")
async def dashboard(user: User = Depends(get_current_user)):
    return {"user": user}
```

### 5. Error Handling

**Usar HTTPException:**
```python
from fastapi import HTTPException, status

@router.get("/{item_id}")
async def get_item(item_id: str):
    item = await repository.find_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item
```

### 6. Testing

**Usar pytest con httpx client:**
```python
@pytest.mark.asyncio
async def test_list_appointments():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/appointments/")
        assert response.status_code == 200
```

### 7. MongoDB Connection

**En desarrollo (local):**
```python
MONGO_URL = "mongodb://localhost:27017"
```

**En producción (si fuera Atlas):**
```python
MONGO_URL = "mongodb+srv://user:password@cluster.mongodb.net"
```

### 8. Environment Variables

**Usar .env (python-dotenv):**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "BarberPro"
    mongo_url: str = "mongodb://localhost:27017"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 9. Logging

**Usar Python logging:**
```python
import logging

logger = logging.getLogger(__name__)

@router.get("/")
async def list_items():
    logger.info("Listing items")
    return await repository.list()
```

### 10. CORS en Desarrollo

**FastAPI CORS middleware:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## ✅ Checklist Pre-Implementación

- [ ] Python 3.11+ instalado
- [ ] MongoDB 7.0+ corriendo en puerto 27017
- [ ] Docker instalado
- [ ] Estructura de directorios creada
- [ ] .env.example listo
- [ ] requirements.txt actualizado
- [ ] Equipo familiarizado con FastAPI
- [ ] Equipo familiarizado con PyMongo

---

## 🎯 Siguiente Paso

Comenzar **FASE 2: Estructura Base**

Ver: `SETUP_INICIAL.md` para primeros pasos
