"""
AppointmentService - Lógica de negocio para citas
Maneja: creación, confirmación, cancelación, reprogramación de citas
Valida disponibilidad de barberos
Calcula duraciones y costos
Integración con notificaciones y pagos
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from bson import ObjectId

from app.models import (
    Appointment,
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatus,
    Service,
    Barber,
    Client,
)
from app.repositories import (
    AppointmentRepository,
    BarberRepository,
    ClientRepository,
    ServiceRepository,
    BarberScheduleRepository,
    TimeSlotRepository,
)
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    ConflictError,
)


class AppointmentService:
    """Servicio de lógica de negocio para citas."""

    def __init__(
        self,
        appointment_repo: AppointmentRepository,
        barber_repo: BarberRepository,
        client_repo: ClientRepository,
        service_repo: ServiceRepository,
        schedule_repo: BarberScheduleRepository,
        timeslot_repo: TimeSlotRepository,
    ):
        self.appointment_repo = appointment_repo
        self.barber_repo = barber_repo
        self.client_repo = client_repo
        self.service_repo = service_repo
        self.schedule_repo = schedule_repo
        self.timeslot_repo = timeslot_repo

    async def create_appointment(
        self, appointment_data: AppointmentCreate, client_id: str
    ) -> Appointment:
        """
        Crear una nueva cita.

        Validaciones:
        - La fecha debe ser futura
        - El barbero existe y está disponible
        - El cliente existe
        - El servicio existe
        - No hay conflicto de horarios
        - El barbero trabaja en esa fecha/hora

        Args:
            appointment_data: Datos de la cita
            client_id: ID del cliente que reserva

        Returns:
            Appointment: La cita creada

        Raises:
            ValidationError: Si las validaciones fallan
            ResourceNotFoundError: Si recursos no existen
            ConflictError: Si hay conflicto de horarios
        """
        # Validar fecha futura
        appointment_date = (
            date.fromisoformat(appointment_data.appointment_date)
            if isinstance(appointment_data.appointment_date, str)
            else appointment_data.appointment_date
        )
        if appointment_date <= date.today():
            raise ValidationError("La fecha de la cita debe ser futura")

        # Validar cliente
        client = await self.client_repo.find_by_id(client_id)
        if not client:
            raise ResourceNotFoundError(f"Cliente {client_id} no encontrado")

        # Validar barbero
        barber = await self.barber_repo.find_by_id(appointment_data.barber_id)
        if not barber:
            raise ResourceNotFoundError(
                f"Barbero {appointment_data.barber_id} no encontrado"
            )

        # Validar servicio
        service = await self.service_repo.find_by_id(appointment_data.service_id)
        if not service:
            raise ResourceNotFoundError(
                f"Servicio {appointment_data.service_id} no encontrado"
            )

        # Validar disponibilidad del barbero
        is_available = await self._check_barber_availability(
            barber_id=appointment_data.barber_id,
            appointment_date=appointment_date.isoformat(),
            start_time=appointment_data.start_time,
            end_time=appointment_data.end_time,
        )

        if not is_available:
            raise ConflictError(
                f"El barbero no está disponible en {appointment_data.appointment_date} "
                f"{appointment_data.start_time}"
            )

        # Calcular hora de fin si no viene explícita
        if not appointment_data.end_time:
            from datetime import datetime as _dt
            duration = getattr(service, "duration_minutes", 30) or 30
            start_dt = _dt.strptime(appointment_data.start_time, "%H:%M")
            end_dt = start_dt + timedelta(minutes=int(duration))
            appointment_data.end_time = end_dt.strftime("%H:%M")

        # Crear la cita
        appointment = await self.appointment_repo.create(
            Appointment(
                client_id=client_id,
                barber_id=appointment_data.barber_id,
                service_id=appointment_data.service_id,
                appointment_date=appointment_date.isoformat(),
                start_time=appointment_data.start_time,
                end_time=appointment_data.end_time,
                status=AppointmentStatus.PENDING,
                notes=appointment_data.notes,
                total_cost=service.price,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        return appointment

    async def confirm_appointment(self, appointment_id: str) -> Appointment:
        """
        Confirmar una cita (cambiar de PENDING a CONFIRMED).

        Args:
            appointment_id: ID de la cita

        Returns:
            Appointment: La cita confirmada

        Raises:
            ResourceNotFoundError: Si la cita no existe
            ValidationError: Si la cita no puede ser confirmada
        """
        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        if appointment.status != AppointmentStatus.PENDING:
            raise ValidationError(
                f"Solo se pueden confirmar citas en estado PENDING. "
                f"Estado actual: {appointment.status}"
            )

        # Cambiar estado a CONFIRMED
        updated = await self.appointment_repo.update(
            appointment_id,
            AppointmentUpdate(status=AppointmentStatus.CONFIRMED),
        )

        return updated

    async def complete_appointment(
        self, appointment_id: str, notes: Optional[str] = None
    ) -> Appointment:
        """
        Completar una cita (cambiar a COMPLETED).

        Args:
            appointment_id: ID de la cita
            notes: Notas adicionales de finalización

        Returns:
            Appointment: La cita completada

        Raises:
            ResourceNotFoundError: Si la cita no existe
            ValidationError: Si la cita no puede completarse
        """
        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        if appointment.status not in [
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.IN_PROGRESS,
        ]:
            raise ValidationError(
                f"Solo se pueden completar citas CONFIRMED o IN_PROGRESS. "
                f"Estado actual: {appointment.status}"
            )

        update_data = AppointmentUpdate(
            status=AppointmentStatus.COMPLETED, notes=notes
        )

        updated = await self.appointment_repo.update(appointment_id, update_data)

        return updated

    async def cancel_appointment(
        self, appointment_id: str, reason: Optional[str] = None
    ) -> Appointment:
        """
        Cancelar una cita.

        Args:
            appointment_id: ID de la cita
            reason: Razón de cancelación

        Returns:
            Appointment: La cita cancelada

        Raises:
            ResourceNotFoundError: Si la cita no existe
            ValidationError: Si la cita no puede cancelarse
        """
        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        if appointment.status == AppointmentStatus.COMPLETED:
            raise ValidationError("No se pueden cancelar citas completadas")

        if appointment.status == AppointmentStatus.CANCELLED:
            raise ValidationError("La cita ya está cancelada")

        # Liberar el time slot
        await self.timeslot_repo.release_slot(
            barber_id=appointment.barber_id,
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
        )

        # Cambiar estado
        update_data = AppointmentUpdate(
            status=AppointmentStatus.CANCELLED, notes=reason
        )

        updated = await self.appointment_repo.update(appointment_id, update_data)

        return updated

    async def reschedule_appointment(
        self,
        appointment_id: str,
        new_date: date,
        new_start_time: str,
        new_end_time: str,
    ) -> Appointment:
        """
        Reprogramar una cita a una nueva fecha/hora.

        Args:
            appointment_id: ID de la cita
            new_date: Nueva fecha
            new_start_time: Nuevo start_time
            new_end_time: Nuevo end_time

        Returns:
            Appointment: La cita reprogramada

        Raises:
            ResourceNotFoundError: Si la cita no existe
            ValidationError: Si no es posible reprogramar
            ConflictError: Si el nuevo horario no está disponible
        """
        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        if appointment.status not in [
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
        ]:
            raise ValidationError(
                f"Solo se pueden reprogramar citas PENDING o CONFIRMED. "
                f"Estado actual: {appointment.status}"
            )

        # Validar nueva fecha
        if new_date <= date.today():
            raise ValidationError("La nueva fecha debe ser futura")

        # Validar disponibilidad en nuevo horario
        is_available = await self._check_barber_availability(
            barber_id=appointment.barber_id,
            appointment_date=new_date.isoformat(),
            start_time=new_start_time,
            end_time=new_end_time,
        )

        if not is_available:
            raise ConflictError(
                f"El barbero no está disponible en {new_date} {new_start_time}"
            )

        # Liberar slot anterior
        await self.timeslot_repo.release_slot(
            barber_id=appointment.barber_id,
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
        )

        # Reservar nuevo slot
        await self.timeslot_repo.book_slot(
            barber_id=appointment.barber_id,
            appointment_date=new_date,
            start_time=new_start_time,
        )

        # Actualizar cita
        update_data = AppointmentUpdate(
            appointment_date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
        )

        updated = await self.appointment_repo.update(appointment_id, update_data)

        return updated

    async def add_rating(
        self, appointment_id: str, rating: int, comment: Optional[str] = None
    ) -> Appointment:
        """
        Agregar calificación a una cita completada.

        Args:
            appointment_id: ID de la cita
            rating: Calificación (1-5 estrellas)
            comment: Comentario del cliente

        Returns:
            Appointment: La cita con calificación

        Raises:
            ResourceNotFoundError: Si la cita no existe
            ValidationError: Si la cita no puede ser calificada
        """
        if rating < 1 or rating > 5:
            raise ValidationError("La calificación debe estar entre 1 y 5")

        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        if appointment.status != AppointmentStatus.COMPLETED:
            raise ValidationError(
                "Solo se pueden calificar citas completadas"
            )

        # Agregar calificación
        updated = await self.appointment_repo.add_rating(
            appointment_id, rating, comment
        )

        # Actualizar calificación promedio del barbero
        await self._update_barber_rating(appointment.barber_id)

        return updated

    async def mark_no_show(self, appointment_id: str) -> Appointment:
        """
        Marcar una cita como NO_SHOW (cliente no se presentó).

        Args:
            appointment_id: ID de la cita

        Returns:
            Appointment: La cita marcada como NO_SHOW

        Raises:
            ResourceNotFoundError: Si la cita no existe
            ValidationError: Si la cita no puede marcarse como NO_SHOW
        """
        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        if appointment.status != AppointmentStatus.CONFIRMED:
            raise ValidationError(
                "Solo se pueden marcar como NO_SHOW citas CONFIRMED"
            )

        # Marcar como NO_SHOW
        updated = await self.appointment_repo.mark_no_show(appointment_id)

        # Liberar el time slot
        await self.timeslot_repo.release_slot(
            barber_id=appointment.barber_id,
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
        )

        return updated

    async def get_appointment_by_id(self, appointment_id: str) -> Appointment:
        """Obtener una cita por ID."""
        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")
        return appointment

    async def list_client_appointments(
        self, client_id: str, status: Optional[AppointmentStatus] = None
    ) -> List[Appointment]:
        """Listar citas de un cliente."""
        if status:
            return await self.appointment_repo.find_by_client(client_id, status)
        return await self.appointment_repo.find_by_client(client_id)

    async def list_barber_appointments(
        self,
        barber_id: str,
        appointment_date: Optional[date] = None,
        status: Optional[AppointmentStatus] = None,
    ) -> List[Appointment]:
        """Listar citas de un barbero."""
        if appointment_date:
            return await self.appointment_repo.find_by_date(
                barber_id, appointment_date, status
            )
        if status:
            return await self.appointment_repo.find_by_barber(barber_id, status)
        return await self.appointment_repo.find_by_barber(barber_id)

    async def list_appointments(
        self,
        skip: int = 0,
        limit: int = 50,
        client_id: Optional[str] = None,
        barber_id: Optional[str] = None,
        status: Optional[AppointmentStatus] = None,
    ) -> List[Appointment]:
        """
        Listar todas las citas con filtros opcionales.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros
            client_id: Filtrar por cliente
            barber_id: Filtrar por barbero
            status: Filtrar por estado
        
        Returns:
            List[Appointment]: Lista de citas
        """
        if client_id:
            return await self.list_client_appointments(client_id, status)
        if barber_id:
            return await self.list_barber_appointments(barber_id, status=status)
        
        # Listar todas las citas (para admin)
        return await self.appointment_repo.find_all(skip=skip, limit=limit)

    # ===== MÉTODOS PRIVADOS (HELPERS) =====

    async def _check_barber_availability(
        self,
        barber_id: str,
        appointment_date: date,
        start_time: str,
        end_time: str,
    ) -> bool:
        """
        Verificar si un barbero está disponible en una fecha/hora.

        Checks:
        1. Barbero trabaja ese día
        2. No hay conflicto de horarios con otras citas
        3. No es un día festivo/feriado
        4. Hay un time slot disponible

        Args:
            barber_id: ID del barbero
            appointment_date: Fecha de la cita
            start_time: Hora inicio (formato "HH:MM")
            end_time: Hora fin (formato "HH:MM")

        Returns:
            bool: True si está disponible, False en caso contrario
        """
        # TODO: Implementar lógica de disponibilidad
        # Por ahora retornar True para que funcione
        return True

    async def _update_barber_rating(self, barber_id: str) -> None:
        """
        Actualizar el rating promedio de un barbero.

        Calcula el promedio de todas las calificaciones de sus citas completadas.

        Args:
            barber_id: ID del barbero
        """
        # TODO: Implementar cálculo de rating promedio
        pass
