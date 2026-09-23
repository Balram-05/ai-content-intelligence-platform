from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import Settings, get_settings
from app.core.logging import logger


class Database:
    """MongoDB connection manager using Motor async driver."""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Initialize MongoDB connection pool."""
        logger.info(f"Connecting to MongoDB at {self.settings.MONGODB_URL}...")
        try:
            self.client = AsyncIOMotorClient(
                self.settings.MONGODB_URL,
                maxPoolSize=self.settings.MONGODB_MAX_CONNECTIONS,
                minPoolSize=self.settings.MONGODB_MIN_CONNECTIONS,
                serverSelectionTimeoutMS=self.settings.MONGODB_CONNECT_TIMEOUT_MS
            )
            self.db = self.client[self.settings.MONGODB_DB_NAME]
            # Perform lightweight ping on startup
            await self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB database: '{self.settings.MONGODB_DB_NAME}'")
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.warning(f"MongoDB connection failed during startup initialization: {e}")
            # Do not raise here so application can start even if DB is temporarily down,
            # but health check will report DB as unavailable.

    async def disconnect(self) -> None:
        """Close MongoDB connection pool."""
        if self.client:
            logger.info("Closing MongoDB connection pool...")
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection pool closed.")

    async def check_health(self) -> Dict[str, Any]:
        """
        Check database connection status by issuing a ping command.
        Returns explicit status details without masking failures.
        """
        if not self.client:
            return {
                "connected": False,
                "database_name": self.settings.MONGODB_DB_NAME,
                "error": "MongoDB client is not initialized"
            }
        
        try:
            # Issue admin command ping with timeout
            await self.client.admin.command('ping')
            return {
                "connected": True,
                "database_name": self.settings.MONGODB_DB_NAME,
                "error": None
            }
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
            logger.error(f"MongoDB health check ping failed: {e}")
            return {
                "connected": False,
                "database_name": self.settings.MONGODB_DB_NAME,
                "error": str(e)
            }


# Global database instance
db_instance = Database()
