"""
Appointment Routes - Gestión de citas
Endpoints: /api/appointments/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date
from typing import Optional, List

from app.models import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatus,
    User,
)
from app.services import AppointmentService
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    ConflictError,
)
from app.routes.dependencies import require_authenticated, require_client

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_appointment_service() -> AppointmentService:
    """Obtener instancia del servicio de citas."""
    from app.repositories import (
        AppointmentRepository,
        BarberRepository,
        ClientRepository,
        ServiceRepository,
        BarberScheduleRepository,
        TimeSlotRepository,
    )
    from app.routes.dependencies import get_db
    
    db = get_db()
    
    return AppointmentService(
        AppointmentRepository(db),
        BarberRepository(db),
        ClientRepository(db),
        ServiceRepository(db),
        BarberScheduleRepository(db),
        TimeSlotRepository(db),
    )


# ===== CREATE =====

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(require_client),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Crear una nueva cita.

    **Request body:**
    - barber_id: ID del barbero
    - service_id: ID del servicio
    - appointment_date: Fecha (YYYY-MM-DD, debe ser futura)
    - start_time: Hora inicio (HH:MM)
    - end_time: Hora fin (HH:MM)
    - notes: Notas adicionales (opcional)

    **Response:**
    - appointment: Datos de la cita creada
    - id: ID de la cita

    **Validaciones:**
    - Fecha futura
    - Barbero disponible
    - Servicio existe
    - No hay conflicto de horarios

    **Códigos de respuesta:**
    - 201: Cita creada
    - 400: Validación fallida
    - 409: Conflicto (barbero no disponible)
    """
    try:
        from app.repositories import ClientRepository
        from app.routes.dependencies import get_db

        db = get_db()
        client = await ClientRepository(db).find_by_user_id(str(current_user.id))
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de cliente no encontrado para el usuario autenticado",
            )

        appointment_id = await appointment_service.create_appointment(
            appointment_data, str(client.id)
        )
        return {
            "success": True,
            "message": "Cita creada exitosamente",
            "data": {
                "id": str(appointment_id),
            },
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ===== READ =====

@router.get("/{appointment_id}", response_model=dict)
async def get_appointment(
    appointment_id: str,
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Obtener una cita por ID.

    **Path parameters:**
    - appointment_id: ID de la cita

    **Response:**
    - appointment: Datos de la cita

    **Códigos de respuesta:**
    - 200: Cita obtenida
    - 404: Cita no encontrada
    """
    try:
        appointment = await appointment_service.get_appointment_by_id(appointment_id)
        return {
            "success": True,
            "data": {"appointment": appointment},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=dict)
async def list_appointments(
    current_user: User = Depends(require_authenticated),
    client_id: Optional[str] = Query(None),
    barber_id: Optional[str] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Listar citas con filtros.

    **Query parameters:**
    - client_id: Filtrar por cliente (opcional)
    - barber_id: Filtrar por barbero (opcional)
    - status: Filtrar por estado (PENDING, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW)
    - skip: Número de registros a saltar (default: 0)
    - limit: Número máximo de registros (default: 50, max: 100)

    **Response:**
    - appointments: Lista de citas
    - total: Total de registros

    **Códigos de respuesta:**
    - 200: Lista obtenida
    """
    appointments = await appointment_service.list_appointments(
        skip=skip,
        limit=limit,
        client_id=client_id,
        barber_id=barber_id,
        status=status,
    )
    
    return {
        "success": True,
        "data": {
            "appointments": appointments,
            "total": len(appointments),
            "skip": skip,
            "limit": limit,
        },
    }



# ===== UPDATE =====

@router.patch("/{appointment_id}", response_model=dict)
async def update_appointment(
    appointment_id: str,
    update_data: AppointmentUpdate,
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Actualizar una cita.

    **Path parameters:**
    - appointment_id: ID de la cita

    **Request body:**
    - Cualquier campo de Appointment (todos opcionales)

    **Response:**
    - appointment: Datos actualizados

    **Códigos de respuesta:**
    - 200: Cita actualizada
    - 404: Cita no encontrada
    - 400: Validación fallida
    """
    try:
        appointment = await appointment_service.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        updated = await appointment_service.appointment_repo.update_partial(
            appointment_id,
            update_data.dict(exclude_unset=True),
        )
        return {
            "success": True,
            "message": "Cita actualizada",
            "data": {"appointment": updated.dict() if updated else None},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== STATUS CHANGES =====

@router.post("/{appointment_id}/confirm", response_model=dict)
async def confirm_appointment(
    appointment_id: str,
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Confirmar una cita (PENDING → CONFIRMED).

    **Path parameters:**
    - appointment_id: ID de la cita

    **Response:**
    - appointment: Cita confirmada

    **Validaciones:**
    - Cita en estado PENDING

    **Códigos de respuesta:**
    - 200: Cita confirmada
    - 404: Cita no encontrada
    - 400: No puede confirmarse (estado inválido)
    """
    try:
        appointment = await appointment_service.confirm_appointment(appointment_id)
        return {
            "success": True,
            "message": "Cita confirmada",
            "data": {"appointment": appointment},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{appointment_id}/complete", response_model=dict)
async def complete_appointment(
    appointment_id: str,
    notes: Optional[str] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Marcar cita como completada (CONFIRMED → COMPLETED).

    **Path parameters:**
    - appointment_id: ID de la cita

    **Query parameters:**
    - notes: Notas de finalización (opcional)

    **Response:**
    - appointment: Cita completada

    **Códigos de respuesta:**
    - 200: Cita completada
    - 404: Cita no encontrada
    - 400: No puede completarse
    """
    try:
        appointment = await appointment_service.complete_appointment(
            appointment_id, notes
        )
        return {
            "success": True,
            "message": "Cita completada",
            "data": {"appointment": appointment},
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{appointment_id}/cancel", response_model=dict)
async def cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Cancelar una cita.

    **Path parameters:**
    - appointment_id: ID de la cita

    **Query parameters:**
    - reason: Razón de cancelación (opcional)

    **Response:**
    - appointment: Cita cancelada

    **Códigos de respuesta:**
    - 200: Cita cancelada
    - 404: Cita no encontrada
    - 400: No puede cancelarse
    """
    try:
        appointment = await appointment_service.cancel_appointment(
            appointment_id, reason
        )
        return {
            "success": True,
            "message": "Cita cancelada",
            "data": {"appointment": appointment},
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{appointment_id}/no-show", response_model=dict)
async def mark_no_show(
    appointment_id: str,
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Marcar cliente como NO_SHOW (no se presentó).

    **Path parameters:**
    - appointment_id: ID de la cita

    **Response:**
    - appointment: Cita marcada como NO_SHOW

    **Códigos de respuesta:**
    - 200: Marcada como NO_SHOW
    - 404: Cita no encontrada
    - 400: No puede marcarse como NO_SHOW
    """
    try:
        appointment = await appointment_service.mark_no_show(appointment_id)
        return {
            "success": True,
            "message": "Cita marcada como NO_SHOW",
            "data": {"appointment": appointment},
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{appointment_id}/reschedule", response_model=dict)
async def reschedule_appointment(
    appointment_id: str,
    new_date: date,
    new_start_time: str,
    new_end_time: str,
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Reprogramar una cita a nueva fecha/hora.

    **Path parameters:**
    - appointment_id: ID de la cita

    **Query parameters:**
    - new_date: Nueva fecha (YYYY-MM-DD)
    - new_start_time: Nueva hora inicio (HH:MM)
    - new_end_time: Nueva hora fin (HH:MM)

    **Response:**
    - appointment: Cita reprogramada

    **Validaciones:**
    - Nueva fecha futura
    - Barbero disponible en nuevo horario
    - Cita no completada

    **Códigos de respuesta:**
    - 200: Cita reprogramada
    - 404: Cita no encontrada
    - 409: Barbero no disponible
    """
    try:
        appointment = await appointment_service.reschedule_appointment(
            appointment_id, new_date, new_start_time, new_end_time
        )
        return {
            "success": True,
            "message": "Cita reprogramada",
            "data": {"appointment": appointment},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (ValidationError, ConflictError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== RATINGS =====

@router.post("/{appointment_id}/rate", response_model=dict)
async def rate_appointment(
    appointment_id: str,
    rating: int,
    comment: Optional[str] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Agregar calificación a una cita.

    **Path parameters:**
    - appointment_id: ID de la cita

    **Query parameters:**
    - rating: Calificación (1-5 estrellas)
    - comment: Comentario (opcional)

    **Response:**
    - appointment: Cita con calificación

    **Validaciones:**
    - Cita completada
    - Rating entre 1 y 5

    **Códigos de respuesta:**
    - 200: Calificación agregada
    - 404: Cita no encontrada
    - 400: Validación fallida
    """
    try:
        appointment = await appointment_service.add_rating(
            appointment_id, rating, comment
        )
        return {
            "success": True,
            "message": "Calificación agregada",
            "data": {"appointment": appointment},
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== CLIENT APPOINTMENTS =====

@router.get("/client/{client_id}", response_model=dict)
async def list_client_appointments(
    client_id: str,
    status: Optional[AppointmentStatus] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Listar citas de un cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Query parameters:**
    - status: Filtrar por estado (opcional)

    **Response:**
    - appointments: Lista de citas del cliente

    **Códigos de respuesta:**
    - 200: Lista obtenida
    - 404: Cliente no encontrado
    """
    appointments = await appointment_service.list_client_appointments(client_id, status)
    return {
        "success": True,
        "data": {
            "appointments": [apt.dict() if hasattr(apt, "dict") else apt for apt in appointments],
            "total": len(appointments),
        },
    }


# ===== BARBER APPOINTMENTS =====

@router.get("/barber/{barber_id}", response_model=dict)
async def list_barber_appointments(
    barber_id: str,
    date: Optional[date] = Query(None),
    status: Optional[AppointmentStatus] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service),
):
    """
    Listar citas de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - date: Filtrar por fecha (opcional)
    - status: Filtrar por estado (opcional)

    **Response:**
    - appointments: Lista de citas

    **Códigos de respuesta:**
    - 200: Lista obtenida
    - 404: Barbero no encontrado
    """
    appointments = await appointment_service.list_barber_appointments(
        barber_id=barber_id,
        appointment_date=date,
        status=status,
    )
    return {
        "success": True,
        "data": {
            "appointments": [apt.dict() if hasattr(apt, "dict") else apt for apt in appointments],
            "total": len(appointments),
        },
    }
