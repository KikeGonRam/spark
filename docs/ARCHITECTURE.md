# 🏗️ ARQUITECTURA: BarberPro Python Edition

**Estado:** Fase 2 - En Construcción  
**Actualizado:** 2026-05-16  
**Versión:** 2.0.0

---

## 📐 DIAGRAMA GENERAL DE ARQUITECTURA

```
┌─────────────────────────────────────────────────────────────────┐
│                      NAVEGADOR / CLIENTE                         │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  FRONTEND (Web)                          │    │
│  │                                                           │    │
│  │  HTML5 + Vite 7 + TailwindCSS 4 + Alpine.js 3          │    │
│  │                                                           │    │
│  │  ├─ resources/views/ (HTML templates)                  │    │
│  │  ├─ resources/css/ (TailwindCSS)                       │    │
│  │  ├─ resources/js/ (Alpine.js + API calls)             │    │
│  │  └─ public/ (Built assets after Vite build)           │    │
│  │                                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             ↑                                     │
│                      REST API Calls                              │
│                      JSON over HTTP                              │
│                             ↓                                     │
└─────────────────────────────────────────────────────────────────┘
                         ↓
        ┌────────────────────────────────────────────┐
        │      NGINX (Web Server/Reverse Proxy)      │
        │           Port: 80/443                     │
        │                                            │
        │  ├─ Serve static assets (/static)         │
        │  ├─ Proxy API requests to FastAPI (:8000) │
        │  ├─ SSL/TLS termination                   │
        │  └─ Compression, caching                  │
        └────────────────────────────────────────────┘
                         ↓
        ┌────────────────────────────────────────────┐
        │  FASTAPI REST API (Backend)                │
        │      Port: 8000 (Uvicorn)                 │
        │                                            │
        │  ┌──────────────────────────────────────┐ │
        │  │  app/                                 │ │
        │  │  ├─ main.py (FastAPI app)            │ │
        │  │  ├─ config.py (Settings)             │ │
        │  │  ├─ routes/ (API endpoints)          │ │
        │  │  │  ├─ auth.py                       │ │
        │  │  │  ├─ appointments.py               │ │
        │  │  │  ├─ barbers.py                    │ │
        │  │  │  ├─ services.py                   │ │
        │  │  │  └─ ... (others)                  │ │
        │  │  ├─ services/ (Business Logic)       │ │
        │  │  │  ├─ appointment_service.py        │ │
        │  │  │  ├─ chatbot_service.py            │ │
        │  │  │  ├─ payment_service.py            │ │
        │  │  │  └─ ... (14 total)                │ │
        │  │  ├─ repositories/ (Data Access)      │ │
        │  │  │  ├─ base_repository.py            │ │
        │  │  │  ├─ user_repository.py            │ │
        │  │  │  └─ ... (18 total)                │ │
        │  │  ├─ models/ (Pydantic Models)        │ │
        │  │  │  ├─ user.py                       │ │
        │  │  │  ├─ appointment.py                │ │
        │  │  │  └─ ... (18 total)                │ │
        │  │  ├─ schemas/ (Request/Response)      │ │
        │  │  ├─ middleware/ (Custom Middleware)  │ │
        │  │  ├─ utils/ (Helper Functions)        │ │
        │  │  └─ exceptions/ (Custom Exceptions)  │ │
        │  │                                      │ │
        │  │  Middleware Stack:                   │ │
        │  │  ├─ CORS Middleware                  │ │
        │  │  ├─ JWT Authentication               │ │
        │  │  ├─ Rate Limiting (slowapi)          │ │
        │  │  ├─ Error Handling                   │ │
        │  │  └─ Logging                          │ │
        │  │                                      │ │
        │  └──────────────────────────────────────┘ │
        │                                            │
        │  OpenAPI Docs: http://localhost:8000/docs │
        │  ReDoc: http://localhost:8000/redoc       │
        │                                            │
        └────────────────────────────────────────────┘
                ↓          ↓          ↓
        ┌──────────┐ ┌──────────┐ ┌────────────┐
        │ MONGODB  │ │  REDIS   │ │  MAILPIT   │
        │ (Local)  │ │ (Cache)  │ │  (Email)   │
        │ :27017   │ │ :6379    │ │ :1025      │
        │          │ │          │ │            │
        │ ┌─────┐  │ │ ┌──────┐ │ │  SMTP      │
        │ │ app │  │ │ │Cache│ │ │  Testing   │
        │ │ db  │  │ │ │ db 0│ │ │            │
        │ │ ... │  │ │ └──────┘ │ │ WebUI      │
        │ │     │  │ │          │ │ :8025      │
        │ └─────┘  │ │ ┌──────┐ │ │            │
        │ Database │ │ │Queue│ │ │            │
        │ Storage  │ │ │ db 1│ │ │            │
        │          │ │ └──────┘ │ │            │
        └──────────┘ └──────────┘ └────────────┘
```

---

## 🎯 ARQUITECTURA DE CAPAS

### Layer 1: Presentation (Frontend)
```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│                                         │
│  HTML5 + Vite 7 + TailwindCSS 4        │
│  + Alpine.js 3 (Lightweight SPA)        │
│                                         │
│  Responsabilidades:                     │
│  • Render UI                            │
│  • User interactions                    │
│  • Form validation (client-side)        │
│  • API calls (fetch/axios)              │
│  • Local state management               │
│  • Cache tokens en localStorage         │
└─────────────────────────────────────────┘
              ↓ JSON/REST
```

### Layer 2: API Gateway (Nginx)
```
┌─────────────────────────────────────────┐
│        API GATEWAY LAYER (Nginx)        │
│                                         │
│  Responsabilidades:                     │
│  • Route requests                       │
│  • SSL/TLS termination                  │
│  • Compression                          │
│  • Static file serving                  │
│  • Rate limiting (nginx)                │
│  • Load balancing (si múltiples apps)   │
└─────────────────────────────────────────┘
              ↓ HTTP
```

### Layer 3: API Application (FastAPI)
```
┌─────────────────────────────────────────┐
│        APPLICATION LAYER (FastAPI)      │
│                                         │
│  Responsabilidades:                     │
│  • Route handling                       │
│  • Request validation (Pydantic)        │
│  • Authentication/Authorization         │
│  • Business logic orchestration         │
│  • Response formatting                  │
│  • Error handling                       │
│  • Logging & monitoring                 │
└─────────────────────────────────────────┘
              ↓
```

### Layer 4: Business Logic (Services)
```
┌─────────────────────────────────────────┐
│      BUSINESS LOGIC LAYER (Services)    │
│                                         │
│  Responsabilidades:                     │
│  • Core business rules                  │
│  • Data transformations                 │
│  • External service integration         │
│  • IA (Google Gemini)                   │
│  • Email notifications                  │
│  • File generation (PDF/Excel)          │
│  • Complex calculations                 │
│  • Transaction management               │
└─────────────────────────────────────────┘
              ↓
```

### Layer 5: Data Access (Repositories)
```
┌─────────────────────────────────────────┐
│     DATA ACCESS LAYER (Repositories)    │
│                                         │
│  Responsabilidades:                     │
│  • Query building                       │
│  • Database operations (CRUD)           │
│  • Query optimization                   │
│  • Caching layer                        │
│  • Connection pooling                   │
│  • Transaction coordination             │
└─────────────────────────────────────────┘
              ↓
```

### Layer 6: Data Storage (MongoDB)
```
┌─────────────────────────────────────────┐
│      DATA STORAGE LAYER (MongoDB)       │
│                                         │
│  Responsabilidades:                     │
│  • Persistent data storage              │
│  • Indexing                             │
│  • Replication (production)             │
│  • Backup/Recovery                      │
│  • Query execution                      │
└─────────────────────────────────────────┘
```

---

## 🔄 REQUEST FLOW EXAMPLE: Crear Cita

```
1. Frontend (HTML)
   └─ User submits appointment form
      └─ Validate locally (HTML5 + JavaScript)
         └─ POST /api/appointments (JSON)

2. Nginx (Reverse Proxy)
   └─ Receives POST request
      └─ SSL/TLS check
         └─ Route to FastAPI :8000
            └─ Add headers (X-Forwarded-For, etc.)

3. FastAPI (Route Handler)
   └─ app.routes.appointments.create_appointment()
      └─ Parse request body → CreateAppointmentSchema
         └─ Validate with Pydantic
            └─ Check authentication (JWT)
               └─ Check authorization (role-based)
                  └─ Call service

4. Service Layer
   └─ AppointmentService.create_appointment(data)
      └─ Validate business rules
         └─ Check barber availability
            └─ Check service validity
               └─ Calculate price
                  └─ Create appointment object
                     └─ Call repository

5. Repository Layer
   └─ AppointmentRepository.create(appointment)
      └─ Check Redis cache (if exists)
         └─ Insert into MongoDB
            └─ Update cache
               └─ Return created appointment

6. Service Layer (cont.)
   └─ Send notifications
      └─ Update related entities
         └─ Log activity
            └─ Return result to controller

7. FastAPI (Response)
   └─ Format response (CreateAppointmentResponse)
      └─ Set HTTP status 201
         └─ Add headers
            └─ Serialize to JSON
               └─ Return to client

8. Nginx (Reverse Proxy)
   └─ Receives response
      └─ Compress (gzip)
         └─ Add caching headers
            └─ Return to client

9. Frontend (Browser)
   └─ Receive JSON response
      └─ Parse response
         └─ Update UI
            └─ Show success message
               └─ Navigate to appointment details
```

---

## 🛠️ COMPONENTES PRINCIPALES

### Frontend Components

```javascript
// Base Components (Alpine.js)
├─ Modal
├─ Toast Notifications
├─ Forms
├─ Tables/Lists
├─ Dropdowns
├─ Pagination
└─ Loading States

// Page Components
├─ Auth Pages (login, register)
├─ Dashboard
├─ Appointments
├─ Barbers
├─ Services
├─ Payments
├─ Reports
└─ Profile
```

### Backend Components

```python
# Routes (Endpoints)
├─ /api/auth/        → Authentication
├─ /api/appointments → Citas
├─ /api/barbers      → Barberos
├─ /api/services     → Servicios
├─ /api/clients      → Clientes
├─ /api/payments     → Pagos
├─ /api/reports      → Reportes
├─ /api/inventory    → Inventario
├─ /api/dashboard    → Dashboards
└─ /api/social       → Feed/Comentarios

# Services (Business Logic)
├─ AppointmentService
├─ BarbershopService
├─ PaymentService
├─ NotificationService
├─ ChatbotService (Gemini)
├─ ReportService (PDF/Excel)
├─ InventoryService
└─ DashboardService

# Repositories (Data Access)
├─ UserRepository
├─ BarberRepository
├─ AppointmentRepository
├─ ServiceRepository
├─ PaymentRepository
├─ ClientRepository
└─ ... (18 total)

# Models (Data Structures)
├─ User
├─ Barber
├─ Client
├─ Appointment
├─ Service
├─ Payment
├─ Product
├─ Work
└─ ... (18 total)
```

---

## 📊 DATA FLOW PATTERNS

### Pattern 1: Simple Query
```
GET /api/barbers/{id}
  ↓
BarbersRouter.get_barber(id)
  ↓
BarbersService.get_barber(id)
  ↓
BarberRepository.find_by_id(id)
  ↓
MongoDB Collection Query
  ↓
Barber Document
  ↓
Response (BarberSchema)
```

### Pattern 2: Create with Related Data
```
POST /api/appointments
  ↓
AppointmentRouter.create_appointment(data)
  ↓
AppointmentService.create_appointment(data)
  ├─ Validate barber exists
  ├─ Validate service exists
  ├─ Check availability
  └─ Create appointment
  ↓
AppointmentRepository.create(appointment)
  ↓
MongoDB Insert
  ↓
NotificationService.send_notifications()
  ├─ Email to barber
  └─ Email to client
  ↓
Response (AppointmentSchema)
```

### Pattern 3: Complex Query with Filters
```
GET /api/appointments?barber_id=X&status=pending
  ↓
AppointmentRouter.list_appointments(filters)
  ↓
AppointmentService.list(filters)
  ↓
AppointmentRepository.find(query, filters)
  ↓
MongoDB Aggregation Pipeline
  ├─ Match filters
  ├─ Sort
  ├─ Paginate
  └─ Lookup related data
  ↓
List[AppointmentSchema]
```

---

## 🔐 SECURITY LAYERS

### Frontend Security
```
1. Input Validation (HTML5)
2. XSS Protection (HTML escaping)
3. CSRF Protection (tokens)
4. Secure Storage (IndexedDB, not localStorage for sensitive)
5. HTTPS Only (production)
```

### API Security
```
1. CORS (Frontend origin validation)
2. JWT Authentication (Bearer tokens)
3. Authorization (Role-based access)
4. Input Validation (Pydantic)
5. Rate Limiting (slowapi)
6. SQL Injection Prevention (PyMongo)
7. Error Handling (no stack traces in prod)
8. HTTPS (nginx termination)
9. HSTS Headers
10. Secure Cookies
```

### Database Security
```
1. Authentication (user/password)
2. Network isolation (local only in dev)
3. Backups
4. Encryption at rest (production)
5. Encryption in transit (TLS)
```

---

## 📈 SCALABILITY CONSIDERATIONS

### Current Setup (Single Machine)
```
Frontend + Backend + DB on Same Machine
- Good for: Development, small deployments
- Limitation: Single point of failure
```

### Future Scaling (Multi-Machine)
```
Tier 1: Load Balancer
  ↓
Tier 2: FastAPI Replicas (multiple)
  ↓
Tier 3: MongoDB Replica Set
  ↓
Tier 4: Redis Cluster
```

---

## 🧪 TESTING STRATEGY

### Frontend Testing
```
├─ Unit Tests (jest)
├─ Integration Tests
└─ E2E Tests (Cypress)
```

### Backend Testing
```
├─ Unit Tests (pytest)
│  └─ Services
│  └─ Repositories
│  └─ Utils
├─ Integration Tests
│  └─ API Endpoints
│  └─ Database operations
└─ E2E Tests (pytest + httpx)
   └─ Full flow testing
```

---

## 📝 DEPLOYMENT ARCHITECTURE

### Development
```
docker-compose up
├─ FastAPI app (:8000)
├─ Nginx (:80)
├─ Redis
├─ Mailpit
└─ MongoDB (local PC)
```

### Production (Future)
```
Kubernetes / Docker Swarm
├─ FastAPI Pods (replicated)
├─ Nginx Ingress
├─ MongoDB Atlas / Cloud
├─ Redis Cloud
├─ CDN (CloudFlare)
└─ Monitoring (Prometheus, Grafana)
```

---

## ✅ VERIFICACIÓN DE FASE 2

- [x] Frameworks decididos (FastAPI + HTML5+Vite)
- [x] Architecture documentada
- [x] app/main.py creado
- [x] app/config.py creado
- [x] database/connection.py creado
- [ ] Health checks funcionando
- [ ] Docker validado
- [ ] Inicialmente corriendo

---

**Siguiente paso:** Probar que FastAPI inicie correctamente
