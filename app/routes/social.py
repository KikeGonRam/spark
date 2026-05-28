"""
Social Routes - Portfolio, likes, comments and saved works
Endpoints: /api/social/*
"""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/feed", response_model=dict)
async def get_social_feed(limit: int = Query(20, ge=1, le=100)):
    return {
        "success": True,
        "data": {
            "items": [],
            "count": 0,
            "limit": limit,
        },
    }


@router.get("/barbers/{barber_id}/portfolio", response_model=dict)
async def get_barber_portfolio(barber_id: str):
    return {
        "success": True,
        "data": {
            "barber_id": barber_id,
            "works": [],
        },
    }


@router.post("/works/{work_id}/react", response_model=dict)
async def react_to_work(work_id: str):
    return {"success": True, "message": "Reacción registrada", "data": {"work_id": work_id}}


@router.post("/works/{work_id}/comment", response_model=dict)
async def comment_on_work(work_id: str):
    return {"success": True, "message": "Comentario registrado", "data": {"work_id": work_id}}


@router.post("/works/{work_id}/save", response_model=dict)
async def save_work(work_id: str):
    return {"success": True, "message": "Trabajo guardado", "data": {"work_id": work_id}}

