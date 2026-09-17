"""Publicación segura de derivados analíticos en MongoDB."""

from datetime import datetime, timezone


def publish_insights_atomically(db, insights, target_collection="analytics_insights"):
    """Publica un snapshot completo sin dejar el destino vacío entre pasos."""
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
