"""
Unidad IV — Script 10: Recomendación de Servicios (Market Basket Analysis)

  Usa FP-Growth para descubrir reglas de asociación entre servicios:
     "Los clientes que piden A también tienden a pedir B"

  Una transacción = conjunto de servicios distintos que ha pedido un cliente
  (solo citas completadas/confirmadas). Métricas: support, confidence, lift.

  Lee la capa de datos única (get_spark_session) → una sola conexión, nombres
  de cliente reales y categoría de servicio ya disponibles.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.sql.functions import col, count, collect_set, size, round as sround, desc
from pyspark.ml.fpm import FPGrowth

print("\n" + "=" * 60)
print("RECOMENDACIÓN DE SERVICIOS (Market Basket) — UrbanBlade")
print("=" * 60)
print("""
Objetivo: "¿Qué servicios adicionales podemos recomendar?"
Técnica : FP-Growth sobre el historial de servicios de cada cliente.
""")

# ── DATOS: capa única, solo citas efectivas ────────────────────────────────────
spark, df, _ = get_spark_session()
df_ok = df.filter(col("estado").isin("completada", "confirmada")) \
          .filter(col("client_id") != "")

print(f"Citas completadas/confirmadas: {df_ok.count()}")
print(f"Clientes con historial:        {df_ok.select('client_id').distinct().count()}")

# ── TRANSACCIONES POR CLIENTE ──────────────────────────────────────────────────
df_tx = (df_ok.groupBy("client_id", "cliente")
              .agg(collect_set("servicio").alias("items"))
              .filter(size(col("items")) >= 1))
print(f"\nClientes con al menos 1 servicio: {df_tx.count()}")
print("Ejemplos de historial (nombres reales):")
df_tx.select("cliente", "items").orderBy(size(col("items")).desc()).show(8, truncate=False)

# ── FP-GROWTH ──────────────────────────────────────────────────────────────────
print("=" * 60)
print("FP-GROWTH — Patrones frecuentes y reglas de asociación")
print("=" * 60)
fp_model = FPGrowth(itemsCol="items", minSupport=0.10, minConfidence=0.20).fit(df_tx)

print("\nItemsets frecuentes (servicios que aparecen juntos):")
fp_model.freqItemsets.orderBy("freq", ascending=False).show(15, truncate=False)

rules = fp_model.associationRules
n_rules = rules.count()
print(f"Reglas de asociación encontradas: {n_rules}")
if n_rules > 0:
    print("\nReglas ordenadas por lift:")
    rules.select(
        col("antecedent").alias("si_pide"),
        col("consequent").alias("tambien_pedira"),
        sround(col("confidence") * 100, 1).alias("confianza_pct"),
        sround(col("lift"), 3).alias("lift"),
        sround(col("support") * 100, 1).alias("support_pct"),
    ).orderBy(desc("lift")).show(20, truncate=False)
    print("""
  Cómo leer: confianza = de los que piden A, % que también pide B
             lift > 1.5 → recomendación fuerte | lift > 1.0 → válida
""")
else:
    print("  No se encontraron reglas con los umbrales actuales.")

# ── CO-OCURRENCIA POR CATEGORÍA ────────────────────────────────────────────────
print("=" * 60)
print("Co-ocurrencia por categoría (clientes que mezclan categorías)")
print("=" * 60)
df_cat = (df_ok.groupBy("client_id", "cliente")
               .agg(collect_set("categoria").alias("categorias"))
               .filter(size(col("categorias")) >= 2))
print(f"Clientes que usaron 2+ categorías: {df_cat.count()}")
df_cat.select("cliente", "categorias").show(10, truncate=False)

# ── POPULARIDAD DE SERVICIOS ───────────────────────────────────────────────────
print("=" * 60)
print("Popularidad de servicios (base para recomendaciones)")
print("=" * 60)
df_ok.groupBy("servicio", "categoria").agg(
    count("*").alias("veces_pedido"),
    count("client_id").alias("citas"),
).orderBy("veces_pedido", ascending=False).show(12, truncate=False)

print("""
IMPLEMENTACIÓN EN URBANBLADE:
  - Al crear la cita: pop-up "También te puede interesar..."
  - Email post-cita: "Clientes como tú también reservaron..."
  - Dashboard admin: oportunidades de upsell por cliente
""")

spark.stop()
print("Recomendación de servicios completada.")
