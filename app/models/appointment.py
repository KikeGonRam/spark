"""
Appointment model - Customer appointments/reservations.
Core business logic for booking system.
"""
from typing import Optional, List
from enum import Enum
from datetime import datetime, date
from pydantic import Field, field_validator
from app.models.base import BaseDocument


class AppointmentStatus(str, Enum):
    """Appointment status enumeration."""
    PENDING = "pending"          # Awaiting confirmation
    CONFIRMED = "confirmed"      # Confirmed and booked
    IN_PROGRESS = "in_progress"  # Currently being served
    COMPLETED = "completed"      # Service completed
    CANCELLED = "cancelled"      # Cancelled by customer or staff
    NO_SHOW = "no_show"         # Customer didn't show up


class Appointment(BaseDocument):
    """
    Appointment model - Customer reservation.
    
    Attributes:
        id: MongoDB ObjectId as string
        barber_id: Reference to Barber document
        client_id: Reference to Client document
        service_id: Reference to Service document
        appointment_date: Date of appointment
        start_time: Start time (HH:MM)
        end_time: End time (HH:MM)
        status: Appointment status
        notes: Special notes from customer
        reminder_sent: Whether reminder was sent
        payment_id: Reference to Payment document (if paid)
        rating: Service rating (1-5) after completion
        feedback: Customer feedback after service
    """
    
    barber_id: str = Field(..., description="Reference to Barber")
    client_id: str = Field(..., description="Reference to Client")
    service_id: str = Field(..., description="Reference to Service")
    appointment_date: str = Field(...)
    start_time: str = Field(..., description="Start time HH:MM")
    end_time: str = Field(..., description="End time HH:MM")
    status: AppointmentStatus = Field(default=AppointmentStatus.PENDING)
    notes: Optional[str] = Field(None, max_length=500)
    reminder_sent: bool = Field(default=False)
    payment_id: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=1000)
    
    class Config:
        collection = "appointments"
    
    @field_validator('start_time', 'end_time')
    @classmethod
    def validate_time_format(cls, v):
        """Validate time format HH:MM."""
        try:
            h, m = v.split(':')
            if not (0 <= int(h) < 24 and 0 <= int(m) < 60):
                raise ValueError
            return v
        except:
            raise ValueError("Invalid time format. Use HH:MM")
    
    @field_validator('appointment_date')
    @classmethod
    def validate_future_date(cls, v):
        """Ensure appointment is in future."""
        parsed = date.fromisoformat(v) if isinstance(v, str) else v
        if parsed < date.today():
            raise ValueError("Appointment date must be in the future")
        return v
    
    def calculate_duration_minutes(self) -> int:
        """Calculate appointment duration in minutes."""
        start = datetime.strptime(self.start_time, "%H:%M")
        end = datetime.strptime(self.end_time, "%H:%M")
        return int((end - start).total_seconds() / 60)
    
    def can_cancel(self) -> bool:
        """Check if appointment can be cancelled."""
        return self.status in [
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED
        ]


class AppointmentCreate(BaseDocument):
    """Schema for creating appointment."""
    
    barber_id: str
    service_id: str
    appointment_date: str
    start_time: str
    end_time: Optional[str] = None
    notes: Optional[str] = None


class AppointmentUpdate(BaseDocument):
    """Schema for updating appointment."""
    
    appointment_date: Optional[str] = None
    start_time: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None


class AppointmentResponse(BaseDocument):
    """Schema for appointment response."""
    
    barber_id: str
    client_id: str
    service_id: str
    appointment_date: str
    start_time: str
    end_time: str
    status: str
    notes: Optional[str]
    rating: Optional[int]
    feedback: Optional[str]
    created_at: str
    updated_at: str
