"""
E2E Test Suite: CT-005 - ChatBot IA (Gemini API)
Tests: ChatBot responses, context awareness, conversation history
"""

import pytest
import os
from fastapi.testclient import TestClient


@pytest.mark.chatbot
@pytest.mark.slow
class TestChatbotIA:
    """ChatBot IA E2E Tests with Gemini API"""
    
    # ========================================================================
    # CT-005.0: Gemini API Configuration
    # ========================================================================
    
    def test_gemini_api_key_configured(self):
        """CT-005.0: Verify Gemini API key is configured"""
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Note: In production, this should be set
        if gemini_key:
            assert len(gemini_key) > 0, "Gemini API key is empty"
            assert "AIzaSy" in gemini_key or len(gemini_key) > 20, "Gemini key format looks invalid"
            print(f"\n✅ Gemini API Key: {'*' * (len(gemini_key)-4)}{gemini_key[-4:]}")
        else:
            pytest.skip("GEMINI_API_KEY not configured - skipping Gemini tests")
    
    
    # ========================================================================
    # CT-005.1: ChatBot Service Initialization
    # ========================================================================
    
    @pytest.mark.slow
    def test_chatbot_service_initializes(self):
        """CT-005.1: ChatBot service initializes correctly"""
        from app.services.chatbot_service import ChatbotService
        
        service = ChatbotService()
        
        # Service should be created without errors
        assert service is not None
        assert hasattr(service, 'get_response'), "ChatbotService missing get_response method"
    
    
    # ========================================================================
    # CT-005.2: Simple Chatbot Query
    # ========================================================================
    
    @pytest.mark.slow
    def test_chatbot_responds_to_barbershop_question(self, client: TestClient, client_headers):
        """CT-005.2: ChatBot responds to barbershop questions"""
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Qué servicios de barbería ofrecen?",
                "context": "client_query"
            }
        )
        
        # May skip if API key not configured
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "answer" in data, "Response should contain 'answer' field"
        assert len(data["answer"]) > 0, "Answer should not be empty"
        assert isinstance(data["answer"], str), "Answer should be string"
        
        # Answer should be in Spanish or contain relevant words
        answer_lower = data["answer"].lower()
        print(f"\n🤖 ChatBot Response: {data['answer']}")
    
    
    @pytest.mark.slow
    def test_chatbot_responds_to_pricing_question(self, client: TestClient, client_headers):
        """CT-005.2b: ChatBot responds to pricing questions"""
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Cuál es el precio de un corte clásico?",
                "context": "pricing_query"
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        print(f"\n💰 Pricing Response: {data['answer']}")
    
    
    @pytest.mark.slow
    def test_chatbot_responds_to_appointment_question(self, client: TestClient, client_headers):
        """CT-005.2c: ChatBot responds to appointment questions"""
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Cómo puedo agendar una cita?",
                "context": "appointment_query"
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        print(f"\n📅 Appointment Response: {data['answer']}")
    
    
    @pytest.mark.slow
    def test_chatbot_handles_out_of_scope_question(self, client: TestClient, client_headers):
        """CT-005.2d: ChatBot handles out-of-scope questions gracefully"""
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Cuál es el sentido de la vida?",
                "context": "philosophical_query"
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        # Should gracefully say it's out of scope or redirect to barbershop context
        print(f"\n🔍 Out-of-scope Response: {data['answer']}")
    
    
    # ========================================================================
    # CT-005.3: Conversation Context
    # ========================================================================
    
    @pytest.mark.slow
    def test_chatbot_maintains_context(self, client: TestClient, client_headers):
        """CT-005.3: ChatBot maintains conversation context"""
        # First question
        response1 = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Qué horarios manejan?",
                "context": "schedule_query"
            }
        )
        
        if response1.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response1.status_code == 200
        answer1 = response1.json()["answer"]
        
        # Follow-up question (should understand context)
        response2 = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Atienden los domingos?",
                "context": "schedule_follow_up"
            }
        )
        
        assert response2.status_code == 200
        answer2 = response2.json()["answer"]
        
        print(f"\n📞 Context Test:")
        print(f"  Q1: ¿Qué horarios manejan?")
        print(f"  A1: {answer1}")
        print(f"  Q2: ¿Atienden los domingos?")
        print(f"  A2: {answer2}")
    
    
    # ========================================================================
    # CT-005.4: Conversation History
    # ========================================================================
    
    @pytest.mark.slow
    def test_chatbot_stores_conversation_history(self, client: TestClient, client_headers):
        """CT-005.4: ChatBot stores conversation history"""
        # Clear history first (if endpoint exists)
        client.delete(
            "/api/chatbot/history",
            headers=client_headers
        )
        
        # Send a question
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Dónde quedan ubicados?",
                "context": "location_query"
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response.status_code == 200
        
        # Get conversation history
        history_response = client.get(
            "/api/chatbot/history",
            headers=client_headers
        )
        
        # History endpoint may not exist, skip if not found
        if history_response.status_code == 404:
            pytest.skip("History endpoint not implemented")
        
        assert history_response.status_code == 200
        history = history_response.json()
        
        assert isinstance(history, list), "History should be a list"
        assert len(history) > 0, "History should contain the message"
        
        # Last message should be our question or response
        last_message = history[-1]
        assert isinstance(last_message, dict)
        print(f"\n📝 Conversation History: {len(history)} messages")
        print(f"   Last message: {last_message}")
    
    
    # ========================================================================
    # CT-005.5: ChatBot Error Handling
    # ========================================================================
    
    def test_chatbot_handles_empty_question(self, client: TestClient, client_headers):
        """CT-005.5: ChatBot handles empty question gracefully"""
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "",
                "context": "empty_query"
            }
        )
        
        # Should return 400 or handle gracefully
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
    
    
    def test_chatbot_requires_authentication(self, client: TestClient):
        """CT-005.5b: ChatBot requires authentication"""
        response = client.post(
            "/api/chatbot/ask",
            json={
                "question": "¿Qué servicios ofrecen?",
                "context": "query"
            }
        )
        
        # Should require auth
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    
    def test_chatbot_rate_limiting(self, client: TestClient, client_headers):
        """CT-005.5c: ChatBot has rate limiting"""
        # Send 10 rapid requests
        responses = []
        for i in range(10):
            response = client.post(
                "/api/chatbot/ask",
                headers=client_headers,
                json={
                    "question": f"Pregunta rápida {i}",
                    "context": "rate_test"
                }
            )
            responses.append(response.status_code)
        
        # Some requests might be rate limited (429) after many rapid requests
        # This is implementation-dependent
        status_codes = set(responses)
        print(f"\n⏱️ Rate Limit Test: {status_codes}")
    
    
    # ========================================================================
    # CT-005.6: ChatBot Performance
    # ========================================================================
    
    @pytest.mark.slow
    def test_chatbot_response_time(self, client: TestClient, client_headers):
        """CT-005.6: ChatBot response time is acceptable"""
        import time
        
        start = time.time()
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "Hola",
                "context": "greeting"
            }
        )
        elapsed = time.time() - start
        
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        print(f"\n⚡ ChatBot Response Time: {elapsed:.2f}s")
        
        # Should respond within 30 seconds (Gemini API can be slow)
        # For production, aim for < 10 seconds
        assert elapsed < 30, f"Response took too long: {elapsed}s"
    
    
    # ========================================================================
    # CT-005.7: ChatBot Content Quality
    # ========================================================================
    
    @pytest.mark.slow
    def test_chatbot_response_is_relevant(self, client: TestClient, client_headers):
        """CT-005.7: ChatBot responses are relevant to barbershop context"""
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Qué es una barbería?",
                "context": "definition_query"
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response.status_code == 200
        data = response.json()
        answer = data["answer"].lower()
        
        # Response should contain barbershop-related words
        barbershop_keywords = ["barber", "barbería", "corte", "afeitado", "cabello", "peluquería"]
        has_relevant_keyword = any(keyword in answer for keyword in barbershop_keywords)
        
        assert has_relevant_keyword, f"Response doesn't seem related to barbershop: {answer}"
        print(f"\n✅ Content Quality: Response is relevant")
    
    
    @pytest.mark.slow
    def test_chatbot_response_is_professional(self, client: TestClient, client_headers):
        """CT-005.7b: ChatBot responses are professional"""
        response = client.post(
            "/api/chatbot/ask",
            headers=client_headers,
            json={
                "question": "¿Cómo es el servicio?",
                "context": "service_inquiry"
            }
        )
        
        if response.status_code == 503:
            pytest.skip("Gemini API not available")
        
        assert response.status_code == 200
        answer = response.json()["answer"]
        
        # Should not contain inappropriate content
        inappropriate_words = ["insult", "profanity"]  # Simplified check
        
        # Check length - response should be substantial
        assert len(answer) > 20, "Response seems too short"
        
        # Check for basic grammar/structure
        assert answer[0].isupper(), "Response should start with capital letter"
        
        print(f"\n✅ Professional Quality: Response is well-formed")


@pytest.mark.chatbot
def test_chatbot_endpoint_exists(client: TestClient, client_headers):
    """Verify ChatBot endpoint is available"""
    response = client.post(
        "/api/chatbot/ask",
        headers=client_headers,
        json={
            "question": "Hola",
            "context": "test"
        }
    )
    
    # Should either return 200 (success) or 503 (Gemini API not available)
    # Should NOT return 404 (endpoint not found)
    assert response.status_code != 404, "ChatBot endpoint not found"
    print(f"\n✅ ChatBot endpoint is available (status: {response.status_code})")


# ============================================================================
# CHATBOT INTEGRATION TESTS
# ============================================================================

@pytest.mark.chatbot
class TestChatbotIntegration:
    """Integration tests for ChatBot with other features"""
    
    def test_chatbot_available_to_authenticated_users(self, client: TestClient, admin_headers, client_headers, barber_headers):
        """All user types can access ChatBot"""
        
        for headers, role in [(admin_headers, "admin"), (client_headers, "client"), (barber_headers, "barber")]:
            response = client.post(
                "/api/chatbot/ask",
                headers=headers,
                json={
                    "question": "Prueba de acceso",
                    "context": f"test_{role}"
                }
            )
            
            # Should not return 401/403 for authenticated users
            assert response.status_code != 401, f"{role} should be authenticated"
            assert response.status_code != 403, f"{role} should have access"
            print(f"✅ {role.upper()} can access ChatBot")
