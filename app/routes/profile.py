"""
Profile Routes - Perfil del usuario autenticado
Endpoints: /api/profile/*
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User
from app.routes.dependencies import require_authenticated
from app.exceptions import UnauthorizedError

router = APIRouter()


async def get_user_repo():
    from app.repositories import UserRepository
    from database.connection import MongoDBConnection
    db = MongoDBConnection.get_db()
    return UserRepository(db)


@router.get("", response_model=dict)
async def get_profile(current_user: User = Depends(require_authenticated)):
    """Obtener perfil del usuario autenticado."""
    ud = current_user.dict() if hasattr(current_user, 'dict') else dict(current_user)
    ud.pop("hashed_password", None)
    ud.pop("password", None)

    # Attach barber or client subprofile if exists
    try:
        from app.repositories import BarberRepository, ClientRepository
        from database.connection import MongoDBConnection
        db = MongoDBConnection.get_db()
        role = str(getattr(current_user, 'role', '') or '').lower()
        if 'barber' in role:
            barber = await BarberRepository(db).find_by_user_id(str(current_user.id))
            if barber:
                ud["barber"] = barber.dict() if hasattr(barber, 'dict') else dict(barber)
        elif 'client' in role:
            client = await ClientRepository(db).find_one({"user_id": str(current_user.id)})
            if client:
                cd = client.dict() if hasattr(client, 'dict') else dict(client)
                ud["client"] = cd
    except Exception:
        pass

    return {"success": True, "data": ud}


@router.put("", response_model=dict)
async def update_profile(
    profile_data: dict,
    current_user: User = Depends(require_authenticated),
    user_repo=Depends(get_user_repo),
):
    """Actualizar perfil del usuario autenticado."""
    try:
        update_fields = {}
        for field in ["name", "phone", "avatar"]:
            if field in profile_data:
                update_fields[field] = profile_data[field]

        if update_fields:
            await user_repo.update_partial(str(current_user.id), update_fields)

        # Update barber/client subprofile
        try:
            from app.repositories import BarberRepository, ClientRepository
            from database.connection import MongoDBConnection
            db = MongoDBConnection.get_db()
            role = str(getattr(current_user, 'role', '') or '').lower()

            if 'barber' in role:
                barber_fields = {}
                for field in ["bio", "specialization", "avatar"]:
                    if field in profile_data:
                        barber_fields[field] = profile_data[field]
                if barber_fields:
                    barber = await BarberRepository(db).find_by_user_id(str(current_user.id))
                    if barber:
                        await BarberRepository(db).update_partial(str(barber.id), barber_fields)

            elif 'client' in role:
                client_fields = {}
                for field in ["phone", "address", "city", "postal_code"]:
                    if field in profile_data:
                        client_fields[field] = profile_data[field]
                if client_fields:
                    from app.repositories.client import ClientRepository as CR
                    client = await CR(db).find_one({"user_id": str(current_user.id)})
                    if client:
                        cid = str(getattr(client, 'id', None) or client.get('id') or client.get('_id', ''))
                        if cid:
                            await CR(db).update_partial(cid, client_fields)
        except Exception:
            pass

        return {"success": True, "message": "Perfil actualizado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/password", response_model=dict)
async def change_password(
    password_data: dict,
    current_user: User = Depends(require_authenticated),
    user_repo=Depends(get_user_repo),
):
    """Cambiar contraseña del usuario autenticado."""
    try:
        from app.utils.security import PasswordHandler
        current_password = password_data.get("current_password", "")
        new_password = password_data.get("new_password", "")

        if not new_password or len(new_password) < 6:
            raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")

        stored_hash = getattr(current_user, 'hashed_password', None) or getattr(current_user, 'password', '')
        if stored_hash and not PasswordHandler.verify_password(current_password, stored_hash):
            raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")

        new_hash = PasswordHandler.hash_password(new_password)
        await user_repo.update_partial(str(current_user.id), {"hashed_password": new_hash})
        return {"success": True, "message": "Contraseña actualizada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("", response_model=dict)
async def delete_account(
    current_user: User = Depends(require_authenticated),
    user_repo=Depends(get_user_repo),
):
    """Eliminar cuenta del usuario autenticado."""
    try:
        await user_repo.delete(str(current_user.id))
        return {"success": True, "message": "Cuenta eliminada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
