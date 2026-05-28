"""
Unidad III/IV – Análisis RFM de Clientes | UrbanBlade
Materia: Extracción del Conocimiento en BD ·  UTVT IDGS-93

RFM = Recency + Frequency + Monetary
  - Recency   : días desde la última visita
  - Frequency : número de citas completadas
  - Monetary  : gasto total del cliente
  - KMeans 4 clusters → VIP / Leal / En Riesgo / Inactivo
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (col, max as _max, min as _min,
                                   count, sum as _sum, datediff, lit,
                                   to_date, avg)
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

database        = os.getenv("MONGO_DB",         "urbanblade")
collection_name = os.getenv("MONGO_COLLECTION", "appointments")
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD", ""))
    cluster  = os.getenv("MONGO_CLUSTER")
    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

spark = SparkSession.builder \
    .appName("UrbanBlade-RFM") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.read.connection.uri",  mongo_uri) \
    .config("spark.mongodb.read.database",        database) \
    .config("spark.mongodb.read.collection",      collection_name) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

SEP = "=" * 65

# ── Carga ─────────────────────────────────────────────────────
df = spark.read.format("mongodb").load()
df = df.filter(col("fecha").isNotNull() & col("cliente_id").isNotNull()) \
       .withColumn("ingreso", col("cantidad").cast("double") * col("precio").cast("double"))

total = df.count()
clientes = df.select("cliente_id").distinct().count()

print(f"\n{SEP}")
print(" ANÁLISIS RFM DE CLIENTES – UrbanBlade")
print(SEP)
print(f"  Registros disponibles : {total:,}")
print(f"  Clientes únicos       : {clientes:,}")

# ═══════════════════════════════════════════════════════════════
# 1. CÁLCULO DE MÉTRICAS RFM
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 1. CÁLCULO DE MÉTRICAS RFM")
print(SEP)

# Fecha de referencia = fecha máxima en el dataset
fecha_ref = df.agg(_max("fecha")).collect()[0][0]
print(f"  Fecha de referencia : {fecha_ref.strftime('%Y-%m-%d')}")

# Solo citas completadas para F y M
df_comp = df.filter(col("estado") == "completada")

# R: días desde última visita (todos los estados)
recency = df.groupBy("cliente_id").agg(
    _max("fecha").alias("ultima_visita")
).withColumn("recency_days",
    datediff(lit(fecha_ref.strftime("%Y-%m-%d")).cast("date"),
             col("ultima_visita").cast("date"))
)

# F: número de citas completadas
frequency = df_comp.groupBy("cliente_id").agg(
    count("*").alias("frequency")
)

# M: gasto total en citas completadas
monetary = df_comp.groupBy("cliente_id").agg(
    _sum("ingreso").alias("monetary")
)

# Unir RFM
rfm = recency.join(frequency, "cliente_id", "left") \
             .join(monetary,  "cliente_id", "left") \
             .fillna({"frequency": 0, "monetary": 0.0})

rfm_count = rfm.count()
print(f"  Clientes en análisis RFM: {rfm_count:,}")

print(f"\n  Estadísticas RFM:")
rfm.select(
    avg("recency_days").alias("Recency_Avg"),
    avg("frequency").alias("Frequency_Avg"),
    avg("monetary").alias("Monetary_Avg")
).show()

print("  Muestra de clientes RFM:")
rfm.orderBy("monetary", ascending=False).show(10, truncate=False)

# ═══════════════════════════════════════════════════════════════
# 2. NORMALIZACIÓN Y CLUSTERING
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 2. NORMALIZACIÓN Y SEGMENTACIÓN KMEANS (K=4)")
print(SEP)

rfm_clean = rfm.dropna(subset=["recency_days", "frequency", "monetary"]) \
               .filter(col("frequency") > 0)

asm = VectorAssembler(
    inputCols=["recency_days", "frequency", "monetary"],
    outputCol="features_raw",
    handleInvalid="skip"
)
rfm_vec = asm.transform(rfm_clean)

scaler = StandardScaler(inputCol="features_raw", outputCol="features",
                        withMean=True, withStd=True)
rfm_scaled = scaler.fit(rfm_vec).transform(rfm_vec)

km = KMeans(k=4, seed=42, featuresCol="features", predictionCol="segmento")
model = km.fit(rfm_scaled)
rfm_seg = model.transform(rfm_scaled)

sil = ClusteringEvaluator(featuresCol="features", predictionCol="segmento").evaluate(rfm_seg)
print(f"  Silhouette Score: {sil:.4f}")

# ═══════════════════════════════════════════════════════════════
# 3. INTERPRETACIÓN DE SEGMENTOS
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 3. PERFILES DE SEGMENTOS")
print(SEP)

perfil = rfm_seg.groupBy("segmento").agg(
    count("*").alias("clientes"),
    avg("recency_days").alias("recency_avg"),
    avg("frequency").alias("freq_avg"),
    avg("monetary").alias("monetary_avg")
).orderBy("monetary_avg", ascending=False).toPandas()

ETIQUETAS = {0: "❓ Sin clasificar"}
recency_vals = perfil["recency_avg"].tolist()
monetary_vals = perfil["monetary_avg"].tolist()
freq_vals = perfil["freq_avg"].tolist()

for _, row in perfil.iterrows():
    seg  = int(row["segmento"])
    r    = row["recency_avg"]
    f    = row["freq_avg"]
    m    = row["monetary_avg"]
    if m == max(monetary_vals) and r == min(recency_vals):
        label = "⭐ VIP"
    elif m >= sorted(monetary_vals)[-2] or f >= sorted(freq_vals)[-2]:
        label = "💚 Leal"
    elif r <= sorted(recency_vals)[1]:
        label = "⚠️  En Riesgo"
    else:
        label = "💤 Inactivo"
    ETIQUETAS[seg] = label

print(f"\n  {'Segmento':<6} {'Etiqueta':<14} {'Clientes':>8} {'Recency':>10} {'Frequency':>10} {'Monetary':>12}")
print(f"  {'-'*65}")
for _, row in perfil.iterrows():
    seg   = int(row["segmento"])
    etiq  = ETIQUETAS.get(seg, "Otro")
    print(f"  {seg:<6} {etiq:<14} {int(row['clientes']):>8,} "
          f"{row['recency_avg']:>9.1f}d "
          f"{row['freq_avg']:>9.1f}  "
          f"${row['monetary_avg']:>10,.0f}")

# ═══════════════════════════════════════════════════════════════
# 4. RECOMENDACIONES DE NEGOCIO
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 4. RECOMENDACIONES DE NEGOCIO")
print(SEP)
print("""
  ⭐ VIP       → Programa de fidelidad premium, descuentos exclusivos
  💚 Leal      → Comunicación regular, invitación a servicios nuevos
  ⚠️  En Riesgo → Campaña de reactivación, cupón de descuento urgente
  💤 Inactivo  → Email de "te extrañamos" + oferta especial
""")

spark.stop()
print("✅ Análisis RFM completado")
