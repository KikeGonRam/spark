"""
Logs Routes - Acceso a logs de la aplicación
Endpoints: /api/logs/*
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Query

from app.config import settings

router = APIRouter()


@router.get("/", response_model=dict)
async def get_log_tail(lines: int = Query(100, ge=1, le=500)):
    log_path = Path(settings.LOG_FILE)
    if not log_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log file not found")

    content = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return {
        "success": True,
        "data": {
            "file": str(log_path),
            "lines": content[-lines:],
        },
    }

