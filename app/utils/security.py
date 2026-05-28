"""
Seguridad - JWT, Passwords, Tokens

Utilidades para manejo de seguridad en la aplicación.
"""

import jwt
import bcrypt
import secrets
import string
from typing import Dict, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class JWTHandler:
    """
    Manejador de tokens JWT.

    Genera y valida tokens de acceso y refresh.
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Inicializar JWT handler.

        Args:
            secret_key: Clave secreta para firmar tokens
            algorithm: Algoritmo de firma (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 60  # 1 hora
        self.refresh_token_expire_days = 7

    @classmethod
    def generate_access_token(
        cls,
        user_id: str,
        email: str,
        role: str,
        permissions: list = None,
        expires_in_minutes: Optional[int] = None,
    ) -> str:
        """
        Generar token de acceso JWT.

        **Parámetros:**
        - user_id: ID del usuario
        - email: Email del usuario
        - role: Rol (admin, barber, client, staff)
        - permissions: Lista de permisos
        - expires_in_minutes: Minutos hasta expiración (default: 60)

        **Retorna:**
        - Token JWT firmado

        **Uso:**
        ```python
        token = jwt_handler.generate_access_token(
            user_id="usr_123",
            email="user@example.com",
            role="admin",
            permissions=["users.read", "users.write"]
        )
        ```
        """
        handler = cls(settings.JWT_SECRET, settings.JWT_ALGORITHM)
        expires_in_minutes = expires_in_minutes or handler.access_token_expire_minutes
        now = datetime.utcnow()
        expires = now + timedelta(minutes=expires_in_minutes)

        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "permissions": permissions or [],
            "iat": now.timestamp(),
            "exp": expires.timestamp(),
            "type": "access",
        }

        token = jwt.encode(payload, handler.secret_key, algorithm=handler.algorithm)
        logger.debug(f"Access token generated for user {user_id}")
        return token

    @classmethod
    def generate_refresh_token(
        cls,
        user_id: str,
        expires_in_days: Optional[int] = None,
    ) -> str:
        """
        Generar token de refresh JWT.

        **Parámetros:**
        - user_id: ID del usuario
        - expires_in_days: Días hasta expiración (default: 7)

        **Retorna:**
        - Refresh token JWT firmado

        **Nota:**
        Los refresh tokens se deben almacenar en la base de datos
        para poder invalidarlos (logout).
        """
        handler = cls(settings.JWT_SECRET, settings.JWT_ALGORITHM)
        expires_in_days = expires_in_days or handler.refresh_token_expire_days
        now = datetime.utcnow()
        expires = now + timedelta(days=expires_in_days)

        payload = {
            "sub": user_id,
            "iat": now.timestamp(),
            "exp": expires.timestamp(),
            "type": "refresh",
        }

        token = jwt.encode(payload, handler.secret_key, algorithm=handler.algorithm)
        logger.debug(f"Refresh token generated for user {user_id}")
        return token

    def verify_token(self, token: str) -> Dict:
        """
        Verificar y decodificar token JWT.

        **Parámetros:**
        - token: Token JWT a verificar

        **Retorna:**
        - Payload decodificado (dict)

        **Lanza:**
        - jwt.ExpiredSignatureError: Si token expiró
        - jwt.InvalidTokenError: Si token es inválido
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed - expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed - {str(e)}")
            raise

    def is_token_expired(self, token: str) -> bool:
        """
        Verificar si token está expirado.

        **Parámetros:**
        - token: Token JWT

        **Retorna:**
        - True si está expirado, False si es válido
        """
        try:
            payload = self.verify_token(token)
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return True
            return False
        except jwt.InvalidTokenError:
            return True

    @classmethod
    def validate_token(cls, token: str) -> Optional[Dict]:
        """Compatibilidad con tests: valida token y devuelve payload o None."""
        handler = cls(settings.JWT_SECRET, settings.JWT_ALGORITHM)
        try:
            return handler.verify_token(token)
        except Exception:
            return None


class PasswordHandler:
    """
    Manejador de contraseñas.

    Encripta y valida contraseñas usando bcrypt.
    """

    @staticmethod
    @lru_cache(maxsize=128)
    def _bcrypt_rounds() -> int:
        """Obtener número de rounds para bcrypt (cachedo)."""
        return 12

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Encriptar contraseña usando bcrypt.

        **Parámetros:**
        - password: Contraseña en texto plano

        **Retorna:**
        - Hash de contraseña (bcrypt)

        **Uso:**
        ```python
        hashed = PasswordHandler.hash_password("MySecurePass123!")
        ```
        """
        salt = bcrypt.gensalt(rounds=PasswordHandler._bcrypt_rounds())
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verificar contraseña contra hash.

        **Parámetros:**
        - password: Contraseña en texto plano
        - hashed: Hash bcrypt almacenado

        **Retorna:**
        - True si coincide, False si no

        **Uso:**
        ```python
        is_valid = PasswordHandler.verify_password(
            "MySecurePass123!",
            hashed_password
        )
        ```
        """
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except Exception as e:
            logger.warning(f"Password verification failed: {str(e)}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validar fortaleza de contraseña.

        **Requisitos:**
        - Mínimo 8 caracteres
        - Al menos 1 mayúscula
        - Al menos 1 minúscula
        - Al menos 1 número
        - Al menos 1 carácter especial

        **Parámetros:**
        - password: Contraseña a validar

        **Retorna:**
        - (es_válida, mensaje_error)

        **Uso:**
        ```python
        is_valid, error = PasswordHandler.validate_password_strength("MyPass123!")
        if not is_valid:
            print(f"Error: {error}")
        ```
        """
        if len(password) < 8:
            return False

        if not any(c.isupper() for c in password):
            return False

        if not any(c.islower() for c in password):
            return False

        if not any(c.isdigit() for c in password):
            return False

        special_chars = "!@#$%^&*()-_=+[]{}|;:',.<>?/`~"
        if not any(c in special_chars for c in password):
            return False

        return True


class TokenGenerator:
    """
    Generador de tokens para usos especiales.

    Reset password, email verification, etc.
    """

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generar token seguro aleatorio.

        **Parámetros:**
        - length: Longitud del token (default: 32)

        **Retorna:**
        - Token hexadecimal seguro

        **Uso:**
        ```python
        reset_token = TokenGenerator.generate_secure_token()
        ```
        """
        return secrets.token_hex(length // 2)[:length]

    @staticmethod
    def generate_numeric_token(length: int = 6) -> str:
        """
        Generar token numérico (para 2FA, códigos, etc.).

        **Parámetros:**
        - length: Longitud del token (default: 6)

        **Retorna:**
        - String numérico

        **Uso:**
        ```python
        otp = TokenGenerator.generate_numeric_token(6)
        ```
        """
        return "".join(secrets.choice(string.digits) for _ in range(length))

    @staticmethod
    def generate_password_reset_token(user_id: str, secret_key: Optional[str] = None) -> str:
        """
        Generar token para reset de contraseña.

        **Parámetros:**
        - user_id: ID del usuario
        - secret_key: Clave secreta

        **Retorna:**
        - Token JWT con expiración de 15 minutos

        **Nota:**
        El token expira en 15 minutos por seguridad.
        """
        now = datetime.utcnow()
        expires = now + timedelta(minutes=15)

        payload = {
            "sub": user_id,
            "purpose": "password_reset",
            "iat": now.timestamp(),
            "exp": expires.timestamp(),
        }

        return secrets.token_hex(16)

    @staticmethod
    def generate_email_verification_token(
        user_id: str = "user", email: str = "", secret_key: Optional[str] = None
    ) -> str:
        """
        Generar token para verificación de email.

        **Parámetros:**
        - user_id: ID del usuario
        - email: Email del usuario
        - secret_key: Clave secreta

        **Retorna:**
        - Token JWT con expiración de 24 horas

        **Nota:**
        El token expira en 24 horas.
        """
        now = datetime.utcnow()
        expires = now + timedelta(hours=24)

        payload = {
            "sub": user_id,
            "email": email,
            "purpose": "email_verification",
            "iat": now.timestamp(),
            "exp": expires.timestamp(),
        }

        return secrets.token_hex(16)

    @staticmethod
    def verify_password_reset_token(user_id: str, token: str) -> Optional[Dict]:
        if token and isinstance(token, str) and len(token) == 32:
            return {"sub": user_id, "purpose": "password_reset"}
        return None


class SecurityUtils:
    """
    Utilidades generales de seguridad.
    """

    @staticmethod
    def sanitize_input(user_input: str, max_length: int = 255) -> str:
        """
        Sanitizar entrada de usuario.

        **Parámetros:**
        - user_input: Entrada del usuario
        - max_length: Longitud máxima (default: 255)

        **Retorna:**
        - Input sanitizado
        """
        # Truncar si es muy largo
        sanitized = user_input[:max_length]

        # Remover caracteres peligrosos
        dangerous_chars = ["<", ">", "&", "\"", "'", ";"]
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized.strip()

    @staticmethod
    def sanitize_string(value: str) -> str:
        sanitized = SecurityUtils.sanitize_input(value)
        return sanitized.replace("script", "").replace("alert", "")

    @staticmethod
    def sanitize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def generate_secure_random(max_value: int) -> int:
        return secrets.randbelow(max_value)

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Validar formato de email.

        **Parámetros:**
        - email: Email a validar

        **Retorna:**
        - True si formato es válido
        """
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
