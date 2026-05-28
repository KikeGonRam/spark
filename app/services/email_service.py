"""
Email Service - Envío de correos mediante SMTP
Utiliza aiosmtplib para envío asincrónico a Mailpit
"""

import logging
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio de envío de emails via SMTP"""
    
    def __init__(
        self,
        host: str = settings.MAIL_HOST,
        port: int = settings.MAIL_PORT,
        username: Optional[str] = settings.MAIL_USERNAME,
        password: Optional[str] = settings.MAIL_PASSWORD,
        from_email: str = settings.MAIL_FROM,
        from_name: str = settings.MAIL_FROM_NAME,
    ):
        """
        Inicializar servicio de email
        
        Args:
            host: Host SMTP
            port: Puerto SMTP
            username: Username SMTP
            password: Password SMTP
            from_email: Email remitente
            from_name: Nombre remitente
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.from_name = from_name
    
    async def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        recipient_name: Optional[str] = None,
    ) -> bool:
        """
        Enviar email via SMTP
        
        Args:
            recipient_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML
            text_content: Contenido de texto plano (opcional)
            recipient_name: Nombre del destinatario (opcional)
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Validar entrada
            if not recipient_email or not subject or not html_content:
                logger.error("Email inválido: datos incompletos")
                return False
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = recipient_email
            
            # Agregar parte de texto plano
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            else:
                # Generar texto plano si no se proporciona
                msg.attach(MIMEText(f"Email: {subject}", 'plain'))
            
            # Agregar parte HTML
            msg.attach(MIMEText(html_content, 'html'))
            
            # Enviar via SMTP
            logger.info(f"Enviando email a {recipient_email}...")
            
            async with aiosmtplib.SMTP(hostname=self.host, port=self.port) as smtp:
                # Mailpit no requiere autenticación
                # Solo autenticar si está configurado y no es Mailpit
                if self.username and self.password and "mailpit" not in self.host.lower():
                    try:
                        await smtp.login(self.username, self.password)
                    except Exception as e:
                        logger.warning(f"Autenticación SMTP fallida (continuando sin auth): {e}")
                
                await smtp.send_message(msg)
            
            logger.info(f"✅ Email enviado exitosamente a {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email a {recipient_email}: {str(e)}", exc_info=True)
            return False
    
    async def send_template_email(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        template_name: str,
        template_data: dict,
    ) -> bool:
        """
        Enviar email usando plantilla HTML
        
        Args:
            recipient_email: Email del destinatario
            recipient_name: Nombre del destinatario
            subject: Asunto del email
            template_name: Nombre de la plantilla
            template_data: Datos para la plantilla
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Generar HTML de la plantilla
            html_content = self._render_template(template_name, template_data)
            
            # Enviar email
            return await self.send_email(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                recipient_name=recipient_name,
            )
            
        except Exception as e:
            logger.error(f"Error enviando email con plantilla: {str(e)}", exc_info=True)
            return False
    
    def _render_template(self, template_name: str, data: dict) -> str:
        """
        Renderizar una plantilla HTML
        
        Args:
            template_name: Nombre de la plantilla
            data: Datos para interpolar
            
        Returns:
            str: HTML renderizado
        """
        # Templates simples (sin Jinja2 por ahora)
        templates = {
            "welcome": """
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2>¡Bienvenido a BarberPro, {name}!</h2>
                        <p>Tu cuenta ha sido creada exitosamente.</p>
                        <p><a href="{verification_url}">Verificar tu cuenta</a></p>
                        <p>Equipo BarberPro</p>
                    </body>
                </html>
            """,
            "appointment_created": """
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2>Cita Confirmada, {client_name}!</h2>
                        <p>Tu cita ha sido agendada con {barber_name}</p>
                        <p><strong>Fecha:</strong> {appointment_date}</p>
                        <p><strong>Hora:</strong> {appointment_time}</p>
                        <p>¡Gracias por usar BarberPro!</p>
                    </body>
                </html>
            """,
            "appointment_reminder": """
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2>Recordatorio de Cita</h2>
                        <p>Hola {client_name},</p>
                        <p>Te recordamos que tienes una cita mañana con {barber_name}</p>
                        <p><strong>Hora:</strong> {appointment_time}</p>
                        <p>¡Nos vemos pronto!</p>
                    </body>
                </html>
            """,
            "payment_processed": """
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2>Pago Procesado</h2>
                        <p>Tu pago ha sido procesado exitosamente.</p>
                        <p><strong>Monto:</strong> {amount}</p>
                        <p><strong>Referencia:</strong> {reference}</p>
                        <p><strong>Fecha:</strong> {date}</p>
                        <p>Gracias por tu compra!</p>
                    </body>
                </html>
            """,
            "password_reset": """
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <h2>Reset de Contraseña</h2>
                        <p>Hola {name},</p>
                        <p>Para resetear tu contraseña, haz clic en el siguiente enlace:</p>
                        <p><a href="{reset_url}">Resetear Contraseña</a></p>
                        <p>Este enlace expira en {expiry_hours} horas.</p>
                        <p>Si no solicitaste esto, ignora este mensaje.</p>
                    </body>
                </html>
            """,
        }
        
        # Obtener plantilla o usar genérica
        html = templates.get(template_name, "<p>Email genérico</p>")
        
        # Interpolar variables (simple string.format)
        try:
            return html.format(**data)
        except KeyError as e:
            logger.warning(f"Variable faltante en plantilla {template_name}: {e}")
            return html
    
    async def send_verification_email(self, recipient_email: str, recipient_name: str) -> bool:
        """
        Enviar email de verificación de cuenta
        
        Args:
            recipient_email: Email del destinatario
            recipient_name: Nombre del destinatario
            
        Returns:
            bool: True si se envió correctamente
        """
        try:
            html_content = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px;">
                            <h2 style="color: #333;">¡Bienvenido a BarberPro, {recipient_name}!</h2>
                            <p style="color: #666;">Tu cuenta ha sido creada exitosamente.</p>
                            <p style="color: #666;">Puedes comenzar a usar BarberPro ahora mismo.</p>
                            <div style="text-align: center; padding: 20px; border-top: 1px solid #eee; margin-top: 20px;">
                                <p style="color: #999; font-size: 12px;">© 2026 BarberPro. Todos los derechos reservados.</p>
                            </div>
                        </div>
                    </body>
                </html>
            """
            
            return await self.send_email(
                recipient_email=recipient_email,
                subject="¡Bienvenido a BarberPro! Tu cuenta ha sido creada",
                html_content=html_content,
                recipient_name=recipient_name,
            )
        except Exception as e:
            logger.error(f"Error enviando email de verificación a {recipient_email}: {str(e)}", exc_info=True)
            return False


# Instancia global
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Factory para obtener instancia del servicio de email"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
