"""
Unidad III – Análisis Supervisado (Clasificación con ensemble)
Script  : 05_bosque_aleatorio.py
Tema    : Random Forest — predicción de citas CANCELADAS (mejora al árbol 04)

  PROBLEMA DE NEGOCIO: mismo que el script 04 (anticipar cancelaciones), pero
  ahora con un BOSQUE de 100 árboles. Comparamos "un árbol vs muchos árboles":
  el ensemble suele mejorar el AUC y es más robusto al ruido.

  Target  : es_cancelada  (1 = cancelada, 0 = resto)
  Features: duracion_min, precio, hora, dia_semana, mes   (SIN fuga de datos)

  Nota: en barber_db los estados reales son {cancelada, completada, confirmada,
  pendiente} — NO existe 'no_asistio'. Solo 'cancelada' representa pérdida.

Métricas: Accuracy, Precision, Recall, F1, AUC-ROC, Importancia de variables
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

from config.mongo_spark_conexion_sinnulos import get_spark_session, FEATURES_CANCEL
from pyspark.sql.functions import col
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator

# ─── 1. Cargar datos reales ───────────────────────────────────────────────────
spark, df, _ = get_spark_session()
print("\n===  UNIDAD III – RANDOM FOREST (cancelación) – UrbanBlade  ===\n")

print("Distribución de estados reales:")
df.groupBy("estado").count().orderBy("count", ascending=False).show()

df = df.withColumn("label", col("es_cancelada").cast("double"))
print("Distribución de la etiqueta (1=cancelada, 0=resto):")
df.groupBy("label").count().orderBy("label").show()

# ─── 2. Split ─────────────────────────────────────────────────────────────────
train_data, test_data = df.randomSplit([0.7, 0.3], seed=42)
print(f"Entrenamiento: {train_data.count()} | Prueba: {test_data.count()}")
print(f"Features: {FEATURES_CANCEL}\n")

# ─── 3. Pipeline: VectorAssembler → RandomForest ────────────────────────────
assembler = VectorAssembler(inputCols=FEATURES_CANCEL, outputCol="features",
                            handleInvalid="skip")
rf = RandomForestClassifier(featuresCol="features", labelCol="label",
                            numTrees=100, maxDepth=5, seed=42)
pipeline = Pipeline(stages=[assembler, rf])

print("Entrenando bosque de 100 árboles...")
model = pipeline.fit(train_data)
print("Pipeline entrenado correctamente")

# ─── 4. Predicciones ──────────────────────────────────────────────────────────
predictions = model.transform(test_data)
print("\nEjemplo de predicciones (10 filas):")
predictions.select("servicio", "hora", "dia_semana", "precio",
                   "estado", "label", "prediction").show(10)

# ─── 5. Evaluación completa ───────────────────────────────────────────────────
auc = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC").evaluate(predictions)

def metric(name):
    return MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName=name).evaluate(predictions)

accuracy, precision, recall, f1 = (metric("accuracy"), metric("weightedPrecision"),
                                   metric("weightedRecall"), metric("f1"))

print("\n" + "=" * 52)
print("MÉTRICAS DE EVALUACIÓN – RANDOM FOREST (100 árboles)")
print("=" * 52)
print(f"  Accuracy            : {accuracy:.4f}  ({accuracy*100:.1f}%)")
print(f"  Precision (weighted): {precision:.4f}")
print(f"  Recall (weighted)   : {recall:.4f}")
print(f"  F1-Score (weighted) : {f1:.4f}")
print(f"  AUC-ROC             : {auc:.4f}   ← comparar contra el árbol del script 04")

# ─── 6. Matriz de confusión ───────────────────────────────────────────────────
print("\nMatriz de confusión (label vs predicción):")
predictions.groupBy("label", "prediction").count().orderBy("label", "prediction").show()

# ─── 7. Importancia de variables ──────────────────────────────────────────────
rf_model     = model.stages[-1]
importancias = rf_model.featureImportances
print("IMPORTANCIA DE VARIABLES:")
for nombre, imp in sorted(zip(FEATURES_CANCEL, importancias), key=lambda x: -x[1]):
    barra = "█" * int(imp * 50)
    print(f"  {nombre:<14} {imp:.4f}  ({imp*100:.1f}%)  {barra}")

# ─── 8. Guardar modelo ────────────────────────────────────────────────────────
model.write().overwrite().save("modelo_pipeline_rf_urbanblade")
print("\nModelo guardado en: modelo_pipeline_rf_urbanblade/")

# ─── 9. Interpretación ────────────────────────────────────────────────────────
var_mas = max(zip(FEATURES_CANCEL, importancias), key=lambda x: x[1])
print("\nINTERPRETACIÓN:")
print(f"  Variable más importante: '{var_mas[0]}' ({var_mas[1]*100:.1f}%)")
if auc > 0.75:
    print(f"  AUC={auc:.2f}: el bosque discrimina MUY BIEN citas normales vs canceladas.")
elif auc > 0.65:
    print(f"  AUC={auc:.2f}: BUENA capacidad para anticipar cancelaciones.")
else:
    print(f"  AUC={auc:.2f}: capacidad MODERADA — el ensemble aún supera al árbol simple.")
print("  El bosque promedia 100 árboles → menos sobreajuste que el árbol único (04).")
print("  Aplicación: sobre-reservar o confirmar activamente las citas de mayor riesgo.")

spark.stop()
print("Sesión Spark finalizada")
