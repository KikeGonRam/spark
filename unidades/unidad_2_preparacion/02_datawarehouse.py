"""
UNIDAD II – Preparación de los datos
SESIÓN 7: Modelado de Datawarehouse

Conceptos demostrados con datos reales de UrbanBlade:
  - Definición de un Data Warehouse
  - Ventajas
  - Modelo Estrella (Star Schema)
  - Modelo Copo de Nieve (Snowflake Schema)
"""

import sys
import os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, dayofmonth, dayofweek, quarter, date_format
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
    .appName("UrbanBlade-DataWarehouse") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# ──────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS DESDE MONGODB
# ──────────────────────────────────────────────────────────────────────────────
client = MongoClient(mongo_uri)
db     = client[database]

apts     = list(db["appointments"].find({}, {"_id": 1, "service_id": 1, "barber_id": 1, "precio_cobrado": 1, "estado": 1, "fecha": 1}))
services = list(db["services"].find({}, {"_id": 1, "nombre": 1, "precio": 1, "duracion_min": 1, "categoria": 1}))
barbers  = list(db["barbers"].find({}, {"_id": 1, "nombre": 1, "user_id": 1, "especialidades": 1}))
users    = list(db["users"].find({}, {"_id": 1, "name": 1, "email": 1}))
client.close()

services_map = {str(s["_id"]): s for s in services}
barbers_map  = {str(b["_id"]): b for b in barbers}
users_map    = {str(u["_id"]): u for u in users}

print("\n" + "="*60)
print("DATA WAREHOUSE — UrbanBlade Barber System")
print("="*60)
print("""
¿Qué es un Data Warehouse?
  Repositorio centralizado que integra datos de múltiples fuentes
  (MongoDB, servicios, pagos) en un modelo optimizado para ANÁLISIS
  y generación de reportes, no para operaciones transaccionales.

Ventajas:
  ✓ Consultas analíticas rápidas (datos ya integrados y limpios)
  ✓ Historia completa de los datos (no se sobreescriben)
  ✓ Una sola fuente de verdad para reportes
  ✓ Separación entre sistema operacional y analítico
""")


# =============================================================================
# MODELO ESTRELLA (Star Schema)
# Una tabla de HECHOS central rodeada de tablas DIMENSIÓN desnormalizadas
# =============================================================================
print("="*60)
print("MODELO ESTRELLA (Star Schema)")
print("="*60)
print("""
                    ┌─────────────┐
                    │  dim_fecha  │
                    │─────────────│
                    │ fecha_id PK │
                    │ año         │
                    │ mes         │
                    │ dia         │
                    │ trimestre   │
                    │ dia_semana  │
                    └──────┬──────┘
                           │
  ┌──────────────┐    ┌────▼──────────────┐    ┌──────────────────┐
  │ dim_servicio │    │   FACT_CITAS       │    │  dim_barbero     │
  │──────────────│    │──────────────────  │    │──────────────────│
  │ servicio_id  ├───►│ cita_id (PK)       │◄───┤ barbero_id (PK)  │
  │ nombre       │    │ fecha_id (FK)      │    │ nombre_completo  │
  │ categoria    │    │ servicio_id (FK)   │    │ especialidades   │
  │ precio_base  │    │ barbero_id (FK)    │    │ email            │
  │ duracion_min │    │ precio_cobrado     │    └──────────────────┘
  └──────────────┘    │ ingreso            │
                      │ estado             │
                      └────────────────────┘
""")

# ── Tabla de hechos ──────────────────────────────────────────────────────────
fact_records = []
for apt in apts:
    svc = services_map.get(str(apt.get("service_id", "")), {})
    brb = barbers_map.get(str(apt.get("barber_id", "")), {})
    uid = str(brb.get("user_id", ""))

    precio_cobrado = apt.get("precio_cobrado")
    precio_base    = float(svc.get("precio") or 0)
    precio         = float(precio_cobrado) if precio_cobrado is not None else precio_base

    fecha = str(apt.get("fecha", ""))[:10]

    fact_records.append({
        "cita_id":        str(apt["_id"]),
        "fecha_id":       fecha,
        "servicio_id":    str(apt.get("service_id", "")),
        "barbero_id":     str(apt.get("barber_id", "")),
        "precio_cobrado": precio,
        "ingreso":        precio,
        "estado":         str(apt.get("estado", "")),
    })

fact_citas = spark.createDataFrame(pd.DataFrame(fact_records))
fact_citas = fact_citas.withColumn("fecha_dt", col("fecha_id").cast("date"))

# ── Dimensión Fecha ──────────────────────────────────────────────────────────
dim_fecha = fact_citas.select("fecha_id", "fecha_dt") \
    .distinct() \
    .withColumn("anio",       year(col("fecha_dt"))) \
    .withColumn("mes",        month(col("fecha_dt"))) \
    .withColumn("dia",        dayofmonth(col("fecha_dt"))) \
    .withColumn("trimestre",  quarter(col("fecha_dt"))) \
    .withColumn("dia_semana", date_format(col("fecha_dt"), "EEEE")) \
    .drop("fecha_dt")

# ── Dimensión Servicio ───────────────────────────────────────────────────────
dim_servicio_records = [{
    "servicio_id":  str(s["_id"]),
    "nombre":       s.get("nombre", ""),
    "categoria":    str(s.get("categoria", "")),
    "precio_base":  float(s.get("precio") or 0),
    "duracion_min": int(s.get("duracion_min") or 30),
} for s in services]

dim_servicio = spark.createDataFrame(pd.DataFrame(dim_servicio_records))

# ── Dimensión Barbero (DESNORMALIZADA — incluye datos del usuario) ────────────
dim_barbero_records = []
for b in barbers:
    uid  = str(b.get("user_id", ""))
    user = users_map.get(uid, {})
    dim_barbero_records.append({
        "barbero_id":     str(b["_id"]),
        "nombre_completo": b.get("nombre") or user.get("name", "Sin nombre"),
        "especialidades": str(b.get("especialidades", "")),
        "email":          user.get("email", ""),
    })

dim_barbero = spark.createDataFrame(pd.DataFrame(dim_barbero_records))

# ── Mostrar las tablas del Modelo Estrella ───────────────────────────────────
print("FACT_CITAS (tabla de hechos):")
fact_citas.select("cita_id", "fecha_id", "servicio_id", "barbero_id", "precio_cobrado", "estado").show(5)
print(f"Total de hechos: {fact_citas.count()} citas\n")

print("DIM_FECHA:")
dim_fecha.orderBy("fecha_id").show(5)

print("DIM_SERVICIO:")
dim_servicio.show(5)

print("DIM_BARBERO:")
dim_barbero.show(5)

# ── Consulta analítica sobre el Modelo Estrella ──────────────────────────────
print("─"*60)
print("CONSULTA ANALÍTICA — Ingreso total por mes y servicio")
print("─"*60)

from pyspark.sql.functions import sum as spark_sum, count

star_query = fact_citas \
    .join(dim_fecha,    "fecha_id",    "left") \
    .join(dim_servicio, "servicio_id", "left") \
    .groupBy("mes", "nombre") \
    .agg(
        spark_sum("ingreso").alias("ingreso_total"),
        count("cita_id").alias("num_citas")
    ) \
    .orderBy("mes", "ingreso_total", ascending=[True, False])

star_query.show(12)


# =============================================================================
# MODELO COPO DE NIEVE (Snowflake Schema)
# Dimensiones normalizadas — dim_barbero se divide en dim_barbero + dim_usuario
# =============================================================================
print("="*60)
print("MODELO COPO DE NIEVE (Snowflake Schema)")
print("="*60)
print("""
Diferencia con Estrella: las dimensiones se normalizan
dividiendo en sub-tablas para eliminar redundancia.

                    ┌─────────────┐
                    │  dim_fecha  │
                    └──────┬──────┘
                           │
  ┌──────────────┐    ┌────▼──────────────┐    ┌──────────────────┐
  │ dim_servicio │    │   FACT_CITAS       │    │  dim_barbero     │
  │──────────────│    │──────────────────  │    │──────────────────│
  │ servicio_id  ├───►│ cita_id (PK)       │◄───┤ barbero_id (PK)  │
  │ nombre       │    │ fecha_id (FK)      │    │ user_id (FK) ────┼─┐
  │ categoria_id ├─┐  │ servicio_id (FK)   │    │ especialidades   │ │
  │ duracion_min │ │  │ barbero_id (FK)    │    └──────────────────┘ │
  └──────────────┘ │  │ precio_cobrado     │                         │
                   │  └────────────────────┘         ┌──────────────┴┐
  ┌────────────────▼┐                                 │  dim_usuario  │
  │ dim_categoria   │                                 │───────────────│
  │─────────────────│                                 │ user_id (PK)  │
  │ categoria_id PK │                                 │ name          │
  │ nombre_cat      │                                 │ email         │
  └─────────────────┘                                 └───────────────┘
""")

# ── dim_categoria (sub-dimensión de servicio) ────────────────────────────────
categorias = list({s.get("categoria", "Sin categoría") for s in services})
dim_categoria = spark.createDataFrame(
    pd.DataFrame([{"categoria_id": str(i), "nombre_cat": c} for i, c in enumerate(categorias)])
)

cat_to_id = {c: str(i) for i, c in enumerate(categorias)}

dim_servicio_snowflake_records = [{
    "servicio_id":  str(s["_id"]),
    "nombre":       s.get("nombre", ""),
    "categoria_id": cat_to_id.get(str(s.get("categoria", "")), "0"),
    "precio_base":  float(s.get("precio") or 0),
    "duracion_min": int(s.get("duracion_min") or 30),
} for s in services]
dim_servicio_snowflake = spark.createDataFrame(pd.DataFrame(dim_servicio_snowflake_records))

# ── dim_usuario (sub-dimensión de barbero) ───────────────────────────────────
dim_usuario = spark.createDataFrame(pd.DataFrame([{
    "user_id": str(u["_id"]),
    "name":    u.get("name", ""),
    "email":   u.get("email", ""),
} for u in users]))

dim_barbero_snowflake = spark.createDataFrame(pd.DataFrame([{
    "barbero_id":    str(b["_id"]),
    "user_id":       str(b.get("user_id", "")),
    "especialidades": str(b.get("especialidades", "")),
} for b in barbers]))

print("DIM_CATEGORIA (sub-dimensión normalizada):")
dim_categoria.show()

print("DIM_SERVICIO_SNOWFLAKE (con FK a categoria):")
dim_servicio_snowflake.show(5)

print("DIM_BARBERO_SNOWFLAKE (con FK a usuario):")
dim_barbero_snowflake.show(5)

print("DIM_USUARIO:")
dim_usuario.show(5)

# ── Comparación ──────────────────────────────────────────────────────────────
print("="*60)
print("COMPARACIÓN: Estrella vs Copo de Nieve")
print("="*60)
print("""
+--------------------+------------------------+------------------------+
| Aspecto            | Modelo Estrella         | Modelo Copo de Nieve   |
+--------------------+------------------------+------------------------+
| Tablas dimensión   | Pocas, desnormalizadas  | Más tablas, normalizadas|
| Complejidad SQL    | Simple (1 JOIN por dim) | Más JOINs necesarios   |
| Redundancia datos  | Alta                    | Baja                   |
| Velocidad consulta | Más rápido              | Más lento              |
| Espacio en disco   | Más                     | Menos                  |
| Uso recomendado    | Reportes rápidos,       | Datos maestros grandes,|
|                    | dashboards ejecutivos   | muchos servicios/barberos|
+--------------------+------------------------+------------------------+

Para UrbanBlade se recomienda: MODELO ESTRELLA
  Razón: dataset pequeño (~300 citas), consultas son simples,
  la velocidad de respuesta importa más que el espacio en disco.
""")

spark.stop()
print("Sesión finalizada correctamente.")
