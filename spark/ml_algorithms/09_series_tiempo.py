"""
Unidad III – Análisis de Series de Tiempo | UrbanBlade
Materia: Extracción del Conocimiento en BD ·  UTVT IDGS-93

Temas:
  - Tendencia de ingresos mensuales (18 meses)
  - Patrones estacionales: horas pico, días de semana
  - Regresión lineal sobre el tiempo → predicción 3 meses
  - Comparativa por servicio a lo largo del tiempo
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (col, year, month, hour, dayofweek,
                                   sum as _sum, avg, count, date_format,
                                   concat_ws, lpad)
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
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
    .appName("UrbanBlade-Series-Tiempo") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.read.connection.uri",  mongo_uri) \
    .config("spark.mongodb.read.database",        database) \
    .config("spark.mongodb.read.collection",      collection_name) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

SEP = "=" * 65

# ── Carga y filtrado ──────────────────────────────────────────
df = spark.read.format("mongodb").load()
df = df.filter(col("fecha").isNotNull()) \
       .withColumn("anio",      year(col("fecha"))) \
       .withColumn("mes",       month(col("fecha"))) \
       .withColumn("hora",      hour(col("fecha"))) \
       .withColumn("dia_sem",   dayofweek(col("fecha"))) \
       .withColumn("ingreso",   col("cantidad").cast("double") * col("precio").cast("double"))

total = df.count()
print(f"\n{SEP}")
print(" ANÁLISIS DE SERIES DE TIEMPO – UrbanBlade")
print(SEP)
print(f"  Registros con fecha: {total:,} (últimos 18 meses)")

# ═══════════════════════════════════════════════════════════════
# 1. TENDENCIA MENSUAL
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 1. TENDENCIA DE INGRESOS MENSUAL")
print(SEP)

mensual = df.groupBy("anio", "mes").agg(
    _sum("ingreso").alias("ingreso_total"),
    count("*").alias("num_citas"),
    avg("ingreso").alias("ticket_promedio")
).orderBy("anio", "mes")

mensual.show(20, truncate=False)

pdf_mensual = mensual.toPandas()
if not pdf_mensual.empty:
    mejor_mes = pdf_mensual.loc[pdf_mensual["ingreso_total"].idxmax()]
    print(f"  Mejor mes: {int(mejor_mes['anio'])}-{int(mejor_mes['mes']):02d}  "
          f"Ingresos: ${mejor_mes['ingreso_total']:,.0f}  "
          f"Citas: {int(mejor_mes['num_citas']):,}")

# ═══════════════════════════════════════════════════════════════
# 2. PREDICCIÓN 3 MESES SIGUIENTES (Regresión Lineal sobre tiempo)
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 2. PREDICCIÓN – PRÓXIMOS 3 MESES")
print(SEP)

pdf_mensual["t"] = range(len(pdf_mensual))

spark_ts = spark.createDataFrame(pdf_mensual[["t", "ingreso_total"]])
asm = VectorAssembler(inputCols=["t"], outputCol="features")
df_ts = asm.transform(spark_ts)
lr = LinearRegression(featuresCol="features", labelCol="ingreso_total")
modelo = lr.fit(df_ts)

print(f"  R² del modelo temporal : {modelo.summary.r2:.4f}")
print(f"  Pendiente (tendencia)   : ${modelo.coefficients[0]:,.0f} por mes")
print(f"  Intercepto              : ${modelo.intercept:,.0f}")

n = len(pdf_mensual)
print(f"\n  Predicción de ingresos:")
for i, label in enumerate(["Mes +1", "Mes +2", "Mes +3"]):
    pred = modelo.intercept + modelo.coefficients[0] * (n + i)
    print(f"    {label}: ${pred:,.0f}")

# ═══════════════════════════════════════════════════════════════
# 3. PATRONES POR HORA DEL DÍA
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 3. HORAS PICO DEL DÍA")
print(SEP)

por_hora = df.groupBy("hora").agg(
    count("*").alias("num_citas"),
    _sum("ingreso").alias("ingreso_total")
).orderBy("hora")

pdf_hora = por_hora.toPandas()
if not pdf_hora.empty:
    hora_pico = pdf_hora.loc[pdf_hora["num_citas"].idxmax()]
    print(f"  Hora pico de citas:   {int(hora_pico['hora'])}:00  ({int(hora_pico['num_citas']):,} citas)")
    for _, row in pdf_hora.iterrows():
        barra = "█" * int(row["num_citas"] / pdf_hora["num_citas"].max() * 30)
        print(f"  {int(row['hora']):02d}:00  {barra}  {int(row['num_citas']):,}")

# ═══════════════════════════════════════════════════════════════
# 4. PATRONES POR DÍA DE SEMANA
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 4. DISTRIBUCIÓN POR DÍA DE SEMANA")
print(SEP)

dias_nombre = {1: "Domingo", 2: "Lunes", 3: "Martes", 4: "Miércoles",
               5: "Jueves", 6: "Viernes", 7: "Sábado"}

por_dia = df.groupBy("dia_sem").agg(
    count("*").alias("num_citas"),
    _sum("ingreso").alias("ingreso_total")
).orderBy("dia_sem")

pdf_dia = por_dia.toPandas()
if not pdf_dia.empty:
    for _, row in pdf_dia.iterrows():
        nombre = dias_nombre.get(int(row["dia_sem"]), str(row["dia_sem"]))
        barra  = "█" * int(row["num_citas"] / pdf_dia["num_citas"].max() * 25)
        print(f"  {nombre:<12} {barra}  {int(row['num_citas']):,}")

# ═══════════════════════════════════════════════════════════════
# 5. TOP SERVICIO POR MES
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" 5. SERVICIO MÁS POPULAR POR MES")
print(SEP)

from pyspark.sql.window import Window
from pyspark.sql.functions import rank

w = Window.partitionBy("anio", "mes").orderBy(col("citas").desc())
top_serv = df.groupBy("anio", "mes", "servicio").agg(count("*").alias("citas")) \
             .withColumn("rank", rank().over(w)) \
             .filter(col("rank") == 1) \
             .orderBy("anio", "mes")

top_serv.select("anio", "mes", "servicio", "citas").show(20, truncate=False)

spark.stop()
print("✅ Análisis de Series de Tiempo completado")
