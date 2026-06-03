import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from memory.db_manager import db

logger = logging.getLogger(__name__)

class HybridMemorySystem:
    """
    Production abstraction layer for managing AI OS multi-tiered cognition.
    Controls short-term sequential sliding caches via Redis and long-term 
    vectorized episodic memory fabrics using ChromaDB.
    """
    def __init__(self):
        self.vector_collection_name = "ai_os_episodic_cortex"

    def _get_vector_collection(self):
        """Retrieves or initializes the persistent deep vector collection layer."""
        if not db.chroma_client:
            raise RuntimeError("Cortex Pipeline Failure: ChromaDB client is offline.")
        return db.chroma_client.get_or_create_collection(name=self.vector_collection_name)

    # ---------------------------------------------------------
    # SHORT-TERM WORKING MEMORY OPERATORS (REDIS)
    # ---------------------------------------------------------
    async def store_chat_message(self, session_id: str, role: str, content: str, max_window: int = 15):
        """Pushes an execution conversation frame directly into the sliding Redis cache window."""
        if not db.redis_client:
            logger.warning("Short-term execution skipped: Redis server is disconnected.")
            return

        key = f"session:{session_id}:context"
        frame_payload = json.dumps({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        try:
            # Append message onto chronological list structure
            db.redis_client.rpush(key, frame_payload)
            # Slice sliding index window to drop oldest messages beyond max_window depth
            db.redis_client.ltrim(key, -max_window, -1)
            # Enforce automatic cleanup of stale sessions after 24 hours of inactivity
            db.redis_client.expire(key, 86400)
        except Exception as e:
            logger.error(f"Failed to append execution frame to short-term cache: {e}")

    async def retrieve_context_window(self, session_id: str) -> List[Dict[str, str]]:
        """Extracts the sequential working conversation buffer for LLM context parsing."""
        if not db.redis_client:
            return []

        key = f"session:{session_id}:context"
        try:
            raw_frames = db.redis_client.lrange(key, 0, -1)
            context_history = []
            
            for frame in raw_frames:
                parsed = json.loads(frame)
                context_history.append({
                    "role": parsed["role"],
                    "content": parsed["content"]
                })
            return context_history
        except Exception as e:
            logger.error(f"Failed to extract contextual short-term window: {e}")
            return []

    # ---------------------------------------------------------
    # LONG-TERM EPISODIC COGNITION OPERATORS (CHROMADB)
    # ---------------------------------------------------------
    async def commit_to_long_term(self, facts: str, metadata: Dict[str, Any]):
        """Vectorizes and commits permanent architectural or context facts to the database storage layer."""
        try:
            collection = self._get_vector_collection()
            memory_uuid = str(uuid.uuid4())
            
            # Enforce standardized operational audit timelines
            metadata["created_at"] = datetime.now(timezone.utc).isoformat()

            # Chroma internally hashes items via sentence-transformers when running raw text arrays
            collection.add(
                documents=[facts],
                metadatas=[metadata],
                ids=[memory_uuid]
            )
            logger.info(f"🎯 Facts consolidated to long-term memory fabric. ID reference: {memory_uuid}")
            return memory_uuid
        except Exception as e:
            logger.error(f"Failed to commit episodic state parameters to long-term memory: {e}")
            raise e

    async def recall_semantic_memories(self, inquiry: str, score_threshold: float = 1.5, limit: int = 3) -> List[Dict[str, Any]]:
        """Queries the vector database using distance matrices to recall relative system memories."""
        try:
            collection = self._get_vector_collection()
            query_results = collection.query(
                query_texts=[inquiry],
                n_results=limit
            )

            recalled_memories = []
            if query_results and query_results.get("documents"):
                documents = query_results["documents"][0]
                metadatas = query_results["metadatas"][0]
                distances = query_results["distances"][0] if "distances" in query_results else [0.0] * len(documents)

                for text, meta, distance in zip(documents, metadatas, distances):
                    # Filter out irrelevant semantic echoes based on distance metrics
                    if distance <= score_threshold:
                        recalled_memories.append({
                            "facts": text,
                            "metadata": meta,
                            "distance_score": float(distance)
                        })
            return recalled_memories
        except Exception as e:
            logger.error(f"Semantic memory compilation failed: {e}")
            return []

# Expose uniform access instance for immediate consumption
memory_vault = HybridMemorySystem()