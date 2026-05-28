"""
Dashboard Routes - Datos en tiempo real para dashboards
Endpoints: /api/dashboard/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import date
from typing import Optional

from app.services import AnalyticsService
from app.exceptions import ResourceNotFoundError

router = APIRouter()


# ===== DEPENDENCIES =====

async def get_analytics_service() -> AnalyticsService:
    """Obtener instancia del servicio de analytics."""
    from app.repositories import (
        AppointmentRepository,
        PaymentRepository,
        ClientRepository,
        BarberRepository,
    )
    from app.routes.dependencies import get_db
    
    db = get_db()
    
    return AnalyticsService(
        AppointmentRepository(db),
        PaymentRepository(db),
        ClientRepository(db),
        BarberRepository(db),
    )


# ===== MAIN DASHBOARD =====

@router.get("/summary", response_model=dict)
async def get_dashboard_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener resumen ejecutivo del dashboard principal.

    **Response:**
    - today_revenue: Ingresos de hoy
    - today_appointments: Citas de hoy
    - total_clients: Total de clientes
    - total_barbers: Total de barberos
    - pending_appointments: Citas pendientes
    - vip_clients: Clientes VIP

    **Notas:**
    - Datos en tiempo real
    - Se recomienda cachear por 1 minuto

    **Códigos de respuesta:**
    - 200: Resumen obtenido
    """
    summary = await analytics_service.get_dashboard_summary()
    return {
        "success": True,
        "data": summary,
    }


# ===== METRICS =====

@router.get("/metrics/revenue", response_model=dict)
async def get_revenue_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener métricas de ingresos.

    **Query parameters:**
    - start_date: Fecha inicio (default: hace 30 días)
    - end_date: Fecha fin (default: hoy)

    **Response:**
    - total_revenue: Ingresos totales
    - average_daily: Promedio diario
    - highest_day: Día con mayor ingreso
    - growth_vs_previous: Crecimiento vs período anterior

    **Códigos de respuesta:**
    - 200: Métricas obtenidas
    """
    metrics = await analytics_service.get_revenue_metrics(start_date, end_date)
    return {
        "success": True,
        "data": metrics,
    }


@router.get("/metrics/appointments", response_model=dict)
async def get_appointment_metrics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener métricas de citas.

    **Query parameters:**
    - start_date: Fecha inicio (default: hace 30 días)
    - end_date: Fecha fin (default: hoy)

    **Response:**
    - total_appointments: Total de citas
    - completed: Completadas
    - cancelled: Canceladas
    - cancellation_rate: Tasa de cancelación
    - average_rating: Calificación promedio

    **Códigos de respuesta:**
    - 200: Métricas obtenidas
    """
    metrics = await analytics_service.get_appointment_metrics(
        start_date, end_date
    )
    return {
        "success": True,
        "data": metrics,
    }


@router.get("/metrics/clients", response_model=dict)
async def get_client_metrics(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener métricas de clientes.

    **Response:**
    - total_clients: Total de clientes
    - new_clients_this_month: Nuevos clientes este mes
    - active_clients: Clientes activos
    - vip_clients: Clientes VIP
    - customer_retention_rate: Tasa de retención

    **Códigos de respuesta:**
    - 200: Métricas obtenidas
    """
    metrics = await analytics_service.get_client_metrics()
    return {
        "success": True,
        "data": metrics,
    }


# ===== TRENDS =====

@router.get("/trends/revenue", response_model=dict)
async def get_revenue_trend(
    days: int = Query(30, ge=7, le=365),
    interval: str = Query("daily"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener tendencia de ingresos.

    **Query parameters:**
    - days: Número de días (default: 30, min: 7, max: 365)
    - interval: Intervalo (daily, weekly, monthly) - default: daily

    **Response:**
    - trend: Lista de puntos [date, amount]

    **Usos:**
    - Gráficos de línea
    - Análisis de tendencias

    **Códigos de respuesta:**
    - 200: Tendencia obtenida
    """
    trend = await analytics_service.get_revenue_trend(days, interval)
    return {
        "success": True,
        "data": {
            "trend": trend,
            "interval": interval,
            "days": days,
        },
    }


@router.get("/trends/appointments", response_model=dict)
async def get_appointment_trend(
    days: int = Query(30, ge=7, le=365),
    interval: str = Query("daily"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener tendencia de citas.

    **Query parameters:**
    - days: Número de días (default: 30)
    - interval: Intervalo (daily, weekly, monthly) - default: daily

    **Response:**
    - trend: Lista de puntos [date, count]

    **Usos:**
    - Gráficos de línea
    - Predicción de demanda

    **Códigos de respuesta:**
    - 200: Tendencia obtenida
    """
    trend = await analytics_service.get_appointment_trend(days, interval)
    return {
        "success": True,
        "data": {
            "trend": trend,
            "interval": interval,
            "days": days,
        },
    }


# ===== RANKINGS =====

@router.get("/rankings/barbers", response_model=dict)
async def get_barber_rankings(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener ranking de barberos.

    **Response:**
    - barbers: Lista ordenada de barberos
    - metrics: rating, appointments_count, earnings

    **Usos:**
    - Mostrar top performers
    - Identificar barberos con bajo performance

    **Códigos de respuesta:**
    - 200: Ranking obtenido
    """
    barbers = await analytics_service.compare_barbers()
    return {
        "success": True,
        "data": {
            "barbers": barbers,
        },
    }


@router.get("/rankings/services", response_model=dict)
async def get_service_rankings(
    limit: int = Query(10, ge=1, le=50),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener servicios más populares.

    **Query parameters:**
    - limit: Número máximo (default: 10, max: 50)

    **Response:**
    - services: Lista ordenada por popularidad
    - metrics: bookings, revenue, avg_rating

    **Códigos de respuesta:**
    - 200: Ranking obtenido
    """
    services = await analytics_service.get_top_services(limit)
    return {
        "success": True,
        "data": {
            "services": services,
            "limit": limit,
        },
    }


# ===== SEGMENTATION =====

@router.get("/segmentation/clients", response_model=dict)
async def get_client_segmentation(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener segmentación de clientes.

    **Response:**
    - segments: Categorías de clientes
    - high_value: Clientes de alto valor
    - medium_value: Clientes de medio valor
    - low_value: Clientes de bajo valor
    - churn_risk: Clientes con riesgo de abandono

    **Usos:**
    - Estrategia de marketing
    - Retención de clientes

    **Códigos de respuesta:**
    - 200: Segmentación obtenida
    """
    segmentation = await analytics_service.get_client_segmentation()
    return {
        "success": True,
        "data": segmentation,
    }


# ===== FORECASTS =====

@router.get("/forecasts/revenue", response_model=dict)
async def forecast_revenue(
    days: int = Query(30, ge=7, le=90),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Predecir ingresos futuros.

    **Query parameters:**
    - days: Días a predecir (default: 30, max: 90)

    **Response:**
    - forecast: Lista de predicciones [date, amount, confidence]
    - model: Nombre del modelo usado
    - accuracy: Precisión histórica

    **Notas:**
    - Usa modelo ARIMA
    - Basado en últimos 12 meses
    - Confianza 0-1

    **Códigos de respuesta:**
    - 200: Predicción obtenida
    """
    forecast = await analytics_service.forecast_revenue(days)
    return {
        "success": True,
        "data": {
            "forecast": forecast,
            "days": days,
            "model": "ARIMA",
        },
    }


@router.get("/forecasts/appointments", response_model=dict)
async def forecast_appointments(
    days: int = Query(30, ge=7, le=90),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Predecir citas futuras.

    **Query parameters:**
    - days: Días a predecir (default: 30)

    **Response:**
    - forecast: Lista de predicciones [date, count]

    **Códigos de respuesta:**
    - 200: Predicción obtenida
    """
    forecast = await analytics_service.forecast_appointments(days)
    return {
        "success": True,
        "data": {
            "forecast": forecast,
            "days": days,
        },
    }


# ===== RECOMMENDATIONS =====

@router.get("/recommendations", response_model=dict)
async def get_recommendations(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener recomendaciones de acciones.

    **Response:**
    - marketing: Recomendaciones de marketing
    - operations: Recomendaciones operacionales
    - customer_service: Recomendaciones de servicio

    **Usos:**
    - Alertas automáticas
    - Sugerencias para mejorar

    **Códigos de respuesta:**
    - 200: Recomendaciones obtenidas
    """
    recommendations = await analytics_service.get_recommendations()
    return {
        "success": True,
        "data": recommendations,
    }


# ===== ANOMALIES =====

@router.get("/anomalies", response_model=dict)
async def get_anomalies(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Detectar anomalías en datos.

    **Response:**
    - anomalies: Lista de anomalías detectadas
    - severity: Severidad (low, medium, high)
    - description: Descripción del problema

    **Ejemplos de anomalías:**
    - Caída repentina de ingresos
    - Aumento de cancelaciones
    - Cliente con compras atípicas

    **Códigos de respuesta:**
    - 200: Análisis completado
    """
    anomalies = await analytics_service.get_anomalies()
    return {
        "success": True,
        "data": {
            "anomalies": anomalies,
            "count": len(anomalies),
        },
    }
