"""
Service Routes - Gestión de servicios de barbería
Endpoints: /api/services/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List

from app.models import (
    Service,
    ServiceCreate,
    ServiceUpdate,
)
from app.services import ServiceService
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_service_service() -> ServiceService:
    """Obtener instancia del servicio de servicios."""
    from app.repositories import ServiceRepository
    from app.routes.dependencies import get_db
    
    db = get_db()
    
    return ServiceService(ServiceRepository(db))


# ===== CREATE =====

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    service_service: ServiceService = Depends(get_service_service),
):
    """
    Crear un nuevo servicio de barbería.

    **Request body:**
    - name: Nombre del servicio
    - description: Descripción
    - price: Precio
    - duration_minutes: Duración en minutos
    - category: Categoría

    **Response:**
    - service: Datos del servicio creado

    **Códigos de respuesta:**
    - 201: Servicio creado
    - 400: Validación fallida
    """
    try:
        service_id = await service_service.create_service(service_data)
        service = await service_service.get_service_by_id(service_id)
        return {
            "success": True,
            "message": "Servicio creado exitosamente",
            "data": {"service": service.dict()},
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== READ =====

@router.get("/{service_id}", response_model=dict)
async def get_service(
    service_id: str,
    service_service: ServiceService = Depends(get_service_service),
):
    """
    Obtener detalles de un servicio específico.

    **Path parameters:**
    - service_id: ID del servicio

    **Response:**
    - service: Detalles del servicio

    **Códigos de respuesta:**
    - 200: Éxito
    - 404: Servicio no encontrado
    """
    try:
        service = await service_service.get_service_by_id(service_id)
        return {"success": True, "data": {"service": service.dict()}}
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")


@router.get("", response_model=dict)
async def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service_service: ServiceService = Depends(get_service_service),
):
    """
    Obtener lista de servicios con paginación.

    **Query parameters:**
    - skip: Número de registros a saltar (default: 0)
    - limit: Máximo de registros por página (default: 50, max: 100)

    **Response:**
    - services: Lista de servicios
    - total: Total de servicios
    - skip: Registros saltados
    - limit: Límite aplicado
    """
    try:
        services = await service_service.list_services(skip=skip, limit=limit)
        total = await service_service.count_services()
        return {
            "success": True,
            "data": {
                "services": [s.dict() for s in services],
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ===== UPDATE =====

@router.put("/{service_id}", response_model=dict)
async def update_service(
    service_id: str,
    service_data: ServiceUpdate,
    service_service: ServiceService = Depends(get_service_service),
):
    """
    Actualizar un servicio existente.

    **Path parameters:**
    - service_id: ID del servicio

    **Request body:**
    - name: Nuevo nombre (opcional)
    - description: Nueva descripción (opcional)
    - price: Nuevo precio (opcional)
    - duration_minutes: Nueva duración (opcional)
    - category: Nueva categoría (opcional)

    **Response:**
    - service: Servicio actualizado

    **Códigos de respuesta:**
    - 200: Éxito
    - 404: Servicio no encontrado
    """
    try:
        service = await service_service.update_service(service_id, service_data)
        return {
            "success": True,
            "message": "Servicio actualizado exitosamente",
            "data": {"service": service.dict()},
        }
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== DELETE =====

@router.delete("/{service_id}", response_model=dict)
async def delete_service(
    service_id: str,
    service_service: ServiceService = Depends(get_service_service),
):
    """
    Eliminar un servicio.

    **Path parameters:**
    - service_id: ID del servicio

    **Response:**
    - message: Mensaje de confirmación

    **Códigos de respuesta:**
    - 200: Éxito
    - 404: Servicio no encontrado
    """
    try:
        await service_service.delete_service(service_id)
        return {
            "success": True,
            "message": "Servicio eliminado exitosamente",
        }
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servicio no encontrado")
