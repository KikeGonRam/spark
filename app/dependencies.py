"""
Dependencies - Inyección de dependencias de FastAPI.

Proporciona funciones que FastAPI llama automáticamente
para cada solicitud, inyectando servicios y contexto.
"""

from fastapi import Depends, HTTPException, status
from starlette.requests import Request
from typing import Optional, AsyncGenerator
from datetime import datetime, timedelta
import jwt
from functools import lru_cache

from app.config import Settings
from app.exceptions import (
    UnauthorizedError,
    ForbiddenError,
    DatabaseError,
)


# ===== CONFIGURATION =====

@lru_cache()
def get_settings() -> Settings:
    """
    Obtener configuración de la aplicación (singleton).

    Se cachea automáticamente en memoria.
    """
    return Settings()


# ===== DATABASE CONNECTION =====

async def get_database() -> AsyncGenerator:
    """
    Obtener cliente de conexión a MongoDB.

    **Uso en rutas:**
    ```python
    @router.get("/items")
    async def list_items(db = Depends(get_database)):
        items = await db.items.find().to_list(length=10)
        return items
    ```

    **Note:** En producción, usar connection pool.
    """
    from motor.motor_asyncio import AsyncIOMotorClient

    settings = get_settings()

    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Verificar conexión
        await client.admin.command("ping")
        yield client
    except Exception as e:
        raise DatabaseError("Conexión MongoDB", str(e))
    finally:
        client.close()


# ===== AUTHENTICATION =====


async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Obtener usuario actual desde JWT token.

    **Validaciones:**
    - Token presente en header Authorization
    - Token no expirado
    - Firma válida
    - Payload contiene user_id

    **Usa en rutas protegidas:**
    ```python
    @router.get("/profile")
    async def get_profile(current_user = Depends(get_current_user)):
        return current_user
    ```

    **Respuesta en caso de error:**
    - 401 Unauthorized: Sin token o token inválido
    - 403 Forbidden: Token expirado

    **Token formato:**
    ```
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        # Verificar expiración manual (jwt.decode lo hace, pero por seguridad)
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "permissions": payload.get("permissions", []),
            "exp": exp,
        }

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )


async def get_current_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Obtener usuario actual y verificar que es admin.

    **Validaciones:**
    - Usuario autenticado (via get_current_user)
    - rol == "admin"

    **Usa en rutas solo para admin:**
    ```python
    @router.post("/settings")
    async def update_settings(
        settings_data: dict,
        current_admin = Depends(get_current_admin)
    ):
        # Solo admins pueden llegar aquí
        ...
    ```

    **Respuesta en caso de error:**
    - 403 Forbidden: Usuario no es admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return current_user


async def get_current_barber(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Obtener usuario actual y verificar que es barbero.

    **Validaciones:**
    - Usuario autenticado
    - rol == "barber"
    """
    if current_user.get("role") not in ["barber", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Barber role required",
        )

    return current_user


async def get_current_client(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Obtener usuario actual y verificar que es cliente.

    **Validaciones:**
    - Usuario autenticado
    - rol == "client"
    """
    if current_user.get("role") not in ["client", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client role required",
        )

    return current_user


# ===== SERVICE DEPENDENCIES =====

async def get_auth_service(db=Depends(get_database)):
    """Obtener instancia del AuthService."""
    from app.services import AuthService
    from app.repositories import UserRepository

    return AuthService(UserRepository(db))


async def get_appointment_service(db=Depends(get_database)):
    """Obtener instancia del AppointmentService."""
    from app.services import AppointmentService
    from app.repositories import (
        AppointmentRepository,
        BarberRepository,
        ClientRepository,
        ServiceRepository,
    )

    return AppointmentService(
        AppointmentRepository(db),
        BarberRepository(db),
        ClientRepository(db),
        ServiceRepository(db),
    )


async def get_barber_service(db=Depends(get_database)):
    """Obtener instancia del BarberService."""
    from app.services import BarberService
    from app.repositories import BarberRepository

    return BarberService(BarberRepository(db))


async def get_client_service(db=Depends(get_database)):
    """Obtener instancia del ClientService."""
    from app.services import ClientService
    from app.repositories import ClientRepository

    return ClientService(ClientRepository(db))


async def get_payment_service(db=Depends(get_database)):
    """Obtener instancia del PaymentService."""
    from app.services import PaymentService
    from app.repositories import PaymentRepository

    return PaymentService(PaymentRepository(db))


async def get_notification_service(db=Depends(get_database)):
    """Obtener instancia del NotificationService."""
    from app.services import NotificationService
    from app.repositories import UserRepository

    return NotificationService(UserRepository(db))


async def get_report_service(db=Depends(get_database)):
    """Obtener instancia del ReportService."""
    from app.services import ReportService
    from app.repositories import (
        AppointmentRepository,
        PaymentRepository,
        BarberRepository,
        ClientRepository,
    )

    return ReportService(
        AppointmentRepository(db),
        PaymentRepository(db),
        BarberRepository(db),
        ClientRepository(db),
    )


async def get_analytics_service(db=Depends(get_database)):
    """Obtener instancia del AnalyticsService."""
    from app.services import AnalyticsService
    from app.repositories import (
        AppointmentRepository,
        PaymentRepository,
        ClientRepository,
        BarberRepository,
    )

    return AnalyticsService(
        AppointmentRepository(db),
        PaymentRepository(db),
        ClientRepository(db),
        BarberRepository(db),
    )


async def get_dashboard_service(db=Depends(get_database)):
    """Obtener instancia del DashboardService (si existe)."""
    # TODO: Implementar DashboardService si es necesario
    # Por ahora, reutilizar analytics_service
    return await get_analytics_service(db)


# ===== PAGINATION HELPERS =====

async def get_pagination(
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Obtener parámetros de paginación validados.

    **Query params:**
    - page: Página (default: 1, min: 1)
    - page_size: Items por página (default: 20, max: 100)

    **Retorna:**
    ```python
    {
        "page": 1,
        "page_size": 20,
        "skip": 0,
        "limit": 20
    }
    ```
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    skip = (page - 1) * page_size

    return {
        "page": page,
        "page_size": page_size,
        "skip": skip,
        "limit": page_size,
    }


# ===== VALIDATION HELPERS =====

async def validate_resource_owner(
    resource_owner_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """
    Validar que usuario actual es propietario del recurso.

    **Uso:**
    ```python
    @router.get("/appointments/{id}")
    async def get_appointment(
        id: str,
        _: None = Depends(validate_resource_owner(id))
    ):
        ...
    ```

    **Lanza:**
    - 403 Forbidden: Si usuario no es propietario
    """
    if current_user["user_id"] != resource_owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this resource",
        )


# ===== PERMISSION CHECKER =====

def require_permission(permission: str):
    """
    Crear dependencia que requiere permiso específico.

    **Uso:**
    ```python
    @router.delete("/appointments/{id}")
    async def delete_appointment(
        id: str,
        current_user = Depends(require_permission("appointments.delete"))
    ):
        ...
    ```

    **Soporta:**
    - "appointments.read"
    - "appointments.create"
    - "appointments.update"
    - "appointments.delete"
    - "payments.read"
    - "payments.refund"
    - etc.
    """
    async def check_permission(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user.get("role") == "admin":
            return current_user

        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )

        return current_user

    return check_permission


# ===== REQUEST CONTEXT =====

class RequestContext:
    """
    Contexto de la solicitud actual.

    Contiene información útil para el handler.
    """

    def __init__(
        self,
        user_id: str = None,
        user_role: str = None,
        request_id: str = None,
        timestamp: datetime = None,
    ):
        self.user_id = user_id
        self.user_role = user_role
        self.request_id = request_id
        self.timestamp = timestamp or datetime.utcnow()


async def get_request_context(
    current_user: Optional[dict] = Depends(get_current_user),
    request_id: Optional[str] = None,
) -> RequestContext:
    """
    Obtener contexto de la solicitud actual.

    **Incluye:**
    - user_id: ID del usuario autenticado
    - user_role: Role del usuario
    - request_id: ID único de la solicitud
    - timestamp: Hora de la solicitud
    """
    return RequestContext(
        user_id=current_user.get("user_id") if current_user else None,
        user_role=current_user.get("role") if current_user else None,
        request_id=request_id,
    )
