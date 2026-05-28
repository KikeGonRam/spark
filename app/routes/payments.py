"""
Payment Routes - Pagos y facturas
Endpoints: /api/payments/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date, datetime
from typing import Optional
from decimal import Decimal
import os

from app.models import (
    PaymentMethod,
    PaymentStatus,
)
from app.services import PaymentService
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    ConflictError,
)
from app.routes.dependencies import get_db, require_authenticated, require_admin
from app.models.user import User

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_payment_service() -> PaymentService:
    """Obtener instancia del servicio de pagos."""
    from app.repositories import (
        PaymentRepository,
        InvoiceRepository,
        AppointmentRepository,
        ClientRepository,
    )
    from app.routes.dependencies import get_db
    
    db = get_db()
    
    return PaymentService(
        PaymentRepository(db),
        InvoiceRepository(db),
        AppointmentRepository(db),
        ClientRepository(db),
    )


# ===== PROCESS PAYMENT =====

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def process_payment(
    appointment_id: str,
    amount: Decimal,
    payment_method: PaymentMethod,
    reference: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Procesar pago para una cita.

    **Query parameters:**
    - appointment_id: ID de la cita
    - amount: Monto a pagar
    - payment_method: Método (CASH, CREDIT_CARD, DEBIT_CARD, BANK_TRANSFER, DIGITAL_WALLET)
    - reference: Referencia externa (ej: ID de transacción)
    - notes: Notas adicionales

    **Response:**
    - payment: Datos del pago
    - payment_id: ID del pago

    **Validaciones:**
    - Cita existe
    - Monto > 0
    - Monto coincide con cita
    - No existe pago completado anterior

    **Códigos de respuesta:**
    - 201: Pago procesado
    - 400: Validación fallida
    - 409: Conflicto (ya existe pago)
    """
    try:
        payment = await payment_service.process_payment(
            appointment_id, amount, payment_method, reference, notes
        )
        return {
            "success": True,
            "message": "Pago procesado exitosamente",
            "data": {
                "payment_id": str(payment.id),
                "payment": payment,
            },
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ===== READ =====

@router.get("/{payment_id}", response_model=dict)
async def get_payment(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Obtener un pago por ID.

    **Path parameters:**
    - payment_id: ID del pago

    **Response:**
    - payment: Datos del pago

    **Códigos de respuesta:**
    - 200: Pago obtenido
    - 404: Pago no encontrado
    """
    try:
        payment = await payment_service.get_payment_by_id(payment_id)
        return {
            "success": True,
            "data": {"payment": payment},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=dict)
async def list_payments(
    status: Optional[PaymentStatus] = Query(None),
    method: Optional[PaymentMethod] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Listar pagos con filtros.

    **Query parameters:**
    - status: Filtrar por estado (PENDING, COMPLETED, FAILED, REFUNDED)
    - method: Filtrar por método de pago
    - start_date: Fecha inicio (YYYY-MM-DD)
    - end_date: Fecha fin (YYYY-MM-DD)
    - skip: Saltar registros
    - limit: Límite de registros

    **Response:**
    - payments: Lista de pagos
    - total: Total de registros

    **Códigos de respuesta:**
    - 200: Lista obtenida
    """
    db = await get_db()
    col = db["payments"]
    query = {}
    if status:
        query["status"] = status.value if hasattr(status, 'value') else status
    if method:
        query["method"] = method.value if hasattr(method, 'value') else method
    if start_date:
        query.setdefault("created_at", {})["$gte"] = start_date.isoformat()
    if end_date:
        query.setdefault("created_at", {})["$lte"] = end_date.isoformat() + "T23:59:59"

    total = await col.count_documents(query)
    cursor = col.find(query).sort("created_at", -1).skip(skip).limit(limit)
    payments_list = []
    async for p in cursor:
        p["id"] = str(p.pop("_id"))
        payments_list.append(p)

    return {
        "success": True,
        "data": {
            "payments": payments_list,
            "total": total,
        },
    }


@router.get("/appointment/{appointment_id}", response_model=dict)
async def get_payment_by_appointment(
    appointment_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Obtener pagos de una cita.

    **Path parameters:**
    - appointment_id: ID de la cita

    **Response:**
    - payments: Lista de pagos

    **Códigos de respuesta:**
    - 200: Pagos obtenidos
    """
    # TODO: Implementar
    return {
        "success": True,
        "data": {
            "payments": [],
        },
    }


# ===== REFUNDS =====

@router.post("/{payment_id}/refund", response_model=dict)
async def refund_payment(
    payment_id: str,
    reason: str,
    refund_amount: Optional[Decimal] = Query(None),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Procesar reembolso de un pago.

    **Path parameters:**
    - payment_id: ID del pago

    **Query parameters:**
    - reason: Razón del reembolso
    - refund_amount: Monto a reembolsar (default: monto completo)

    **Response:**
    - payment: Pago con estado REFUNDED

    **Validaciones:**
    - Pago existe
    - Pago en estado COMPLETED
    - Monto válido

    **Códigos de respuesta:**
    - 200: Reembolso procesado
    - 404: Pago no encontrado
    - 400: Validación fallida
    """
    try:
        payment = await payment_service.refund_payment(
            payment_id, reason, refund_amount
        )
        return {
            "success": True,
            "message": "Reembolso procesado",
            "data": {"payment": payment},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== INVOICES =====

@router.post("/{payment_id}/invoice", response_model=dict)
async def generate_invoice(
    payment_id: str,
    customer_email: str,
    customer_name: Optional[str] = Query(None),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Generar factura para un pago.

    **Path parameters:**
    - payment_id: ID del pago

    **Query parameters:**
    - customer_email: Email del cliente
    - customer_name: Nombre del cliente (opcional)

    **Response:**
    - invoice: Factura generada
    - invoice_id: ID de la factura

    **Códigos de respuesta:**
    - 200: Factura generada
    - 404: Pago no encontrado
    - 400: No puede generarse
    """
    try:
        invoice = await payment_service.generate_invoice(
            payment_id, customer_email, customer_name
        )
        return {
            "success": True,
            "message": "Factura generada",
            "data": {
                "invoice_id": str(invoice.id),
                "invoice": invoice,
            },
        }
    except (ResourceNotFoundError, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/invoice/{invoice_id}", response_model=dict)
async def get_invoice(
    invoice_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Obtener una factura por ID.

    **Path parameters:**
    - invoice_id: ID de la factura

    **Response:**
    - invoice: Datos de la factura

    **Códigos de respuesta:**
    - 200: Factura obtenida
    - 404: Factura no encontrada
    """
    try:
        invoice = await payment_service.get_invoice_by_id(invoice_id)
        return {
            "success": True,
            "data": {"invoice": invoice},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/invoices", response_model=dict)
async def list_unpaid_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Listar facturas sin pagar.

    **Query parameters:**
    - skip: Saltar registros
    - limit: Límite de registros

    **Response:**
    - invoices: Lista de facturas pendientes
    - total: Total de facturas

    **Códigos de respuesta:**
    - 200: Lista obtenida
    """
    # TODO: Implementar
    return {
        "success": True,
        "data": {
            "invoices": [],
            "total": 0,
        },
    }


@router.post("/invoice/{invoice_id}/mark-paid", response_model=dict)
async def mark_invoice_as_paid(
    invoice_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Marcar factura como pagada.

    **Path parameters:**
    - invoice_id: ID de la factura

    **Response:**
    - invoice: Factura actualizada

    **Códigos de respuesta:**
    - 200: Factura actualizada
    - 404: Factura no encontrada
    """
    try:
        invoice = await payment_service.mark_invoice_as_paid(invoice_id)
        return {
            "success": True,
            "message": "Factura marcada como pagada",
            "data": {"invoice": invoice},
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== REPORTS & ANALYTICS =====

@router.get("/revenue/daily", response_model=dict)
async def get_daily_revenue(
    revenue_date: date,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Obtener ingresos del día.

    **Query parameters:**
    - revenue_date: Fecha (YYYY-MM-DD)

    **Response:**
    - date: Fecha
    - total_revenue: Ingresos totales
    - transaction_count: Número de transacciones

    **Códigos de respuesta:**
    - 200: Ingresos obtenidos
    """
    try:
        revenue = await payment_service.get_daily_revenue(revenue_date)
        return {
            "success": True,
            "data": {
                "date": str(revenue_date),
                "total_revenue": str(revenue),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/revenue/monthly", response_model=dict)
async def get_monthly_revenue(
    year: int,
    month: int = Query(ge=1, le=12),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Obtener ingresos del mes.

    **Query parameters:**
    - year: Año (ej: 2026)
    - month: Mes (1-12)

    **Response:**
    - year: Año
    - month: Mes
    - total_revenue: Ingresos totales

    **Códigos de respuesta:**
    - 200: Ingresos obtenidos
    """
    try:
        revenue = await payment_service.get_monthly_revenue(year, month)
        return {
            "success": True,
            "data": {
                "year": year,
                "month": month,
                "total_revenue": str(revenue),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== STRIPE PAYMENT INTENT =====

@router.post("/stripe/intent", response_model=dict)
async def create_stripe_payment_intent(
    payment_data: dict,
    current_user: User = Depends(require_authenticated),
):
    """Crear Payment Intent de Stripe para pago con tarjeta."""
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Stripe no configurado")

    amount = payment_data.get("amount", 0)
    try:
        amount_cents = int(float(amount) * 100)
        if amount_cents <= 0:
            raise HTTPException(status_code=400, detail="Monto inválido")

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="mxn",
            metadata={
                "user_id": str(current_user.id),
                "appointment_id": payment_data.get("appointment_id", ""),
            },
            description=f"BarberPro — Cita para {current_user.email}",
        )

        db = await get_db()
        doc = {
            "stripe_intent_id": intent.id,
            "amount": float(amount),
            "tip": float(payment_data.get("tip", 0)),
            "method": "credit_card",
            "status": "processing",
            "customer_name": current_user.name,
            "appointment_id": payment_data.get("appointment_id", ""),
            "card_last4": payment_data.get("card_last4", ""),
            "created_at": datetime.utcnow().isoformat(),
        }
        await db["payments"].insert_one(doc)

        return {
            "success": True,
            "data": {
                "client_secret": intent.client_secret,
                "intent_id": intent.id,
                "amount": float(amount),
            },
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=402, detail=str(e.user_message or e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stripe/list", response_model=dict)
async def list_stripe_payments(
    current_user: User = Depends(require_admin),
):
    """Listar pagos registrados con Stripe (admin only)."""
    db = await get_db()
    col = db["payments"]
    cursor = col.find({"stripe_intent_id": {"$exists": True}}).sort("created_at", -1).limit(100)
    results = []
    async for p in cursor:
        p["id"] = str(p.pop("_id"))
        results.append(p)
    return {"success": True, "data": {"payments": results}}


@router.get("/revenue/summary", response_model=dict)
async def get_revenue_summary(
    start_date: date,
    end_date: date,
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    Obtener resumen de ingresos en un período.

    **Query parameters:**
    - start_date: Fecha inicio (YYYY-MM-DD)
    - end_date: Fecha fin (YYYY-MM-DD)

    **Response:**
    - total_revenue: Ingresos totales
    - total_payments: Número de pagos
    - average_payment: Pago promedio
    - by_method: Desglose por método

    **Códigos de respuesta:**
    - 200: Resumen obtenido
    """
    try:
        summary = await payment_service.get_revenue_summary(start_date, end_date)
        return {
            "success": True,
            "data": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
