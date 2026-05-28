"""
Users Routes - Gestión de usuarios (admin)
Endpoints: /api/users/*
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.models import User
from app.exceptions import ResourceNotFoundError, ValidationError
from app.routes.dependencies import require_admin, require_authenticated

router = APIRouter()


async def get_user_repo():
    from app.repositories import UserRepository
    from database.connection import MongoDBConnection
    db = MongoDBConnection.get_db()
    return UserRepository(db)


@router.get("", response_model=dict)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    role: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    user_repo=Depends(get_user_repo),
):
    try:
        query = {}
        if role:
            query["role"] = role
        if query:
            users = await user_repo.find(query, skip=skip, limit=limit)
        else:
            users = await user_repo.find_all(skip=skip, limit=limit)
        users_list = []
        for u in users:
            ud = u.dict() if hasattr(u, 'dict') else dict(u)
            ud.pop("hashed_password", None)
            ud.pop("password", None)
            users_list.append(ud)
        return {"success": True, "data": {"users": users_list}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(require_authenticated)):
    ud = current_user.dict() if hasattr(current_user, 'dict') else dict(current_user)
    ud.pop("hashed_password", None)
    ud.pop("password", None)
    return {"success": True, "data": {"user": ud}}


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    user_repo=Depends(get_user_repo),
):
    try:
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        ud = user.dict() if hasattr(user, 'dict') else dict(user)
        ud.pop("hashed_password", None)
        ud.pop("password", None)
        return {"success": True, "data": {"user": ud}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=dict, status_code=201)
async def create_user(
    user_data: dict,
    current_user: User = Depends(require_admin),
):
    try:
        from app.services import AuthService
        from app.models import UserCreate, UserRole
        user_repo = await get_user_repo()
        auth_service = AuthService(user_repo)

        role_val = user_data.get("role", "client")
        try:
            role_enum = UserRole(role_val)
        except ValueError:
            role_enum = UserRole.CLIENT

        create_data = UserCreate(
            name=user_data.get("name", ""),
            email=user_data.get("email", ""),
            password=user_data.get("password", ""),
            phone=user_data.get("phone"),
            role=role_enum,
        )
        result = await auth_service.register(create_data, role=role_enum)
        ud = result["user"].dict() if hasattr(result["user"], 'dict') else dict(result["user"])
        ud.pop("hashed_password", None)
        return {"success": True, "message": "Usuario creado", "data": {"user": ud}}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: User = Depends(require_admin),
    user_repo=Depends(get_user_repo),
):
    try:
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        update_fields = {}
        for field in ["name", "phone", "role", "is_active"]:
            if field in user_data:
                update_fields[field] = user_data[field]

        if user_data.get("password"):
            from app.utils.security import PasswordHandler
            update_fields["hashed_password"] = PasswordHandler.hash_password(user_data["password"])

        updated = await user_repo.update_partial(user_id, update_fields)
        if updated:
            ud = updated.dict() if hasattr(updated, 'dict') else dict(updated)
            ud.pop("hashed_password", None)
        else:
            ud = {}
        return {"success": True, "message": "Usuario actualizado", "data": {"user": ud}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    user_repo=Depends(get_user_repo),
):
    try:
        if str(current_user.id) == user_id:
            raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
        deleted = await user_repo.delete(user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return {"success": True, "message": "Usuario eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
