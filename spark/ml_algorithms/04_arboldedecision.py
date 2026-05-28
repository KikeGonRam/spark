import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyspark.sql.functions import when, col
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from config.mongo_spark_conexion_sinnulos import get_spark_session

spark, df, df_vector = get_spark_session()
print("\nDataset UrbanBlade original")
df.show()

# Etiqueta: cita de ALTO VALOR (ingreso > 500) = 1, BAJO = 0
df = df.withColumn(
    "label",
    when(col("ingreso") > 500, 1).otherwise(0)
)

print("\nDataset con etiqueta de valor")
df.select("servicio", "cantidad", "precio", "ingreso", "label").show()

df = df.dropna(subset=["cantidad", "precio", "ingreso"])

assembler = VectorAssembler(
    inputCols=["cantidad", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)
df_ml   = assembler.transform(df)
dataset = df_ml.select("features", "label")

train_data, test_data = dataset.randomSplit([0.8, 0.2], seed=42)
print(f"\nDatos de entrenamiento: {train_data.count()}")
print(f"Datos de prueba:        {test_data.count()}")

dt    = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=3)
model = dt.fit(train_data)

print("\nEstructura del Árbol de Decisión:\n")
print(model.toDebugString)

predictions = model.transform(test_data)
print("\nPredicciones (muestra):")
predictions.select("features", "label", "prediction").show(10)

accuracy = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="accuracy"
).evaluate(predictions)
print(f"\nAccuracy del modelo: {round(accuracy * 100, 2)}%")

if accuracy >= 0.85:
    print("Modelo con alta precisión")
elif accuracy >= 0.70:
    print("Modelo aceptable")
else:
    print("Modelo con baja precisión — revisar datos")

spark.stop()
