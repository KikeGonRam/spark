"""
UNIDAD III — Script 09: Predicción de Abandono de Clientes (Churn)

Identifica clientes que probablemente dejarán de asistir analizando:
  - dias_sin_cita:        días desde su última visita
  - frecuencia_mensual:   visitas por mes
  - tasa_cancelacion:     porcentaje de citas canceladas
  - gasto_promedio:       ticket promedio del cliente
  - tendencia_gasto:      ¿está gastando más o menos que antes?

Modelo: Random Forest Classifier
Label:  en_riesgo = 1 si dias_sin_cita > umbral o tasa_cancelacion alta
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, max as spark_max, min as spark_min,
    when, round as spark_round, datediff, to_date, lit, months_between
)
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
from datetime import date
import pandas as pd

os.environ["PYSPARK_PYTHON"]        = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

mongo_uri = (f"mongodb+srv://{os.getenv('MONGO_USER')}:"
             f"{quote_plus(os.getenv('MONGO_PASSWORD'))}@"
             f"{os.getenv('MONGO_CLUSTER')}")
db_name = os.getenv("MONGO_DB")

spark = SparkSession.builder \
    .appName("UrbanBlade-PrediccionAbandono") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

print("\n" + "="*60)
print("PREDICCIÓN DE ABANDONO DE CLIENTES — UrbanBlade")
print("="*60)
print("""
Churn = cliente que probablemente dejará de asistir.

Variables predictoras:
  - Tiempo sin cita (recencia)
  - Frecuencia de visitas (frequencia)
  - Gasto promedio por cita (valor monetario)
  - Tasa de cancelaciones (comportamiento)

Modelo: Random Forest Classifier
""")

# ── EXTRACCIÓN ─────────────────────────────────────────────────────────────────
mc = MongoClient(mongo_uri)
db = mc[db_name]

users_map    = {str(u["_id"]): u for u in db["users"].find(
    {}, {"_id": 1, "name": 1, "email": 1})}
services_map = {str(s["_id"]): s for s in db["services"].find(
    {}, {"_id": 1, "precio": 1})}
raw_apts     = list(db["appointments"].find({}, {
    "_id": 0, "client_id": 1, "service_id": 1,
    "precio_cobrado": 1, "estado": 1, "fecha": 1
}))
mc.close()

today_str = str(date.today())
records   = []
for apt in raw_apts:
    cid = str(apt.get("client_id", ""))
    if not cid or cid in ("None", ""):
        continue
    svc   = services_map.get(str(apt.get("service_id", "")), {})
    pc    = apt.get("precio_cobrado")
    precio = float(pc) if pc is not None else float(svc.get("precio") or 0)
    records.append({
        "client_id": cid,
        "nombre":    users_map.get(cid, {}).get("name", "Cliente"),
        "precio":    precio,
        "estado":    str(apt.get("estado", "")),
        "fecha":     str(apt.get("fecha", ""))[:10],
    })

df_citas = spark.createDataFrame(pd.DataFrame(records))
df_citas = (df_citas
    .withColumn("fecha_dt",        to_date(col("fecha"), "yyyy-MM-dd"))
    .withColumn("hoy",             to_date(lit(today_str), "yyyy-MM-dd"))
    .withColumn("dias_desde_cita", datediff(col("hoy"), col("fecha_dt"))))

# ── FEATURE ENGINEERING POR CLIENTE ───────────────────────────────────────────
print("="*60)
print("FEATURE ENGINEERING — Métricas por cliente")
print("="*60)

df_stats = df_citas.groupBy("client_id", "nombre").agg(
    count("*").alias("total_citas"),
    spark_round(avg("precio"), 2).alias("gasto_promedio"),
    spark_round(spark_sum("precio"), 2).alias("gasto_total"),
    spark_round(
        (count(when(col("estado") == "cancelada", True)) / count("*")) * 100, 1
    ).alias("tasa_cancelacion_pct"),
    spark_round(
        spark_max(col("dias_desde_cita").cast("double")), 0
    ).alias("dias_sin_cita"),
    spark_round(
        spark_min(col("dias_desde_cita").cast("double")), 0
    ).alias("dias_desde_ultima_cita"),
)

# Frecuencia mensual = total_citas / meses_activo (donde meses = rango de fechas / 30)
df_rango = df_citas.groupBy("client_id").agg(
    spark_round(
        (spark_max(col("dias_desde_cita").cast("double")) -
         spark_min(col("dias_desde_cita").cast("double"))) / 30.0, 2
    ).alias("meses_activo")
)
df_clientes = df_stats.join(df_rango, "client_id", "left")
df_clientes = df_clientes.withColumn(
    "frecuencia_mensual",
    spark_round(
        col("total_citas") / when(col("meses_activo") < 1, lit(1.0)).otherwise(col("meses_activo")), 2
    )
)

print("\nPerfil de cada cliente:")
df_clientes.select("nombre", "total_citas", "gasto_promedio",
                   "tasa_cancelacion_pct", "dias_sin_cita",
                   "frecuencia_mensual").show(30, truncate=False)

# ── ETIQUETADO: EN RIESGO ──────────────────────────────────────────────────────
print("="*60)
print("DEFINICIÓN DE RIESGO DE ABANDONO")
print("="*60)

# Calcular umbral dinámico: percentil 75 de dias_sin_cita
umbral_dias = df_clientes.approxQuantile("dias_sin_cita", [0.60], 0.05)[0]
umbral_cancel = 30.0

print(f"""
Criterios de riesgo (basados en los datos reales del sistema):
  1. dias_sin_cita > {umbral_dias:.0f} días (percentil 60 del dataset)
  2. tasa_cancelacion > {umbral_cancel:.0f}%

Un cliente está "en_riesgo" si cumple CUALQUIERA de los dos criterios.
""")

df_labeled = df_clientes.withColumn(
    "en_riesgo",
    when(
        (col("dias_sin_cita") > umbral_dias) |
        (col("tasa_cancelacion_pct") > umbral_cancel),
        1
    ).otherwise(0)
)

en_riesgo   = df_labeled.filter(col("en_riesgo") == 1).count()
sin_riesgo  = df_labeled.filter(col("en_riesgo") == 0).count()
total_cl    = df_labeled.count()
print(f"Clientes en riesgo:  {en_riesgo}  ({round(en_riesgo/total_cl*100)}%)")
print(f"Clientes estables:   {sin_riesgo}  ({round(sin_riesgo/total_cl*100)}%)")

# ── MODELO RANDOM FOREST ───────────────────────────────────────────────────────
print("\n" + "="*60)
print("MODELO: Random Forest Classifier")
print("="*60)

feature_cols = ["total_citas", "gasto_promedio", "tasa_cancelacion_pct",
                "dias_sin_cita", "frecuencia_mensual"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features",
                            handleInvalid="skip")
df_vec = assembler.transform(df_labeled).withColumn("label", col("en_riesgo").cast("double"))

# Con pocos clientes usamos todo para entrenamiento y evaluamos en el mismo set
# (en producción con más datos: split 80/20)
train_df = df_vec
rf = RandomForestClassifier(
    featuresCol="features", labelCol="label",
    numTrees=10, maxDepth=3, seed=42
)
rf_model = rf.fit(train_df)
df_pred  = rf_model.transform(train_df)

auc = BinaryClassificationEvaluator(
    labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC"
).evaluate(df_pred)
acc = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="accuracy"
).evaluate(df_pred)

print(f"AUC-ROC:  {round(auc, 4)}")
print(f"Accuracy: {round(acc, 4)}")

# Importancia de features
print("\nImportancia de cada variable (mayor = más predictiva):")
for feat, imp in sorted(zip(feature_cols, rf_model.featureImportances.toArray()),
                        key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"  {feat:<30} {bar}  {round(imp, 4)}")

# ── LISTA DE CLIENTES EN RIESGO ────────────────────────────────────────────────
print("\n" + "="*60)
print("CLIENTES EN RIESGO DE ABANDONO")
print("="*60)

from pyspark.sql.functions import vector_to_array
df_riesgo = df_pred \
    .withColumn("prob_abandono_pct",
        spark_round(vector_to_array(col("probability"))[1] * 100, 1)) \
    .filter(col("en_riesgo") == 1) \
    .select("nombre", "total_citas", "gasto_promedio",
            "tasa_cancelacion_pct", "dias_sin_cita",
            "frecuencia_mensual", "prob_abandono_pct") \
    .orderBy(col("prob_abandono_pct").desc())

df_riesgo.show(truncate=False)

print("Clientes estables (bajo riesgo):")
df_pred.filter(col("en_riesgo") == 0) \
    .select("nombre", "total_citas", "gasto_promedio", "dias_sin_cita") \
    .orderBy(col("total_citas").desc()) \
    .show(truncate=False)

print("""
Acciones de retención recomendadas:
  ALTA probabilidad (>70%):  Llamada personalizada + oferta urgente
  MEDIA probabilidad (40-70%): WhatsApp recordatorio + descuento 15%
  BAJA probabilidad (<40%):    Newsletter mensual con novedades
""")

spark.stop()
print("Predicción de abandono completada.")
