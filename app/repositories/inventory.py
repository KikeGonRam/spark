"""
Inventory Repository - Data access for Product and Inventory models.
Specific queries and operations for inventory management.
"""
from typing import Optional, List
from app.models.inventory import Product, Inventory, InventoryMovement, InventoryMovementType
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Product repository for database operations."""
    
    def __init__(self, db, collection_name: str = "products"):
        """Initialize product repository."""
        super().__init__(db, Product, collection_name)
    
    async def find_by_sku(self, sku: str) -> Optional[Product]:
        """Find product by SKU."""
        return await self.find_one({"sku": sku.upper()})
    
    async def find_active(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Find all active products."""
        return await self.find({"is_active": True}, skip, limit)
    
    async def find_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[Product]:
        """Find products by category."""
        return await self.find({"category": category.lower()}, skip, limit)
    
    async def find_low_stock(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """Find products with low stock."""
        query = {"$expr": {"$lte": ["$quantity", "$minimum_quantity"]}}
        return await self.find(query, skip, limit)
    
    async def find_expired_or_expiring(self) -> List[Product]:
        """Find expired or expiring products."""
        from datetime import date, timedelta
        today = date.today()
        expiring_date = today + timedelta(days=30)
        
        query = {
            "expiry_date": {
                "$lte": expiring_date
            }
        }
        return await self.find(query)
    
    async def count_active(self) -> int:
        """Count active products."""
        return await self.count({"is_active": True})
    
    async def count_low_stock(self) -> int:
        """Count products with low stock."""
        query = {"$expr": {"$lte": ["$quantity", "$minimum_quantity"]}}
        return await self.count(query)
    
    async def deactivate_product(self, product_id: str) -> bool:
        """Deactivate product."""
        return await self.update_partial(product_id, {"is_active": False})
    
    async def activate_product(self, product_id: str) -> bool:
        """Activate product."""
        return await self.update_partial(product_id, {"is_active": True})


class InventoryRepository(BaseRepository[Inventory]):
    """Inventory repository for database operations."""
    
    def __init__(self, db, collection_name: str = "inventory"):
        """Initialize inventory repository."""
        super().__init__(db, Inventory, collection_name)
    
    async def find_by_product(self, product_id: str) -> Optional[Inventory]:
        """Find inventory by product ID."""
        return await self.find_one({"product_id": product_id})
    
    async def find_low_stock(self, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """Find inventory with low stock."""
        query = {
            "available_quantity": {"$lte": 5}
        }
        return await self.find(query, skip, limit)
    
    async def find_out_of_stock(self) -> List[Inventory]:
        """Find out of stock items."""
        return await self.find({"available_quantity": 0})
    
    async def update_stock(self, inventory_id: str, quantity_change: int) -> bool:
        """Update stock quantity."""
        inv = await self.find_by_id(inventory_id)
        if inv:
            inv.total_quantity += quantity_change
            inv.available_quantity += quantity_change
            from datetime import datetime
            inv.last_restocked = datetime.utcnow()
            return await self.update(inventory_id, inv)
        return False
    
    async def reserve_stock(self, inventory_id: str, quantity: int) -> bool:
        """Reserve stock for appointment."""
        inv = await self.find_by_id(inventory_id)
        if inv and inv.available_quantity >= quantity:
            inv.reserved_quantity += quantity
            inv.available_quantity -= quantity
            return await self.update(inventory_id, inv)
        return False
    
    async def release_reserved(self, inventory_id: str, quantity: int) -> bool:
        """Release reserved stock."""
        inv = await self.find_by_id(inventory_id)
        if inv and inv.reserved_quantity >= quantity:
            inv.reserved_quantity -= quantity
            inv.available_quantity += quantity
            return await self.update(inventory_id, inv)
        return False


class InventoryMovementRepository(BaseRepository[InventoryMovement]):
    """Inventory movement repository for database operations."""
    
    def __init__(self, db, collection_name: str = "inventory_movements"):
        """Initialize inventory movement repository."""
        super().__init__(db, InventoryMovement, collection_name)
    
    async def find_by_product(self, product_id: str, skip: int = 0, limit: int = 100) -> List[InventoryMovement]:
        """Find movements for product."""
        return await self.find({"product_id": product_id}, skip, limit)
    
    async def find_by_type(self, movement_type: InventoryMovementType, skip: int = 0, limit: int = 100) -> List[InventoryMovement]:
        """Find movements by type."""
        return await self.find({"type": movement_type.value}, skip, limit)
    
    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[InventoryMovement]:
        """Find movements by user."""
        return await self.find({"created_by": user_id}, skip, limit)
    
    async def count_by_product(self, product_id: str) -> int:
        """Count movements for product."""
        return await self.count({"product_id": product_id})
