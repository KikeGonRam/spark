"""
App models package - All Pydantic models for the application.

This package contains all data models used in the application:
- Base models with common fields
- Domain models (User, Barber, Client, Appointment, Service, Payment, etc.)
- Request/Response schemas
- Enum types for status fields
"""

from app.models.base import BaseDocument, TimestampModel
from app.models.user import User, UserCreate, UserLogin, UserUpdate, UserResponse, UserRole, UserStatus
from app.models.barber import Barber, BarberCreate, BarberWithUserCreate, BarberUpdate, BarberResponse
from app.models.client import Client, ClientCreate, ClientUpdate, ClientResponse
from app.models.service import Service, ServiceCreate, ServiceUpdate, ServiceResponse, ServiceCombo, ServiceComboCreate
from app.models.appointment import Appointment, AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentStatus
from app.models.payment import Payment, PaymentCreate, PaymentUpdate, PaymentResponse, Invoice, InvoiceCreate, PaymentMethod, PaymentStatus
from app.models.inventory import Product, Inventory, InventoryMovement, ProductCreate, InventoryMovementCreate, InventoryMovementType
from app.models.schedule import BarberSchedule, SpecialHours, Holiday, TimeSlot, ScheduleCreate, SpecialHourCreate, HolidayCreate

__all__ = [
    # Base
    "BaseDocument",
    "TimestampModel",
    # User models
    "User",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserRole",
    "UserStatus",
    # Barber models
    "Barber",
    "BarberCreate",
    "BarberWithUserCreate",
    "BarberUpdate",
    "BarberResponse",
    # Client models
    "Client",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    # Service models
    "Service",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceCombo",
    "ServiceComboCreate",
    # Appointment models
    "Appointment",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "AppointmentStatus",
    # Payment models
    "Payment",
    "PaymentCreate",
    "PaymentUpdate",
    "PaymentResponse",
    "Invoice",
    "InvoiceCreate",
    "PaymentMethod",
    "PaymentStatus",
    # Inventory models
    "Product",
    "Inventory",
    "InventoryMovement",
    "ProductCreate",
    "InventoryMovementCreate",
    "InventoryMovementType",
    # Schedule models
    "BarberSchedule",
    "SpecialHours",
    "Holiday",
    "TimeSlot",
    "ScheduleCreate",
    "SpecialHourCreate",
    "HolidayCreate",
]
