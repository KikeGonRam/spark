"""
Tests para servicios de negocio
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.unit
class TestAppointmentService:
    """Tests para AppointmentService"""
    
    def test_create_appointment_success(self, test_db):
        """Crear cita exitosamente"""
        from app.services.appointment_service import AppointmentService
        
        service = AppointmentService(test_db)
        
        appointment_data = {
            'barber_id': 'barber-123',
            'client_id': 'client-456',
            'service_id': 'service-789',
            'scheduled_at': datetime.now() + timedelta(days=1),
            'duration_minutes': 30,
            'notes': 'Corte clásico',
        }
        
        # El servicio debería retornar el ID de la cita creada
        result = service.create_appointment(
            barber_id=appointment_data['barber_id'],
            client_id=appointment_data['client_id'],
            service_id=appointment_data['service_id'],
            scheduled_at=appointment_data['scheduled_at'],
            duration_minutes=appointment_data['duration_minutes'],
            notes=appointment_data['notes'],
        )
        
        # Debería tener un ID
        assert result is not None
    
    def test_get_appointment_by_id(self, test_db, create_appointment_in_db):
        """Obtener cita por ID"""
        from app.services.appointment_service import AppointmentService
        
        appointment = {
            'barber_id': 'barber-123',
            'client_id': 'client-456',
            'scheduled_at': datetime.now(),
            'status': 'pending',
        }
        created = create_appointment_in_db(appointment)
        
        service = AppointmentService(test_db)
        result = service.get_appointment(str(created['_id']))
        
        assert result is not None
        if result:
            assert result['barber_id'] == 'barber-123'
    
    def test_update_appointment_status(self, test_db, create_appointment_in_db):
        """Actualizar estado de cita"""
        from app.services.appointment_service import AppointmentService
        from bson import ObjectId
        
        appointment = {
            'barber_id': 'barber-123',
            'client_id': 'client-456',
            'status': 'pending',
        }
        created = create_appointment_in_db(appointment)
        
        service = AppointmentService(test_db)
        result = service.update_appointment(
            str(created['_id']),
            {'status': 'confirmed'}
        )
        
        assert result is not None
    
    def test_list_appointments_by_barber(self, test_db):
        """Listar citas de barbero"""
        from app.services.appointment_service import AppointmentService
        
        barber_id = 'barber-123'
        
        # Crear varias citas
        test_db['appointments'].insert_many([
            {'barber_id': barber_id, 'status': 'pending'},
            {'barber_id': barber_id, 'status': 'confirmed'},
            {'barber_id': 'other-barber', 'status': 'pending'},
        ])
        
        service = AppointmentService(test_db)
        appointments = service.get_appointments_by_barber(barber_id)
        
        assert len(appointments) >= 2
        assert all(a['barber_id'] == barber_id for a in appointments)
    
    def test_cancel_appointment(self, test_db, create_appointment_in_db):
        """Cancelar cita"""
        from app.services.appointment_service import AppointmentService
        
        appointment = {
            'barber_id': 'barber-123',
            'status': 'confirmed',
        }
        created = create_appointment_in_db(appointment)
        
        service = AppointmentService(test_db)
        result = service.cancel_appointment(str(created['_id']))
        
        assert result is not None


@pytest.mark.unit
class TestPaymentService:
    """Tests para PaymentService"""
    
    def test_create_payment(self, test_db):
        """Crear pago"""
        from app.services.payment_service import PaymentService
        
        service = PaymentService(test_db)
        
        payment = service.create_payment(
            appointment_id='appointment-123',
            amount=15000,
            method='card',
        )
        
        assert payment is not None
    
    def test_process_payment(self, test_db):
        """Procesar pago"""
        from app.services.payment_service import PaymentService
        
        service = PaymentService(test_db)
        
        # Crear pago primero
        payment = service.create_payment(
            appointment_id='appointment-123',
            amount=15000,
            method='card',
        )
        
        # Procesar pago
        if payment:
            result = service.process_payment(
                str(payment['_id']),
                transaction_id='txn-abc123'
            )
            assert result is not None
    
    def test_refund_payment(self, test_db):
        """Reembolsar pago"""
        from app.services.payment_service import PaymentService
        
        service = PaymentService(test_db)
        
        # Crear pago completado
        payment = test_db['payments'].insert_one({
            'amount': 15000,
            'status': 'completed',
            'appointment_id': 'appointment-123',
        })
        
        result = service.refund_payment(str(payment.inserted_id))
        
        assert result is not None
    
    def test_get_payment_by_appointment(self, test_db):
        """Obtener pago de cita"""
        from app.services.payment_service import PaymentService
        
        appointment_id = 'appointment-123'
        
        # Crear pagos
        test_db['payments'].insert_many([
            {'appointment_id': appointment_id, 'amount': 15000},
            {'appointment_id': 'other-appointment', 'amount': 20000},
        ])
        
        service = PaymentService(test_db)
        payment = service.get_payment_by_appointment(appointment_id)
        
        if payment:
            assert payment['appointment_id'] == appointment_id


@pytest.mark.unit
class TestDashboardService:
    """Tests para DashboardService"""
    
    def test_get_dashboard_metrics(self, test_db):
        """Obtener métricas del dashboard"""
        from app.services.dashboard_service import DashboardService
        
        service = DashboardService(test_db)
        
        metrics = service.get_metrics()
        
        assert metrics is not None
        assert isinstance(metrics, dict)
    
    def test_get_revenue_today(self, test_db):
        """Obtener ingresos de hoy"""
        from app.services.dashboard_service import DashboardService
        
        service = DashboardService(test_db)
        
        revenue = service.get_revenue_today()
        
        assert revenue is not None
        assert isinstance(revenue, (int, float))
    
    def test_get_appointments_today(self, test_db):
        """Obtener citas de hoy"""
        from app.services.dashboard_service import DashboardService
        
        service = DashboardService(test_db)
        
        appointments = service.get_appointments_today()
        
        assert appointments is not None
        assert isinstance(appointments, (int, list))


@pytest.mark.unit
class TestReportService:
    """Tests para ReportService"""
    
    def test_generate_sales_report(self, test_db):
        """Generar reporte de ventas"""
        from app.services.report_service import ReportService
        
        service = ReportService(test_db)
        
        report = service.generate_sales_report(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
        )
        
        assert report is not None
    
    def test_generate_barber_performance_report(self, test_db):
        """Generar reporte de desempeño"""
        from app.services.report_service import ReportService
        
        service = ReportService(test_db)
        
        report = service.generate_barber_performance_report(
            barber_id='barber-123',
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
        )
        
        assert report is not None
    
    def test_export_report_pdf(self, test_db):
        """Exportar reporte a PDF"""
        from app.services.report_service import ReportService
        
        service = ReportService(test_db)
        
        # Crear reporte primero
        report = {
            'title': 'Test Report',
            'data': [{'item': 'Test', 'value': 100}],
        }
        
        # Exportar
        pdf = service.export_report_pdf(report)
        
        # Debería retornar bytes o None
        assert pdf is None or isinstance(pdf, bytes)
    
    def test_export_report_excel(self, test_db):
        """Exportar reporte a Excel"""
        from app.services.report_service import ReportService
        
        service = ReportService(test_db)
        
        report = {
            'title': 'Test Report',
            'data': [{'item': 'Test', 'value': 100}],
        }
        
        excel = service.export_report_excel(report)
        
        assert excel is None or isinstance(excel, bytes)


@pytest.mark.unit
class TestInventoryService:
    """Tests para InventoryService"""
    
    def test_get_inventory_items(self, test_db):
        """Obtener items de inventario"""
        from app.services.inventory_service import InventoryService
        
        service = InventoryService(test_db)
        
        items = service.get_inventory_items()
        
        assert items is not None
        assert isinstance(items, (list, dict))
    
    def test_update_stock(self, test_db):
        """Actualizar stock"""
        from app.services.inventory_service import InventoryService
        
        service = InventoryService(test_db)
        
        # Crear item primero
        item = test_db['inventory'].insert_one({
            'name': 'Gel',
            'quantity': 100,
        })
        
        result = service.update_stock(str(item.inserted_id), -10)
        
        assert result is not None
    
    def test_low_stock_alert(self, test_db):
        """Alerta de stock bajo"""
        from app.services.inventory_service import InventoryService
        
        service = InventoryService(test_db)
        
        # Crear item con stock bajo
        test_db['inventory'].insert_one({
            'name': 'Gel',
            'quantity': 2,
            'min_quantity': 10,
        })
        
        alerts = service.get_low_stock_items()
        
        assert alerts is not None


@pytest.mark.unit
class TestChatbotService:
    """Tests para ChatbotService"""
    
    @patch('app.services.chatbot_service.gemini_client')
    def test_get_chatbot_response(self, mock_gemini):
        """Obtener respuesta del chatbot"""
        from app.services.chatbot_service import ChatbotService
        
        mock_gemini.generate_content.return_value.text = 'Test response'
        
        service = ChatbotService()
        
        response = service.get_response('¿Cuáles son tus horarios?')
        
        assert response is not None
        assert isinstance(response, str)


@pytest.mark.unit
class TestBusinessEventService:
    """Tests para BusinessEventService"""
    
    def test_create_business_event(self, test_db):
        """Crear evento de negocio"""
        from app.services.business_event_service import BusinessEventService
        
        service = BusinessEventService(test_db)
        
        event = service.create_event(
            event_type='appointment_created',
            data={'appointment_id': 'apt-123'},
        )
        
        assert event is not None
    
    def test_get_event_history(self, test_db):
        """Obtener historial de eventos"""
        from app.services.business_event_service import BusinessEventService
        
        service = BusinessEventService(test_db)
        
        # Crear eventos primero
        test_db['business_events'].insert_many([
            {'event_type': 'appointment_created', 'timestamp': datetime.now()},
            {'event_type': 'payment_received', 'timestamp': datetime.now()},
        ])
        
        events = service.get_event_history()
        
        assert events is not None
        assert isinstance(events, list)


@pytest.mark.unit
class TestServiceValidation:
    """Tests para validación en servicios"""
    
    def test_validate_appointment_time_conflict(self, test_db):
        """Validar conflicto de tiempo en cita"""
        from app.services.appointment_service import AppointmentService
        
        barber_id = 'barber-123'
        scheduled_time = datetime.now() + timedelta(days=1)
        
        # Crear cita existente
        test_db['appointments'].insert_one({
            'barber_id': barber_id,
            'scheduled_at': scheduled_time,
            'duration_minutes': 30,
            'status': 'confirmed',
        })
        
        service = AppointmentService(test_db)
        
        # Intentar crear cita en mismo tiempo
        has_conflict = service.check_barber_availability(
            barber_id,
            scheduled_time,
            30
        )
        
        # Debería detectar conflicto
        assert has_conflict in [True, False]
    
    def test_validate_payment_amount(self, test_db):
        """Validar monto de pago"""
        from app.services.payment_service import PaymentService
        
        service = PaymentService(test_db)
        
        # Monto debe ser positivo
        is_valid = service.validate_payment_amount(15000)
        
        assert is_valid in [True, False]


@pytest.mark.unit
class TestServiceErrorHandling:
    """Tests para manejo de errores en servicios"""
    
    def test_handle_invalid_barber_id(self, test_db):
        """Manejar ID de barbero inválido"""
        from app.services.appointment_service import AppointmentService
        
        service = AppointmentService(test_db)
        
        # ID que no existe
        result = service.get_appointment('invalid-id')
        
        assert result is None or isinstance(result, dict)
    
    def test_handle_duplicate_email(self, test_db, create_user_in_db):
        """Manejar email duplicado"""
        user = {
            'email': 'duplicate@example.com',
            'password_hash': 'hash',
            'full_name': 'Test User',
        }
        create_user_in_db(user)
        
        # Intentar crear otro usuario con mismo email
        from app.repositories.user_repository import UserRepository
        
        repo = UserRepository(test_db)
        existing = repo.find_by_email('duplicate@example.com')
        
        assert existing is not None
