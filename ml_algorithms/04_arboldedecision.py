"""
Unidad III – Análisis Supervisado
Script  : 04_arboldedecision.py
Tema    : Clasificación con Árbol de Decisión — citas de alto valor (ingreso > $500 MXN)
Métricas: Accuracy, Precision, Recall, F1-Score  (requeridas Unidad III)
Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Equipo  : Equipo UrbanBlade
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-93
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql.functions import when, col
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
from config.mongo_spark_conexion_sinnulos import get_spark_session

# ─── 1. Cargar datos reales desde MongoDB Atlas ───────────────────────────────
spark, df, df_vector = get_spark_session()
print("\n===  UNIDAD III – ÁRBOL DE DECISIÓN – UrbanBlade  ===\n")
print("Dataset original:")
df.select("servicio", "barbero", "duracion_min", "precio", "ingreso", "estado").show(10)

# ─── 2. Etiqueta de clasificación ────────────────────────────────────────────
# Cita de ALTO VALOR (ingreso > $500 MXN) = 1  |  BAJO VALOR = 0
# Umbral de $500: divide bien servicios básicos (corte ~$200) de premium (corte+barba ~$600+)
UMBRAL = 500
df = df.withColumn(
    "label",
    when(col("ingreso") > UMBRAL, 1).otherwise(0)
)

print(f"\nDistribución de clases (umbral ingreso > ${UMBRAL} MXN):")
df.groupBy("label").count().orderBy("label").show()

df = df.dropna(subset=["duracion_min", "precio", "ingreso"])

# ─── 3. Vectorización ────────────────────────────────────────────────────────
assembler = VectorAssembler(
    inputCols=["duracion_min", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)
df_ml   = assembler.transform(df)
dataset = df_ml.select("features", "label")

train_data, test_data = dataset.randomSplit([0.8, 0.2], seed=42)
print(f"Entrenamiento: {train_data.count()} | Prueba: {test_data.count()}")

# ─── 4. Entrenamiento ─────────────────────────────────────────────────────────
dt    = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=5)
model = dt.fit(train_data)

print("\nEstructura del árbol de decisión:")
print(model.toDebugString)

# ─── 5. Predicciones ──────────────────────────────────────────────────────────
predictions = model.transform(test_data)
print("\nEjemplo de predicciones:")
predictions.select("features", "label", "prediction", "probability").show(10)

# ─── 6. Evaluación completa – Unidad III requiere MSE/MAE para regresión;
#         para clasificación: Accuracy, Precision, Recall, F1 ─────────────────
def metric(name):
    return MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName=name
    ).evaluate(predictions)

accuracy  = metric("accuracy")
precision = metric("weightedPrecision")
recall    = metric("weightedRecall")
f1        = metric("f1")
auc       = BinaryClassificationEvaluator(
    labelCol="label", metricName="areaUnderROC"
).evaluate(predictions)

print("\n" + "=" * 50)
print("MÉTRICAS DE EVALUACIÓN – ÁRBOL DE DECISIÓN")
print("=" * 50)
print(f"  Accuracy           : {accuracy:.4f}  ({accuracy*100:.1f}%)")
print(f"  Precision (weighted): {precision:.4f}")
print(f"  Recall (weighted)  : {recall:.4f}")
print(f"  F1-Score (weighted): {f1:.4f}")
print(f"  AUC-ROC            : {auc:.4f}")

# ─── 7. Matriz de confusión ────────────────────────────────────────────────────
print("\nMATRIZ DE CONFUSIÓN:")
print("  label=0 → ingreso ≤ $500  |  label=1 → ingreso > $500")
predictions.groupBy("label", "prediction").count().orderBy("label", "prediction").show()

# ─── 8. Importancia de variables ──────────────────────────────────────────────
nombres  = ["duracion_min", "precio", "ingreso"]
importancias = model.featureImportances
print("IMPORTANCIA DE VARIABLES:")
for nombre, imp in zip(nombres, importancias):
    barra = "█" * int(imp * 40)
    print(f"  {nombre:<15} {imp:.4f}  {barra}")

# ─── 9. Interpretación ───────────────────────────────────────────────────────
print("\nINTERPRETACIÓN:")
if accuracy > 0.85:
    print(f"  Árbol de decisión con EXCELENTE precisión ({accuracy*100:.1f}%)")
elif accuracy > 0.70:
    print(f"  Árbol de decisión con BUENA precisión ({accuracy*100:.1f}%)")
else:
    print(f"  Árbol de decisión con precisión MODERADA ({accuracy*100:.1f}%)")

print(f"  F1-Score de {f1:.2f} indica balance entre precisión y recall.")
print(f"  AUC={auc:.2f}: {'excelente' if auc > 0.9 else 'buena' if auc > 0.75 else 'moderada'} "
      f"capacidad discriminativa del modelo.")

spark.stop()
print("\nSesión Spark finalizada")
