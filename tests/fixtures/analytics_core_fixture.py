"""Fixture sintético para validar el exportador completo sin datos reales."""

import os
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pymongo import MongoClient


def main():
    uri = os.environ["CORE_E2E_URI"]
    database = os.environ["CORE_E2E_DB"]
    action = os.getenv("CORE_E2E_ACTION", "create")
    if not database.endswith("_e2e"):
        raise RuntimeError("La base temporal debe terminar en _e2e")

    client = MongoClient(uri)
    if action == "drop":
        client.drop_database(database)
        client.close()
        return

    client.drop_database(database)
    db = client[database]
    services = [
        {"_id": ObjectId(), "nombre": "Corte", "categoria": "corte", "precio": 250.0, "duracion_min": 45},
        {"_id": ObjectId(), "nombre": "Barba", "categoria": "barba", "precio": 180.0, "duracion_min": 30},
        {"_id": ObjectId(), "nombre": "Combo", "categoria": "combo", "precio": 380.0, "duracion_min": 60},
    ]
    barber_users = [{"_id": ObjectId(), "name": f"Barbero {i}", "email": f"barbero{i}@e2e.test"} for i in range(3)]
    barbers = [{"_id": ObjectId(), "user_id": user["_id"], "comision_pct": 40} for user in barber_users]
    client_users = [{"_id": ObjectId(), "name": f"Cliente {i}", "email": f"cliente{i}@e2e.test"} for i in range(24)]
    clients = [{
        "_id": ObjectId(), "user_id": user["_id"], "nivel": ["nuevo", "regular", "vip"][i % 3],
        "puntos": i * 10, "total_citas": 1 + i % 8,
        "fecha_nacimiento": datetime(1985 + i % 15, 1 + i % 12, 1 + i % 27, tzinfo=timezone.utc),
    } for i, user in enumerate(client_users)]
    now = datetime.now(timezone.utc)
    states = ["completada", "completada", "confirmada", "cancelada", "no_asistio", "pendiente"]
    appointments = []
    for i in range(96):
        service = services[i % len(services)]
        appointments.append({
            "_id": ObjectId(), "client_id": clients[i % len(clients)]["_id"],
            "barber_id": barbers[i % len(barbers)]["_id"], "service_id": service["_id"],
            "precio_cobrado": service["precio"] + (i % 4) * 10, "estado": states[i % len(states)],
            "fecha": now - timedelta(days=i * 3), "hora_inicio": f"{9 + i % 9:02d}:00",
            "metodo_pago": ["efectivo", "tarjeta", "transferencia"][i % 3], "deleted_at": None,
        })

    db.services.insert_many(services)
    db.users.insert_many(barber_users + client_users)
    db.barbers.insert_many(barbers)
    db.clients.insert_many(clients)
    db.appointments.insert_many(appointments)
    client.close()


if __name__ == "__main__":
    main()
