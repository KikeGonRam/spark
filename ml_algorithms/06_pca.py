"""
Unidad IV – Análisis No Supervisado
Script  : 06_pca.py
Tema    : Reducción de dimensionalidad con PCA + Clustering KMeans sobre componentes
Métricas: Varianza explicada, Silhouette Score, interpretación de componentes principales
Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Equipo  : Equipo UrbanBlade
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-93
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.feature import StandardScaler, PCA, VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql.functions import udf, col
from pyspark.sql.types import ArrayType, DoubleType
import pandas as pd
import plotly.express as px
import plotly.io as pio

print("\n===  UNIDAD IV – PCA + KMEANS – UrbanBlade  ===\n")

# ─── 1. Cargar datos reales ───────────────────────────────────────────────────
spark, df, _ = get_spark_session()
df = df.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})
print("Datos cargados:")
df.select("servicio", "barbero", "duracion_min", "precio", "ingreso").show(10)

# ─── 2. Vectorización ────────────────────────────────────────────────────────
assembler = VectorAssembler(
    inputCols=["duracion_min", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)
df_vector = assembler.transform(df)

# ─── 3. Escalado — OBLIGATORIO antes de PCA ──────────────────────────────────
# PCA es sensible a escala: duracion_min (15–90), precio (100–800), ingreso (100–800)
# StandardScaler centra y normaliza cada feature
print("Escalando datos (StandardScaler withMean=True, withStd=True)...")
scaler       = StandardScaler(inputCol="features", outputCol="scaledFeatures",
                              withStd=True, withMean=True)
scaler_model = scaler.fit(df_vector)
df_scaled    = scaler_model.transform(df_vector)
print("Datos escalados correctamente")

# ─── 4. PCA (3 variables → 2 componentes) ────────────────────────────────────
print("\nAplicando PCA (3 features → 2 componentes principales)...")
pca       = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures")
pca_model = pca.fit(df_scaled)
df_pca    = pca_model.transform(df_scaled)
print("PCA aplicado correctamente")

varianza = pca_model.explainedVariance
print(f"\nVarianza explicada por componente:")
print(f"  PC1: {varianza[0]*100:.1f}%")
print(f"  PC2: {varianza[1]*100:.1f}%")
print(f"  Total: {sum(varianza)*100:.1f}% de la varianza total")

print("\nPesos (cargas) de las variables en cada componente:")
print("  Columnas → [duracion_min, precio, ingreso]")
print(f"  PC1: {pca_model.pc.toArray()[:,0].round(4)}")
print(f"  PC2: {pca_model.pc.toArray()[:,1].round(4)}")

# ─── 5. KMeans sobre las 2 componentes principales ───────────────────────────
print("\nAplicando KMeans (K=3) sobre las componentes PCA...")
kmeans       = KMeans(k=3, seed=42, featuresCol="pcaFeatures", predictionCol="cluster")
kmeans_model = kmeans.fit(df_pca)
df_cluster   = kmeans_model.transform(df_pca)
print("Clustering aplicado correctamente")

# ─── 6. Silhouette Score ──────────────────────────────────────────────────────
silhouette = ClusteringEvaluator(
    featuresCol="pcaFeatures", predictionCol="cluster", metricName="silhouette"
).evaluate(df_cluster)
print(f"\nSilhouette Score (PCA+KMeans): {silhouette:.4f}")

# ─── 7. Centroides e interpretación ──────────────────────────────────────────
centros = kmeans_model.clusterCenters()
print("\nCENTROIDES en espacio PCA (PC1, PC2):")
for i, c in enumerate(centros):
    print(f"  Cluster {i}: PC1={c[0]:.4f}  PC2={c[1]:.4f}")

def interpretar_cluster(centroid):
    pc1, pc2 = centroid
    desc_pc1 = "duración/precio/ingreso ALTOS" if pc1 > 0 else "duración/precio/ingreso BAJOS"
    desc_pc2 = "contraste positivo entre features" if pc2 > 0 else "contraste negativo entre features"
    return f"{desc_pc1}; {desc_pc2}"

print("\nInterpretación de clusters:")
for i, c in enumerate(centros):
    print(f"  Cluster {i}: {interpretar_cluster(c)}")

print("\nDistribución por cluster:")
df_cluster.groupBy("cluster").count().orderBy("cluster").show()

# ─── 8. Visualización (Plotly scatter) ───────────────────────────────────────
vector_to_array = udf(lambda v: v.toArray().tolist(), ArrayType(DoubleType()))
df_final = df_cluster.withColumn("pcaArray", vector_to_array("pcaFeatures"))

print("Generando visualización interactiva (Plotly)...")
pdf = df_final.select("pcaArray", "cluster", "servicio", "barbero",
                      "duracion_min", "precio", "ingreso").toPandas()
pdf["PC1"] = pdf["pcaArray"].apply(lambda x: x[0])
pdf["PC2"] = pdf["pcaArray"].apply(lambda x: x[1])

fig = px.scatter(
    pdf,
    x="PC1",
    y="PC2",
    color=pdf["cluster"].astype(str),
    hover_data=["servicio", "barbero", "duracion_min", "precio", "ingreso"],
    title=f"PCA + KMeans (K=3) – UrbanBlade  |  Varianza explicada: {sum(varianza)*100:.1f}%  "
          f"|  Silhouette: {silhouette:.3f}",
    labels={"color": "Cluster"},
    color_discrete_sequence=px.colors.qualitative.Set1
)
fig.add_annotation(
    text=f"PC1 explica {varianza[0]*100:.1f}% | PC2 explica {varianza[1]*100:.1f}%",
    xref="paper", yref="paper", x=0, y=1.05, showarrow=False, font=dict(size=11)
)
pio.renderers.default = "browser"
fig.show()

# ─── 9. Resumen final ─────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("RESUMEN PCA + KMEANS – UNIDAD IV")
print("=" * 55)
print(f"  Features originales : duracion_min, precio, ingreso")
print(f"  Componentes PCA     : 2 (PC1 + PC2)")
print(f"  Varianza explicada  : {sum(varianza)*100:.1f}%")
print(f"  Clusters            : 3")
print(f"  Silhouette Score    : {silhouette:.4f}")
print(f"  Evaluación          : {'Buena' if silhouette > 0.5 else 'Aceptable' if silhouette > 0.2 else 'Débil'} segmentación")

spark.stop()
print("\nProceso finalizado correctamente")
