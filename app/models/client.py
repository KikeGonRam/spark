"""
Client model - Customer/Client entity.
Extends User model with client-specific information.
"""
from typing import Optional, List
from pydantic import Field, field_validator
from app.models.base import BaseDocument


class ClientLoyaltyStatus(str):
    """Client loyalty status levels."""
    BRONZE = "bronze"      # 0-100 points
    SILVER = "silver"      # 100-500 points
    GOLD = "gold"          # 500-1000 points
    PLATINUM = "platinum"  # 1000+ points


class Client(BaseDocument):
    """
    Client model - Customer information.
    
    Attributes:
        id: MongoDB ObjectId as string
        user_id: Reference to User document
        total_appointments: Total count of appointments
        completed_appointments: Count of completed appointments
        preferred_barber: Optional preferred barber ID
        loyalty_points: Accumulated loyalty points
        total_spent: Total money spent at barbershop
        phone_verified: Whether phone is verified
        address: Full address
        city: City name
        postal_code: Postal/ZIP code
        country: Country name
        referral_code: Unique referral code for this client
        referred_by: Who referred this client (if any)
        is_vip: VIP customer status
    """
    
    user_id: str = Field(..., description="Reference to User")
    total_appointments: int = Field(default=0, ge=0)
    completed_appointments: int = Field(default=0, ge=0)
    preferred_barber: Optional[str] = None
    loyalty_points: int = Field(default=0, ge=0)
    total_spent: float = Field(default=0.0, ge=0)
    phone_verified: bool = Field(default=False)
    address: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    referral_code: Optional[str] = Field(None, unique=True)
    referred_by: Optional[str] = None
    is_vip: bool = Field(default=False)
    
    class Config:
        collection = "clients"
    
    def get_loyalty_status(self) -> ClientLoyaltyStatus:
        """Get loyalty status based on points."""
        if self.loyalty_points >= 1000:
            return ClientLoyaltyStatus.PLATINUM
        elif self.loyalty_points >= 500:
            return ClientLoyaltyStatus.GOLD
        elif self.loyalty_points >= 100:
            return ClientLoyaltyStatus.SILVER
        else:
            return ClientLoyaltyStatus.BRONZE
    
    def add_loyalty_points(self, points: int) -> int:
        """Add loyalty points to client."""
        self.loyalty_points += points
        return self.loyalty_points
    
    def add_appointment(self) -> int:
        """Increment appointment count."""
        self.total_appointments += 1
        return self.total_appointments
    
    def complete_appointment(self, amount: float) -> None:
        """Mark appointment as completed and add spending."""
        self.completed_appointments += 1
        self.total_spent += amount


class ClientCreate(BaseDocument):
    """Schema for creating client."""
    
    user_id: str
    preferred_barber: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


class ClientUpdate(BaseDocument):
    """Schema for updating client."""
    
    preferred_barber: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_vip: Optional[bool] = None


class ClientResponse(BaseDocument):
    """Schema for client response."""
    
    user_id: str
    total_appointments: int
    completed_appointments: int
    preferred_barber: Optional[str]
    loyalty_points: int
    total_spent: float
    loyalty_status: str
    is_vip: bool
    created_at: str
    updated_at: str
