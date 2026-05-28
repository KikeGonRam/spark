"""
ChatBot Service - Conversación con IA (Gemini)
Maneja conversaciones con Google Gemini API
"""

import logging
from typing import Optional, List, Dict
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service para interactuar con Gemini API"""
    
    SYSTEM_PROMPT = """Eres un asistente de atención al cliente para una barbería profesional llamada BarberPro.
Tu rol es ayudar a los clientes con información sobre servicios, citas, precios y políticas de la barbería.

INFORMACIÓN DE LA BARBERÍA:
- Nombre: BarberPro
- Servicios: Cortes de cabello, rasurado, tratamientos capilares, diseño de barba
- Horario: Lunes a Viernes 9AM-8PM, Sábado 10AM-6PM, Domingo Cerrado
- Ubicación: Centro comercial principal, Calle Principal 123
- Teléfono: +1-800-BARBER1
- Precios: Corte $25, Rasurado $20, Tratamiento $35, Barba $30

INSTRUCCIONES:
1. Responde siempre en español
2. Sé amable, profesional y conciso
3. Si el cliente pregunta por un servicio específico, proporciona detalles
4. Si es una pregunta sobre citas, sugiere agendar por teléfono o la app
5. No des información que no tengas confirmada
6. Mantén un tono conversacional y cálido
7. Si no puedes ayudar, sugiere contactar directamente a la barbería"""

    def __init__(self):
        """Inicializar servicio con Gemini API"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.conversation_history: List[Dict[str, str]] = []
    
    async def chat(self, user_message: str) -> str:
        """
        Procesar mensaje del usuario y obtener respuesta de Gemini
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Respuesta del chatbot
        """
        try:
            if not user_message or not user_message.strip():
                return "¿Cómo puedo ayudarte hoy? Pregúntame sobre nuestros servicios, horarios o cómo agendar una cita."
            
            # Agregar mensaje del usuario al historial
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Construir prompt con contexto
            messages = f"{self.SYSTEM_PROMPT}\n\n"
            messages += "Historial de conversación:\n"
            for msg in self.conversation_history[-5:]:  # Últimos 5 mensajes para contexto
                role = "Cliente" if msg["role"] == "user" else "BarberPro"
                messages += f"{role}: {msg['content']}\n"
            
            # Llamar a Gemini API
            response = self.model.generate_content(messages)
            assistant_message = response.text
            
            # Agregar respuesta al historial
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error en ChatBot: {e}")
            return f"Lo siento, hubo un error procesando tu solicitud: {str(e)}"
    
    def clear_history(self):
        """Limpiar historial de conversación"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Obtener historial de conversación"""
        return self.conversation_history
    
    async def get_response(self, user_message: str) -> str:
        """
        Alias para chat() para compatibilidad con tests
        
        Args:
            user_message: Mensaje del usuario
            
        Returns:
            Respuesta del chatbot
        """
        return await self.chat(user_message)


# Instancia global (simplista, en producción usar DI container)
_chatbot_instance: Optional[ChatbotService] = None


def get_chatbot_service() -> ChatbotService:
    """Factory para obtener instancia del servicio"""
    global _chatbot_instance
    if _chatbot_instance is None:
        try:
            _chatbot_instance = ChatbotService()
        except ValueError as e:
            logger.error(f"ChatBot initialization failed: {e}")
            raise
    return _chatbot_instance
