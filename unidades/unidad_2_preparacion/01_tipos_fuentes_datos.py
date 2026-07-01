"""
UNIDAD II – Preparación de los datos
SESIÓN 6: Tipos y fuentes de datos

Demuestra los 3 tipos de datos usando la base de datos real UrbanBlade (MongoDB Atlas):
  - Estructurados:     appointments como tabla con esquema definido
  - Semi-estructurados: documentos MongoDB con campos anidados/arrays
  - No estructurados:  campo 'notas' (texto libre) de appointments
"""

import sys
import os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd

os.environ["PYSPARK_PYTHON"]        = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

_p = Path(__file__).resolve()
env_path = next((c / ".env" for c in _p.parents if (c / ".env").exists()), _p.parent / ".env")
load_dotenv(dotenv_path=env_path)

user     = os.getenv("MONGO_USER")
password = quote_plus(os.getenv("MONGO_PASSWORD"))
cluster  = os.getenv("MONGO_CLUSTER")
database = os.getenv("MONGO_DB")
mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

spark = SparkSession.builder \
    .appName("UrbanBlade-TiposDatos") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

client = MongoClient(mongo_uri)
db     = client[database]

# =============================================================================
# TIPO 1: DATOS ESTRUCTURADOS
# Tabla con esquema fijo, tipos definidos y relaciones entre campos.
# Fuente: colección appointments (unida con services y barbers)
# =============================================================================
print("\n" + "="*60)
print("TIPO 1 — DATOS ESTRUCTURADOS")
print("Tabla de citas con esquema fijo y tipado")
print("="*60)

services_map = {str(s["_id"]): s for s in db["services"].find({}, {"_id": 1, "nombre": 1, "precio": 1, "duracion_min": 1})}
users_map    = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}
barbers_map  = {str(b["_id"]): b for b in db["barbers"].find({}, {"_id": 1, "user_id": 1, "nombre": 1})}

apts = list(db["appointments"].find({}, {
    "_id": 0, "service_id": 1, "barber_id": 1,
    "precio_cobrado": 1, "estado": 1, "fecha": 1
}))

records_estructurado = []
for apt in apts:
    svc = services_map.get(str(apt.get("service_id", "")), {})
    brb = barbers_map.get(str(apt.get("barber_id", "")), {})
    uid = str(brb.get("user_id", ""))
    nombre_barbero = brb.get("nombre") or users_map.get(uid, {}).get("name", "Sin nombre")

    precio_cobrado = apt.get("precio_cobrado")
    precio_base    = float(svc.get("precio") or 0)
    precio         = float(precio_cobrado) if precio_cobrado is not None else precio_base

    records_estructurado.append({
        "servicio":    svc.get("nombre", "Desconocido"),
        "barbero":     nombre_barbero,
        "duracion_min": int(svc.get("duracion_min") or 30),
        "precio":      precio,
        "estado":      str(apt.get("estado", "")),
        "fecha":       str(apt.get("fecha", ""))[:10],
    })

# Esquema explícito (ESTO es lo que hace "estructurado")
schema_estructurado = StructType([
    StructField("servicio",    StringType(),  True),
    StructField("barbero",     StringType(),  True),
    StructField("duracion_min", IntegerType(), True),
    StructField("precio",      DoubleType(),  True),
    StructField("estado",      StringType(),  True),
    StructField("fecha",       StringType(),  True),
])

df_estructurado = spark.createDataFrame(
    pd.DataFrame(records_estructurado), schema=schema_estructurado
)

print(f"\nFuente: MongoDB Atlas → barber_db.appointments + services + barbers")
print(f"Registros: {df_estructurado.count()}")
print("\nEsquema definido (StructType):")
df_estructurado.printSchema()
print("Muestra de datos estructurados:")
df_estructurado.show(5)

# Estadísticas descriptivas (solo posibles con datos estructurados)
print("Estadísticas descriptivas:")
df_estructurado.select("precio", "duracion_min").describe().show()


# =============================================================================
# TIPO 2: DATOS SEMI-ESTRUCTURADOS
# Documentos con campos variables, anidados o en formato JSON/BSON.
# Fuente: MongoDB devuelve documentos BSON (Binary JSON) — semi-estructurado por naturaleza.
# =============================================================================
print("\n" + "="*60)
print("TIPO 2 — DATOS SEMI-ESTRUCTURADOS")
print("Documentos MongoDB con campos variables y anidados")
print("="*60)

# Un documento de appointments tal como llega de MongoDB (raw, sin join)
raw_docs = list(db["appointments"].find({}, {
    "_id": 0, "service_id": 1, "barber_id": 1, "estado": 1,
    "notas": 1, "productos": 1, "precio_cobrado": 1, "metodo_pago": 1
}).limit(5))

print(f"\nFuente: documentos BSON crudos de appointments")
print("Los campos pueden estar ausentes, ser nulos o contener arrays:\n")
for i, doc in enumerate(raw_docs, 1):
    print(f"Documento {i}:")
    for key, val in doc.items():
        print(f"  {key}: {repr(val)}")
    print()

# Demostración: los mismos datos como JSON (semi-estructurado)
import json
from bson import ObjectId

def bson_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return str(obj)

print("Representación JSON (semi-estructurado) del documento 1:")
print(json.dumps({k: bson_to_str(v) for k, v in raw_docs[0].items()}, indent=2, ensure_ascii=False))

print("\nDiferencias vs datos estructurados:")
print("  - 'productos' puede ser null, [] o [{'nombre': ...}]")
print("  - 'notas' puede estar ausente o ser texto libre")
print("  - 'metodo_pago' puede ser null o string")


# =============================================================================
# TIPO 3: DATOS NO ESTRUCTURADOS
# Texto libre, sin formato fijo ni esquema.
# Fuente: campo 'notas' de appointments
# =============================================================================
print("\n" + "="*60)
print("TIPO 3 — DATOS NO ESTRUCTURADOS")
print("Texto libre del campo 'notas' de las citas")
print("="*60)

notas_docs = list(db["appointments"].find(
    {"notas": {"$nin": [None, ""]}},
    {"_id": 0, "notas": 1, "estado": 1}
).limit(10))

if notas_docs:
    notas_df = spark.createDataFrame(
        [{"nota": d.get("notas", ""), "estado": d.get("estado", "")} for d in notas_docs]
    )
    print(f"\nFuente: campo 'notas' (texto libre) de appointments")
    print(f"Citas con notas: {len(notas_docs)}")
    print("\nEjemplos de texto libre (no estructurado):")
    notas_df.show(10, truncate=False)

    print("Características del dato no estructurado:")
    print("  - Longitud variable (0 a N palabras)")
    print("  - Sin esquema ni tipos fijos")
    print("  - Requiere NLP para extraer información")
    print("  - No se puede ordenar ni agregar directamente")
else:
    print("\nNo hay notas en la base de datos actual.")
    print("Ejemplo conceptual de datos no estructurados:")
    ejemplos = [
        "Cliente solicitó corte más corto de lo habitual",
        "Alérgico a cierto tinte, usar productos naturales",
        "Prefiere música tranquila durante el servicio",
    ]
    for e in ejemplos:
        print(f"  → {e}")

client.close()

# =============================================================================
# RESUMEN COMPARATIVO
# =============================================================================
print("\n" + "="*60)
print("RESUMEN: TIPOS DE DATOS")
print("="*60)
print("""
+------------------+-------------------+------------------------+------------------+
| Tipo             | Fuente UrbanBlade | Formato                | Procesamiento    |
+------------------+-------------------+------------------------+------------------+
| Estructurado     | appointments      | Tabla con schema fijo  | SQL / Spark DF   |
|                  | + services        | (StructType)           | directo          |
+------------------+-------------------+------------------------+------------------+
| Semi-estructurado| MongoDB BSON docs | JSON / BSON con campos | Parsing + mapeo  |
|                  | (raw documents)   | opcionales y anidados  | manual           |
+------------------+-------------------+------------------------+------------------+
| No estructurado  | appointments.notas| Texto libre            | NLP / expresiones|
|                  |                   | sin esquema            | regulares        |
+------------------+-------------------+------------------------+------------------+
""")

spark.stop()
print("Sesión finalizada correctamente.")
