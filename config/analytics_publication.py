"""Publicación segura de derivados analíticos en MongoDB."""

from datetime import datetime, timezone
import os


def publish_insights_atomically(db, insights, target_collection="analytics_insights"):
    """Publica un snapshot completo sin dejar el destino vacío entre pasos."""
    if target_collection != "analytics_insights":
        raise ValueError("El publicador solo admite analytics_insights.")
    if not isinstance(db.name, str) or db.name in {
        os.getenv("MONGO_DB", "barber_db"), "admin", "config", "local"
    }:
        raise ValueError("El destino debe ser una base de derivados separada del core.")
    if not insights:
        raise ValueError("Un snapshot vacío no sustituye los insights publicados.")
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    temporary_collection = f"{target_collection}__{suffix}"

    try:
        db.create_collection(temporary_collection)
        if insights:
            db[temporary_collection].insert_many(insights, ordered=True)
        db[temporary_collection].create_index([("roles", 1), ("generado_en", -1)])
        db[temporary_collection].create_index("barbero_user_id")
        db[temporary_collection].create_index("barbero_perfil_id")
        db[temporary_collection].rename(target_collection, dropTarget=True)
    except Exception:
        db.drop_collection(temporary_collection)
        raise

    return len(insights)
