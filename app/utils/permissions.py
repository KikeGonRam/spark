"""
Decoradores y Utilidades de Permisos

Decoradores para proteger endpoints basado en roles y permisos.
"""

from functools import wraps
from typing import List
from fastapi import HTTPException, status, Request
import logging

logger = logging.getLogger(__name__)


def require_role(*allowed_roles: str):
    """
    Decorador para requerir un rol específico.

    **Uso:**
    ```python
    @router.get("/admin-only")
    @require_role("admin")
    async def admin_endpoint(request: Request):
        return {"message": "Admin access"}
    ```

    **Roles soportados:**
    - admin
    - barber
    - client
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = getattr(request.state, "user_role", None)

            if not user_role:
                logger.warning("Unauthorized access attempt - no user role")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if user_role not in allowed_roles:
                logger.warning(
                    f"Forbidden access - required roles: {allowed_roles}, "
                    f"user role: {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This endpoint requires one of: {', '.join(allowed_roles)}",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_permission(permission: str):
    """
    Decorador para requerir un permiso específico.

    **Uso:**
    ```python
    @router.delete("/appointments/{id}")
    @require_permission("appointments.delete")
    async def delete_appointment(id: str, request: Request):
        return {"deleted": True}
    ```

    **Permisos ejemplos:**
    - appointments.read
    - appointments.create
    - appointments.update
    - appointments.delete
    - appointments.confirm
    - appointments.complete
    - payments.read
    - payments.create
    - payments.refund
    - reports.read
    - reports.export
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = getattr(request.state, "user_role", None)
            user_permissions = getattr(request.state, "user_permissions", [])

            # Admin tiene todos los permisos
            if user_role == "admin":
                return await func(request, *args, **kwargs)

            if permission not in user_permissions:
                logger.warning(
                    f"Forbidden - required permission: {permission}, "
                    f"user permissions: {user_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_any_role(*allowed_roles: str):
    """
    Decorador para requerir uno de varios roles.

    **Uso:**
    ```python
    @router.get("/admin-panel")
    @require_any_role("admin", "barber")
    async def staff_endpoint(request: Request):
        return {"data": "panel"}
    ```
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_role = getattr(request.state, "user_role", None)

            if not user_role:
                logger.warning("Unauthorized - no user role")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if user_role not in allowed_roles:
                logger.warning(
                    f"Forbidden - required one of: {allowed_roles}, "
                    f"got: {user_role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {', '.join(allowed_roles)}",
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def check_resource_owner(user_id_param: str = "user_id"):
    """
    Decorador para verificar que usuario es propietario del recurso.

    **Uso:**
    ```python
    @router.get("/profile/{user_id}")
    @check_resource_owner("user_id")
    async def get_profile(user_id: str, request: Request):
        return {"user": user_id}
    ```

    **Nota:** El endpoint debe tener parámetro user_id o equivalente.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            # Obtener user_id del parámetro
            resource_owner_id = kwargs.get(user_id_param)

            if not resource_owner_id:
                logger.warning(f"Resource owner check failed - no {user_id_param}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing {user_id_param}",
                )

            # Obtener user_id autenticado
            current_user_id = getattr(request.state, "user_id", None)
            user_role = getattr(request.state, "user_role", None)

            if not current_user_id:
                logger.warning("No authenticated user")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Admin puede acceder a todo
            if user_role == "admin":
                return await func(*args, request=request, **kwargs)

            # Verificar propiedad del recurso
            if current_user_id != resource_owner_id:
                logger.warning(
                    f"Unauthorized resource access - "
                    f"user {current_user_id} tried to access {resource_owner_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this resource",
                )

            return await func(*args, request=request, **kwargs)

        return wrapper

    return decorator


class PermissionChecker:
    """
    Clase para verificaciones complejas de permisos.

    **Uso:**
    ```python
    checker = PermissionChecker(request)
    if checker.has_role("admin"):
        ...
    if checker.has_permission("payments.refund"):
        ...
    ```
    """

    def __init__(self, request: Request):
        """Inicializar con request."""
        self.request = request
        self.user_id = getattr(request.state, "user_id", None)
        self.user_role = getattr(request.state, "user_role", None)
        self.user_permissions = getattr(request.state, "user_permissions", [])

    def is_authenticated(self) -> bool:
        """Verificar si usuario está autenticado."""
        return self.user_id is not None

    def has_role(self, role: str) -> bool:
        """Verificar si usuario tiene rol específico."""
        return self.user_role == role

    def has_any_role(self, *roles: str) -> bool:
        """Verificar si usuario tiene uno de los roles."""
        return self.user_role in roles

    def has_permission(self, permission: str) -> bool:
        """Verificar si usuario tiene permiso específico."""
        # Admin tiene todos los permisos
        if self.user_role == "admin":
            return True
        return permission in self.user_permissions

    def has_all_permissions(self, *permissions: str) -> bool:
        """Verificar si usuario tiene todos los permisos."""
        if self.user_role == "admin":
            return True
        return all(p in self.user_permissions for p in permissions)

    def has_any_permission(self, *permissions: str) -> bool:
        """Verificar si usuario tiene alguno de los permisos."""
        if self.user_role == "admin":
            return True
        return any(p in self.user_permissions for p in permissions)

    def assert_role(self, role: str, message: str = None):
        """Lanzar excepción si usuario no tiene rol."""
        if not self.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message or f"Role '{role}' required",
            )

    def assert_permission(self, permission: str, message: str = None):
        """Lanzar excepción si usuario no tiene permiso."""
        if not self.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=message or f"Permission '{permission}' required",
            )


def get_current_user_id(request: Request) -> str:
    """
    Obtener ID del usuario actual desde request.

    **Uso:**
    ```python
    @router.get("/profile")
    async def get_profile(request: Request):
        user_id = get_current_user_id(request)
        return {"user_id": user_id}
    ```
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return user_id


def get_current_user_role(request: Request) -> str:
    """
    Obtener rol del usuario actual desde request.

    **Uso:**
    ```python
    @router.get("/check-role")
    async def check_role(request: Request):
        role = get_current_user_role(request)
        return {"role": role}
    ```
    """
    role = getattr(request.state, "user_role", None)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated",
        )
    return role
