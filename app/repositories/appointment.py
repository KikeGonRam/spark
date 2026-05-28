"""
Appointment Repository - Data access for Appointment model.
Specific queries and operations for appointments/reservations.
"""
from typing import Optional, List
from datetime import date, datetime
from app.models.appointment import Appointment, AppointmentStatus
from app.repositories.base import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    """Appointment repository for database operations."""
    
    def __init__(self, db, collection_name: str = "appointments"):
        """Initialize appointment repository."""
        super().__init__(db, Appointment, collection_name)
    
    async def find_by_client(self, client_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Find appointments for a client."""
        return await self.find({"client_id": client_id}, skip, limit)
    
    async def find_by_barber(self, barber_id: str, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Find appointments for a barber."""
        return await self.find({"barber_id": barber_id}, skip, limit)
    
    async def find_by_date(self, date_val: date, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Find appointments on specific date."""
        return await self.find({"appointment_date": date_val}, skip, limit)
    
    async def find_by_status(self, status: AppointmentStatus, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Find appointments by status."""
        return await self.find({"status": status.value}, skip, limit)
    
    async def find_pending(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Find all pending appointments."""
        return await self.find({"status": AppointmentStatus.PENDING.value}, skip, limit)
    
    async def find_confirmed(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Find all confirmed appointments."""
        return await self.find({"status": AppointmentStatus.CONFIRMED.value}, skip, limit)
    
    async def find_completed(self, skip: int = 0, limit: int = 100) -> List[Appointment]:
        """Find all completed appointments."""
        return await self.find({"status": AppointmentStatus.COMPLETED.value}, skip, limit)
    
    async def find_upcoming(self, barber_id: str, days: int = 7) -> List[Appointment]:
        """Find upcoming appointments for barber."""
        from datetime import timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        query = {
            "barber_id": barber_id,
            "appointment_date": {
                "$gte": start_date,
                "$lte": end_date
            },
            "status": {"$in": [AppointmentStatus.CONFIRMED.value, AppointmentStatus.PENDING.value]}
        }
        return await self.find(query)
    
    async def find_by_barber_and_date(self, barber_id: str, date_val: date) -> List[Appointment]:
        """Find appointments for barber on specific date."""
        return await self.find({
            "barber_id": barber_id,
            "appointment_date": date_val
        })
    
    async def count_by_client(self, client_id: str) -> int:
        """Count appointments for client."""
        return await self.count({"client_id": client_id})
    
    async def count_by_barber(self, barber_id: str) -> int:
        """Count appointments for barber."""
        return await self.count({"barber_id": barber_id})
    
    async def count_completed_by_barber(self, barber_id: str) -> int:
        """Count completed appointments for barber."""
        return await self.count({
            "barber_id": barber_id,
            "status": AppointmentStatus.COMPLETED.value
        })
    
    async def confirm_appointment(self, appointment_id: str) -> bool:
        """Confirm pending appointment."""
        return await self.update_partial(appointment_id, {
            "status": AppointmentStatus.CONFIRMED.value
        })
    
    async def complete_appointment(self, appointment_id: str) -> bool:
        """Mark appointment as completed."""
        return await self.update_partial(appointment_id, {
            "status": AppointmentStatus.COMPLETED.value
        })
    
    async def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel appointment."""
        return await self.update_partial(appointment_id, {
            "status": AppointmentStatus.CANCELLED.value
        })
    
    async def mark_no_show(self, appointment_id: str) -> bool:
        """Mark appointment as no-show."""
        return await self.update_partial(appointment_id, {
            "status": AppointmentStatus.NO_SHOW.value
        })
    
    async def add_rating(self, appointment_id: str, rating: int, feedback: str = None) -> bool:
        """Add rating and feedback to completed appointment."""
        update_data = {"rating": rating}
        if feedback:
            update_data["feedback"] = feedback
        return await self.update_partial(appointment_id, update_data)
