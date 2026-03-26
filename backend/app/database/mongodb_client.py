"""
MongoDB Client
Handle connection to local MongoDB for storing:
- Users
- Notebooks
- Documents metadata
"""

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional
from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

settings = get_settings()


class MongoDBClient:
    """MongoDB client for local database operations"""
    
    _instance: Optional['MongoDBClient'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> Database:
        """Connect to MongoDB"""
        if self._db is not None:
            return self._db
        
        try:
            self._client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[settings.MONGODB_DB_NAME]
            
            # Create indexes
            self._create_indexes()
            
            logger.info(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
            return self._db
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Create necessary indexes for collections"""
        # Users collection
        self._db.users.create_index("email", unique=True)
        self._db.users.create_index("username", unique=True)
        
        # Notebooks collection
        self._db.notebooks.create_index("user_id")
        self._db.notebooks.create_index([("user_id", 1), ("created_at", -1)])
        
        # Documents collection
        self._db.documents.create_index("notebook_id")
        self._db.documents.create_index([("notebook_id", 1), ("created_at", -1)])
        
        logger.info("MongoDB indexes created")
    
    @property
    def db(self) -> Database:
        """Get database instance"""
        if self._db is None:
            self.connect()
        return self._db
    
    @property
    def users(self) -> Collection:
        """Get users collection"""
        return self.db.users
    
    @property
    def notebooks(self) -> Collection:
        """Get notebooks collection"""
        return self.db.notebooks
    
    @property
    def documents(self) -> Collection:
        """Get documents collection"""
        return self.db.documents
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed")


# Global instance
mongodb_client = MongoDBClient()


def get_mongodb() -> MongoDBClient:
    """Get MongoDB client instance"""
    return mongodb_client
