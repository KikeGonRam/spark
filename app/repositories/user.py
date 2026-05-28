"""
User Repository - Data access for User model.
Specific queries and operations for users.
"""
from typing import Optional, List
from app.models.user import User, UserRole, UserStatus
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    User repository for database operations.
    Inherits generic CRUD from BaseRepository.
    """
    
    def __init__(self, db, collection_name: str = "users"):
        """Initialize user repository."""
        super().__init__(db, User, collection_name)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        return await self.find_one({"email": email.lower()})
    
    async def find_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Find all users with specific role."""
        return await self.find({"role": role.value}, skip, limit)
    
    async def find_active(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Find all active users."""
        return await self.find({"status": UserStatus.ACTIVE.value}, skip, limit)
    
    async def find_by_status(self, status: UserStatus, skip: int = 0, limit: int = 100) -> List[User]:
        """Find users by status."""
        return await self.find({"status": status.value}, skip, limit)
    
    async def find_admins(self) -> List[User]:
        """Find all admin users."""
        return await self.find({"role": UserRole.ADMIN.value})
    
    async def find_barbers(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Find all barber users."""
        return await self.find({"role": UserRole.BARBER.value}, skip, limit)
    
    async def find_clients(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Find all client users."""
        return await self.find({"role": UserRole.CLIENT.value}, skip, limit)
    
    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role."""
        return await self.count({"role": role.value})
    
    async def count_active(self) -> int:
        """Count active users."""
        return await self.count({"status": UserStatus.ACTIVE.value})
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return await self.exists({"email": email.lower()})
    
    async def verify_email(self, user_id: str) -> bool:
        """Mark email as verified."""
        return await self.update_partial(user_id, {"is_email_verified": True})
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update last login timestamp."""
        from datetime import datetime
        return await self.update_partial(user_id, {"last_login": datetime.utcnow()})
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        return await self.update_partial(user_id, {"status": UserStatus.INACTIVE.value})
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate user account."""
        return await self.update_partial(user_id, {"status": UserStatus.ACTIVE.value})
    
    async def ban_user(self, user_id: str) -> bool:
        """Ban user account."""
        return await self.update_partial(user_id, {"status": UserStatus.BANNED.value})
