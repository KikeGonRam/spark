"""
Schedule models - Barber scheduling and availability.
Manages working hours, special hours, and holidays.
"""
from typing import Optional, List
from enum import Enum
from datetime import time, date, datetime
from pydantic import BaseModel, Field, field_validator
from app.models.base import BaseDocument


class DayOfWeek(int, Enum):
    """Days of week enumeration."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class BarberSchedule(BaseDocument):
    """
    Barber Schedule model - Regular working hours.
    
    Attributes:
        id: MongoDB ObjectId as string
        barber_id: Reference to Barber
        day_of_week: Day of week (0=Monday, 6=Sunday)
        start_time: Start time (HH:MM)
        end_time: End time (HH:MM)
        break_start: Break start time (HH:MM)
        break_end: Break end time (HH:MM)
        is_working: Whether barber works this day
        max_appointments: Maximum appointments per day
    """
    
    barber_id: str = Field(..., description="Reference to Barber")
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    break_start: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    break_end: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    is_working: bool = Field(True, description="Whether barber works this day")
    max_appointments: int = Field(8, ge=1, description="Max appointments per day")
    
    @field_validator('start_time', 'end_time', 'break_start', 'break_end', mode='before')
    def validate_time_format(cls, v):
        if v and not isinstance(v, str):
            return v
        return v


class SpecialHours(BaseDocument):
    """
    Special Hours model - Overrides for holidays or special days.
    
    Attributes:
        barber_id: Reference to Barber
        date: Date for special hours
        start_time: Start time for this day
        end_time: End time for this day
        is_closed: Whether barber is closed this day
        reason: Reason for special hours (vacation, training, etc.)
    """
    
    barber_id: str
    date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_closed: bool = False
    reason: Optional[str] = None


class Holiday(BaseModel):
    """
    Holiday model - Public holidays when barbers are closed.
    """
    
    id: Optional[str] = None
    name: str
    date: date
    apply_to_all: bool = True
    barber_ids: Optional[List[str]] = None
    is_active: bool = True


class TimeSlot(BaseModel):
    """Time slot for availability."""
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class ScheduleCreate(BaseModel):
    """Create schedule model."""
    barber_id: str
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    break_start: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    break_end: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    is_working: bool = True
    max_appointments: int = 8


class SpecialHourCreate(BaseModel):
    """Create special hours model."""
    barber_id: str
    date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_closed: bool = False
    reason: Optional[str] = None


class HolidayCreate(BaseModel):
    """Create holiday model."""
    name: str = Field(..., min_length=3, max_length=100)
    date: date
    apply_to_all: bool = True
    barber_ids: Optional[List[str]] = None


class ScheduleResponse(BaseDocument):
    """Response model for schedule queries."""
    barber_id: str
    schedules: Optional[List[dict]] = None
    special_hours: Optional[List[dict]] = None
    holidays: Optional[List[dict]] = None
