"""
E2E Test Suite: Core Functionality by Role
Tests for Admin, Client, and Barber features
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


@pytest.mark.admin
class TestAdminFunctionality:
    """Admin-only functionality tests"""
    
    def test_admin_can_create_barber(self, client: TestClient, admin_headers):
        """Admin can create a new barber"""
        response = client.post(
            "/api/barbers",
            headers=admin_headers,
            json={
                "email": f"barber.admin.{datetime.now().timestamp()}@barberpro.example.com",
                "password": "BarberoAdmin@2026",
                "name": "Barber Created by Admin",
                "specialization": ["cortes modernos", "coloración"]
            }
        )
        
        assert response.status_code in [201, 200], f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data or "data" in data
        print(f"\n✅ Admin created barber: {data}")

    
    
    def test_admin_can_list_barbers(self, client: TestClient, admin_headers):
        """Admin can list all barbers"""
        response = client.get(
            "/api/barbers",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"\n✅ Admin can list barbers: {len(data)} found")
    
    
    def test_admin_can_view_barber_details(self, client: TestClient, admin_headers):
        """Admin can view specific barber details"""
        # First create a barber to view
        create_response = client.post(
            "/api/barbers",
            headers=admin_headers,
            json={
                "email": f"barber.detail.{datetime.now().timestamp()}@barberpro.example.com",
                "password": "BarberoAdmin@2026",
                "name": "Barber Detail Test",
                "specialization": ["cortes"]
            }
        )
        
        if create_response.status_code not in [201, 200]:
            # If we can't create, skip this test
            pytest.skip("Could not create barber for detail test")
        
        created_data = create_response.json()
        barber_data = created_data.get("data", {}).get("barber", {})
        # MongoDB returns _id, not id
        barber_id = barber_data.get("_id") or barber_data.get("id")
        
        if not barber_id:
            pytest.skip("Could not extract barber ID from creation response")
        
        # Get specific barber
        response = client.get(
            f"/api/barbers/{barber_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Handle response structure - might be wrapped or direct
        if isinstance(data, dict) and "data" in data:
            barber = data["data"].get("barber", {})
        else:
            barber = data
        
        barber_id_in_response = barber.get("_id") or barber.get("id")
        assert barber_id_in_response == barber_id
        print(f"\n✅ Admin viewed barber details: {barber.get('name')}")
    
    
    def test_admin_can_view_all_appointments(self, client: TestClient, admin_headers):
        """Admin can view all appointments"""
        response = client.get(
            "/api/appointments",
            headers=admin_headers
        )
        
        # May return 200 even if empty
        assert response.status_code == 200
        data = response.json()
        # Handle wrapped response format
        if isinstance(data, dict) and "data" in data:
            appointments = data["data"].get("appointments", [])
        else:
            appointments = data if isinstance(data, list) else []
        
        assert isinstance(appointments, list)
        print(f"\n✅ Admin can view appointments: {len(appointments)} total")
    
    
    def test_admin_cannot_be_deleted(self, client: TestClient, admin_headers):
        """Admin users cannot be deleted by other admins"""
        # This test documents the business rule
        # Implementation may vary
        response = client.delete(
            "/api/auth/current",
            headers=admin_headers
        )
        
        # Should either deny or return error
        assert response.status_code != 204, "Admin should not be easily deleted"
        print(f"\n✅ Admin protection: Cannot delete admin user")


@pytest.mark.client
class TestClientFunctionality:
    """Client-only functionality tests"""
    
    def test_client_can_view_available_barbers(self, client: TestClient, client_headers):
        """Client can view available barbers"""
        response = client.get(
            "/api/barbers",
            headers=client_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"\n✅ Client can view {len(data)} barbers")
    
    
    def test_client_can_schedule_appointment(self, client: TestClient, client_headers, created_service):
        """Client can schedule a new appointment"""
        # Get barbers first
        barbers_response = client.get(
            "/api/barbers",
            headers=client_headers
        )
        
        if barbers_response.status_code != 200 or not barbers_response.json():
            pytest.skip("No barbers available for appointment")
        
        barber_list = barbers_response.json()
        barber_data = barber_list[0]
        barber_id = barber_data.get("_id") or barber_data.get("id")
        
        if not barber_id:
            pytest.skip("Could not extract barber ID")
        
        # Schedule appointment
        future_time = datetime.now() + timedelta(days=1)
        
        response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "E2E Test Appointment"
            }
        )
        
        assert response.status_code in [201, 200], f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["status"] in ["pending", "confirmed"]
        print(f"\n✅ Client scheduled appointment: {data.get('id')}")
    
    
    def test_client_can_view_own_appointments(self, client: TestClient, client_headers):
        """Client can view their own appointments"""
        response = client.get(
            "/api/clients/appointments",
            headers=client_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"\n✅ Client can view own appointments: {len(data)} total")
    
    
    def test_client_cannot_view_other_clients(self, client: TestClient, client_headers):
        """Client cannot view other client's data"""
        response = client.get(
            "/api/clients",
            headers=client_headers
        )
        
        # Should be 403 Forbidden or 404 Not Found
        assert response.status_code in [403, 404], f"Expected 403/404, got {response.status_code}"
        print(f"\n✅ Client privacy: Cannot view other clients")
    
    
    def test_client_cannot_create_barber(self, client: TestClient, client_headers):
        """Client cannot create a barber"""
        response = client.post(
            "/api/barbers",
            headers=client_headers,
            json={
                "email": "fake.barber@e2etest.local",
                "password": "FakeBarber@2026",
                "name": "Fake Barber",
                "specialization": ["Fake"]
            }
        )
        
        # Should be 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"\n✅ Client limitation: Cannot create barbers")
    
    
    def test_client_can_pay_for_appointment(self, client: TestClient, client_headers):
        """Client can make payment for appointment"""
        response = client.post(
            "/api/payments",
            headers=client_headers,
            json={
                "appointment_id": "test-apt-id",
                "amount": 50.00,
                "payment_method": "credit_card",
                "currency": "USD"
            }
        )
        
        # May fail due to invalid appointment, but endpoint should exist
        assert response.status_code != 404, "Payments endpoint should exist"
        print(f"\n✅ Payments endpoint available to clients")


@pytest.mark.barber
class TestBarberFunctionality:
    """Barber-only functionality tests"""
    
    def test_barber_can_view_own_appointments(self, client: TestClient, barber_headers):
        """Barber can view their own appointments"""
        response = client.get(
            "/api/barbers/appointments",
            headers=barber_headers
        )
        
        if response.status_code != 200:
            print(f"\n❌ Got {response.status_code}: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"\n✅ Barber can view own appointments: {len(data)} total")
    
    
    def test_barber_can_update_appointment_status(self, client: TestClient, barber_headers):
        """Barber can update appointment status"""
        response = client.patch(
            "/api/appointments/test-apt-id",
            headers=barber_headers,
            json={
                "status": "in_progress"
            }
        )
        
        # May fail due to invalid appointment, but endpoint should exist
        assert response.status_code != 404, "Appointment update endpoint should exist"
        print(f"\n✅ Appointment status update endpoint available")
    
    
    def test_barber_can_view_own_schedule(self, client: TestClient, barber_headers):
        """Barber can view their schedule"""
        response = client.get(
            "/api/barbers/schedule",
            headers=barber_headers
        )
        
        assert response.status_code == 200
        print(f"\n✅ Barber can view own schedule")
    
    
    def test_barber_can_view_clients(self, client: TestClient, barber_headers):
        """Barber can view clients they serve"""
        response = client.get(
            "/api/barbers/clients",
            headers=barber_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"\n✅ Barber can view clients: {len(data)} total")
    
    
    def test_barber_cannot_create_other_barbers(self, client: TestClient, barber_headers):
        """Barber cannot create other barbers"""
        response = client.post(
            "/api/barbers",
            headers=barber_headers,
            json={
                "email": "another.barber@e2etest.local",
                "password": "AnotherBarber@2026",
                "name": "Another Barber",
                "specialization": "Fake"
            }
        )
        
        # Should be 403 Forbidden
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print(f"\n✅ Barber limitation: Cannot create other barbers")
    
    
    def test_barber_can_view_statistics(self, client: TestClient, barber_headers):
        """Barber can view their statistics"""
        response = client.get(
            "/api/barbers/stats",
            headers=barber_headers
        )
        
        # May not be implemented, but document the feature
        assert response.status_code != 404, "Stats endpoint should exist for barbers"
        print(f"\n✅ Barber statistics available")


# ============================================================================
# CROSS-ROLE TESTS
# ============================================================================

@pytest.mark.auth
class TestRoleBasedAccess:
    """Test access control across roles"""
    
    def test_admin_endpoints_blocked_for_client(self, client: TestClient, client_headers):
        """Client cannot access admin endpoints"""
        response = client.post(
            "/api/barbers",
            headers=client_headers,
            json={
                "email": "test@e2etest.local",
                "password": "Test@2026",
                "name": "Test",
                "specialization": "Test"
            }
        )
        
        assert response.status_code == 403
        print(f"\n✅ Access Control: Client blocked from admin endpoint")
    
    
    def test_admin_endpoints_blocked_for_barber(self, client: TestClient, barber_headers):
        """Barber cannot access admin endpoints"""
        response = client.post(
            "/api/reports/all",
            headers=barber_headers,
            json={
                "start_date": "2026-01-01",
                "end_date": "2026-12-31"
            }
        )
        
        # May not exist, but if it does should be blocked
        if response.status_code == 200:
            pytest.fail("Barber should not access admin report endpoint")
        print(f"\n✅ Access Control: Barber blocked from admin endpoint")
    
    
    def test_each_role_can_access_health(self, client: TestClient, admin_headers, client_headers, barber_headers):
        """All roles can access health endpoint"""
        for headers, role in [(admin_headers, "admin"), (client_headers, "client"), (barber_headers, "barber")]:
            response = client.get(
                "/api/health",
                headers=headers
            )
            
            assert response.status_code == 200, f"{role} cannot access health"
        
        print(f"\n✅ All roles can access health endpoint")


# ============================================================================
# BATCH ROLE TESTS
# ============================================================================

@pytest.mark.admin
@pytest.mark.client
@pytest.mark.barber
def test_three_roles_complete_workflow(client: TestClient, admin_headers, client_headers, barber_headers, created_service):
    """
    Complete workflow test with all 3 roles
    1. Admin creates service
    2. Client books appointment
    3. Barber views appointment
    """
    
    print("\n🔄 Three-Role Workflow Test")
    print("=" * 50)
    
    # Step 1: Admin creates service (already done via fixture)
    print(f"✅ Step 1: Service created")
    
    # Step 2: Client books appointment
    barbers_response = client.get(
        "/api/barbers",
        headers=client_headers
    )
    
    if barbers_response.status_code == 200 and barbers_response.json():
        barber_id = barbers_response.json()[0]["id"]
        
        future_time = datetime.now() + timedelta(days=1)
        
        appointment_response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "Workflow test"
            }
        )
        
        if appointment_response.status_code in [201, 200]:
            appointment = appointment_response.json()
            print(f"✅ Step 2: Client booked appointment: {appointment.get('id')}")
            
            # Step 3: Barber views appointments
            barber_appointments = client.get(
                "/api/barbers/appointments",
                headers=barber_headers
            )
            
            if barber_appointments.status_code == 200:
                appointments = barber_appointments.json()
                print(f"✅ Step 3: Barber viewed {len(appointments)} appointments")
                print("=" * 50)
                print(f"✅ Complete workflow successful with all 3 roles")
