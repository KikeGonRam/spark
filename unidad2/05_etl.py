"""
UNIDAD II – Preparación de los datos
SESIÓN 10: Proceso ETL — Extracción, Transformación y Carga de datos

Implementa el proceso ETL completo sobre UrbanBlade usando PySpark:

  EXTRACT  → Extrae datos de 4 colecciones de MongoDB Atlas
  TRANSFORM → Limpia, une, calcula features y añade dimensiones
  LOAD      → Carga el resultado en formato Parquet y CSV
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, year, month, dayofmonth, dayofweek,
    date_format, trim, lower, round as spark_round,
    lit, count, avg, sum as spark_sum
)
from pyspark.sql.types import DoubleType, IntegerType, StringType
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd
import time

os.environ["PYSPARK_PYTHON"]        = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

user     = os.getenv("MONGO_USER")
password = quote_plus(os.getenv("MONGO_PASSWORD"))
cluster  = os.getenv("MONGO_CLUSTER")
database = os.getenv("MONGO_DB")
mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

spark = SparkSession.builder \
    .appName("UrbanBlade-ETL") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

print("\n" + "="*60)
print("PROCESO ETL — UrbanBlade Barber System")
print("="*60)
print("""
ETL = Extract → Transform → Load

  EXTRACT:   Leer datos desde las fuentes originales
  TRANSFORM: Limpiar, integrar, enriquecer y calcular
  LOAD:      Guardar el resultado en un destino analítico

Tipos de extracción:
  - Completa (Full): todos los registros cada vez
  - Incremental: sólo registros nuevos o modificados
  - Por streaming: en tiempo real (Spark Streaming)

  → En este ETL usamos: EXTRACCIÓN COMPLETA desde MongoDB Atlas

Tipos de transformación:
  - Limpieza: nulos, duplicados, tipos incorrectos
  - Integración: joins entre múltiples fuentes
  - Enriquecimiento: nuevas columnas calculadas
  - Agregación: resúmenes y métricas

Tipos de carga:
  - Truncate & Load: reemplazar todo (usada aquí)
  - Append: agregar sin borrar histórico
  - Upsert: actualizar si existe, insertar si no
  - Streaming: carga continua en tiempo real
""")

# =============================================================================
# FASE 1: EXTRACT
# =============================================================================
print("="*60)
print("FASE 1 — EXTRACT (Extracción)")
print("="*60)
t_start = time.time()

client = MongoClient(mongo_uri)
db     = client[database]

print("\nConectando a MongoDB Atlas...")
print(f"  Host:     {cluster}")
print(f"  Base de datos: {database}")

# Extracción completa de 4 colecciones
print("\nExtrayendo colecciones...")

t1 = time.time()
raw_appointments = list(db["appointments"].find({}, {
    "_id": 1, "service_id": 1, "barber_id": 1, "client_id": 1,
    "precio_cobrado": 1, "estado": 1, "fecha": 1,
    "hora_inicio": 1, "hora_fin": 1, "metodo_pago": 1, "notas": 1
}))
print(f"  appointments:  {len(raw_appointments):>5} documentos  ({round(time.time()-t1, 2)}s)")

t1 = time.time()
raw_services = list(db["services"].find({}, {
    "_id": 1, "nombre": 1, "precio": 1, "duracion_min": 1, "categoria": 1, "activo": 1
}))
print(f"  services:      {len(raw_services):>5} documentos  ({round(time.time()-t1, 2)}s)")

t1 = time.time()
raw_barbers = list(db["barbers"].find({}, {
    "_id": 1, "user_id": 1, "nombre": 1, "especialidades": 1, "activo": 1
}))
print(f"  barbers:       {len(raw_barbers):>5} documentos  ({round(time.time()-t1, 2)}s)")

t1 = time.time()
raw_users = list(db["users"].find({}, {
    "_id": 1, "name": 1, "email": 1
}))
print(f"  users:         {len(raw_users):>5} documentos  ({round(time.time()-t1, 2)}s)")

client.close()
t_extract = time.time() - t_start
print(f"\n  Total extraído: {len(raw_appointments) + len(raw_services) + len(raw_barbers) + len(raw_users)} documentos en {round(t_extract, 2)}s")


# =============================================================================
# FASE 2: TRANSFORM
# =============================================================================
print("\n" + "="*60)
print("FASE 2 — TRANSFORM (Transformación)")
print("="*60)
t_transform = time.time()

services_map = {str(s["_id"]): s for s in raw_services}
barbers_map  = {str(b["_id"]): b for b in raw_barbers}
users_map    = {str(u["_id"]): u for u in raw_users}

print("\n2.1 INTEGRACIÓN — Join de 4 colecciones en Python")
records = []
for apt in raw_appointments:
    svc  = services_map.get(str(apt.get("service_id", "")), {})
    brb  = barbers_map.get(str(apt.get("barber_id", "")), {})
    uid  = str(brb.get("user_id", ""))
    user = users_map.get(uid, {})

    precio_cobrado = apt.get("precio_cobrado")
    precio_base    = float(svc.get("precio") or 0)
    precio         = float(precio_cobrado) if precio_cobrado is not None else precio_base

    barbero_nombre = brb.get("nombre") or user.get("name", "Sin nombre")

    records.append({
        "cita_id":        str(apt["_id"]),
        "servicio":       svc.get("nombre", "Desconocido"),
        "categoria":      str(svc.get("categoria", "")),
        "barbero":        barbero_nombre,
        "duracion_min":   float(svc.get("duracion_min") or 30),
        "precio":         precio,
        "estado":         str(apt.get("estado", "")),
        "metodo_pago":    str(apt.get("metodo_pago") or "no_registrado"),
        "fecha":          str(apt.get("fecha", ""))[:10],
        "hora_inicio":    str(apt.get("hora_inicio", "")),
    })

df = spark.createDataFrame(pd.DataFrame(records))
print(f"  Registros integrados: {df.count()}")

print("\n2.2 LIMPIEZA")
df_clean = df \
    .dropna(subset=["precio", "duracion_min", "estado"]) \
    .withColumn("estado",       lower(trim(col("estado")))) \
    .withColumn("metodo_pago",  lower(trim(col("metodo_pago")))) \
    .withColumn("precio",       col("precio").cast(DoubleType())) \
    .withColumn("duracion_min", col("duracion_min").cast(DoubleType()))

df_clean = df_clean.dropDuplicates(["cita_id"])
print(f"  Registros después de limpieza: {df_clean.count()}")

print("\n2.3 ENRIQUECIMIENTO — Nuevas columnas calculadas")
df_enrich = df_clean \
    .withColumn("ingreso",       col("precio")) \
    .withColumn("alto_valor",    when(col("precio") > 500, 1).otherwise(0)) \
    .withColumn("cancelada",     when(col("estado") == "cancelada", 1).otherwise(0)) \
    .withColumn("pagado",        when(col("estado") == "completada", 1).otherwise(0)) \
    .withColumn("anio",          col("fecha").substr(1, 4).cast(IntegerType())) \
    .withColumn("mes",           col("fecha").substr(6, 2).cast(IntegerType())) \
    .withColumn("dia",           col("fecha").substr(9, 2).cast(IntegerType()))

print("  Columnas añadidas: ingreso, alto_valor, cancelada, pagado, anio, mes, dia")
print("  Schema del dataset transformado:")
df_enrich.printSchema()

print("\n  Muestra del dataset transformado:")
df_enrich.select(
    "servicio", "barbero", "duracion_min", "precio",
    "estado", "alto_valor", "cancelada", "mes"
).show(8)

t_transform_end = time.time()
print(f"\n  Tiempo de transformación: {round(t_transform_end - t_transform, 2)}s")


# =============================================================================
# FASE 3: LOAD
# =============================================================================
print("\n" + "="*60)
print("FASE 3 — LOAD (Carga)")
print("="*60)

output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "etl_output")
os.makedirs(output_dir, exist_ok=True)

# 3a. Guardar en formato PARQUET (eficiente para análisis)
parquet_path = os.path.join(output_dir, "citas_etl.parquet")
print(f"\n3.1 CARGA EN PARQUET (columnar, comprimido, óptimo para ML)")
print(f"  Ruta: {parquet_path}")
t_load = time.time()
df_enrich.write.mode("overwrite").parquet(parquet_path)
print(f"  ✓ Parquet guardado en {round(time.time()-t_load, 2)}s")

# 3b. Guardar en CSV (legible por humanos / Excel)
csv_path = os.path.join(output_dir, "citas_etl.csv")
print(f"\n3.2 CARGA EN CSV (legible, compatible con Excel / BI tools)")
print(f"  Ruta: {csv_path}")
t_load = time.time()
df_enrich.coalesce(1).write.mode("overwrite").option("header", True).csv(csv_path)
print(f"  ✓ CSV guardado en {round(time.time()-t_load, 2)}s")

# 3c. Verificar que se puede leer de vuelta
print("\n3.3 VERIFICACIÓN — Leer Parquet de vuelta:")
df_verificacion = spark.read.parquet(parquet_path)
print(f"  Registros cargados desde Parquet: {df_verificacion.count()}")
df_verificacion.select("servicio", "barbero", "precio", "estado", "mes").show(5)

# Tabla de métricas del ETL
print("\n3.4 TABLA RESUMEN DEL ETL (dataset cargado en DW):")
resumen_etl = df_enrich.groupBy("mes").agg(
    count("cita_id").alias("num_citas"),
    spark_sum("ingreso").alias("ingreso_total"),
    spark_sum("cancelada").alias("cancelaciones"),
    spark_round(avg("precio"), 2).alias("precio_promedio")
).orderBy("mes")
resumen_etl.show()

t_total = time.time() - t_start
print("\n" + "="*60)
print("RESUMEN DEL PROCESO ETL")
print("="*60)
print(f"""
  ┌─────────────┬────────────────────────────────────────────┐
  │ Fase        │ Resultado                                  │
  ├─────────────┼────────────────────────────────────────────┤
  │ EXTRACT     │ {len(raw_appointments)} citas + {len(raw_services)} servicios + {len(raw_barbers)} barberos + {len(raw_users)} usuarios     │
  │             │ Tiempo: {round(t_extract, 2)}s                                │
  ├─────────────┼────────────────────────────────────────────┤
  │ TRANSFORM   │ {df_enrich.count()} registros limpios y enriquecidos      │
  │             │ Joins: 4 colecciones unidas                │
  │             │ Nuevas columnas: ingreso, alto_valor,      │
  │             │   cancelada, pagado, anio, mes, dia        │
  ├─────────────┼────────────────────────────────────────────┤
  │ LOAD        │ ✓ Parquet: {parquet_path[:40]}... │
  │             │ ✓ CSV:     {csv_path[:40]}... │
  ├─────────────┼────────────────────────────────────────────┤
  │ TOTAL       │ Tiempo total ETL: {round(t_total, 2)}s                      │
  └─────────────┴────────────────────────────────────────────┘

Tipo de extracción usada: COMPLETA (Full Load)
  → Alternativa incremental: filtrar por fecha > última_ejecución

Formato de carga: PARQUET
  Ventajas: columnar, comprimido (3-10x menos espacio que CSV),
  lectura 10-100x más rápida en queries analíticas.
""")

spark.stop()
print("Proceso ETL completado correctamente.")
