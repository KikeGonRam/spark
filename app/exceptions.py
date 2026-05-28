"""
Custom Exceptions - Excepciones personalizadas de la aplicación.

Estas excepciones se lanzan desde servicios y repositories,
y se capturan en las rutas para convertirse en HTTPExceptions.
"""


class BarberProException(Exception):
    """Excepción base para toda la aplicación."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self):
        return self.message

    def to_dict(self):
        """Convertir a diccionario para respuesta JSON."""
        return {
            "success": False,
            "error": self.code,
            "message": self.message,
        }


class ResourceNotFoundError(BarberProException):
    """
    Se lanza cuando un recurso solicitado no existe.

    Mapea a: HTTP 404 Not Found

    **Ejemplos:**
    - Cita no encontrada
    - Cliente no existe
    - Barbero no registrado
    - Servicio discontinuado
    """

    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} no encontrado"
        if identifier:
            message += f" (ID: {identifier})"
        super().__init__(message, "RESOURCE_NOT_FOUND")


class ValidationError(BarberProException):
    """
    Se lanza cuando datos no cumplen validaciones de negocio.

    Mapea a: HTTP 400 Bad Request

    **Ejemplos:**
    - Email inválido
    - Password muy débil
    - Cantidad negativa
    - Formato de fecha incorrecto
    - Campo requerido ausente
    - Valor fuera de rango
    """

    def __init__(self, field: str = None, reason: str = None, message: str = None):
        # Support both positional string and keyword arguments
        # If first arg is a string and looks like a message (not a field name):
        if isinstance(field, str) and reason is None and message is None:
            # Check if it looks like a message (contains spaces or common error words)
            if ' ' in field or any(word in field.lower() for word in ['error', 'debe', 'no puede', 'ya', 'inválido', 'requerido']):
                # Treat as message
                super().__init__(field, "VALIDATION_ERROR")
            else:
                # Treat as field name
                msg = f"Validación fallida en '{field}': campo requerido"
                super().__init__(msg, "VALIDATION_ERROR")
        elif message:
            # Direct message
            super().__init__(message, "VALIDATION_ERROR")
        elif field and reason:
            msg = f"Validación fallida en '{field}': {reason}"
            super().__init__(msg, "VALIDATION_ERROR")
        elif reason:
            msg = f"Validación fallida: {reason}"
            super().__init__(msg, "VALIDATION_ERROR")
        else:
            msg = "Los datos no cumplen validaciones requeridas"
            super().__init__(msg, "VALIDATION_ERROR")


class ConflictError(BarberProException):
    """
    Se lanza cuando hay conflicto de estado en la operación.

    Mapea a: HTTP 409 Conflict

    **Ejemplos:**
    - Email ya registrado
    - Slot de tiempo ya ocupado
    - Cita ya confirmada (no puede confirmarse de nuevo)
    - Barbero no disponible
    - Servicio agotado
    - Estado transición inválida
    """

    def __init__(self, message: str, reason: str = None):
        if reason:
            full_message = f"{message} ({reason})"
        else:
            full_message = message
        super().__init__(full_message, "CONFLICT")


class UnauthorizedError(BarberProException):
    """
    Se lanza cuando falla autenticación o autorización.

    Mapea a: HTTP 401 Unauthorized

    **Ejemplos:**
    - Token JWT expirado
    - Credenciales inválidas
    - Usuario no autenticado
    - Token malformado
    - Firma JWT inválida
    """

    def __init__(self, reason: str = "Autenticación requerida"):
        super().__init__(reason, "UNAUTHORIZED")


class ForbiddenError(BarberProException):
    """
    Se lanza cuando usuario autenticado no tiene permiso.

    Mapea a: HTTP 403 Forbidden

    **Ejemplos:**
    - Cliente intenta ver citas de otro cliente
    - Barbero intenta acceder a sección admin
    - Usuario no tiene rol requerido
    - Permiso específico denegado
    """

    def __init__(self, resource: str = None, action: str = None):
        if resource and action:
            message = f"No tiene permiso para {action} {resource}"
        else:
            message = "No tiene permisos para esta operación"
        super().__init__(message, "FORBIDDEN")


class DuplicateError(BarberProException):
    """
    Se lanza cuando se intenta crear un recurso duplicado.

    Mapea a: HTTP 409 Conflict (especialización de ConflictError)

    **Ejemplos:**
    - Email ya registrado
    - Nombre de usuario duplicado
    - Teléfono ya en uso
    """

    def __init__(self, field: str, value: str):
        message = f"El {field} '{value}' ya está registrado"
        super().__init__(message, "DUPLICATE_RESOURCE")


class InvalidStateTransitionError(BarberProException):
    """
    Se lanza cuando transición de estado es inválida.

    Mapea a: HTTP 409 Conflict

    **Ejemplos:**
    - Completar cita que no está confirmada
    - Confirmar cita que ya fue cancelada
    - Cambiar estado que requiere condiciones previas
    """

    def __init__(self, current_state: str, target_state: str):
        message = f"No se puede ir de estado '{current_state}' a '{target_state}'"
        super().__init__(message, "INVALID_STATE_TRANSITION")


class BusinessLogicError(BarberProException):
    """
    Se lanza cuando reglas de negocio no se cumplen.

    Mapea a: HTTP 400 Bad Request

    **Ejemplos:**
    - Barbero no tiene especialización requerida
    - Horario fuera de disponibilidad
    - Cliente sin puntos para canjear
    - Refund solicitud fuera de plazo
    - Precio mínimo no alcanzado
    """

    def __init__(self, rule: str, reason: str = None):
        message = f"Regla de negocio incumplida: {rule}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "BUSINESS_LOGIC_ERROR")


class DatabaseError(BarberProException):
    """
    Se lanza cuando hay error en base de datos.

    Mapea a: HTTP 500 Internal Server Error

    **Ejemplos:**
    - Conexión perdida
    - Transacción fallida
    - Índice no encontrado
    - Escritura fallida
    """

    def __init__(self, operation: str, reason: str = None):
        message = f"Error en base de datos: {operation}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "DATABASE_ERROR")


class ExternalServiceError(BarberProException):
    """
    Se lanza cuando servicio externo falla.

    Mapea a: HTTP 503 Service Unavailable

    **Ejemplos:**
    - Payment gateway down
    - Email service no responde
    - Gemini API error
    - SMS service error
    """

    def __init__(self, service: str, reason: str = None):
        message = f"Error en servicio externo: {service}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")


class RateLimitError(BarberProException):
    """
    Se lanza cuando se excede rate limit.

    Mapea a: HTTP 429 Too Many Requests

    **Ejemplos:**
    - Demasiados intentos de login
    - Demasiadas solicitudes de reset password
    - API rate limit excedido
    """

    def __init__(self, limit: int = None, reset_in: int = None):
        message = "Ha excedido el límite de intentos permitidos"
        if reset_in:
            message += f". Intente nuevamente en {reset_in} segundos"
        super().__init__(message, "RATE_LIMIT_EXCEEDED")


class InvalidInputError(BarberProException):
    """
    Se lanza cuando input es completamente inválido.

    Mapea a: HTTP 400 Bad Request

    **Ejemplos:**
    - JSON malformado
    - Tipo de dato incorrecto
    - Campo faltante requerido
    """

    def __init__(self, field: str = None, expected: str = None):
        if field and expected:
            message = f"Campo '{field}' debe ser de tipo {expected}"
        else:
            message = "Input inválido o malformado"
        super().__init__(message, "INVALID_INPUT")
