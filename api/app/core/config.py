"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Music Charts Tracking API"
    VERSION: str = "1.0.0"

    # Security
    SECRET_KEY: str = "default-secret-key-for-development-only-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database URLs
    DATABASE_URL: str = "postgresql://musicuser:musicpass@postgres:5432/musicdb"
    MONGODB_URL: str = "mongodb://mongouser:mongopass@mongodb:27017/musiccharts?authSource=admin"
    TIMESCALE_URL: Optional[str] = None  # TimescaleDB
    REDIS_URL: str = "redis://redis:6379/0"

    # CORS (stored as comma-separated string, parsed in main.py)
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8501"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 3600  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()

