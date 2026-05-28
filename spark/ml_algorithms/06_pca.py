import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.mongo_spark_conexion import get_spark_session
from pyspark.ml.feature import StandardScaler, PCA, VectorAssembler
from pyspark.ml.clustering import KMeans
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col
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

# 3. PCA — reducir a 2 componentes principales
print("Aplicando PCA...")
pca       = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures")
pca_model = pca.fit(df_scaled)
df_pca    = pca_model.transform(df_scaled)
print("PCA aplicado correctamente")

print("\nVarianza explicada por componente:")
for i, v in enumerate(pca_model.explainedVariance):
    print(f"  PC{i+1}: {round(v * 100, 2)}%")

# 4. CLUSTERING sobre componentes PCA
print("\nAplicando KMeans sobre PCA...")
kmeans       = KMeans(k=3, featuresCol="pcaFeatures", predictionCol="cluster", seed=42)
kmeans_model = kmeans.fit(df_pca)
df_cluster   = kmeans_model.transform(df_pca)
print("Clustering aplicado correctamente")

print("\nCentroides de clusters (espacio PCA):")
for i, c in enumerate(kmeans_model.clusterCenters()):
    print(f"  Cluster {i}: PC1={round(c[0],4)}, PC2={round(c[1],4)}")

# 5. INTERPRETACIÓN AUTOMÁTICA
def interpretar_cluster(centroid):
    pc1, pc2 = centroid
    desc = []
    desc.append("ingresos/precios ALTOS" if pc1 > 0 else "ingresos/precios BAJOS")
    desc.append("segunda dimensión POSITIVA" if pc2 > 0 else "segunda dimensión NEGATIVA")
    return ", ".join(desc)

print("\nInterpretación de clusters UrbanBlade:")
for i, c in enumerate(kmeans_model.clusterCenters()):
    print(f"  Cluster {i}: {interpretar_cluster(c)}")

# 6. Convertir DenseVector a array para visualización
df_final = df_cluster.withColumn("pcaArray", vector_to_array(col("pcaFeatures")))

print("\nGenerando DataFrame para visualización...")
pdf = df_final.select("pcaArray", "cluster").toPandas()
pdf["PC1"] = pdf["pcaArray"].apply(lambda x: x[0])
pdf["PC2"] = pdf["pcaArray"].apply(lambda x: x[1])

# 7. VISUALIZACIÓN con Plotly
print("Generando gráfica interactiva...")
fig = px.scatter(
    pdf,
    x="PC1",
    y="PC2",
    color=pdf["cluster"].astype(str),
    title="PCA + KMeans – Segmentación UrbanBlade",
    labels={"color": "Cluster"}
)
pio.renderers.default = "browser"
fig.show()

spark.stop()
print("\nProceso PCA finalizado correctamente")
