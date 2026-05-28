import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from config.mongo_spark_conexion_sinnulos import get_spark_session

st.set_page_config(
    page_title="UrbanBlade – Segmentación KMeans",
    page_icon="💈",
    layout="wide"
)

st.title("💈 Dashboard Ejecutivo – Segmentación con KMeans | UrbanBlade")
st.markdown("*Machine Learning aplicado a la barbería – Extracción del Conocimiento en BD*")

k_value = st.sidebar.slider("Número de Clusters (K)", min_value=2, max_value=8, value=3)


@st.cache_resource
def cargar_y_entrenar(k):
    spark, df, df_vector = get_spark_session()
    kmeans     = KMeans(k=k, seed=42)
    model      = kmeans.fit(df_vector)
    result     = model.transform(df_vector)
    evaluator  = ClusteringEvaluator()
    silhouette = evaluator.evaluate(result)
    pdf = result.select(
        "servicio", "barbero", "cantidad", "precio", "ingreso", "prediction"
    ).toPandas()
    centers = [c.tolist() for c in model.clusterCenters()]
    spark.stop()
    return pdf, silhouette, centers


data, silhouette_score, centroids = cargar_y_entrenar(k_value)

# MÉTRICAS EJECUTIVAS
col1, col2, col3, col4 = st.columns(4)
col1.metric("Citas Totales",       f"{len(data):,}")
col2.metric("Ingreso Total",       f"${data['ingreso'].sum():,.0f}")
col3.metric("Ingreso Promedio",    f"${data['ingreso'].mean():,.0f}")
col4.metric("Silhouette Score",    round(silhouette_score, 4))

# FILTRO DE CLUSTERS
cluster_filter = st.sidebar.multiselect(
    "Filtrar por Cluster",
    sorted(data["prediction"].unique()),
    default=sorted(data["prediction"].unique())
)
data_filtrada = data[data["prediction"].isin(cluster_filter)]

# GRÁFICA 2D – Precio vs Ingreso
st.subheader("Precio vs Ingreso por Cluster")
fig = px.scatter(
    data_filtrada,
    x="precio", y="ingreso",
    color=data_filtrada["prediction"].astype(str),
    hover_data=["servicio", "barbero", "cantidad"],
    title="Segmentación de Citas – UrbanBlade"
)
st.plotly_chart(fig, use_container_width=True)

# GRÁFICA 3D
st.subheader("Visualización 3D – Precio / Cantidad / Ingreso")
fig_3d = px.scatter_3d(
    data_filtrada,
    x="precio", y="cantidad", z="ingreso",
    color=data_filtrada["prediction"].astype(str),
    hover_name="servicio"
)
st.plotly_chart(fig_3d, use_container_width=True)

# MÉTODO DEL CODO
st.subheader("Método del Codo")


@st.cache_resource
def metodo_del_codo():
    spark, df, df_vector = get_spark_session()
    wcss = []
    for k in range(2, 9):
        m = KMeans(k=k, seed=42).fit(df_vector)
        wcss.append(m.summary.trainingCost)
    spark.stop()
    return wcss


wcss_values = metodo_del_codo()
fig_elbow = go.Figure()
fig_elbow.add_trace(go.Scatter(
    x=list(range(2, 9)), y=wcss_values, mode="lines+markers",
    line=dict(color="#d4af37", width=2)
))
fig_elbow.update_layout(
    xaxis_title="Número de Clusters (K)",
    yaxis_title="WCSS",
    title="Método del Codo – UrbanBlade"
)
st.plotly_chart(fig_elbow, use_container_width=True)

# INGRESOS POR SERVICIO
st.subheader("Ingresos por Servicio")
by_servicio = data_filtrada.groupby("servicio")["ingreso"].sum().reset_index()
fig_bar = px.bar(by_servicio, x="servicio", y="ingreso",
                 color="ingreso", title="Ingreso Total por Servicio",
                 color_continuous_scale="Viridis")
st.plotly_chart(fig_bar, use_container_width=True)

# INTERPRETACIÓN EJECUTIVA
st.subheader("Interpretación Ejecutiva por Cluster")
resumen = data.groupby("prediction").mean(numeric_only=True)

for cluster in resumen.index:
    ingreso = resumen.loc[cluster, "ingreso"]
    precio  = resumen.loc[cluster, "precio"]
    st.markdown(f"### Cluster {cluster}")
    st.write(f"Ingreso promedio: **${round(ingreso, 2):,.0f}**")
    st.write(f"Precio promedio: **${round(precio, 2):,.0f}**")
    if ingreso == resumen["ingreso"].max():
        st.success("Segmento Estratégico (Mayor ingreso)")
    elif precio == resumen["precio"].max():
        st.info("Segmento Premium (Precio alto)")
    else:
        st.warning("Segmento Operativo")
