"""Verifica que una credencial de ANALYTICS autentique contra Atlas y diga que privilegios tiene.

De solo lectura: usa connectionStatus con showPrivileges, no modifica nada.

Uso:
    # La contrasena sale del .env del proyecto
    python scripts/verificar_credencial_analytics.py

    # La contrasena sale de una variable de entorno (para no dejarla en el historial
    # ni en la linea de comandos al probar una rotacion)
    UB_ANALYTICS_PASSWORD='...' python scripts/verificar_credencial_analytics.py

Codigos de salida:
    0  autentico correctamente
    1  no autentico o faltan datos
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient

RAIZ = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=RAIZ / ".env")

ACCIONES_ESCRITURA = {
    "insert", "update", "remove", "createCollection", "dropCollection",
    "dropDatabase", "createIndex", "dropIndex", "renameCollection",
    "renameCollectionSameDB", "collMod", "convertToCapped", "anyAction",
}


def main() -> int:
    usuario = os.getenv("ANALYTICS_MONGO_USER")
    cluster = os.getenv("ANALYTICS_MONGO_CLUSTER")
    base = os.getenv("ANALYTICS_MONGO_DB")
    contrasena = os.getenv("UB_ANALYTICS_PASSWORD") or os.getenv("ANALYTICS_MONGO_PASSWORD")

    faltantes = [
        nombre for nombre, valor in {
            "ANALYTICS_MONGO_USER": usuario,
            "ANALYTICS_MONGO_CLUSTER": cluster,
            "ANALYTICS_MONGO_DB": base,
            "ANALYTICS_MONGO_PASSWORD": contrasena,
        }.items() if not valor
    ]
    if faltantes:
        print("Faltan datos: " + ", ".join(faltantes))
        return 1

    origen = "UB_ANALYTICS_PASSWORD" if os.getenv("UB_ANALYTICS_PASSWORD") else "ANALYTICS_MONGO_PASSWORD del .env"
    print(f"Probando la credencial {usuario} sobre {base} (contrasena tomada de {origen})")

    client = MongoClient(
        f"mongodb+srv://{usuario}:{quote_plus(contrasena)}@{cluster}",
        serverSelectionTimeoutMS=15000,
    )
    try:
        estado = client[base].command({"connectionStatus": 1, "showPrivileges": True})
        info = estado.get("authInfo", {})
        roles = [rol.get("role") for rol in info.get("authenticatedUserRoles", [])]
        acciones = set()
        recursos = set()
        for privilegio in info.get("authenticatedUserPrivileges", []):
            acciones |= set(privilegio.get("actions", []))
            recurso = privilegio.get("resource", {})
            recursos.add(recurso.get("db", "?"))

        escrituras = sorted(acciones & ACCIONES_ESCRITURA)
        print(f"  OK: autenticacion correcta")
        print(f"  roles: {roles}")
        print(f"  bases alcanzables: {sorted(recursos)}")
        print(f"  acciones de escritura: {escrituras or 'ninguna'}")
        if "changeOwnPassword" in acciones or "changeAnyPassword" in acciones:
            print("  AVISO: este usuario puede cambiar contrasenas")
        return 0
    except Exception as exc:
        print(f"  FALLO: {type(exc).__name__}: {exc}")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
