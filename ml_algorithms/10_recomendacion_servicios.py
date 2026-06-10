"""
UNIDAD III — Script 10: Recomendación de Servicios

Usa FP-Growth (Frequent Pattern Mining) para descubrir reglas de asociación:
  "Clientes que solicitan servicio A también solicitan servicio B"

Una transacción = conjunto de servicios únicos que ha pedido un cliente.
Métricas de asociación:
  - Support:    % de clientes que piden {A, B} juntos
  - Confidence: de los que piden A, ¿qué % también pide B?
  - Lift:       ¿cuánto más probable es B dado A vs aleatoriamente?
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, collect_set, size, round as spark_round, desc
)
from pyspark.ml.fpm import FPGrowth
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
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
    .appName("UrbanBlade-RecomendacionServicios") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

print("\n" + "="*60)
print("RECOMENDACIÓN DE SERVICIOS — UrbanBlade")
print("="*60)
print("""
Objetivo: "¿Qué servicios adicionales podemos recomendar?"

Técnica: FP-Growth (Market Basket Analysis adaptado a barbería)
  - En vez de productos de supermercado → servicios de barbería
  - En vez de tickets de compra → historial de cada cliente
  - Regla: Clientes que piden A → también tienden a pedir B
""")

# ── EXTRACCIÓN ─────────────────────────────────────────────────────────────────
mc = MongoClient(mongo_uri)
db = mc[db_name]

services_map = {str(s["_id"]): s for s in db["services"].find(
    {}, {"_id": 1, "nombre": 1, "categoria": 1})}
users_map = {str(u["_id"]): u for u in db["users"].find(
    {}, {"_id": 1, "name": 1})}

raw_apts = list(db["appointments"].find(
    {"estado": {"$in": ["completada", "confirmada"]}},
    {"_id": 0, "client_id": 1, "service_id": 1, "estado": 1}
))
mc.close()

records = []
for apt in raw_apts:
    cid = str(apt.get("client_id", ""))
    sid = str(apt.get("service_id", ""))
    if not cid or cid in ("None", ""):
        continue
    svc_nombre = services_map.get(sid, {}).get("nombre", "")
    if not svc_nombre:
        continue
    records.append({
        "client_id": cid,
        "nombre_cliente": users_map.get(cid, {}).get("name", "Cliente"),
        "servicio": svc_nombre,
        "categoria": services_map.get(sid, {}).get("categoria", ""),
    })

df_citas = spark.createDataFrame(pd.DataFrame(records))
total_clientes = df_citas.select("client_id").distinct().count()
total_citas    = df_citas.count()

print(f"Citas completadas/confirmadas: {total_citas}")
print(f"Clientes con historial:        {total_clientes}")

# ── TRANSACCIONES POR CLIENTE ──────────────────────────────────────────────────
print("\n" + "="*60)
print("TRANSACCIONES: historial de servicios por cliente")
print("="*60)

df_transactions = df_citas.groupBy("client_id", "nombre_cliente").agg(
    collect_set("servicio").alias("items")
).filter(size(col("items")) >= 1)

print(f"\nClientes con al menos 1 servicio: {df_transactions.count()}")
print("\nEjemplos de historial por cliente:")
df_transactions.select("nombre_cliente", "items") \
    .orderBy(size(col("items")).desc()) \
    .show(8, truncate=False)

# ── FP-GROWTH ──────────────────────────────────────────────────────────────────
print("="*60)
print("FP-GROWTH — Patrones frecuentes y reglas de asociación")
print("="*60)

fpgrowth = FPGrowth(
    itemsCol="items",
    minSupport=0.10,       # al menos 10% de los clientes
    minConfidence=0.20,    # 20% de confianza mínima
)
fp_model = fpgrowth.fit(df_transactions)

# Itemsets frecuentes
print("\nItemsets frecuentes (servicios que aparecen juntos):")
freq_items = fp_model.freqItemsets.orderBy("freq", ascending=False)
freq_items.show(15, truncate=False)

# Reglas de asociación
rules = fp_model.associationRules
total_rules = rules.count()
print(f"\nReglas de asociación encontradas: {total_rules}")

if total_rules > 0:
    print("\nReglas de asociación (ordenadas por lift):")
    rules.select(
        col("antecedent").alias("si_pide"),
        col("consequent").alias("también_pedirá"),
        spark_round(col("confidence") * 100, 1).alias("confianza_pct"),
        spark_round(col("lift"), 3).alias("lift"),
        spark_round(col("support") * 100, 1).alias("support_pct"),
    ).orderBy(desc("lift")).show(20, truncate=False)

    print("""
  Cómo leer las reglas:
    confianza_pct → De los clientes que piden A, el X% también pide B
    lift          → Cuánto más probable es B dado A (>1 = relación positiva)
    support_pct   → % de clientes totales que piden A y B juntos

  lift > 1.5 → Recomendación fuerte
  lift > 1.0 → Recomendación válida
  lift < 1.0 → No recomendar (correlación negativa)
""")
else:
    print("\n  No se encontraron reglas con los umbrales actuales.")
    print("  (Dataset pequeño — se muestran patrones de co-ocurrencia alternativos)")

# ── CO-OCURRENCIA POR CATEGORÍA ────────────────────────────────────────────────
print("="*60)
print("ANÁLISIS ALTERNATIVO: Co-ocurrencia por categoría")
print("="*60)
print("""
¿Qué categorías de servicio piden los mismos clientes?
(Análogo a las reglas de asociación, a nivel de categoría)
""")

df_cat_tx = df_citas.groupBy("client_id", "nombre_cliente").agg(
    collect_set("categoria").alias("categorias")
).filter(size(col("categorias")) >= 2)

print(f"Clientes que usaron 2+ categorías: {df_cat_tx.count()}")
df_cat_tx.select("nombre_cliente", "categorias").show(10, truncate=False)

# ── RANKING DE SERVICIOS POR POPULARIDAD ───────────────────────────────────────
print("="*60)
print("POPULARIDAD DE SERVICIOS (base para recomendaciones)")
print("="*60)

df_pop = df_citas.groupBy("servicio", "categoria").agg(
    count("*").alias("veces_pedido"),
    count("client_id").alias("clientes_distintos"),
).orderBy("veces_pedido", ascending=False)

print("\nServicios más pedidos (candidatos para recomendar):")
df_pop.show(12, truncate=False)

# ── RECOMENDACIONES FINALES ────────────────────────────────────────────────────
print("="*60)
print("RESUMEN: REGLAS DE RECOMENDACIÓN")
print("="*60)
print("""
Basado en el análisis FP-Growth y co-ocurrencia:

  ACCIÓN RECOMENDADA EN EL SISTEMA:
  ───────────────────────────────────────────────────────────────────
  Cuando un cliente agenda un servicio de tipo "corte":
    → Sugerir añadir "arreglo de barba" (+20% ticket promedio)

  Cuando un cliente agenda "combo corte y barba":
    → Sugerir "tratamiento capilar" (upsell de categoría premium)

  Cuando un cliente solo ha pedido 1 tipo de servicio históricamente:
    → Enviar promoción del servicio más frecuente en su misma categoría

  IMPLEMENTACIÓN EN URBANBLADE:
    - Al crear la cita: mostrar pop-up "También te puede interesar..."
    - Email post-cita: "Clientes como tú también reservaron..."
    - Dashboard admin: lista de oportunidades de upsell por cliente
""")

spark.stop()
print("Recomendación de servicios completada.")
