"""Generación reproducible de datos sintéticos; nunca modifica el core."""

import argparse
import json
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import connect_mongo, load_environment, require_write_opt_in


SERVICES = {"Corte Clásico": 150, "Corte Fade": 200, "Barba": 100, "Corte + Barba": 250, "Tintura": 400}


def generate_records(count=2000, seed=42):
    if not 1 <= count <= 100000:
        raise ValueError("El conteo debe estar entre 1 y 100000.")
    rng = random.Random(seed)
    return [
        {
            "servicio": service,
            "barbero": rng.choice(["Sintético A", "Sintético B", "Sintético C"]),
            "cantidad": rng.randint(1, 3),
            "precio": SERVICES[service] + rng.randint(-20, 50),
            "estado": rng.choices(["completada", "cancelada", "pendiente"], weights=[70, 20, 10])[0],
            "synthetic": True,
        }
        for service in (rng.choice(list(SERVICES)) for _ in range(count))
    ]


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
