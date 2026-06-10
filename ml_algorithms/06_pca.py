import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion import get_spark_session
from pyspark.ml.feature import StandardScaler, PCA, VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, DoubleType
import pandas as pd
import plotly.express as px
import plotly.io as pio

spark, df, df_vector = get_spark_session()

df = df.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})

assembler = VectorAssembler(
    inputCols=["duracion_min", "precio", "ingreso"],
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
    desc.append("duración/precio/ingreso ALTOS" if pc1 > 0
                 else "duración/precio/ingreso BAJOS")
    desc.append("segunda componente POSITIVA" if pc2 > 0
                 else "segunda componente NEGATIVA")
    return ", ".join(desc)


print("\nInterpretación de clusters:")
for i, c in enumerate(kmeans_model.clusterCenters()):
    print(f"Cluster {i}: {interpretar_cluster(c)}")

print("\nPesos de los componentes principales:")
print(pca_model.pc)

# 6. DenseVector → lista Python
vector_to_array = udf(lambda v: v.toArray().tolist(), ArrayType(DoubleType()))
df_final = df_cluster.withColumn("pcaArray", vector_to_array("pcaFeatures"))

print("\nGenerando DataFrame para visualización...")
pdf = df_final.select("pcaArray", "cluster", "servicio", "barbero").toPandas()
pdf["PC1"] = pdf["pcaArray"].apply(lambda x: x[0])
pdf["PC2"] = pdf["pcaArray"].apply(lambda x: x[1])

# 7. VISUALIZACIÓN
print("Generando gráfica...")
fig = px.scatter(
    pdf,
    x="PC1",
    y="PC2",
    color=pdf["cluster"].astype(str),
    hover_data=["servicio", "barbero"],
    title="PCA + KMeans – UrbanBlade (datos reales)"
)
pio.renderers.default = "browser"
fig.show()

spark.stop()
print("\nProceso finalizado correctamente")
