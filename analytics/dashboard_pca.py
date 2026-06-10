import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.ml.feature import VectorAssembler, StandardScaler, PCA
from pyspark.ml.clustering import KMeans
from pyspark.sql.functions import col, avg
from pyspark.ml.functions import vector_to_array
from config.mongo_spark_conexion import get_spark_session

st.set_page_config(page_title="Dashboard PCA – UrbanBlade", layout="wide")
st.title("Dashboard Inteligente: PCA + Clustering + IA | UrbanBlade")

st.sidebar.header("Configuración")
k_clusters = st.sidebar.slider("Número de clusters", 2, 6, 3)


def interpretar_clusters(perfil_df):
    interpretaciones = []
    avg_global = perfil_df.mean(numeric_only=True)

    for _, row in perfil_df.iterrows():
        cluster  = int(row["cluster"])
        ingreso  = row["avg_ingreso"]
        precio   = row["avg_precio"]
        duracion = row["avg_duracion"]

        texto = f"Cluster {cluster}:\n"

        texto += "- Ingreso superior al promedio\n" if ingreso > avg_global["avg_ingreso"] \
            else "- Ingreso inferior al promedio\n"

        texto += "- Precio de servicio alto\n" if precio > avg_global["avg_precio"] \
            else "- Precio de servicio económico\n"

        texto += "- Servicios de larga duración\n" if duracion > avg_global["avg_duracion"] \
            else "- Servicios rápidos\n"

        if ingreso > avg_global["avg_ingreso"] and precio > avg_global["avg_precio"]:
            perfil = "Cliente Premium"
        elif ingreso < avg_global["avg_ingreso"] and duracion > avg_global["avg_duracion"]:
            perfil = "Cliente Frecuente Económico"
        else:
            perfil = "Cliente Estándar"

        texto += f"\nPerfil: {perfil}\n"
        texto += "\nRecomendaciones:\n"

        if perfil == "Cliente Premium":
            texto += "- Ofrecer servicios VIP\n- Programa de fidelidad\n"
        elif perfil == "Cliente Frecuente Económico":
            texto += "- Combos y descuentos por volumen\n"
        else:
            texto += "- Estrategias mixtas de retención\n"

        interpretaciones.append(texto)

    return interpretaciones


if st.button("Ejecutar análisis"):

    spark, df, _ = get_spark_session()

    df = df.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})

    assembler = VectorAssembler(
        inputCols=["duracion_min", "precio", "ingreso"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_vector = assembler.transform(df)

    scaler    = StandardScaler(inputCol="features", outputCol="scaledFeatures",
                               withMean=True, withStd=True)
    df_scaled = scaler.fit(df_vector).transform(df_vector)

    pca       = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures")
    pca_model = pca.fit(df_scaled)
    df_pca    = pca_model.transform(df_scaled)

    varianza  = pca_model.explainedVariance
    c1, c2    = st.columns(2)
    c1.metric("Varianza PC1", f"{round(varianza[0]*100, 2)}%")
    c2.metric("Varianza PC2", f"{round(varianza[1]*100, 2)}%")

    kmeans    = KMeans(k=k_clusters, featuresCol="pcaFeatures", predictionCol="cluster")
    model     = kmeans.fit(df_pca)
    df_cluster = model.transform(df_pca)

    df_cluster = df_cluster.withColumn(
        "pcaArray", vector_to_array(col("pcaFeatures"))
    )
    df_cluster = df_cluster.withColumn("PC1", col("pcaArray")[0])
    df_cluster = df_cluster.withColumn("PC2", col("pcaArray")[1])

    pdf = df_cluster.select(
        "PC1", "PC2", "cluster", "duracion_min", "precio", "ingreso", "servicio", "barbero"
    ).toPandas()

    st.subheader("Mapa de clusters – Citas UrbanBlade (datos reales)")
    fig = px.scatter(
        pdf,
        x="PC1",
        y="PC2",
        color=pdf["cluster"].astype(str),
        hover_data=["servicio", "barbero", "precio", "duracion_min"],
        title="Segmentación de Citas – PCA + KMeans"
    )
    st.plotly_chart(fig, use_container_width=True)

    perfil = df_cluster.groupBy("cluster").agg(
        avg("duracion_min").alias("avg_duracion"),
        avg("precio").alias("avg_precio"),
        avg("ingreso").alias("avg_ingreso")
    ).toPandas()

    st.subheader("Perfil de clusters")
    st.dataframe(perfil)

    st.subheader("Interpretación inteligente")
    for texto in interpretar_clusters(perfil):
        st.code(texto)

    st.subheader("Datos")
    st.dataframe(pdf.head(100))

    spark.stop()
