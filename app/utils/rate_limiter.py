"""
Rate Limiting - Control de solicitudes

Limita solicitudes por IP/usuario para prevenir abuso.
"""

from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class SimpleRateLimiter:
    """
    Rate limiter simple en memoria.

    **Nota:** Para producción, usar Redis con slowapi.
    Esta es una implementación simple para desarrollo.
    """

    def __init__(self):
        """Inicializar rate limiter."""
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 300  # 5 minutos

    def _cleanup_old_requests(self, key: str, window_seconds: int):
        """Limpiar solicitudes antiguas."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window_seconds)

        # Remover solicitudes fuera del window
        self.requests[key] = [
            req_time
            for req_time in self.requests.get(key, [])
            if req_time > cutoff
        ]

    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int]:
        """
        Verificar si solicitud está dentro del límite.

        **Parámetros:**
        - key: Identificador (IP, user_id, etc.)
        - max_requests: Máximo de solicitudes permitidas
        - window_seconds: Ventana de tiempo en segundos

        **Retorna:**
        - (está_limitado, solicitudes_restantes)

        **Uso:**
        ```python
        is_limited, remaining = limiter.is_rate_limited("192.168.1.1", 10, 60)
        if is_limited:
            raise HTTPException(status_code=429)
        ```
        """
        self._cleanup_old_requests(key, window_seconds)

        now = datetime.utcnow()
        request_count = len(self.requests[key])

        if request_count >= max_requests:
            # Rate limited
            return True, 0

        # Agregar solicitud actual
        self.requests[key].append(now)

        # Retornar solicitudes restantes
        remaining = max_requests - request_count - 1
        return False, remaining

    def get_reset_time(self, key: str, window_seconds: int = 60) -> int:
        """
        Obtener segundos hasta reset de límite.

        **Parámetros:**
        - key: Identificador
        - window_seconds: Ventana de tiempo

        **Retorna:**
        - Segundos hasta reset
        """
        if key not in self.requests or not self.requests[key]:
            return 0

        oldest_request = min(self.requests[key])
        reset_time = oldest_request + timedelta(seconds=window_seconds)
        seconds_remaining = max(0, int((reset_time - datetime.utcnow()).total_seconds()))

        return seconds_remaining


# Instancia global de rate limiter
_rate_limiter = SimpleRateLimiter()


def get_client_ip(request: Request) -> str:
    """
    Obtener IP del cliente.

    **Maneja:**
    - IP directa
    - X-Forwarded-For (proxy)
    - X-Real-IP (nginx)
    """
    if request.client:
        # Directo
        return request.client.host

    # Proxy
    if x_forwarded_for := request.headers.get("X-Forwarded-For"):
        return x_forwarded_for.split(",")[0].strip()

    # Nginx
    if x_real_ip := request.headers.get("X-Real-IP"):
        return x_real_ip

    return "unknown"


class RateLimitMiddleware:
    """
    Middleware de rate limiting.

    Limita solicitudes por IP.
    """

    def __init__(
        self,
        app,
        default_max_requests: int = 100,
        default_window_seconds: int = 60,
    ):
        """
        Inicializar middleware.

        **Parámetros:**
        - app: Aplicación FastAPI
        - default_max_requests: Límite por defecto
        - default_window_seconds: Ventana por defecto
        """
        self.app = app
        self.default_max_requests = default_max_requests
        self.default_window_seconds = default_window_seconds

        # Límites por ruta
        self.route_limits = {
            "/api/auth/login": (10, 60),  # 10 por minuto
            "/api/auth/register": (5, 60),  # 5 por minuto
            "/api/auth/request-password-reset": (3, 60),  # 3 por minuto
            "/api/auth/refresh": (20, 60),  # 20 por minuto
            "/api/payments": (50, 60),  # 50 por minuto
        }

    async def __call__(self, request: Request, call_next):
        """Procesar solicitud y aplicar rate limiting."""
        path = request.url.path

        # Obtener límite para esta ruta
        if path in self.route_limits:
            max_requests, window_seconds = self.route_limits[path]
        else:
            max_requests = self.default_max_requests
            window_seconds = self.default_window_seconds

        # Obtener IP del cliente
        client_ip = get_client_ip(request)

        # Verificar rate limit
        is_limited, remaining = _rate_limiter.is_rate_limited(
            client_ip, max_requests, window_seconds
        )

        if is_limited:
            reset_in = _rate_limiter.get_reset_time(client_ip, window_seconds)
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {path} "
                f"(reset in {reset_in}s)"
            )

            return HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Try again in {reset_in} seconds.",
                headers={"Retry-After": str(reset_in)},
            )

        # Pasar solicitud
        response = await call_next(request)

        # Agregar headers de rate limit
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(
            _rate_limiter.get_reset_time(client_ip, window_seconds)
        )

        return response


def rate_limit_route(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorador para aplicar rate limiting a una ruta.

    **Uso:**
    ```python
    @router.post("/submit")
    @rate_limit_route(max_requests=5, window_seconds=60)
    async def submit(request: Request):
        return {"success": True}
    ```

    **Parámetros:**
    - max_requests: Máximo de solicitudes
    - window_seconds: Ventana de tiempo
    """

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = get_client_ip(request)
            is_limited, remaining = _rate_limiter.is_rate_limited(
                f"{client_ip}:{func.__name__}",
                max_requests,
                window_seconds,
            )

            if is_limited:
                reset_in = _rate_limiter.get_reset_time(
                    f"{client_ip}:{func.__name__}",
                    window_seconds,
                )
                logger.warning(f"Rate limit: {client_ip} on {func.__name__}")

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Try again in {reset_in}s.",
                    headers={"Retry-After": str(reset_in)},
                )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
