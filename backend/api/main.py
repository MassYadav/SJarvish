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
    """Public endpoint to verify the API and memory connections are alive."""
    return {
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "redis_connected": db.redis_client is not None,
        "chroma_connected": db.chroma_client is not None,
        "version": "0.1.0"
    }

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns a JWT token.
    For development, we use a hardcoded admin password.
    """
    # In a production environment, this would check a database hash
    # For our local AI OS, we verify against the master password
    if form_data.password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate the encrypted token payload
    access_token = create_access_token(data={"sub": form_data.username})
    
    return {"access_token": access_token, "token_type": "bearer"}

# ---------------------------------------------------------
# PROTECTED ROUTES
# ---------------------------------------------------------
@app.get("/api/v1/system/status")
async def secure_system_status(current_user: dict = Depends(get_current_user)):
    """
    A protected route. If you don't pass a valid JWT token in the header, 
    FastAPI will automatically block the request and return a 401 error.
    """
    return {
        "message": "Access Granted",
        "user": current_user["username"],
        "system_state": "All core modules online and secure."
    }

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )