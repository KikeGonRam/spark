"""
Inventory models - Product and inventory management.
Tracks barbershop products, stock levels, and movements.
"""
from typing import Optional, List
from enum import Enum
from datetime import datetime, date
from pydantic import Field, field_validator
from app.models.base import BaseDocument


class InventoryMovementType(str, Enum):
    """Type of inventory movement."""
    IN = "in"              # Stock added
    OUT = "out"            # Stock used/sold
    ADJUSTMENT = "adjustment"  # Manual adjustment
    RETURN = "return"      # Returned to supplier
    DAMAGE = "damage"      # Damaged/destroyed


class ProductCategory(str, Enum):
    """Product categories."""
    HAIR_PRODUCTS = "hair_products"
    SHAVING_PRODUCTS = "shaving_products"
    STYLING_PRODUCTS = "styling_products"
    TOOLS = "tools"
    SUPPLIES = "supplies"
    OTHER = "other"


class Product(BaseDocument):
    """
    Product model - Inventory product.
    
    Attributes:
        id: MongoDB ObjectId as string
        name: Product name
        sku: Stock Keeping Unit (unique code)
        category: Product category
        quantity: Current quantity in stock
        minimum_quantity: Minimum quantity threshold
        unit: Unit of measurement (ml, g, pieces, etc.)
        price: Cost price per unit
        supplier: Supplier name
        expiry_date: Expiration date (if applicable)
        image: Product image URL
        description: Product description
        is_active: Whether product is active
        location: Storage location in barbershop
    """
    
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., unique=True, min_length=1, max_length=50)
    category: ProductCategory = Field(...)
    quantity: int = Field(default=0, ge=0)
    minimum_quantity: int = Field(default=5, ge=0)
    unit: str = Field(default="unit", max_length=20)
    price: float = Field(..., gt=0)
    supplier: Optional[str] = Field(None, max_length=200)
    expiry_date: Optional[date] = None
    image: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)
    location: Optional[str] = Field(None, max_length=100)
    
    class Config:
        collection = "products"
    
    def is_low_stock(self) -> bool:
        """Check if stock is below minimum."""
        return self.quantity <= self.minimum_quantity
    
    def is_expired(self) -> bool:
        """Check if product is expired."""
        if self.expiry_date:
            return date.today() > self.expiry_date
        return False


class InventoryMovement(BaseDocument):
    """
    Inventory Movement model - Track all inventory changes.
    
    Attributes:
        id: MongoDB ObjectId as string
        product_id: Reference to Product
        type: Type of movement (in, out, adjustment, etc.)
        quantity: Quantity moved
        reason: Reason for movement
        notes: Additional notes
        created_by: User ID who made the movement
        old_quantity: Quantity before movement
        new_quantity: Quantity after movement
        reference: Reference number (invoice, order, etc.)
    """
    
    product_id: str = Field(..., description="Reference to Product")
    type: InventoryMovementType = Field(...)
    quantity: int = Field(..., gt=0)
    reason: str = Field(..., max_length=200)
    notes: Optional[str] = Field(None, max_length=500)
    created_by: str = Field(..., description="User ID")
    old_quantity: int = Field(default=0, ge=0)
    new_quantity: int = Field(default=0, ge=0)
    reference: Optional[str] = Field(None, max_length=100)
    
    class Config:
        collection = "inventory_movements"
    
    @field_validator('new_quantity')
    @classmethod
    def validate_new_quantity(cls, v):
        """Ensure new quantity is not negative."""
        if v < 0:
            raise ValueError("New quantity cannot be negative")
        return v


class Inventory(BaseDocument):
    """
    Inventory model - Current inventory status.
    
    Attributes:
        id: MongoDB ObjectId as string
        product_id: Reference to Product
        total_quantity: Total quantity in inventory
        reserved_quantity: Quantity reserved for appointments
        available_quantity: Quantity available for sale
        last_counted: Last physical count date
        last_restocked: Last restocking date
    """
    
    product_id: str = Field(..., unique=True)
    total_quantity: int = Field(default=0, ge=0)
    reserved_quantity: int = Field(default=0, ge=0)
    available_quantity: int = Field(default=0, ge=0)
    last_counted: Optional[datetime] = None
    last_restocked: Optional[datetime] = None
    
    class Config:
        collection = "inventory"
    
    def add_stock(self, quantity: int) -> int:
        """Add stock."""
        self.total_quantity += quantity
        self.available_quantity += quantity
        return self.total_quantity
    
    def remove_stock(self, quantity: int) -> bool:
        """Remove stock if available."""
        if self.available_quantity >= quantity:
            self.total_quantity -= quantity
            self.available_quantity -= quantity
            return True
        return False


class ProductCreate(BaseDocument):
    """Schema for creating product."""
    
    name: str
    sku: str
    category: ProductCategory
    quantity: int = 0
    minimum_quantity: int = 5
    unit: str = "unit"
    price: float
    supplier: Optional[str] = None
    expiry_date: Optional[date] = None


class InventoryMovementCreate(BaseDocument):
    """Schema for creating inventory movement."""
    
    product_id: str
    type: InventoryMovementType
    quantity: int = Field(..., gt=0)
    reason: str
    notes: Optional[str] = None
    created_by: str
    reference: Optional[str] = None
