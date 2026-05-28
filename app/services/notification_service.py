"""
NotificationService - Lógica de notificaciones
Maneja: envío de emails, SMS, notificaciones push/in-app
Plantillas de notificación, colas de envío
"""

import logging
from datetime import datetime
from typing import Optional, List
from enum import Enum

from app.models import (
    User,
    Appointment,
    Client,
    Barber,
)
from app.exceptions import (
    ValidationError,
)
from app.config import settings
from app.services.email_service import get_email_service

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Tipos de notificaciones."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationTemplate(str, Enum):
    """Plantillas de notificación disponibles."""

    # Citas
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_COMPLETED = "appointment_completed"

    # Pagos
    PAYMENT_PROCESSED = "payment_processed"
    PAYMENT_FAILED = "payment_failed"
    INVOICE_GENERATED = "invoice_generated"

    # Clientes
    WELCOME = "welcome"
    ACCOUNT_VERIFIED = "account_verified"
    PASSWORD_RESET = "password_reset"

    # Marketing
    PROMOTION = "promotion"
    LOYALTY_POINTS_EARNED = "loyalty_points_earned"
    VIP_STATUS_ACHIEVED = "vip_status_achieved"


class NotificationService:
    """Servicio de notificaciones."""

    def __init__(self):
        """Inicializar servicio de notificaciones."""
        # TODO: Inyectar providers de email/SMS
        pass

    # ===== NOTIFICACIONES DE CITAS =====

    async def notify_appointment_created(
        self, appointment: Appointment, client: Client, barber: Barber
    ) -> bool:
        """
        Enviar notificación cuando se crea una cita.

        Args:
            appointment: Objeto cita
            client: Objeto cliente
            barber: Objeto barbero

        Returns:
            bool: True si se envió exitosamente
        """
        # Notificar al cliente
        client_email_sent = await self.send_email(
            recipient_email=client.email,
            template=NotificationTemplate.APPOINTMENT_CREATED,
            context={
                "client_name": client.first_name,
                "barber_name": f"{barber.first_name} {barber.last_name}",
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.start_time,
            },
        )

        # TODO: Notificar al barbero
        # TODO: Crear notificación in-app para cliente

        return client_email_sent

    async def notify_appointment_confirmed(
        self, appointment: Appointment, client: Client, barber: Barber
    ) -> bool:
        """Enviar notificación cuando se confirma una cita."""
        return await self.send_email(
            recipient_email=client.email,
            template=NotificationTemplate.APPOINTMENT_CONFIRMED,
            context={
                "client_name": client.first_name,
                "barber_name": f"{barber.first_name} {barber.last_name}",
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.start_time,
            },
        )

    async def notify_appointment_cancelled(
        self, appointment: Appointment, client: Client, reason: Optional[str] = None
    ) -> bool:
        """Enviar notificación cuando se cancela una cita."""
        return await self.send_email(
            recipient_email=client.email,
            template=NotificationTemplate.APPOINTMENT_CANCELLED,
            context={
                "client_name": client.first_name,
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.start_time,
                "reason": reason or "Sin especificar",
            },
        )

    async def notify_appointment_reminder(
        self, appointment: Appointment, client: Client, barber: Barber
    ) -> bool:
        """Enviar recordatorio de cita (típicamente 24h antes)."""
        # TODO: Validar que la cita sea mañana

        return await self.send_email(
            recipient_email=client.email,
            template=NotificationTemplate.APPOINTMENT_REMINDER,
            context={
                "client_name": client.first_name,
                "barber_name": f"{barber.first_name} {barber.last_name}",
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.start_time,
            },
        )

    async def notify_appointment_completed(
        self, appointment: Appointment, client: Client
    ) -> bool:
        """Enviar notificación cuando se completa una cita."""
        return await self.send_email(
            recipient_email=client.email,
            template=NotificationTemplate.APPOINTMENT_COMPLETED,
            context={
                "client_name": client.first_name,
                "appointment_id": str(appointment.id),
            },
        )

    # ===== NOTIFICACIONES DE PAGOS =====

    async def notify_payment_processed(
        self, recipient_email: str, amount: str, reference: str
    ) -> bool:
        """Enviar notificación cuando se procesa un pago."""
        return await self.send_email(
            recipient_email=recipient_email,
            template=NotificationTemplate.PAYMENT_PROCESSED,
            context={
                "amount": amount,
                "reference": reference,
                "date": datetime.now().isoformat(),
            },
        )

    async def notify_payment_failed(
        self, recipient_email: str, amount: str, reason: str
    ) -> bool:
        """Enviar notificación cuando falla un pago."""
        return await self.send_email(
            recipient_email=recipient_email,
            template=NotificationTemplate.PAYMENT_FAILED,
            context={
                "amount": amount,
                "reason": reason,
            },
        )

    async def notify_invoice_generated(
        self, recipient_email: str, invoice_number: str
    ) -> bool:
        """Enviar notificación cuando se genera una factura."""
        return await self.send_email(
            recipient_email=recipient_email,
            template=NotificationTemplate.INVOICE_GENERATED,
            context={
                "invoice_number": invoice_number,
                "date": datetime.now().isoformat(),
            },
        )

    # ===== NOTIFICACIONES DE CLIENTES =====

    async def notify_welcome(self, user: User) -> bool:
        """Enviar email de bienvenida."""
        return await self.send_email(
            recipient_email=user.email,
            template=NotificationTemplate.WELCOME,
            context={
                "name": user.first_name,
                "verification_url": f"{settings.APP_URL}/verify-email",
            },
        )

    async def notify_account_verified(self, user: User) -> bool:
        """Enviar notificación cuando se verifica cuenta."""
        return await self.send_email(
            recipient_email=user.email,
            template=NotificationTemplate.ACCOUNT_VERIFIED,
            context={
                "name": user.first_name,
                "login_url": f"{settings.APP_URL}/login",
            },
        )

    async def notify_password_reset(
        self, user: User, reset_token: str
    ) -> bool:
        """Enviar email de reset de contraseña."""
        return await self.send_email(
            recipient_email=user.email,
            template=NotificationTemplate.PASSWORD_RESET,
            context={
                "name": user.first_name,
                "reset_url": f"{settings.APP_URL}/reset-password?token={reset_token}",
                "expiry_hours": 24,
            },
        )

    # ===== NOTIFICACIONES DE MARKETING =====

    async def notify_loyalty_points_earned(
        self, recipient_email: str, points: int, total_points: int
    ) -> bool:
        """Enviar notificación cuando se ganan puntos de fidelización."""
        return await self.send_email(
            recipient_email=recipient_email,
            template=NotificationTemplate.LOYALTY_POINTS_EARNED,
            context={
                "points": points,
                "total_points": total_points,
            },
        )

    async def notify_vip_status_achieved(
        self, recipient_email: str, client_name: str
    ) -> bool:
        """Enviar notificación cuando cliente logra estado VIP."""
        return await self.send_email(
            recipient_email=recipient_email,
            template=NotificationTemplate.VIP_STATUS_ACHIEVED,
            context={
                "name": client_name,
                "benefits_url": f"{settings.APP_URL}/vip-benefits",
            },
        )

    async def notify_promotion(
        self,
        recipient_email: str,
        promotion_title: str,
        promotion_description: str,
    ) -> bool:
        """Enviar notificación de promoción."""
        return await self.send_email(
            recipient_email=recipient_email,
            template=NotificationTemplate.PROMOTION,
            context={
                "title": promotion_title,
                "description": promotion_description,
                "promotion_url": f"{settings.APP_URL}/promotions",
            },
        )

    # ===== MÉTODOS GENÉRICOS DE ENVÍO =====

    async def send_email(
        self,
        recipient_email: str,
        template: NotificationTemplate,
        context: dict,
        subject: Optional[str] = None,
    ) -> bool:
        """
        Enviar email usando plantilla.

        Args:
            recipient_email: Email destinatario
            template: Plantilla a usar
            context: Datos para la plantilla
            subject: Asunto personalizado

        Returns:
            bool: True si se envió exitosamente
        """
        try:
            # Obtener servicio de email
            email_service = get_email_service()
            
            # Generar asunto automáticamente si no se proporciona
            if not subject:
                subject_map = {
                    NotificationTemplate.APPOINTMENT_CREATED: "Cita Agendada - BarberPro",
                    NotificationTemplate.APPOINTMENT_CONFIRMED: "Cita Confirmada - BarberPro",
                    NotificationTemplate.APPOINTMENT_CANCELLED: "Cita Cancelada - BarberPro",
                    NotificationTemplate.APPOINTMENT_REMINDER: "Recordatorio de Cita - BarberPro",
                    NotificationTemplate.APPOINTMENT_COMPLETED: "Cita Completada - BarberPro",
                    NotificationTemplate.PAYMENT_PROCESSED: "Pago Procesado - BarberPro",
                    NotificationTemplate.PAYMENT_FAILED: "Pago Fallido - BarberPro",
                    NotificationTemplate.INVOICE_GENERATED: "Factura Generada - BarberPro",
                    NotificationTemplate.WELCOME: "Bienvenido a BarberPro",
                    NotificationTemplate.ACCOUNT_VERIFIED: "Cuenta Verificada - BarberPro",
                    NotificationTemplate.PASSWORD_RESET: "Reset de Contraseña - BarberPro",
                    NotificationTemplate.PROMOTION: "Promoción Especial - BarberPro",
                    NotificationTemplate.LOYALTY_POINTS_EARNED: "Puntos de Fidelización - BarberPro",
                    NotificationTemplate.VIP_STATUS_ACHIEVED: "¡Eres VIP! - BarberPro",
                }
                subject = subject_map.get(template, "Notificación de BarberPro")
            
            # Enviar email con plantilla
            return await email_service.send_template_email(
                recipient_email=recipient_email,
                recipient_name=context.get("name") or context.get("client_name", "Usuario"),
                subject=subject,
                template_name=template.value,
                template_data=context,
            )

        except Exception as e:
            logger.error(f"❌ Error enviando email: {str(e)}", exc_info=True)
            return False

    async def send_sms(
        self,
        phone_number: str,
        message: str,
    ) -> bool:
        """
        Enviar SMS.

        Args:
            phone_number: Número telefónico
            message: Mensaje

        Returns:
            bool: True si se envió exitosamente

        TODO: Implementar con proveedor real (Twilio, etc)
        """
        try:
            print(f"📱 SMS enviado a {phone_number}")
            return True
        except Exception as e:
            print(f"❌ Error enviando SMS: {str(e)}")
            return False

    async def send_push_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        data: Optional[dict] = None,
    ) -> bool:
        """
        Enviar notificación push.

        Args:
            user_id: ID del usuario
            title: Título
            message: Mensaje
            data: Datos adicionales

        Returns:
            bool: True si se envió exitosamente

        TODO: Implementar con Firebase o similar
        """
        try:
            print(f"🔔 Push notification enviada a usuario {user_id}")
            return True
        except Exception as e:
            print(f"❌ Error enviando push: {str(e)}")
            return False

    async def create_in_app_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.IN_APP,
    ) -> bool:
        """
        Crear notificación in-app.

        Args:
            user_id: ID del usuario
            title: Título
            message: Mensaje
            notification_type: Tipo de notificación

        Returns:
            bool: True si se creó exitosamente

        TODO: Implementar guardando en colección de notificaciones
        """
        try:
            # TODO: Guardar en MongoDB
            print(f"📬 In-app notification creada para usuario {user_id}")
            return True
        except Exception as e:
            print(f"❌ Error creando notificación: {str(e)}")
            return False

    # ===== UTILIDADES =====

    def get_template_html(
        self, template: NotificationTemplate, context: dict
    ) -> str:
        """
        Obtener HTML renderizado de una plantilla.

        Args:
            template: Plantilla
            context: Datos

        Returns:
            str: HTML de la plantilla
        """
        # TODO: Implementar con Jinja2
        return "<p>Template placeholder</p>"

    def validate_email(self, email: str) -> bool:
        """Validar formato de email."""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def validate_phone(self, phone: str) -> bool:
        """Validar formato de teléfono."""
        import re

        # Formato simple: 10 dígitos
        pattern = r"^\+?1?\d{9,15}$"
        return re.match(pattern, phone) is not None
