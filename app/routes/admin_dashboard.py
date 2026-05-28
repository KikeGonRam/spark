"""
Admin Dashboard Routes - Estadísticas avanzadas para admin
Endpoints: /api/admin/dashboard/*
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models import User
from app.routes.dependencies import require_admin

router = APIRouter()


async def get_db():
    from database.connection import MongoDBConnection
    return MongoDBConnection.get_db()


@router.get("/stats", response_model=dict)
async def get_admin_stats(current_user: User = Depends(require_admin)):
    """Estadísticas globales para el dashboard del admin."""
    try:
        from datetime import datetime, date
        db = await get_db()

        today = date.today().isoformat()

        # Count collections
        total_clients = await db["clients"].count_documents({})
        total_barbers = await db["barbers"].count_documents({})
        active_barbers = await db["barbers"].count_documents({"is_available": True})

        # Today's appointments
        today_apps = await db["appointments"].count_documents({"appointment_date": today})
        today_completed = await db["appointments"].count_documents({"appointment_date": today, "status": "completed"})

        # Week appointments
        from datetime import timedelta
        week_start = (date.today() - timedelta(days=7)).isoformat()
        week_apps = await db["appointments"].count_documents({"appointment_date": {"$gte": week_start}})

        # Revenue today
        today_revenue = 0.0
        async for p in db["payments"].find({"status": "completed", "created_at": {"$regex": f"^{today}"}}):
            today_revenue += float(p.get("amount", 0))

        # Revenue month
        month_start = date.today().replace(day=1).isoformat()
        month_revenue = 0.0
        async for p in db["payments"].find({"status": "completed", "created_at": {"$regex": f"^{date.today().strftime('%Y-%m')}"}}):
            month_revenue += float(p.get("amount", 0))

        # Low stock products
        low_stock_count = await db["products"].count_documents(
            {"$expr": {"$lte": ["$quantity", "$minimum_quantity"]}}
        )

        # Occupancy rate
        occupancy_rate = round((today_completed / today_apps * 100) if today_apps > 0 else 0, 1)

        return {
            "success": True,
            "data": {
                "total_clients": total_clients,
                "total_barbers": total_barbers,
                "active_barbers": active_barbers,
                "today_appointments": today_apps,
                "today_completed": today_completed,
                "today_revenue": round(today_revenue, 2),
                "week_appointments": week_apps,
                "month_revenue": round(month_revenue, 2),
                "low_stock_count": low_stock_count,
                "occupancy_rate": occupancy_rate,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=dict)
async def get_admin_alerts(current_user: User = Depends(require_admin)):
    """Alertas del sistema para el admin."""
    try:
        db = await get_db()
        alerts = []

        # Low stock alerts
        async for p in db["products"].find({"$expr": {"$lte": ["$quantity", "$minimum_quantity"]}}):
            alerts.append({
                "type": "low_stock",
                "title": f"Stock bajo: {p.get('name', 'Producto')}",
                "message": f"Quedan {p.get('quantity', 0)} {p.get('unit', 'unidades')} (mínimo: {p.get('minimum_quantity', 5)})",
                "severity": "warning",
            })

        # Pending appointments
        from datetime import date
        today = date.today().isoformat()
        pending_count = await db["appointments"].count_documents({"appointment_date": today, "status": "pending"})
        if pending_count > 0:
            alerts.append({
                "type": "pending_appointments",
                "title": f"{pending_count} citas pendientes hoy",
                "message": "Hay citas que aún no han sido confirmadas",
                "severity": "info",
            })

        return {"success": True, "data": {"alerts": alerts}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
