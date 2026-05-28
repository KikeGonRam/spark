"""
Barber Portfolio Routes - Portafolio del barbero
Endpoints: /api/barber/portfolio/*
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime

from app.models import User
from app.routes.dependencies import require_barber, require_authenticated

router = APIRouter()


async def get_db():
    from database.connection import MongoDBConnection
    return MongoDBConnection.get_db()


async def get_barber_for_user(current_user: User):
    from app.repositories import BarberRepository
    from database.connection import MongoDBConnection
    db = MongoDBConnection.get_db()
    barber = await BarberRepository(db).find_by_user_id(str(current_user.id))
    if not barber:
        raise HTTPException(status_code=404, detail="Perfil de barbero no encontrado")
    return barber


@router.get("", response_model=list)
async def get_portfolio(current_user: User = Depends(require_barber)):
    """Obtener trabajos del portafolio del barbero autenticado."""
    try:
        barber = await get_barber_for_user(current_user)
        db = await get_db()
        works_col = db["works"]
        cursor = works_col.find({"barber_id": str(barber.id)}).sort("created_at", -1)
        works = []
        async for w in cursor:
            w["id"] = str(w.pop("_id"))
            works.append(w)
        return works
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=dict, status_code=201)
async def create_work(
    work_data: dict,
    current_user: User = Depends(require_barber),
):
    """Crear un nuevo trabajo en el portafolio."""
    try:
        barber = await get_barber_for_user(current_user)
        db = await get_db()
        works_col = db["works"]

        doc = {
            "barber_id": str(barber.id),
            "title": work_data.get("title", ""),
            "description": work_data.get("description", ""),
            "service_type": work_data.get("service_type", "haircut"),
            "before_image_url": work_data.get("before_image_url") or work_data.get("before_image", ""),
            "after_image_url": work_data.get("after_image_url") or work_data.get("after_image", ""),
            "tags": work_data.get("tags", []),
            "reactions_count": 0,
            "comments_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = await works_col.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        doc.pop("_id", None)
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{work_id}", response_model=dict)
async def update_work(
    work_id: str,
    work_data: dict,
    current_user: User = Depends(require_barber),
):
    """Actualizar un trabajo del portafolio."""
    try:
        from bson import ObjectId
        barber = await get_barber_for_user(current_user)
        db = await get_db()
        works_col = db["works"]

        update_fields = {}
        for field in ["title", "description", "service_type", "before_image_url", "after_image_url"]:
            if field in work_data:
                update_fields[field] = work_data[field]

        result = await works_col.update_one(
            {"_id": ObjectId(work_id), "barber_id": str(barber.id)},
            {"$set": update_fields}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        return {"success": True, "message": "Trabajo actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{work_id}", response_model=dict)
async def delete_work(
    work_id: str,
    current_user: User = Depends(require_barber),
):
    """Eliminar un trabajo del portafolio."""
    try:
        from bson import ObjectId
        barber = await get_barber_for_user(current_user)
        db = await get_db()
        works_col = db["works"]

        result = await works_col.delete_one(
            {"_id": ObjectId(work_id), "barber_id": str(barber.id)}
        )
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        return {"success": True, "message": "Trabajo eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public/{barber_id}", response_model=dict)
async def get_public_portfolio(barber_id: str):
    """Ver portafolio público de un barbero."""
    try:
        db = await get_db()
        works_col = db["works"]
        cursor = works_col.find({"barber_id": barber_id}).sort("created_at", -1)
        works = []
        async for w in cursor:
            w["id"] = str(w.pop("_id"))
            works.append(w)
        return {"success": True, "data": {"works": works}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
