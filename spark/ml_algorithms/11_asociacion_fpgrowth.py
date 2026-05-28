"""
Unidad IV – Reglas de Asociación FP-Growth | UrbanBlade
Materia: Extracción del Conocimiento en BD ·  UTVT IDGS-93

FP-Growth (Frequent Pattern Growth):
  - Algoritmo de minería de patrones frecuentes
  - Más eficiente que Apriori en Big Data (sin generación de candidatos)
  - Métricas: Soporte, Confianza, Lift
  - ¿Qué servicios se contratan juntos por los mismos clientes?
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, collect_set, count, size
from pyspark.ml.fpm import FPGrowth
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus

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
    .appName("UrbanBlade-FPGrowth") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.read.connection.uri",  mongo_uri) \
    .config("spark.mongodb.read.database",        database) \
    .config("spark.mongodb.read.collection",      collection_name) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

SEP = "=" * 65

# ── Carga ─────────────────────────────────────────────────────
df = spark.read.format("mongodb").load()
df_comp = df.filter(
    col("cliente_id").isNotNull() &
    col("servicio").isNotNull()   &
    (col("estado") == "completada")
)

total = df_comp.count()
clientes = df_comp.select("cliente_id").distinct().count()

print(f"\n{SEP}")
print(" REGLAS DE ASOCIACIÓN FP-GROWTH – UrbanBlade")
print(SEP)
print(f"  Citas completadas   : {total:,}")
print(f"  Clientes únicos     : {clientes:,}")

# ═══════════════════════════════════════════════════════════════
# 1. CONSTRUIR TRANSACCIONES
#    Cada cliente → cesta de servicios que ha contratado
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 1. CONSTRUCCIÓN DE TRANSACCIONES")
print(SEP)
print("  Estrategia: cada cliente = 1 transacción")
print("  Ítem = servicios distintos contratados históricamente")

transacciones = df_comp.groupBy("cliente_id").agg(
    collect_set("servicio").alias("items")
).filter(size(col("items")) >= 2)

total_trans = transacciones.count()
print(f"\n  Transacciones con ≥2 servicios: {total_trans:,}")
print("\n  Muestra de transacciones:")
transacciones.show(5, truncate=False)

# ═══════════════════════════════════════════════════════════════
# 2. APLICAR FP-GROWTH
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 2. ALGORITMO FP-GROWTH")
print(SEP)
print("  minSupport    = 0.05 (aparece en ≥5% de transacciones)")
print("  minConfidence = 0.30 (regla es correcta ≥30% de los casos)")

fp = FPGrowth(
    itemsCol     = "items",
    minSupport   = 0.05,
    minConfidence= 0.30
)
model = fp.fit(transacciones)

# ═══════════════════════════════════════════════════════════════
# 3. ITEMSETS FRECUENTES
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 3. CONJUNTOS DE ÍTEMS FRECUENTES (Top 15)")
print(SEP)
print("""
  Soporte = frecuencia / total_transacciones
  Un soporte de 0.15 significa que el servicio aparece
  en el 15% de todas las cestas de clientes.
""")

freq_items = model.freqItemsets.orderBy("freq", ascending=False)
total_freq = freq_items.count()
print(f"  Conjuntos frecuentes encontrados: {total_freq}")
freq_items.show(15, truncate=False)

# ═══════════════════════════════════════════════════════════════
# 4. REGLAS DE ASOCIACIÓN
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 4. REGLAS DE ASOCIACIÓN (SI → ENTONCES)")
print(SEP)
print("""
  Confianza: P(consecuente | antecedente)
  Lift > 1 → la regla aporta información real (no es aleatoria)
  Lift = 1 → independencia (la regla no sirve)
""")

reglas = model.associationRules.orderBy("confidence", ascending=False)
total_reglas = reglas.count()
print(f"  Reglas generadas: {total_reglas}")

if total_reglas > 0:
    reglas.show(20, truncate=False)

    pdf_reglas = reglas.toPandas()
    print("\n  INTERPRETACIÓN DE LAS MEJORES REGLAS:")
    print(f"  {'-'*55}")
    for _, row in pdf_reglas.head(10).iterrows():
        ante  = ", ".join(sorted(list(row["antecedent"])))
        cons  = ", ".join(sorted(list(row["consequent"])))
        conf  = row["confidence"]
        lift  = row["lift"]
        nivel = "⭐ Fuerte" if lift > 1.5 else "✅ Útil" if lift > 1.1 else "⚠️ Débil"
        print(f"  Si [{ante}] → [{cons}]")
        print(f"    Confianza: {conf*100:.1f}%  |  Lift: {lift:.2f}  |  {nivel}\n")
else:
    print("  No se generaron reglas con los parámetros actuales.")
    print("  Prueba reduciendo minSupport o minConfidence.")

# ═══════════════════════════════════════════════════════════════
# 5. SERVICIOS MÁS FRECUENTES (soporte individual)
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 5. POPULARIDAD DE SERVICIOS (Soporte individual)")
print(SEP)

freq_single = freq_items.filter(size(col("items")) == 1).toPandas()
for _, row in freq_single.iterrows():
    serv   = row["items"][0]
    soporte = row["freq"] / total_trans
    barra   = "█" * int(soporte * 100)
    print(f"  {serv:<20} {barra}  {soporte*100:.1f}%  ({row['freq']} clientes)")

spark.stop()
print("\n✅ Análisis FP-Growth completado")
