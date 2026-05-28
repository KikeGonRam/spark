"""
BarberService - Lógica de negocio para barberos
Maneja: gestión de barberos, horarios, disponibilidad, especializaciones
Calcula ratings, ganancias, performance
"""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from app.models import (
    Barber,
    BarberCreate,
    BarberUpdate,
    BarberSchedule,
    SpecialHours,
    Holiday,
)
from app.repositories import (
    BarberRepository,
    BarberScheduleRepository,
    SpecialHourRepository,
    HolidayRepository,
    AppointmentRepository,
)
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)


class BarberService:
    """Servicio de lógica de negocio para barberos."""

    def __init__(
        self,
        barber_repo: BarberRepository,
        schedule_repo: BarberScheduleRepository,
        special_hour_repo: SpecialHourRepository,
        holiday_repo: HolidayRepository,
        appointment_repo: AppointmentRepository,
    ):
        self.barber_repo = barber_repo
        self.schedule_repo = schedule_repo
        self.special_hour_repo = special_hour_repo
        self.holiday_repo = holiday_repo
        self.appointment_repo = appointment_repo

    async def create_barber(self, barber_data: BarberCreate) -> Barber:
        """
        Crear un nuevo barbero.

        Args:
            barber_data: Datos del barbero

        Returns:
            Barber: El barbero creado

        Raises:
            ValidationError: Si los datos no son válidos
        """
        # Crear barbero (user_id ya existe, email será validado en User)
        data = barber_data.dict(exclude={'created_at', 'updated_at', 'id'})
        barber = await self.barber_repo.create(
            Barber(
                **data,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        return barber

    async def get_barber_by_id(self, barber_id: str) -> Barber:
        """Obtener un barbero por ID."""
        barber = await self.barber_repo.find_by_id(barber_id)
        if not barber:
            raise ResourceNotFoundError(f"Barbero {barber_id} no encontrado")
        return barber

    async def update_barber(self, barber_id: str, update_data: BarberUpdate) -> Barber:
        """
        Actualizar datos de un barbero.

        Args:
            barber_id: ID del barbero
            update_data: Datos a actualizar

        Returns:
            Barber: El barbero actualizado

        Raises:
            ResourceNotFoundError: Si el barbero no existe
        """
        barber = await self.barber_repo.find_by_id(barber_id)
        if not barber:
            raise ResourceNotFoundError(f"Barbero {barber_id} no encontrado")

        updated = await self.barber_repo.update(barber_id, update_data)
        return updated

    async def list_barbers(
        self,
        specialization: Optional[str] = None,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Barber]:
        """
        Listar barberos.

        Args:
            specialization: Filtrar por especialización
            available_only: Solo barberos disponibles
            skip: Número de registros a saltar
            limit: Número máximo de registros

        Returns:
            List[Barber]: Lista de barberos
        """
        if specialization:
            return await self.barber_repo.find_by_specialization(
                specialization, skip, limit
            )

        if available_only:
            return await self.barber_repo.find_available(skip, limit)

        return await self.barber_repo.find_all(skip, limit)

    async def list_top_barbers(self, limit: int = 10) -> List[Barber]:
        """Obtener barberos mejor calificados."""
        return await self.barber_repo.find_top_rated(limit)

    # ===== HORARIOS Y DISPONIBILIDAD =====

    async def set_working_day(
        self,
        barber_id: str,
        day_of_week: int,
        start_time: str,
        end_time: str,
    ) -> BarberSchedule:
        """
        Configurar el horario de trabajo de un barbero para un día específico.

        Args:
            barber_id: ID del barbero
            day_of_week: Día de la semana (0=lunes, 6=domingo)
            start_time: Hora de inicio (formato "HH:MM")
            end_time: Hora de fin (formato "HH:MM")

        Returns:
            BarberSchedule: El horario configurado

        Raises:
            ValidationError: Si los datos no son válidos
        """
        if day_of_week < 0 or day_of_week > 6:
            raise ValidationError("day_of_week debe estar entre 0 y 6")

        schedule = await self.schedule_repo.set_working_day(
            barber_id, day_of_week, start_time, end_time
        )

        return schedule

    async def get_barber_schedule(self, barber_id: str) -> List[BarberSchedule]:
        """Obtener horario completo de un barbero."""
        return await self.schedule_repo.find_by_barber(barber_id)

    async def get_barber_schedule_for_day(
        self, barber_id: str, day_of_week: int
    ) -> Optional[BarberSchedule]:
        """Obtener horario de un barbero para un día específico."""
        return await self.schedule_repo.find_by_barber_and_day(barber_id, day_of_week)

    async def add_special_hour(
        self,
        barber_id: str,
        date_hour: date,
        start_time: str,
        end_time: str,
        reason: str,
    ) -> SpecialHours:
        """
        Agregar un horario especial (diferente al regular).

        Ejemplos: cierre especial, horario extendido, etc.

        Args:
            barber_id: ID del barbero
            date_hour: Fecha
            start_time: Hora de inicio
            end_time: Hora de fin
            reason: Razón del cambio

        Returns:
            SpecialHours: El horario especial creado
        """
        special_hour = await self.special_hour_repo.create(
            SpecialHours(
                barber_id=barber_id,
                date=date_hour,
                start_time=start_time,
                end_time=end_time,
                reason=reason,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        return special_hour

    async def get_special_hours_for_date(
        self, barber_id: str, date_hour: date
    ) -> List[SpecialHours]:
        """Obtener horarios especiales para una fecha."""
        return await self.special_hour_repo.find_by_barber_and_date(
            barber_id, date_hour
        )

    async def add_holiday(
        self,
        barber_id: str,
        start_date: date,
        end_date: date,
        reason: str,
        is_recurring: bool = False,
    ) -> Holiday:
        """
        Agregar un día/período de vacaciones o feriado.

        Args:
            barber_id: ID del barbero
            start_date: Fecha de inicio
            end_date: Fecha de fin
            reason: Razón del feriado
            is_recurring: Si se repite cada año

        Returns:
            Holiday: El feriado creado
        """
        if end_date < start_date:
            raise ValidationError("end_date no puede ser anterior a start_date")

        holiday = await self.holiday_repo.create(
            Holiday(
                barber_id=barber_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                is_recurring=is_recurring,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        return holiday

    async def get_holidays(
        self, barber_id: str, include_upcoming: bool = True
    ) -> List[Holiday]:
        """Obtener feriados/vacaciones de un barbero."""
        if include_upcoming:
            return await self.holiday_repo.find_upcoming(barber_id)
        return await self.holiday_repo.find_for_barber(barber_id)

    # ===== RATINGS Y PERFORMANCE =====

    async def get_barber_rating(self, barber_id: str) -> float:
        """
        Obtener calificación promedio de un barbero.

        Returns:
            float: Rating promedio (0-5)
        """
        barber = await self.barber_repo.find_by_id(barber_id)
        if not barber:
            raise ResourceNotFoundError(f"Barbero {barber_id} no encontrado")

        # TODO: Calcular desde citas completadas con rating
        return barber.average_rating or 0.0

    async def get_barber_earnings(
        self, barber_id: str, start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Decimal:
        """
        Obtener ganancias de un barbero en un período.

        Args:
            barber_id: ID del barbero
            start_date: Fecha de inicio (default: hace 30 días)
            end_date: Fecha de fin (default: hoy)

        Returns:
            Decimal: Total de ganancias
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # TODO: Calcular desde pagos completados de citas del barbero
        return Decimal("0.00")

    async def get_barber_statistics(self, barber_id: str) -> dict:
        """
        Obtener estadísticas completas de un barbero.

        Returns:
            dict: Contiene:
            - total_appointments: Total de citas
            - completed_appointments: Citas completadas
            - avg_rating: Calificación promedio
            - total_earnings: Ganancias totales
            - client_count: Número de clientes únicos
        """
        barber = await self.barber_repo.find_by_id(barber_id)
        if not barber:
            raise ResourceNotFoundError(f"Barbero {barber_id} no encontrado")

        # TODO: Implementar estadísticas completas
        return {
            "total_appointments": 0,
            "completed_appointments": 0,
            "avg_rating": barber.average_rating or 0.0,
            "total_earnings": "0.00",
            "client_count": 0,
        }

    # ===== ESPECIALIZACIONES =====

    async def add_specialization(
        self, barber_id: str, specialization: str
    ) -> Barber:
        """
        Agregar una especialización a un barbero.

        Args:
            barber_id: ID del barbero
            specialization: Nombre de la especialización

        Returns:
            Barber: El barbero actualizado
        """
        barber = await self.barber_repo.find_by_id(barber_id)
        if not barber:
            raise ResourceNotFoundError(f"Barbero {barber_id} no encontrado")

        if not barber.specializations:
            barber.specializations = []

        if specialization not in barber.specializations:
            barber.specializations.append(specialization)
            await self.barber_repo.update(barber_id, BarberUpdate(
                specializations=barber.specializations
            ))

        return barber

    async def remove_specialization(
        self, barber_id: str, specialization: str
    ) -> Barber:
        """
        Remover una especialización de un barbero.

        Args:
            barber_id: ID del barbero
            specialization: Nombre de la especialización

        Returns:
            Barber: El barbero actualizado
        """
        barber = await self.barber_repo.find_by_id(barber_id)
        if not barber:
            raise ResourceNotFoundError(f"Barbero {barber_id} no encontrado")

        if barber.specializations and specialization in barber.specializations:
            barber.specializations.remove(specialization)
            await self.barber_repo.update(barber_id, BarberUpdate(
                specializations=barber.specializations
            ))

        return barber

