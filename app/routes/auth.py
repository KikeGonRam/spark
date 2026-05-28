"""
Auth Routes - Autenticación y autorización
Endpoints: /api/auth/*
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime
from typing import Optional

from app.models import (
    UserCreate,
    UserResponse,
)
from app.services import AuthService
from app.exceptions import ValidationError, UnauthorizedError
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_auth_service() -> AuthService:
    """Obtener instancia del servicio de autenticación."""
    from app.repositories import UserRepository
    from database.connection import MongoDBConnection
    db = MongoDBConnection.get_db()
    user_repo = UserRepository(db)
    return AuthService(user_repo)


# ===== ENDPOINTS =====

@router.post("/register", response_model=dict, status_code=201)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Registrar un nuevo usuario.

    **Request body:**
    - email: Email único
    - password: Contraseña (8+ chars, mayúscula, número, especial)
    - first_name: Nombre
    - last_name: Apellido
    - phone: Teléfono (opcional)

    **Response:**
    - user: Datos del usuario
    - access_token: JWT para autenticación
    - refresh_token: Token para renovar access_token
    - token_type: "bearer"

    **Códigos de respuesta:**
    - 201: Registro exitoso
    - 400: Validación fallida
    """
    try:
        logger.info(f"Register attempt: email={user_data.email}, role={user_data.role}")
        result = await auth_service.register(user_data, role=user_data.role)
        logger.info(f"Register success: {result['user'].email}")
        return {
            "id": result["user"].id,
            "email": result["user"].email,
            "name": result["user"].name,
            "role": result["user"].role.value,
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
        }
    except ValidationError as e:
        error_msg = str(e)
        # Check if it's a duplicate email error
        if "ya está registrado" in error_msg:
            logger.error(f"Conflict in register: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            )
        logger.error(f"ValidationError in register: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in register: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )


@router.post("/login", response_model=dict)
async def login(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login con email y contraseña.

    **Request body:**
    - email: Email registrado
    - password: Contraseña

    **Response:**
    - user: Datos del usuario
    - access_token: JWT (válido 30 minutos)
    - refresh_token: Token (válido 7 días)
    - token_type: "bearer"

    **Códigos de respuesta:**
    - 200: Login exitoso
    - 401: Credenciales inválidas
    """
    try:
        payload = await request.json()
        result = await auth_service.login(payload["email"], payload["password"])
        return {
            "token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
                "name": result["user"].name,
                "role": result["user"].role.value,
            }
        }
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Renovar access_token usando refresh_token.

    **Query parameters:**
    - refresh_token: Refresh token válido

    **Response:**
    - access_token: Nuevo JWT
    - token_type: "bearer"

    **Códigos de respuesta:**
    - 200: Token renovado
    - 401: Refresh token inválido o expirado
    """
    try:
        result = await auth_service.refresh_access_token(refresh_token)
        return {
            "success": True,
            "message": "Token renovado",
            "data": result,
        }
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout", response_model=dict)
async def logout(
    # current_user: User = Depends(get_current_user)  # TODO: Implementar
):
    """
    Logout del usuario.

    **Headers:**
    - Authorization: "Bearer <token>"

    **Response:**
    - message: Confirmación de logout

    **Notas:**
    - En JWT stateless no hay mucho que hacer en logout
    - El cliente simplemente descarta el token
    - TODO: Implementar blacklist de tokens si es necesario

    **Códigos de respuesta:**
    - 200: Logout exitoso
    """
    return {
        "success": True,
        "message": "Logout exitoso. Token descartado.",
    }


@router.post("/verify-email", response_model=dict)
async def verify_email(
    token: str,
):
    """
    Verificar email usando token.

    **Query parameters:**
    - token: Token de verificación

    **Response:**
    - message: Confirmación de verificación

    **TODO:**
    - Implementar verificación de token
    - Marcar email como verificado en BD

    **Códigos de respuesta:**
    - 200: Email verificado
    - 400: Token inválido o expirado
    """
    # TODO: Verificar token y marcar email como verificado
    return {
        "success": True,
        "message": "Email verificado exitosamente",
    }


@router.post("/request-password-reset", response_model=dict)
async def request_password_reset(
    email: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Solicitar reset de contraseña.

    **Query parameters:**
    - email: Email del usuario

    **Response:**
    - message: Confirmación de envío

    **Process:**
    1. Generar token de reset único
    2. Enviar email con link: /reset-password?token={token}
    3. Token válido por 24 horas

    **Códigos de respuesta:**
    - 200: Email enviado (incluso si usuario no existe, por seguridad)
    """
    try:
        reset_token = await auth_service.request_password_reset(email)
        # TODO: Enviar email con reset_token
        return {
            "success": True,
            "message": "Si el email existe, recibirás un link de reset",
        }
    except Exception as e:
        # Por seguridad, no revelar si el email existe
        return {
            "success": True,
            "message": "Si el email existe, recibirás un link de reset",
        }


@router.post("/reset-password", response_model=dict)
async def reset_password(
    reset_token: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Resetear contraseña con token.

    **Query parameters:**
    - reset_token: Token de reset
    - new_password: Nueva contraseña

    **Response:**
    - message: Confirmación de reset

    **Validaciones:**
    - Token válido y no expirado
    - Nueva contraseña cumple requisitos

    **Códigos de respuesta:**
    - 200: Contraseña actualizada
    - 400: Token inválido o expirado
    """
    try:
        await auth_service.reset_password(reset_token, new_password)
        return {
            "success": True,
            "message": "Contraseña actualizada exitosamente",
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    old_password: str,
    new_password: str,
    auth_service: AuthService = Depends(get_auth_service),
    # current_user: User = Depends(get_current_user)  # TODO: Implementar
):
    """
    Cambiar contraseña del usuario autenticado.

    **Headers:**
    - Authorization: "Bearer <token>"

    **Query parameters:**
    - old_password: Contraseña actual
    - new_password: Nueva contraseña

    **Response:**
    - message: Confirmación

    **Validaciones:**
    - Usuario autenticado
    - Contraseña actual correcta
    - Nueva contraseña cumple requisitos

    **Códigos de respuesta:**
    - 200: Contraseña actualizada
    - 401: No autenticado
    - 400: Contraseña actual incorrecta
    """
    try:
        # TODO: Obtener current_user del token
        # await auth_service.change_password(current_user.id, old_password, new_password)
        return {
            "success": True,
            "message": "Contraseña actualizada exitosamente",
        }
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=dict)
async def get_current_user_endpoint(current_user: dict = Depends(get_current_user)):
    """
    Obtener datos del usuario autenticado.

    **Headers:**
    - Authorization: "Bearer <token>"

    **Response:**
    - user: Datos del usuario actual

    **Códigos de respuesta:**
    - 200: Usuario obtenido
    - 401: Token inválido o expirado
    """
    return {
        "success": True,
        "message": "Usuario obtenido",
        "data": current_user
    }


@router.get("/health")
async def health_check(current_user: dict = Depends(get_current_user)):
    """
    Health check de endpoint protegido.
    
    Verifica que el usuario esté autenticado.
    
    **Headers:**
    - Authorization: "Bearer <token>"
    
    **Response:**
    - status: ok
    - user: user_id autenticado
    
    **Códigos de respuesta:**
    - 200: OK, usuario autenticado
    - 401: Token inválido o no proporcionado
    """
    return {
        "status": "ok",
        "user": current_user["user_id"],
        "role": current_user["role"]
    }
