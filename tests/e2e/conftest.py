"""
E2E Testing Fixtures and Configuration
Tests for BarberPro Python - End-to-End Testing
Roles: Admin, Client, Barber
"""

import pytest
from starlette.testclient import TestClient
from typing import Dict
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.main import app

logger = logging.getLogger(__name__)

# ============================================================================
# HTTP CLIENT SETUP  
# ============================================================================

@pytest.fixture
def client():
    """Starlette TestClient - handles lifespan events properly"""
    # This TestClient automatically manages the lifespan events
    # including MongoDB connection
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True, scope="function")
def cleanup_db_around_tests(client: TestClient):
    """Comprehensive database cleanup before and after each test"""
    from database.connection import MongoDBConnection
    
    async def clear_test_data():
        """Clear collections that might have test data"""
        try:
            db = MongoDBConnection.get_db()
            if db is not None:
                # Clear all collections EXCEPT admin user (created per fixture)
                collections_to_clear = [
                    "barbers",
                    "clients",
                    "appointments",
                    "services",
                    "payments",
                    "schedules",
                    "special_hours",
                    "holidays",
                ]
                for collection in collections_to_clear:
                    try:
                        await db[collection].delete_many({})
                    except Exception:
                        pass
                
                # For users, only clear test users (not admin@example.com)
                await db["users"].delete_many({
                    "email": {"$ne": "admin@example.com"}
                })
        except Exception as e:
            logger.warning(f"Database cleanup error: {e}")
    
    # Clear before test  
    try:
        asyncio.run(clear_test_data())
    except Exception as e:
        logger.warning(f"Pre-test cleanup failed: {e}")
    
    yield
    
    # Clear after test
    try:
        asyncio.run(clear_test_data())
    except Exception as e:
        logger.warning(f"Post-test cleanup failed: {e}")


# ============================================================================
# TEST DATA - BASE URLS AND CONFIG
# ============================================================================

API_URL = "/api"

@pytest.fixture
def unique_email(request) -> str:
    """Generate unique email for test isolation"""
    import time
    test_name = request.node.name
    timestamp = int(time.time() * 1000)
    return f"{test_name}_{timestamp}@barberpro.example.com"

# Test accounts credentials
TEST_ADMIN = {
    "email": "admin@example.com",
    "password": "AdminE2E@2026",
    "name": "Admin E2E Test",
    "role": "admin"
}

TEST_CLIENT = {
    "email": "cliente@example.com",
    "password": "ClientE2E@2026",
    "name": "Juan Cliente Test",
    "role": "client"
}

TEST_BARBER = {
    "email": "barbero@example.com",
    "password": "BarberoE2E@2026",
    "name": "Carlos Barbero Test",
    "specialization": ["Cortes Profesionales"]
}


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture(scope="function")
def admin_token(client: TestClient) -> str:
    """Get admin JWT token"""
    # First, try login (might already exist)
    login_response = client.post(
        f"{API_URL}/auth/login",
        json={
            "email": TEST_ADMIN["email"],
            "password": TEST_ADMIN["password"]
        }
    )
    
    if login_response.status_code == 200:
        return login_response.json()["token"]
    
    # If login fails, register
    register_response = client.post(
        f"{API_URL}/auth/register",
        json={
            "email": TEST_ADMIN["email"],
            "password": TEST_ADMIN["password"],
            "name": TEST_ADMIN["name"],
            "role": TEST_ADMIN["role"]
        }
    )
    
    assert register_response.status_code in [201, 200], f"Admin registration failed: {register_response.text}"
    data = register_response.json()
    token = data.get("token") or data.get("access_token")
    assert token, f"No token in register response: {data}"
    return token


@pytest.fixture
def admin_headers(admin_token: str) -> Dict[str, str]:
    """Admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def client_token(client: TestClient) -> str:
    """Get client JWT token"""
    # Always create a fresh client with unique email for each test
    import time
    unique_email = f"client{int(time.time() * 1000)}@barberpro.example.com"
    
    response = client.post(
        f"{API_URL}/auth/register",
        json={
            "email": unique_email,
            "password": TEST_CLIENT["password"],
            "name": TEST_CLIENT["name"],
            "role": TEST_CLIENT["role"]
        }
    )
    
    assert response.status_code in [201, 200], f"Client registration failed: {response.text}"
    response_data = response.json()
    # Try both 'token' and 'access_token' keys
    token = response_data.get("token") or response_data.get("access_token")
    assert token, f"No token in response: {response_data}"
    return token


@pytest.fixture
def client_headers(client_token: str) -> Dict[str, str]:
    """Client authorization headers"""
    return {"Authorization": f"Bearer {client_token}"}


@pytest.fixture(scope="function")
def barber_token(client: TestClient, admin_headers: Dict[str, str]) -> str:
    """Get barber JWT token (created by admin)"""
    # Always create a fresh barber with unique email for each test
    import time
    unique_email = f"barber{int(time.time() * 1000)}@barberpro.example.com"
    
    response = client.post(
        f"{API_URL}/barbers",
        headers=admin_headers,
        json={
            "email": unique_email,
            "password": TEST_BARBER["password"],
            "name": TEST_BARBER["name"],
            "specialization": TEST_BARBER["specialization"]
        }
    )
    
    assert response.status_code in [201, 200], f"Barber creation failed: {response.status_code} - {response.text}"
    
    # Login with the new barber
    login_response = client.post(
        f"{API_URL}/auth/login",
        json={
            "email": unique_email,
            "password": TEST_BARBER["password"]
        }
    )
    assert login_response.status_code == 200, f"Barber login failed: {login_response.text}"
    return login_response.json().get("token")


@pytest.fixture
def barber_headers(barber_token: str) -> Dict[str, str]:
    """Barber authorization headers"""
    return {"Authorization": f"Bearer {barber_token}"}


# ============================================================================
# DATA FIXTURES - SERVICES, SCHEDULES, ETC
# ============================================================================

@pytest.fixture
def service_data() -> Dict:
    """Service data for testing"""
    return {
        "name": "Corte Clásico E2E",
        "description": "Corte clásico de barbería profesional",
        "duration_minutes": 30,
        "price": 50.00,
        "is_active": True
    }


@pytest.fixture
def created_service(client: TestClient, admin_headers: Dict[str, str], service_data: Dict) -> Dict:
    """Create a service and return its data"""
    response = client.post(
        f"{API_URL}/services",
        headers=admin_headers,
        json=service_data
    )
    
    if response.status_code in [409, 400]:  # Already exists
        # Try to get existing service
        list_response = client.get(
            f"{API_URL}/services",
            headers=admin_headers
        )
        if list_response.status_code == 200:
            services = list_response.json()
            if services:
                return services[0]
    
    assert response.status_code in [201, 200], f"Service creation failed: {response.text}"
    return response.json()


@pytest.fixture
def appointment_data(created_service: Dict) -> Dict:
    """Appointment data for testing"""
    future_date = datetime.now() + timedelta(days=2)
    return {
        "service_id": created_service.get("id"),
        "date_time": future_date.isoformat(),
        "notes": "E2E Test Appointment"
    }


@pytest.fixture
def payment_data(created_service: Dict) -> Dict:
    """Payment data for testing"""
    return {
        "amount": created_service.get("price", 50.00),
        "payment_method": "credit_card",
        "card_token": "test_token_e2e",
        "description": "E2E Test Payment"
    }


# ============================================================================
# DATABASE FIXTURES - CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def reset_test_data(client: TestClient):
    """Reset test data before each test"""
    yield
    # Cleanup after test
    # Note: In real scenario, you might clear test collections
    pass


@pytest.fixture
def clear_test_users(client: TestClient, admin_headers: Dict[str, str]):
    """Clear test users after test"""
    yield
    # Note: This would be implemented based on your admin endpoints


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def timestamp() -> str:
    """Current ISO timestamp"""
    return datetime.now().isoformat()


@pytest.fixture
def future_datetime() -> str:
    """Future datetime (2 days from now)"""
    future = datetime.now() + timedelta(days=2)
    return future.isoformat()


@pytest.fixture
def past_datetime() -> str:
    """Past datetime (2 days ago)"""
    past = datetime.now() - timedelta(days=2)
    return past.isoformat()


# ============================================================================
# MARKERS FOR ORGANIZING TESTS
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "admin: Tests for admin functionality"
    )
    config.addinivalue_line(
        "markers", "client: Tests for client functionality"
    )
    config.addinivalue_line(
        "markers", "barber: Tests for barber functionality"
    )
    config.addinivalue_line(
        "markers", "auth: Tests for authentication"
    )
    config.addinivalue_line(
        "markers", "chatbot: Tests for AI chatbot"
    )
    config.addinivalue_line(
        "markers", "payment: Tests for payments"
    )
    config.addinivalue_line(
        "markers", "security: Tests for security"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (e.g., AI API calls)"
    )


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add e2e marker to all tests in e2e directory
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


# ============================================================================
# HELPER FUNCTIONS (not fixtures, but useful)
# ============================================================================

def assert_json_response(response, expected_status: int = 200, msg: str = ""):
    """Helper to assert JSON response"""
    assert response.status_code == expected_status, f"{msg} Status: {response.status_code}, Body: {response.text}"
    assert response.headers.get("content-type") == "application/json", "Response is not JSON"
    return response.json()


def extract_token(response_data: Dict) -> str:
    """Extract JWT token from response"""
    assert "token" in response_data, "Token not in response"
    return response_data["token"]
