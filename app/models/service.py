"""
Service model - Barbershop services offered.
Examples: Hair cut, coloring, beard trim, treatment, etc.
"""
from enum import Enum
from typing import Optional, List
from pydantic import Field, field_validator
from app.models.base import BaseDocument


class ServiceCategory(str, Enum):
    """Service category types."""
    HAIRCUT = "haircut"
    COLORING = "coloring"
    STYLING = "styling"
    SHAVING = "shaving"
    TREATMENT = "treatment"
    COMBO = "combo"


class Service(BaseDocument):
    """
    Service model - Barbershop service offering.
    
    Attributes:
        id: MongoDB ObjectId as string
        name: Service name (e.g., "Classic Haircut")
        description: Detailed description
        duration: Service duration in minutes
        price: Service price
        category: Service category
        image: Service image URL
        is_active: Service availability
        requirements: List of required specializations
        rating: Average rating
        rating_count: Number of ratings
    """
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    duration: int = Field(..., gt=0, le=480, description="Duration in minutes (max 8 hours)")
    price: float = Field(..., gt=0, description="Price in currency units")
    category: ServiceCategory = Field(default=ServiceCategory.HAIRCUT)
    image: Optional[str] = None
    is_active: bool = Field(default=True)
    requirements: List[str] = Field(default_factory=list, description="Required specializations")
    rating: float = Field(default=0.0, ge=0, le=5)
    rating_count: int = Field(default=0, ge=0)
    discount_percent: float = Field(default=0.0, ge=0, le=100)
    
    class Config:
        collection = "services"
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        """Ensure price has valid decimal places."""
        return round(v, 2)
    
    def get_discounted_price(self) -> float:
        """Calculate discounted price."""
        return round(self.price * (1 - self.discount_percent / 100), 2)


class ServiceCreate(BaseDocument):
    """Schema for creating a new service."""
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    duration: Optional[int] = None
    duration_minutes: Optional[int] = None
    price: float = Field(..., gt=0)
    category: str = Field(default=ServiceCategory.HAIRCUT)
    requirements: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    
    def dict(self, **kwargs):
        """Override dict to map duration_minutes to duration and validate."""
        d = super().dict(**kwargs)
        
        # Map duration_minutes to duration if not set
        if d.get('duration') is None and d.get('duration_minutes') is not None:
            d['duration'] = d['duration_minutes']
        
        # Ensure duration is set
        if d.get('duration') is None:
            raise ValueError("duration or duration_minutes is required")
        
        # Remove duration_minutes as it's not needed for Service model
        d.pop('duration_minutes', None)
        
        return d


class ServiceUpdate(BaseDocument):
    """Schema for updating service."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    category: Optional[ServiceCategory] = None
    image: Optional[str] = None
    is_active: Optional[bool] = None
    discount_percent: Optional[float] = None


class ServiceResponse(BaseDocument):
    """Schema for service response."""
    
    name: str
    description: Optional[str]
    duration: int
    price: float
    category: str
    image: Optional[str]
    is_active: bool
    rating: float
    rating_count: int
    created_at: str
    updated_at: str


class ServiceCombo(BaseDocument):
    """
    Service combo model - Multiple services bundled together.
    
    Attributes:
        id: MongoDB ObjectId as string
        name: Combo name (e.g., "Full Grooming Package")
        description: Combo description
        services: List of service IDs in combo
        price: Total combo price
        discount_percent: Discount applied to combo
        is_active: Combo availability
    """
    
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    services: List[str] = Field(..., min_items=2, description="Service IDs in combo")
    price: float = Field(..., gt=0)
    discount_percent: float = Field(default=0.0, ge=0, le=100)
    is_active: bool = Field(default=True)
    
    class Config:
        collection = "service_combos"
    
    def get_discounted_price(self) -> float:
        """Calculate discounted combo price."""
        return round(self.price * (1 - self.discount_percent / 100), 2)


class ServiceComboCreate(BaseDocument):
    """Schema for creating service combo."""
    
    name: str
    description: Optional[str] = None
    services: List[str] = Field(..., min_items=2)
    price: float = Field(..., gt=0)
    discount_percent: float = Field(default=0.0, ge=0, le=100)
