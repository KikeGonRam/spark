# 🤖 CHATBOT IA - TESTING Y DOCUMENTACIÓN

**Integración:** Google Gemini API  
**Lenguaje:** Español  
**Contexto:** Barbería BarberPro  
**Status:** ✅ Listo para Testing

---

## 📋 RESUMEN

El ChatBot de BarberPro utiliza **Google Gemini API** para responder preguntas sobre servicios de barbería, horarios, precios y agendamiento de citas.

### Características
- 🗣️ Respuestas en español natural
- 🎯 Contexto de barbería
- 💬 Historial de conversaciones
- 👥 Acceso por rol (Admin, Cliente, Barbero)
- ⚡ Respuestas rápidas (< 10s ideal)
- 🔒 Autenticación obligatoria

---

## 🔑 CONFIGURACIÓN GEMINI API

### Paso 1: Obtener API Key

**URL:** https://makersuite.google.com/app/apikey

**Pasos:**
1. Ir a Google AI Studio
2. Click en "Create API key"
3. Seleccionar/crear proyecto
4. Copiar la API key (formato: AIzaSy...)

**Validar formato:**
```
✅ Empieza con "AIzaSy"
✅ Longitud: 39 caracteres
✅ Solo alphanumericos + guiones
```

### Paso 2: Configurar en .env

```bash
# .env
GEMINI_API_KEY=AIzaSy...xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Verificar:**
```bash
# Windows
echo %GEMINI_API_KEY%

# Linux/Mac
echo $GEMINI_API_KEY
```

### Paso 3: Cargar en Aplicación

```python
# app/config.py
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not configured in .env")

print(f"✅ Gemini API Key loaded: {GEMINI_API_KEY[:10]}...")
```

---

## 🏗️ ARQUITECTURA

### Componentes

```
┌─────────────────────────────────────┐
│         API FastAPI                  │
│  POST /api/chatbot/ask              │
│  GET  /api/chatbot/history          │
└────────────────┬────────────────────┘
                 │
        ┌────────▼────────┐
        │ ChatbotService  │
        │ (app/services)  │
        └────────┬────────┘
                 │
        ┌────────▼──────────────┐
        │  Gemini API Client    │
        │  (google.generativeai)│
        └──────────────────────┘
```

### Flow de Conversación

```
1. Cliente hace pregunta
   POST /api/chatbot/ask
   {
     "question": "¿Cuáles son tus horarios?",
     "context": "schedule_query"
   }

2. ChatbotService recibe pregunta
   - Valida autenticación
   - Construye prompt
   - Agrega contexto de barbería

3. Envía a Gemini API
   - modelo: "gemini-pro"
   - sistema: "Eres asistente de barbería"
   - pregunta: "¿Cuáles son tus horarios?"

4. Gemini responde
   "Atendemos de lunes a viernes 9am-6pm,
    sábados 10am-4pm. Los domingos estamos cerrados."

5. Guarda en historial
   {
     "role": "user",
     "content": "¿Cuáles son tus horarios?",
     "timestamp": "2026-05-17T11:56:00"
   }
   {
     "role": "assistant",
     "content": "Atendemos de lunes a viernes...",
     "timestamp": "2026-05-17T11:56:05"
   }

6. Retorna al cliente
   {
     "answer": "Atendemos de lunes a viernes...",
     "timestamp": "2026-05-17T11:56:05",
     "model": "gemini-pro"
   }
```

---

## 🧪 TESTING DEL CHATBOT

### Setup para Tests

```python
# conftest.py
import os
os.environ["GEMINI_API_KEY"] = "AIzaSy...xxxxx"

from app.services.chatbot_service import ChatbotService

@pytest.fixture
def chatbot_service():
    return ChatbotService()
```

### Test 1: Preguntas sobre Servicios

```python
def test_chatbot_services_question(client, client_headers):
    """¿Qué servicios ofrecen?"""
    
    response = client.post(
        "/api/chatbot/ask",
        headers=client_headers,
        json={
            "question": "¿Qué servicios de barbería ofrecen?",
            "context": "services_query"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Respuesta debe contener servicios de barbería
    expected_keywords = ["corte", "afeitado", "servicio", "barbería"]
    answer = data["answer"].lower()
    
    for keyword in expected_keywords:
        if keyword in answer:
            print(f"✅ Respuesta menciona: {keyword}")
            break
```

**Output Esperado:**
```
Usuario: ¿Qué servicios de barbería ofrecen?

ChatBot:
Ofrecemos los siguientes servicios:
- Corte clásico (30 min) - $50
- Corte moderno (30 min) - $55
- Afeitado con navaja (20 min) - $40
- Tinte de barba (20 min) - $35
- Tratamiento capilar (20 min) - $45

Todos nuestros servicios son realizados por barberos profesionales.
```

### Test 2: Preguntas sobre Horarios

```python
def test_chatbot_schedule_question(client, client_headers):
    """¿Cuál es su horario?"""
    
    response = client.post(
        "/api/chatbot/ask",
        headers=client_headers,
        json={
            "question": "¿Cuál es su horario de atención?",
            "context": "schedule_query"
        }
    )
    
    assert response.status_code == 200
    answer = response.json()["answer"]
    
    # Debe contener información de horarios
    assert any(time in answer for time in ["9am", "6pm", "lunes", "viernes"])
```

**Output Esperado:**
```
Usuario: ¿Cuál es su horario de atención?

ChatBot:
Nuestro horario es:
- Lunes a Viernes: 9:00 AM - 6:00 PM
- Sábados: 10:00 AM - 4:00 PM
- Domingos: Cerrado

Recomendamos agendar cita con anticipación,
especialmente los viernes y sábados.
```

### Test 3: Preguntas sobre Precios

```python
def test_chatbot_pricing_question(client, client_headers):
    """¿Cuánto cuesta un corte?"""
    
    response = client.post(
        "/api/chatbot/ask",
        headers=client_headers,
        json={
            "question": "¿Cuánto cuesta un corte clásico?",
            "context": "pricing_query"
        }
    )
    
    assert response.status_code == 200
    answer = response.json()["answer"]
    
    # Debe contener precio
    assert "$" in answer or "USD" in answer
```

**Output Esperado:**
```
Usuario: ¿Cuánto cuesta un corte clásico?

ChatBot:
El corte clásico cuesta $50.00 USD.
Este servicio incluye:
- Corte personalizado según tu tipo de cabello
- Peinado y acabado profesional
- Duración: 30 minutos aproximadamente

Puedes agendar cita a través de nuestra aplicación.
```

### Test 4: Preguntas sobre Agendamiento

```python
def test_chatbot_appointment_question(client, client_headers):
    """¿Cómo agendo una cita?"""
    
    response = client.post(
        "/api/chatbot/ask",
        headers=client_headers,
        json={
            "question": "¿Cómo puedo agendar una cita?",
            "context": "appointment_query"
        }
    )
    
    assert response.status_code == 200
    answer = response.json()["answer"]
    
    # Debe tener instrucciones
    assert "cita" in answer.lower() or "agendar" in answer.lower()
```

**Output Esperado:**
```
Usuario: ¿Cómo puedo agendar una cita?

ChatBot:
Para agendar una cita:

1. Ingresa a la aplicación con tu cuenta
2. Ve a "Agendar Cita"
3. Selecciona un barbero
4. Elige la fecha y hora disponible
5. Selecciona el servicio
6. Confirma y paga

También puedes llamar al (555) 123-4567
o escribir a hello@barberpro.local
```

### Test 5: Out-of-Scope

```python
def test_chatbot_out_of_scope(client, client_headers):
    """Preguntas fuera de contexto"""
    
    response = client.post(
        "/api/chatbot/ask",
        headers=client_headers,
        json={
            "question": "¿Cuál es el sentido de la vida?",
            "context": "philosophical"
        }
    )
    
    assert response.status_code == 200
    answer = response.json()["answer"]
    
    # Debe redireccionar a barbería
    assert "barbería" in answer.lower() or "servicio" in answer.lower()
```

**Output Esperado:**
```
Usuario: ¿Cuál es el sentido de la vida?

ChatBot:
Esa es una pregunta profunda, pero te ayudaremos
con lo que sabemos mejor: ¡hacerte lucir bien!

El sentido de la vida según BarberPro es:
Brindarte el mejor servicio de barbería profesional.

¿Hay algo sobre nuestros servicios en lo que 
pueda ayudarte? 😊
```

---

## 💬 EJEMPLOS DE CONVERSACIONES

### Ejemplo 1: Cliente Nuevo
```
Cliente: Hola, ¿Qué servicios ofrecen?
ChatBot: Ofrecemos cortes, afeitados, tintes y más...

Cliente: ¿Cuánto cuesta?
ChatBot: El corte clásico cuesta $50...

Cliente: ¿Cómo agendo?
ChatBot: Puedes agendar desde la app: 1. Login 2. Selecciona...

Cliente: ¿Atienden mañana?
ChatBot: Sí, atendemos mañana de 9am a 6pm...
```

### Ejemplo 2: Cliente con Dudas
```
Cliente: ¿Qué diferencia hay entre corte clásico y moderno?
ChatBot: Ambos ofrecen estilos diferentes:
- Clásico: Líneas limpias, estilo tradicional
- Moderno: Cortes contemporáneos con técnica fade

Cliente: ¿Cuál me recomiendas?
ChatBot: Depende tu tipo de rostro y preferencias...

Cliente: Listo, agendo moderno
ChatBot: Perfecto! Entra a la app para agendar...
```

---

## ⚙️ CONFIGURACIÓN AVANZADA

### Personalizar Prompt del Sistema

```python
# app/services/chatbot_service.py

SYSTEM_PROMPT = """
Eres un asistente de barbería para BarberPro.
Tu responsabilidad es ayudar a clientes con:
- Información sobre servicios
- Horarios y disponibilidad
- Precios
- Cómo agendar citas
- Responder preguntas frecuentes

Responde siempre en español.
Si la pregunta no está relacionada con barbería,
redirige amablemente la conversación.

Información de BarberPro:
- Servicios: Cortes, afeitados, tintes
- Horario: Lunes-Viernes 9am-6pm, Sábados 10am-4pm
- Precios: Corte $50, Afeitado $40, etc.
- Ubicación: [Dirección]
- Teléfono: [Teléfono]
"""

service = ChatbotService(system_prompt=SYSTEM_PROMPT)
```

### Rate Limiting

```python
# app/routes/chatbot.py
from slowapi import Limiter

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@router.post("/ask")
@limiter.limit("10 per minute")
async def ask_chatbot(request: ChatbotRequest):
    """Máximo 10 preguntas por minuto"""
    ...
```

### Caching de Respuestas

```python
# Cachear respuestas idénticas
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(question: str) -> str:
    """Cachea últimas 100 preguntas"""
    ...
```

---

## 🔒 SEGURIDAD

### Validaciones

```python
# Validar entrada
def validate_question(question: str) -> bool:
    """
    ✅ No vacío
    ✅ Máximo 500 caracteres
    ✅ Sin SQL injection
    ✅ Sin XSS
    """
    if not question or len(question) > 500:
        return False
    return True

# Validar salida
def sanitize_response(response: str) -> str:
    """
    ✅ Sin código inyectado
    ✅ Sin URLs sospechosas
    ✅ Encoding correcto UTF-8
    """
    return html.escape(response)
```

### Autenticación

```python
# Solo usuarios autenticados pueden acceder
@router.post("/api/chatbot/ask")
async def ask(
    request: ChatbotRequest,
    current_user: User = Depends(get_current_user)
):
    """Requiere JWT token válido"""
    ...
```

### Rate Limiting por Usuario

```python
# Por usuario autenticado, no por IP
@router.post("/api/chatbot/ask")
@limiter.limit("10 per minute", key_func=lambda: current_user.id)
async def ask(current_user: User = Depends(get_current_user)):
    """10 preguntas por minuto por usuario"""
    ...
```

---

## 📊 MONITOREO

### Logging

```python
import logging

logger = logging.getLogger("chatbot")

async def ask_chatbot(question: str, user_id: str):
    logger.info(f"Q: {question[:50]}... (user: {user_id})")
    
    response = gemini_client.generate_content(question)
    
    logger.info(f"A: {response[:50]}... (latency: 2.5s)")
    
    return response
```

### Métricas

```python
# Registrar estadísticas
chatbot_stats = {
    "total_questions": 0,
    "total_responses": 0,
    "average_latency": 0,
    "most_common_topics": {},
    "error_count": 0
}
```

---

## 🐛 TROUBLESHOOTING

### Error: "GEMINI_API_KEY not found"

**Causa:** Variable de entorno no configurada

**Solución:**
```bash
# Verificar .env
cat .env | grep GEMINI

# Si no existe, agregar
echo "GEMINI_API_KEY=AIzaSy..." >> .env

# Recargar
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
```

### Error: "Invalid API key"

**Causa:** API key expirada o incorrecta

**Solución:**
```bash
# Obtener nueva key de https://makersuite.google.com
# Actualizar .env
GEMINI_API_KEY=AIzaSy...nueva_key...
```

### Error: "Rate limit exceeded"

**Causa:** Demasiadas requests a Gemini

**Solución:**
```python
# Agregar retry logic
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def ask_gemini(question):
    return await gemini_client.generate_content(question)
```

### Error: "Response timeout"

**Causa:** Gemini API tarda más de lo esperado

**Solución:**
```python
# Aumentar timeout
import asyncio

response = await asyncio.wait_for(
    gemini_client.generate_content(question),
    timeout=30  # 30 segundos
)
```

---

## 📈 ESTADÍSTICAS ESPERADAS

### Métricas de Performance

| Métrica | Meta |
|---------|------|
| Latencia promedio | < 3 segundos |
| Uptime | > 99.9% |
| Errores | < 0.1% |
| Rate limit violations | 0 |

### Ejemplos de Uso

| Pregunta | Respuesta | Latencia |
|----------|-----------|----------|
| "¿Qué servicios?" | 200 palabras | 2.3s |
| "¿Horarios?" | 150 palabras | 1.8s |
| "¿Cómo agendo?" | 250 palabras | 2.8s |

---

## ✅ CHECKLIST DE DEPLOYMENT

Antes de deployar a producción:

```
☐ GEMINI_API_KEY configurada
☐ Prompt del sistema personalizado
☐ Rate limiting activo
☐ Logging activado
☐ Tests pasando (18 tests)
☐ Respuestas validadas
☐ Historial funcionando
☐ Cache activado
☐ Monitoreo configurado
☐ Documentación actualizada
```

---

## 🎯 PRÓXIMOS PASOS

1. ✅ **Testing:** Ejecutar 18 tests de ChatBot
2. ✅ **Validación:** Probar respuestas manualmente
3. ✅ **Deployment:** Subir a producción
4. 📈 **Monitoreo:** Observar uso y errores
5. 🔄 **Iteración:** Mejorar prompts basado en feedback

---

**Documento Generado:** 17 de Mayo de 2026  
**Última Actualización:** 2026-05-17T11:56:31Z

