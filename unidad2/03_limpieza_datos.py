"""
UNIDAD II – Preparación de los datos
SESIÓN 8: Técnicas de limpieza de datos

Demuestra técnicas de limpieza sobre datos reales de UrbanBlade:
  BÁSICAS:
    - Identificar y eliminar valores nulos (dropna / fillna)
    - Detectar y eliminar duplicados
    - Corrección de tipos de datos (casting)
    - Estandarización de strings (trim, lowercase)

  AVANZADAS:
    - Detección de outliers (método IQR)
    - Winsorización (limitar outliers sin eliminar filas)
    - Codificación de variables categóricas (StringIndexer)
    - Normalización numérica (MinMaxScaler)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, trim, lower, when, count, isnan, isnull,
    percentile_approx, lit, regexp_replace
)
from pyspark.ml.feature import StringIndexer, MinMaxScaler, VectorAssembler
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
import pandas as pd

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
    .appName("UrbanBlade-LimpiezaDatos") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Carga de datos crudos (SIN limpiar) para demostración
client = MongoClient(mongo_uri)
db     = client[database]

services_map = {str(s["_id"]): s for s in db["services"].find({}, {"_id": 1, "nombre": 1, "precio": 1, "duracion_min": 1})}
barbers_map  = {str(b["_id"]): b for b in db["barbers"].find({}, {"_id": 1, "user_id": 1, "nombre": 1})}
users_map    = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

raw_apts = list(db["appointments"].find({}, {
    "_id": 0, "service_id": 1, "barber_id": 1,
    "precio_cobrado": 1, "estado": 1, "fecha": 1, "notas": 1, "metodo_pago": 1
}))
client.close()

# Construir dataset crudo con nulos intencionales para demostración
raw_records = []
for apt in raw_apts:
    svc = services_map.get(str(apt.get("service_id", "")), {})
    brb = barbers_map.get(str(apt.get("barber_id", "")), {})
    uid = str(brb.get("user_id", ""))
    barbero = brb.get("nombre") or users_map.get(uid, {}).get("name", None)

    raw_records.append({
        "servicio":     svc.get("nombre", None),
        "barbero":      barbero,
        "precio":       apt.get("precio_cobrado"),   # puede ser None
        "precio_base":  float(svc.get("precio") or 0),
        "duracion_min": float(svc.get("duracion_min") or 0) if svc else None,
        "estado":       apt.get("estado", None),
        "metodo_pago":  apt.get("metodo_pago", None),
        "notas":        apt.get("notas", None),
    })

df_raw = spark.createDataFrame(pd.DataFrame(raw_records))
total_raw = df_raw.count()

print("\n" + "="*60)
print("SESIÓN 8: TÉCNICAS DE LIMPIEZA DE DATOS")
print(f"Dataset crudo: {total_raw} registros")
print("="*60)


# =============================================================================
# TÉCNICAS BÁSICAS
# =============================================================================
print("\n── TÉCNICAS BÁSICAS ──────────────────────────────────────")

# 1. Análisis de valores nulos
print("\n1. ANÁLISIS DE VALORES NULOS")
print("Conteo de nulos por columna:")
null_counts = df_raw.select([
    count(when(isnull(c), c)).alias(c)
    for c in ["servicio", "barbero", "precio", "duracion_min", "estado", "metodo_pago", "notas"]
])
null_counts.show()

# 2. fillna — rellenar nulos con valores por defecto
print("2. FILLNA — Rellenar nulos con valores por defecto")
df_fillna = df_raw.fillna({
    "precio":       0.0,
    "duracion_min": 30.0,
    "metodo_pago":  "no_registrado",
    "notas":        "",
    "servicio":     "Sin servicio",
    "barbero":      "Sin asignar",
    "estado":       "pendiente",
})
print(f"Nulos después de fillna:")
df_fillna.select([
    count(when(isnull(c), c)).alias(c)
    for c in ["precio", "duracion_min", "metodo_pago", "notas"]
]).show()

# 3. dropna — eliminar filas con nulos en columnas críticas
print("3. DROPNA — Eliminar filas con nulos en campos críticos")
df_dropna = df_raw.dropna(subset=["servicio", "estado"])
print(f"Registros antes de dropna: {total_raw}")
print(f"Registros después de dropna: {df_dropna.count()}")
print(f"Filas eliminadas: {total_raw - df_dropna.count()}")

# 4. Corrección de tipos (casting)
print("\n4. CASTING — Corrección de tipos de datos")
df_typed = df_fillna.select(
    col("servicio").cast("string"),
    col("barbero").cast("string"),
    col("precio").cast("double"),
    col("precio_base").cast("double"),
    col("duracion_min").cast("double"),
    col("estado").cast("string"),
    col("metodo_pago").cast("string"),
)
print("Schema después de casting correcto:")
df_typed.printSchema()

# 5. Estandarización de strings
print("5. ESTANDARIZACIÓN DE STRINGS — trim + lowercase")
df_std = df_typed \
    .withColumn("estado",      lower(trim(col("estado")))) \
    .withColumn("metodo_pago", lower(trim(col("metodo_pago")))) \
    .withColumn("servicio",    trim(col("servicio")))

print("Valores únicos de 'estado' después de estandarizar:")
df_std.select("estado").distinct().orderBy("estado").show()

# 6. Detectar y eliminar duplicados
print("6. DUPLICADOS")
total_dup = df_std.count()
df_dedup  = df_std.dropDuplicates(["servicio", "barbero", "precio", "estado"])
print(f"Registros antes: {total_dup}")
print(f"Registros después de dropDuplicates: {df_dedup.count()}")
print(f"Duplicados eliminados: {total_dup - df_dedup.count()}")


# =============================================================================
# TÉCNICAS AVANZADAS
# =============================================================================
print("\n── TÉCNICAS AVANZADAS ────────────────────────────────────")

# 7. Detección de outliers con IQR
print("\n7. DETECCIÓN DE OUTLIERS — Método IQR (rango intercuartílico)")
print("Se aplica sobre el campo 'precio':")

q1 = df_dedup.approxQuantile("precio", [0.25], 0.05)[0]
q3 = df_dedup.approxQuantile("precio", [0.75], 0.05)[0]
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

print(f"  Q1 (percentil 25): ${q1:,.2f}")
print(f"  Q3 (percentil 75): ${q3:,.2f}")
print(f"  IQR = Q3 - Q1:     ${iqr:,.2f}")
print(f"  Límite inferior:   ${lower_bound:,.2f}")
print(f"  Límite superior:   ${upper_bound:,.2f}")

outliers = df_dedup.filter((col("precio") < lower_bound) | (col("precio") > upper_bound))
print(f"\nOutliers detectados: {outliers.count()} registros")
if outliers.count() > 0:
    outliers.select("servicio", "precio", "estado").show(5)

df_sin_outliers = df_dedup.filter(
    (col("precio") >= lower_bound) & (col("precio") <= upper_bound)
)
print(f"Registros después de eliminar outliers: {df_sin_outliers.count()}")

# 8. Winsorización (alternativa a eliminar — limitar el valor)
print("\n8. WINSORIZACIÓN — Limitar outliers sin eliminar filas")
df_winsor = df_dedup.withColumn(
    "precio_limpio",
    when(col("precio") < lower_bound, lit(lower_bound))
    .when(col("precio") > upper_bound, lit(upper_bound))
    .otherwise(col("precio"))
)
print("Precio original vs precio limitado (winsorizado):")
df_winsor.select("precio", "precio_limpio") \
    .orderBy(col("precio").desc()) \
    .show(5)

# 9. Codificación de variables categóricas (StringIndexer)
print("\n9. CODIFICACIÓN CATEGÓRICA — StringIndexer")
print("Convierte 'estado' (string) en número para ML:")
indexer = StringIndexer(inputCol="estado", outputCol="estado_idx")
df_indexed = indexer.fit(df_winsor).transform(df_winsor)
df_indexed.select("estado", "estado_idx").distinct().orderBy("estado_idx").show()

# 10. Normalización (MinMaxScaler → rango [0, 1])
print("\n10. NORMALIZACIÓN — MinMaxScaler (precio al rango [0,1])")
assembler = VectorAssembler(inputCols=["precio_limpio"], outputCol="precio_vec", handleInvalid="skip")
df_vec    = assembler.transform(df_indexed)
scaler    = MinMaxScaler(inputCol="precio_vec", outputCol="precio_norm")
df_norm   = scaler.fit(df_vec).transform(df_vec)

from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col as scol
df_norm = df_norm.withColumn("precio_norm_val", vector_to_array(scol("precio_norm"))[0])
print("Precio original vs precio normalizado [0-1]:")
df_norm.select("precio_limpio", "precio_norm_val").orderBy("precio_limpio").show(8)


# =============================================================================
# RESUMEN
# =============================================================================
print("\n" + "="*60)
print("RESUMEN — TÉCNICAS DE LIMPIEZA APLICADAS")
print("="*60)
print(f"""
Dataset original:          {total_raw} registros
Después de fillna:         {df_fillna.count()} registros (nulos rellenados)
Después de dropDuplicates: {df_dedup.count()} registros
Sin outliers (IQR):        {df_sin_outliers.count()} registros

Técnicas básicas aplicadas:
  ✓ Análisis de nulos (isnull + count)
  ✓ fillna — rellenar nulos con defaults
  ✓ dropna — eliminar filas con nulos críticos
  ✓ Casting — corrección de tipos
  ✓ Estandarización de strings (trim, lower)
  ✓ Eliminación de duplicados (dropDuplicates)

Técnicas avanzadas aplicadas:
  ✓ Detección de outliers por IQR
  ✓ Winsorización (limitar en vez de eliminar)
  ✓ Codificación categórica (StringIndexer)
  ✓ Normalización MinMax [0, 1]
""")

spark.stop()
print("Sesión finalizada correctamente.")
