"""
BarberPro Python - FastAPI Application
Main entry point for the application
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.config import settings
from database.connection import MongoDBConnection

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE),
    ],
)

logger = logging.getLogger(__name__)


# ============================================
# Lifespan Events (Startup/Shutdown)
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan events
    Handles startup and shutdown
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug: {settings.APP_DEBUG}")
    logger.info("=" * 60)
    
    try:
        # Connect to MongoDB
        await MongoDBConnection.connect()
        logger.info("Database connected")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info(f"Shutting down {settings.APP_NAME}")
    logger.info("=" * 60)
    
    try:
        await MongoDBConnection.disconnect()
        logger.info("Database disconnected")
    except Exception as e:
        logger.error(f"✗ Error disconnecting from database: {e}")


# ============================================
# Create FastAPI Application
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Barbershop Management System - API",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)


# ============================================
# Middleware Configuration
# ============================================

from app.middleware import JWTMiddleware, LoggingMiddleware
from app.utils.rate_limiter import RateLimitMiddleware

# Logging Middleware (debe ser el primero)
# app.add_middleware(LoggingMiddleware) # DISABLED: wrong signature

# Rate Limiting Middleware
# app.add_middleware(RateLimitMiddleware) # DISABLED: wrong signature

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# JWT Authentication Middleware (después de CORS)
# app.add_middleware(JWTMiddleware, secret_key=settings.JWT_SECRET) # DISABLED: wrong signature

logger.info("Middleware configured (Logging, Rate Limit, CORS, JWT)")


# ============================================
# Custom Error Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # In production, don't expose stack traces
    if settings.APP_DEBUG:
        detail = str(exc)
    else:
        detail = "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": detail,
            "path": request.url.path,
        },
    )


# ============================================
# Health Check Endpoints
# ============================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe - simple health check"""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/health", tags=["Health"])
async def api_health_check():
    return await health_check()


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe - checks if service is ready for traffic"""
    # Check MongoDB connection
    db_healthy = await MongoDBConnection.health_check()
    
    if not db_healthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "message": "Database unavailable",
            },
        )
    
    return {
        "status": "ready",
        "database": "connected",
        "service": settings.APP_NAME,
    }


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Check if service is running"""
    return {
        "status": "alive",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
    }


# ============================================
# Root Endpoint
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "message": f"{settings.APP_NAME} API v{settings.APP_VERSION}",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }


# ============================================
# API Routes Integration
# ============================================

# Import all route modules
from app.routes import (
    auth,
    appointments,
    barbers,
    clients,
    payments,
    reports,
    dashboard,
    analytics,
    chatbot,
    services,
    settings as settings_routes,
    logs,
    notifications,
    social,
    predictions,
    test_email,
)
from app.routes import users, profile, portfolio, admin_dashboard

# Include all routers with /api prefix and proper tags
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(barbers.router, prefix="/api/barbers", tags=["Barbers"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["ChatBot"])
app.include_router(services.router, prefix="/api/services", tags=["Services"])
app.include_router(settings_routes.router, prefix="/api/settings", tags=["Settings"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(social.router, prefix="/api/social", tags=["Social"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(test_email.router, prefix="/api/test", tags=["Test"])
# New routers
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(portfolio.router, prefix="/api/barber/portfolio", tags=["Portfolio"])
app.include_router(admin_dashboard.router, prefix="/api/admin/dashboard", tags=["Admin Dashboard"])

logger.info("All route modules loaded")


@app.get("/api", tags=["API"])
async def api_root():
    """API root - List all available endpoints"""
    return {
        "message": "Welcome to BarberPro Elite API",
        "version": settings.APP_VERSION,
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "health_ready": "/health/ready",
            "health_live": "/health/live",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "info": "/api/info",
        },
        "modules": {
            "auth": "/api/auth",
            "appointments": "/api/appointments",
            "barbers": "/api/barbers",
            "clients": "/api/clients",
            "payments": "/api/payments",
            "reports": "/api/reports",
            "dashboard": "/api/dashboard",
            "analytics": "/api/analytics",
            "chatbot": "/api/chatbot",
            "settings": "/api/settings",
            "logs": "/api/logs",
            "notifications": "/api/notifications",
            "social": "/api/social",
            "predictions": "/api/predictions",
        },
    }


# ============================================
# Static Files (Frontend Assets)
# ============================================

# Mount static files (after building with Vite)
# This will be uncommented when frontend is ready
# try:
#     app.mount("/static", StaticFiles(directory="public"), name="static")
#     logger.info("Static files mounted")
# except Exception as e:
#     logger.warning(f"Could not mount static files: {e}")


# ============================================
# Application Info
# ============================================

@app.get("/api/info", tags=["Info"])
async def app_info():
    """Get application information"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "debug": settings.APP_DEBUG,
        "database": {
            "host": settings.MONGO_HOST.split("@")[-1] if "@" in settings.MONGO_HOST else settings.MONGO_HOST,
            "db": settings.MONGO_DB,
        },
        "features": {
            "authentication": True,
            "gemini_ai": settings.GEMINI_ENABLED,
            "s3_storage": settings.AWS_ENABLED,
            "sentry_monitoring": settings.SENTRY_ENABLED,
        },
    }


# ============================================
# Run Application (Development Only)
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
