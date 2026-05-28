"""
Base Repository - Generic CRUD operations for MongoDB.
All specific repositories inherit from this base class.
"""
from typing import List, Optional, TypeVar, Generic, Type
from datetime import datetime
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.models.base import BaseDocument

T = TypeVar('T', bound=BaseDocument)


class BaseRepository(Generic[T]):
    """
    Generic repository for CRUD operations on MongoDB.
    
    Type parameter T represents the model class.
    All methods are async to work with Motor (async MongoDB driver).
    """
    
    def __init__(self, db: AsyncIOMotorDatabase, model: Type[T], collection_name: str):
        """
        Initialize repository.
        
        Args:
            db: Motor AsyncIOMotorDatabase instance
            model: Pydantic model class
            collection_name: MongoDB collection name
        """
        self.db = db
        self.model = model
        self.collection: AsyncIOMotorCollection = db[collection_name]
    
    async def create(self, obj: T) -> str:
        """
        Create a new document.
        
        Args:
            obj: Model instance to create
            
        Returns:
            Inserted document ID
            
        Raises:
            DuplicateKeyError: If unique field already exists
            PyMongoError: For other database errors
        """
        try:
            doc = obj.dict(by_alias=True)
            doc.pop('_id', None)  # Remove id if None
            result = await self.collection.insert_one(doc)
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            raise DuplicateKeyError(f"Duplicate key error: {e}")
        except PyMongoError as e:
            raise PyMongoError(f"Database error: {e}")
    
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find document by ID.
        
        Args:
            id: Document ObjectId as string
            
        Returns:
            Model instance or None if not found
        """
        try:
            doc = await self.collection.find_one({'_id': ObjectId(id)})
            if doc:
                doc['_id'] = str(doc['_id'])
                return self.model(**doc)
            return None
        except Exception:
            return None
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Find all documents with pagination.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum documents to return
            
        Returns:
            List of model instances
        """
        cursor = self.collection.find().skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model(**{**doc, '_id': str(doc['_id'])}) for doc in docs]
    
    async def find_one(self, query: dict) -> Optional[T]:
        """
        Find one document matching query.
        
        Args:
            query: MongoDB query dict
            
        Returns:
            Model instance or None if not found
        """
        doc = await self.collection.find_one(query)
        if doc:
            # Convert ObjectId to string for _id field
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            return self.model(**doc)
        return None
    
    async def find(self, query: dict, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Find documents matching query with pagination.
        
        Args:
            query: MongoDB query dict
            skip: Number of documents to skip
            limit: Maximum documents to return
            
        Returns:
            List of model instances
        """
        cursor = self.collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self.model(**{**doc, '_id': str(doc['_id'])}) for doc in docs]
    
    async def count(self, query: dict = None) -> int:
        """
        Count documents matching query.
        
        Args:
            query: MongoDB query dict (None for all)
            
        Returns:
            Count of documents
        """
        if query is None:
            query = {}
        return await self.collection.count_documents(query)
    
    async def update(self, id: str, obj: T) -> Optional[T]:
        """
        Update document by ID.
        
        Args:
            id: Document ObjectId as string
            obj: Model instance with updated values
            
        Returns:
            True if updated, False if not found
        """
        try:
            doc = obj.dict(by_alias=True)
            doc.pop('_id', None)
            doc['updated_at'] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {'_id': ObjectId(id)},
                {'$set': doc}
            )
            if result.matched_count == 0:
                return None
            updated = await self.collection.find_one({'_id': ObjectId(id)})
            if updated:
                updated['_id'] = str(updated['_id'])
                return self.model(**updated)
            return None
        except Exception as e:
            raise PyMongoError(f"Update error: {e}")
    
    async def update_partial(self, id: str, data: dict) -> Optional[T]:
        """
        Partial update (only specified fields).
        
        Args:
            id: Document ObjectId as string
            data: Dict with fields to update
            
        Returns:
            True if updated, False if not found
        """
        try:
            data['updated_at'] = datetime.utcnow()
            result = await self.collection.update_one(
                {'_id': ObjectId(id)},
                {'$set': data}
            )
            if result.matched_count == 0:
                return None
            updated = await self.collection.find_one({'_id': ObjectId(id)})
            if updated:
                updated['_id'] = str(updated['_id'])
                return self.model(**updated)
            return None
        except Exception as e:
            raise PyMongoError(f"Update error: {e}")
    
    async def delete(self, id: str) -> bool:
        """
        Delete document by ID.
        
        Args:
            id: Document ObjectId as string
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({'_id': ObjectId(id)})
        return result.deleted_count > 0
    
    async def delete_many(self, query: dict) -> int:
        """
        Delete multiple documents matching query.
        
        Args:
            query: MongoDB query dict
            
        Returns:
            Count of deleted documents
        """
        result = await self.collection.delete_many(query)
        return result.deleted_count
    
    async def create_index(self, key: str, unique: bool = False, ascending: bool = True):
        """
        Create index on collection.
        
        Args:
            key: Field name to index
            unique: Whether index should be unique
            ascending: Sort direction (True = ascending)
        """
        direction = ASCENDING if ascending else DESCENDING
        await self.collection.create_index(
            [(key, direction)],
            unique=unique
        )
    
    async def exists(self, query: dict) -> bool:
        """
        Check if document matching query exists.
        
        Args:
            query: MongoDB query dict
            
        Returns:
            True if exists, False otherwise
        """
        doc = await self.collection.find_one(query)
        return doc is not None
    
    async def bulk_insert(self, objects: List[T]) -> List[str]:
        """
        Insert multiple documents.
        
        Args:
            objects: List of model instances
            
        Returns:
            List of inserted document IDs
        """
        docs = [obj.dict(by_alias=True) for obj in objects]
        result = await self.collection.insert_many(docs)
        return [str(id) for id in result.inserted_ids]
    
    async def drop(self):
        """Drop entire collection (use with caution!)."""
        await self.collection.drop()
