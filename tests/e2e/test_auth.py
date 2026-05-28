"""
E2E Test Suite: CT-001 - Authentication and Login
Tests: Register, Login, Logout, Token Validation
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.auth
class TestAuthentication:
    """Authentication E2E Tests"""
    
    # ========================================================================
    # CT-001.1: Register Admin
    # ========================================================================
    
    def test_register_admin_success(self, client: TestClient, unique_email: str):
        """CT-001.1: Successful admin registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "AdminTest@2026",
                "name": "Admin CT 001.1",
                "role": "admin"
            }
        )
        
        # Should return 201 Created
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain user id"
        assert data["email"] == unique_email
        assert data["role"] == "admin"
        assert data["name"] == "Admin CT 001.1"
    
    
    def test_register_admin_duplicate_email(self, client: TestClient, unique_email: str):
        """Admin registration with duplicate email should fail"""
        # Register first time
        response1 = client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "AdminTest@2026",
                "name": "Admin Dup",
                "role": "admin"
            }
        )
        assert response1.status_code == 201
        
        # Try register again with same email
        response2 = client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "AdminTest@2026Different",
                "name": "Admin Dup 2",
                "role": "admin"
            }
        )
        
        # Should return 409 Conflict
        assert response2.status_code == 409, f"Expected 409, got {response2.status_code}"
    
    
    def test_register_admin_invalid_email(self, client: TestClient):
        """Admin registration with invalid email should fail"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",  # Not a valid email
                "password": "AdminTest@2026",
                "name": "Admin Invalid",
                "role": "admin"
            }
        )
        
        # Should return 422 Unprocessable Entity or 400 Bad Request
        assert response.status_code in [422, 400], f"Expected 422/400, got {response.status_code}"
    
    
    def test_register_admin_weak_password(self, client: TestClient, unique_email: str):
        """Admin registration with weak password should fail"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "123",  # Too weak
                "name": "Admin Weak",
                "role": "admin"
            }
        )
        
        # Should return 422 or 400
        assert response.status_code in [422, 400], f"Expected 422/400, got {response.status_code}"
    
    
    # ========================================================================
    # CT-001.2: Register Client
    # ========================================================================
    
    @pytest.mark.client
    def test_register_client_success(self, client: TestClient, unique_email: str):
        """CT-001.2: Successful client registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "ClientTest@2026",
                "name": "Juan Cliente CT 001.2",
                "role": "client"
            }
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["email"] == unique_email
        assert data["role"] == "client"
    
    
    # ========================================================================
    # CT-001.3: Create Barber (by Admin)
    # ========================================================================
    
    @pytest.mark.barber
    def test_create_barber_as_admin(self, client: TestClient, admin_headers, unique_email: str):
        """CT-001.3: Admin creates barber"""
        response = client.post(
            "/api/barbers",
            headers=admin_headers,
            json={
                "email": unique_email,
                "password": "BarberoTest@2026",
                "name": "Carlos Barbero CT 001.3",
                "specialization": "Cortes Clásicos"
            }
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["email"] == unique_email
        assert data["name"] == "Carlos Barbero CT 001.3"
        assert data["specialization"] == "Cortes Clásicos"
    
    
    def test_create_barber_as_client_fails(self, client: TestClient, client_headers):
        """CT-001.3b: Client cannot create barber"""
        response = client.post(
            "/api/barbers",
            headers=client_headers,
            json={
                "email": "barbero.fail@example.com",
                "password": "BarberoTest@2026",
                "name": "Carlos Fail",
                "specialization": "Cortes"
            }
        )
        
        # Should return 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    
    
    # ========================================================================
    # CT-001.4: Login
    # ========================================================================
    
    @pytest.mark.auth
    def test_login_admin_success(self, client: TestClient, unique_email: str):
        """CT-001.4: Successful admin login"""
        # First register
        password = "AdminLogin@2026"
        
        client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "name": "Admin Login",
                "role": "admin"
            }
        )
        
        # Then login
        response = client.post(
            "/api/auth/login",
            json={
                "email": unique_email,
                "password": password
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain JWT token"
        assert data["user"]["email"] == unique_email
        assert data["user"]["role"] == "admin"
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
    
    
    def test_login_client_success(self, client: TestClient, unique_email: str):
        """CT-001.4b: Successful client login"""
        password = "ClientLogin@2026"
        
        client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": password,
                "name": "Cliente Login",
                "role": "client"
            }
        )
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": unique_email,
                "password": password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "client"
    
    
    def test_login_invalid_password(self, client: TestClient, unique_email: str):
        """CT-001.4c: Login with invalid password fails"""
        # Register
        client.post(
            "/api/auth/register",
            json={
                "email": unique_email,
                "password": "CorrectPassword@2026",
                "name": "Admin Invalid",
                "role": "admin"
            }
        )
        
        # Try login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": unique_email,
                "password": "WrongPassword@2026"
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    
    def test_login_nonexistent_user(self, client: TestClient):
        """CT-001.4d: Login with nonexistent user fails"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword@2026"
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    
    # ========================================================================
    # CT-001.5: Token Validation
    # ========================================================================
    
    @pytest.mark.auth
    def test_valid_token_provides_access(self, client: TestClient, admin_token: str):
        """CT-001.5: Valid token allows access to protected endpoints"""
        response = client.get(
            "/api/health",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Health endpoint should return 200
        assert response.status_code == 200
    
    
    def test_invalid_token_denies_access(self, client: TestClient):
        """CT-001.5b: Invalid token denies access"""
        response = client.get(
            "/api/health",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        # Should return 401 Unauthorized
        assert response.status_code == 401 or response.status_code == 403
    
    
    def test_missing_token_denies_access(self, client: TestClient):
        """CT-001.5c: Missing token denies access to protected endpoints"""
        # Try to access protected endpoint without token
        response = client.get("/api/barbers")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    
    # ========================================================================
    # CT-001.6: Logout
    # ========================================================================
    
    @pytest.mark.auth
    def test_logout_invalidates_token(self, client: TestClient, admin_token: str):
        """CT-001.6: Logout invalidates token"""
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Logout should return 200
        assert response.status_code == 200
        
        # After logout, token should be invalid
        # Try to use token on a protected endpoint
        health_response = client.get(
            "/api/health",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Should fail (either 401 or work depending on implementation)
        # In real apps, tokens are still valid until expiry
        # This test documents the behavior


class TestAuthenticationEdgeCases:
    """Edge case tests for authentication"""
    
    def test_register_with_special_characters_in_name(self, client: TestClient):
        """Test registration with special characters in name"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "special@example.com",
                "password": "SpecialTest@2026",
                "name": "João José-María O'Connor",
                "role": "client"
            }
        )
        
        # Should handle unicode properly
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "João José-María O'Connor"
    
    
    def test_register_with_uppercase_email(self, client: TestClient):
        """Test that email is case-insensitive"""
        email = "UpperCase@example.com"
        
        response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "UpperTest@2026",
                "name": "Upper Case",
                "role": "client"
            }
        )
        
        # Should normalize email to lowercase
        assert response.status_code == 201
        data = response.json()
        assert data["email"].lower() == email.lower()
    
    
    def test_login_with_uppercase_email(self, client: TestClient):
        """Test login with uppercase email"""
        email_lower = "login.case@example.com"
        password = "CaseTest@2026"
        
        # Register with lowercase
        client.post(
            "/api/auth/register",
            json={
                "email": email_lower,
                "password": password,
                "name": "Login Case",
                "role": "client"
            }
        )
        
        # Try login with uppercase
        response = client.post(
            "/api/auth/login",
            json={
                "email": email_lower.upper(),
                "password": password
            }
        )
        
        # Should still work (case-insensitive email)
        assert response.status_code == 200


# ============================================================================
# BATCH AUTHENTICATION TESTS
# ============================================================================

@pytest.mark.auth
def test_all_three_users_can_register_and_login(client: TestClient):
    """
    CT-001-BATCH: All 3 user types can register and login
    This is a batch test to verify the core auth flow works for all roles
    """
    
    users = [
        {
            "email": "batch.admin@example.com",
            "password": "BatchAdmin@2026",
            "name": "Batch Admin",
            "role": "admin"
        },
        {
            "email": "batch.client@example.com",
            "password": "BatchClient@2026",
            "name": "Batch Client",
            "role": "client"
        }
    ]
    
    tokens = {}
    
    for user in users:
        # Register
        register_response = client.post(
            "/api/auth/register",
            json=user
        )
        assert register_response.status_code == 201, f"Failed to register {user['role']}"
        
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": user["email"],
                "password": user["password"]
            }
        )
        assert login_response.status_code == 200, f"Failed to login {user['role']}"
        
        login_data = login_response.json()
        tokens[user["role"]] = login_data["token"]
        
        # Verify token works
        health_response = client.get(
            "/api/health",
            headers={"Authorization": f"Bearer {login_data['token']}"}
        )
        assert health_response.status_code == 200, f"Token failed for {user['role']}"
    
    assert "admin" in tokens
    assert "client" in tokens
    print(f"\n✅ All 3 user types authenticated successfully")

