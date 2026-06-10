import sys
import os
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
    pdf = predictions.select("duracion_min", "ingreso", "prediction").toPandas()
    plt.figure()
    plt.scatter(pdf["duracion_min"], pdf["ingreso"],    label="Real")
    plt.scatter(pdf["duracion_min"], pdf["prediction"], label="Predicción")
    plt.title(titulo)
    plt.xlabel("Duración del Servicio (min)")
    plt.ylabel("Ingreso ($)")
    plt.legend()
    plt.show()


# MODELO 1 – Regresión Lineal Simple
print("MODELO 1 REGRESIÓN LINEAL SIMPLE")
a_simple  = VectorAssembler(inputCols=["duracion_min"], outputCol="features")
tr_simple = a_simple.transform(train)
te_simple = a_simple.transform(test)
m1 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr_simple)
p1 = m1.transform(te_simple)
r2_simple = evaluator.evaluate(p1)
print("R2:", r2_simple)
graficar(p1, "Regresión Lineal Simple – UrbanBlade")

# MODELO 2 – Regresión Lineal Múltiple
print("MODELO 2 REGRESIÓN LINEAL MÚLTIPLE")
a_mult  = VectorAssembler(inputCols=["duracion_min", "precio"], outputCol="features")
tr_mult = a_mult.transform(train)
te_mult = a_mult.transform(test)
m2 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr_mult)
p2 = m2.transform(te_mult)
r2_multiple = evaluator.evaluate(p2)
print("R2:", r2_multiple)
graficar(p2, "Regresión Lineal Múltiple – UrbanBlade")

# MODELO 3 – Ridge
print("MODELO 3 RIDGE REGRESSION")
m3 = LinearRegression(featuresCol="features", labelCol="ingreso",
                      regParam=0.5, elasticNetParam=0).fit(tr_mult)
p3 = m3.transform(te_mult)
r2_ridge = evaluator.evaluate(p3)
print("R2:", r2_ridge)
graficar(p3, "Ridge Regression – UrbanBlade")

# MODELO 4 – Lasso
print("MODELO 4 LASSO REGRESSION")
m4 = LinearRegression(featuresCol="features", labelCol="ingreso",
                      regParam=0.5, elasticNetParam=1).fit(tr_mult)
p4 = m4.transform(te_mult)
r2_lasso = evaluator.evaluate(p4)
print("R2:", r2_lasso)
graficar(p4, "Lasso Regression – UrbanBlade")

# MODELO 5 – Regresión Polinómica
print("MODELO 5 REGRESIÓN POLINÓMICA")
poly    = PolynomialExpansion(inputCol="features", outputCol="poly_features", degree=2)
tr_poly = poly.transform(tr_mult)
te_poly = poly.transform(te_mult)
m5  = LinearRegression(featuresCol="poly_features", labelCol="ingreso").fit(tr_poly)
p5  = m5.transform(te_poly)
r2_poly = evaluator.evaluate(p5)
print("R2:", r2_poly)
graficar(p5, "Regresión Polinómica – UrbanBlade")

# MODELO 6 – Cross Validation
print("MODELO 6 CROSS VALIDATION")
lr_cv      = LinearRegression(featuresCol="features", labelCol="ingreso")
paramGrid  = ParamGridBuilder() \
    .addGrid(lr_cv.regParam, [0.01, 0.1, 1]) \
    .addGrid(lr_cv.elasticNetParam, [0, 0.5, 1]) \
    .build()
cv   = CrossValidator(estimator=lr_cv, estimatorParamMaps=paramGrid,
                      evaluator=evaluator, numFolds=3)
m6   = cv.fit(tr_mult)
p6   = m6.transform(te_mult)
r2_cv = evaluator.evaluate(p6)
print("R2:", r2_cv)
graficar(p6, "Cross Validation – UrbanBlade")

# COMPARACIÓN FINAL
print("COMPARACIÓN FINAL")
resultados = {
    "Lineal Simple":    r2_simple,
    "Lineal Múltiple":  r2_multiple,
    "Ridge":            r2_ridge,
    "Lasso":            r2_lasso,
    "Polinomial":       r2_poly,
    "Cross Validation": r2_cv
}
for k, v in resultados.items():
    print(k, "→", round(v, 4))

mejor = max(resultados, key=resultados.get)
print("MEJOR MODELO:", mejor)

spark.stop()
