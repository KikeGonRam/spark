"""
ServiceService - Lógica de negocio para servicios de barbería
Maneja: gestión de servicios, precios, duración, categorías
"""

from datetime import datetime
from typing import Optional, List

from app.models import (
    Service,
    ServiceCreate,
    ServiceUpdate,
)
from app.models.service import ServiceCategory
from app.repositories import ServiceRepository
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)


class ServiceService:
    """Servicio de lógica de negocio para servicios."""

    def __init__(self, service_repo: ServiceRepository):
        self.service_repo = service_repo

    async def create_service(self, service_data: ServiceCreate) -> str:
        """
        Crear un nuevo servicio.

        Args:
            service_data: Datos del servicio

        Returns:
            str: ID del servicio creado

        Raises:
            ValidationError: Si los datos no son válidos
        """
        # Validar nombre único
        exists = await self.service_repo.find_by_name(service_data.name)
        if exists:
            raise ValidationError(f"El servicio {service_data.name} ya existe")

        # Crear servicio
        service_dict = service_data.dict()
        # Ensure category is ServiceCategory enum
        if isinstance(service_dict.get('category'), str):
            service_dict['category'] = ServiceCategory(service_dict['category'])
        service_id = await self.service_repo.create(
            Service(**service_dict)
        )

        return service_id

    async def get_service_by_id(self, service_id: str) -> Service:
        """Obtener un servicio por ID."""
        service = await self.service_repo.find_by_id(service_id)
        if not service:
            raise ResourceNotFoundError(f"Servicio {service_id} no encontrado")
        return service

    async def list_services(self, skip: int = 0, limit: int = 50) -> List[Service]:
        """
        Obtener lista de servicios con paginación.

        Args:
            skip: Número de registros a saltar
            limit: Máximo de registros a retornar

        Returns:
            List[Service]: Lista de servicios
        """
        services = await self.service_repo.find_all(skip=skip, limit=limit)
        return services

    async def count_services(self) -> int:
        """Obtener el total de servicios."""
        return await self.service_repo.count()

    async def update_service(self, service_id: str, service_data: ServiceUpdate) -> Service:
        """
        Actualizar un servicio existente.

        Args:
            service_id: ID del servicio
            service_data: Nuevos datos

        Returns:
            Service: Servicio actualizado

        Raises:
            ResourceNotFoundError: Si el servicio no existe
        """
        # Verificar que existe
        service = await self.get_service_by_id(service_id)

        # Actualizar
        update_data = service_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        await self.service_repo.update(service_id, update_data)

        # Retornar actualizado
        return await self.get_service_by_id(service_id)

    async def delete_service(self, service_id: str) -> bool:
        """
        Eliminar un servicio.

        Args:
            service_id: ID del servicio

        Returns:
            bool: True si se eliminó

        Raises:
            ResourceNotFoundError: Si el servicio no existe
        """
        # Verificar que existe
        await self.get_service_by_id(service_id)

        # Eliminar
        return await self.service_repo.delete(service_id)

    async def get_services_by_category(self, category: str) -> List[Service]:
        """Obtener servicios por categoría."""
        return await self.service_repo.find_by_category(category)
