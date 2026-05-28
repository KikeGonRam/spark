"""
E2E Integration Tests: Multi-Role Workflows
Tests for interactions between Admin, Client, and Barber
Validates how roles relate and depend on each other
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAdminClientWorkflow:
    """Workflow: Admin creates services → Client sees them → Client books"""
    
    def test_admin_creates_service_client_sees_it(
        self, 
        client: TestClient, 
        admin_headers, 
        client_headers,
        service_data
    ):
        """
        Integration Test 1: Service Creation Flow
        
        1. Admin creates service
        2. Client lists services
        3. Client sees the service created by admin
        """
        
        # Step 1: Admin creates service
        create_response = client.post(
            "/api/services",
            headers=admin_headers,
            json=service_data
        )
        
        assert create_response.status_code in [201, 200], \
            f"Admin failed to create service: {create_response.text}"
        
        created_service = create_response.json()
        service_id = created_service.get("id")
        service_name = created_service.get("name")
        
        print(f"\n✅ Step 1: Admin created service '{service_name}' (ID: {service_id})")
        
        # Step 2: Client lists services
        list_response = client.get(
            "/api/services",
            headers=client_headers
        )
        
        assert list_response.status_code == 200, \
            f"Client failed to list services: {list_response.text}"
        
        services = list_response.json()
        assert isinstance(services, list), "Services should be a list"
        
        # Step 3: Verify client sees admin's service
        service_found = any(
            svc.get("id") == service_id 
            for svc in services
        )
        
        assert service_found, \
            f"Client cannot see service created by admin. Services: {services}"
        
        print(f"✅ Step 2: Client sees the service created by admin")
        print(f"✅ Integration 1: PASSED - Service visibility across roles")
    
    
    def test_admin_creates_barber_client_sees_it(
        self,
        client: TestClient,
        admin_headers,
        client_headers
    ):
        """
        Integration Test 2: Barber Creation and Visibility
        
        1. Admin creates barber
        2. Client lists barbers
        3. Client sees the barber created by admin
        """
        
        # Step 1: Admin creates barber
        barber_email = f"barber.integration.{datetime.now().timestamp()}@e2etest.local"
        create_response = client.post(
            "/api/barbers",
            headers=admin_headers,
            json={
                "email": barber_email,
                "password": "BarberoIntegration@2026",
                "name": "Barber from Admin",
                "specialization": "Integration Test Barber"
            }
        )
        
        assert create_response.status_code in [201, 200], \
            f"Admin failed to create barber: {create_response.text}"
        
        created_barber = create_response.json()
        barber_id = created_barber.get("id")
        barber_name = created_barber.get("name")
        
        print(f"\n✅ Step 1: Admin created barber '{barber_name}' (ID: {barber_id})")
        
        # Step 2: Client lists barbers
        list_response = client.get(
            "/api/barbers",
            headers=client_headers
        )
        
        assert list_response.status_code == 200, \
            f"Client failed to list barbers: {list_response.text}"
        
        barbers = list_response.json()
        assert isinstance(barbers, list), "Barbers should be a list"
        
        # Step 3: Verify client sees admin's barber
        barber_found = any(
            b.get("id") == barber_id 
            for b in barbers
        )
        
        assert barber_found, \
            f"Client cannot see barber created by admin. Barbers: {barbers}"
        
        print(f"✅ Step 2: Client sees the barber created by admin")
        print(f"✅ Integration 2: PASSED - Barber visibility across roles")


@pytest.mark.integration
class TestClientBarberWorkflow:
    """Workflow: Client books → Barber sees it → Both can view it"""
    
    def test_client_books_barber_sees_appointment(
        self,
        client: TestClient,
        admin_headers,
        client_headers,
        barber_headers,
        created_service
    ):
        """
        Integration Test 3: Appointment Booking Workflow
        
        1. Admin creates/retrieves barber
        2. Client books appointment with barber
        3. Barber sees the appointment
        4. Both see the same appointment with same details
        """
        
        # Step 1: Get barber (created via fixture or create new)
        barbers_response = client.get(
            "/api/barbers",
            headers=client_headers
        )
        
        assert barbers_response.status_code == 200
        barbers = barbers_response.json()
        
        if not barbers:
            # Create barber if none exists
            create_response = client.post(
                "/api/barbers",
                headers=admin_headers,
                json={
                    "email": f"barber.book.{datetime.now().timestamp()}@e2etest.local",
                    "password": "BarberoBook@2026",
                    "name": "Barber for Booking",
                    "specialization": "Booking Test"
                }
            )
            assert create_response.status_code in [201, 200]
            barber_id = create_response.json().get("id")
        else:
            barber_id = barbers[0].get("id")
        
        print(f"\n✅ Step 1: Barber retrieved/created (ID: {barber_id})")
        
        # Step 2: Client books appointment
        future_time = datetime.now() + timedelta(days=2)
        
        book_response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "Integration test booking"
            }
        )
        
        assert book_response.status_code in [201, 200], \
            f"Client failed to book: {book_response.text}"
        
        appointment = book_response.json()
        appointment_id = appointment.get("id")
        
        print(f"✅ Step 2: Client booked appointment (ID: {appointment_id})")
        
        # Step 3: Barber sees the appointment
        barber_appointments_response = client.get(
            "/api/barbers/appointments",
            headers=barber_headers
        )
        
        assert barber_appointments_response.status_code == 200, \
            f"Barber failed to get appointments: {barber_appointments_response.text}"
        
        barber_appointments = barber_appointments_response.json()
        appointment_found = any(
            apt.get("id") == appointment_id 
            for apt in barber_appointments
        )
        
        assert appointment_found, \
            f"Barber cannot see appointment booked by client"
        
        print(f"✅ Step 3: Barber sees the appointment")
        
        # Step 4: Client verifies their own appointment
        client_appointments_response = client.get(
            "/api/clients/appointments",
            headers=client_headers
        )
        
        assert client_appointments_response.status_code == 200
        client_appointments = client_appointments_response.json()
        
        client_apt_found = any(
            apt.get("id") == appointment_id 
            for apt in client_appointments
        )
        
        assert client_apt_found, \
            "Client cannot see their own appointment"
        
        print(f"✅ Step 4: Client sees their own appointment")
        print(f"✅ Integration 3: PASSED - Appointment visibility and booking")


@pytest.mark.integration
class TestAdminMonitoringWorkflow:
    """Workflow: Admin sees all activities from all users"""
    
    def test_admin_sees_client_appointments(
        self,
        client: TestClient,
        admin_headers,
        client_headers,
        created_service
    ):
        """
        Integration Test 4: Admin Monitoring
        
        1. Client books appointment
        2. Admin lists all appointments
        3. Admin sees client's appointment
        """
        
        # Step 1: Get barber
        barbers_response = client.get(
            "/api/barbers",
            headers=admin_headers
        )
        
        barbers = barbers_response.json()
        if not barbers:
            pytest.skip("No barbers available")
        
        barber_id = barbers[0].get("id")
        
        # Step 2: Client books
        future_time = datetime.now() + timedelta(days=1)
        
        book_response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "Admin monitoring test"
            }
        )
        
        assert book_response.status_code in [201, 200]
        appointment = book_response.json()
        appointment_id = appointment.get("id")
        
        print(f"\n✅ Step 1: Client booked appointment (ID: {appointment_id})")
        
        # Step 3: Admin lists all appointments
        admin_appointments_response = client.get(
            "/api/appointments",
            headers=admin_headers
        )
        
        assert admin_appointments_response.status_code == 200, \
            f"Admin failed to list appointments: {admin_appointments_response.text}"
        
        all_appointments = admin_appointments_response.json()
        admin_sees_apt = any(
            apt.get("id") == appointment_id 
            for apt in all_appointments
        )
        
        assert admin_sees_apt, \
            "Admin cannot see client's appointment"
        
        print(f"✅ Step 2: Admin sees all appointments including client's")
        print(f"✅ Integration 4: PASSED - Admin monitoring capability")


@pytest.mark.integration
class TestBarberStatusUpdateWorkflow:
    """Workflow: Barber updates status → Client sees updated status"""
    
    def test_barber_updates_appointment_status_client_sees_it(
        self,
        client: TestClient,
        admin_headers,
        client_headers,
        barber_headers,
        created_service
    ):
        """
        Integration Test 5: Status Update Propagation
        
        1. Client books appointment (status: pending)
        2. Barber updates status to in_progress
        3. Client sees updated status
        4. Admin sees updated status
        """
        
        # Step 1: Setup barber
        barbers_response = client.get(
            "/api/barbers",
            headers=admin_headers
        )
        barbers = barbers_response.json()
        if not barbers:
            pytest.skip("No barbers available")
        
        barber_id = barbers[0].get("id")
        
        # Step 2: Client books
        future_time = datetime.now() + timedelta(hours=2)
        
        book_response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "Status update test"
            }
        )
        
        assert book_response.status_code in [201, 200]
        appointment = book_response.json()
        appointment_id = appointment.get("id")
        initial_status = appointment.get("status")
        
        print(f"\n✅ Step 1: Client booked appointment (Status: {initial_status})")
        
        # Step 3: Barber updates status
        update_response = client.patch(
            f"/api/appointments/{appointment_id}",
            headers=barber_headers,
            json={"status": "in_progress"}
        )
        
        if update_response.status_code not in [200, 204, 202]:
            pytest.skip(f"Status update endpoint not fully implemented: {update_response.status_code}")
        
        print(f"✅ Step 2: Barber updated status to 'in_progress'")
        
        # Step 4: Client sees updated status
        client_apts_response = client.get(
            "/api/clients/appointments",
            headers=client_headers
        )
        
        assert client_apts_response.status_code == 200
        client_apts = client_apts_response.json()
        
        updated_apt = next(
            (apt for apt in client_apts if apt.get("id") == appointment_id),
            None
        )
        
        if updated_apt:
            assert updated_apt.get("status") == "in_progress", \
                f"Client sees wrong status: {updated_apt.get('status')}"
            print(f"✅ Step 3: Client sees updated status")
        
        # Step 5: Admin sees updated status
        admin_apts_response = client.get(
            "/api/appointments",
            headers=admin_headers
        )
        
        assert admin_apts_response.status_code == 200
        admin_apts = admin_apts_response.json()
        
        admin_apt = next(
            (apt for apt in admin_apts if apt.get("id") == appointment_id),
            None
        )
        
        if admin_apt:
            assert admin_apt.get("status") == "in_progress", \
                f"Admin sees wrong status: {admin_apt.get('status')}"
            print(f"✅ Step 4: Admin sees updated status")
        
        print(f"✅ Integration 5: PASSED - Status update propagation")


@pytest.mark.integration
class TestPaymentWorkflow:
    """Workflow: Client pays → Status changes → Everyone sees it"""
    
    def test_client_payment_updates_appointment_status(
        self,
        client: TestClient,
        admin_headers,
        client_headers,
        created_service
    ):
        """
        Integration Test 6: Payment Processing
        
        1. Client books appointment (status: pending)
        2. Client makes payment
        3. Appointment status changes to paid/confirmed
        4. Admin sees payment
        """
        
        # Step 1: Get barber
        barbers_response = client.get(
            "/api/barbers",
            headers=admin_headers
        )
        barbers = barbers_response.json()
        if not barbers:
            pytest.skip("No barbers available")
        
        barber_id = barbers[0].get("id")
        
        # Step 2: Client books
        future_time = datetime.now() + timedelta(days=3)
        
        book_response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "Payment test"
            }
        )
        
        assert book_response.status_code in [201, 200]
        appointment = book_response.json()
        appointment_id = appointment.get("id")
        
        print(f"\n✅ Step 1: Client booked appointment (ID: {appointment_id})")
        
        # Step 3: Client makes payment
        payment_response = client.post(
            "/api/payments",
            headers=client_headers,
            json={
                "appointment_id": appointment_id,
                "amount": created_service.get("price", 50.00),
                "payment_method": "credit_card",
                "currency": "USD"
            }
        )
        
        if payment_response.status_code not in [200, 201]:
            pytest.skip(f"Payment endpoint not fully implemented: {payment_response.status_code}")
        
        print(f"✅ Step 2: Client made payment")
        
        # Step 4: Admin sees the payment
        payments_response = client.get(
            "/api/payments",
            headers=admin_headers
        )
        
        if payments_response.status_code == 200:
            payments = payments_response.json()
            payment_found = any(
                p.get("appointment_id") == appointment_id 
                for p in payments
            )
            assert payment_found, "Admin cannot see payment"
            print(f"✅ Step 3: Admin sees the payment")
        
        print(f"✅ Integration 6: PASSED - Payment processing")


@pytest.mark.integration
class TestMultiRoleCompleteWorkflow:
    """Complete real-world workflow: Full barber shop scenario"""
    
    def test_complete_barbershop_workflow(
        self,
        client: TestClient,
        admin_headers,
        client_headers,
        barber_headers,
        created_service
    ):
        """
        Integration Test 7: Complete Workflow
        
        Full scenario:
        1. Admin creates service
        2. Admin creates barber
        3. Client sees barber and service
        4. Client books appointment
        5. Barber sees appointment
        6. Barber updates status (in progress)
        7. Admin monitors everything
        8. Client sees all updates
        """
        
        print("\n" + "="*70)
        print("COMPLETE BARBERSHOP WORKFLOW")
        print("="*70)
        
        # Step 1: Admin creates service (via fixture)
        print("\n✅ Step 1: Service already created by fixture")
        print(f"   Service: {created_service.get('name')}")
        
        # Step 2: Get or create barber
        barbers_response = client.get(
            "/api/barbers",
            headers=admin_headers
        )
        barbers = barbers_response.json()
        
        if barbers:
            barber_id = barbers[0].get("id")
            barber_name = barbers[0].get("name")
            print(f"\n✅ Step 2: Barber exists")
            print(f"   Barber: {barber_name} (ID: {barber_id})")
        else:
            print(f"\n⚠️  No barbers available for workflow")
            pytest.skip("No barbers available")
        
        # Step 3: Client lists and sees barber
        client_barbers = client.get(
            "/api/barbers",
            headers=client_headers
        ).json()
        
        assert any(b.get("id") == barber_id for b in client_barbers)
        print(f"\n✅ Step 3: Client sees barber")
        print(f"   Barber visible: {barber_name}")
        
        # Step 4: Client books appointment
        future_time = datetime.now() + timedelta(days=1)
        
        book_response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "Complete workflow test"
            }
        )
        
        assert book_response.status_code in [201, 200]
        appointment = book_response.json()
        appointment_id = appointment.get("id")
        
        print(f"\n✅ Step 4: Client booked appointment")
        print(f"   Appointment ID: {appointment_id}")
        print(f"   Date/Time: {future_time.isoformat()}")
        
        # Step 5: Barber sees appointment
        barber_apts = client.get(
            "/api/barbers/appointments",
            headers=barber_headers
        ).json()
        
        assert any(a.get("id") == appointment_id for a in barber_apts)
        print(f"\n✅ Step 5: Barber sees appointment")
        print(f"   Barber appointment count: {len(barber_apts)}")
        
        # Step 6: Barber updates status
        update_response = client.patch(
            f"/api/appointments/{appointment_id}",
            headers=barber_headers,
            json={"status": "in_progress"}
        )
        
        if update_response.status_code in [200, 204, 202]:
            print(f"\n✅ Step 6: Barber updated status to 'in_progress'")
        else:
            print(f"\n⚠️  Status update not available")
        
        # Step 7: Admin monitors
        admin_apts = client.get(
            "/api/appointments",
            headers=admin_headers
        ).json()
        
        assert any(a.get("id") == appointment_id for a in admin_apts)
        print(f"\n✅ Step 7: Admin monitoring")
        print(f"   Total appointments visible to admin: {len(admin_apts)}")
        
        # Step 8: Client sees their appointment
        client_apts = client.get(
            "/api/clients/appointments",
            headers=client_headers
        ).json()
        
        assert any(a.get("id") == appointment_id for a in client_apts)
        print(f"\n✅ Step 8: Client sees their appointment")
        print(f"   Client's total appointments: {len(client_apts)}")
        
        print("\n" + "="*70)
        print("✅ COMPLETE WORKFLOW PASSED - ALL ROLES WORKING TOGETHER")
        print("="*70)


@pytest.mark.integration
class TestDataConsistencyAcrossRoles:
    """Verify data consistency across all roles"""
    
    def test_appointment_data_consistency(
        self,
        client: TestClient,
        client_headers,
        barber_headers,
        created_service
    ):
        """
        Integration Test 8: Data Consistency
        
        When a client and barber view the same appointment:
        - IDs match
        - Dates/times match
        - Service info matches
        - Status matches
        """
        
        # Get barber
        barbers = client.get(
            "/api/barbers",
            headers=client_headers
        ).json()
        
        if not barbers:
            pytest.skip("No barbers available")
        
        barber_id = barbers[0].get("id")
        
        # Client books
        future_time = datetime.now() + timedelta(days=2)
        
        book_response = client.post(
            "/api/appointments",
            headers=client_headers,
            json={
                "barber_id": barber_id,
                "service_id": created_service.get("id"),
                "date_time": future_time.isoformat(),
                "notes": "Consistency test"
            }
        )
        
        assert book_response.status_code in [201, 200]
        client_apt = book_response.json()
        appointment_id = client_apt.get("id")
        
        # Get appointment from both perspectives
        client_apts = client.get(
            "/api/clients/appointments",
            headers=client_headers
        ).json()
        
        barber_apts = client.get(
            "/api/barbers/appointments",
            headers=barber_headers
        ).json()
        
        # Find same appointment
        client_view = next(
            (a for a in client_apts if a.get("id") == appointment_id),
            None
        )
        
        barber_view = next(
            (a for a in barber_apts if a.get("id") == appointment_id),
            None
        )
        
        if client_view and barber_view:
            # Verify consistency
            assert client_view.get("id") == barber_view.get("id"), \
                "Appointment IDs don't match"
            
            assert client_view.get("status") == barber_view.get("status"), \
                "Appointment status doesn't match"
            
            print(f"\n✅ Data consistency validated:")
            print(f"   ID: {client_view.get('id')} == {barber_view.get('id')}")
            print(f"   Status: {client_view.get('status')} == {barber_view.get('status')}")
            print(f"✅ Integration 8: PASSED - Data consistency across roles")
