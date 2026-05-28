"""
BarberPro Python - Application Configuration
Handles all environment variables and application settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings with Environment Variables"""
    
    # ============================================
    # Application Settings
    # ============================================
    APP_NAME: str = "BarberPro"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "True").lower() == "true"
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # ============================================
    # Server Settings
    # ============================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = APP_ENV == "development"
    WORKERS: int = 4 if APP_ENV == "production" else 1
    
    # ============================================
    # Database - MongoDB
    # ============================================
    MONGO_HOST: str = os.getenv("MONGO_HOST", "mongodb://localhost:27017")
    MONGO_DB: str = os.getenv("MONGO_DB", "barberpro")
    MONGO_USER: Optional[str] = os.getenv("MONGO_USER", None)
    MONGO_PASSWORD: Optional[str] = os.getenv("MONGO_PASSWORD", None)
    MONGO_TIMEOUT: int = int(os.getenv("MONGO_TIMEOUT", "5000"))
    MONGO_POOL_SIZE: int = 20
    MONGO_MIN_POOL_SIZE: int = 10
    
    # ============================================
    # Cache - Redis
    # ============================================
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_ENABLED: bool = True
    
    # ============================================
    # JWT Configuration
    # ============================================
    JWT_SECRET: str = os.getenv("JWT_SECRET", "jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
    JWT_REFRESH_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "30"))
    
    # ============================================
    # Email Configuration
    # ============================================
    MAIL_DRIVER: str = os.getenv("MAIL_DRIVER", "smtp")
    MAIL_HOST: str = os.getenv("MAIL_HOST", "mailpit")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@barberpro.local")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "BarberPro")
    MAIL_USERNAME: Optional[str] = os.getenv("MAIL_USERNAME", None)
    MAIL_PASSWORD: Optional[str] = os.getenv("MAIL_PASSWORD", None)
    
    # ============================================
    # Google Gemini API (IA)
    # ============================================
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = "gemini-pro"
    GEMINI_ENABLED: bool = bool(os.getenv("GEMINI_API_KEY"))
    
    # ============================================
    # AWS S3 (Optional - File Storage)
    # ============================================
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_DEFAULT_REGION: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    AWS_BUCKET: Optional[str] = os.getenv("AWS_BUCKET", None)
    AWS_URL: Optional[str] = os.getenv("AWS_URL", None)
    AWS_ENABLED: bool = bool(os.getenv("AWS_ACCESS_KEY_ID"))
    
    # ============================================
    # Sentry (Error Tracking)
    # ============================================
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    SENTRY_ENABLED: bool = bool(os.getenv("SENTRY_DSN"))
    
    # ============================================
    # Logging
    # ============================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/barberpro.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ============================================
    # CORS Configuration
    # ============================================
    CORS_ORIGINS: list = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # ============================================
    # Rate Limiting
    # ============================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # ============================================
    # Pagination
    # ============================================
    DEFAULT_PAGE_SIZE: int = 15
    MAX_PAGE_SIZE: int = 100
    
    # ============================================
    # Security
    # ============================================
    SECURE_HSTS_SECONDS: int = 31536000
    SECURE_SSL_REDIRECT: bool = APP_ENV == "production"
    SESSION_COOKIE_SECURE: bool = APP_ENV == "production"
    CSRF_COOKIE_SECURE: bool = APP_ENV == "production"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Export settings for easy import
settings = get_settings()

# ============================================
# Environment-specific configurations
# ============================================

if settings.APP_ENV == "production":
    settings.APP_DEBUG = False
    settings.RELOAD = False
    settings.WORKERS = 4

if settings.APP_ENV == "testing":
    settings.MONGO_DB = "barberpro_test"
    settings.REDIS_DB = 1
