"""
UNIDAD III — Script 08: Segmentación de Clientes Premium

Clasifica clientes en 4 segmentos usando KMeans sobre métricas reales de comportamiento:
  VIP          → alto gasto + alta frecuencia + baja cancelación
  Alto consumo → mayor gasto total por cita
  Frecuente    → visitas regulares, gasto moderado
  Inactivo     → muchos días sin cita reciente
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, max as spark_max,
    when, round as spark_round, datediff, to_date, lit
)
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
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
    .appName("UrbanBlade-SegmentacionClientes") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

print("\n" + "="*60)
print("SEGMENTACIÓN DE CLIENTES PREMIUM — UrbanBlade")
print("="*60)
print("""
Objetivo: Detectar automáticamente el perfil de cada cliente para
ofrecer experiencias personalizadas:

  VIP          → Recompensar con descuentos exclusivos
  Alto consumo → Ofrecer paquetes premium / membresías
  Frecuente    → Fidelizar con programa de puntos
  Inactivo     → Campaña de reactivación (recordatorio / oferta)
""")

# ── EXTRACCIÓN ─────────────────────────────────────────────────────────────────
mc = MongoClient(mongo_uri)
db = mc[db_name]

users_map    = {str(u["_id"]): u for u in db["users"].find(
    {}, {"_id": 1, "name": 1, "email": 1})}
services_map = {str(s["_id"]): s for s in db["services"].find(
    {}, {"_id": 1, "nombre": 1, "precio": 1})}
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
    .withColumn("fecha_dt",       to_date(col("fecha"), "yyyy-MM-dd"))
    .withColumn("hoy",            to_date(lit(today_str), "yyyy-MM-dd"))
    .withColumn("dias_desde_cita", datediff(col("hoy"), col("fecha_dt"))))

n_citas    = df_citas.count()
n_clientes = df_citas.select("client_id").distinct().count()
print(f"Citas con cliente registrado: {n_citas}")
print(f"Clientes únicos:              {n_clientes}")

# ── MÉTRICAS POR CLIENTE ───────────────────────────────────────────────────────
df_clientes = df_citas.groupBy("client_id", "nombre").agg(
    count("*").alias("total_citas"),
    spark_round(spark_sum("precio"), 2).alias("total_gasto"),
    spark_round(avg("precio"), 2).alias("promedio_gasto"),
    spark_round(
        (count(when(col("estado") == "cancelada", True)) / count("*")) * 100, 1
    ).alias("tasa_cancelacion_pct"),
    spark_round(
        spark_max(col("dias_desde_cita").cast("double")), 0
    ).alias("dias_inactivo"),
)

print("\nMétricas por cliente (top 10 por gasto total):")
df_clientes.orderBy(col("total_gasto").desc()).show(10, truncate=False)

# ── VECTORIZACIÓN ──────────────────────────────────────────────────────────────
feature_cols = ["total_citas", "total_gasto", "promedio_gasto",
                "tasa_cancelacion_pct", "dias_inactivo"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw",
                            handleInvalid="skip")
df_vec    = assembler.transform(df_clientes)

scaler    = StandardScaler(inputCol="features_raw", outputCol="features",
                           withMean=True, withStd=True)
df_scaled = scaler.fit(df_vec).transform(df_vec)

# ── KMEANS k=4 ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("MODELO: KMeans k=4 (un cluster por segmento)")
print("="*60)

kmeans   = KMeans(k=4, seed=42, featuresCol="features")
km_model = kmeans.fit(df_scaled)
df_pred  = km_model.transform(df_scaled)

silhouette = ClusteringEvaluator(featuresCol="features").evaluate(df_pred)
print(f"Silhouette Score: {round(silhouette, 4)}")

# ── ESTADÍSTICAS POR CLUSTER ───────────────────────────────────────────────────
print("\nCaracterísticas promedio por cluster (para asignar etiqueta):")
df_stats = df_pred.groupBy("prediction").agg(
    count("*").alias("num_clientes"),
    spark_round(avg("total_citas"),          1).alias("citas_prom"),
    spark_round(avg("total_gasto"),          0).alias("gasto_total_prom"),
    spark_round(avg("promedio_gasto"),       0).alias("ticket_prom"),
    spark_round(avg("tasa_cancelacion_pct"), 1).alias("cancelacion_pct"),
    spark_round(avg("dias_inactivo"),        0).alias("dias_inactivo_prom"),
).orderBy("gasto_total_prom", ascending=False)
df_stats.show()

# ── ETIQUETADO AUTOMÁTICO ──────────────────────────────────────────────────────
stats_pd = (df_stats.toPandas()
    .sort_values("gasto_total_prom", ascending=False)
    .reset_index(drop=True))

label_map = {}
label_map[int(stats_pd.iloc[0]["prediction"])] = "VIP"
label_map[int(stats_pd.iloc[1]["prediction"])] = "Alto consumo"

remaining = [int(stats_pd.iloc[2]["prediction"]),
             int(stats_pd.iloc[3]["prediction"])]
# El de mayor inactividad → Inactivo
sub = stats_pd[stats_pd["prediction"].astype(int).isin(remaining)]
inactivo_cluster = int(sub.sort_values("dias_inactivo_prom", ascending=False).iloc[0]["prediction"])
label_map[inactivo_cluster] = "Inactivo"
for p in remaining:
    if p not in label_map:
        label_map[p] = "Frecuente"

label_udf = udf(lambda p: label_map.get(p, "Desconocido"), StringType())
df_final  = df_pred.withColumn("segmento", label_udf(col("prediction")))

# ── RESULTADO FINAL ────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("CLIENTES SEGMENTADOS")
print("="*60)
df_final.select("nombre", "total_citas", "total_gasto", "promedio_gasto",
                "tasa_cancelacion_pct", "dias_inactivo", "segmento") \
    .orderBy("segmento", col("total_gasto").desc()) \
    .show(50, truncate=False)

print("Distribución de segmentos:")
df_final.groupBy("segmento").agg(
    count("*").alias("clientes"),
    spark_round(avg("total_gasto"),    0).alias("gasto_total_prom"),
    spark_round(avg("total_citas"),    1).alias("citas_prom"),
    spark_round(avg("dias_inactivo"),  0).alias("dias_inactivo_prom"),
).orderBy("gasto_total_prom", ascending=False).show()

print("""
Acciones recomendadas por segmento:
  VIP          → Tarjeta premium, descuento del 15%, cita preferente
  Alto consumo → Membresía mensual todo incluido
  Frecuente    → Programa de puntos, 10a cita gratis
  Inactivo     → WhatsApp/email: "Te extrañamos — 20% en tu próxima cita"
""")

spark.stop()
print("Segmentación de clientes completada.")
