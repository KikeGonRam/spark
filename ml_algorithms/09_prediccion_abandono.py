"""
Unidad III — Script 09: Predicción de Abandono de Clientes (Churn)

  PROBLEMA: identificar clientes que probablemente dejarán de asistir.

  Definición de churn (honesta, NO circular):
     en_riesgo = 1  si el cliente lleva > umbral días sin volver (recencia alta).
     El umbral = percentil 70 de la recencia del dataset.

  Features predictoras (NO incluyen la recencia que define la etiqueta → sin fuga):
     total_citas, gasto_promedio, gasto_total, tasa_cancelacion_pct,
     frecuencia_mensual, meses_activo
  → El modelo aprende a anticipar el abandono a partir del PATRÓN de consumo,
    no a partir de la propia variable que define el abandono.

  Modelo   : Random Forest Classifier  +  split train/test 70/30 (evaluación real).
  Nombres  : reales (client_id → clients → users.name) vía la capa de datos única.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session, get_clientes_df
from pyspark.sql.functions import col, when, round as sround
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator

print("\n" + "=" * 60)
print("PREDICCIÓN DE ABANDONO DE CLIENTES (CHURN) — UrbanBlade")
print("=" * 60)

# ── DATOS: RFM por cliente (capa única) ────────────────────────────────────────
spark, df, _ = get_spark_session()
clientes = get_clientes_df(spark, df).cache()
total_cl = clientes.count()
print(f"Clientes analizados: {total_cl}")

# ── ETIQUETA: churn por recencia (percentil 70) ────────────────────────────────
umbral_dias = clientes.approxQuantile("dias_sin_cita", [0.70], 0.01)[0]
print(f"""
Definición de riesgo:
  en_riesgo = 1  si dias_sin_cita > {umbral_dias:.0f} (percentil 70 de recencia)
  La recencia define la etiqueta pero NO se usa como feature (evita fuga de datos).
""")
clientes = clientes.withColumn(
    "en_riesgo", when(col("dias_sin_cita") > umbral_dias, 1).otherwise(0))

en_riesgo = clientes.filter(col("en_riesgo") == 1).count()
print(f"Clientes en riesgo: {en_riesgo} ({en_riesgo/total_cl*100:.0f}%) | "
      f"estables: {total_cl-en_riesgo} ({(total_cl-en_riesgo)/total_cl*100:.0f}%)")

# ── MODELO: Random Forest con split 70/30 ──────────────────────────────────────
print("\n" + "=" * 60)
print("MODELO: Random Forest Classifier (split train/test 70/30)")
print("=" * 60)

feature_cols = ["total_citas", "gasto_promedio", "gasto_total",
                "tasa_cancelacion_pct", "frecuencia_mensual", "meses_activo"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features",
                            handleInvalid="skip")
data = assembler.transform(clientes).withColumn("label", col("en_riesgo").cast("double"))

train, test = data.randomSplit([0.7, 0.3], seed=42)
print(f"Entrenamiento: {train.count()} | Prueba: {test.count()}")
print(f"Features (sin la recencia): {feature_cols}\n")

rf = RandomForestClassifier(featuresCol="features", labelCol="label",
                            numTrees=100, maxDepth=5, seed=42)
model = rf.fit(train)
preds = model.transform(test)

auc = BinaryClassificationEvaluator(
    labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC").evaluate(preds)
acc = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="accuracy").evaluate(preds)
f1  = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="f1").evaluate(preds)

print(f"AUC-ROC : {round(auc, 4)}   ← evaluado en datos NO vistos")
print(f"Accuracy: {round(acc, 4)}")
print(f"F1-Score: {round(f1, 4)}")

# ── Importancia de features ────────────────────────────────────────────────────
print("\nImportancia de cada variable (patrón que anticipa el abandono):")
for feat, imp in sorted(zip(feature_cols, model.featureImportances.toArray()),
                        key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"  {feat:<24} {bar}  {round(imp, 4)}")

# ── LISTA DE CLIENTES EN RIESGO (con probabilidad del modelo) ──────────────────
print("\n" + "=" * 60)
print("CLIENTES EN RIESGO DE ABANDONO (probabilidad del modelo)")
print("=" * 60)
try:
    from pyspark.ml.functions import vector_to_array
    scored = model.transform(data).withColumn(
        "prob_abandono_pct", sround(vector_to_array(col("probability"))[1] * 100, 1))
except Exception:
    # Fallback sin vector_to_array (versiones antiguas de Spark)
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType
    prob1 = udf(lambda v: float(v[1]) * 100, DoubleType())
    scored = model.transform(data).withColumn(
        "prob_abandono_pct", sround(prob1(col("probability")), 1))

scored.filter(col("en_riesgo") == 1) \
    .select("cliente", "nivel", "total_citas", "gasto_promedio",
            "tasa_cancelacion_pct", "dias_sin_cita", "prob_abandono_pct") \
    .orderBy(col("prob_abandono_pct").desc()).show(20, truncate=False)

print("""
Acciones de retención recomendadas:
  ALTA prob. (>70%):   Llamada personalizada + oferta urgente
  MEDIA prob. (40-70%): WhatsApp recordatorio + descuento 15%
  BAJA prob. (<40%):    Newsletter mensual con novedades
""")

spark.stop()
print("Predicción de abandono completada.")
