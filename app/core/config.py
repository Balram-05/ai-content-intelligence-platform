from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration model loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application Settings
    APP_NAME: str = "AI Personal Branding & Content Intelligence Platform"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # FastAPI Server Configuration
    FASTAPI_HOST: str = "127.0.0.1"
    FASTAPI_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "content_intelligence_db"
    MONGODB_MAX_CONNECTIONS: int = 10
    MONGODB_MIN_CONNECTIONS: int = 1
    MONGODB_CONNECT_TIMEOUT_MS: int = 2000


@lru_cache
def get_settings() -> Settings:
    """Returns a cached instance of the settings."""
    return Settings()
