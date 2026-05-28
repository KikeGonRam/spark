"""
Service Repository - Data access for Service model.
Specific queries and operations for services.
"""
from typing import Optional, List
from app.models.service import Service, ServiceCombo
from app.repositories.base import BaseRepository


class ServiceRepository(BaseRepository[Service]):
    """Service repository for database operations."""
    
    def __init__(self, db, collection_name: str = "services"):
        """Initialize service repository."""
        super().__init__(db, Service, collection_name)
    
    async def find_active(self, skip: int = 0, limit: int = 100) -> List[Service]:
        """Find all active services."""
        return await self.find({"is_active": True}, skip, limit)
    
    async def find_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Service]:
        """Find services by category."""
        return await self.find({"category": category.lower()}, skip, limit)
    
    async def find_by_name(self, name: str) -> Optional[Service]:
        """Find service by name."""
        return await self.find_one({"name": {"$regex": name, "$options": "i"}})
    
    async def find_top_rated(self, limit: int = 10) -> List[Service]:
        """Find top rated services."""
        cursor = self.collection.find({"is_active": True}).sort("rating", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model(**doc) for doc in docs]
    
    async def find_by_duration_range(self, min_duration: int, max_duration: int, skip: int = 0, limit: int = 100) -> List[Service]:
        """Find services within duration range."""
        query = {
            "duration": {
                "$gte": min_duration,
                "$lte": max_duration
            }
        }
        return await self.find(query, skip, limit)
    
    async def find_by_price_range(self, min_price: float, max_price: float, skip: int = 0, limit: int = 100) -> List[Service]:
        """Find services within price range."""
        query = {
            "price": {
                "$gte": min_price,
                "$lte": max_price
            }
        }
        return await self.find(query, skip, limit)
    
    async def count_active(self) -> int:
        """Count active services."""
        return await self.count({"is_active": True})
    
    async def update_rating(self, service_id: str, new_rating: float, rating_count: int) -> bool:
        """Update service rating."""
        return await self.update_partial(service_id, {
            "rating": round(new_rating, 2),
            "rating_count": rating_count
        })
    
    async def deactivate_service(self, service_id: str) -> bool:
        """Deactivate service."""
        return await self.update_partial(service_id, {"is_active": False})
    
    async def activate_service(self, service_id: str) -> bool:
        """Activate service."""
        return await self.update_partial(service_id, {"is_active": True})


class ServiceComboRepository(BaseRepository[ServiceCombo]):
    """Service combo repository for database operations."""
    
    def __init__(self, db, collection_name: str = "service_combos"):
        """Initialize service combo repository."""
        super().__init__(db, ServiceCombo, collection_name)
    
    async def find_active(self, skip: int = 0, limit: int = 100) -> List[ServiceCombo]:
        """Find all active combos."""
        return await self.find({"is_active": True}, skip, limit)
    
    async def find_by_service_id(self, service_id: str) -> List[ServiceCombo]:
        """Find combos containing service."""
        return await self.find({"services": service_id})
    
    async def find_best_value(self, limit: int = 10) -> List[ServiceCombo]:
        """Find combos with highest discount."""
        cursor = self.collection.find({"is_active": True}).sort("discount_percent", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model(**doc) for doc in docs]
    
    async def count_active(self) -> int:
        """Count active combos."""
        return await self.count({"is_active": True})
    
    async def deactivate_combo(self, combo_id: str) -> bool:
        """Deactivate combo."""
        return await self.update_partial(combo_id, {"is_active": False})
    
    async def activate_combo(self, combo_id: str) -> bool:
        """Activate combo."""
        return await self.update_partial(combo_id, {"is_active": True})
