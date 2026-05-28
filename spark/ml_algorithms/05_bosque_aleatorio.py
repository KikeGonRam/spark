import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import when, col
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator

spark, df, _ = get_spark_session()

df = df.fillna({"cantidad": 0, "precio": 0, "ingreso": 0})

# Label: cita cancelada = 1, completada/pendiente = 0
df = df.withColumn(
    "categoria",
    when(col("estado") == "cancelada", 1).otherwise(0)
)

train_data, test_data = df.randomSplit([0.7, 0.3], seed=42)

assembler = VectorAssembler(
    inputCols=["cantidad", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="categoria",
    numTrees=50,
    maxDepth=5,
    seed=42
)

pipeline = Pipeline(stages=[assembler, rf])

print("\nEntrenando pipeline Random Forest UrbanBlade...")
model = pipeline.fit(train_data)
print("Pipeline entrenado correctamente")

predictions = model.transform(test_data)
print("\nEjemplo de predicciones:")
predictions.select(
    "servicio", "cantidad", "precio", "ingreso",
    "prediction", "categoria", "probability"
).show(10)

auc = BinaryClassificationEvaluator(
    labelCol="categoria", metricName="areaUnderROC"
).evaluate(predictions)
print(f"\nAUC del modelo: {round(auc, 4)}")

if auc >= 0.85:
    print("Excelente capacidad de discriminación")
elif auc >= 0.70:
    print("Buena capacidad de discriminación")
else:
    print("Capacidad de discriminación baja")

print("\nComparación predicción vs real:")
predictions.groupBy("categoria", "prediction").count().show()

rf_model = model.stages[-1]
print("\nImportancia de variables:")
nombres = ["cantidad", "precio", "ingreso"]
for nombre, imp in zip(nombres, rf_model.featureImportances):
    print(f"  {nombre}: {round(imp, 4)}")

model.write().overwrite().save("modelo_pipeline_rf_urbanblade")
print("\nModelo guardado en 'modelo_pipeline_rf_urbanblade'")

spark.stop()
print("Sesión Spark finalizada")
