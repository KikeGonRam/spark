"""
Predictions Routes - Forecasts and operational insights
Endpoints: /api/predictions/*
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/income/{days}", response_model=dict)
async def income_forecast(days: int):
    return {
        "success": True,
        "data": {
            "days": days,
            "forecast": [],
        },
    }


@router.get("/appointments/{days}", response_model=dict)
async def appointment_forecast(days: int):
    return {
        "success": True,
        "data": {
            "days": days,
            "forecast": [],
        },
    }


@router.get("/insights", response_model=dict)
async def insights():
    return {
        "success": True,
        "data": {
            "insights": [],
        },
    }


@router.get("/peak-hours", response_model=dict)
async def peak_hours():
    # Example shape expected by frontend
    hours = [{"hour": h, "count": 0} for h in range(6, 22)]
    busiest = max(hours, key=lambda x: x['count'])['hour'] if hours else None
    return {
        "success": True,
        "data": {
            "hours": hours,
            "busiest_hour": busiest,
        },
    }


@router.get("/services", response_model=dict)
async def predicted_services():
    # Return top_services array expected by frontend
    top = [{"name": f"Servicio {i+1}", "predicted_count": 0} for i in range(8)]
    return {
        "success": True,
        "data": {
            "top_services": top,
        },
    }
