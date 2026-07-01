"""
Unidad IV — Script 08: Segmentación de Clientes (KMeans sobre RFM)

Clasifica a los 1000 clientes reales en 4 segmentos según su comportamiento:
  VIP          → alto gasto + alta frecuencia + baja cancelación
  Alto consumo → mayor ticket promedio
  Frecuente    → visitas regulares, gasto moderado
  Inactivo     → muchos días sin cita reciente (recencia alta)

Usa la capa de datos única (get_clientes_df) → nombres de cliente REALES
(client_id → clients → users.name) y métricas RFM ya calculadas.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session, get_clientes_df
from pyspark.sql.functions import col, count, avg, round as sround, udf
from pyspark.sql.types import StringType
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

print("\n" + "=" * 60)
print("SEGMENTACIÓN DE CLIENTES — UrbanBlade")
print("=" * 60)
print("""
Objetivo: detectar el perfil de cada cliente para personalizar la experiencia.
  VIP          → Recompensar con descuentos exclusivos
  Alto consumo → Ofrecer paquetes premium / membresías
  Frecuente    → Fidelizar con programa de puntos
  Inactivo     → Campaña de reactivación
""")

# ── DATOS: métricas RFM por cliente (capa única) ───────────────────────────────
spark, df, _ = get_spark_session()
clientes = get_clientes_df(spark, df).cache()

n_clientes = clientes.count()
print(f"Clientes únicos: {n_clientes}")
print("\nTop 10 clientes por gasto total (nombres reales):")
clientes.orderBy(col("gasto_total").desc()) \
    .select("cliente", "nivel", "total_citas", "gasto_total",
            "gasto_promedio", "tasa_cancelacion_pct", "dias_sin_cita") \
    .show(10, truncate=False)

# ── VECTORIZACIÓN + ESCALADO ───────────────────────────────────────────────────
feature_cols = ["total_citas", "gasto_total", "gasto_promedio",
                "tasa_cancelacion_pct", "dias_sin_cita"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features_raw",
                            handleInvalid="skip")
df_vec    = assembler.transform(clientes)
scaler    = StandardScaler(inputCol="features_raw", outputCol="features",
                           withMean=True, withStd=True)
df_scaled = scaler.fit(df_vec).transform(df_vec)

# ── KMEANS k=4 ─────────────────────────────────────────────────────────────────
print("=" * 60)
print("MODELO: KMeans k=4 (un cluster por segmento)")
print("=" * 60)
km_model = KMeans(k=4, seed=42, featuresCol="features").fit(df_scaled)
df_pred  = km_model.transform(df_scaled)
silhouette = ClusteringEvaluator(featuresCol="features").evaluate(df_pred)
print(f"Silhouette Score: {round(silhouette, 4)}")

# ── ESTADÍSTICAS POR CLUSTER ───────────────────────────────────────────────────
print("\nCaracterísticas promedio por cluster:")
df_stats = df_pred.groupBy("prediction").agg(
    count("*").alias("num_clientes"),
    sround(avg("total_citas"),          1).alias("citas_prom"),
    sround(avg("gasto_total"),          0).alias("gasto_total_prom"),
    sround(avg("gasto_promedio"),       0).alias("ticket_prom"),
    sround(avg("tasa_cancelacion_pct"), 1).alias("cancelacion_pct"),
    sround(avg("dias_sin_cita"),        0).alias("dias_inactivo_prom"),
).orderBy("gasto_total_prom", ascending=False)
df_stats.show()

# ── ETIQUETADO AUTOMÁTICO ──────────────────────────────────────────────────────
stats_pd = (df_stats.toPandas()
            .sort_values("gasto_total_prom", ascending=False).reset_index(drop=True))
label_map = {int(stats_pd.iloc[0]["prediction"]): "VIP",
             int(stats_pd.iloc[1]["prediction"]): "Alto consumo"}
remaining = [int(stats_pd.iloc[2]["prediction"]), int(stats_pd.iloc[3]["prediction"])]
sub = stats_pd[stats_pd["prediction"].astype(int).isin(remaining)]
inactivo = int(sub.sort_values("dias_inactivo_prom", ascending=False).iloc[0]["prediction"])
label_map[inactivo] = "Inactivo"
for p in remaining:
    label_map.setdefault(p, "Frecuente")

label_udf = udf(lambda p: label_map.get(p, "Desconocido"), StringType())
df_final  = df_pred.withColumn("segmento", label_udf(col("prediction")))

# ── RESULTADO ───────────────────────────────────────────────────────────────────
print("=" * 60)
print("CLIENTES SEGMENTADOS (muestra por segmento)")
print("=" * 60)
df_final.select("cliente", "nivel", "total_citas", "gasto_total",
                "tasa_cancelacion_pct", "dias_sin_cita", "segmento") \
    .orderBy("segmento", col("gasto_total").desc()).show(30, truncate=False)

print("Distribución de segmentos:")
df_final.groupBy("segmento").agg(
    count("*").alias("clientes"),
    sround(avg("gasto_total"),   0).alias("gasto_total_prom"),
    sround(avg("total_citas"),   1).alias("citas_prom"),
    sround(avg("dias_sin_cita"), 0).alias("dias_inactivo_prom"),
).orderBy("gasto_total_prom", ascending=False).show()

print("""
Acciones recomendadas por segmento:
  VIP          → Tarjeta premium, descuento 15%, cita preferente
  Alto consumo → Membresía mensual todo incluido
  Frecuente    → Programa de puntos, 10ª cita gratis
  Inactivo     → WhatsApp/email: "Te extrañamos — 20% en tu próxima cita"
""")

spark.stop()
print("Segmentación de clientes completada.")
