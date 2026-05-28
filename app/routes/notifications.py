"""
Notifications Routes - Notificaciones del usuario
Endpoints: /api/notifications/*
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.models import User
from app.routes.dependencies import require_authenticated
from app.services.notification_service import NotificationTemplate

router = APIRouter()


async def get_db():
    from database.connection import MongoDBConnection
    return MongoDBConnection.get_db()


@router.get("/", response_model=list)
async def list_notifications(
    current_user: User = Depends(require_authenticated),
):
    """Lista las notificaciones del usuario autenticado."""
    try:
        db = await get_db()
        col = db["notifications"]
        cursor = col.find({"user_id": str(current_user.id)}).sort("created_at", -1).limit(50)
        notifications = []
        async for n in cursor:
            n["id"] = str(n.pop("_id"))
            notifications.append(n)
        return notifications
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}/read", response_model=dict)
async def mark_read(
    notification_id: str,
    current_user: User = Depends(require_authenticated),
):
    """Marcar una notificación como leída."""
    try:
        from bson import ObjectId
        db = await get_db()
        col = db["notifications"]
        result = await col.update_one(
            {"_id": ObjectId(notification_id), "user_id": str(current_user.id)},
            {"$set": {"read": True, "read_at": datetime.utcnow().isoformat()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")
        return {"success": True, "message": "Notificación marcada como leída"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/read-all", response_model=dict)
async def mark_all_read(
    current_user: User = Depends(require_authenticated),
):
    """Marcar todas las notificaciones como leídas."""
    try:
        db = await get_db()
        col = db["notifications"]
        await col.update_many(
            {"user_id": str(current_user.id), "read": {"$ne": True}},
            {"$set": {"read": True, "read_at": datetime.utcnow().isoformat()}}
        )
        return {"success": True, "message": "Todas las notificaciones marcadas como leídas"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=dict)
async def notifications_status():
    """Estado del sistema de notificaciones (público)."""
    return {
        "success": True,
        "data": {
            "email_enabled": True,
            "sms_enabled": True,
            "push_enabled": True,
            "in_app_enabled": True,
            "templates": [template.value for template in NotificationTemplate],
        },
    }
