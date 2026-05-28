"""
Report Routes - Generación de reportes
Endpoints: /api/reports/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date
from typing import Optional
from fastapi.responses import FileResponse

from app.services import ReportService
from app.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_report_service() -> ReportService:
    """Obtener instancia del servicio de reportes."""
    from app.repositories import (
        AppointmentRepository,
        PaymentRepository,
        ClientRepository,
        BarberRepository,
    )
    from app.routes.dependencies import get_db
    
    db = get_db()
    
    return ReportService(
        AppointmentRepository(db),
        PaymentRepository(db),
        ClientRepository(db),
        BarberRepository(db),
    )


# ===== REVENUE REPORTS =====

@router.post("/revenue", response_model=dict)
async def generate_revenue_report(
    start_date: date,
    end_date: date,
    format: str = Query("pdf"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Generar reporte de ingresos.

    **Query parameters:**
    - start_date: Fecha inicio (YYYY-MM-DD)
    - end_date: Fecha fin (YYYY-MM-DD)
    - format: Formato (pdf, excel) - default: pdf

    **Response:**
    - file: Archivo descargable

    **Códigos de respuesta:**
    - 200: Reporte generado
    - 400: Validación fallida
    """
    try:
        file_data = await report_service.generate_revenue_report(
            start_date, end_date, format
        )
        filename = f"reporte-ingresos-{start_date}-a-{end_date}.{format}"
        return {
            "success": True,
            "message": f"Reporte generado en {format.upper()}",
            "file": filename,
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== CLIENT REPORTS =====

@router.post("/client/{client_id}", response_model=dict)
async def generate_client_report(
    client_id: str,
    format: str = Query("pdf"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Generar reporte de cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Query parameters:**
    - format: Formato (pdf, excel) - default: pdf

    **Response:**
    - file: Archivo descargable

    **Códigos de respuesta:**
    - 200: Reporte generado
    - 404: Cliente no encontrado
    """
    try:
        file_data = await report_service.generate_client_report(client_id, format)
        return {
            "success": True,
            "message": f"Reporte generado en {format.upper()}",
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== BARBER REPORTS =====

@router.post("/barber/{barber_id}", response_model=dict)
async def generate_barber_report(
    barber_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("pdf"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Generar reporte de performance de barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Query parameters:**
    - start_date: Fecha inicio (default: hace 30 días)
    - end_date: Fecha fin (default: hoy)
    - format: Formato (pdf, excel) - default: pdf

    **Response:**
    - file: Archivo descargable

    **Códigos de respuesta:**
    - 200: Reporte generado
    - 404: Barbero no encontrado
    """
    try:
        file_data = await report_service.generate_barber_performance_report(
            barber_id, start_date, end_date, format
        )
        return {
            "success": True,
            "message": f"Reporte generado en {format.upper()}",
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== BUSINESS SUMMARY =====

@router.post("/business-summary", response_model=dict)
async def generate_business_summary(
    start_date: date,
    end_date: date,
    format: str = Query("pdf"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Generar resumen ejecutivo del negocio.

    **Query parameters:**
    - start_date: Fecha inicio (YYYY-MM-DD)
    - end_date: Fecha fin (YYYY-MM-DD)
    - format: Formato (pdf, excel) - default: pdf

    **Response:**
    - file: Archivo descargable

    **Códigos de respuesta:**
    - 200: Reporte generado
    - 400: Validación fallida
    """
    try:
        file_data = await report_service.generate_business_summary(
            start_date, end_date, format
        )
        return {
            "success": True,
            "message": f"Resumen generado en {format.upper()}",
        }
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ===== EXPORTS =====

@router.post("/export/appointments", response_model=dict)
async def export_appointments(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    format: str = Query("excel"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Exportar datos de citas.

    **Query parameters:**
    - start_date: Fecha inicio (opcional)
    - end_date: Fecha fin (opcional)
    - format: Formato (excel, csv) - default: excel

    **Response:**
    - file: Archivo descargable

    **Códigos de respuesta:**
    - 200: Datos exportados
    """
    # TODO: Implementar
    return {
        "success": True,
        "message": f"Datos exportados a {format.upper()}",
    }


@router.post("/export/clients", response_model=dict)
async def export_clients(
    format: str = Query("excel"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Exportar lista de clientes.

    **Query parameters:**
    - format: Formato (excel, csv) - default: excel

    **Response:**
    - file: Archivo descargable

    **Códigos de respuesta:**
    - 200: Datos exportados
    """
    # TODO: Implementar
    return {
        "success": True,
        "message": f"Clientes exportados a {format.upper()}",
    }


@router.post("/export/barbers", response_model=dict)
async def export_barbers(
    format: str = Query("excel"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    Exportar lista de barberos.

    **Query parameters:**
    - format: Formato (excel, csv) - default: excel

    **Response:**
    - file: Archivo descargable

    **Códigos de respuesta:**
    - 200: Datos exportados
    """
    # TODO: Implementar
    return {
        "success": True,
        "message": f"Barberos exportados a {format.upper()}",
    }
