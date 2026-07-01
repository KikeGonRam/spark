"""
UNIDAD II – Preparación de los datos
SESIÓN 9: Tipos y conjuntos de datos en minería de datos

Conceptos demostrados con datos reales de UrbanBlade:
  - Concepto de minería de datos
  - Diagrama del proceso de minería de datos (KDD)
  - Tipos de datasets: entrenamiento, prueba, validación
  - Tipos de tareas de minería: clasificación, clustering, regresión, asociación
"""

import sys
import os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, count, avg, round as spark_round
from pyspark.ml.feature import VectorAssembler, StringIndexer
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
    .appName("UrbanBlade-MineriaDatos") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Carga de datos
client = MongoClient(mongo_uri)
db     = client[database]
services_map = {str(s["_id"]): s for s in db["services"].find({}, {"_id": 1, "nombre": 1, "precio": 1, "duracion_min": 1})}
barbers_map  = {str(b["_id"]): b for b in db["barbers"].find({}, {"_id": 1, "user_id": 1, "nombre": 1})}
users_map    = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}
apts         = list(db["appointments"].find({}, {"_id": 0, "service_id": 1, "barber_id": 1, "precio_cobrado": 1, "estado": 1, "fecha": 1}))
client.close()

records = []
for apt in apts:
    svc  = services_map.get(str(apt.get("service_id", "")), {})
    brb  = barbers_map.get(str(apt.get("barber_id", "")), {})
    uid  = str(brb.get("user_id", ""))
    barbero = brb.get("nombre") or users_map.get(uid, {}).get("name", "Sin nombre")
    precio_cobrado = apt.get("precio_cobrado")
    precio_base    = float(svc.get("precio") or 0)
    precio         = float(precio_cobrado) if precio_cobrado is not None else precio_base
    records.append({
        "servicio":    svc.get("nombre", "Desconocido"),
        "barbero":     barbero,
        "duracion_min": float(svc.get("duracion_min") or 30),
        "precio":      precio,
        "estado":      str(apt.get("estado", "")),
        "ingreso":     precio,
    })

df = spark.createDataFrame(pd.DataFrame(records))
df = df.dropna(subset=["precio", "duracion_min"])
total = df.count()

print("\n" + "="*60)
print("SESIÓN 9: MINERÍA DE DATOS")
print("="*60)

print("""
¿Qué es la Minería de Datos?
  Proceso de descubrir patrones, correlaciones, anomalías y tendencias
  útiles en grandes conjuntos de datos usando estadística, aprendizaje
  automático y sistemas de bases de datos.

  KDD: Knowledge Discovery in Databases
""")

# =============================================================================
# DIAGRAMA DEL PROCESO KDD (Knowledge Discovery in Databases)
# =============================================================================
print("="*60)
print("PROCESO KDD — Diagrama de Minería de Datos")
print("="*60)
print("""
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   FUENTES   │────►│  SELECCIÓN  │────►│  LIMPIEZA   │
  │  DE DATOS   │     │  DE DATOS   │     │  DE DATOS   │
  │─────────────│     │─────────────│     │─────────────│
  │ MongoDB     │     │appointments │     │ dropna      │
  │ barber_db   │     │ + services  │     │ fillna      │
  │ (raw BSON)  │     │ + barbers   │     │ casting     │
  └─────────────┘     └─────────────┘     └──────┬──────┘
                                                  │
  ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
  │CONOCIMIENTO │◄────│   MINERÍA   │◄────│TRANSFORMACIÓN│
  │  (Resultado)│     │ (Algoritmos)│     │  DE DATOS   │
  │─────────────│     │─────────────│     │─────────────│
  │ Clusters    │     │ KMeans      │     │ VectorAssemb│
  │ Predicciones│     │ RandomForest│     │ Normaliz.   │
  │ Patrones    │     │ PCA         │     │ Encoding    │
  └─────────────┘     └─────────────┘     └─────────────┘

  Aplicado a UrbanBlade:
  Fuente → appointments (283 citas reales)
  Limpieza → eliminación de nulos, casting
  Transformación → join con services+barbers+users, feature engineering
  Minería → KMeans, RandomForest, PCA, Regresión
  Conocimiento → segmentos de citas, predicción de cancelaciones
""")

# =============================================================================
# TIPOS DE TAREAS DE MINERÍA DE DATOS
# =============================================================================
print("="*60)
print("TIPOS DE TAREAS DE MINERÍA")
print("="*60)

# ── 1. CLASIFICACIÓN ─────────────────────────────────────────────────────────
print("\n1. CLASIFICACIÓN — Predecir una categoría (variable discreta)")
print("   Pregunta: ¿Esta cita será cancelada?")
print("   Label: cancelada=1, otro estado=0\n")

df_clasif = df.withColumn(
    "cancelada",
    when(col("estado") == "cancelada", 1).otherwise(0)
)
dist_label = df_clasif.groupBy("cancelada").count().orderBy("cancelada")
dist_label.show()

canceladas = df_clasif.filter(col("cancelada") == 1).count()
print(f"  Citas canceladas: {canceladas} ({round(canceladas/total*100, 1)}%)")
print(f"  Citas no canceladas: {total - canceladas} ({round((total-canceladas)/total*100, 1)}%)")

# ── 2. REGRESIÓN ─────────────────────────────────────────────────────────────
print("\n2. REGRESIÓN — Predecir un valor numérico (variable continua)")
print("   Pregunta: ¿Cuánto ingreso generará esta cita?")
print("   Variable objetivo: precio (continua)\n")

estadisticas = df.select(
    spark_round(avg("precio"), 2).alias("precio_promedio"),
    spark_round(avg("duracion_min"), 1).alias("duracion_promedio"),
).first()
print(f"  Precio promedio (objetivo): ${estadisticas['precio_promedio']}")
print(f"  Duración promedio (feature): {estadisticas['duracion_promedio']} min")

# ── 3. CLUSTERING ─────────────────────────────────────────────────────────────
print("\n3. CLUSTERING — Agrupar sin etiqueta (aprendizaje no supervisado)")
print("   Pregunta: ¿Qué grupos naturales existen entre las citas?")
print("   Sin variable objetivo — el algoritmo descubre los grupos\n")
print("   Features para clustering:")
df.select("duracion_min", "precio", "ingreso").describe().show()

# ── 4. ASOCIACIÓN ─────────────────────────────────────────────────────────────
print("\n4. REGLAS DE ASOCIACIÓN — Patrones frecuentes entre variables")
print("   Pregunta: ¿Qué servicios tienden a coincidir con ciertos barberos?")
print("   (Ejemplo: Market Basket Analysis)\n")

from pyspark.sql.functions import count as spark_count
asociacion = df.groupBy("servicio", "barbero") \
    .agg(spark_count("*").alias("frecuencia")) \
    .orderBy("frecuencia", ascending=False)
print("   Combinaciones servicio-barbero más frecuentes:")
asociacion.show(8)


# =============================================================================
# TIPOS DE CONJUNTOS DE DATOS EN MINERÍA
# =============================================================================
print("="*60)
print("TIPOS DE CONJUNTOS DE DATOS")
print("="*60)

# Preparar dataset vectorizado
df_ml = df_clasif.withColumn("ingreso", col("precio"))
assembler = VectorAssembler(
    inputCols=["duracion_min", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)
df_vec = assembler.transform(df_ml)

# ── Split 60/20/20 (Train / Validation / Test) ───────────────────────────────
train_val, test = df_vec.randomSplit([0.8, 0.2], seed=42)
train, val      = train_val.randomSplit([0.75, 0.25], seed=42)

print(f"""
Distribución del dataset UrbanBlade ({total} citas totales):

  ┌────────────────────────────────────────────────────────┐
  │              Dataset Total: {total} citas                      │
  ├─────────────────────────┬──────────────────────────────┤
  │    ENTRENAMIENTO 60%    │      EVALUACIÓN 40%          │
  │    {train.count()} registros          ├──────────────┬───────────────┤
  │                         │ VALIDACIÓN   │ TEST         │
  │  Para AJUSTAR el modelo │ {val.count()} reg.    │ {test.count()} reg.    │
  │                         │ 20% total    │ 20% total    │
  │                         │ Para ELEGIR  │ Para MEDIR   │
  │                         │ hiperparáms  │ rendimiento  │
  │                         │ del modelo   │ final        │
  └─────────────────────────┴──────────────┴───────────────┘
""")

print("Conjunto de ENTRENAMIENTO (60% — primeras 5 filas):")
train.select("servicio", "duracion_min", "precio", "cancelada").show(5)

print("Conjunto de VALIDACIÓN (20% — primeras 5 filas):")
val.select("servicio", "duracion_min", "precio", "cancelada").show(5)

print("Conjunto de TEST (20% — primeras 5 filas):")
test.select("servicio", "duracion_min", "precio", "cancelada").show(5)

# ── Cross-Validation ─────────────────────────────────────────────────────────
print("\nVALIDACIÓN CRUZADA (K-Fold Cross Validation, k=5):")
print(f"""
  Dataset: {total} citas → dividido en 5 folds de ~{total//5} registros cada uno

  Fold 1: [TEST]  [TRAIN] [TRAIN] [TRAIN] [TRAIN]
  Fold 2: [TRAIN] [TEST]  [TRAIN] [TRAIN] [TRAIN]
  Fold 3: [TRAIN] [TRAIN] [TEST]  [TRAIN] [TRAIN]
  Fold 4: [TRAIN] [TRAIN] [TRAIN] [TEST]  [TRAIN]
  Fold 5: [TRAIN] [TRAIN] [TRAIN] [TRAIN] [TEST]

  Resultado: promedio de las 5 métricas → estimación más robusta
  (Usado en 03_regresion_analytics.py con numFolds=3)
""")

print("="*60)
print("RESUMEN: TIPOS DE MINERÍA DE DATOS")
print("="*60)
print(f"""
  Tipo              | Supervisado | Variable objetivo | Script
  ─────────────────────────────────────────────────────────────
  Clasificación     | Sí          | cancelada (0/1)   | 05_bosque_aleatorio.py
  Regresión         | Sí          | precio (float)    | 03_regresion_analytics.py
  Clustering        | No          | ninguna           | 02_kmeans.py
  Reglas asociación | No          | ninguna           | 01_mapreduce.py (co-ocurrencia)
  Reducción dim.    | No          | ninguna           | 06_pca.py
  Red neuronal      | Sí          | clase ingreso     | 07_red_neural.py
""")

spark.stop()
print("Sesión finalizada correctamente.")
