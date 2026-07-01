"""
Unidad III – Análisis Supervisado
Script  : 03_regresion_analytics.py
Tema    : 6 modelos de regresión con evaluación completa (R², MSE, MAE)
Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Equipo  : Equipo UrbanBlade
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-93
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.feature import VectorAssembler, PolynomialExpansion
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import matplotlib.pyplot as plt

# ─── 1. Cargar datos reales desde MongoDB Atlas ───────────────────────────────
spark, df, _ = get_spark_session()
print("\n===  UNIDAD III – ANÁLISIS SUPERVISADO – UrbanBlade  ===\n")
print("Muestra del dataset:")
df.select("servicio", "barbero", "duracion_min", "precio", "ingreso", "estado").show(10)

# ─── 2. Train/test split ──────────────────────────────────────────────────────
train, test = df.randomSplit([0.8, 0.2], seed=42)
print(f"Entrenamiento: {train.count()} registros  |  Prueba: {test.count()} registros\n")

# ─── 3. Evaluadores (R², MSE, MAE) ───────────────────────────────────────────
# Unidad III exige reportar Error Cuadrático Medio (MSE) y Error Absoluto Medio (MAE)
def evaluar(predictions, label="ingreso"):
    r2  = RegressionEvaluator(labelCol=label, predictionCol="prediction", metricName="r2").evaluate(predictions)
    mse = RegressionEvaluator(labelCol=label, predictionCol="prediction", metricName="mse").evaluate(predictions)
    mae = RegressionEvaluator(labelCol=label, predictionCol="prediction", metricName="mae").evaluate(predictions)
    return r2, mse, mae


def graficar(predictions, titulo):
    pdf = predictions.select("duracion_min", "ingreso", "prediction").toPandas()
    plt.figure(figsize=(8, 5))
    plt.scatter(pdf["duracion_min"], pdf["ingreso"],    label="Real",      alpha=0.6, color="steelblue")
    plt.scatter(pdf["duracion_min"], pdf["prediction"], label="Predicción", alpha=0.6, color="tomato", marker="x")
    plt.title(titulo)
    plt.xlabel("Duración del Servicio (min)")
    plt.ylabel("Ingreso ($MXN)")
    plt.legend()
    plt.tight_layout()
    plt.show()


# ─── MODELO 1 – Regresión Lineal Simple ───────────────────────────────────────
print("=" * 55)
print("MODELO 1 – REGRESIÓN LINEAL SIMPLE")
print("  Feature: duracion_min → predice ingreso")
a_simple  = VectorAssembler(inputCols=["duracion_min"], outputCol="features", handleInvalid="skip")
tr_simple = a_simple.transform(train)
te_simple = a_simple.transform(test)
m1 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr_simple)
p1 = m1.transform(te_simple)
r2_1, mse_1, mae_1 = evaluar(p1)
print(f"  R²={r2_1:.4f}  MSE={mse_1:.2f}  MAE={mae_1:.2f}")
graficar(p1, "Regresión Lineal Simple – UrbanBlade")

# ─── MODELO 2 – Regresión Lineal Múltiple ─────────────────────────────────────
print("=" * 55)
print("MODELO 2 – REGRESIÓN LINEAL MÚLTIPLE")
print("  Features: duracion_min + precio → predice ingreso")
a_mult  = VectorAssembler(inputCols=["duracion_min", "precio"], outputCol="features", handleInvalid="skip")
tr_mult = a_mult.transform(train)
te_mult = a_mult.transform(test)
m2 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr_mult)
p2 = m2.transform(te_mult)
r2_2, mse_2, mae_2 = evaluar(p2)
print(f"  R²={r2_2:.4f}  MSE={mse_2:.2f}  MAE={mae_2:.2f}")
graficar(p2, "Regresión Lineal Múltiple – UrbanBlade")

# ─── MODELO 3 – Ridge (L2) ────────────────────────────────────────────────────
print("=" * 55)
print("MODELO 3 – RIDGE REGRESSION  (regParam=0.5, elasticNetParam=0)")
m3 = LinearRegression(featuresCol="features", labelCol="ingreso",
                      regParam=0.5, elasticNetParam=0).fit(tr_mult)
p3 = m3.transform(te_mult)
r2_3, mse_3, mae_3 = evaluar(p3)
print(f"  R²={r2_3:.4f}  MSE={mse_3:.2f}  MAE={mae_3:.2f}")
graficar(p3, "Ridge Regression – UrbanBlade")

# ─── MODELO 4 – Lasso (L1) ───────────────────────────────────────────────────
print("=" * 55)
print("MODELO 4 – LASSO REGRESSION  (regParam=0.5, elasticNetParam=1)")
m4 = LinearRegression(featuresCol="features", labelCol="ingreso",
                      regParam=0.5, elasticNetParam=1).fit(tr_mult)
p4 = m4.transform(te_mult)
r2_4, mse_4, mae_4 = evaluar(p4)
print(f"  R²={r2_4:.4f}  MSE={mse_4:.2f}  MAE={mae_4:.2f}")
graficar(p4, "Lasso Regression – UrbanBlade")

# ─── MODELO 5 – Regresión Polinómica (grado 2) ───────────────────────────────
print("=" * 55)
print("MODELO 5 – REGRESIÓN POLINÓMICA  (degree=2)")
poly    = PolynomialExpansion(inputCol="features", outputCol="poly_features", degree=2)
tr_poly = poly.transform(tr_mult)
te_poly = poly.transform(te_mult)
m5 = LinearRegression(featuresCol="poly_features", labelCol="ingreso").fit(tr_poly)
p5 = m5.transform(te_poly)
r2_5, mse_5, mae_5 = evaluar(p5)
print(f"  R²={r2_5:.4f}  MSE={mse_5:.2f}  MAE={mae_5:.2f}")
graficar(p5, "Regresión Polinómica – UrbanBlade")

# ─── MODELO 6 – Cross Validation ─────────────────────────────────────────────
print("=" * 55)
print("MODELO 6 – CROSS VALIDATION  (3-fold, regParam & elasticNetParam grid)")
ev_cv     = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="r2")
lr_cv     = LinearRegression(featuresCol="features", labelCol="ingreso")
paramGrid = ParamGridBuilder() \
    .addGrid(lr_cv.regParam,        [0.01, 0.1, 1]) \
    .addGrid(lr_cv.elasticNetParam, [0, 0.5, 1]) \
    .build()
cv  = CrossValidator(estimator=lr_cv, estimatorParamMaps=paramGrid,
                     evaluator=ev_cv, numFolds=3)
m6  = cv.fit(tr_mult)
p6  = m6.transform(te_mult)
r2_6, mse_6, mae_6 = evaluar(p6)
print(f"  R²={r2_6:.4f}  MSE={mse_6:.2f}  MAE={mae_6:.2f}")
graficar(p6, "Cross Validation – UrbanBlade")

# ─── 4. COMPARACIÓN FINAL ────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("COMPARACIÓN FINAL DE MODELOS – UNIDAD III")
print("=" * 65)
print(f"{'Modelo':<25} {'R²':>8} {'MSE':>12} {'MAE':>10}")
print("-" * 65)
modelos = [
    ("Lineal Simple",    r2_1, mse_1, mae_1),
    ("Lineal Múltiple",  r2_2, mse_2, mae_2),
    ("Ridge",            r2_3, mse_3, mae_3),
    ("Lasso",            r2_4, mse_4, mae_4),
    ("Polinomial",       r2_5, mse_5, mae_5),
    ("Cross Validation", r2_6, mse_6, mae_6),
]
for nombre, r2, mse, mae in modelos:
    print(f"  {nombre:<23} {r2:>8.4f} {mse:>12.2f} {mae:>10.2f}")

mejor = max(modelos, key=lambda x: x[1])
print("-" * 65)
print(f"\n  Mejor modelo (mayor R²): {mejor[0]}")
print(f"    R²  = {mejor[1]:.4f}  (% varianza explicada)")
print(f"    MSE = {mejor[2]:.2f}   (Error Cuadrático Medio en $²)")
print(f"    MAE = {mejor[3]:.2f}   (Error Absoluto Medio en $MXN)")

# ─── 5. INTERPRETACIÓN AUTOMÁTICA ────────────────────────────────────────────
print("\nINTERPRETACIÓN:")
for nombre, r2, mse, mae in modelos:
    if r2 > 0.85:
        nivel = "Excelente ajuste"
    elif r2 > 0.65:
        nivel = "Buen ajuste"
    elif r2 > 0.40:
        nivel = "Ajuste moderado"
    else:
        nivel = "Ajuste débil"
    print(f"  {nombre:<25}: {nivel} (R²={r2:.2f}, MAE=${mae:.0f})")

spark.stop()
print("\nSesión Spark finalizada")
