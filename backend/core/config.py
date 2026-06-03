import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    # Core API
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    SECRET_KEY: SecretStr

    # Databases
    REDIS_URL: str
    CHROMA_DB_URL: str
    SQLITE_DB_PATH: str

    # AI OS Frontend
    NEXT_PUBLIC_API_URL: str

    # LLM Keys (Optional, system will route to available ones)
    GEMINI_API_KEY: Optional[SecretStr] = None
    OPENAI_API_KEY: Optional[SecretStr] = None
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    GROQ_API_KEY: Optional[SecretStr] = None
    DEEPSEEK_API_KEY: Optional[SecretStr] = None
    OPENROUTER_API_KEY: Optional[SecretStr] = None

    # LiveKit Voice
    LIVEKIT_URL: Optional[str] = None
    LIVEKIT_API_KEY: Optional[SecretStr] = None
    LIVEKIT_API_SECRET: Optional[SecretStr] = None

    # Load from the .env file in the root directory
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate the settings so it can be imported across the app
settings = Settings()