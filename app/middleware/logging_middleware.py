"""
Middleware de Logging - Request/Response Logging

Registra todas las solicitudes y respuestas para auditoría y debugging.
"""

import logging
import time
import uuid
from fastapi import Request
from fastapi.responses import Response
from typing import Callable
import json

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Middleware para logging de solicitudes y respuestas.
    
    Registra:
    - Request ID único
    - Método y ruta
    - Usuario (si autenticado)
    - Status code
    - Tiempo de ejecución
    - Errores
    """

    def __init__(self, app):
        """Inicializar middleware de logging."""
        self.app = app

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Procesar solicitud y loguear información."""
        # Generar request ID único
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Información de la solicitud
        method = request.method
        path = request.url.path
        query_string = request.url.query
        client_ip = request.client.host if request.client else "unknown"

        # Usuario (si está autenticado)
        user_id = getattr(request.state, "user_id", None)
        user_role = getattr(request.state, "user_role", None)

        # Timestamp de inicio
        start_time = time.time()

        try:
            # Ejecutar solicitud
            response = await call_next(request)

            # Tiempo de ejecución
            duration_ms = (time.time() - start_time) * 1000

            # Log de solicitud exitosa
            log_message = (
                f"[{request_id}] {method} {path} "
                f"→ {response.status_code} ({duration_ms:.0f}ms)"
            )

            if user_id:
                log_message += f" | User: {user_id} ({user_role})"
            if query_string:
                log_message += f" | Query: {query_string}"

            # Log level según status code
            if response.status_code < 400:
                logger.info(log_message)
            elif response.status_code < 500:
                logger.warning(log_message)
            else:
                logger.error(log_message)

            # Agregar request ID a headers de respuesta
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Tiempo de ejecución
            duration_ms = (time.time() - start_time) * 1000

            # Log de error
            log_message = (
                f"[{request_id}] {method} {path} "
                f"→ ERROR ({duration_ms:.0f}ms)"
            )

            if user_id:
                log_message += f" | User: {user_id} ({user_role})"

            log_message += f" | Exception: {str(exc)}"

            logger.error(log_message, exc_info=True)

            # Re-lanzar excepción
            raise
