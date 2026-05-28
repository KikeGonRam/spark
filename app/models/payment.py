"""
Payment model - Payment transactions and invoicing.
Tracks all payment records for appointments and services.
"""
from typing import Optional, List
from enum import Enum
from datetime import datetime
from decimal import Decimal
from pydantic import Field, field_validator
from app.models.base import BaseDocument


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    MOBILE_PAYMENT = "mobile_payment"
    BANK_TRANSFER = "bank_transfer"
    CRYPTOCURRENCY = "cryptocurrency"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Payment(BaseDocument):
    """
    Payment model - Payment transaction record.
    
    Attributes:
        id: MongoDB ObjectId as string
        appointment_id: Reference to Appointment
        amount: Payment amount
        currency: Currency code (e.g., USD, MXN)
        method: Payment method used
        status: Payment status
        transaction_id: External transaction ID (from payment provider)
        invoice_number: Invoice number for accounting
        customer_name: Customer name on payment
        customer_email: Customer email for receipt
        notes: Additional payment notes
        payment_date: When payment was processed
        refund_date: When refund was processed (if any)
        refund_reason: Reason for refund
    """
    
    appointment_id: str = Field(..., description="Reference to Appointment")
    amount: float = Field(..., gt=0, description="Amount in currency units")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    method: PaymentMethod = Field(...)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    transaction_id: Optional[str] = Field(None, description="External transaction ID")
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)
    payment_date: Optional[datetime] = None
    refund_date: Optional[datetime] = None
    refund_reason: Optional[str] = Field(None, max_length=500)
    
    class Config:
        collection = "payments"
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Ensure amount has valid decimal places."""
        return round(v, 2)
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code."""
        return v.upper()
    
    def process_payment(self) -> bool:
        """Mark payment as completed."""
        if self.status == PaymentStatus.PENDING:
            self.status = PaymentStatus.COMPLETED
            self.payment_date = datetime.utcnow()
            return True
        return False
    
    def refund_payment(self, reason: str) -> bool:
        """Refund payment."""
        if self.status == PaymentStatus.COMPLETED:
            self.status = PaymentStatus.REFUNDED
            self.refund_date = datetime.utcnow()
            self.refund_reason = reason
            return True
        return False
    
    def is_paid(self) -> bool:
        """Check if payment is completed."""
        return self.status == PaymentStatus.COMPLETED


class PaymentCreate(BaseDocument):
    """Schema for creating payment."""
    
    appointment_id: str
    amount: float = Field(..., gt=0)
    method: PaymentMethod
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseDocument):
    """Schema for updating payment."""
    
    status: Optional[PaymentStatus] = None
    transaction_id: Optional[str] = None
    invoice_number: Optional[str] = None
    refund_reason: Optional[str] = None


class PaymentResponse(BaseDocument):
    """Schema for payment response."""
    
    appointment_id: str
    amount: float
    currency: str
    method: str
    status: str
    transaction_id: Optional[str]
    invoice_number: Optional[str]
    payment_date: Optional[str]
    created_at: str
    updated_at: str


class Invoice(BaseDocument):
    """Invoice model - Generated from payment."""
    
    payment_id: str
    invoice_number: str
    appointment_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str
    issued_date: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    items: List[dict] = Field(default_factory=list)
    notes: Optional[str] = None
    paid: bool = Field(default=False)
    
    class Config:
        collection = "invoices"

class InvoiceCreate(BaseDocument):
    "Schema for creating invoice."
    
    payment_id: str
    invoice_number: str
    appointment_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str = "USD"
    items: Optional[List[dict]] = None
    notes: Optional[str] = None
