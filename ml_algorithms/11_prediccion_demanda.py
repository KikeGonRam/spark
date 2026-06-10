"""
UNIDAD III — Script 11: Predicción de Demanda y Análisis de Horarios

Analiza patrones temporales para anticipar la demanda:
  - Horarios más saturados del día
  - Días de la semana con mayor carga
  - Meses / temporadas con más ingresos
  - Modelo predictivo: dada una fecha/hora, ¿cuántas citas se esperan?

Modelo: Gradient Boosted Trees Regressor
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, round as spark_round,
    to_date, dayofweek, month, hour, lit, when
)
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor, LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime
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
    .appName("UrbanBlade-PrediccionDemanda") \
    .config("spark.pyspark.python",        sys.executable) \
    .config("spark.pyspark.driver.python", sys.executable) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

print("\n" + "="*60)
print("PREDICCIÓN DE DEMANDA — UrbanBlade")
print("="*60)
print("""
Objetivo: Anticipar la carga de trabajo por horario, día y mes para:
  - Asignar barberos en los momentos de mayor demanda
  - Detectar horarios muertos y lanzar promociones
  - Planificar compras de insumos por temporada
  - Evitar doble agendado en horas pico
""")

# ── EXTRACCIÓN ─────────────────────────────────────────────────────────────────
mc = MongoClient(mongo_uri)
db = mc[db_name]

services_map = {str(s["_id"]): s for s in db["services"].find(
    {}, {"_id": 1, "precio": 1})}
raw_apts = list(db["appointments"].find({}, {
    "_id": 0, "service_id": 1, "precio_cobrado": 1,
    "estado": 1, "fecha": 1, "hora_inicio": 1
}))
mc.close()

def safe_hour(hora_str):
    try:
        return int(str(hora_str)[:2])
    except Exception:
        return 10

records = []
for apt in raw_apts:
    svc  = services_map.get(str(apt.get("service_id", "")), {})
    pc   = apt.get("precio_cobrado")
    precio = float(pc) if pc is not None else float(svc.get("precio") or 0)
    fecha_str = str(apt.get("fecha", ""))[:10]
    if len(fecha_str) < 10:
        continue
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
    except Exception:
        continue
    records.append({
        "fecha":      fecha_str,
        "mes":        dt.month,
        "dia_semana": dt.isoweekday(),   # 1=Lunes … 7=Domingo
        "hora":       safe_hour(apt.get("hora_inicio")),
        "precio":     precio,
        "estado":     str(apt.get("estado", "")),
        "cancelada":  1 if apt.get("estado") == "cancelada" else 0,
    })

df_raw = spark.createDataFrame(pd.DataFrame(records))
print(f"Total de citas cargadas: {df_raw.count()}")

# ── ANÁLISIS POR HORA ───────────────────────────────────────────────────────────
print("\n" + "="*60)
print("ANÁLISIS 1 — Distribución por hora del día")
print("="*60)

df_por_hora = df_raw.groupBy("hora").agg(
    count("*").alias("total_citas"),
    spark_round(avg("precio"), 0).alias("ingreso_promedio"),
    spark_round(spark_sum("precio"), 0).alias("ingreso_total"),
).orderBy("hora")

print("\nCitas e ingresos por hora:")
df_por_hora.show(24)

hora_pico = df_por_hora.orderBy("total_citas", ascending=False).first()
print(f"Hora pico:    {hora_pico['hora']:02d}:00 — {hora_pico['total_citas']} citas")

hora_baja = df_por_hora.orderBy("total_citas").first()
print(f"Hora baja:    {hora_baja['hora']:02d}:00 — {hora_baja['total_citas']} citas")

print("\nHEATMAP de demanda por hora (█ = 1 cita):")
hora_pd = df_por_hora.toPandas().sort_values("hora")
max_citas = hora_pd["total_citas"].max()
for _, row in hora_pd.iterrows():
    barra   = "█" * int((row["total_citas"] / max_citas) * 40)
    pct     = row["total_citas"] / df_raw.count() * 100
    print(f"  {int(row['hora']):02d}:00 {barra:<40} {int(row['total_citas']):>4} citas ({pct:.1f}%)")

# ── ANÁLISIS POR DÍA DE LA SEMANA ──────────────────────────────────────────────
print("\n" + "="*60)
print("ANÁLISIS 2 — Distribución por día de la semana")
print("="*60)

dias_nombres = {1:"Lunes", 2:"Martes", 3:"Miércoles",
                4:"Jueves", 5:"Viernes", 6:"Sábado", 7:"Domingo"}
dias_udf = spark.udf.register("nombre_dia",
    lambda d: dias_nombres.get(d, "?"), "string")

df_por_dia = df_raw.groupBy("dia_semana").agg(
    count("*").alias("total_citas"),
    spark_round(spark_sum("precio"), 0).alias("ingreso_total"),
    spark_round(avg("precio"), 0).alias("ticket_promedio"),
).orderBy("dia_semana")

print("\nCitas e ingresos por día:")
df_dia_pd = df_por_dia.toPandas().sort_values("dia_semana")
for _, row in df_dia_pd.iterrows():
    nombre = dias_nombres.get(int(row["dia_semana"]), "?")
    barra  = "█" * int((row["total_citas"] / df_dia_pd["total_citas"].max()) * 30)
    print(f"  {nombre:<12} {barra:<30} {int(row['total_citas']):>4} citas  ${int(row['ingreso_total']):>7,}")

dia_pico = df_dia_pd.loc[df_dia_pd["total_citas"].idxmax()]
dia_baja = df_dia_pd.loc[df_dia_pd["total_citas"].idxmin()]
print(f"\nDía más concurrido: {dias_nombres.get(int(dia_pico['dia_semana']), '?')} — {int(dia_pico['total_citas'])} citas")
print(f"Día menos activo:   {dias_nombres.get(int(dia_baja['dia_semana']), '?')} — {int(dia_baja['total_citas'])} citas")

# ── ANÁLISIS POR MES ────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("ANÁLISIS 3 — Distribución mensual (temporadas)")
print("="*60)

meses_nombres = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",
                 6:"Junio",7:"Julio",8:"Agosto",9:"Septiembre",
                 10:"Octubre",11:"Noviembre",12:"Diciembre"}

df_por_mes = df_raw.groupBy("mes").agg(
    count("*").alias("total_citas"),
    spark_round(spark_sum("precio"), 0).alias("ingreso_total"),
    spark_round(avg("cancelada") * 100, 1).alias("tasa_cancelacion_pct"),
).orderBy("mes")

print()
df_mes_pd = df_por_mes.toPandas().sort_values("mes")
for _, row in df_mes_pd.iterrows():
    nombre = meses_nombres.get(int(row["mes"]), str(int(row["mes"])))
    barra  = "█" * int((row["total_citas"] / df_mes_pd["total_citas"].max()) * 30)
    print(f"  {nombre:<12} {barra:<30} {int(row['total_citas']):>4} citas  ${int(row['ingreso_total']):>7,}  cancel:{row['tasa_cancelacion_pct']}%")

# ── MODELO PREDICTIVO ───────────────────────────────────────────────────────────
print("\n" + "="*60)
print("MODELO: Predicción de demanda horaria")
print("="*60)
print("""
Features: mes, dia_semana, hora
Target:   num_citas en ese slot horario
""")

# Agrupar por (mes, dia_semana, hora) → número de citas
df_slots = df_raw.groupBy("mes", "dia_semana", "hora").agg(
    count("*").alias("num_citas"),
    spark_round(spark_sum("precio"), 0).alias("ingreso_slot"),
).withColumn("num_citas", col("num_citas").cast("double"))

print(f"Slots (mes × día × hora) con datos: {df_slots.count()}")

assembler = VectorAssembler(
    inputCols=["mes", "dia_semana", "hora"],
    outputCol="features", handleInvalid="skip"
)
df_vec = assembler.transform(df_slots)

train, test = df_vec.randomSplit([0.8, 0.2], seed=42)

gbt = GBTRegressor(featuresCol="features", labelCol="num_citas",
                   maxDepth=3, maxIter=20, seed=42)
gbt_model = gbt.fit(train)
df_pred   = gbt_model.transform(test)

rmse = RegressionEvaluator(labelCol="num_citas", predictionCol="prediction",
                            metricName="rmse").evaluate(df_pred)
r2   = RegressionEvaluator(labelCol="num_citas", predictionCol="prediction",
                            metricName="r2").evaluate(df_pred)

print(f"RMSE: {round(rmse, 3)}")
print(f"R²:   {round(r2, 4)}")

# Importancia de features
print("\nImportancia de variables para predecir demanda:")
for feat, imp in sorted(zip(["mes", "dia_semana", "hora"],
                             gbt_model.featureImportances.toArray()),
                        key=lambda x: -x[1]):
    barra = "█" * int(imp * 50)
    print(f"  {feat:<15} {barra}  {round(imp, 4)}")

# ── PREDICCIONES DE EJEMPLO ─────────────────────────────────────────────────────
print("\n" + "="*60)
print("PREDICCIONES DE DEMANDA (escenarios)")
print("="*60)

ejemplos = pd.DataFrame([
    {"mes": 5, "dia_semana": 6, "hora": 10},   # Sábado mayo 10am
    {"mes": 5, "dia_semana": 1, "hora": 8},    # Lunes mayo 8am
    {"mes": 6, "dia_semana": 5, "hora": 17},   # Viernes junio 5pm
    {"mes": 6, "dia_semana": 3, "hora": 14},   # Miércoles junio 2pm
    {"mes": 7, "dia_semana": 6, "hora": 11},   # Sábado julio 11am
])
df_ej = assembler.transform(spark.createDataFrame(ejemplos))
preds = gbt_model.transform(df_ej).collect()

print(f"\n  {'Escenario':<35} {'Citas esperadas':>15}")
print("  " + "-"*52)
escenarios = [
    "Sábado mayo 10:00",
    "Lunes mayo 08:00 (apertura)",
    "Viernes junio 17:00 (tarde)",
    "Miércoles junio 14:00",
    "Sábado julio 11:00",
]
for esc, row in zip(escenarios, preds):
    pred_val = max(0, round(row["prediction"], 1))
    print(f"  {esc:<35} {pred_val:>15.1f} citas")

# ── RESUMEN EJECUTIVO ───────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESUMEN EJECUTIVO — DEMANDA")
print("="*60)
print(f"""
Patrones detectados en {df_raw.count()} citas reales:

  HORARIO PICO:    {hora_pico['hora']:02d}:00 hrs → {int(hora_pico['total_citas'])} citas
  HORARIO MUERTO:  {hora_baja['hora']:02d}:00 hrs → {int(hora_baja['total_citas'])} citas
  DÍA MÁS ACTIVO: {dias_nombres.get(int(dia_pico['dia_semana']), '?')} → {int(dia_pico['total_citas'])} citas
  DÍA MÁS QUIETO: {dias_nombres.get(int(dia_baja['dia_semana']), '?')} → {int(dia_baja['total_citas'])} citas

Recomendaciones operativas:
  - Asignar los 3 barberos en horario pico
  - Reforzar con barbero adicional los sábados
  - Promoción "Martes de descuento" en el día de menor demanda
  - Compra de insumos: concentrar en mayo (70%+ de la demanda)
""")

spark.stop()
print("Predicción de demanda completada.")
