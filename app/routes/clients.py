"""
Client Routes - Gestión de clientes
Endpoints: /api/clients/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from decimal import Decimal

from app.models import (
    Client,
    ClientCreate,
    ClientUpdate,
    User,
)
from app.services import ClientService
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)
from app.routes.dependencies import (
    get_client_service,
    require_client,
    require_admin,
)

router = APIRouter()


# ===== CREATE =====

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Crear un nuevo cliente.

    **Request body:**
    - email: Email único
    - first_name: Nombre
    - last_name: Apellido
    - phone: Teléfono (opcional)

    **Response:**
    - client: Datos del cliente creado
    - referral_code: Código único de referido

    **Códigos de respuesta:**
    - 201: Cliente creado
    - 400: Validación fallida
    """
    try:
        client = await client_service.create_client(client_data)
        # client_service.create_client may return either a Client object or the created ID (string)
        if isinstance(client, str):
            # fetch full client object
            client_obj = await client_service.get_client_by_id(client)
        else:
            client_obj = client

        return {
            "success": True,
            "message": "Cliente creado exitosamente",
            "data": {
                "client": client_obj,
                "referral_code": getattr(client_obj, 'referral_code', None),
            },
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== READ =====

# ===== CLIENT'S OWN DATA (Current User) - Must come before /{client_id} =====

@router.get("/appointments", response_model=list)
async def get_my_client_appointments(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_client),
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener citas del cliente autenticado.
    
    **Query parameters:**
    - status: Filtrar por estado (opcional)
    - skip: Registros a saltar
    - limit: Límite de registros
    
    **Response:**
    - Lista de citas del cliente
    """
    from app.repositories import ClientRepository
    from app.routes.dependencies import get_db

    db = get_db()
    client = await ClientRepository(db).find_by_user_id(str(current_user.id))
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de cliente no encontrado",
        )

    appointments = await client_service.list_client_appointments(str(client.id), status=status)
    return [apt.dict() if hasattr(apt, "dict") else apt for apt in appointments]


@router.get("/me", response_model=dict)
async def get_my_client(
    current_user: User = Depends(require_client),
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener el perfil del cliente autenticado.
    """
    try:
        from app.repositories import ClientRepository
        from app.routes.dependencies import get_db

        db = get_db()
        client = await ClientRepository(db).find_by_user_id(str(current_user.id))
        if not client:
            raise ResourceNotFoundError("Cliente no encontrado")

        return {
            "success": True,
            "data": {"client": client.dict()},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== READ =====
async def get_client(
    client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener un cliente por ID.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - client: Datos del cliente

    **Códigos de respuesta:**
    - 200: Cliente obtenido
    - 404: Cliente no encontrado
    """
    try:
        client = await client_service.get_client_by_id(client_id)
        return {
            "success": True,
            "data": {"client": client},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=dict)
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    client_service: ClientService = Depends(get_client_service),
):
    """
    Listar clientes.

    **Query parameters:**
    - skip: Número de registros a saltar (default: 0)
    - limit: Número máximo (default: 50, max: 100)

    **Response:**
    - clients: Lista de clientes
    - total: Total de registros

    **Códigos de respuesta:**
    - 200: Lista obtenida
    """
    # TODO: Implementar
    return {
        "success": True,
        "data": {
            "clients": [],
            "total": 0,
            "skip": skip,
            "limit": limit,
        },
    }


@router.get("/vip", response_model=dict)
async def list_vip_clients(
    current_user: User = Depends(require_admin),
    client_service: ClientService = Depends(get_client_service),
):
    """
    Listar clientes VIP.

    **Response:**
    - clients: Lista de clientes VIP

    **Códigos de respuesta:**
    - 200: Lista obtenida
    """
    # TODO: Implementar
    return {
        "success": True,
        "data": {
            "clients": [],
            "total": 0,
        },
    }


# ===== UPDATE =====

@router.patch("/{client_id}", response_model=dict)
async def update_client(
    client_id: str,
    update_data: ClientUpdate,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Actualizar datos de un cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Request body:**
    - Campos a actualizar (todos opcionales)

    **Response:**
    - client: Datos actualizados

    **Códigos de respuesta:**
    - 200: Cliente actualizado
    - 404: Cliente no encontrado
    """
    try:
        client = await client_service.update_client(client_id, update_data)
        return {
            "success": True,
            "message": "Cliente actualizado",
            "data": {"client": client},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== LOYALTY PROGRAM =====

@router.post("/{client_id}/loyalty-points", response_model=dict)
async def add_loyalty_points(
    client_id: str,
    points: int,
    reason: str = Query("Compra"),
    client_service: ClientService = Depends(get_client_service),
):
    """
    Agregar puntos de fidelización.

    **Path parameters:**
    - client_id: ID del cliente

    **Query parameters:**
    - points: Número de puntos a agregar
    - reason: Razón (default: "Compra")

    **Response:**
    - client: Cliente con puntos actualizados
    - loyalty_points: Puntos totales

    **Códigos de respuesta:**
    - 200: Puntos agregados
    - 404: Cliente no encontrado
    - 400: Validación fallida
    """
    try:
        client = await client_service.add_loyalty_points(
            client_id, points, reason
        )
        return {
            "success": True,
            "message": "Puntos agregados",
            "data": {
                "client": client,
                "loyalty_points": client.loyalty_points,
            },
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{client_id}/redeem-points", response_model=dict)
async def redeem_loyalty_points(
    client_id: str,
    points: int,
    discount_value: Decimal,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Canjear puntos por descuento.

    **Path parameters:**
    - client_id: ID del cliente

    **Query parameters:**
    - points: Puntos a canjear
    - discount_value: Valor del descuento

    **Response:**
    - client: Cliente con puntos actualizados
    - discount_value: Valor del descuento aplicado

    **Códigos de respuesta:**
    - 200: Puntos canjeados
    - 404: Cliente no encontrado
    - 400: Puntos insuficientes
    """
    try:
        client = await client_service.redeem_loyalty_points(
            client_id, points, discount_value
        )
        return {
            "success": True,
            "message": "Puntos canjeados",
            "data": {
                "client": client,
                "discount_applied": str(discount_value),
                "loyalty_points": client.loyalty_points,
            },
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== VIP STATUS =====

@router.post("/{client_id}/check-vip", response_model=dict)
async def check_vip_status(
    client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Verificar y actualizar estado VIP del cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - is_vip: Booleano indicando si es VIP
    - status_changed: Si cambió de estado
    - vip_benefits: Beneficios VIP (si aplica)

    **Códigos de respuesta:**
    - 200: Estado obtenido
    - 404: Cliente no encontrado
    """
    try:
        is_vip = await client_service.check_vip_status(client_id)
        return {
            "success": True,
            "data": {
                "is_vip": is_vip,
                "vip_benefits": [
                    "10% descuento en servicios",
                    "Prioridad en reservas",
                    "Puntos dobles en compras",
                ] if is_vip else [],
            },
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== REFERRAL PROGRAM =====

@router.get("/{client_id}/referral-code", response_model=dict)
async def get_referral_code(
    client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener código de referido único del cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - referral_code: Código único
    - referral_url: URL para compartir

    **Códigos de respuesta:**
    - 200: Código obtenido
    - 404: Cliente no encontrado
    """
    try:
        code = await client_service.get_referral_code(client_id)
        return {
            "success": True,
            "data": {
                "referral_code": code,
                "referral_url": f"https://barberpro.com/register?ref={code}",
            },
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/register-referral", response_model=dict)
async def register_referral(
    referral_code: str,
    new_client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Registrar nuevo cliente como referido.

    **Query parameters:**
    - referral_code: Código del referidor
    - new_client_id: ID del nuevo cliente

    **Response:**
    - referrer: Cliente que refirió
    - new_client: Nuevo cliente registrado
    - points_awarded: Puntos otorgados

    **Códigos de respuesta:**
    - 200: Referido registrado
    - 400: Código inválido
    - 404: Cliente no encontrado
    """
    try:
        referrer, new_client = await client_service.register_referral(
            referral_code, new_client_id
        )
        return {
            "success": True,
            "message": "Referido registrado",
            "data": {
                "referrer": referrer,
                "new_client": new_client,
                "referrer_points": 100,
                "new_client_points": 50,
            },
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{client_id}/referral-statistics", response_model=dict)
async def get_referral_statistics(
    client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener estadísticas de referidos del cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - total_referrals: Total de referidos
    - active_referrals: Referidos activos
    - points_earned: Puntos ganados por referidos

    **Códigos de respuesta:**
    - 200: Estadísticas obtenidas
    - 404: Cliente no encontrado
    """
    try:
        stats = await client_service.get_referral_statistics(client_id)
        return {
            "success": True,
            "data": stats,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== STATISTICS =====

@router.get("/{client_id}/statistics", response_model=dict)
async def get_client_statistics(
    client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener estadísticas completas de un cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - total_appointments: Total de citas
    - completed_appointments: Citas completadas
    - total_spent: Total gastado
    - average_spend: Gasto promedio
    - loyalty_points: Puntos actuales
    - is_vip: Si es VIP

    **Códigos de respuesta:**
    - 200: Estadísticas obtenidas
    - 404: Cliente no encontrado
    """
    try:
        stats = await client_service.get_client_statistics(client_id)
        return {
            "success": True,
            "data": stats,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{client_id}/appointment-history", response_model=dict)
async def get_appointment_history(
    client_id: str,
    limit: int = Query(10, ge=1, le=50),
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener historial de citas del cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Query parameters:**
    - limit: Número máximo de citas (default: 10, max: 50)

    **Response:**
    - appointments: Lista de citas recientes

    **Códigos de respuesta:**
    - 200: Historial obtenido
    - 404: Cliente no encontrado
    """
    # TODO: Implementar
    return {
        "success": True,
        "data": {
            "appointments": [],
        },
    }


@router.get("/{client_id}/spending-summary", response_model=dict)
async def get_spending_summary(
    client_id: str,
    client_service: ClientService = Depends(get_client_service),
):
    """
    Obtener resumen de gastos del cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - total_spent: Total gastado
    - monthly_average: Promedio mensual
    - highest_month: Mes con mayor gasto
    - favorite_service: Servicio más usado
    - favorite_barber: Barbero más frecuente

    **Códigos de respuesta:**
    - 200: Resumen obtenido
    - 404: Cliente no encontrado
    """
    try:
        summary = await client_service.get_client_spending_summary(client_id)
        return {
            "success": True,
            "data": summary,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
