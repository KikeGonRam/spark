"""
MongoDB Connection Management
Handles MongoDB connection using Motor (async driver), pooling, and lifecycle
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError
from app.config import settings

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """MongoDB connection manager using Motor for async operations"""
    
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """
        Connect to MongoDB using Motor and return database instance
        
        Returns:
            AsyncIOMotorDatabase instance
            
        Raises:
            ServerSelectionTimeoutError: If connection fails
        """
        if cls._client is not None:
            logger.info("Using existing MongoDB connection")
            return cls._db
            
        try:
            logger.info(f"Connecting to MongoDB: {settings.MONGO_HOST}")
            
            # Build MongoDB URI
            uri = settings.MONGO_HOST
            
            # Add credentials if provided
            if settings.MONGO_USER and settings.MONGO_PASSWORD:
                # Parse the URI and insert credentials
                if "mongodb://" in uri:
                    uri = uri.replace(
                        "mongodb://",
                        f"mongodb://{settings.MONGO_USER}:{settings.MONGO_PASSWORD}@"
                    )
                elif "mongodb+srv://" in uri:
                    uri = uri.replace(
                        "mongodb+srv://",
                        f"mongodb+srv://{settings.MONGO_USER}:{settings.MONGO_PASSWORD}@"
                    )
            
            # Create Motor async MongoDB client
            cls._client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=settings.MONGO_TIMEOUT,
                maxPoolSize=settings.MONGO_POOL_SIZE,
                minPoolSize=settings.MONGO_MIN_POOL_SIZE,
                connectTimeoutMS=settings.MONGO_TIMEOUT,
                socketTimeoutMS=settings.MONGO_TIMEOUT,
            )
            
            # Verify connection
            await cls._client.admin.command('ping')
            
            # Get database instance
            cls._db = cls._client[settings.MONGO_DB]
            
            logger.info(f"✓ Connected to MongoDB database: {settings.MONGO_DB}")
            return cls._db
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"✗ Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"✗ Unexpected error connecting to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls) -> None:
        """Disconnect from MongoDB"""
        if cls._client is not None:
            try:
                cls._client.close()
                logger.info("✓ Disconnected from MongoDB")
            except Exception as e:
                logger.error(f"Error disconnecting from MongoDB: {e}")
            finally:
                cls._client = None
                cls._db = None
    
    @classmethod
    def get_db(cls) -> Optional[AsyncIOMotorDatabase]:
        """Get current database instance"""
        if cls._db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return cls._db
    
    @classmethod
    async def health_check(cls) -> bool:
        """
        Check MongoDB health/availability
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if cls._client is None:
                return False
            await cls._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False


# Global database dependency function
async def get_db():
    """
    FastAPI dependency to get database instance
    
    Returns:
        MongoDB database instance
    """
    db = MongoDBConnection.get_db()
    if db is None:
        raise RuntimeError("Database not initialized")
    return db
