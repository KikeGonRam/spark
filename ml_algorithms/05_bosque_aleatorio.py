"""
Unidad III – Análisis Supervisado
Script  : 05_bosque_aleatorio.py
Tema    : Clasificación con Random Forest — predicción de citas canceladas
Métricas: Accuracy, Precision, Recall, F1, AUC-ROC, Importancia de variables
Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Equipo  : Equipo UrbanBlade
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-93
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.sql.functions import when, col
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator

# ─── 1. Cargar datos reales desde MongoDB Atlas ───────────────────────────────
spark, df, _ = get_spark_session()
print("\n===  UNIDAD III – RANDOM FOREST – UrbanBlade  ===\n")

df = df.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})

# ─── 2. Etiqueta: predecir cita CANCELADA ────────────────────────────────────
# Estados reales en barber_db: pendiente, confirmada, en_proceso, completada, cancelada, no_asistio
# Label 1 = cita problemática (cancelada o no_asistio) → permite tomar acción preventiva
df = df.withColumn(
    "categoria",
    when(col("estado").isin("cancelada", "no_asistio"), 1).otherwise(0)
)

print("Distribución de estados reales:")
df.groupBy("estado").count().orderBy("count", ascending=False).show()

print("Distribución de etiqueta (1=cancelada/no_asistio, 0=otras):")
df.groupBy("categoria").count().orderBy("categoria").show()

# ─── 3. Split ─────────────────────────────────────────────────────────────────
train_data, test_data = df.randomSplit([0.7, 0.3], seed=42)
print(f"Entrenamiento: {train_data.count()} | Prueba: {test_data.count()}")

# ─── 4. Pipeline: VectorAssembler → RandomForest ────────────────────────────
assembler = VectorAssembler(
    inputCols=["duracion_min", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="categoria",
    numTrees=100,
    maxDepth=5,
    seed=42
)

pipeline = Pipeline(stages=[assembler, rf])

print("\nEntrenando pipeline Random Forest UrbanBlade...")
model = pipeline.fit(train_data)
print("Pipeline entrenado correctamente")

# ─── 5. Predicciones ──────────────────────────────────────────────────────────
predictions = model.transform(test_data)
print("\nEjemplo de predicciones (10 filas):")
predictions.select(
    "servicio", "duracion_min", "precio", "ingreso",
    "estado", "categoria", "prediction", "probability"
).show(10)

# ─── 6. Evaluación completa ───────────────────────────────────────────────────
auc = BinaryClassificationEvaluator(
    labelCol="categoria", metricName="areaUnderROC"
).evaluate(predictions)

def metric(name):
    return MulticlassClassificationEvaluator(
        labelCol="categoria", predictionCol="prediction", metricName=name
    ).evaluate(predictions)

accuracy  = metric("accuracy")
precision = metric("weightedPrecision")
recall    = metric("weightedRecall")
f1        = metric("f1")

print("\n" + "=" * 52)
print("MÉTRICAS DE EVALUACIÓN – RANDOM FOREST (100 árboles)")
print("=" * 52)
print(f"  Accuracy           : {accuracy:.4f}  ({accuracy*100:.1f}%)")
print(f"  Precision (weighted): {precision:.4f}")
print(f"  Recall (weighted)  : {recall:.4f}")
print(f"  F1-Score (weighted): {f1:.4f}")
print(f"  AUC-ROC            : {auc:.4f}")

# ─── 7. Comparación predicción vs real ────────────────────────────────────────
print("\nCOMPARACIÓN PREDICCIÓN vs REAL (Matriz de confusión):")
predictions.groupBy("categoria", "prediction").count().orderBy("categoria", "prediction").show()

# ─── 8. Importancia de variables ──────────────────────────────────────────────
rf_model  = model.stages[-1]
nombres   = ["duracion_min", "precio", "ingreso"]
importancias = rf_model.featureImportances

print("IMPORTANCIA DE VARIABLES:")
for nombre, imp in zip(nombres, importancias):
    barra = "█" * int(imp * 50)
    print(f"  {nombre:<15} {imp:.4f}  ({imp*100:.1f}%)  {barra}")

# ─── 9. Guardar modelo ────────────────────────────────────────────────────────
model.write().overwrite().save("modelo_pipeline_rf_urbanblade")
print("\nModelo guardado en: modelo_pipeline_rf_urbanblade/")

# ─── 10. Interpretación ──────────────────────────────────────────────────────
print("\nINTERPRETACIÓN:")
var_mas_importante = nombres[list(importancias).index(max(importancias))]
print(f"  Variable más importante: '{var_mas_importante}' ({max(importancias)*100:.1f}%)")
if auc > 0.85:
    print(f"  AUC={auc:.2f}: el modelo discrimina EXCELENTEMENTE entre citas normales y canceladas.")
elif auc > 0.70:
    print(f"  AUC={auc:.2f}: el modelo tiene BUENA capacidad para identificar cancelaciones.")
else:
    print(f"  AUC={auc:.2f}: el modelo tiene capacidad MODERADA. Considerar más features.")
print(f"  Con {accuracy*100:.1f}% de accuracy, el modelo puede ayudar a anticipar")
print("  cancelaciones y optimizar la agenda de la barbería.")

spark.stop()
print("Sesión Spark finalizada")
