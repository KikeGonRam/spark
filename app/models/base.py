"""
Base model for MongoDB documents.
All models inherit from this to ensure consistent timestamp handling.
"""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class BaseDocument(BaseModel):
    """Base class for all MongoDB documents."""
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def dict(self, **kwargs):
        """Convert to dict, handling ObjectId properly."""
        d = super().model_dump(**kwargs)
        if self.id:
            d["_id"] = self.id
            d.pop("id", None)
        return d


class TimestampModel(BaseModel):
    """Mixin for models with timestamp fields."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
