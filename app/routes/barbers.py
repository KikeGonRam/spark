"""
Barber Routes - Gestión de barberos
Endpoints: /api/barbers/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date
from typing import Optional, List

from app.models import (
    Barber,
    BarberCreate,
    BarberWithUserCreate,
    BarberUpdate,
    User,
)
from app.services import BarberService
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)
from app.routes.dependencies import (
    get_barber_service,
    require_admin,
    require_barber,
    require_authenticated,
)

router = APIRouter()



# ===== CREATE =====

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_barber(
    barber_data: BarberWithUserCreate,
    current_user: User = Depends(require_admin),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Crear un nuevo barbero con cuenta de usuario.
    **SOLO ADMIN**

    **Request body:**
    - name: Nombre del barbero
    - email: Email único
    - password: Contraseña
    - phone: Teléfono (opcional)
    - specialization: Lista de especializaciones
    - bio: Biografía (opcional)
    - working_hours_start: Horario de inicio (HH:MM, opcional)
    - working_hours_end: Horario de fin (HH:MM, opcional)

    **Response:**
    - barber: Datos del barbero creado

    **Códigos de respuesta:**
    - 201: Barbero creado
    - 400: Validación fallida
    - 403: Solo admin puede crear barberos
    """
    try:
        from app.repositories import UserRepository
        from app.services import AuthService
        from app.models import UserCreate, UserRole
        from app.routes.dependencies import get_db
        
        db = get_db()
        
        # Crear usuario
        user_repo = UserRepository(db)
        auth_service = AuthService(user_repo)
        
        user_create = UserCreate(
            name=barber_data.name,
            email=barber_data.email,
            password=barber_data.password,
            phone=barber_data.phone,
            role=UserRole.BARBER,
        )
        
        user_result = await auth_service.register(user_create, role=UserRole.BARBER)
        user = user_result["user"]
        user_id = user.id if hasattr(user, 'id') else user['id']
        
        # Crear barbero
        barber_create = BarberCreate(
            user_id=user_id,
            specialization=barber_data.specialization,
            bio=barber_data.bio,
            working_hours_start=barber_data.working_hours_start,
            working_hours_end=barber_data.working_hours_end,
        )
        
        barber_id = await barber_service.create_barber(barber_create)
        barber = await barber_service.get_barber_by_id(barber_id)
        
        return {
            "success": True,
            "message": "Barbero creado exitosamente",
            "data": {"barber": barber.dict()},
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ===== READ =====

@router.get("", response_model=list)
async def list_barbers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Listar barberos.

    **Query parameters:**
    - skip: Número de registros a saltar (default: 0)
    - limit: Número máximo (default: 50, max: 100)

    **Response:**
    - Lista de barberos

    **Códigos de respuesta:**
    - 200: Lista obtenida
    """
    try:
        barbers = await barber_service.list_barbers(skip=skip, limit=limit)
        return [barber.dict() for barber in barbers]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ===== BARBER'S OWN DATA (Current User) - Must come before /{barber_id} =====

@router.get("/appointments", response_model=list)
async def get_my_appointments(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_barber),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener citas del barbero autenticado.
    
    **Query parameters:**
    - status: Filtrar por estado (opcional)
    - skip: Registros a saltar
    - limit: Límite de registros
    
    **Response:**
    - Lista de citas del barbero
    """
    try:
        # Get barber ID from user_id
        from app.repositories import BarberRepository
        from app.routes.dependencies import get_db
        
        db = get_db()
        barber = await BarberRepository(db).find_by_field("user_id", str(current_user.id))
        
        if not barber:
            return []
        
        appointments = await barber_service.list_barber_appointments(
            str(barber.id),
            status=status
        )
        return [apt.dict() for apt in appointments]
    except Exception:
        return []


@router.get("/schedule", response_model=dict)
async def get_my_schedule(
    current_user: User = Depends(require_barber),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener horario del barbero autenticado.
    
    **Response:**
    - schedule: Horario configurado
    """
    try:
        from app.repositories import BarberRepository
        from app.routes.dependencies import get_db
        
        db = get_db()
        barber = await BarberRepository(db).find_by_field("user_id", str(current_user.id))
        
        if not barber:
            raise ResourceNotFoundError("Barber not found")
        
        schedule = await barber_service.get_barber_schedule(str(barber.id))
        # Convert schedule objects to dicts
        schedule_data = [s.dict() if hasattr(s, 'dict') else s for s in (schedule or [])]
        return {
            "success": True,
            "data": {"schedule": schedule_data}
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/clients", response_model=list)
async def get_my_clients(
    current_user: User = Depends(require_barber),
):
    """
    Obtener clientes del barbero autenticado.
    
    **Response:**
    - Lista de clientes
    """
    # TODO: Implementar obtención de clientes únicos del barbero
    return []


# ===== PARAMETRIZED ROUTES - Must come AFTER non-parametrized routes =====

@router.get("/{barber_id}", response_model=dict)
async def get_barber(
    barber_id: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener un barbero por ID.

    **Path parameters:**
    - barber_id: ID del barbero

    **Response:**
    - barber: Datos del barbero

    **Códigos de respuesta:**
    - 200: Barbero obtenido
    - 404: Barbero no encontrado
    """
    try:
        barber = await barber_service.get_barber_by_id(barber_id)
        return {
            "success": True,
            "data": {"barber": barber},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== UPDATE =====

@router.patch("/{barber_id}", response_model=dict)
async def update_barber(
    barber_id: str,
    update_data: BarberUpdate,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Actualizar datos de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Request body:**
    - Campos a actualizar (todos opcionales)

    **Response:**
    - barber: Datos actualizados

    **Códigos de respuesta:**
    - 200: Barbero actualizado
    - 404: Barbero no encontrado
    """
    try:
        barber = await barber_service.update_barber(barber_id, update_data)
        return {
            "success": True,
            "message": "Barbero actualizado",
            "data": {"barber": barber},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== SCHEDULES =====

@router.get("/{barber_id}/schedule", response_model=dict)
async def get_barber_schedule(
    barber_id: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """Obtener horario completo de un barbero."""
    try:
        schedule = await barber_service.get_barber_schedule(barber_id)
        schedule_data = [s.dict() if hasattr(s, 'dict') else s for s in (schedule or [])]
        return {"success": True, "data": {"schedule": schedule_data}}
    except Exception:
        return {"success": True, "data": {"schedule": []}}


@router.put("/{barber_id}/schedule", response_model=dict)
async def update_barber_schedule(
    barber_id: str,
    schedule_data: dict,
    current_user: User = Depends(require_admin),
):
    """Guardar horario semanal de un barbero."""
    try:
        from database.connection import MongoDBConnection
        from datetime import datetime
        db = MongoDBConnection.get_db()
        schedules_col = db["barber_schedules"]

        schedule_list = schedule_data.get("schedule", [])
        await schedules_col.delete_many({"barber_id": barber_id})

        if schedule_list:
            docs = []
            for day in schedule_list:
                docs.append({
                    "barber_id": barber_id,
                    "day_of_week": day.get("day_of_week", 0),
                    "is_working": day.get("is_working", True),
                    "start_time": day.get("start_time", "09:00"),
                    "end_time": day.get("end_time", "19:00"),
                    "updated_at": datetime.utcnow().isoformat(),
                })
            await schedules_col.insert_many(docs)

        return {"success": True, "message": "Horario actualizado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{barber_id}/schedule", response_model=dict)
async def set_working_day(
    barber_id: str,
    day_of_week: int,
    start_time: str,
    end_time: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Configurar horario de trabajo para un día específico.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - day_of_week: Día (0=lunes, 6=domingo)
    - start_time: Hora inicio (HH:MM)
    - end_time: Hora fin (HH:MM)

    **Response:**
    - schedule: Horario configurado

    **Códigos de respuesta:**
    - 200: Horario configurado
    - 400: Validación fallida
    """
    try:
        schedule = await barber_service.set_working_day(
            barber_id, day_of_week, start_time, end_time
        )
        return {
            "success": True,
            "message": "Horario configurado",
            "data": {"schedule": schedule},
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{barber_id}/special-hours", response_model=dict)
async def add_special_hour(
    barber_id: str,
    date_hour: date,
    start_time: str,
    end_time: str,
    reason: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Agregar horario especial (diferente al regular).

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - date_hour: Fecha (YYYY-MM-DD)
    - start_time: Hora inicio (HH:MM)
    - end_time: Hora fin (HH:MM)
    - reason: Razón del cambio

    **Response:**
    - special_hour: Horario especial creado

    **Códigos de respuesta:**
    - 200: Horario especial creado
    - 404: Barbero no encontrado
    """
    # TODO: Implementar
    return {
        "success": True,
        "message": "Horario especial agregado",
        "data": {"special_hour": {}},
    }


@router.get("/{barber_id}/special-hours", response_model=dict)
async def get_special_hours(
    barber_id: str,
    date_hour: Optional[date] = Query(None),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener horarios especiales de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - date_hour: Filtrar por fecha (opcional)

    **Response:**
    - special_hours: Lista de horarios especiales

    **Códigos de respuesta:**
    - 200: Lista obtenida
    - 404: Barbero no encontrado
    """
    # TODO: Implementar
    return {
        "success": True,
        "data": {
            "special_hours": [],
        },
    }


# ===== HOLIDAYS =====

@router.post("/{barber_id}/holidays", response_model=dict)
async def add_holiday(
    barber_id: str,
    start_date: date,
    end_date: date,
    reason: str,
    is_recurring: bool = Query(False),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Agregar vacaciones o feriado.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - start_date: Fecha inicio (YYYY-MM-DD)
    - end_date: Fecha fin (YYYY-MM-DD)
    - reason: Razón del feriado
    - is_recurring: Se repite cada año (default: false)

    **Response:**
    - holiday: Feriado creado

    **Códigos de respuesta:**
    - 200: Feriado creado
    - 400: Validación fallida
    """
    try:
        holiday = await barber_service.add_holiday(
            barber_id, start_date, end_date, reason, is_recurring
        )
        return {
            "success": True,
            "message": "Feriado agregado",
            "data": {"holiday": holiday},
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{barber_id}/holidays", response_model=dict)
async def get_holidays(
    barber_id: str,
    include_upcoming: bool = Query(True),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener feriados/vacaciones de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - include_upcoming: Incluir futuros (default: true)

    **Response:**
    - holidays: Lista de feriados

    **Códigos de respuesta:**
    - 200: Lista obtenida
    - 404: Barbero no encontrado
    """
    # TODO: Implementar
    return {
        "success": True,
        "data": {
            "holidays": [],
        },
    }


# ===== RATINGS & PERFORMANCE =====

@router.get("/{barber_id}/rating", response_model=dict)
async def get_barber_rating(
    barber_id: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener calificación promedio de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Response:**
    - rating: Calificación promedio (0-5)
    - review_count: Número de reseñas

    **Códigos de respuesta:**
    - 200: Rating obtenido
    - 404: Barbero no encontrado
    """
    try:
        rating = await barber_service.get_barber_rating(barber_id)
        return {
            "success": True,
            "data": {
                "rating": rating,
                "review_count": 0,  # TODO: Calcular
            },
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{barber_id}/statistics", response_model=dict)
async def get_barber_statistics(
    barber_id: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener estadísticas completas de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Response:**
    - total_appointments: Total de citas
    - completed_appointments: Citas completadas
    - avg_rating: Calificación promedio
    - total_earnings: Ganancias totales
    - client_count: Número de clientes únicos

    **Códigos de respuesta:**
    - 200: Estadísticas obtenidas
    - 404: Barbero no encontrado
    """
    try:
        stats = await barber_service.get_barber_statistics(barber_id)
        return {
            "success": True,
            "data": stats,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{barber_id}/earnings", response_model=dict)
async def get_barber_earnings(
    barber_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Obtener ganancias de un barbero en un período.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - start_date: Fecha inicio (default: hace 30 días)
    - end_date: Fecha fin (default: hoy)

    **Response:**
    - total_earnings: Ganancias totales
    - currency: Moneda

    **Códigos de respuesta:**
    - 200: Ganancias obtenidas
    - 404: Barbero no encontrado
    """
    try:
        earnings = await barber_service.get_barber_earnings(
            barber_id, start_date, end_date
        )
        return {
            "success": True,
            "data": {
                "total_earnings": str(earnings),
                "currency": "USD",
            },
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== SPECIALIZATIONS =====

@router.post("/{barber_id}/specializations", response_model=dict)
async def add_specialization(
    barber_id: str,
    specialization: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Agregar una especialización a un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - specialization: Nombre de la especialización

    **Response:**
    - barber: Barbero actualizado

    **Códigos de respuesta:**
    - 200: Especialización agregada
    - 404: Barbero no encontrado
    """
    try:
        barber = await barber_service.add_specialization(barber_id, specialization)
        return {
            "success": True,
            "message": "Especialización agregada",
            "data": {"barber": barber},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{barber_id}/specializations/{specialization}", response_model=dict)
async def remove_specialization(
    barber_id: str,
    specialization: str,
    barber_service: BarberService = Depends(get_barber_service),
):
    """
    Remover una especialización de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero
    - specialization: Nombre de la especialización

    **Response:**
    - barber: Barbero actualizado

    **Códigos de respuesta:**
    - 200: Especialización removida
    - 404: Barbero no encontrado
    """
    try:
        barber = await barber_service.remove_specialization(
            barber_id, specialization
        )
        return {
            "success": True,
            "message": "Especialización removida",
            "data": {"barber": barber},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
