"""
Routes - API Endpoints
Contiene todos los endpoints REST de la aplicación.
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .appointments import router as appointments_router
from .barbers import router as barbers_router
from .clients import router as clients_router
from .payments import router as payments_router
from .reports import router as reports_router
from .dashboard import router as dashboard_router
from .analytics import router as analytics_router
from .services import router as services_router
from .settings import router as settings_router
from .logs import router as logs_router
from .notifications import router as notifications_router
from .social import router as social_router
from .predictions import router as predictions_router
from . import users, profile, portfolio, admin_dashboard

# Crear router principal
api_router = APIRouter(prefix="/api")

# Incluir todos los sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(appointments_router, prefix="/appointments", tags=["appointments"])
api_router.include_router(barbers_router, prefix="/barbers", tags=["barbers"])
api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(services_router, prefix="/services", tags=["services"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(logs_router, prefix="/logs", tags=["logs"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(social_router, prefix="/social", tags=["social"])
api_router.include_router(predictions_router, prefix="/predictions", tags=["predictions"])

__all__ = ["api_router"]
