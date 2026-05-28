"""
Configuración central de pytest para todos los tests
"""
import pytest
import os
from fastapi.testclient import TestClient
from pymongo import MongoClient
from datetime import datetime, timedelta
import json

# --- CONFIGURACIÓN GLOBAL ---
os.environ['ENVIRONMENT'] = 'testing'
os.environ['JWT_SECRET'] = 'test-secret-key-for-testing-only'
os.environ['JWT_ALGORITHM'] = 'HS256'
os.environ['MONGODB_URL'] = 'mongodb://admin:password@mongodb:27017/?authSource=admin'
os.environ['DATABASE_NAME'] = 'barberpro_test'
os.environ['MONGO_HOST'] = 'mongodb://mongodb:27017'
os.environ['MONGO_DB'] = 'barberpro_test'
os.environ['MONGO_USER'] = 'admin'
os.environ['MONGO_PASSWORD'] = 'password'

# Import app
from app.main import app
from database.connection import get_db


# --- FIXTURES: DATABASE ---
@pytest.fixture(scope='session')
def mongodb_connection():
    """Conexión a MongoDB para toda la sesión de tests"""
    client = MongoClient(os.environ['MONGODB_URL'])
    yield client
    client.close()


@pytest.fixture(scope='function')
def test_db(mongodb_connection):
    """Base de datos limpia para cada test"""
    db = mongodb_connection[os.environ['DATABASE_NAME']]
    
    # Limpiar antes
    db.drop_collection('users')
    db.drop_collection('barbers')
    db.drop_collection('clients')
    db.drop_collection('appointments')
    db.drop_collection('services')
    db.drop_collection('payments')
    db.drop_collection('reports')
    db.drop_collection('inventory')
    
    yield db
    
    # Limpiar después
    db.drop_collection('users')
    db.drop_collection('barbers')
    db.drop_collection('clients')
    db.drop_collection('appointments')
    db.drop_collection('services')
    db.drop_collection('payments')
    db.drop_collection('reports')
    db.drop_collection('inventory')


# --- FIXTURES: API CLIENT ---
@pytest.fixture
def client(test_db):
    """TestClient de FastAPI"""
    with TestClient(app) as client:
        yield client


# --- FIXTURES: USUARIOS DE PRUEBA ---
@pytest.fixture
def admin_user():
    """Usuario administrador para tests"""
    return {
        '_id': 'admin-user-123',
        'email': 'admin@barberpro.local',
        'password_hash': '$2b$12$...',  # Hash simulado
        'full_name': 'Admin User',
        'phone': '+56912345678',
        'role': 'admin',
        'permissions': ['users.read', 'users.write', 'appointments.read', 'payments.refund'],
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }


@pytest.fixture
def barber_user():
    """Usuario barbero para tests"""
    return {
        '_id': 'barber-user-456',
        'email': 'barber@barberpro.local',
        'password_hash': '$2b$12$...',  # Hash simulado
        'full_name': 'Juan Barbero',
        'phone': '+56987654321',
        'role': 'barber',
        'permissions': ['appointments.read', 'appointments.write', 'clients.read'],
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }


@pytest.fixture
def client_user():
    """Usuario cliente para tests"""
    return {
        '_id': 'client-user-789',
        'email': 'client@example.com',
        'password_hash': '$2b$12$...',  # Hash simulado
        'full_name': 'Cliente Test',
        'phone': '+56912341234',
        'role': 'client',
        'permissions': ['appointments.read', 'appointments.create', 'payments.read'],
        'is_active': True,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
    }


# --- FIXTURES: JWT TOKENS ---
@pytest.fixture
def admin_token(admin_user):
    """Token JWT para usuario admin"""
    from app.utils.security import JWTHandler
    return JWTHandler.generate_access_token(
        user_id=admin_user['_id'],
        email=admin_user['email'],
        role=admin_user['role'],
        permissions=admin_user['permissions'],
    )


@pytest.fixture
def barber_token(barber_user):
    """Token JWT para usuario barbero"""
    from app.utils.security import JWTHandler
    return JWTHandler.generate_access_token(
        user_id=barber_user['_id'],
        email=barber_user['email'],
        role=barber_user['role'],
        permissions=barber_user['permissions'],
    )


@pytest.fixture
def client_token(client_user):
    """Token JWT para usuario cliente"""
    from app.utils.security import JWTHandler
    return JWTHandler.generate_access_token(
        user_id=client_user['_id'],
        email=client_user['email'],
        role=client_user['role'],
        permissions=client_user['permissions'],
    )


@pytest.fixture
def expired_token():
    """Token JWT expirado"""
    from app.utils.security import JWTHandler
    payload = {
        'sub': 'test-user',
        'email': 'test@example.com',
        'role': 'client',
        'permissions': [],
        'exp': datetime.utcnow() - timedelta(hours=1),  # Expirado hace 1 hora
        'iat': datetime.utcnow() - timedelta(hours=2),
        'type': 'access',
    }
    import jwt
    return jwt.encode(payload, os.environ['JWT_SECRET'], algorithm='HS256')


# --- FIXTURES: HEADERS AUTENTICADOS ---
@pytest.fixture
def admin_headers(admin_token):
    """Headers con token admin"""
    return {'Authorization': f'Bearer {admin_token}'}


@pytest.fixture
def barber_headers(barber_token):
    """Headers con token barbero"""
    return {'Authorization': f'Bearer {barber_token}'}


@pytest.fixture
def client_headers(client_token):
    """Headers con token cliente"""
    return {'Authorization': f'Bearer {client_token}'}


# --- FIXTURES: DATOS DE PRUEBA ---
@pytest.fixture
def appointment_data():
    """Datos de prueba para una cita"""
    return {
        'barber_id': 'barber-user-456',
        'client_id': 'client-user-789',
        'service_id': 'service-123',
        'scheduled_at': (datetime.now() + timedelta(days=1)).isoformat(),
        'duration_minutes': 30,
        'notes': 'Corte clásico',
        'status': 'pending',
    }


@pytest.fixture
def service_data():
    """Datos de prueba para un servicio"""
    return {
        'name': 'Corte Clásico',
        'description': 'Corte de cabello clásico',
        'duration_minutes': 30,
        'price': 15000,
        'is_active': True,
    }


@pytest.fixture
def payment_data():
    """Datos de prueba para un pago"""
    return {
        'appointment_id': 'appointment-123',
        'amount': 15000,
        'method': 'card',
        'status': 'completed',
        'transaction_id': 'txn-abc123',
    }


# --- FIXTURES: HELPERS ---
@pytest.fixture
def create_user_in_db(test_db):
    """Factory para crear usuarios en la BD"""
    def _create(user_data):
        result = test_db['users'].insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return user_data
    return _create


@pytest.fixture
def create_appointment_in_db(test_db):
    """Factory para crear citas en la BD"""
    def _create(appointment_data):
        result = test_db['appointments'].insert_one(appointment_data)
        appointment_data['_id'] = result.inserted_id
        return appointment_data
    return _create


# --- PYTEST CONFIGURATION ---
def pytest_configure(config):
    """Configuración inicial de pytest"""
    config.addinivalue_line(
        "markers", "unit: marca tests unitarios"
    )
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "slow: marca tests lentos"
    )


# --- PYTEST HOOKS ---
@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset del rate limiter entre tests"""
    from app.utils.rate_limiter import SimpleRateLimiter
    SimpleRateLimiter.requests = {}
    yield
    SimpleRateLimiter.requests = {}
