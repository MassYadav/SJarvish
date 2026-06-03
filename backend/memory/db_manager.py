import logging
import redis.asyncio as redis
import chromadb
from chromadb.config import Settings as ChromaSettings
from core.config import settings

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Singleton connection manager for AI OS databases.
    Maintains persistent connections to Redis and ChromaDB.
    """
    def __init__(self):
        self.redis_client = None
        self.chroma_client = None
        # SQLite path is just a string reference used by LangGraph later
        self.sqlite_path = settings.SQLITE_DB_PATH

    async def connect(self):
        """Establish connections to all external databases."""
        # 1. Connect to Redis (Async)
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True
            )
            # Ping to verify connection
            await self.redis_client.ping()
            logger.info("✅ Successfully connected to Redis.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise e

        # 2. Connect to ChromaDB (Sync HTTP Client)
        try:
            # Parse the host and port from the URL in .env (e.g., http://localhost:8000)
            url_parts = settings.CHROMA_DB_URL.replace("http://", "").split(":")
            host = url_parts[0]
            port = int(url_parts[1]) if len(url_parts) > 1 else 8000

            self.chroma_client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=ChromaSettings(allow_reset=True)
            )
            # Heartbeat to verify connection
            self.chroma_client.heartbeat()
            logger.info("✅ Successfully connected to ChromaDB.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to ChromaDB: {e}")
            raise e

    async def disconnect(self):
        """Gracefully close connections during shutdown."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed.")

# Create a single global instance to be imported across the app
db = DatabaseManager()