"""
Schedule Repository - Data access for Schedule models.
Specific queries and operations for barber schedules.
"""
from typing import Optional, List
from datetime import date
from app.models.schedule import BarberSchedule, SpecialHours, Holiday, TimeSlot
from app.repositories.base import BaseRepository


class BarberScheduleRepository(BaseRepository[BarberSchedule]):
    """Barber schedule repository for database operations."""
    
    def __init__(self, db, collection_name: str = "barber_schedules"):
        """Initialize schedule repository."""
        super().__init__(db, BarberSchedule, collection_name)
    
    async def find_by_barber(self, barber_id: str) -> List[BarberSchedule]:
        """Find all schedules for barber."""
        return await self.find({"barber_id": barber_id})
    
    async def find_by_barber_and_day(self, barber_id: str, day_of_week: int) -> Optional[BarberSchedule]:
        """Find schedule for barber on specific day."""
        return await self.find_one({
            "barber_id": barber_id,
            "day_of_week": day_of_week
        })
    
    async def find_working_days(self, barber_id: str) -> List[BarberSchedule]:
        """Find all working days for barber."""
        return await self.find({
            "barber_id": barber_id,
            "is_working": True
        })
    
    async def count_working_days(self, barber_id: str) -> int:
        """Count working days for barber."""
        return await self.count({
            "barber_id": barber_id,
            "is_working": True
        })
    
    async def set_working_day(self, barber_id: str, day_of_week: int, is_working: bool) -> bool:
        """Update working day status."""
        schedule = await self.find_by_barber_and_day(barber_id, day_of_week)
        if schedule:
            return await self.update_partial(schedule.id, {"is_working": is_working})
        return False


class SpecialHourRepository(BaseRepository[SpecialHours]):
    """Special hour repository for database operations."""
    
    def __init__(self, db, collection_name: str = "special_hours"):
        """Initialize special hour repository."""
        super().__init__(db, SpecialHours, collection_name)
    
    async def find_by_barber(self, barber_id: str, skip: int = 0, limit: int = 100) -> List[SpecialHours]:
        """Find special hours for barber."""
        return await self.find({"barber_id": barber_id}, skip, limit)
    
    async def find_by_barber_and_date(self, barber_id: str, date_val: date) -> Optional[SpecialHours]:
        """Find special hour for barber on specific date."""
        return await self.find_one({
            "barber_id": barber_id,
            "date": date_val
        })
    
    async def find_closed_on_date(self, barber_id: str, date_val: date) -> Optional[SpecialHours]:
        """Find if barber is closed on date."""
        return await self.find_one({
            "barber_id": barber_id,
            "date": date_val,
            "is_closed": True
        })
    
    async def find_upcoming(self, barber_id: str, days: int = 30) -> List[SpecialHours]:
        """Find upcoming special hours."""
        from datetime import timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        query = {
            "barber_id": barber_id,
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        return await self.find(query)


class HolidayRepository(BaseRepository[Holiday]):
    """Holiday repository for database operations."""
    
    def __init__(self, db, collection_name: str = "holidays"):
        """Initialize holiday repository."""
        super().__init__(db, Holiday, collection_name)
    
    async def find_all_holidays(self, skip: int = 0, limit: int = 100) -> List[Holiday]:
        """Find all holidays."""
        return await self.find({}, skip, limit)
    
    async def find_by_date(self, date_val: date) -> Optional[Holiday]:
        """Find holiday on specific date."""
        return await self.find_one({"date": date_val})
    
    async def find_for_barber(self, barber_id: str) -> List[Holiday]:
        """Find holidays that apply to barber."""
        query = {
            "$or": [
                {"applies_to_all": True},
                {"barber_ids": barber_id}
            ]
        }
        return await self.find(query)
    
    async def find_upcoming(self, days: int = 90) -> List[Holiday]:
        """Find upcoming holidays."""
        from datetime import timedelta
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        query = {
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        return await self.find(query)
    
    async def find_recurring(self) -> List[Holiday]:
        """Find recurring holidays."""
        return await self.find({"is_recurring": True})


class TimeSlotRepository(BaseRepository[TimeSlot]):
    """Time slot repository for database operations."""
    
    def __init__(self, db, collection_name: str = "time_slots"):
        """Initialize time slot repository."""
        super().__init__(db, TimeSlot, collection_name)
    
    async def find_by_barber_and_date(self, barber_id: str, date_val: date) -> List[TimeSlot]:
        """Find all slots for barber on date."""
        return await self.find({
            "barber_id": barber_id,
            "date": date_val
        })
    
    async def find_available_slots(self, barber_id: str, date_val: date) -> List[TimeSlot]:
        """Find available slots for barber on date."""
        return await self.find({
            "barber_id": barber_id,
            "date": date_val,
            "is_available": True
        })
    
    async def count_available_slots(self, barber_id: str, date_val: date) -> int:
        """Count available slots for barber on date."""
        return await self.count({
            "barber_id": barber_id,
            "date": date_val,
            "is_available": True
        })
    
    async def book_slot(self, slot_id: str, client_id: str, appointment_id: str) -> bool:
        """Book a time slot."""
        return await self.update_partial(slot_id, {
            "is_available": False,
            "booked_by": client_id,
            "appointment_id": appointment_id
        })
    
    async def release_slot(self, slot_id: str) -> bool:
        """Release a booked slot."""
        return await self.update_partial(slot_id, {
            "is_available": True,
            "booked_by": None,
            "appointment_id": None
        })
    
    async def delete_slots_for_date(self, barber_id: str, date_val: date) -> int:
        """Delete all slots for barber on date."""
        return await self.delete_many({
            "barber_id": barber_id,
            "date": date_val
        })
