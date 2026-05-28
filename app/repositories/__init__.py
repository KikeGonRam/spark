"""
Repositories package - Data access layer.
All repository classes for database operations.
"""

from app.repositories.base import BaseRepository
from app.repositories.user import UserRepository
from app.repositories.barber import BarberRepository
from app.repositories.appointment import AppointmentRepository
from app.repositories.service import ServiceRepository, ServiceComboRepository
from app.repositories.payment import PaymentRepository, InvoiceRepository
from app.repositories.inventory import ProductRepository, InventoryRepository, InventoryMovementRepository
from app.repositories.schedule import BarberScheduleRepository, SpecialHourRepository, HolidayRepository, TimeSlotRepository
from app.repositories.client import ClientRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "BarberRepository",
    "AppointmentRepository",
    "ServiceRepository",
    "ServiceComboRepository",
    "PaymentRepository",
    "InvoiceRepository",
    "ProductRepository",
    "InventoryRepository",
    "InventoryMovementRepository",
    "BarberScheduleRepository",
    "SpecialHourRepository",
    "HolidayRepository",
    "TimeSlotRepository",
    "ClientRepository",
]
