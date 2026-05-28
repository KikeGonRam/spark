"""
AuthService - Lógica de autenticación y seguridad
Maneja: JWT tokens, password hashing, login, logout, refresh tokens
Integración con roles y permisos
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import bcrypt
import jwt
from functools import lru_cache

from app.models import (
    User,
    UserCreate,
    UserRole,
    UserStatus,
)
from app.repositories import (
    UserRepository,
)
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    UnauthorizedError,
)
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Servicio de lógica de autenticación."""

    # Cache TTL en segundos
    TOKEN_EXPIRY_MINUTES = 30
    REFRESH_TOKEN_EXPIRY_DAYS = 7

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    # ===== REGISTRO =====

    async def register(
        self, user_data: UserCreate, role: UserRole = None
    ) -> Dict:
        """
        Registrar un nuevo usuario.

        Args:
            user_data: Datos del usuario
            role: Rol del usuario (optional, uses user_data.role if not provided)

        Returns:
            Dict: Contiene usuario y token de acceso

        Raises:
            ValidationError: Si el email ya existe o datos inválidos
        """
        # Use role from parameter if provided, otherwise use from user_data
        user_role = role if role is not None else user_data.role
        
        # Validar email único
        exists = await self.user_repo.email_exists(user_data.email)
        if exists:
            raise ValidationError(field="email", reason=f"{user_data.email} ya está registrado")

        # Validar contraseña
        self._validate_password(user_data.password)

        # Hash de contraseña
        hashed_password = self._hash_password(user_data.password)

        # Crear usuario
        user_id = await self.user_repo.create(
            User(
                email=user_data.email.lower(),
                password=hashed_password,
                name=user_data.name,
                phone=user_data.phone,
                role=user_role,
                status=UserStatus.ACTIVE,
                is_email_verified=False,
            )
        )

        # Build the user object from the data we just created
        user = User(
            id=user_id,
            email=user_data.email.lower(),
            password=hashed_password,
            name=user_data.name,
            phone=user_data.phone,
            role=user_role,
            status=UserStatus.ACTIVE,
            is_email_verified=False,
        )

        # Enviar email de verificación
        try:
            from app.services.email_service import get_email_service
            email_service = get_email_service()
            await email_service.send_verification_email(
                recipient_email=user.email,
                recipient_name=user.name
            )
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")

        # Generar tokens
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ===== LOGIN =====

    async def login(self, email: str, password: str) -> Dict:
        """
        Realizar login de un usuario.

        Args:
            email: Email del usuario
            password: Contraseña

        Returns:
            Dict: Contiene usuario y token de acceso

        Raises:
            UnauthorizedError: Si las credenciales son inválidas
        """
        # Buscar usuario
        user = await self.user_repo.find_by_email(email.lower())
        if not user:
            raise UnauthorizedError("Email o contraseña incorrectos")

        # Validar contraseña
        if not self._verify_password(password, user.password):
            raise UnauthorizedError("Email o contraseña incorrectos")

        # Validar que usuario está activo
        if user.status != UserStatus.ACTIVE:
            raise UnauthorizedError(
                f"Usuario inactivo. Estado: {user.status}"
            )

        # Actualizar último login
        await self.user_repo.update_last_login(user.id)

        # Generar tokens
        access_token = self.generate_access_token(user)
        refresh_token = self.generate_refresh_token(user)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ===== JWT TOKENS =====

    def generate_access_token(self, user: User) -> str:
        """
        Generar JWT access token.

        Args:
            user: Objeto usuario

        Returns:
            str: JWT token

        Raises:
            ValidationError: Si hay error en la generación
        """
        try:
            payload = {
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow()
                + timedelta(minutes=self.TOKEN_EXPIRY_MINUTES),
                "type": "access",
            }

            token = jwt.encode(
                payload,
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM,
            )

            return token
        except Exception as e:
            raise ValidationError(message=f"Error generando token: {str(e)}")

    def generate_refresh_token(self, user: User) -> str:
        """
        Generar JWT refresh token.

        Args:
            user: Objeto usuario

        Returns:
            str: JWT refresh token
        """
        try:
            payload = {
                "sub": str(user.id),
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow()
                + timedelta(days=self.REFRESH_TOKEN_EXPIRY_DAYS),
                "type": "refresh",
            }

            token = jwt.encode(
                payload,
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM,
            )

            return token
        except Exception as e:
            raise ValidationError(message=f"Error generando refresh token: {str(e)}")

    def verify_token(self, token: str) -> Dict:
        """
        Verificar y decodificar JWT access token.

        Args:
            token: JWT token

        Returns:
            Dict: Payload del token

        Raises:
            UnauthorizedError: Si el token es inválido o expirado
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )

            if payload.get("type") != "access":
                raise UnauthorizedError("Tipo de token inválido")

            return payload

        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Token expirado")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Token inválido")
        except Exception as e:
            raise UnauthorizedError(f"Error verificando token: {str(e)}")

    def verify_refresh_token(self, token: str) -> Dict:
        """
        Verificar y decodificar JWT refresh token.

        Args:
            token: Refresh token

        Returns:
            Dict: Payload del token

        Raises:
            UnauthorizedError: Si el token es inválido
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )

            if payload.get("type") != "refresh":
                raise UnauthorizedError("Tipo de token inválido")

            return payload

        except jwt.ExpiredSignatureError:
            raise UnauthorizedError("Refresh token expirado")
        except jwt.InvalidTokenError:
            raise UnauthorizedError("Refresh token inválido")
        except Exception as e:
            raise UnauthorizedError(f"Error verificando refresh token: {str(e)}")

    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Generar nuevo access token usando refresh token.

        Args:
            refresh_token: Refresh token válido

        Returns:
            Dict: Nuevo access token

        Raises:
            UnauthorizedError: Si refresh token no es válido
        """
        # Verificar refresh token
        payload = self.verify_refresh_token(refresh_token)

        # Obtener usuario
        user_id = payload.get("sub")
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise UnauthorizedError("Usuario no encontrado")

        # Generar nuevo access token
        access_token = self.generate_access_token(user)

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    # ===== PASSWORD MANAGEMENT =====

    def _hash_password(self, password: str) -> str:
        """
        Hashear contraseña con bcrypt.

        Args:
            password: Contraseña en texto plano

        Returns:
            str: Hash de la contraseña
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, hashed: str) -> bool:
        """
        Verificar contraseña contra hash.

        Args:
            password: Contraseña en texto plano
            hashed: Hash almacenado

        Returns:
            bool: True si coincide
        """
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def _validate_password(self, password: str) -> None:
        """
        Validar requisitos de contraseña.

        Requisitos:
        - Mínimo 8 caracteres
        - Al menos 1 mayúscula
        - Al menos 1 minúscula
        - Al menos 1 número
        - Al menos 1 carácter especial

        Args:
            password: Contraseña a validar

        Raises:
            ValidationError: Si no cumple requisitos
        """
        if len(password) < 8:
            raise ValidationError(
                reason="La contraseña debe tener al menos 8 caracteres"
            )

        if not any(c.isupper() for c in password):
            raise ValidationError(
                reason="La contraseña debe contener al menos 1 mayúscula"
            )

        if not any(c.islower() for c in password):
            raise ValidationError(
                reason="La contraseña debe contener al menos 1 minúscula"
            )

        if not any(c.isdigit() for c in password):
            raise ValidationError(
                reason="La contraseña debe contener al menos 1 número"
            )

        special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/\\~`"
        if not any(c in special_chars for c in password):
            raise ValidationError(
                reason="La contraseña debe contener al menos 1 carácter especial"
            )

    async def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> None:
        """
        Cambiar contraseña de un usuario.

        Args:
            user_id: ID del usuario
            old_password: Contraseña actual
            new_password: Nueva contraseña

        Raises:
            ResourceNotFoundError: Si usuario no existe
            UnauthorizedError: Si contraseña actual es incorrecta
            ValidationError: Si nueva contraseña no cumple requisitos
        """
        # Obtener usuario
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"Usuario {user_id} no encontrado")

        # Verificar contraseña actual
        if not self._verify_password(old_password, user.password):
            raise UnauthorizedError("Contraseña actual incorrecta")

        # Validar nueva contraseña
        self._validate_password(new_password)

        # Hash de nueva contraseña
        hashed_password = self._hash_password(new_password)

        # Actualizar
        await self.user_repo.update(
            user_id,
            {"password": hashed_password, "updated_at": datetime.utcnow()},
        )

    async def request_password_reset(self, email: str) -> str:
        """
        Solicitar reset de contraseña.

        Args:
            email: Email del usuario

        Returns:
            str: Token de reset

        Raises:
            ResourceNotFoundError: Si usuario no existe
        """
        user = await self.user_repo.find_by_email(email.lower())
        if not user:
            raise ResourceNotFoundError(f"Usuario con email {email} no encontrado")

        # TODO: Generar token de reset
        # TODO: Almacenar token en base de datos con expiración
        # TODO: Enviar email con link de reset

        return "reset_token_placeholder"

    async def reset_password(self, reset_token: str, new_password: str) -> None:
        """
        Cambiar contraseña usando reset token.

        Args:
            reset_token: Token de reset
            new_password: Nueva contraseña

        Raises:
            ValidationError: Si token inválido o expirado
        """
        # TODO: Verificar token
        # TODO: Validar nueva contraseña
        # TODO: Actualizar contraseña
        pass

    # ===== ROLES Y PERMISOS =====

    def has_role(self, user: User, required_role: UserRole) -> bool:
        """
        Verificar si usuario tiene un rol específico.

        Args:
            user: Objeto usuario
            required_role: Rol requerido

        Returns:
            bool: True si tiene el rol
        """
        return user.role == required_role

    def has_permission(self, user: User, permission: str) -> bool:
        """
        Verificar si usuario tiene un permiso específico.

        Args:
            user: Objeto usuario
            permission: Permiso requerido

        Returns:
            bool: True si tiene permiso

        Nota: Por ahora es un placeholder. Implementar con roles y permisos
        """
        # TODO: Implementar sistema de permisos granulares
        # Por ahora basado en roles

        role_permissions = {
            UserRole.ADMIN: [
                "view_all_users",
                "manage_users",
                "manage_barbers",
                "view_reports",
                "manage_settings",
            ],
            UserRole.RECEPTIONIST: [
                "view_appointments",
                "create_appointments",
                "update_appointments",
                "process_payments",
            ],
            UserRole.BARBER: [
                "view_own_schedule",
                "view_appointments",
                "update_own_appointments",
            ],
            UserRole.CLIENT: [
                "view_own_appointments",
                "create_appointments",
                "cancel_own_appointments",
                "rate_services",
            ],
        }

        return permission in role_permissions.get(user.role, [])
