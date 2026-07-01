"""
Unidad III – Análisis Supervisado (Clasificación)
Script  : 04_arboldedecision.py
Tema    : Árbol de Decisión — ¿se CANCELARÁ esta cita?

  PROBLEMA DE NEGOCIO: anticipar cancelaciones para reducir huecos en la agenda.
  Target  : es_cancelada  (1 = cancelada, 0 = resto)
  Features: duracion_min, precio, hora, dia_semana, mes   (SIN fuga — el estado
            NO se usa como feature; se predice desde el contexto de la cita)

  Metodología: un árbol es interpretable → mostramos sus reglas y la importancia
  de cada variable. En el script 05 el mismo problema se resuelve con un BOSQUE
  (ensemble) para comparar "un árbol vs muchos árboles".

Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Equipo  : Equipo UrbanBlade
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-93
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session, FEATURES_CANCEL
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import (
    MulticlassClassificationEvaluator, BinaryClassificationEvaluator
)
from pyspark.sql.functions import col

# ─── 1. Cargar datos reales ───────────────────────────────────────────────────
spark, df, _ = get_spark_session()
print("\n===  UNIDAD III – ÁRBOL DE DECISIÓN (cancelación) – UrbanBlade  ===\n")

print("Distribución real de la etiqueta (es_cancelada):")
df.groupBy("es_cancelada").count().orderBy("es_cancelada").show()
tot   = df.count()
canc  = df.filter(col("es_cancelada") == 1).count()
print(f"  Tasa de cancelación real: {canc/tot*100:.1f}%  "
      f"(clases desbalanceadas → AUC es más informativo que accuracy)\n")

# ─── 2. Features honestas (contexto de la cita, NO el estado) ────────────────
asm = VectorAssembler(inputCols=FEATURES_CANCEL, outputCol="features", handleInvalid="skip")
ds  = asm.transform(df).select("features", col("es_cancelada").alias("label"),
                               *FEATURES_CANCEL)
train, test = ds.randomSplit([0.8, 0.2], seed=42)
print(f"Features: {FEATURES_CANCEL}")
print(f"Entrenamiento: {train.count()}  |  Prueba: {test.count()}\n")

# ─── 3. Entrenar Árbol de Decisión ────────────────────────────────────────────
arbol = DecisionTreeClassifier(featuresCol="features", labelCol="label",
                               maxDepth=5, seed=42)
model = arbol.fit(train)
preds = model.transform(test)

# ─── 4. Métricas ──────────────────────────────────────────────────────────────
def m(metric):
    return MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName=metric).evaluate(preds)

acc  = m("accuracy")
prec = m("weightedPrecision")
rec  = m("weightedRecall")
f1   = m("f1")
auc  = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC").evaluate(preds)

print("=" * 52)
print("MÉTRICAS DE EVALUACIÓN – ÁRBOL DE DECISIÓN")
print("=" * 52)
print(f"  Accuracy            : {acc:.4f}  ({acc*100:.1f}%)")
print(f"  Precision (weighted): {prec:.4f}")
print(f"  Recall (weighted)   : {rec:.4f}")
print(f"  F1-Score (weighted) : {f1:.4f}")
print(f"  AUC-ROC             : {auc:.4f}   ← métrica clave con clases desbalanceadas")

# ─── 5. Matriz de confusión ───────────────────────────────────────────────────
print("\nMatriz de confusión (label vs predicción):")
preds.groupBy("label", "prediction").count().orderBy("label", "prediction").show()

# ─── 6. Importancia de variables ──────────────────────────────────────────────
print("IMPORTANCIA DE VARIABLES (qué predice mejor la cancelación):")
importancias = list(model.featureImportances)
for nombre, imp in sorted(zip(FEATURES_CANCEL, importancias), key=lambda x: -x[1]):
    barra = "█" * int(imp * 40)
    print(f"  {nombre:<14} {imp:.4f}  {barra}")

# ─── 7. Reglas del árbol (interpretabilidad) ─────────────────────────────────
print("\nREGLAS APRENDIDAS (primeros niveles del árbol):")
reglas = model.toDebugString.splitlines()
for linea in reglas[:22]:
    print("  " + linea)
if len(reglas) > 22:
    print(f"  … ({len(reglas)-22} líneas más)")

# ─── 8. Interpretación ────────────────────────────────────────────────────────
var_top = max(zip(FEATURES_CANCEL, importancias), key=lambda x: x[1])
print("\nINTERPRETACIÓN:")
print(f"  Variable más predictiva: '{var_top[0]}' ({var_top[1]*100:.1f}%).")
if auc > 0.70:
    print(f"  AUC={auc:.2f}: el árbol distingue BIEN las citas con riesgo de cancelación.")
elif auc > 0.60:
    print(f"  AUC={auc:.2f}: capacidad MODERADA — útil como alerta temprana.")
else:
    print(f"  AUC={auc:.2f}: señal DÉBIL — la cancelación depende de factores externos.")
print("  Acción: reforzar recordatorios en los horarios/servicios de mayor riesgo.")
print("  (En el script 05, un Bosque Aleatorio mejora esta misma predicción.)")

spark.stop()
print("\nSesión Spark finalizada")
