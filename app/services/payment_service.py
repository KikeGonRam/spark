"""
PaymentService - Lógica de negocio para pagos
Maneja: procesamiento de pagos, refunds, generación de facturas
Integración con gateway de pagos, reportes de ingresos
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from decimal import Decimal
from enum import Enum

from app.models import (
    Payment,
    PaymentCreate,
    PaymentUpdate,
    Invoice,
    InvoiceCreate,
    PaymentStatus,
    PaymentMethod,
)
from app.repositories import (
    PaymentRepository,
    InvoiceRepository,
    AppointmentRepository,
    ClientRepository,
)
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    ConflictError,
)


class PaymentService:
    """Servicio de lógica de negocio para pagos."""

    def __init__(
        self,
        payment_repo: PaymentRepository,
        invoice_repo: InvoiceRepository,
        appointment_repo: AppointmentRepository,
        client_repo: ClientRepository,
    ):
        self.payment_repo = payment_repo
        self.invoice_repo = invoice_repo
        self.appointment_repo = appointment_repo
        self.client_repo = client_repo

    # ===== PROCESAMIENTO DE PAGOS =====

    async def process_payment(
        self,
        appointment_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        reference: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Payment:
        """
        Procesar un pago para una cita.

        Args:
            appointment_id: ID de la cita
            amount: Monto a pagar
            payment_method: Método de pago
            reference: Referencia externa (ej: ID de transacción)
            notes: Notas adicionales

        Returns:
            Payment: El pago creado

        Raises:
            ResourceNotFoundError: Si la cita no existe
            ValidationError: Si los datos no son válidos
            ConflictError: Si ya existe un pago completado
        """
        # Validar cita
        appointment = await self.appointment_repo.find_by_id(appointment_id)
        if not appointment:
            raise ResourceNotFoundError(f"Cita {appointment_id} no encontrada")

        # Validar que no exista pago completado
        existing_payments = await self.payment_repo.find_by_appointment(
            appointment_id
        )

        for payment in existing_payments:
            if payment.status == PaymentStatus.COMPLETED:
                raise ConflictError(
                    f"Ya existe un pago completado para esta cita"
                )

        # Validar monto
        if amount <= 0:
            raise ValidationError("El monto debe ser mayor a 0")

        if amount != appointment.total_cost:
            # TODO: Permitir pagos parciales o en cuotas
            raise ValidationError(
                f"El monto debe ser {appointment.total_cost}"
            )

        # Crear pago
        payment = await self.payment_repo.create(
            Payment(
                appointment_id=appointment_id,
                amount=amount,
                payment_method=payment_method,
                status=PaymentStatus.COMPLETED,
                reference=reference,
                notes=notes,
                processed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        # Actualizar estado de cita (opcional)
        # await self.appointment_repo.update(appointment_id, {...})

        # Actualizar gasto total del cliente
        # TODO: Agregar monto al total_spent del cliente

        return payment

    async def get_payment_by_id(self, payment_id: str) -> Payment:
        """Obtener un pago por ID."""
        payment = await self.payment_repo.find_by_id(payment_id)
        if not payment:
            raise ResourceNotFoundError(f"Pago {payment_id} no encontrado")
        return payment

    async def list_payments_by_appointment(
        self, appointment_id: str
    ) -> List[Payment]:
        """Listar pagos de una cita."""
        return await self.payment_repo.find_by_appointment(appointment_id)

    async def list_payments_by_client(
        self, client_id: str, skip: int = 0, limit: int = 50
    ) -> List[Payment]:
        """Listar pagos de un cliente."""
        # TODO: Implementar join con appointments por client_id
        return []

    async def list_payments_by_status(
        self,
        status: PaymentStatus,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Payment]:
        """Listar pagos por estado."""
        return await self.payment_repo.find_by_status(status, skip, limit)

    async def list_payments_by_date_range(
        self,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Payment]:
        """Listar pagos en un rango de fechas."""
        return await self.payment_repo.find_by_date_range(
            start_date, end_date, skip, limit
        )

    async def list_payments_by_method(
        self,
        payment_method: PaymentMethod,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Payment]:
        """Listar pagos por método."""
        return await self.payment_repo.find_by_method(
            payment_method, skip, limit
        )

    # ===== REFUNDS =====

    async def refund_payment(
        self,
        payment_id: str,
        reason: str,
        refund_amount: Optional[Decimal] = None,
    ) -> Payment:
        """
        Procesar un reembolso para un pago.

        Args:
            payment_id: ID del pago
            reason: Razón del reembolso
            refund_amount: Monto a reembolsar (default: monto completo)

        Returns:
            Payment: El pago con estado REFUNDED

        Raises:
            ResourceNotFoundError: Si el pago no existe
            ValidationError: Si el pago no puede ser reembolsado
        """
        payment = await self.payment_repo.find_by_id(payment_id)
        if not payment:
            raise ResourceNotFoundError(f"Pago {payment_id} no encontrado")

        if payment.status != PaymentStatus.COMPLETED:
            raise ValidationError(
                f"Solo se pueden reembolsar pagos COMPLETED. "
                f"Estado actual: {payment.status}"
            )

        # Validar monto
        refund_amount = refund_amount or payment.amount

        if refund_amount <= 0 or refund_amount > payment.amount:
            raise ValidationError(
                f"El monto de reembolso debe estar entre 0 y {payment.amount}"
            )

        # TODO: Procesar reembolso en gateway de pagos

        # Actualizar estado del pago
        updated = await self.payment_repo.refund_payment(
            payment_id, refund_amount, reason
        )

        return updated

    # ===== FACTURAS =====

    async def generate_invoice(
        self,
        payment_id: str,
        customer_email: str,
        customer_name: Optional[str] = None,
    ) -> Invoice:
        """
        Generar una factura para un pago.

        Args:
            payment_id: ID del pago
            customer_email: Email del cliente
            customer_name: Nombre del cliente

        Returns:
            Invoice: La factura generada

        Raises:
            ResourceNotFoundError: Si el pago no existe
            ValidationError: Si la factura no puede generarse
        """
        payment = await self.payment_repo.find_by_id(payment_id)
        if not payment:
            raise ResourceNotFoundError(f"Pago {payment_id} no encontrado")

        if payment.status != PaymentStatus.COMPLETED:
            raise ValidationError(
                "Solo se pueden generar facturas para pagos completados"
            )

        # TODO: Generar número de factura único
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        invoice = await self.invoice_repo.create(
            Invoice(
                payment_id=payment_id,
                invoice_number=invoice_number,
                customer_email=customer_email,
                customer_name=customer_name or "Cliente",
                amount=payment.amount,
                tax=Decimal("0.00"),  # TODO: Calcular impuestos
                total=payment.amount,
                status=PaymentStatus.PAID,
                issued_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        return invoice

    async def get_invoice_by_id(self, invoice_id: str) -> Invoice:
        """Obtener una factura por ID."""
        invoice = await self.invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise ResourceNotFoundError(f"Factura {invoice_id} no encontrada")
        return invoice

    async def get_invoice_by_number(self, invoice_number: str) -> Invoice:
        """Obtener una factura por número."""
        invoice = await self.invoice_repo.find_by_invoice_number(invoice_number)
        if not invoice:
            raise ResourceNotFoundError(
                f"Factura {invoice_number} no encontrada"
            )
        return invoice

    async def list_unpaid_invoices(
        self, skip: int = 0, limit: int = 50
    ) -> List[Invoice]:
        """Listar facturas sin pagar."""
        return await self.invoice_repo.find_unpaid(skip, limit)

    async def list_invoices_by_customer(
        self, customer_email: str, skip: int = 0, limit: int = 50
    ) -> List[Invoice]:
        """Listar facturas de un cliente."""
        return await self.invoice_repo.find_by_customer_email(
            customer_email, skip, limit
        )

    async def mark_invoice_as_paid(self, invoice_id: str) -> Invoice:
        """Marcar una factura como pagada."""
        invoice = await self.invoice_repo.find_by_id(invoice_id)
        if not invoice:
            raise ResourceNotFoundError(f"Factura {invoice_id} no encontrada")

        updated = await self.invoice_repo.mark_as_paid(invoice_id)
        return updated

    # ===== REPORTES Y ANÁLISIS =====

    async def get_daily_revenue(self, revenue_date: date) -> Decimal:
        """
        Obtener ingresos del día.

        Args:
            revenue_date: Fecha del reporte

        Returns:
            Decimal: Ingresos totales del día
        """
        end_date = revenue_date + timedelta(days=1)

        payments = await self.payment_repo.find_by_date_range(
            revenue_date, end_date
        )

        total = Decimal("0.00")
        for payment in payments:
            if payment.status == PaymentStatus.COMPLETED:
                total += payment.amount

        return total

    async def get_monthly_revenue(self, year: int, month: int) -> Decimal:
        """
        Obtener ingresos del mes.

        Args:
            year: Año
            month: Mes (1-12)

        Returns:
            Decimal: Ingresos totales del mes
        """
        # Calcular rango de fechas
        start_date = date(year, month, 1)

        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        payments = await self.payment_repo.find_by_date_range(
            start_date, end_date
        )

        total = Decimal("0.00")
        for payment in payments:
            if payment.status == PaymentStatus.COMPLETED:
                total += payment.amount

        return total

    async def get_revenue_summary(
        self, start_date: date, end_date: date
    ) -> dict:
        """
        Obtener resumen de ingresos en un período.

        Returns:
            dict: Contiene:
            - total_revenue: Ingresos totales
            - total_payments: Número de pagos
            - average_payment: Pago promedio
            - by_method: Desglose por método de pago
        """
        payments = await self.payment_repo.find_by_date_range(
            start_date, end_date
        )

        total_revenue = Decimal("0.00")
        by_method = {}

        for payment in payments:
            if payment.status == PaymentStatus.COMPLETED:
                total_revenue += payment.amount

                method = payment.payment_method
                if method not in by_method:
                    by_method[method] = Decimal("0.00")
                by_method[method] += payment.amount

        return {
            "total_revenue": total_revenue,
            "total_payments": len(payments),
            "average_payment": (
                total_revenue / len(payments) if payments else Decimal("0.00")
            ),
            "by_method": by_method,
        }

    async def get_payment_method_stats(self) -> dict:
        """
        Obtener estadísticas de métodos de pago.

        Returns:
            dict: Estadísticas por método
        """
        # TODO: Implementar con agregación de base de datos
        return {}
