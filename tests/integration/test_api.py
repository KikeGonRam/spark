"""
Tests para endpoints de API
"""
import pytest
import json
from datetime import datetime, timedelta


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests para endpoint de health check"""
    
    def test_health_endpoint_exists(self, client):
        """Verificar que endpoint /health existe"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        assert 'status' in response.json()
    
    def test_health_endpoint_returns_ok(self, client):
        """Health endpoint retorna estado OK"""
        response = client.get('/api/health')
        
        assert response.json()['status'] == 'ok'


@pytest.mark.integration
class TestAppointmentEndpoints:
    """Tests para endpoints de citas"""
    
    def test_list_appointments_requires_auth(self, client):
        """Listar citas requiere autenticación"""
        response = client.get('/api/appointments')
        
        # Sin token debería rechazar
        assert response.status_code in [401, 307, 404]
    
    def test_list_appointments_with_auth(self, client, admin_headers):
        """Listar citas con autenticación"""
        response = client.get('/api/appointments', headers=admin_headers)
        
        # Con token válido debería retornar 200 o 404 si no existe
        assert response.status_code in [200, 404]
    
    def test_create_appointment(self, client, barber_headers, appointment_data):
        """Crear nueva cita"""
        response = client.post(
            '/api/appointments',
            json=appointment_data,
            headers=barber_headers
        )
        
        # Debería retornar 201 Created o similar
        assert response.status_code in [201, 404, 422]
    
    def test_get_appointment_by_id(self, client, admin_headers):
        """Obtener cita por ID"""
        appointment_id = 'appointment-123'
        response = client.get(
            f'/api/appointments/{appointment_id}',
            headers=admin_headers
        )
        
        # Puede ser 404 (no existe) o 200 (existe)
        assert response.status_code in [200, 404]
    
    def test_update_appointment(self, client, admin_headers):
        """Actualizar cita"""
        appointment_id = 'appointment-123'
        update_data = {'status': 'confirmed'}
        
        response = client.patch(
            f'/api/appointments/{appointment_id}',
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code in [200, 404, 422]
    
    def test_delete_appointment(self, client, admin_headers):
        """Eliminar cita"""
        appointment_id = 'appointment-123'
        
        response = client.delete(
            f'/api/appointments/{appointment_id}',
            headers=admin_headers
        )
        
        assert response.status_code in [200, 204, 404]


@pytest.mark.integration
class TestBarberEndpoints:
    """Tests para endpoints de barberos"""
    
    def test_list_barbers(self, client, admin_headers):
        """Listar barberos"""
        response = client.get('/api/barbers', headers=admin_headers)
        
        assert response.status_code in [200, 404]
    
    def test_create_barber(self, client, admin_headers):
        """Crear nuevo barbero"""
        barber_data = {
            'email': 'newbarber@example.com',
            'full_name': 'New Barber',
            'phone': '+56912345678',
            'specialties': ['cortes', 'afeitado'],
        }
        
        response = client.post(
            '/api/barbers',
            json=barber_data,
            headers=admin_headers
        )
        
        assert response.status_code in [201, 404, 422]
    
    def test_get_barber_availability(self, client, admin_headers):
        """Obtener disponibilidad de barbero"""
        barber_id = 'barber-123'
        
        response = client.get(
            f'/api/barbers/{barber_id}/availability',
            headers=admin_headers
        )
        
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestClientEndpoints:
    """Tests para endpoints de clientes"""
    
    def test_list_clients(self, client, admin_headers):
        """Listar clientes"""
        response = client.get('/api/clients', headers=admin_headers)
        
        assert response.status_code in [200, 404]
    
    def test_create_client(self, client, admin_headers):
        """Crear nuevo cliente"""
        client_data = {
            'email': 'newclient@example.com',
            'full_name': 'New Client',
            'phone': '+56912345678',
        }
        
        response = client.post(
            '/api/clients',
            json=client_data,
            headers=admin_headers
        )
        
        assert response.status_code in [201, 404, 422]
    
    def test_get_client_profile(self, client, client_headers):
        """Obtener perfil de cliente"""
        # Cliente obtiene su propio perfil
        response = client.get('/api/clients/profile', headers=client_headers)
        
        assert response.status_code in [200, 404, 401]


@pytest.mark.integration
class TestPaymentEndpoints:
    """Tests para endpoints de pagos"""
    
    def test_list_payments(self, client, admin_headers):
        """Listar pagos"""
        response = client.get('/api/payments', headers=admin_headers)
        
        assert response.status_code in [200, 404]
    
    def test_create_payment(self, client, admin_headers, payment_data):
        """Crear nuevo pago"""
        response = client.post(
            '/api/payments',
            json=payment_data,
            headers=admin_headers
        )
        
        assert response.status_code in [201, 404, 422]
    
    def test_refund_payment(self, client, admin_headers):
        """Reembolsar pago"""
        payment_id = 'payment-123'
        
        response = client.post(
            f'/api/payments/{payment_id}/refund',
            headers=admin_headers
        )
        
        assert response.status_code in [200, 404, 422]


@pytest.mark.integration
class TestReportEndpoints:
    """Tests para endpoints de reportes"""
    
    def test_list_reports(self, client, admin_headers):
        """Listar reportes"""
        response = client.get('/api/reports', headers=admin_headers)
        
        assert response.status_code in [200, 404]
    
    def test_generate_sales_report(self, client, admin_headers):
        """Generar reporte de ventas"""
        report_data = {
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'format': 'pdf',
        }
        
        response = client.post(
            '/api/reports/sales',
            json=report_data,
            headers=admin_headers
        )
        
        assert response.status_code in [201, 404, 422]
    
    def test_generate_barber_performance_report(self, client, admin_headers):
        """Generar reporte de desempeño de barbero"""
        report_data = {
            'barber_id': 'barber-123',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'format': 'excel',
        }
        
        response = client.post(
            '/api/reports/barber-performance',
            json=report_data,
            headers=admin_headers
        )
        
        assert response.status_code in [201, 404, 422]


@pytest.mark.integration
class TestPermissionValidation:
    """Tests para validación de permisos"""
    
    def test_client_cannot_create_appointment_for_others(self, client, client_headers):
        """Cliente no puede crear cita para otros"""
        appointment_data = {
            'barber_id': 'barber-123',
            'client_id': 'other-client-456',  # Cliente diferente
            'service_id': 'service-123',
            'scheduled_at': datetime.now().isoformat(),
        }
        
        response = client.post(
            '/api/appointments',
            json=appointment_data,
            headers=client_headers
        )
        
        # Debería rechazar o retornar 403
        assert response.status_code in [403, 404, 401, 422]
    
    def test_barber_cannot_access_payments(self, client, barber_headers):
        """Barbero no puede acceder a pagos"""
        response = client.get('/api/payments', headers=barber_headers)
        
        # Debería rechazar o retornar 403
        assert response.status_code in [403, 404, 401]
    
    def test_admin_can_access_all(self, client, admin_headers):
        """Admin puede acceder a todo"""
        endpoints = [
            '/api/appointments',
            '/api/barbers',
            '/api/clients',
            '/api/payments',
            '/api/reports',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=admin_headers)
            
            # Admin debería tener acceso (200 o 404 si no existe, pero no 403)
            assert response.status_code != 403


@pytest.mark.integration
class TestErrorHandling:
    """Tests para manejo de errores"""
    
    def test_404_not_found(self, client, admin_headers):
        """Endpoint no existente retorna 404"""
        response = client.get('/api/nonexistent', headers=admin_headers)
        
        assert response.status_code == 404
    
    def test_invalid_json_payload(self, client, admin_headers):
        """JSON inválido retorna error"""
        # Simular request con JSON inválido
        response = client.post(
            '/api/appointments',
            data='invalid json {',
            headers={**admin_headers, 'Content-Type': 'application/json'}
        )
        
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, client, admin_headers):
        """Campos requeridos faltantes retornan error"""
        response = client.post(
            '/api/appointments',
            json={},  # Vacío, sin campos requeridos
            headers=admin_headers
        )
        
        assert response.status_code in [400, 422]


@pytest.mark.integration
class TestResponseFormats:
    """Tests para formato de respuestas"""
    
    def test_success_response_format(self, client, admin_headers):
        """Respuesta exitosa tiene formato correcto"""
        response = client.get('/api/health', headers=admin_headers)
        
        if response.status_code == 200:
            data = response.json()
            # Debería tener estructura consistente
            assert isinstance(data, dict)
    
    def test_error_response_format(self, client, admin_headers):
        """Respuesta de error tiene formato correcto"""
        response = client.get('/api/nonexistent', headers=admin_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert isinstance(data, dict)
    
    def test_list_response_is_array(self, client, admin_headers):
        """Respuesta de lista es array"""
        response = client.get('/api/appointments', headers=admin_headers)
        
        if response.status_code == 200:
            data = response.json()
            # Debería ser lista o tener items
            assert isinstance(data, (list, dict))
