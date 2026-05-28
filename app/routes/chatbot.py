"""
ChatBot Routes - Conversación con IA
Endpoints: /api/chatbot/*
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict
import logging

from app.services.chatbot_service import get_chatbot_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# MODELS
# ============================================================================

class ChatMessage(BaseModel):
    """Mensaje de chat"""
    message: str = Field(..., min_length=1, max_length=1000, description="Mensaje del usuario")


class ChatResponse(BaseModel):
    """Respuesta del chatbot"""
    message: str = Field(..., description="Respuesta del chatbot")
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")


class ConversationHistory(BaseModel):
    """Historial de conversación"""
    history: List[Dict[str, str]] = Field(default=[], description="Historial de mensajes")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/chat", response_model=ChatResponse, tags=["ChatBot"])
async def send_message(payload: ChatMessage):
    """
    Enviar mensaje al chatbot IA y obtener respuesta.
    
    El chatbot es un asistente inteligente para la barbería que responde
    preguntas sobre servicios, horarios, precios y políticas.
    
    **Request body:**
    - message: Pregunta o mensaje (1-1000 caracteres)
    
    **Response:**
    - message: Respuesta del chatbot
    - success: Indica si fue exitoso
    
    **Ejemplos:**
    - "¿Cuál es tu horario de atención?"
    - "¿Cuánto cuesta un corte?"
    - "¿Cómo agendo una cita?"
    """
    try:
        # Validar entrada
        if not payload.message or not payload.message.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El mensaje no puede estar vacío"
            )
        
        # Obtener servicio del chatbot
        chatbot_service = get_chatbot_service()
        
        # Procesar mensaje
        response = await chatbot_service.chat(payload.message.strip())
        
        return ChatResponse(message=response, success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ChatBot error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}"
        )


@router.get("/history", response_model=ConversationHistory, tags=["ChatBot"])
async def get_conversation_history():
    """
    Obtener el historial de conversación actual.
    
    Retorna todos los mensajes intercambiados en la conversación actual.
    
    **Response:**
    - history: Lista de mensajes (role: "user" o "assistant", content: texto)
    """
    try:
        chatbot_service = get_chatbot_service()
        history = chatbot_service.get_history()
        return ConversationHistory(history=history)
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error obteniendo historial"
        )


@router.delete("/history", response_model=dict, tags=["ChatBot"])
async def clear_conversation_history():
    """
    Limpiar el historial de conversación.
    
    Elimina todos los mensajes previos de la conversación.
    
    **Response:**
    - message: Confirmación
    - success: Indica si fue exitoso
    """
    try:
        chatbot_service = get_chatbot_service()
        chatbot_service.clear_history()
        return {
            "message": "Historial de conversación eliminado",
            "success": True
        }
    except Exception as e:
        logger.error(f"Error clearing history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error limpiando historial"
        )
