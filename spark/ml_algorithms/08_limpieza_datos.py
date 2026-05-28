"""
Unidad II – Validación y Limpieza de Datos | UrbanBlade
Materia: Extracción del Conocimiento en BD · UTVT IDGS-93

Temas:
  - Tipos de Extracción del dato (MongoDB NoSQL)
  - Tipos de Transformación del dato (básicas y avanzadas)
  - Tipos de carga de Datos (en memoria Spark)
  - Técnicas básicas de limpieza: dropDuplicates, fillna, filter
  - Técnicas avanzadas: Imputer, IQR, StandardScaler, MinMaxScaler
  - Métricas de evaluación de modelos de procesamiento
  - Diagrama de Minería de Datos (KDD)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, when, isnull, stddev, mean, percentile_approx
from pyspark.ml.feature import Imputer, StandardScaler, MinMaxScaler, VectorAssembler
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

database        = os.getenv("MONGO_DB",         "urbanblade")
collection_name = os.getenv("MONGO_COLLECTION", "appointments")
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD", ""))
    cluster  = os.getenv("MONGO_CLUSTER")
    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

spark = SparkSession.builder \
    .appName("UrbanBlade-Limpieza-ETL") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
    .config("spark.mongodb.read.connection.uri",  mongo_uri) \
    .config("spark.mongodb.read.database",        database) \
    .config("spark.mongodb.read.collection",      collection_name) \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

SEP = "=" * 65

# ═══════════════════════════════════════════════════════════════
# DIAGRAMA DE MINERÍA DE DATOS (KDD)
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" DIAGRAMA DE MINERÍA DE DATOS – Proceso KDD")
print(SEP)
print("""
  [1. DATOS RAW]       MongoDB Atlas / Local
        ↓
  [2. SELECCIÓN]       Elegir campos relevantes
        ↓
  [3. PREPROCESADO]    Limpiar nulos, duplicados, tipos
        ↓
  [4. TRANSFORMACIÓN]  Escalar, normalizar, imputar
        ↓
  [5. MINERÍA]         KMeans, Regresión, Árboles, PCA
        ↓
  [6. INTERPRETACIÓN]  Dashboard Ejecutivo + Visualizaciones
        ↓
  [7. CONOCIMIENTO]    Decisiones de negocio UrbanBlade
""")

# ═══════════════════════════════════════════════════════════════
# FASE 1 – EXTRACCIÓN (Extract)
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" FASE 1: EXTRACCIÓN DE DATOS (Extract)")
print(" Tipo: Base de Datos NoSQL (MongoDB) vía Apache Spark")
print(SEP)

# Tipo de Extracción: Full Load (carga completa)
df_raw = spark.read.format("mongodb").load()
total_raw = df_raw.count()

print(f"\n  Tipo de extracción : Full Load (carga completa)")
print(f"  Fuente             : MongoDB – {database}.{collection_name}")
print(f"  Registros cargados : {total_raw:,}")
print(f"  Columnas           : {len(df_raw.columns)}")
print(f"\n  Schema de los datos:")
df_raw.printSchema()


# ═══════════════════════════════════════════════════════════════
# DIAGNÓSTICO DE CALIDAD DE DATOS
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" DIAGNÓSTICO DE CALIDAD DE DATOS")
print(SEP)

campos_revisar = ["servicio", "barbero", "cantidad", "precio", "estado",
                  "propina", "rating", "duracion_min", "cliente_id"]

print(f"\n  {'Campo':<16} {'Nulos':>8} {'% Nulo':>8}  Calidad")
print(f"  {'-'*50}")
for campo in campos_revisar:
    if campo in df_raw.columns:
        nulos = df_raw.filter(col(campo).isNull()).count()
        pct   = (nulos / total_raw) * 100
        cal   = "✅ OK" if pct < 5 else "⚠️  Revisar" if pct < 30 else "❌ Crítico"
        print(f"  {campo:<16} {nulos:>8,} {pct:>7.1f}%  {cal}")

# Duplicados
total_uniq  = df_raw.dropDuplicates().count()
duplicados  = total_raw - total_uniq
print(f"\n  Registros duplicados : {duplicados:,}")
print(f"  Registros únicos     : {total_uniq:,}")


# ═══════════════════════════════════════════════════════════════
# FASE 2 – TRANSFORMACIÓN BÁSICA
# Técnicas básicas de limpieza
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" FASE 2A: TRANSFORMACIÓN – Técnicas BÁSICAS de Limpieza")
print(SEP)

# ── Técnica 1: Eliminar duplicados (dropDuplicates)
print("\n  [Técnica 1] dropDuplicates() – Elimina registros duplicados")
df_t1 = df_raw.dropDuplicates()
print(f"    Antes: {total_raw:,}  →  Después: {df_t1.count():,}  (eliminados: {total_raw - df_t1.count():,})")

# ── Técnica 2: Filtrar nulos en campos críticos (filter / isNotNull)
print("\n  [Técnica 2] filter(isNotNull) – Filtra nulos en campos obligatorios")
df_t2 = df_t1.filter(
    col("servicio").isNotNull() &
    col("barbero").isNotNull()  &
    col("cantidad").isNotNull() &
    col("precio").isNotNull()
)
print(f"    Campos críticos: servicio, barbero, cantidad, precio")
print(f"    Antes: {df_t1.count():,}  →  Después: {df_t2.count():,}")

# ── Técnica 3: Rellenar nulos con valores por defecto (fillna)
print("\n  [Técnica 3] fillna() – Rellena nulos con valores por defecto")
df_t3 = df_t2.fillna({
    "estado":      "desconocido",
    "propina":     0.0,
    "duracion_min": 30
})
print("    estado=None → 'desconocido' | propina=None → 0 | duracion_min=None → 30")

# ── Técnica 4: Convertir tipos de datos (cast)
print("\n  [Técnica 4] cast() – Conversión y validación de tipos de datos")
df_t4 = df_t3 \
    .withColumn("cantidad",    col("cantidad").cast("double")) \
    .withColumn("precio",      col("precio").cast("double")) \
    .withColumn("propina",     col("propina").cast("double")) \
    .withColumn("duracion_min",col("duracion_min").cast("double"))
print("    cantidad, precio, propina, duracion_min → DoubleType")
print(f"    Registros válidos post-casteo: {df_t4.count():,}")

# ── Técnica 5: Reclasificación de nulos (fillna con categoría)
print("\n  [Técnica 5] Reclasificación – Nulos conocidos → categoría 'SIN_CLASIFICAR'")
df_t5_basic = df_t4.fillna({"estado": "SIN_CLASIFICAR"})
print("    En lugar de eliminar, convertimos → no perdemos información estadística")


# ═══════════════════════════════════════════════════════════════
# FASE 2B – TRANSFORMACIÓN AVANZADA
# Técnicas avanzadas de limpieza
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" FASE 2B: TRANSFORMACIÓN – Técnicas AVANZADAS de Limpieza")
print(SEP)

# ── Técnica 6: Imputación con media (Imputer de MLlib)
print("\n  [Técnica 6] Imputer(strategy='mean') – Imputación estadística")
campos_imp = ["cantidad", "precio", "propina"]
imputer = Imputer(
    inputCols  = campos_imp,
    outputCols = [f"{c}_imp" for c in campos_imp],
    strategy   = "mean"
)
df_imp = imputer.fit(df_t4).transform(df_t4)
print(f"    Campos imputados: {campos_imp}")
print("    Estrategia: media aritmética (evita sesgo de eliminación)")

# ── Técnica 7: Detección y eliminación de outliers (IQR)
print("\n  [Técnica 7] IQR – Remoción de valores atípicos")
q1, q3 = df_imp.approxQuantile("precio", [0.25, 0.75], 0.01)
iqr     = q3 - q1
lower   = q1 - 1.5 * iqr
upper   = q3 + 1.5 * iqr
df_iqr  = df_imp.filter((col("precio") >= lower) & (col("precio") <= upper))
print(f"    Q1 = ${q1:.0f}  |  Q3 = ${q3:.0f}  |  IQR = ${iqr:.0f}")
print(f"    Límite inferior: ${lower:.0f}  |  Límite superior: ${upper:.0f}")
print(f"    Antes: {df_imp.count():,}  →  Después de IQR: {df_iqr.count():,}")

# ── Técnica 8: Estandarización Z-score (StandardScaler)
print("\n  [Técnica 8] StandardScaler – Estandarización (Z-score)")
asm_std = VectorAssembler(
    inputCols = ["cantidad_imp", "precio_imp"],
    outputCol = "features_raw",
    handleInvalid = "skip"
)
df_vec  = asm_std.transform(df_iqr)
scaler  = StandardScaler(inputCol="features_raw", outputCol="features_std",
                         withMean=True, withStd=True)
df_std  = scaler.fit(df_vec).transform(df_vec)
print("    Resultado: μ=0, σ=1 → elimina sesgo de escala entre variables")
print("    Aplicación: Regresión, SVM, Redes Neuronales, PCA")

# ── Técnica 9: Normalización [0,1] (MinMaxScaler)
print("\n  [Técnica 9] MinMaxScaler – Normalización al rango [0, 1]")
norm   = MinMaxScaler(inputCol="features_raw", outputCol="features_norm")
df_norm = norm.fit(df_vec).transform(df_vec)
print("    Rango: [0, 1] → útil para KNN, Redes Neuronales, K-Means")
print("    Fórmula: x_norm = (x - x_min) / (x_max - x_min)")

# ── Técnica 10: Validación de rango de negocio
print("\n  [Técnica 10] Reglas de negocio – Validación de rangos lógicos")
invalidos_precio   = df_iqr.filter((col("precio") <= 0) | (col("precio") > 5000)).count()
invalidos_cantidad = df_iqr.filter((col("cantidad") <= 0) | (col("cantidad") > 20)).count()
print(f"    Precios inválidos (≤0 o >5000): {invalidos_precio:,}")
print(f"    Cantidades inválidas (≤0 o >20): {invalidos_cantidad:,}")
df_clean = df_iqr.filter(
    (col("precio") > 0) & (col("precio") <= 5000) &
    (col("cantidad") > 0) & (col("cantidad") <= 20)
)
print(f"    Registros después de reglas de negocio: {df_clean.count():,}")


# ═══════════════════════════════════════════════════════════════
# FASE 3 – CARGA (Load)
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" FASE 3: CARGA DE DATOS (Load)")
print(SEP)

# Tipo de carga: In-Memory (Spark DataFrame)
df_final = df_clean.select(
    col("servicio"), col("barbero"), col("estado"),
    col("cantidad").cast("double"),
    col("precio").cast("double"),
    col("propina").cast("double")
).dropna()

total_final = df_final.count()
print(f"\n  Tipo de carga      : In-Memory (Spark DataFrame)")
print(f"  Destino            : Pipeline de ML UrbanBlade")
print(f"  Registros limpios  : {total_final:,}")
print(f"\n  Muestra del dataset limpio:")
df_final.show(5, truncate=False)


# ═══════════════════════════════════════════════════════════════
# MÉTRICAS DE EVALUACIÓN DE CALIDAD POST-ETL
# ═══════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print(" MÉTRICAS DE EVALUACIÓN DEL PROCESO ETL")
print(SEP)

retencion = (total_final / total_raw) * 100
print(f"\n  Registros originales  : {total_raw:,}")
print(f"  Registros finales     : {total_final:,}")
print(f"  Tasa de retención     : {retencion:.1f}%")
print(f"  Registros eliminados  : {total_raw - total_final:,} ({100 - retencion:.1f}%)")

print(f"\n  Estadísticas descriptivas post-ETL:")
print(f"  {'Campo':<12} {'Media':>10} {'Std':>10} {'Min':>10} {'Max':>10}")
print(f"  {'-'*55}")
for campo in ["cantidad", "precio", "propina"]:
    stats = df_final.select(
        mean(campo).alias("media"),
        stddev(campo).alias("std")
    ).collect()[0]
    minv, maxv = df_final.agg({campo: "min"}).collect()[0][0], \
                 df_final.agg({campo: "max"}).collect()[0][0]
    print(f"  {campo:<12} {stats['media']:>10.2f} {stats['std']:>10.2f} {minv:>10.2f} {maxv:>10.2f}")

print(f"\n{SEP}")
print(" RESUMEN DEL PROCESO KDD – UrbanBlade")
print(SEP)
print("""
  Fase 1 – EXTRACCIÓN   : MongoDB → Spark (Full Load)
  Fase 2 – TRANSFORMACIÓN:
    Básicas  → dropDuplicates, filter, fillna, cast, reclasificación
    Avanzadas→ Imputer, IQR outliers, StandardScaler, MinMaxScaler, reglas negocio
  Fase 3 – CARGA        : DataFrame limpio → Pipeline ML

  Modelos posteriores usan este dataset limpio:
  KMeans → Segmentación de clientes
  Regresión → Predicción de ingreso
  Random Forest → Clasificación de citas de alto valor
  PCA → Reducción dimensional
  Red Neuronal → Clasificación de ingreso con PyTorch
""")

spark.stop()
print("✅ Pipeline ETL finalizado correctamente")
