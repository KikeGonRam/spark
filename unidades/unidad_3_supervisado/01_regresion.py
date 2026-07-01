"""
Unidad III – Análisis Supervisado (Regresión)
Script  : 03_regresion_analytics.py
Tema    : 6 modelos de regresión con evaluación honesta (R², MSE, MAE)

  PROBLEMA DE NEGOCIO: ¿Cuánto facturará la barbería en un día dado?
  Target  : ingreso_dia  (facturación total del día)
  Features: num_citas, duracion_total, dia_semana, mes   (SIN fuga de datos —
            el ingreso NO se usa como feature de sí mismo)

  Nota metodológica: en `barber_db` el precio por cita es determinista por
  servicio (precio_cobrado == precio_servicio), así que predecir el precio de
  UNA cita sería trivial (R²≈1.0, fuga). Por eso agregamos por día: la
  facturación diaria SÍ tiene varianza real (mezcla de servicios, volumen,
  día de la semana), y la regresión se vuelve un problema honesto.

Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Equipo  : Equipo UrbanBlade
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-93
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.sql.functions import (
    col, count, sum as ssum, avg, to_date, dayofweek, month
)
from pyspark.ml.feature import VectorAssembler, PolynomialExpansion
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import matplotlib.pyplot as plt

# ─── 1. Cargar datos reales y AGREGAR por día ─────────────────────────────────
spark, df, _ = get_spark_session()
print("\n===  UNIDAD III – REGRESIÓN (facturación diaria) – UrbanBlade  ===\n")

# Solo citas que generan ingreso real (no canceladas)
df_ok = df.filter(col("estado") != "cancelada") \
          .withColumn("fecha_dt", to_date(col("fecha").substr(1, 10), "yyyy-MM-dd"))

# Una fila por día: facturación, volumen, duración total, calendario
dia = (df_ok.groupBy("fecha_dt").agg(
            count("*").alias("num_citas"),
            ssum("ingreso").alias("ingreso_dia"),
            ssum("duracion_min").alias("duracion_total"),
            avg("precio").alias("ticket_promedio"),
        )
        .withColumn("dia_semana", dayofweek(col("fecha_dt")))
        .withColumn("mes",        month(col("fecha_dt")))
        .dropna())

print("Muestra de la facturación diaria (target = ingreso_dia):")
dia.select("fecha_dt", "num_citas", "duracion_total",
           "dia_semana", "mes", "ingreso_dia").show(8)
print(f"Días con datos: {dia.count()}")

# ─── 2. Train/test split ──────────────────────────────────────────────────────
train, test = dia.randomSplit([0.8, 0.2], seed=42)
print(f"Entrenamiento: {train.count()} días  |  Prueba: {test.count()} días\n")

# ─── 3. Evaluadores (R², MSE, MAE) ───────────────────────────────────────────
def evaluar(predictions, label="ingreso_dia"):
    r2  = RegressionEvaluator(labelCol=label, predictionCol="prediction", metricName="r2").evaluate(predictions)
    mse = RegressionEvaluator(labelCol=label, predictionCol="prediction", metricName="mse").evaluate(predictions)
    mae = RegressionEvaluator(labelCol=label, predictionCol="prediction", metricName="mae").evaluate(predictions)
    return round(r2, 4), round(mse, 2), round(mae, 2)


def graficar(predictions, titulo):
    pdf = predictions.select("num_citas", "ingreso_dia", "prediction").toPandas()
    plt.figure(figsize=(8, 5))
    plt.scatter(pdf["num_citas"], pdf["ingreso_dia"],  label="Real",       alpha=0.6, color="steelblue")
    plt.scatter(pdf["num_citas"], pdf["prediction"],   label="Predicción", alpha=0.6, color="tomato", marker="x")
    plt.title(titulo)
    plt.xlabel("Número de citas en el día")
    plt.ylabel("Facturación del día ($MXN)")
    plt.legend(); plt.tight_layout(); plt.show()


# ─── MODELO 1 – Regresión Lineal Simple (ingreso ~ num_citas) ─────────────────
print("=" * 58)
print("MODELO 1 – LINEAL SIMPLE   (ingreso_dia ~ num_citas)")
a1  = VectorAssembler(inputCols=["num_citas"], outputCol="features", handleInvalid="skip")
m1  = LinearRegression(featuresCol="features", labelCol="ingreso_dia").fit(a1.transform(train))
p1  = m1.transform(a1.transform(test))
r1  = evaluar(p1)
print(f"  Coef: {m1.coefficients[0]:.2f} $/cita  |  Intercepto: {m1.intercept:.2f}")
print(f"  R²={r1[0]}  MSE={r1[1]}  MAE={r1[2]}")

# ─── MODELO 2 – Regresión Lineal Múltiple ─────────────────────────────────────
print("=" * 58)
print("MODELO 2 – LINEAL MÚLTIPLE (+ duracion_total, dia_semana, mes)")
feat = ["num_citas", "duracion_total", "dia_semana", "mes"]
a2   = VectorAssembler(inputCols=feat, outputCol="features", handleInvalid="skip")
tr2, te2 = a2.transform(train), a2.transform(test)
m2   = LinearRegression(featuresCol="features", labelCol="ingreso_dia").fit(tr2)
r2m  = evaluar(m2.transform(te2))
print(f"  R²={r2m[0]}  MSE={r2m[1]}  MAE={r2m[2]}")

# ─── MODELO 3 – Ridge (L2) ────────────────────────────────────────────────────
print("=" * 58)
print("MODELO 3 – RIDGE (L2, regParam=0.5, elasticNet=0)")
m3  = LinearRegression(featuresCol="features", labelCol="ingreso_dia",
                       regParam=0.5, elasticNetParam=0.0).fit(tr2)
r3  = evaluar(m3.transform(te2))
print(f"  R²={r3[0]}  MSE={r3[1]}  MAE={r3[2]}")

# ─── MODELO 4 – Lasso (L1) ────────────────────────────────────────────────────
print("=" * 58)
print("MODELO 4 – LASSO (L1, regParam=0.5, elasticNet=1)")
m4  = LinearRegression(featuresCol="features", labelCol="ingreso_dia",
                       regParam=0.5, elasticNetParam=1.0).fit(tr2)
r4  = evaluar(m4.transform(te2))
print(f"  R²={r4[0]}  MSE={r4[1]}  MAE={r4[2]}")

# ─── MODELO 5 – Polinomial (grado 2) ──────────────────────────────────────────
print("=" * 58)
print("MODELO 5 – POLINOMIAL (grado 2 sobre las features múltiples)")
poly = PolynomialExpansion(inputCol="features", outputCol="pf", degree=2)
m5   = LinearRegression(featuresCol="pf", labelCol="ingreso_dia").fit(poly.transform(tr2))
r5   = evaluar(m5.transform(poly.transform(te2)))
print(f"  R²={r5[0]}  MSE={r5[1]}  MAE={r5[2]}")

# ─── MODELO 6 – Cross Validation (búsqueda de hiperparámetros) ────────────────
print("=" * 58)
print("MODELO 6 – CROSS VALIDATION (3-fold, grid regParam × elasticNet)")
lr  = LinearRegression(featuresCol="features", labelCol="ingreso_dia")
grid = (ParamGridBuilder()
        .addGrid(lr.regParam,        [0.01, 0.1, 1.0])
        .addGrid(lr.elasticNetParam, [0.0, 0.5, 1.0])
        .build())
ev  = RegressionEvaluator(labelCol="ingreso_dia", predictionCol="prediction", metricName="r2")
cv  = CrossValidator(estimator=lr, estimatorParamMaps=grid, evaluator=ev, numFolds=3)
cv_model = cv.fit(tr2)
r6  = evaluar(cv_model.transform(te2))
best = cv_model.bestModel
print(f"  Mejor regParam={best.getRegParam()}  elasticNet={best.getElasticNetParam()}")
print(f"  R²={r6[0]}  MSE={r6[1]}  MAE={r6[2]}")

# ─── 4. Tabla comparativa ─────────────────────────────────────────────────────
print("\n" + "=" * 58)
print("COMPARATIVA DE MODELOS (Unidad III — R², MSE, MAE)")
print("=" * 58)
modelos = [
    ("Lineal Simple",    r1), ("Lineal Múltiple", r2m), ("Ridge (L2)",  r3),
    ("Lasso (L1)",       r4), ("Polinomial",      r5),  ("Cross Valid.", r6),
]
print(f"  {'Modelo':<18}{'R²':>10}{'MSE':>14}{'MAE':>12}")
print("  " + "-" * 52)
for nombre, (r2v, mse, mae) in modelos:
    print(f"  {nombre:<18}{r2v:>10}{mse:>14,.0f}{mae:>12,.0f}")

mejor = max(modelos, key=lambda x: x[1][0])
print(f"\nMejor modelo: {mejor[0]}  (R²={mejor[1][0]})")

# ─── 5. Interpretación honesta ────────────────────────────────────────────────
r2_best = mejor[1][0]
print("\nINTERPRETACIÓN:")
if r2_best > 0.85:
    nivel = "EXCELENTE — el volumen y el calendario explican casi toda la facturación."
elif r2_best > 0.65:
    nivel = "BUENO — el modelo captura el patrón principal; queda ruido por la mezcla de servicios."
elif r2_best > 0.40:
    nivel = "MODERADO — hay señal, pero la facturación diaria es intrínsecamente variable."
else:
    nivel = "DÉBIL — se necesitan más variables (promociones, clima, festivos)."
print(f"  R²={r2_best}: {nivel}")
print(f"  Cada cita adicional aporta ~${m1.coefficients[0]:.0f} de facturación (modelo simple).")
print("  A diferencia de predecir el precio de una cita (trivial), predecir la")
print("  facturación diaria es un problema real y defendible.")

graficar(p1, "Regresión: Facturación diaria vs Número de citas")

spark.stop()
print("\nProceso finalizado correctamente")
