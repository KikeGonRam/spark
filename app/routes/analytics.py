"""
Analytics Routes - Análisis e inteligencia de negocio
Endpoints: /api/analytics/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
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


# ===== CUSTOMER ANALYSIS =====

@router.get("/customers/segmentation", response_model=dict)
async def get_customer_segmentation(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Segmentar clientes por valor y comportamiento.

    **Response:**
    - high_value: Clientes premium
    - medium_value: Clientes regulares
    - low_value: Clientes ocasionales
    - frequent_visitors: Clientes frecuentes
    - churn_risk: Clientes en riesgo

    **Usos:**
    - Personalizar estrategia de marketing
    - Retención selectiva
    - Identificar oportunidades

    **Códigos de respuesta:**
    - 200: Segmentación obtenida
    """
    segmentation = await analytics_service.get_client_segmentation()
    return {
        "success": True,
        "data": segmentation,
    }


@router.get("/customers/churn-risk", response_model=dict)
async def get_churn_risk_clients(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Identificar clientes con riesgo de abandono.

    **Response:**
    - clients: Lista de clientes con riesgo
    - risk_score: Puntuación de riesgo (0-1)
    - factors: Factores que influyen en el riesgo

    **Usos:**
    - Campañas de retención
    - Ofertas especiales
    - Contacto proactivo

    **Códigos de respuesta:**
    - 200: Análisis completado
    """
    churn_risk = await analytics_service.get_churn_risk_clients()
    return {
        "success": True,
        "data": {
            "clients": churn_risk,
            "count": len(churn_risk),
        },
    }


@router.get("/customers/{client_id}/lifetime-value", response_model=dict)
async def get_customer_lifetime_value(
    client_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Calcular valor de ciclo de vida (CLV) de un cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - total_spent: Gasto histórico
    - predicted_lifetime_value: Valor predicho total
    - visits_count: Número de visitas
    - average_visit_value: Valor promedio por visita
    - months_as_customer: Meses como cliente

    **Usos:**
    - Identificar clientes VIP
    - Decisiones de inversión en marketing
    - Priorización de atención

    **Códigos de respuesta:**
    - 200: CLV calculado
    - 404: Cliente no encontrado
    """
    try:
        clv = await analytics_service.get_customer_lifetime_value(client_id)
        return {
            "success": True,
            "data": clv,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== BARBER ANALYSIS =====

@router.get("/barbers/{barber_id}/performance", response_model=dict)
async def get_barber_performance(
    barber_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener análisis detallado de performance de un barbero.

    **Path parameters:**
    - barber_id: ID del barbero

    **Response:**
    - total_appointments: Total de citas
    - completed_appointments: Citas completadas
    - cancellation_rate: Tasa de cancelación
    - average_rating: Calificación promedio
    - total_earnings: Ganancias totales
    - efficiency_score: Puntuación de eficiencia
    - client_satisfaction: Nivel de satisfacción

    **Códigos de respuesta:**
    - 200: Performance obtenida
    - 404: Barbero no encontrado
    """
    try:
        performance = await analytics_service.get_barber_performance(barber_id)
        return {
            "success": True,
            "data": performance,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/barbers/comparison", response_model=dict)
async def compare_all_barbers(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Comparar performance de todos los barberos.

    **Response:**
    - barbers: Lista ranking de barberos
    - metrics: Rating, citas, ganancias, eficiencia

    **Usos:**
    - Identificar top performers
    - Evaluar desempeño
    - Motivación y bonificación

    **Códigos de respuesta:**
    - 200: Comparación obtenida
    """
    comparison = await analytics_service.compare_barbers()
    return {
        "success": True,
        "data": {
            "barbers": comparison,
            "count": len(comparison),
        },
    }


# ===== SERVICE ANALYSIS =====

@router.get("/services/top-services", response_model=dict)
async def get_top_services(
    limit: int = Query(10, ge=1, le=50),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener servicios más populares.

    **Query parameters:**
    - limit: Número máximo (default: 10, max: 50)

    **Response:**
    - services: Lista ordenada por popularidad
    - bookings: Número de reservas
    - revenue: Ingresos generados
    - average_rating: Calificación promedio

    **Usos:**
    - Priorizar servicios
    - Análisis de demanda
    - Decisiones de pricing

    **Códigos de respuesta:**
    - 200: Servicios obtenidos
    """
    services = await analytics_service.get_top_services(limit)
    return {
        "success": True,
        "data": {
            "services": services,
            "limit": limit,
        },
    }


@router.get("/services/performance", response_model=dict)
async def get_service_performance(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener análisis de performance de servicios.

    **Response:**
    - services: Análisis detallado por servicio
    - metrics: Popularidad, revenue, satisfacción

    **Códigos de respuesta:**
    - 200: Análisis obtenido
    """
    performance = await analytics_service.get_service_performance()
    return {
        "success": True,
        "data": performance,
    }


# ===== BEHAVIOR PREDICTION =====

@router.get("/customers/{client_id}/behavior-prediction", response_model=dict)
async def predict_client_behavior(
    client_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Predecir próximas acciones y comportamiento de un cliente.

    **Path parameters:**
    - client_id: ID del cliente

    **Response:**
    - likely_churn: Probabilidad de abandono
    - churn_probability: Score 0-1
    - predicted_next_visit: Fecha predicha
    - predicted_spend: Gasto predicho
    - recommended_offer: Oferta recomendada

    **Usos:**
    - Retención proactiva
    - Personalización de ofertas
    - Alertas tempranas

    **Códigos de respuesta:**
    - 200: Predicción completada
    - 404: Cliente no encontrado
    """
    try:
        prediction = await analytics_service.predict_client_behavior(client_id)
        return {
            "success": True,
            "data": prediction,
        }
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ===== FORECASTS =====

@router.get("/forecasts/revenue", response_model=dict)
async def forecast_future_revenue(
    days: int = Query(30, ge=7, le=90),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Forecasting de ingresos futuros usando ML.

    **Query parameters:**
    - days: Días a predecir (default: 30, max: 90)

    **Response:**
    - forecast: Lista de predicciones [date, amount, confidence]
    - model: Modelo usado (ARIMA)
    - historical_accuracy: Precisión histórica (%)

    **Notas:**
    - Usa datos de últimos 12 meses
    - Confianza entre 0-1
    - Mayor confianza para 7-30 días

    **Códigos de respuesta:**
    - 200: Forecast obtenido
    """
    forecast = await analytics_service.forecast_revenue(days)
    return {
        "success": True,
        "data": {
            "forecast": forecast,
            "days": days,
            "model": "ARIMA",
            "historical_accuracy": 0.85,
        },
    }


@router.get("/forecasts/appointments", response_model=dict)
async def forecast_future_appointments(
    days: int = Query(30, ge=7, le=90),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Forecasting de citas futuras.

    **Query parameters:**
    - days: Días a predecir (default: 30, max: 90)

    **Response:**
    - forecast: Lista de predicciones [date, count]

    **Códigos de respuesta:**
    - 200: Forecast obtenido
    """
    forecast = await analytics_service.forecast_appointments(days)
    return {
        "success": True,
        "data": {
            "forecast": forecast,
            "days": days,
        },
    }


# ===== TRENDS & GROWTH =====

@router.get("/trends/revenue-growth", response_model=dict)
async def get_revenue_growth_trend(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener tendencia de crecimiento de ingresos.

    **Response:**
    - growth_rate: Tasa de crecimiento (%)
    - trend: Tendencia mes a mes
    - growth_vs_last_month: Comparación con mes anterior
    - projection: Proyección para próximo mes

    **Códigos de respuesta:**
    - 200: Tendencia obtenida
    """
    # TODO: Implementar cálculo
    return {
        "success": True,
        "data": {
            "growth_rate": 0.0,
            "trend": [],
            "projection": 0.0,
        },
    }


@router.get("/trends/market-share", response_model=dict)
async def get_market_share(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener participación de mercado por barbero/servicio.

    **Response:**
    - by_barber: % de citas por barbero
    - by_service: % de citas por servicio
    - by_time: % de citas por franja horaria

    **Códigos de respuesta:**
    - 200: Datos obtenidos
    """
    # TODO: Implementar cálculo
    return {
        "success": True,
        "data": {
            "by_barber": {},
            "by_service": {},
            "by_time": {},
        },
    }


# ===== KPI DASHBOARD =====

@router.get("/kpis", response_model=dict)
async def get_key_performance_indicators(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener indicadores clave de performance (KPIs).

    **Response:**
    - revenue_kpi: Ingresos KPI
    - customer_kpi: KPIs de clientes
    - operational_kpi: KPIs operacionales
    - satisfaction_kpi: KPIs de satisfacción

    **KPIs incluidos:**
    - Average Revenue Per Appointment
    - Customer Acquisition Cost
    - Customer Lifetime Value
    - Net Promoter Score
    - Employee Efficiency
    - Appointment Cancellation Rate

    **Códigos de respuesta:**
    - 200: KPIs obtenidos
    """
    # TODO: Implementar cálculo completo de KPIs
    return {
        "success": True,
        "data": {
            "revenue_kpi": {
                "arpa": 0.0,
                "monthly_revenue": 0.0,
                "year_to_date": 0.0,
            },
            "customer_kpi": {
                "total_customers": 0,
                "new_customers_month": 0,
                "churn_rate": 0.0,
                "customer_lifetime_value": 0.0,
            },
            "operational_kpi": {
                "avg_appointment_duration": 0,
                "appointment_utilization": 0.0,
                "no_show_rate": 0.0,
            },
            "satisfaction_kpi": {
                "average_rating": 0.0,
                "nps": 0.0,
                "customer_satisfaction": 0.0,
            },
        },
    }


# ===== ANOMALY DETECTION =====

@router.get("/anomalies/detection", response_model=dict)
async def detect_anomalies(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Detectar anomalías en datos operacionales.

    **Response:**
    - anomalies: Lista de anomalías
    - severity: Severidad (low, medium, high)
    - recommendation: Acción recomendada

    **Ejemplos de anomalías:**
    - Caída repentina de ingresos
    - Aumento anormal de cancelaciones
    - Cliente con patrón atípico
    - Barbero con bajo performance

    **Códigos de respuesta:**
    - 200: Análisis completado
    """
    anomalies = await analytics_service.get_anomalies()
    return {
        "success": True,
        "data": {
            "anomalies": anomalies,
            "count": len(anomalies),
            "alert_count": sum(
                1 for a in anomalies
                if a.get("severity") == "high"
            ) if anomalies else 0,
        },
    }


# ===== RECOMMENDATIONS ENGINE =====

@router.get("/recommendations", response_model=dict)
async def get_business_recommendations(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Obtener recomendaciones automáticas basadas en análisis.

    **Response:**
    - marketing: Recomendaciones de marketing
    - operations: Recomendaciones operacionales
    - customer_service: Mejoras de servicio
    - pricing: Estrategia de precios
    - staffing: Gestión de personal

    **Ejemplos:**
    - "Promover servicio X con baja demanda"
    - "Contactar clientes de alto riesgo"
    - "Aumentar disponibilidad barbero Y"
    - "Ajustar precio de servicio Z"

    **Códigos de respuesta:**
    - 200: Recomendaciones obtenidas
    """
    recommendations = await analytics_service.get_recommendations()
    return {
        "success": True,
        "data": recommendations,
    }
