"""
Middleware de Autenticación - JWT Token Validation

Validar JWT tokens en cada solicitud y extraer información del usuario.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import jwt
import logging
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger(__name__)


class JWTMiddleware:
    """
    Middleware para validación de JWT tokens.
    
    Valida el token en solicitudes protegidas y agrega información
    del usuario al estado de la solicitud.
    """

    # Endpoints públicos (sin autenticación requerida)
    PUBLIC_ENDPOINTS = {
        "/health",
        "/health/ready",
        "/health/live",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api",
        "/api/info",
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/refresh",
    }

    def __init__(self, app, secret_key: str, algorithm: str = "HS256"):
        """
        Inicializar middleware JWT.

        Args:
            app: Aplicación FastAPI
            secret_key: Clave secreta para validar tokens
            algorithm: Algoritmo JWT (default: HS256)
        """
        self.app = app
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def __call__(self, scope, receive, send):
        """Procesar solicitud y validar JWT si es requerido."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        path = request.url.path

        # Endpoints públicos - pasar sin validación
        if self._is_public_endpoint(path):
            await self.app(scope, receive, send)
            return

        # Rutas de autenticación sin protección adicional
        if path.startswith("/api/auth/"):
            await self.app(scope, receive, send)
            return

        # Rutas protegidas - validar JWT
        authorization = request.headers.get("Authorization")

        if not authorization:
            logger.warning(f"Missing authorization header: {path}")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": "Authorization header required",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        # Extraer token
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                logger.warning(f"Invalid authorization scheme: {scheme}")
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "success": False,
                        "error": "UNAUTHORIZED",
                        "message": "Invalid authorization scheme. Use 'Bearer'",
                    },
                )
                await response(scope, receive, send)
                return
        except ValueError:
            logger.warning(f"Invalid authorization format")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": "Invalid authorization format",
                },
            )
            await response(scope, receive, send)
            return

        # Validar token
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )

            # Verificar expiración
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.warning(f"Token expired for user: {payload.get('sub')}")
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "success": False,
                        "error": "UNAUTHORIZED",
                        "message": "Token has expired",
                    },
                )
                await response(scope, receive, send)
                return

            # Agregar user context al scope
            scope["user_id"] = payload.get("sub")
            scope["user_email"] = payload.get("email")
            scope["user_role"] = payload.get("role", "user")
            scope["user_permissions"] = payload.get("permissions", [])
            scope["token"] = token

            logger.debug(f"JWT validated for user: {scope['user_id']}")

        except jwt.ExpiredSignatureError:
            logger.warning(f"Expired token attempt")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": "Token has expired",
                },
            )
            await response(scope, receive, send)
            return
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "success": False,
                    "error": "UNAUTHORIZED",
                    "message": "Invalid token",
                },
            )
            await response(scope, receive, send)
            return

        # Pasar a siguiente middleware/endpoint
        await self.app(scope, receive, send)

    @staticmethod
    def _is_public_endpoint(path: str) -> bool:
        """Verificar si endpoint es público."""
        # Rutas exactas
        if path in JWTMiddleware.PUBLIC_ENDPOINTS:
            return True

        # Swagger/OpenAPI
        if path.startswith("/swagger") or path.startswith("/redoc"):
            return True

        return False
