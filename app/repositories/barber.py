"""
Barber Repository - Data access for Barber model.
Specific queries and operations for barbers.
"""
from typing import Optional, List
from app.models.barber import Barber
from app.repositories.base import BaseRepository


class BarberRepository(BaseRepository[Barber]):
    """Barber repository for database operations."""
    
    def __init__(self, db, collection_name: str = "barbers"):
        """Initialize barber repository."""
        super().__init__(db, Barber, collection_name)
    
    async def find_by_user_id(self, user_id: str) -> Optional[Barber]:
        """Find barber by user ID."""
        return await self.find_one({"user_id": user_id})
    
    async def find_available(self, skip: int = 0, limit: int = 100) -> List[Barber]:
        """Find all available barbers."""
        return await self.find({"is_available": True}, skip, limit)
    
    async def find_by_specialization(self, specialization: str, skip: int = 0, limit: int = 100) -> List[Barber]:
        """Find barbers with specific specialization."""
        return await self.find({"specialization": specialization.lower()}, skip, limit)
    
    async def find_top_rated(self, limit: int = 10) -> List[Barber]:
        """Find top rated barbers."""
        cursor = self.collection.find().sort("rating", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model(**doc) for doc in docs]
    
    async def find_by_minimum_rating(self, min_rating: float, skip: int = 0, limit: int = 100) -> List[Barber]:
        """Find barbers with minimum rating."""
        return await self.find({"rating": {"$gte": min_rating}}, skip, limit)
    
    async def count_available(self) -> int:
        """Count available barbers."""
        return await self.count({"is_available": True})
    
    async def update_rating(self, barber_id: str, new_rating: float, rating_count: int) -> bool:
        """Update barber rating."""
        return await self.update_partial(barber_id, {
            "rating": round(new_rating, 2),
            "rating_count": rating_count
        })
    
    async def add_appointment(self, barber_id: str, amount: float = 0) -> bool:
        """Increment appointment count and earnings."""
        barber = await self.find_by_id(barber_id)
        if barber:
            barber.total_appointments += 1
            barber.total_earnings += amount
            return await self.update(barber_id, barber)
        return False
    
    async def set_availability(self, barber_id: str, is_available: bool) -> bool:
        """Update barber availability."""
        return await self.update_partial(barber_id, {"is_available": is_available})
    
    async def add_specialization(self, barber_id: str, specialization: str) -> bool:
        """Add specialization to barber."""
        barber = await self.find_by_id(barber_id)
        if barber:
            if specialization.lower() not in barber.specialization:
                barber.specialization.append(specialization.lower())
                return await self.update(barber_id, barber)
        return False
