---
name: spark-urbanblade
description: >
  Skill para el proyecto UrbanBlade en la materia "Extracción del conocimiento en
  bases de datos" (UTVT, IDGS-93, Prof. Héctor Velázquez Estrada, Mayo–Agosto 2026).
  Cubre las 5 unidades del programa usando los patrones EXACTOS del profesor:
  conexión MongoDB Atlas con get_spark_session(), MapReduce, KMeans, Regresión (6 modelos),
  Árbol de Decisión, Bosque Aleatorio, PCA + KMeans, Red Neuronal PyTorch, dashboards
  Streamlit + Plotly.
  Proyecto: barbería UrbanBlade (roles Admin, Barbero, Cliente).
  Directorio raíz: /spark/
  Entorno: WSL Ubuntu (Windows).
  Triggers: "spark", "pyspark", "mapreduce", "kmeans", "regresion", "arbol de decision",
  "bosque aleatorio", "pca", "red neuronal", "dashboard", "streamlit", "ETL",
  "mongo spark", "get_spark_session", "ingreso", "features", "VectorAssembler".
stack: PySpark 3.5.x, MongoDB Atlas, Python 3.11+, Streamlit, Plotly, PyTorch
project: UrbanBlade – Sistema de gestión de barbería
course: Extracción del conocimiento en bases de datos – UTVT IDGS-93
teacher: MGTI. Héctor Velázquez Estrada
period: Mayo–Agosto 2026
env: WSL Ubuntu
author: Equipo UrbanBlade
---

# Spark + MongoDB – UrbanBlade
## Materia: Extracción del conocimiento en bases de datos | UTVT IDGS-93
## Entorno: WSL Ubuntu | Directorio raíz: /spark/

---

## Contexto del proyecto

UrbanBlade es un sistema de gestión de barbería con tres roles:
- **Admin**: reportes globales, KPIs, configuración del negocio
- **Barbero**: agenda personal, historial de clientes
- **Cliente**: reservas, historial, preferencias de servicio

Stack web: **Laravel 12 / PHP 8.4 + TailwindCSS v4 + Alpine.js + MySQL**.
La capa Spark es un **módulo Python independiente en `/spark/`** que conecta a
MongoDB Atlas, procesa datos y alimenta dashboards Streamlit.

---

## Colecciones MongoDB UrbanBlade (barber_db — REAL)

```
appointments  → _id, service_id, barber_id, client_id, precio_cobrado,
                estado (pendiente|confirmada|completada|cancelada),   ← SOLO 4 estados reales
                fecha (UTCDateTime), hora_inicio, hora_fin, metodo_pago, code

services      → _id, nombre, categoria (barba|combo|corte|tratamiento), duracion_min, precio, activo
barbers       → _id, user_id, activo   ← NO tiene campo 'nombre': se resuelve por user_id → users.name
users         → _id, name, email, role_id
clients       → _id, user_id, nivel (regular|vip), puntos, total_citas, fecha_nacimiento
payments      → _id, appointment_id, monto, propina (=0 en datos actuales), metodo_pago
loyalty_transactions → _id, client_id, puntos, tipo
```

> **Schema real verificado** (12,535 citas, 1000 clientes, 25 barberos):
> `client_id` referencia la colección **`clients`** (NO `users`) → nombre real por
> `client_id → clients.user_id → users.name`. `precio_cobrado == precio_servicio`
> siempre (sin descuentos ni propinas).
>
> **Capa de datos única** `mongo_spark_conexion_sinnulos.py` → `get_spark_session()`
> devuelve `(spark, df, df_vector)`. El `df` conserva las columnas originales
> (`servicio, barbero, duracion_min, precio, estado, ingreso, fecha`) y AGREGA:
> `cliente, nivel, categoria, precio_base, es_cancelada, anio, mes, dia, dia_semana,
> hora, puntos_cliente, edad_cliente, client_id`. Los scripts 01–07 no se rompen.
>
> Helpers y constantes exportadas:
> - `get_clientes_df(spark, df)` → RFM por cliente (usado por 08 y 09)
> - `FEATURES_BASE = ["duracion_min","precio","ingreso"]` (compatibilidad)
> - `FEATURES_CANCEL = ["duracion_min","precio","hora","dia_semana","mes"]` (clasificación honesta)
> - `ESTADOS_VALIDOS`, `CATEGORIAS`, `DIAS_SEMANA`, `MESES`
>
> **Sin fuga de datos (leakage)**: como `ingreso == precio`, NUNCA se predice `ingreso`
> usando `precio` como feature. La regresión (03) predice la **facturación diaria**;
> la clasificación (04/05) predice **cancelación** con `FEATURES_CANCEL`.

---

## Estructura de directorios `/spark/`

```
/spark/
├── config/
│   ├── mongo_spark_conexion.py            ← Conexión base (con nulos)
│   └── mongo_spark_conexion_sinnulos.py   ← Conexión limpia (sin nulos) ← USAR ESTA
├── data_ingestion/
│   └── generar_datos_urbanblade.py        ← Poblar MongoDB con datos de prueba
├── ml_algorithms/
│   ├── 01_mapreduce.py                    ← Unidad II – ETL/MapReduce
│   ├── 02_kmeans.py                       ← Unidad IV – Clustering
│   ├── 03_regresion_analytics.py          ← Unidad III – Regresión (6 modelos)
│   ├── 04_arboldedecision.py              ← Unidad III – Árbol de Decisión
│   ├── 05_bosque_aleatorio.py             ← Unidad III – Random Forest
│   ├── 06_pca.py                          ← Unidad IV – PCA + KMeans
│   └── 07_red_neural.py                   ← Unidad III/IV – Red Neuronal PyTorch
├── analytics/
│   ├── dashboard_kmeans.py                ← Unidad V – Dashboard KMeans
│   ├── dashboard_regresion_models.py      ← Unidad V – Dashboard Regresión
│   └── dashboard_pca.py                   ← Unidad V – Dashboard PCA
├── processing/
│   └── (utilidades y consultas)
├── .env
└── requirements.txt
```

---

## Variables de entorno — `.env` (raíz `/spark/`)

```env
MONGO_USER=luis_urbanblade
MONGO_PASSWORD=TuPasswordSeguro
MONGO_CLUSTER=cluster0.xxxxx.mongodb.net
MONGO_DB=urbanblade
MONGO_COLLECTION=appointments
```

> El profesor usa **MongoDB Atlas** (`mongodb+srv://`) con variables separadas.
> NO usar `MONGO_URI` como variable única — usar las 5 variables del profesor.

---

## PATRÓN BASE — `config/mongo_spark_conexion_sinnulos.py`

**ESTE ES EL ARCHIVO MÁS IMPORTANTE. Todos los scripts lo importan.**
Usa PyMongo para hacer JOIN real de 4 colecciones (appointments + services + barbers + users),
luego construye el DataFrame Spark con los campos correctos del barber_db.

```python
# config/mongo_spark_conexion_sinnulos.py  (versión actualizada — con dropna y handleInvalid)
# Conecta a MongoDB Atlas via PyMongo, hace JOIN de 4 colecciones,
# crea DataFrame Spark con: servicio, barbero, duracion_min, precio, estado, ingreso, fecha
# Features: ["duracion_min", "precio", "ingreso"]   (NO "cantidad" — ese campo no existe en barber_db)
# Devuelve: (spark, df, df_vector)

# Campos disponibles en df:
#   servicio   (str)  — nombre del servicio (de services.nombre)
#   barbero    (str)  — nombre del barbero  (de users.name vía barbers.user_id)
#   duracion_min (double) — duración del servicio en minutos
#   precio     (double)   — precio cobrado (appointments.precio_cobrado)
#   estado     (str)      — estado de la cita (completada, cancelada, etc.)
#   ingreso    (double)   — igual que precio (ingreso real por cita)
#   fecha      (str)      — fecha de la cita como string
```

> **Regla crítica**: `get_spark_session()` siempre devuelve `(spark, df, df_vector)`.
> Desempaquetar igual que el profesor: `spark, df, df_vector = get_spark_session()`
> o `spark, df, _ = get_spark_session()` si no necesitas el vector.
>
> **NO usar `cantidad`** — ese campo no existe en appointments de barber_db.
> Usar `duracion_min` como feature principal (viene de services.duracion_min).
> `ingreso = precio_cobrado` del appointment, NO `cantidad × precio`.

---

## `config/mongo_spark_conexion.py` — versión básica (con nulos)

```python
# config/mongo_spark_conexion.py
# Igual que sinnulos pero sin dropna — para scripts que manejan nulos manualmente
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus


def get_spark_session():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD"))
    cluster  = os.getenv("MONGO_CLUSTER")
    database = os.getenv("MONGO_DB")
    coll     = os.getenv("MONGO_COLLECTION")

    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

    spark = SparkSession.builder \
        .appName("UrbanBlade-BigData") \
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.13:10.3.0") \
        .config("spark.mongodb.read.connection.uri",  mongo_uri) \
        .config("spark.mongodb.read.database",        database) \
        .config("spark.mongodb.read.collection",      coll) \
        .config("spark.mongodb.write.connection.uri", mongo_uri) \
        .getOrCreate()

    df = spark.read.format("mongodb").load()

    df = df.withColumn("ingreso", col("cantidad") * col("precio"))

    assembler = VectorAssembler(
        inputCols=["cantidad", "precio", "ingreso"],
        outputCol="features"
    )
    df_vector = assembler.transform(df)

    return spark, df, df_vector
```

---

## `data_ingestion/generar_datos_urbanblade.py`

Equivalente al `generar_datos2_insertmany.py` del profesor, adaptado a UrbanBlade.

```python
import random
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

user     = os.getenv("MONGO_USER")
password = quote_plus(os.getenv("MONGO_PASSWORD"))
cluster  = os.getenv("MONGO_CLUSTER")
database = os.getenv("MONGO_DB")
coll     = os.getenv("MONGO_COLLECTION")

mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"
client = MongoClient(mongo_uri)
client.admin.command("ping")
print("Conexión exitosa a MongoDB")

db        = client[database]
coleccion = db[coll]

# Datos de UrbanBlade
servicios = ["Corte Clásico", "Corte Fade", "Barba", "Corte + Barba", "Tintura"]
barberos  = ["Carlos", "Miguel", "Andrés", "Javier"]
estados   = ["completada", "cancelada", "pendiente"]

citas = []
for _ in range(2000):
    servicio = random.choice(servicios)
    precio_base = {
        "Corte Clásico": 150, "Corte Fade": 200,
        "Barba": 100, "Corte + Barba": 250, "Tintura": 400
    }[servicio]
    cita = {
        "servicio":  servicio,
        "barbero":   random.choice(barberos),
        "cantidad":  random.randint(1, 3),
        "precio":    precio_base + random.randint(-20, 50),
        "estado":    random.choices(estados, weights=[70, 20, 10])[0]
    }
    citas.append(cita)

resultado = coleccion.insert_many(citas)
coleccion.create_index("servicio")
coleccion.create_index("barbero")
coleccion.create_index("precio")

print(f"{len(resultado.inserted_ids)} citas insertadas correctamente")
```

---

## UNIDAD II — MapReduce (ETL distribuido)

### `ml_algorithms/01_mapreduce.py`

```python
from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum, avg, count

spark, df, _ = get_spark_session()

print("\n")
print("=== MAPREDUCE – INGRESOS POR SERVICIO UrbanBlade ===")
print("\n")

# MAP → agrupa por servicio
# REDUCE → suma ingresos
df.groupBy("servicio") \
  .agg(sum("ingreso").alias("total_ingreso")) \
  .orderBy("total_ingreso", ascending=False) \
  .show()

spark.stop()
```

### `ml_algorithms/01_mapreduce_analytics_sinnulos.py` — con interpretación + gráficas

```python
from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum, avg, count
import matplotlib.pyplot as plt


def interpretar_mapreduce(resumen_df):
    resumen_pd = resumen_df.toPandas()
    print("\nINTERPRETACIÓN AUTOMÁTICA MAPREDUCE\n")
    max_ingreso  = resumen_pd["ingreso_total"].max()
    max_cantidad = resumen_pd["cantidad_total"].max()

    for _, row in resumen_pd.iterrows():
        servicio = row["servicio"]
        ingreso  = round(row["ingreso_total"], 2)
        cantidad = row["cantidad_total"]
        print(f"Servicio: {servicio}")
        print(f"  Ingreso Total: ${ingreso}")
        print(f"  Citas Totales: {cantidad}")
        if ingreso == max_ingreso:
            print("  → Servicio Estrella (Mayor ingreso)")
        elif cantidad == max_cantidad:
            print("  → Servicio de Alta Rotación")
        else:
            print("  → Servicio Secundario")
        print()


def graficar_ingresos(resumen_df):
    pdf = resumen_df.toPandas()
    plt.figure(figsize=(10, 6))
    plt.bar(pdf["servicio"], pdf["ingreso_total"])
    plt.xlabel("Servicio")
    plt.ylabel("Ingreso Total ($)")
    plt.title("Ingreso Total por Servicio – UrbanBlade")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main():
    spark, df, _ = get_spark_session()
    print("\nEJECUTANDO MAPREDUCE AVANZADO – UrbanBlade\n")

    df = df.fillna({"servicio": "SIN_CLASIFICAR"})

    resumen = df.groupBy("servicio").agg(
        sum("ingreso").alias("ingreso_total"),
        sum("cantidad").alias("cantidad_total"),
        avg("precio").alias("precio_promedio"),
        count("*").alias("numero_citas")
    )
    resumen.show()

    interpretar_mapreduce(resumen)
    graficar_ingresos(resumen)

    spark.stop()


if __name__ == "__main__":
    main()
```

---

## UNIDAD III — Análisis Supervisado

### `ml_algorithms/03_regresion_analytics.py` — 6 modelos de regresión

Evalúa R², MSE (Error Cuadrático Medio) y MAE (Error Absoluto Medio) para cada modelo,
tal como requiere la Unidad III del programa.

```python
from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.feature import VectorAssembler, PolynomialExpansion
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
import matplotlib.pyplot as plt

spark, df, _ = get_spark_session()
# df tiene: servicio, barbero, duracion_min, precio, estado, ingreso, fecha
train, test = df.randomSplit([0.8, 0.2], seed=42)

# Evalúa las 3 métricas requeridas por Unidad III
def evaluar(predictions, label="ingreso"):
    r2  = RegressionEvaluator(labelCol=label, metricName="r2").evaluate(predictions)
    mse = RegressionEvaluator(labelCol=label, metricName="mse").evaluate(predictions)
    mae = RegressionEvaluator(labelCol=label, metricName="mae").evaluate(predictions)
    return r2, mse, mae
# Modelo 1: VectorAssembler(inputCols=["duracion_min"])  → Lineal Simple
# Modelo 2: VectorAssembler(inputCols=["duracion_min","precio"]) → Múltiple
# Modelos 3–4: Ridge / Lasso con regParam=0.5
# Modelo 5: PolynomialExpansion(degree=2)
# Modelo 6: CrossValidator(numFolds=3, paramGrid)
# Salida: tabla comparativa con R²/MSE/MAE + interpretación automática


def graficar(predictions, titulo):
    pdf = predictions.select("cantidad", "ingreso", "prediction").toPandas()
    plt.figure()
    plt.scatter(pdf["cantidad"], pdf["ingreso"],    label="Real")
    plt.scatter(pdf["cantidad"], pdf["prediction"], label="Predicción")
    plt.title(titulo)
    plt.xlabel("Cantidad de Servicios")
    plt.ylabel("Ingreso ($)")
    plt.legend()
    plt.show()


# MODELO 1 – Regresión Lineal Simple
print("MODELO 1 REGRESIÓN LINEAL SIMPLE")
a_simple  = VectorAssembler(inputCols=["cantidad"], outputCol="features")
tr_simple = a_simple.transform(train)
te_simple = a_simple.transform(test)
m1 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr_simple)
p1 = m1.transform(te_simple)
r2_simple = evaluator.evaluate(p1)
print("R2:", r2_simple)
graficar(p1, "Regresión Lineal Simple – UrbanBlade")

# MODELO 2 – Regresión Lineal Múltiple
print("MODELO 2 REGRESIÓN LINEAL MÚLTIPLE")
a_mult  = VectorAssembler(inputCols=["cantidad", "precio"], outputCol="features")
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
```

### `ml_algorithms/04_arboldedecision.py`

```python
from pyspark.sql.functions import when, col
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from config.mongo_spark_conexion_sinnulos import get_spark_session

spark, df, df_vector = get_spark_session()
print("\nDataset UrbanBlade original")
df.show()

# Etiqueta: cita de ALTO VALOR (ingreso > umbral) = 1, BAJO = 0
df = df.withColumn(
    "label",
    when(col("ingreso") > 500, 1).otherwise(0)   # umbral UrbanBlade
)

print("\nDataset con etiqueta")
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
print("Datos entrenamiento:", train_data.count())
print("Datos prueba:", test_data.count())

dt    = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=3)
model = dt.fit(train_data)

print("\nEstructura del árbol:\n")
print(model.toDebugString)

predictions = model.transform(test_data)
print("\nPredicciones")
predictions.select("features", "label", "prediction").show()

accuracy = MulticlassClassificationEvaluator(
    labelCol="label", predictionCol="prediction", metricName="accuracy"
).evaluate(predictions)
print("\nAccuracy del modelo:", accuracy)

spark.stop()
```

### `ml_algorithms/05_bosque_aleatorio.py`

```python
from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import when, col
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator

spark, df, _ = get_spark_session()

df = df.fillna({"cantidad": 0, "precio": 0, "ingreso": 0})

# Label: cita cancelada = 1, completada = 0
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
print(f"\nAUC del modelo: {auc}")

print("\nComparación predicción vs real:")
predictions.groupBy("categoria", "prediction").count().show()

rf_model = model.stages[-1]
print("\nImportancia de variables:")
for i, imp in enumerate(rf_model.featureImportances):
    nombres = ["cantidad", "precio", "ingreso"]
    print(f"  {nombres[i]}: {imp:.4f}")

model.write().overwrite().save("modelo_pipeline_rf_urbanblade")
print("\nModelo guardado correctamente")

spark.stop()
print("Sesión Spark finalizada")
```

---

## UNIDAD IV — Análisis No Supervisado

### `ml_algorithms/02_kmeans.py`

```python
from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator


def main():
    print("\n=== INICIANDO KMEANS – UrbanBlade ===\n")
    spark, df, df_vector = get_spark_session()

    total = df_vector.count()
    if total < 3:
        print("No hay suficientes datos para clustering.")
        spark.stop()
        return

    print(f"Total registros: {total}")

    kmeans = KMeans(
        k=3,
        seed=42,
        featuresCol="features",
        predictionCol="cluster"
    )
    model  = kmeans.fit(df_vector)
    result = model.transform(df_vector)

    print("\n=== RESULTADOS ===")
    result.select("servicio", "cantidad", "precio", "ingreso", "cluster").show(10)

    evaluator  = ClusteringEvaluator(
        featuresCol="features", predictionCol="cluster", metricName="silhouette"
    )
    silhouette = evaluator.evaluate(result)
    print(f"\nSilhouette Score: {round(silhouette, 4)}")

    if silhouette > 0.5:
        print("Buena segmentación")
    elif silhouette > 0.2:
        print("Segmentación aceptable")
    else:
        print("Segmentación débil")

    print("\n=== CENTROIDES ===")
    for i, center in enumerate(model.clusterCenters()):
        print(f"Cluster {i}: {center}")

    print("\n=== DISTRIBUCIÓN DE CLUSTERS ===")
    result.groupBy("cluster").count().show()

    spark.stop()


if __name__ == "__main__":
    main()
```

### `ml_algorithms/06_pca.py`

```python
from config.mongo_spark_conexion import get_spark_session
from pyspark.ml.feature import StandardScaler, PCA, VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, DoubleType
import pandas as pd
import plotly.express as px
import plotly.io as pio

spark, df, df_vector = get_spark_session()

df = df.fillna({"cantidad": 0, "precio": 0, "ingreso": 0})

assembler = VectorAssembler(
    inputCols=["cantidad", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)
df_vector = assembler.transform(df)
print("Datos cargados correctamente")

# 2. ESCALADO — CRÍTICO para PCA
print("Escalando datos...")
scaler       = StandardScaler(inputCol="features", outputCol="scaledFeatures",
                              withStd=True, withMean=True)
scaler_model = scaler.fit(df_vector)
df_scaled    = scaler_model.transform(df_vector)
print("Datos escalados correctamente")

# 3. PCA
print("Aplicando PCA...")
pca       = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures")
pca_model = pca.fit(df_scaled)
df_pca    = pca_model.transform(df_scaled)
print("PCA aplicado correctamente")

print("\nVarianza explicada:")
print(pca_model.explainedVariance)

# 4. CLUSTERING sobre componentes PCA
print("\nAplicando KMeans sobre PCA...")
kmeans       = KMeans(k=3, featuresCol="pcaFeatures", predictionCol="cluster")
kmeans_model = kmeans.fit(df_pca)
df_cluster   = kmeans_model.transform(df_pca)
print("Clustering aplicado correctamente")

print("\nCentroides de clusters:")
for i, c in enumerate(kmeans_model.clusterCenters()):
    print(f"Cluster {i}: {c}")

# 5. INTERPRETACIÓN AUTOMÁTICA
def interpretar_cluster(centroid):
    pc1, pc2 = centroid
    desc = []
    desc.append("valores ALTOS en servicios/precio/ingreso" if pc1 > 0
                 else "valores BAJOS en servicios/precio/ingreso")
    desc.append("segunda componente POSITIVA" if pc2 > 0
                 else "segunda componente NEGATIVA")
    return ", ".join(desc)

print("\nInterpretación de clusters:")
for i, c in enumerate(kmeans_model.clusterCenters()):
    print(f"Cluster {i}: {interpretar_cluster(c)}")

print("\nPesos de los componentes principales:")
print(pca_model.pc)

# 6. SOLUCIÓN ERROR DenseVector → lista Python
vector_to_array = udf(lambda v: v.toArray().tolist(), ArrayType(DoubleType()))
df_final = df_cluster.withColumn("pcaArray", vector_to_array("pcaFeatures"))

print("\nGenerando DataFrame para visualización...")
pdf = df_final.select("pcaArray", "cluster").toPandas()
pdf["PC1"] = pdf["pcaArray"].apply(lambda x: x[0])
pdf["PC2"] = pdf["pcaArray"].apply(lambda x: x[1])

# 7. VISUALIZACIÓN
print("Generando gráfica...")
fig = px.scatter(
    pdf,
    x="PC1",
    y="PC2",
    color=pdf["cluster"].astype(str),
    title="PCA + KMeans – UrbanBlade"
)
pio.renderers.default = "browser"
fig.show()

spark.stop()
print("\nProceso finalizado correctamente")
```

---

## UNIDAD III/IV — Red Neuronal PyTorch

### `ml_algorithms/07_red_neural.py`

```python
# Spark preprocesa → PyTorch entrena — patrón del profesor
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.model_selection import train_test_split

spark = SparkSession.builder \
    .appName("UrbanBlade-RedNeuronal") \
    .getOrCreate()

# Dataset de UrbanBlade (usa datos reales o simulados)
data = [
    (1, 150, 0), (2, 300, 1), (1, 100, 0), (3, 450, 2),
    (2, 200, 1), (1, 400, 2), (3, 600, 2), (1, 120, 0),
    (2, 250, 1), (3, 750, 2)
]
columns = ["cantidad", "precio", "label"]
df = spark.createDataFrame(data, columns)

assembler = VectorAssembler(inputCols=["cantidad", "precio"], outputCol="features")
df_vector = assembler.transform(df)

scaler       = StandardScaler(inputCol="features", outputCol="scaledFeatures",
                              withMean=True, withStd=True)
scaler_model = scaler.fit(df_vector)
df_scaled    = scaler_model.transform(df_vector)

pdf = df_scaled.select("scaledFeatures", "label").toPandas()
X   = pdf["scaledFeatures"].apply(lambda x: x.toArray()).tolist()
y   = pdf["label"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.long)
X_test  = torch.tensor(X_test,  dtype=torch.float32)
y_test  = torch.tensor(y_test,  dtype=torch.long)


class RedNeuronal(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 3)
        )
    def forward(self, x):
        return self.net(x)


model     = RedNeuronal()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

for epoch in range(100):
    outputs = model(X_train)
    loss    = criterion(outputs, y_train)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    if epoch % 10 == 0:
        print(f"Epoch {epoch} - Loss: {loss.item():.4f}")

with torch.no_grad():
    outputs   = model(X_test)
    _, pred   = torch.max(outputs, 1)
    accuracy  = (pred == y_test).sum().item() / len(y_test)

print(f"Precisión: {accuracy * 100:.2f}%")

labels_map = {0: "Ingreso bajo", 1: "Ingreso medio", 2: "Ingreso alto"}
nuevo = torch.tensor([[5.0, 300.0]])
with torch.no_grad():
    prob  = torch.softmax(model(nuevo), dim=1)
    clase = torch.argmax(prob).item()
print(f"Clase predicha: {labels_map[clase]}")
print(f"Probabilidades: {prob.numpy()}")

spark.stop()
```

---

## UNIDAD V — Dashboards Streamlit + Plotly

### `analytics/dashboard_kmeans.py`

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from config.mongo_spark_conexion_sinnulos import get_spark_session

st.set_page_config(page_title="Dashboard – Segmentación UrbanBlade", layout="wide")
st.title("Dashboard Ejecutivo – Segmentación con KMeans | UrbanBlade")

k_value = st.sidebar.slider("Número de Clusters (K)", min_value=2, max_value=8, value=3)

@st.cache_resource
def cargar_y_entrenar(k):
    spark, df, df_vector = get_spark_session()
    kmeans    = KMeans(k=k, seed=1)
    model     = kmeans.fit(df_vector)
    result    = model.transform(df_vector)
    evaluator = ClusteringEvaluator()
    silhouette = evaluator.evaluate(result)
    pdf = result.select("servicio", "barbero", "cantidad",
                        "precio", "ingreso", "prediction").toPandas()
    spark.stop()
    return pdf, silhouette

data, silhouette_score = cargar_y_entrenar(k_value)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Citas Totales", len(data))
col2.metric("Ingreso Total", f"${round(data['ingreso'].sum(), 2):,.0f}")
col3.metric("Ingreso Promedio", f"${round(data['ingreso'].mean(), 2):,.0f}")
col4.metric("Silhouette Score", round(silhouette_score, 4))

cluster_filter = st.sidebar.multiselect(
    "Filtrar por Cluster",
    sorted(data["prediction"].unique()),
    default=sorted(data["prediction"].unique())
)
data_filtrada = data[data["prediction"].isin(cluster_filter)]

st.subheader("Precio vs Ingreso por Cluster")
fig = px.scatter(data_filtrada, x="precio", y="ingreso",
                 color="prediction", hover_data=["servicio", "barbero", "cantidad"],
                 title="Segmentación de Citas UrbanBlade")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Visualización 3D")
fig_3d = px.scatter_3d(data_filtrada, x="precio", y="cantidad", z="ingreso",
                        color="prediction", hover_name="servicio")
st.plotly_chart(fig_3d, use_container_width=True)

st.subheader("Método del Codo")
def metodo_del_codo():
    spark, df, df_vector = get_spark_session()
    wcss = []
    for k in range(2, 9):
        m = KMeans(k=k, seed=1).fit(df_vector)
        wcss.append(m.summary.trainingCost)
    spark.stop()
    return wcss

wcss_values = metodo_del_codo()
fig_elbow = go.Figure()
fig_elbow.add_trace(go.Scatter(x=list(range(2, 9)), y=wcss_values, mode="lines+markers"))
fig_elbow.update_layout(xaxis_title="K", yaxis_title="WCSS", title="Método del Codo")
st.plotly_chart(fig_elbow, use_container_width=True)

st.subheader("Interpretación Ejecutiva")
resumen = data.groupby("prediction").mean(numeric_only=True)
for cluster in resumen.index:
    ingreso = resumen.loc[cluster, "ingreso"]
    precio  = resumen.loc[cluster, "precio"]
    st.markdown(f"### Cluster {cluster}")
    st.write(f"Ingreso promedio: ${round(ingreso, 2):,.0f}")
    st.write(f"Precio promedio: ${round(precio, 2):,.0f}")
    if ingreso == resumen["ingreso"].max():
        st.success("Segmento Estratégico (Mayor ingreso)")
    elif precio == resumen["precio"].max():
        st.info("Segmento Premium")
    else:
        st.warning("Segmento Operativo")
```

---

## `requirements.txt`

```
pyspark==3.5.1
pymongo==4.7.2
dnspython==2.6.1
python-dotenv==1.0.1
matplotlib==3.9.0
seaborn==0.13.2
pandas==2.2.2
streamlit==1.36.0
plotly==5.22.0
torch==2.3.0
scikit-learn==1.5.0
```

---

## Cómo ejecutar en WSL Ubuntu

```bash
# Instalar dependencias
pip install -r requirements.txt

# Generar datos de prueba en MongoDB Atlas
python3 data_ingestion/generar_datos_urbanblade.py

# Scripts ML (requieren spark-submit)
spark-submit --packages org.mongodb.spark:mongo-spark-connector_2.13:10.3.0 \
  ml_algorithms/01_mapreduce.py

spark-submit --packages org.mongodb.spark:mongo-spark-connector_2.13:10.3.0 \
  ml_algorithms/02_kmeans.py

# Red Neuronal (NO requiere spark-submit — usa SparkSession.builder interno)
python3 ml_algorithms/07_red_neural.py

# Dashboards Streamlit
streamlit run analytics/dashboard_kmeans.py
streamlit run analytics/dashboard_pca.py
```

---

## Reglas críticas para Claude Code / Copilot CLI

1. **Conector**: siempre `mongo-spark-connector_2.13:10.3.0` (con `_2.13`, NO `_2.12`).
2. **URI**: construir como `f"mongodb+srv://{user}:{password}@{cluster}"` con `quote_plus(password)`.
3. **Variables .env**: 5 variables separadas (`MONGO_USER`, `MONGO_PASSWORD`, `MONGO_CLUSTER`, `MONGO_DB`, `MONGO_COLLECTION`). NUNCA una sola `MONGO_URI`.
4. **Leer MongoDB**: configurar database/collection en `SparkSession.builder`, luego `spark.read.format("mongodb").load()` sin opciones extra.
5. **get_spark_session()** siempre devuelve `(spark, df, df_vector)` — desempaquetar con `spark, df, df_vector = get_spark_session()`.
6. **ingreso = cantidad * precio** — esta es la columna derivada principal, igual que el profesor.
7. **features** = siempre `["cantidad", "precio", "ingreso"]` con `VectorAssembler` y `handleInvalid="skip"`.
8. **Dashboards**: Streamlit + Plotly (NO matplotlib standalone para dashboards interactivos).
9. **PCA/KMeans**: SIEMPRE aplicar `StandardScaler` antes de PCA.
10. **Red Neuronal**: Spark procesa y escala → convertir a Pandas → entrenar con PyTorch.
11. **sys.path.append** al inicio de scripts en `analytics/` para importar `config/`.
12. **Directorio raíz**: todo vive en `/spark/` en WSL Ubuntu.
