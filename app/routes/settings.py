"""
Settings Routes - Configuración general de la barbería
Endpoints: /api/settings/*
"""

from fastapi import APIRouter, Depends

from app.config import settings

router = APIRouter()


@router.get("/", response_model=dict)
async def get_settings_summary():
    return {
        "success": True,
        "data": {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "app_env": settings.APP_ENV,
            "app_debug": settings.APP_DEBUG,
            "app_url": settings.APP_URL,
            "default_page_size": settings.DEFAULT_PAGE_SIZE,
            "max_page_size": settings.MAX_PAGE_SIZE,
            "rate_limit_enabled": settings.RATE_LIMIT_ENABLED,
        },
    }

