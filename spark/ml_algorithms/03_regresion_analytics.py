import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.feature import VectorAssembler, PolynomialExpansion
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import matplotlib.pyplot as plt

spark, df, _ = get_spark_session()
print("Dataset UrbanBlade cargado")
df.show()

train, test = df.randomSplit([0.8, 0.2], seed=42)

evaluator = RegressionEvaluator(
    labelCol="ingreso",
    predictionCol="prediction",
    metricName="r2"
)


def graficar(predictions, titulo):
    pdf = predictions.select("cantidad", "ingreso", "prediction").toPandas()
    plt.figure()
    plt.scatter(pdf["cantidad"], pdf["ingreso"],    label="Real",      color="#4ade80")
    plt.scatter(pdf["cantidad"], pdf["prediction"], label="Predicción", color="#d4af37")
    plt.title(titulo)
    plt.xlabel("Cantidad de Servicios")
    plt.ylabel("Ingreso ($)")
    plt.legend()
    plt.tight_layout()
    plt.show()


# MODELO 1 – Regresión Lineal Simple
print("\nMODELO 1 – REGRESIÓN LINEAL SIMPLE")
a_simple  = VectorAssembler(inputCols=["cantidad"], outputCol="features", handleInvalid="skip")
tr_simple = a_simple.transform(train)
te_simple = a_simple.transform(test)
m1 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr_simple)
p1 = m1.transform(te_simple)
r2_simple = evaluator.evaluate(p1)
print("R2:", round(r2_simple, 4))
graficar(p1, "Regresión Lineal Simple – UrbanBlade")

# MODELO 2 – Regresión Lineal Múltiple
print("\nMODELO 2 – REGRESIÓN LINEAL MÚLTIPLE")
a_mult  = VectorAssembler(inputCols=["cantidad", "precio"], outputCol="features", handleInvalid="skip")
tr_mult = a_mult.transform(train)
te_mult = a_mult.transform(test)
m2 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr_mult)
p2 = m2.transform(te_mult)
r2_multiple = evaluator.evaluate(p2)
print("R2:", round(r2_multiple, 4))
graficar(p2, "Regresión Lineal Múltiple – UrbanBlade")

# MODELO 3 – Ridge Regression
print("\nMODELO 3 – RIDGE REGRESSION")
m3 = LinearRegression(featuresCol="features", labelCol="ingreso",
                      regParam=0.5, elasticNetParam=0).fit(tr_mult)
p3 = m3.transform(te_mult)
r2_ridge = evaluator.evaluate(p3)
print("R2:", round(r2_ridge, 4))
graficar(p3, "Ridge Regression – UrbanBlade")

# MODELO 4 – Lasso Regression
print("\nMODELO 4 – LASSO REGRESSION")
m4 = LinearRegression(featuresCol="features", labelCol="ingreso",
                      regParam=0.5, elasticNetParam=1).fit(tr_mult)
p4 = m4.transform(te_mult)
r2_lasso = evaluator.evaluate(p4)
print("R2:", round(r2_lasso, 4))
graficar(p4, "Lasso Regression – UrbanBlade")

# MODELO 5 – Regresión Polinómica (grado 2)
print("\nMODELO 5 – REGRESIÓN POLINÓMICA")
poly    = PolynomialExpansion(inputCol="features", outputCol="poly_features", degree=2)
tr_poly = poly.transform(tr_mult)
te_poly = poly.transform(te_mult)
m5  = LinearRegression(featuresCol="poly_features", labelCol="ingreso").fit(tr_poly)
p5  = m5.transform(te_poly)
r2_poly = evaluator.evaluate(p5)
print("R2:", round(r2_poly, 4))
graficar(p5, "Regresión Polinómica – UrbanBlade")

# MODELO 6 – Cross Validation
print("\nMODELO 6 – CROSS VALIDATION")
lr_cv     = LinearRegression(featuresCol="features", labelCol="ingreso")
paramGrid = ParamGridBuilder() \
    .addGrid(lr_cv.regParam, [0.01, 0.1, 1]) \
    .addGrid(lr_cv.elasticNetParam, [0, 0.5, 1]) \
    .build()
cv    = CrossValidator(estimator=lr_cv, estimatorParamMaps=paramGrid,
                       evaluator=evaluator, numFolds=3)
m6    = cv.fit(tr_mult)
p6    = m6.transform(te_mult)
r2_cv = evaluator.evaluate(p6)
print("R2:", round(r2_cv, 4))
graficar(p6, "Cross Validation – UrbanBlade")

# COMPARACIÓN FINAL
print("\n=== COMPARACIÓN FINAL DE MODELOS ===")
resultados = {
    "Lineal Simple":    r2_simple,
    "Lineal Múltiple":  r2_multiple,
    "Ridge":            r2_ridge,
    "Lasso":            r2_lasso,
    "Polinomial":       r2_poly,
    "Cross Validation": r2_cv
}
for modelo, r2 in resultados.items():
    print(f"  {modelo:20s} → R2: {round(r2, 4)}")

mejor = max(resultados, key=resultados.get)
print(f"\nMEJOR MODELO: {mejor} (R2 = {round(resultados[mejor], 4)})")

spark.stop()
