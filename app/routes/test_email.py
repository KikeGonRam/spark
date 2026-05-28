"""
Test Email Routes - Endpoints para pruebas de email
Endpoints: /api/test/email/*
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
import logging

from app.services.email_service import get_email_service

logger = logging.getLogger(__name__)

router = APIRouter()


class TestEmailRequest(BaseModel):
    """Solicitud de prueba de email"""
    email: EmailStr = Field(..., description="Email destino")
    subject: str = Field(default="Prueba de Email - BarberPro", description="Asunto")
    name: str = Field(default="Usuario", description="Nombre del usuario")


class TestEmailResponse(BaseModel):
    """Respuesta de prueba de email"""
    success: bool = Field(..., description="Indica si se envió")
    message: str = Field(..., description="Mensaje de estado")
    email: str = Field(..., description="Email destino")


@router.post("/email/test", response_model=TestEmailResponse, tags=["Test"])
async def test_send_email(payload: TestEmailRequest):
    """
    Enviar email de prueba a Mailpit.
    
    Este endpoint es solo para pruebas y diagnóstico.
    
    **Request body:**
    - email: Email destino
    - subject: Asunto (opcional)
    - name: Nombre del usuario (opcional)
    
    **Response:**
    - success: True si se envió
    - message: Detalles del envío
    - email: Email destino
    
    **Ejemplo:**
    ```
    POST /api/test/email/test
    {
      "email": "test@example.com",
      "subject": "Prueba",
      "name": "Juan"
    }
    ```
    """
    try:
        email_service = get_email_service()
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                    <h1 style="color: #333;">✅ Email de Prueba Exitoso</h1>
                    <p>Hola <strong>{payload.name}</strong>,</p>
                    
                    <p>Este es un email de prueba del sistema BarberPro.</p>
                    
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>Detalles de la Prueba:</h3>
                        <ul>
                            <li><strong>Email:</strong> {payload.email}</li>
                            <li><strong>Asunto:</strong> {payload.subject}</li>
                            <li><strong>Timestamp:</strong> {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                            <li><strong>Servidor:</strong> BarberPro API</li>
                        </ul>
                    </div>
                    
                    <p>Si ves este email, significa que:</p>
                    <ul>
                        <li>✅ La configuración SMTP es correcta</li>
                        <li>✅ Mailpit está recibiendo emails</li>
                        <li>✅ El servicio de notificaciones funciona</li>
                    </ul>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <p><em>Email enviado automáticamente por BarberPro</em></p>
                    <p style="color: #999; font-size: 12px;">No respondas este email</p>
                </div>
            </body>
        </html>
        """
        
        success = await email_service.send_email(
            recipient_email=payload.email,
            subject=payload.subject,
            html_content=html_content,
            recipient_name=payload.name,
        )
        
        if success:
            return TestEmailResponse(
                success=True,
                message=f"Email de prueba enviado exitosamente a {payload.email}. Verifica Mailpit en http://localhost:8025",
                email=payload.email,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error enviando email - verifica los logs"
            )
            
    except Exception as e:
        logger.error(f"Error en test_send_email: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@router.get("/email/config", tags=["Test"])
async def get_email_config():
    """
    Obtener configuración actual de email (para diagnóstico).
    
    **Response:**
    - host: Host SMTP
    - port: Puerto SMTP
    - from_email: Email remitente
    - from_name: Nombre remitente
    """
    from app.config import settings
    
    return {
        "host": settings.MAIL_HOST,
        "port": settings.MAIL_PORT,
        "from_email": settings.MAIL_FROM,
        "from_name": settings.MAIL_FROM_NAME,
        "username": settings.MAIL_USERNAME or "No configurado",
        "driver": settings.MAIL_DRIVER,
        "mailpit_ui": "http://localhost:8025",
    }
