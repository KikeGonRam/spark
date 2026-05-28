import streamlit as st
import plotly.express as px
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.ml.feature import VectorAssembler, StandardScaler, PCA
from pyspark.ml.clustering import KMeans
from pyspark.ml.functions import vector_to_array
from pyspark.sql.functions import col, avg
from config.mongo_spark_conexion import get_spark_session

st.set_page_config(
    page_title="UrbanBlade – PCA + Clustering",
    page_icon="💈",
    layout="wide"
)

st.title("💈 Dashboard Inteligente: PCA + Clustering | UrbanBlade")
st.markdown("*Reducción de dimensionalidad y segmentación avanzada – Extracción del Conocimiento en BD*")

st.sidebar.header("Configuración")
k_clusters = st.sidebar.slider("Número de clusters", 2, 6, 3)


def interpretar_clusters_avanzado(perfil_df):
    interpretaciones = []
    avg_global = perfil_df.mean(numeric_only=True)

    for _, row in perfil_df.iterrows():
        cluster  = int(row["cluster"])
        ingreso  = row["avg_ingreso"]
        precio   = row["avg_precio"]
        cantidad = row["avg_cantidad"]

        texto = f"Cluster {cluster}:\n"

        texto += ("- Ingreso SUPERIOR al promedio\n" if ingreso > avg_global["avg_ingreso"]
                  else "- Ingreso INFERIOR al promedio\n")
        texto += ("- Servicios de precio ALTO\n" if precio > avg_global["avg_precio"]
                  else "- Servicios de precio BAJO\n")
        texto += ("- Alta demanda (muchas citas)\n" if cantidad > avg_global["avg_cantidad"]
                  else "- Baja demanda (pocas citas)\n")

        if ingreso > avg_global["avg_ingreso"] and precio > avg_global["avg_precio"]:
            perfil = "Segmento Premium"
        elif ingreso < avg_global["avg_ingreso"] and cantidad > avg_global["avg_cantidad"]:
            perfil = "Segmento de Alta Rotación"
        else:
            perfil = "Segmento Estándar"

        texto += f"\nPerfil: {perfil}\n"
        texto += "\nRecomendaciones:\n"
        if perfil == "Segmento Premium":
            texto += "- Ofrecer paquetes VIP\n- Servicios complementarios premium\n"
        elif perfil == "Segmento de Alta Rotación":
            texto += "- Promociones por volumen\n- Descuentos en combos\n"
        else:
            texto += "- Estrategias mixtas\n- Fidelización básica\n"

        interpretaciones.append(texto)

    return interpretaciones


if st.button("Ejecutar análisis PCA + Clustering"):
    with st.spinner("Procesando con PySpark..."):

        spark, df, _ = get_spark_session()

        df = df.fillna({"cantidad": 0, "precio": 0, "ingreso": 0})

        assembler = VectorAssembler(
            inputCols=["cantidad", "precio", "ingreso"],
            outputCol="features",
            handleInvalid="skip"
        )
        df_vector = assembler.transform(df)

        # Escalado — obligatorio antes de PCA
        scaler    = StandardScaler(inputCol="features", outputCol="scaledFeatures",
                                   withMean=True, withStd=True)
        df_scaled = scaler.fit(df_vector).transform(df_vector)

        # PCA a 2 componentes
        pca       = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures")
        pca_model = pca.fit(df_scaled)
        df_pca    = pca_model.transform(df_scaled)

        varianza = pca_model.explainedVariance
        c1, c2 = st.columns(2)
        c1.metric("Varianza PC1", f"{round(varianza[0]*100, 2)}%")
        c2.metric("Varianza PC2", f"{round(varianza[1]*100, 2)}%")

        # KMeans sobre espacio PCA
        kmeans    = KMeans(k=k_clusters, featuresCol="pcaFeatures",
                           predictionCol="cluster", seed=42)
        model     = kmeans.fit(df_pca)
        df_cluster = model.transform(df_pca)

        # Extraer componentes PCA a columnas
        df_cluster = df_cluster.withColumn("pcaArray", vector_to_array(col("pcaFeatures")))
        df_cluster = df_cluster.withColumn("PC1", col("pcaArray")[0])
        df_cluster = df_cluster.withColumn("PC2", col("pcaArray")[1])

        pdf = df_cluster.select(
            "PC1", "PC2", "cluster", "cantidad", "precio", "ingreso"
        ).toPandas()

        # Perfil de clusters
        perfil = df_cluster.groupBy("cluster").agg(
            avg("cantidad").alias("avg_cantidad"),
            avg("precio").alias("avg_precio"),
            avg("ingreso").alias("avg_ingreso")
        ).toPandas()

        spark.stop()

    # Mapa de clusters
    st.subheader("Mapa de Clusters (Espacio PCA)")
    fig = px.scatter(
        pdf, x="PC1", y="PC2",
        color=pdf["cluster"].astype(str),
        title="Segmentación UrbanBlade – PCA + KMeans",
        labels={"color": "Cluster"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Perfil de clusters
    st.subheader("Perfil de Clusters")
    st.dataframe(perfil.round(2))

    # Interpretación IA
    st.subheader("Interpretación Inteligente")
    interpretaciones = interpretar_clusters_avanzado(perfil)
    for texto in interpretaciones:
        st.code(texto)

    # Tabla de datos
    st.subheader("Datos procesados (primeros 100 registros)")
    st.dataframe(pdf.head(100))
