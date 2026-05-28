"""
User model - Core user entity for the system.
Represents users with different roles: Admin, Barber, Client.
"""
from typing import Optional, List
from enum import Enum
from datetime import datetime
from pydantic import Field, EmailStr, field_validator, AliasChoices
from app.models.base import BaseDocument


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    BARBER = "barber"
    CLIENT = "client"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    PENDING = "pending"


class User(BaseDocument):
    """
    User model.
    
    Attributes:
        id: MongoDB ObjectId as string
        name: Full name
        email: Unique email address
        password: Hashed password (bcrypt)
        phone: Phone number with country code
        role: User role (admin, barber, client)
        status: User status (active, inactive, banned, pending)
        avatar: URL to user avatar image
        bio: Short biography
        is_email_verified: Email verification flag
        last_login: Last login timestamp
        metadata: Additional user data (flexible)
    """
    
    name: Optional[str] = Field(None, max_length=100)
    email: str = Field(..., unique=True)
    password: Optional[str] = Field(None, min_length=8, validation_alias=AliasChoices("password", "password_hash"))
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = Field(default=UserRole.CLIENT)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    avatar: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    is_email_verified: bool = Field(default=False)
    last_login: Optional[datetime] = None
    metadata: Optional[dict] = Field(default_factory=dict)
    
    class Config:
        collection = "users"
    
    @field_validator('email')
    @classmethod
    def email_must_be_valid(cls, v):
        """Validate email format."""
        return v.lower().strip()
    
    @field_validator('name')
    @classmethod
    def name_must_not_be_blank(cls, v):
        """Validate name is not blank."""
        return v.strip() if v else v
    
    def to_dict_safe(self) -> dict:
        """Convert to dict excluding sensitive fields."""
        d = self.dict()
        d.pop("password", None)
        return d


class UserCreate(BaseDocument):
    """Schema for creating a new user."""
    
    name: str = Field(..., min_length=2, max_length=100, validation_alias=AliasChoices("name", "full_name"))
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    role: UserRole = Field(default=UserRole.CLIENT)


class UserLogin(BaseDocument):
    """Schema for user login."""
    
    email: EmailStr
    password: str


class UserUpdate(BaseDocument):
    """Schema for updating user."""
    
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)
    status: Optional[UserStatus] = None


class UserResponse(BaseDocument):
    """Schema for user response (excluding password)."""
    
    name: str
    email: str
    phone: Optional[str]
    role: UserRole
    status: UserStatus
    avatar: Optional[str]
    bio: Optional[str]
    is_email_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
