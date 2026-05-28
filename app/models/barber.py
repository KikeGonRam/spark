"""
Barber model - Professional barber entity.
Extends User model with barber-specific information.
"""
from typing import Optional, List
from datetime import time
from pydantic import Field, field_validator
from app.models.base import BaseDocument


class BarbersSpecialization(str):
    """Barber specialization types."""
    CUTS = "cuts"
    COLORING = "coloring"
    STYLING = "styling"
    SHAVING = "shaving"
    TREATMENTS = "treatments"


class Barber(BaseDocument):
    """
    Barber model - Professional barber information.
    
    Attributes:
        id: MongoDB ObjectId as string
        user_id: Reference to User document
        specialization: List of barber specializations
        rating: Average rating (0-5)
        total_appointments: Count of completed appointments
        total_earnings: Sum of all payments received
        bio: Extended biography
        avatar: Profile picture URL
        is_available: Availability status
        rating_count: Number of ratings received
    """
    
    user_id: str = Field(..., description="Reference to User document")
    specialization: List[str] = Field(default_factory=list, description="List of specializations")
    rating: float = Field(default=0.0, ge=0, le=5, description="Average rating")
    total_appointments: int = Field(default=0, ge=0)
    total_earnings: float = Field(default=0.0, ge=0)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar: Optional[str] = None
    is_available: bool = Field(default=True)
    rating_count: int = Field(default=0, ge=0)
    working_hours_start: Optional[str] = Field(None, description="Working hours start (HH:MM)")
    working_hours_end: Optional[str] = Field(None, description="Working hours end (HH:MM)")
    days_off: List[int] = Field(default_factory=list, description="Days off (0=Monday, 6=Sunday)")
    
    class Config:
        collection = "barbers"
    
    @field_validator('specialization')
    @classmethod
    def validate_specialization(cls, v):
        """Ensure specialization is not empty if provided."""
        if v and isinstance(v, list):
            return [s.lower() for s in v]
        return v


class BarberCreate(BaseDocument):
    """Schema for creating a new barber."""
    
    user_id: str
    specialization: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None


class BarberWithUserCreate(BaseDocument):
    """Schema for creating a barber with user account (combined)."""
    
    name: str = Field(..., min_length=2, max_length=100)
    email: str
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    specialization: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None


class BarberUpdate(BaseDocument):
    """Schema for updating barber information."""
    
    specialization: Optional[List[str]] = None
    bio: Optional[str] = None
    avatar: Optional[str] = None
    is_available: Optional[bool] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None


class BarberResponse(BaseDocument):
    """Schema for barber response."""
    
    user_id: str
    specialization: List[str]
    rating: float
    total_appointments: int
    total_earnings: float
    bio: Optional[str]
    avatar: Optional[str]
    is_available: bool
    rating_count: int
    created_at: str
    updated_at: str
