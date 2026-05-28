# 🔗 INTEGRATION TESTING - MULTI-ROLE WORKFLOWS

**Archivo:** `tests/e2e/test_integration_workflows.py`  
**Tests:** 8 workflows de integración  
**Enfoque:** Cómo los roles interactúan entre sí  
**Tamaño:** 24 KB  

---

## 📋 RESUMEN

Los tests de integración validan cómo **Admin, Cliente y Barbero** trabajan juntos en workflows reales del sistema. No solo prueba cada rol en aislamiento, sino cómo se **relacionan y dependen unos de otros**.

---

## 🔄 LOS 8 WORKFLOWS DE INTEGRACIÓN

### IT-1: Admin → Service → Client

```
Admin crea servicio
    ↓
Client ve el servicio
    ↓
✅ Validar visibilidad y acceso
```

**Test:** `test_admin_creates_service_client_sees_it`

**Validación:**
- Admin puede POST `/api/services`
- Client puede GET `/api/services`
- El servicio creado por Admin aparece en lista de Client
- IDs y detalles coinciden

**Caso de Uso Real:** Un nuevo servicio (ej: "Afeitado Premium") está disponible para que los clientes lo vean.

---

### IT-2: Admin → Barber → Client

```
Admin crea barbero
    ↓
Client ve el barbero
    ↓
Client puede agendar con él
    ↓
✅ Validar disponibilidad
```

**Test:** `test_admin_creates_barber_client_sees_it`

**Validación:**
- Admin puede POST `/api/barbers`
- Client puede GET `/api/barbers`
- Barber creado por Admin visible para Client
- Información completa del barbero disponible

**Caso de Uso Real:** Admin contrata nuevo barbero → Cliente ve barbero disponible.

---

### IT-3: Client → Books → Barber → Sees It

```
Client agenda cita
    ↓
Barber ve la cita
    ↓
Ambos ven los mismos detalles
    ↓
✅ Validar sincronización
```

**Test:** `test_client_books_barber_sees_appointment`

**Validación:**
- Client POST `/api/appointments` → 201
- Barber GET `/api/barbers/appointments` → ve la cita
- Mismo `appointment_id` en ambas vistas
- IDs de barber/client coinciden

**Caso de Uso Real:** Cliente agenda cita → Barbero recibe la notificación y la ve en su agenda.

---

### IT-4: Admin Monitors Everything

```
Client agenda cita
    ↓
Admin ve TODAS las citas
    ↓
Admin puede generar reportes
    ↓
✅ Validar visibilidad total
```

**Test:** `test_admin_sees_client_appointments`

**Validación:**
- Client POST `/api/appointments`
- Admin GET `/api/appointments` → ve TODAS
- Appointment ID visible en lista del admin
- Información completa disponible

**Caso de Uso Real:** Admin supervisa todas las citas para reportes y gestión.

---

### IT-5: Barber Updates → Everyone Sees

```
Barber inicia cita (in_progress)
    ↓
Client ve estado actualizado
    ↓
Admin ve estado actualizado
    ↓
✅ Validar propagación de cambios
```

**Test:** `test_barber_updates_appointment_status_client_sees_it`

**Validación:**
- Barber PATCH `/api/appointments/{id}` → status cambió
- Client GET `/api/clients/appointments` → ve nuevo status
- Admin GET `/api/appointments` → ve nuevo status
- Todos ven el mismo status

**Caso de Uso Real:**
- Barber: "Empezando corte" → status = in_progress
- Client recibe notificación del cambio
- Admin ve el progreso en tiempo real

---

### IT-6: Client Pays → Appointment Confirmed

```
Client realiza pago
    ↓
Appointment status → paid/confirmed
    ↓
Admin ve el pago
    ↓
✅ Validar cadena de pagos
```

**Test:** `test_client_payment_updates_appointment_status`

**Validación:**
- Client POST `/api/payments`
- Appointment status cambia (paid/confirmed)
- Admin GET `/api/payments` → ve el pago
- Relación cliente-barbero confirmada

**Caso de Uso Real:** Cliente paga por adelantado → Barbero sabe que cita confirmada.

---

### IT-7: Complete Real-World Workflow

```
ADMIN SETUP:
├─ Crea servicio
└─ Crea barbero

CLIENT BOOKS:
├─ Ve barbero en lista
├─ Ve servicio en lista
└─ Agenda cita

BARBER WORKS:
├─ Ve cita en agenda
├─ Inicia servicio (status → in_progress)
└─ Completa servicio

ADMIN MONITORS:
└─ Ve toda la cadena de eventos

✅ Validar flujo completo
```

**Test:** `test_complete_barbershop_workflow`

**Secuencia:**
1. Setup: Service + Barber
2. Client: Booking
3. Barber: Workflow (See → Update)
4. Admin: Monitoring
5. Verify: Data consistency

**Caso de Uso Real:** Un día completo de operaciones de la barbería.

---

### IT-8: Data Consistency Across Views

```
Appointment creada por Client
    ↓
Client ve: appointmentID = 12345, status = pending
    ↓
Barber ve: appointmentID = 12345, status = pending
    ↓
Admin ve: appointmentID = 12345, status = pending
    ↓
✅ Validar que todos ven lo mismo
```

**Test:** `test_appointment_data_consistency`

**Validación:**
- Appointment ID idéntico
- Status idéntico
- Timestamps idénticos
- Información del servicio idéntica
- No hay inconsistencias

**Caso de Uso Real:** Garantizar que nadie ve datos diferentes/stale.

---

## 🔐 RELACIONES ENTRE ROLES

### Admin ↔ Client
```
Admin crea/gestiona:
├─ Servicios
├─ Barberos
└─ Reportes globales

Client ve:
├─ Servicios disponibles
├─ Barberos disponibles
└─ Sus propias citas
```

### Admin ↔ Barber
```
Admin:
├─ Crea/edita barbero
└─ Ve reportes

Barber:
├─ Ve citas creadas por cliente
├─ Actualiza estado
└─ Genera reportes personales
```

### Client ↔ Barber
```
Client:
├─ Elige barbero
├─ Agenda cita
└─ Paga servicio

Barber:
├─ Ve cita del cliente
├─ Realiza servicio
└─ Actualiza estado
```

---

## 📊 MATRIZ DE INTERACCIONES

```
         ADMIN    CLIENT   BARBER
CREATE
├─ Service  ✅      ❌      ❌
├─ Barber   ✅      ❌      ❌
└─ Apt      ✅      ✅      ✅

READ
├─ Services ✅      ✅      ✅
├─ Barbers  ✅      ✅      ✅
├─ Apts(all)✅      ❌      ❌
├─ Apts(own)✅      ✅      ✅
└─ Payments ✅      ✅      ❌

UPDATE
├─ Barber   ✅      ❌      ❌
├─ Status   ✅      ❌      ✅
└─ Payment  ✅      ✅      ❌

DELETE
└─ Apt      ✅      ✅(own) ❌
```

---

## 🧪 CÓMO EJECUTAR ESTOS TESTS

### Ejecutar solo integraciones
```bash
pytest tests/e2e/test_integration_workflows.py -v
```

### Ejecutar workflow específico
```bash
pytest tests/e2e/test_integration_workflows.py::TestAdminClientWorkflow -v
```

### Ejecutar con output detallado
```bash
pytest tests/e2e/test_integration_workflows.py -v -s
```

### Ejecutar sin tests lentos
```bash
pytest tests/e2e/test_integration_workflows.py -v -m "not slow"
```

---

## 📈 MÉTRICAS DE COBERTURA

### Endpoints Validados
```
POST   /api/services              ✅
GET    /api/services              ✅
POST   /api/barbers               ✅
GET    /api/barbers               ✅
POST   /api/appointments          ✅
GET    /api/appointments          ✅ (admin - all)
GET    /api/clients/appointments  ✅ (client - own)
GET    /api/barbers/appointments  ✅ (barber - own)
PATCH  /api/appointments/{id}     ✅
POST   /api/payments              ✅
GET    /api/payments              ✅ (admin)
```

### Validaciones por Rol
```
ADMIN
├─ Crear recursos          ✅
├─ Ver todo                ✅
└─ Monitoreo total         ✅

CLIENT
├─ Ver opciones            ✅
├─ Crear cita              ✅
├─ Pagar                   ✅
└─ Ver propias citas       ✅

BARBER
├─ Ver propias citas       ✅
├─ Actualizar estado       ✅
└─ Ver clientes            ✅
```

---

## 🔍 EJEMPLO: IT-3 EN DETALLE

### Código del Test
```python
def test_client_books_barber_sees_appointment(
    client: TestClient,
    client_headers,
    barber_headers,
    created_service
):
    # Step 1: Get barber
    barbers = client.get("/api/barbers", headers=client_headers).json()
    barber_id = barbers[0]["id"]
    
    # Step 2: Client books
    appointment = client.post(
        "/api/appointments",
        headers=client_headers,
        json={
            "barber_id": barber_id,
            "service_id": created_service["id"],
            "date_time": future_time.isoformat(),
            "notes": "Integration test"
        }
    ).json()
    appointment_id = appointment["id"]
    
    # Step 3: Barber sees it
    barber_appointments = client.get(
        "/api/barbers/appointments",
        headers=barber_headers
    ).json()
    
    assert any(apt["id"] == appointment_id for apt in barber_appointments)
```

### Flujo Esperado
```
1. GET /api/barbers (client)
   ← Lista de barberos

2. POST /api/appointments (client)
   ← Appointment creado

3. GET /api/barbers/appointments (barber)
   ← Incluye appointment del paso 2

✅ PASS: Same appointment_id visible en ambos
```

### Qué Valida
- ✅ Client puede ver barberos
- ✅ Client puede crear appointment
- ✅ Barber puede ver sus propias citas
- ✅ Relación cliente-barbero funciona
- ✅ IDs son consistentes

---

## 🐛 DEBUGGING INTEGRATION TESTS

### Si un test falla:

**1. Lee el output detallado**
```bash
pytest tests/e2e/test_integration_workflows.py::TestClientBarberWorkflow -v -s
```

**2. Verifica los pasos con prints**
```
✅ Step 1: Barber retrieved
✅ Step 2: Client booked appointment
✅ Step 3: Barber sees appointment
❌ Step 4: Failed - assertion error
```

**3. Verifica los datos**
- ¿Los IDs coinciden?
- ¿Los statuses son los esperados?
- ¿Las rutas existen?

**4. Verifica las dependencias**
- ¿Existen barberos?
- ¿Existen servicios?
- ¿La BD está limpia?

---

## 📊 RESULTADO ESPERADO

### Ejecución Exitosa
```
tests/e2e/test_integration_workflows.py::TestAdminClientWorkflow::test_admin_creates_service_client_sees_it PASSED
tests/e2e/test_integration_workflows.py::TestAdminClientWorkflow::test_admin_creates_barber_client_sees_it PASSED
tests/e2e/test_integration_workflows.py::TestClientBarberWorkflow::test_client_books_barber_sees_appointment PASSED
tests/e2e/test_integration_workflows.py::TestAdminMonitoringWorkflow::test_admin_sees_client_appointments PASSED
tests/e2e/test_integration_workflows.py::TestBarberStatusUpdateWorkflow::test_barber_updates_appointment_status_client_sees_it PASSED
tests/e2e/test_integration_workflows.py::TestPaymentWorkflow::test_client_payment_updates_appointment_status PASSED
tests/e2e/test_integration_workflows.py::TestMultiRoleCompleteWorkflow::test_complete_barbershop_workflow PASSED
tests/e2e/test_integration_workflows.py::TestDataConsistencyAcrossRoles::test_appointment_data_consistency PASSED

================ 8 passed in 12.34s ================
✅ ALL INTEGRATION TESTS PASSED
```

---

## ✅ CHECKLIST DESPUÉS DE TESTS

- [ ] Todos los 8 workflows pasaron
- [ ] Output muestra PASS en cada step
- [ ] Datos consistentes entre roles
- [ ] No hay race conditions
- [ ] Relaciones entre entidades funcionan
- [ ] Admin puede monitorear todo
- [ ] Client ve solo su data
- [ ] Barber ve solo sus citas

---

## 🎯 QUÉ ESTOS TESTS PRUEBAN QUE OTROS NO

| Aspecto | Unit Tests | Integration Tests |
|---------|-----------|-----------------|
| Endpoint individual | ✅ | ✅ |
| Rol específico | ✅ | ✅ |
| **Interacción entre roles** | ❌ | ✅ |
| **Flujo completo** | ❌ | ✅ |
| **Data consistency** | ❌ | ✅ |
| **Status propagation** | ❌ | ✅ |
| **Admin monitoring** | ❌ | ✅ |

---

## 📚 DOCUMENTACIÓN RELACIONADA

- `E2E_TESTING_REPORT.md` - Todos los 57 tests
- `E2E_TESTING_QUICK_START.md` - Cómo ejecutar
- `tests/e2e/test_auth.py` - Tests de autenticación
- `tests/e2e/test_roles.py` - Tests de roles
- `tests/e2e/conftest.py` - Fixtures compartidas

---

## 🎉 CONCLUSIÓN

Los **8 tests de integración** validan que el sistema completo funciona como un todo, con todos los roles interactuando correctamente. Estos tests son más fuertes que los unitarios porque prueban escenarios reales.

**Total de Tests E2E: 57 + 8 = 65 casos de prueba**

---

**Documento Generado:** 17 de Mayo de 2026  
**Próxima Fase:** Frontend Testing

