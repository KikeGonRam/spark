"""
Unidad III — Predicción de Demanda y Análisis de Horarios (regresión supervisada)

  Analiza patrones temporales para anticipar la demanda:
    - Horarios más saturados del día
    - Días de la semana con mayor carga
    - Meses / temporadas con más ingresos
    - Modelo: dada (mes, día_semana, hora) → ¿cuántas citas se esperan?

  Modelo: Gradient Boosted Trees Regressor (GBT) — es aprendizaje SUPERVISADO
  (target numérico = nº de citas), por eso pertenece a la Unidad III.
  Lee la capa de datos única → columnas temporales ya derivadas (hora, dia_semana, mes).

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import (
    get_spark_session, DIAS_SEMANA, MESES
)
from pyspark.sql.functions import (
    col, count, sum as ssum, avg, round as sround
)
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator
import pandas as pd

print("\n" + "=" * 60)
print("PREDICCIÓN DE DEMANDA — UrbanBlade")
print("=" * 60)
print("""
Objetivo: anticipar la carga de trabajo por horario, día y mes para:
  - Asignar barberos en los momentos de mayor demanda
  - Detectar horarios muertos y lanzar promociones
  - Planificar compras de insumos por temporada
""")

# ── DATOS: capa única ──────────────────────────────────────────────────────────
spark, df, _ = get_spark_session()
df = df.filter((col("hora") > 0) & (col("dia_semana") > 0))
print(f"Total de citas cargadas: {df.count()}")

# ── ANÁLISIS 1 — por hora del día ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("ANÁLISIS 1 — Distribución por hora del día")
print("=" * 60)
por_hora = df.groupBy("hora").agg(
    count("*").alias("total_citas"),
    sround(ssum("ingreso"), 0).alias("ingreso_total"),
).orderBy("hora")
hora_pd  = por_hora.toPandas().sort_values("hora")
max_h    = hora_pd["total_citas"].max()
tot_c    = int(hora_pd["total_citas"].sum())
print("\nHEATMAP de demanda por hora (█):")
for _, r in hora_pd.iterrows():
    barra = "█" * int((r["total_citas"] / max_h) * 40)
    pct   = r["total_citas"] / tot_c * 100
    print(f"  {int(r['hora']):02d}:00 {barra:<40} {int(r['total_citas']):>4} citas ({pct:.1f}%)")
hora_pico = hora_pd.loc[hora_pd["total_citas"].idxmax()]
hora_baja = hora_pd.loc[hora_pd["total_citas"].idxmin()]
print(f"Hora pico: {int(hora_pico['hora']):02d}:00 ({int(hora_pico['total_citas'])}) | "
      f"Hora baja: {int(hora_baja['hora']):02d}:00 ({int(hora_baja['total_citas'])})")

# ── ANÁLISIS 2 — por día de la semana ─────────────────────────────────────────
print("\n" + "=" * 60)
print("ANÁLISIS 2 — Distribución por día de la semana")
print("=" * 60)
por_dia = df.groupBy("dia_semana").agg(
    count("*").alias("total_citas"),
    sround(ssum("ingreso"), 0).alias("ingreso_total"),
).orderBy("dia_semana")
dia_pd = por_dia.toPandas().sort_values("dia_semana")
for _, r in dia_pd.iterrows():
    nombre = DIAS_SEMANA.get(int(r["dia_semana"]), "?")
    barra  = "█" * int((r["total_citas"] / dia_pd["total_citas"].max()) * 30)
    print(f"  {nombre:<12} {barra:<30} {int(r['total_citas']):>4} citas  ${int(r['ingreso_total']):>8,}")
dia_pico = dia_pd.loc[dia_pd["total_citas"].idxmax()]
dia_baja = dia_pd.loc[dia_pd["total_citas"].idxmin()]

# ── ANÁLISIS 3 — por mes ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ANÁLISIS 3 — Distribución mensual (temporadas)")
print("=" * 60)
por_mes = df.groupBy("mes").agg(
    count("*").alias("total_citas"),
    sround(ssum("ingreso"), 0).alias("ingreso_total"),
    sround(avg("es_cancelada") * 100, 1).alias("tasa_cancelacion_pct"),
).orderBy("mes")
mes_pd = por_mes.toPandas().sort_values("mes")
for _, r in mes_pd.iterrows():
    nombre = MESES.get(int(r["mes"]), str(int(r["mes"])))
    barra  = "█" * int((r["total_citas"] / mes_pd["total_citas"].max()) * 30)
    print(f"  {nombre:<12} {barra:<30} {int(r['total_citas']):>4} citas  "
          f"${int(r['ingreso_total']):>8,}  cancel:{r['tasa_cancelacion_pct']}%")

# ── MODELO GBT: predicción de citas por slot (mes, día, hora) ──────────────────
print("\n" + "=" * 60)
print("MODELO: GBT Regressor — citas esperadas por (mes, día_semana, hora)")
print("=" * 60)
slots = df.groupBy("mes", "dia_semana", "hora").agg(
    count("*").alias("num_citas")).withColumn("num_citas", col("num_citas").cast("double"))
print(f"Slots (mes × día × hora) con datos: {slots.count()}")

assembler = VectorAssembler(inputCols=["mes", "dia_semana", "hora"],
                            outputCol="features", handleInvalid="skip")
data = assembler.transform(slots)
train, test = data.randomSplit([0.8, 0.2], seed=42)

gbt = GBTRegressor(featuresCol="features", labelCol="num_citas",
                   maxDepth=3, maxIter=20, seed=42)
gbt_model = gbt.fit(train)
pred = gbt_model.transform(test)

rmse = RegressionEvaluator(labelCol="num_citas", predictionCol="prediction", metricName="rmse").evaluate(pred)
r2   = RegressionEvaluator(labelCol="num_citas", predictionCol="prediction", metricName="r2").evaluate(pred)
print(f"RMSE: {round(rmse, 3)}  |  R²: {round(r2, 4)}")

print("\nImportancia de variables para predecir demanda:")
for feat, imp in sorted(zip(["mes", "dia_semana", "hora"],
                            gbt_model.featureImportances.toArray()), key=lambda x: -x[1]):
    print(f"  {feat:<12} {'█' * int(imp * 50)}  {round(imp, 4)}")

# ── PREDICCIONES DE EJEMPLO ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("PREDICCIONES DE DEMANDA (escenarios)")
print("=" * 60)
ejemplos = pd.DataFrame([
    {"mes": 5, "dia_semana": 6, "hora": 10, "desc": "Sábado mayo 10:00"},
    {"mes": 5, "dia_semana": 1, "hora": 9,  "desc": "Lunes mayo 09:00 (apertura)"},
    {"mes": 6, "dia_semana": 5, "hora": 17, "desc": "Viernes junio 17:00 (tarde)"},
    {"mes": 6, "dia_semana": 3, "hora": 14, "desc": "Miércoles junio 14:00"},
])
df_ej = assembler.transform(spark.createDataFrame(ejemplos.drop(columns=["desc"])))
preds = gbt_model.transform(df_ej).collect()
print(f"\n  {'Escenario':<35}{'Citas esperadas':>15}")
print("  " + "-" * 50)
for desc, row in zip(ejemplos["desc"], preds):
    print(f"  {desc:<35}{max(0, round(row['prediction'], 1)):>15.1f}")

# ── RESUMEN EJECUTIVO ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("RESUMEN EJECUTIVO — DEMANDA")
print("=" * 60)
print(f"""
  HORARIO PICO:   {int(hora_pico['hora']):02d}:00 → {int(hora_pico['total_citas'])} citas
  HORARIO MUERTO: {int(hora_baja['hora']):02d}:00 → {int(hora_baja['total_citas'])} citas
  DÍA MÁS ACTIVO: {DIAS_SEMANA.get(int(dia_pico['dia_semana']),'?')} → {int(dia_pico['total_citas'])} citas
  DÍA MÁS QUIETO: {DIAS_SEMANA.get(int(dia_baja['dia_semana']),'?')} → {int(dia_baja['total_citas'])} citas

Recomendaciones operativas:
  - Reforzar personal en el horario y día pico
  - Promoción en el día/hora de menor demanda
  - Planear insumos según el mes de mayor actividad
""")

spark.stop()
print("Predicción de demanda completada.")
