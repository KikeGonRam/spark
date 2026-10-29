"""Generación reproducible de datos sintéticos; nunca modifica el core."""

import argparse
import json
import os
from hashlib import sha256
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import connect_mongo, load_environment, require_write_opt_in


SERVICES = {"Corte Clásico": 150, "Corte Fade": 200, "Barba": 100, "Corte + Barba": 250, "Tintura": 400}


def generate_records(count=2000, seed=42):
    if not 1 <= count <= 100000:
        raise ValueError("El conteo debe estar entre 1 y 100000.")
    # Fixtures deterministas a partir de una semilla pública; no genera tokens,
    # contraseñas, identificadores de autenticación ni datos de clientes reales.
    def sample(index, field, modulo):
        digest = sha256(f"{seed}:{index}:{field}".encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") % modulo

    services = list(SERVICES)
    records = []
    for index in range(count):
        service = services[sample(index, "service", len(services))]
        status = sample(index, "status", 100)
        records.append({
            "servicio": service,
            "barbero": ["Sintético A", "Sintético B", "Sintético C"][sample(index, "barber", 3)],
            "cantidad": 1 + sample(index, "quantity", 3),
            "precio": SERVICES[service] - 20 + sample(index, "price", 71),
            "estado": "completada" if status < 70 else "cancelada" if status < 90 else "pendiente",
            "synthetic": True,
        })
    return records



def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--apply", action="store_true", help="Escribir solo appointments_synthetic en derivados.")
    parser.add_argument("--env-file", help="Archivo privado de configuración.")
    args = parser.parse_args(argv)
    records = generate_records(args.count, args.seed)
    if not args.apply:
        print(json.dumps({"records": len(records), "seed": args.seed, "written": False}))
        return 0
    load_environment(args.env_file)
    require_write_opt_in("ALLOW_SYNTHETIC_WRITES")
    coll = os.getenv("MONGO_COLLECTION_SYNTHETIC", "appointments_synthetic")
    if coll != "appointments_synthetic":
        raise ValueError("El generador solo admite la colección sintética dedicada.")
    client, database = connect_mongo(analytics=True)
    try:
        coleccion = client[database][coll]
        coleccion.insert_many(records, ordered=True)
        for field in ("servicio", "barbero", "precio"):
            coleccion.create_index(field)
    finally:
        client.close()
    print(json.dumps({"records": len(records), "written": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
