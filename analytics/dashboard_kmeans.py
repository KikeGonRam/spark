import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

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
    kmeans     = KMeans(k=k, seed=1)
    model      = kmeans.fit(df_vector)
    result     = model.transform(df_vector)
    evaluator  = ClusteringEvaluator()
    silhouette = evaluator.evaluate(result)
    pdf = result.select(
        "servicio", "barbero", "duracion_min", "precio", "ingreso", "estado", "prediction"
    ).toPandas()
    spark.stop()
    return pdf, silhouette


data, silhouette_score = cargar_y_entrenar(k_value)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Citas Totales",    len(data))
col2.metric("Ingreso Total",    f"${round(data['ingreso'].sum(), 2):,.0f}")
col3.metric("Ingreso Promedio", f"${round(data['ingreso'].mean(), 2):,.0f}")
col4.metric("Silhouette Score", round(silhouette_score, 4))

cluster_filter = st.sidebar.multiselect(
    "Filtrar por Cluster",
    sorted(data["prediction"].unique()),
    default=sorted(data["prediction"].unique())
)
data_filtrada = data[data["prediction"].isin(cluster_filter)]

st.subheader("Precio vs Ingreso por Cluster")
fig = px.scatter(
    data_filtrada,
    x="precio",
    y="ingreso",
    color="prediction",
    hover_data=["servicio", "barbero", "duracion_min", "estado"],
    title="Segmentación de Citas – UrbanBlade (datos reales)"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Visualización 3D")
fig_3d = px.scatter_3d(
    data_filtrada,
    x="precio",
    y="duracion_min",
    z="ingreso",
    color="prediction",
    hover_name="servicio",
    labels={"duracion_min": "Duración (min)"}
)
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
fig_elbow.add_trace(go.Scatter(
    x=list(range(2, 9)), y=wcss_values, mode="lines+markers"
))
fig_elbow.update_layout(xaxis_title="K", yaxis_title="WCSS", title="Método del Codo")
st.plotly_chart(fig_elbow, use_container_width=True)

st.subheader("Interpretación Ejecutiva")
resumen = data.groupby("prediction").mean(numeric_only=True)
for cluster in resumen.index:
    ingreso   = resumen.loc[cluster, "ingreso"]
    precio    = resumen.loc[cluster, "precio"]
    duracion  = resumen.loc[cluster, "duracion_min"]
    st.markdown(f"### Cluster {cluster}")
    st.write(f"Ingreso promedio: ${round(ingreso, 2):,.0f}")
    st.write(f"Precio promedio: ${round(precio, 2):,.0f}")
    st.write(f"Duración promedio: {round(duracion, 1)} min")
    if ingreso == resumen["ingreso"].max():
        st.success("Segmento Estratégico (Mayor ingreso)")
    elif precio == resumen["precio"].max():
        st.info("Segmento Premium")
    else:
        st.warning("Segmento Operativo")
