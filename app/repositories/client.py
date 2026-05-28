"""
Client Repository - Data access for Client models.
Specific queries and operations for barbershop clients.
"""
from typing import Optional, List
from app.models.client import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    """Client repository for database operations."""
    
    def __init__(self, db, collection_name: str = "clients"):
        """Initialize client repository."""
        super().__init__(db, Client, collection_name)
    
    async def find_by_user_id(self, user_id: str) -> Optional[Client]:
        """Find client by user ID."""
        return await self.find_one({"user_id": user_id})

    async def find_by_email(self, email: str) -> Optional[Client]:
        """Find client by the linked user email."""
        user = await self.db["users"].find_one({"email": email.lower()})
        if not user:
            return None
        user_id = str(user["_id"])
        return await self.find_by_user_id(user_id)
    
    async def find_vip_clients(self, skip: int = 0, limit: int = 100) -> List[Client]:
        """Find all VIP clients."""
        return await self.find({"is_vip": True}, skip, limit)
    
    async def find_by_loyalty_status(self, status: str, skip: int = 0, limit: int = 100) -> List[Client]:
        """Find clients by loyalty status."""
        query = {}
        if status == "platinum":
            query = {"loyalty_points": {"$gte": 1000}}
        elif status == "gold":
            query = {"loyalty_points": {"$gte": 500, "$lt": 1000}}
        elif status == "silver":
            query = {"loyalty_points": {"$gte": 100, "$lt": 500}}
        elif status == "bronze":
            query = {"loyalty_points": {"$lt": 100}}
        
        return await self.find(query, skip, limit)
    
    async def find_high_spenders(self, min_spent: float = 1000.0, skip: int = 0, limit: int = 100) -> List[Client]:
        """Find clients who have spent above minimum."""
        return await self.find({"total_spent": {"$gte": min_spent}}, skip, limit)
    
    async def find_by_referral_code(self, referral_code: str) -> Optional[Client]:
        """Find client by referral code."""
        return await self.find_one({"referral_code": referral_code})
    
    async def find_referred_by(self, referrer_id: str, skip: int = 0, limit: int = 100) -> List[Client]:
        """Find clients referred by specific client."""
        return await self.find({"referred_by": referrer_id}, skip, limit)
    
    async def find_by_preferred_barber(self, barber_id: str, skip: int = 0, limit: int = 100) -> List[Client]:
        """Find clients who prefer specific barber."""
        return await self.find({"preferred_barber": barber_id}, skip, limit)
    
    async def update_loyalty_points(self, client_id: str, points: int) -> bool:
        """Update loyalty points for client."""
        return await self.update_partial(client_id, {"loyalty_points": points})
    
    async def add_loyalty_points(self, client_id: str, points: int) -> bool:
        """Add loyalty points to client."""
        client = await self.find_by_id(client_id)
        if client:
            new_points = client.loyalty_points + points
            return await self.update_loyalty_points(client_id, new_points)
        return False
    
    async def update_appointment_count(self, client_id: str, completed: bool = False) -> bool:
        """Increment appointment count."""
        client = await self.find_by_id(client_id)
        if client:
            update_data = {"total_appointments": client.total_appointments + 1}
            if completed:
                update_data["completed_appointments"] = client.completed_appointments + 1
            return await self.update_partial(client_id, update_data)
        return False
    
    async def add_spending(self, client_id: str, amount: float) -> bool:
        """Add amount to client's total spending."""
        client = await self.find_by_id(client_id)
        if client:
            new_spent = client.total_spent + amount
            return await self.update_partial(client_id, {"total_spent": new_spent})
        return False
    
    async def verify_phone(self, client_id: str) -> bool:
        """Mark client's phone as verified."""
        return await self.update_partial(client_id, {"phone_verified": True})
    
    async def set_vip_status(self, client_id: str, is_vip: bool) -> bool:
        """Update VIP status for client."""
        return await self.update_partial(client_id, {"is_vip": is_vip})
    
    async def set_preferred_barber(self, client_id: str, barber_id: Optional[str]) -> bool:
        """Set or clear preferred barber for client."""
        return await self.update_partial(client_id, {"preferred_barber": barber_id})
    
    async def count_vip_clients(self) -> int:
        """Count total VIP clients."""
        return await self.count({"is_vip": True})
    
    async def count_by_loyalty_status(self, status: str) -> int:
        """Count clients by loyalty status."""
        query = {}
        if status == "platinum":
            query = {"loyalty_points": {"$gte": 1000}}
        elif status == "gold":
            query = {"loyalty_points": {"$gte": 500, "$lt": 1000}}
        elif status == "silver":
            query = {"loyalty_points": {"$gte": 100, "$lt": 500}}
        elif status == "bronze":
            query = {"loyalty_points": {"$lt": 100}}
        
        return await self.count(query)
