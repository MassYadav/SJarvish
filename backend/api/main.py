import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn

# Ensure the backend directory is in the Python path for absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from memory.db_manager import db
from core.security.auth import create_access_token, get_current_user
from llm.litellm_router.router import llm_router
from memory.service import memory_vault

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Booting up AI OS Neural Center...")
    try:
        await db.connect()
        logger.info("✅ Database connections verified.")
    except Exception as e:
        logger.error(f"❌ Critical Failure during database connection: {e}")
        raise e
    yield
    logger.info("🛑 Shutting down AI OS Neural Center...")
    await db.disconnect()
    logger.info("✅ Graceful shutdown complete.")

app = FastAPI(
    title="AI OS Core API",
    description="Neural Center for the AI Operating System",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# PUBLIC ROUTES
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "redis_connected": db.redis_client is not None,
        "chroma_connected": db.chroma_client is not None,
        "version": "0.1.0"
    }

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------------------------------------
# PROTECTED ROUTES
# ---------------------------------------------------------
@app.get("/api/v1/system/status")
async def secure_system_status(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Access Granted",
        "user": current_user["username"],
        "system_state": "All core modules online and secure."
    }

@app.post("/api/v1/llm/test-route")
async def test_llm_routing(prompt: str, current_user: dict = Depends(get_current_user)):
    """Validates the high-availability failover chain execution engine."""
    payload = [{"role": "user", "content": prompt}]
    result = await llm_router.generate_reply(messages=payload)
    return result

@app.post("/api/v1/memory/short-term")
async def add_short_term_memory(session_id: str, role: str, content: str, current_user: dict = Depends(get_current_user)):
    """Appends sequential records to high-speed working cache storage."""
    await memory_vault.store_chat_message(session_id=session_id, role=role, content=content)
    return {"status": "success", "message": "Frame appended to short term history buffer."}

@app.get("/api/v1/memory/short-term/{session_id}")
async def get_short_term_memory(session_id: str, current_user: dict = Depends(get_current_user)):
    """Fetches the sliding history window array from Redis."""
    history = await memory_vault.retrieve_context_window(session_id=session_id)
    return {"session_id": session_id, "history": history}

@app.post("/api/v1/memory/long-term")
async def add_long_term_memory(facts: str, category: str, current_user: dict = Depends(get_current_user)):
    """Indexes deep factual structures inside the persistent vector cortex."""
    uuid_ref = await memory_vault.commit_to_long_term(facts=facts, metadata={"category": category})
    return {"status": "success", "memory_id": uuid_ref}

@app.get("/api/v1/memory/long-term/search")
async def search_long_term_memory(query: str, current_user: dict = Depends(get_current_user)):
    """Executes high-performance distance query logic across semantic memories."""
    matches = await memory_vault.recall_semantic_memories(inquiry=query)
    return {"query": query, "matches": matches}

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )