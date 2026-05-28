"""
Payment Repository - Data access for Payment model.
Specific queries and operations for payments.
"""
from typing import Optional, List
from datetime import datetime, date
from app.models.payment import Payment, Invoice, PaymentStatus, PaymentMethod
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Payment repository for database operations."""
    
    def __init__(self, db, collection_name: str = "payments"):
        """Initialize payment repository."""
        super().__init__(db, Payment, collection_name)
    
    async def find_by_appointment(self, appointment_id: str) -> Optional[Payment]:
        """Find payment by appointment ID."""
        return await self.find_one({"appointment_id": appointment_id})
    
    async def find_by_status(self, status: PaymentStatus, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Find payments by status."""
        return await self.find({"status": status.value}, skip, limit)
    
    async def find_completed(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Find all completed payments."""
        return await self.find({"status": PaymentStatus.COMPLETED.value}, skip, limit)
    
    async def find_pending(self) -> List[Payment]:
        """Find all pending payments."""
        return await self.find({"status": PaymentStatus.PENDING.value})
    
    async def find_refunded(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Find all refunded payments."""
        return await self.find({"status": PaymentStatus.REFUNDED.value}, skip, limit)
    
    async def find_by_date_range(self, start_date: date, end_date: date, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Find payments within date range."""
        query = {
            "payment_date": {
                "$gte": datetime.combine(start_date, datetime.min.time()),
                "$lte": datetime.combine(end_date, datetime.max.time())
            }
        }
        return await self.find(query, skip, limit)
    
    async def find_by_method(self, method: PaymentMethod, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Find payments by method."""
        return await self.find({"method": method.value}, skip, limit)
    
    async def count_by_status(self, status: PaymentStatus) -> int:
        """Count payments by status."""
        return await self.count({"status": status.value})
    
    async def sum_completed_payments(self) -> float:
        """Calculate total completed payments."""
        pipeline = [
            {"$match": {"status": PaymentStatus.COMPLETED.value}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0.0
    
    async def sum_by_date_range(self, start_date: date, end_date: date) -> float:
        """Sum payments within date range."""
        query = {
            "payment_date": {
                "$gte": datetime.combine(start_date, datetime.min.time()),
                "$lte": datetime.combine(end_date, datetime.max.time())
            },
            "status": PaymentStatus.COMPLETED.value
        }
        pipeline = [
            {"$match": query},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0.0
    
    async def process_payment(self, payment_id: str, transaction_id: str) -> bool:
        """Mark payment as completed."""
        return await self.update_partial(payment_id, {
            "status": PaymentStatus.COMPLETED.value,
            "payment_date": datetime.utcnow(),
            "transaction_id": transaction_id
        })
    
    async def refund_payment(self, payment_id: str, reason: str) -> bool:
        """Refund a payment."""
        return await self.update_partial(payment_id, {
            "status": PaymentStatus.REFUNDED.value,
            "refund_date": datetime.utcnow(),
            "refund_reason": reason
        })


class InvoiceRepository(BaseRepository[Invoice]):
    """Invoice repository for database operations."""
    
    def __init__(self, db, collection_name: str = "invoices"):
        """Initialize invoice repository."""
        super().__init__(db, Invoice, collection_name)
    
    async def find_by_payment(self, payment_id: str) -> Optional[Invoice]:
        """Find invoice by payment ID."""
        return await self.find_one({"payment_id": payment_id})
    
    async def find_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Find invoice by invoice number."""
        return await self.find_one({"invoice_number": invoice_number})
    
    async def find_unpaid(self, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Find all unpaid invoices."""
        return await self.find({"paid": False}, skip, limit)
    
    async def find_by_customer_email(self, email: str, skip: int = 0, limit: int = 100) -> List[Invoice]:
        """Find invoices by customer email."""
        return await self.find({"customer_email": email.lower()}, skip, limit)
    
    async def mark_as_paid(self, invoice_id: str) -> bool:
        """Mark invoice as paid."""
        return await self.update_partial(invoice_id, {"paid": True})
