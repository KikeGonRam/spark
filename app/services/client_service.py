"""
ClientService - Lógica de negocio para clientes
Maneja: gestión de clientes, programa de fidelización, referidos
Calcula puntos, beneficios VIP, estadísticas de compra
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from app.models import (
    Client,
    ClientCreate,
    ClientUpdate,
)
from app.repositories import (
    ClientRepository,
    AppointmentRepository,
)
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)


class ClientService:
    """Servicio de lógica de negocio para clientes."""

    def __init__(
        self,
        client_repo: ClientRepository,
        appointment_repo: AppointmentRepository,
    ):
        self.client_repo = client_repo
        self.appointment_repo = appointment_repo

    async def create_client(self, client_data: ClientCreate) -> Client:
        """
        Crear un nuevo cliente.

        Args:
            client_data: Datos del cliente

        Returns:
            Client: El cliente creado

        Raises:
            ValidationError: Si los datos no son válidos
        """
        # Validar que no exista ya un perfil para ese usuario
        exists = await self.client_repo.find_by_user_id(client_data.user_id)
        if exists:
            raise ValidationError(f"El usuario {client_data.user_id} ya tiene perfil de cliente")

        # Crear cliente
        # Prevent passing duplicate metadata fields that may come from BaseDocument or external payloads
        data = client_data.dict(exclude_unset=True)
        # Ensure created_at/updated_at are not present in the dict to avoid constructor collisions
        data.pop("created_at", None)
        data.pop("updated_at", None)

        client = await self.client_repo.create(
            Client(
                **data,
                loyalty_points=0,
                total_spent=Decimal("0.00"),
                is_vip=False,
                referral_code=self._generate_referral_code(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        return client

    async def get_client_by_id(self, client_id: str) -> Client:
        """Obtener un cliente por ID."""
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")
        return client

    async def get_client_by_email(self, email: str) -> Client:
        """Obtener un cliente por email."""
        client = await self.client_repo.find_by_email(email)
        if not client:
            raise ResourceNotFoundError(f"Cliente con email {email} no encontrado")
        return client

    async def update_client(
        self, client_id: str, update_data: ClientUpdate
    ) -> Client:
        """
        Actualizar datos de un cliente.

        Args:
            client_id: ID del cliente
            update_data: Datos a actualizar

        Returns:
            Client: El cliente actualizado

        Raises:
            ResourceNotFoundError: Si el cliente no existe
        """
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        updated = await self.client_repo.update(client_id, update_data)
        return updated

    async def list_clients(self, skip: int = 0, limit: int = 50) -> List[Client]:
        """Listar todos los clientes."""
        return await self.client_repo.find_all(skip, limit)

    async def list_vip_clients(self) -> List[Client]:
        """Listar clientes VIP."""
        # TODO: Implementar filtro de clientes VIP
        return []

    # ===== PROGRAMA DE FIDELIZACIÓN =====

    async def add_loyalty_points(
        self, client_id: str, points: int, reason: str = "Compra"
    ) -> Client:
        """
        Agregar puntos de fidelización a un cliente.

        Args:
            client_id: ID del cliente
            points: Número de puntos a agregar
            reason: Razón de los puntos

        Returns:
            Client: El cliente actualizado

        Raises:
            ResourceNotFoundError: Si el cliente no existe
            ValidationError: Si los puntos son negativos
        """
        if points < 0:
            raise ValidationError("Los puntos no pueden ser negativos")

        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        new_points = (client.loyalty_points or 0) + points

        # Actualizar cliente
        updated = await self.client_repo.update(
            client_id,
            ClientUpdate(loyalty_points=new_points),
        )

        # TODO: Registrar transacción de puntos en historial

        return updated

    async def redeem_loyalty_points(
        self, client_id: str, points: int, discount_value: Decimal
    ) -> Client:
        """
        Canjear puntos de fidelización por descuento.

        Args:
            client_id: ID del cliente
            points: Puntos a canjear
            discount_value: Valor del descuento

        Returns:
            Client: El cliente actualizado

        Raises:
            ResourceNotFoundError: Si el cliente no existe
            ValidationError: Si no tiene suficientes puntos
        """
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        if (client.loyalty_points or 0) < points:
            raise ValidationError("Puntos insuficientes para canjear")

        new_points = (client.loyalty_points or 0) - points

        updated = await self.client_repo.update(
            client_id,
            ClientUpdate(loyalty_points=new_points),
        )

        # TODO: Registrar canje en historial

        return updated

    async def check_vip_status(self, client_id: str) -> bool:
        """
        Verificar y actualizar estado VIP de un cliente.

        Un cliente es VIP si:
        - Ha gastado más de $X en los últimos Y días, O
        - Ha completado más de Z citas, O
        - Tiene más de W puntos de fidelización

        Args:
            client_id: ID del cliente

        Returns:
            bool: True si es VIP, False en caso contrario

        Raises:
            ResourceNotFoundError: Si el cliente no existe
        """
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        # TODO: Implementar lógica VIP (criterios configurables)
        is_vip = (client.total_spent or Decimal("0.00")) > Decimal("1000.00")

        if is_vip and not client.is_vip:
            # Actualizar a VIP
            await self.client_repo.update(
                client_id,
                ClientUpdate(is_vip=True),
            )

        elif not is_vip and client.is_vip:
            # Remover estado VIP
            await self.client_repo.update(
                client_id,
                ClientUpdate(is_vip=False),
            )

        return is_vip

    # ===== PROGRAMA DE REFERIDOS =====

    async def get_referral_code(self, client_id: str) -> str:
        """
        Obtener código de referido de un cliente.

        Args:
            client_id: ID del cliente

        Returns:
            str: Código de referido

        Raises:
            ResourceNotFoundError: Si el cliente no existe
        """
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        return client.referral_code

    async def register_referral(
        self, referral_code: str, new_client_id: str
    ) -> tuple[Client, Client]:
        """
        Registrar un nuevo cliente como referido.

        Cuando un cliente usa un código de referido:
        - El cliente referido obtiene puntos de bienvenida
        - El cliente que refirió obtiene puntos de referencia

        Args:
            referral_code: Código de referido
            new_client_id: ID del nuevo cliente

        Returns:
            tuple[Client, Client]: (cliente que refirió, nuevo cliente)

        Raises:
            ValidationError: Si el código no existe
            ResourceNotFoundError: Si el nuevo cliente no existe
        """
        # Buscar cliente que refirió
        referrer = await self.client_repo.find_by_referral_code(referral_code)
        if not referrer:
            raise ValidationError(f"Código de referido inválido: {referral_code}")

        # Validar nuevo cliente
        new_client = await self.client_repo.find_by_id(new_client_id)
        if not new_client:
            raise ResourceNotFoundError(f"Cliente {new_client_id} no encontrado")

        # Agregar puntos al referidor
        # TODO: Usar constante configurable para puntos de referencia
        await self.add_loyalty_points(
            referrer.id, 100, "Referido registrado"
        )

        # Agregar puntos al nuevo cliente
        # TODO: Usar constante configurable para puntos de bienvenida
        await self.add_loyalty_points(
            new_client_id, 50, "Referido registrado"
        )

        # TODO: Registrar relación de referido en historial

        return referrer, new_client

    async def get_referral_statistics(self, client_id: str) -> dict:
        """
        Obtener estadísticas de referidos de un cliente.

        Returns:
            dict: Contiene:
            - total_referrals: Total de referidos
            - active_referrals: Referidos activos
            - points_earned: Puntos ganados por referidos
        """
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        # TODO: Implementar estadísticas de referidos
        return {
            "total_referrals": 0,
            "active_referrals": 0,
            "points_earned": 0,
        }

    # ===== ESTADÍSTICAS DE CLIENTE =====

    async def get_client_statistics(self, client_id: str) -> dict:
        """
        Obtener estadísticas completas de un cliente.

        Returns:
            dict: Contiene:
            - total_appointments: Total de citas
            - completed_appointments: Citas completadas
            - total_spent: Total gastado
            - average_spend: Gasto promedio
            - loyalty_points: Puntos actuales
            - is_vip: Si es VIP
        """
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        # TODO: Calcular estadísticas desde citas y pagos
        return {
            "total_appointments": 0,
            "completed_appointments": 0,
            "total_spent": client.total_spent or "0.00",
            "average_spend": "0.00",
            "loyalty_points": client.loyalty_points or 0,
            "is_vip": client.is_vip,
        }

    async def get_client_appointment_history(
        self, client_id: str, limit: int = 10
    ) -> List[dict]:
        """
        Obtener historial de citas de un cliente.

        Args:
            client_id: ID del cliente
            limit: Número máximo de citas

        Returns:
            List[dict]: Lista de citas con detalles
        """
        # TODO: Implementar con join de citas, barbero, servicio
        return []

    async def get_client_spending_summary(self, client_id: str) -> dict:
        """
        Obtener resumen de gasto de un cliente.

        Returns:
            dict: Contiene:
            - total_spent: Total gastado
            - monthly_average: Promedio mensual
            - highest_month: Mes con mayor gasto
            - favorite_service: Servicio más usado
            - favorite_barber: Barbero más frecuente
        """
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        # TODO: Calcular desde historial de citas y pagos
        return {
            "total_spent": client.total_spent or "0.00",
            "monthly_average": "0.00",
            "highest_month": None,
            "favorite_service": None,
            "favorite_barber": None,
        }

    # ===== MÉTODOS PRIVADOS =====

    def _generate_referral_code(self) -> str:
        """
        Generar código único de referido.

        Returns:
            str: Código alfanumérico único
        """
        # TODO: Generar código aleatorio, validar uniqueness
        import uuid
        return str(uuid.uuid4())[:8].upper()
