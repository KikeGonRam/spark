"""
Common dependencies for routes
"""
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer
from starlette.requests import Request
from database.connection import MongoDBConnection
from app.models import User, UserRole
from app.config import settings
import jwt
from typing import Optional

security = HTTPBearer()


def get_db():
    """Get MongoDB connection or raise error"""
    db = MongoDBConnection.get_db()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not connected"
        )
    return db


async def get_current_user(request: Request) -> User:
    """Extract and validate JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    # Get user from DB
    db = get_db()
    from bson import ObjectId
    
    try:
        user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
    except:
        user_doc = await db["users"].find_one({"_id": user_id})
    
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Convert ObjectId to string for Pydantic model
    if "_id" in user_doc and hasattr(user_doc["_id"], "__str__"):
        user_doc["_id"] = str(user_doc["_id"])
    
    return User(**user_doc)


def require_role(*allowed_roles: UserRole):
    """Dependency to require specific roles"""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current_user.role} not allowed. Required: {allowed_roles}"
            )
        return current_user
    return role_checker


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_barber(current_user: User = Depends(get_current_user)) -> User:
    """Require barber role"""
    if current_user.role != UserRole.BARBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Barber access required"
        )
    return current_user


async def require_client(current_user: User = Depends(get_current_user)) -> User:
    """Require client role"""
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client access required"
        )
    return current_user


async def require_authenticated(current_user: User = Depends(get_current_user)) -> User:
    """Simply require authenticated user (any role)"""
    return current_user


# ===== SERVICE DEPENDENCIES =====

async def get_barber_service():
    """Get BarberService instance"""
    from app.repositories import (
        BarberRepository,
        BarberScheduleRepository,
        SpecialHourRepository,
        HolidayRepository,
        AppointmentRepository,
    )
    from app.services import BarberService
    
    db = get_db()
    
    return BarberService(
        BarberRepository(db),
        BarberScheduleRepository(db),
        SpecialHourRepository(db),
        HolidayRepository(db),
        AppointmentRepository(db),
    )


async def get_client_service():
    """Get ClientService instance"""
    from app.repositories import (
        ClientRepository,
        AppointmentRepository,
    )
    from app.services import ClientService
    
    db = get_db()
    
    return ClientService(
        ClientRepository(db),
        AppointmentRepository(db),
    )


