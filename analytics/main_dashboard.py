"""
Dashboard Principal – UrbanBlade Analytics
Unidades II–V | Materia: Extracción del conocimiento en bases de datos
UTVT IDGS-84 | MGTI. Héctor Velázquez Estrada | Mayo–Agosto 2026
Alumno: KikeGonRam (Luis Enrique González Ramírez)

Ejecutar:  streamlit run analytics/main_dashboard.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UrbanBlade Analytics",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

GOLD   = "#d4af37"
DARK   = "#0e0e0e"
CARD   = "#1a1a1a"
GREEN  = "#2ecc71"
RED    = "#e74c3c"
BLUE   = "#3498db"
PURPLE = "#9b59b6"

st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{ background-color: {DARK}; }}
  [data-testid="stSidebar"]          {{ background-color: #111; }}
  h1, h2, h3, h4                     {{ color: {GOLD}; }}
  .stMetric label                    {{ color: #aaa !important; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
  .stMetric [data-testid="stMetricValue"] {{ color: white !important; font-size: 1.6rem; font-weight: 900; }}
  .stTabs [data-baseweb="tab"]        {{ color: #888; font-weight: 700; font-size: 13px; }}
  .stTabs [aria-selected="true"]      {{ color: {GOLD} !important; border-bottom: 2px solid {GOLD}; }}
  div[data-testid="stHorizontalBlock"] > div {{ border-radius: 12px; }}
  .block-container {{ padding-top: 1.5rem; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS (UNA VEZ POR SESIÓN)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando a MongoDB Atlas y cargando datos reales…")
def cargar_datos():
    from config.mongo_spark_conexion_sinnulos import get_spark_session
    from pyspark.sql.functions import when, col
    spark, df, df_vector = get_spark_session()
    pdf = df.toPandas()
    return spark, df, df_vector, pdf

@st.cache_resource(show_spinner="Entrenando modelos de regresión…")
def entrenar_regresion(_spark, _df):
    from pyspark.ml.feature import VectorAssembler, PolynomialExpansion
    from pyspark.ml.regression import LinearRegression
    from pyspark.ml.evaluation import RegressionEvaluator
    from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

    train, test = _df.randomSplit([0.8, 0.2], seed=42)

    def evaluar(preds):
        r2  = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="r2").evaluate(preds)
        mse = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="mse").evaluate(preds)
        mae = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="mae").evaluate(preds)
        return round(r2, 4), round(mse, 2), round(mae, 2)

    a1   = VectorAssembler(inputCols=["duracion_min"], outputCol="features", handleInvalid="skip")
    p1   = LinearRegression(featuresCol="features", labelCol="ingreso").fit(a1.transform(train)).transform(a1.transform(test))
    r1   = evaluar(p1)
    pdf1 = p1.select("duracion_min", "ingreso", "prediction").toPandas()

    a2   = VectorAssembler(inputCols=["duracion_min", "precio"], outputCol="features", handleInvalid="skip")
    tr2  = a2.transform(train); te2 = a2.transform(test)
    m2   = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr2)
    p2   = m2.transform(te2)
    r2   = evaluar(p2)

    m3   = LinearRegression(featuresCol="features", labelCol="ingreso", regParam=0.5, elasticNetParam=0).fit(tr2)
    r3   = evaluar(m3.transform(te2))
    m4   = LinearRegression(featuresCol="features", labelCol="ingreso", regParam=0.5, elasticNetParam=1).fit(tr2)
    r4   = evaluar(m4.transform(te2))

    poly = PolynomialExpansion(inputCol="features", outputCol="pf", degree=2)
    m5   = LinearRegression(featuresCol="pf", labelCol="ingreso").fit(poly.transform(tr2))
    r5   = evaluar(m5.transform(poly.transform(te2)))

    ev   = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="r2")
    lr   = LinearRegression(featuresCol="features", labelCol="ingreso")
    pg   = ParamGridBuilder().addGrid(lr.regParam, [0.01, 0.1, 1]).addGrid(lr.elasticNetParam, [0, 0.5, 1]).build()
    cv   = CrossValidator(estimator=lr, estimatorParamMaps=pg, evaluator=ev, numFolds=3)
    r6   = evaluar(cv.fit(tr2).transform(te2))

    tabla = pd.DataFrame({
        "Modelo":  ["Lineal Simple", "Lineal Múltiple", "Ridge (L2)", "Lasso (L1)", "Polinomial", "Cross Validation"],
        "R²":      [r1[0], r2[0], r3[0], r4[0], r5[0], r6[0]],
        "MSE":     [r1[1], r2[1], r3[1], r4[1], r5[1], r6[1]],
        "MAE":     [r1[2], r2[2], r3[2], r4[2], r5[2], r6[2]],
    })
    return tabla, pdf1

@st.cache_resource(show_spinner="Entrenando Árbol de Decisión…")
def entrenar_arbol(_spark, _df):
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.classification import DecisionTreeClassifier
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
    from pyspark.sql.functions import when, col

    df2   = _df.withColumn("label", when(col("ingreso") > 500, 1).otherwise(0))
    asm   = VectorAssembler(inputCols=["duracion_min", "precio", "ingreso"], outputCol="features", handleInvalid="skip")
    ds    = asm.transform(df2).select("features", "label", "servicio", "precio", "ingreso", "duracion_min")
    tr, te = ds.randomSplit([0.8, 0.2], seed=42)
    model = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=5).fit(tr)
    preds = model.transform(te)

    def m(name): return MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName=name).evaluate(preds)
    metrics = {"Accuracy": round(m("accuracy"), 4), "Precision": round(m("weightedPrecision"), 4),
               "Recall": round(m("weightedRecall"), 4), "F1": round(m("f1"), 4),
               "AUC": round(BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC").evaluate(preds), 4)}

    conf = preds.groupBy("label", "prediction").count().toPandas()
    feat_imp = list(model.featureImportances)
    return metrics, conf, feat_imp

@st.cache_resource(show_spinner="Entrenando Random Forest…")
def entrenar_rf(_spark, _df):
    from pyspark.ml import Pipeline
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
    from pyspark.sql.functions import when, col

    df2  = _df.withColumn("categoria", when(col("estado").isin("cancelada", "no_asistio"), 1).otherwise(0))
    df2  = df2.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})
    tr, te = df2.randomSplit([0.7, 0.3], seed=42)
    asm  = VectorAssembler(inputCols=["duracion_min", "precio", "ingreso"], outputCol="features", handleInvalid="skip")
    rf   = RandomForestClassifier(featuresCol="features", labelCol="categoria", numTrees=100, maxDepth=5, seed=42)
    model = Pipeline(stages=[asm, rf]).fit(tr)
    preds = model.transform(te)

    auc  = round(BinaryClassificationEvaluator(labelCol="categoria", metricName="areaUnderROC").evaluate(preds), 4)
    def m(name): return round(MulticlassClassificationEvaluator(labelCol="categoria", predictionCol="prediction", metricName=name).evaluate(preds), 4)
    metrics = {"Accuracy": m("accuracy"), "Precision": m("weightedPrecision"),
               "Recall": m("weightedRecall"), "F1": m("f1"), "AUC": auc}
    conf     = preds.groupBy("categoria", "prediction").count().toPandas()
    feat_imp = list(model.stages[-1].featureImportances)
    dist     = df2.groupBy("estado").count().toPandas()
    return metrics, conf, feat_imp, dist

@st.cache_resource(show_spinner="Ejecutando KMeans y Método del Codo…")
def entrenar_kmeans(_df_vector, k=3):
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    wcss, sil_scores = [], []
    for ki in range(2, 9):
        m  = KMeans(k=ki, seed=42, featuresCol="features", predictionCol="cluster").fit(_df_vector)
        r  = m.transform(_df_vector)
        ev = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette")
        wcss.append(m.summary.trainingCost)
        sil_scores.append(round(ev.evaluate(r), 4))
    model  = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster").fit(_df_vector)
    result = model.transform(_df_vector)
    ev     = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette")
    sil    = round(ev.evaluate(result), 4)
    pdf    = result.select("servicio", "barbero", "duracion_min", "precio", "ingreso", "estado", "cluster").toPandas()
    centers = [(round(c[0],1), round(c[1],2), round(c[2],2)) for c in model.clusterCenters()]
    return list(range(2, 9)), wcss, sil_scores, pdf, sil, centers

@st.cache_resource(show_spinner="Ejecutando PCA + KMeans…")
def entrenar_pca(_df_vector, _df):
    from pyspark.ml.feature import StandardScaler, PCA, VectorAssembler
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    from pyspark.sql.functions import udf
    from pyspark.sql.types import ArrayType, DoubleType
    df2  = _df.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})
    asm  = VectorAssembler(inputCols=["duracion_min", "precio", "ingreso"], outputCol="features", handleInvalid="skip")
    dv   = asm.transform(df2)
    sc   = StandardScaler(inputCol="features", outputCol="sf", withStd=True, withMean=True).fit(dv).transform(dv)
    pca  = PCA(k=2, inputCol="sf", outputCol="pf")
    pm   = pca.fit(sc); dp = pm.transform(sc)
    km   = KMeans(k=3, seed=42, featuresCol="pf", predictionCol="cluster").fit(dp)
    dc   = km.transform(dp)
    sil  = round(ClusteringEvaluator(featuresCol="pf", predictionCol="cluster").evaluate(dc), 4)
    v2a  = udf(lambda v: v.toArray().tolist(), ArrayType(DoubleType()))
    dc   = dc.withColumn("arr", v2a("pf"))
    pdf  = dc.select("arr", "cluster", "servicio", "barbero", "duracion_min", "precio", "ingreso").toPandas()
    pdf["PC1"] = pdf["arr"].apply(lambda x: x[0])
    pdf["PC2"] = pdf["arr"].apply(lambda x: x[1])
    var  = [round(float(v)*100, 1) for v in pm.explainedVariance]
    return pdf, var, sil

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h1 style='color:{GOLD};font-size:28px;margin-bottom:0'>✂️ UrbanBlade</h1>", unsafe_allow_html=True)
    st.caption("Extracción del conocimiento en BD · UTVT IDGS-84")
    st.divider()
    st.markdown("**Alumno:** KikeGonRam")
    st.markdown("**Docente:** MGTI. Héctor Velázquez Estrada")
    st.markdown("**Período:** Mayo–Agosto 2026")
    st.divider()
    st.markdown("**Filtros**")
    k_clusters = st.slider("Clusters KMeans (K)", 2, 8, 3)
    st.divider()
    st.caption("MongoDB Atlas → barber_db")

# ─────────────────────────────────────────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────────────────────────────────────────
try:
    spark, df, df_vector, pdf = cargar_datos()
except Exception as e:
    st.error(f"Error al conectar con MongoDB Atlas: {e}")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER + KPIs GLOBALES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"<h1 style='text-align:center;color:{GOLD};font-size:2.2rem;'>✂️ UrbanBlade Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#888;margin-top:-10px;'>Extracción del conocimiento en bases de datos · Datos reales MongoDB Atlas</p>", unsafe_allow_html=True)
st.divider()

c1, c2, c3, c4, c5 = st.columns(5)
completadas = pdf[pdf["estado"] == "completada"]
c1.metric("Total Citas",       f"{len(pdf):,}")
c2.metric("Ingreso Total",     f"${pdf['ingreso'].sum():,.0f}")
c3.metric("Ingreso Promedio",  f"${pdf['ingreso'].mean():,.0f}")
c4.metric("Tasa Completadas",  f"{len(completadas)/len(pdf)*100:.1f}%")
c5.metric("Servicios Únicos",  pdf["servicio"].nunique())

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 Resumen General",
    "🔄 MapReduce",
    "📈 Regresión",
    "🌳 Árbol de Decisión",
    "🌲 Random Forest",
    "🔵 KMeans",
    "🔷 PCA",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUMEN GENERAL
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Resumen General del Negocio")

    col_a, col_b = st.columns(2)

    with col_a:
        # Distribución de estados
        estados = pdf["estado"].value_counts().reset_index()
        estados.columns = ["estado", "count"]
        fig = px.pie(estados, values="count", names="estado",
                     title="Distribución de Estados de Citas",
                     color_discrete_sequence=px.colors.qualitative.Set3,
                     hole=0.4)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", legend_font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Top barberos por citas
        top_barberos = pdf.groupby("barbero").size().reset_index(name="citas").sort_values("citas", ascending=False).head(10)
        fig2 = px.bar(top_barberos, x="citas", y="barbero", orientation="h",
                      title="Top 10 Barberos por Número de Citas",
                      color="citas", color_continuous_scale=[[0, "#444"], [1, GOLD]])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", yaxis=dict(autorange="reversed"),
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        # Ingresos por servicio
        por_svc = pdf.groupby("servicio")["ingreso"].sum().reset_index().sort_values("ingreso", ascending=False)
        fig3 = px.bar(por_svc, x="servicio", y="ingreso",
                      title="Ingreso Total por Tipo de Servicio",
                      color="ingreso", color_continuous_scale=[[0, "#444"], [1, GOLD]],
                      labels={"ingreso": "Ingreso ($MXN)", "servicio": "Servicio"})
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        # Histograma de precios
        fig4 = px.histogram(pdf, x="precio", nbins=30,
                            title="Distribución de Precios de Citas",
                            color_discrete_sequence=[GOLD],
                            labels={"precio": "Precio ($MXN)", "count": "Frecuencia"})
        fig4.add_vline(x=pdf["precio"].mean(), line_dash="dash", line_color=RED,
                       annotation_text=f"Media: ${pdf['precio'].mean():.0f}", annotation_font_color="white")
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MAPREDUCE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("Unidad II — MapReduce / ETL Distribuido")
    st.caption("MAP → agrupa | REDUCE → agrega métricas por servicio y barbero")

    resumen = pdf.groupby("servicio").agg(
        ingreso_total=("ingreso", "sum"),
        citas=("ingreso", "count"),
        precio_promedio=("precio", "mean"),
        duracion_promedio=("duracion_min", "mean"),
    ).reset_index().sort_values("ingreso_total", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(resumen, x="servicio", y="ingreso_total",
                     title="REDUCE → Ingreso Total por Servicio",
                     color="ingreso_total", color_continuous_scale=[[0, "#333"], [1, GOLD]],
                     labels={"ingreso_total": "Ingreso Total ($MXN)", "servicio": ""})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(resumen.sort_values("citas", ascending=False), x="servicio", y="citas",
                      title="REDUCE → Número de Citas por Servicio",
                      color="citas", color_continuous_scale=[[0, "#333"], [1, BLUE]],
                      labels={"citas": "Número de Citas", "servicio": ""})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig3 = px.scatter(resumen, x="citas", y="ingreso_total", size="precio_promedio",
                          text="servicio", title="Citas vs Ingreso Total (tamaño = precio promedio)",
                          color="ingreso_total", color_continuous_scale=[[0, "#333"], [1, GOLD]])
        fig3.update_traces(textposition="top center", textfont_color="white")
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Ingreso por barbero
        por_barbero = pdf.groupby("barbero")["ingreso"].sum().reset_index().sort_values("ingreso", ascending=False).head(12)
        fig4 = px.bar(por_barbero, x="ingreso", y="barbero", orientation="h",
                      title="Ingreso Total por Barbero (Top 12)",
                      color="ingreso", color_continuous_scale=[[0, "#333"], [1, PURPLE]])
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Tabla MapReduce — Resumen por Servicio")
    resumen_display = resumen.copy()
    resumen_display["ingreso_total"]     = resumen_display["ingreso_total"].apply(lambda x: f"${x:,.2f}")
    resumen_display["precio_promedio"]   = resumen_display["precio_promedio"].apply(lambda x: f"${x:,.2f}")
    resumen_display["duracion_promedio"] = resumen_display["duracion_promedio"].apply(lambda x: f"{x:.1f} min")
    resumen_display.columns = ["Servicio", "Ingreso Total", "Núm. Citas", "Precio Promedio", "Duración Promedio"]
    st.dataframe(resumen_display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REGRESIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Unidad III — Análisis Supervisado: Regresión")
    st.caption("6 modelos de regresión | métricas: R², MSE (Error Cuadrático Medio), MAE (Error Absoluto Medio)")

    with st.spinner("Entrenando 6 modelos de regresión sobre datos reales…"):
        tabla_reg, pdf_scatter = entrenar_regresion(spark, df)

    mejor = tabla_reg.loc[tabla_reg["R²"].idxmax()]
    peor  = tabla_reg.loc[tabla_reg["MSE"].idxmax()]

    c1, c2, c3 = st.columns(3)
    c1.metric("Mejor R²",       f"{mejor['R²']:.4f}",  delta=mejor["Modelo"])
    c2.metric("Menor MAE",      f"${tabla_reg['MAE'].min():.2f}")
    c3.metric("Menor MSE",      f"{tabla_reg['MSE'].min():.2f}")

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.bar(tabla_reg, x="Modelo", y="R²",
                     title="Comparación R² — 6 Modelos de Regresión",
                     color="R²", color_continuous_scale=[[0, "#333"], [1, GOLD]],
                     text_auto=".4f")
        fig.add_hline(y=0.9, line_dash="dot", line_color=GREEN, annotation_text="R²=0.9 excelente", annotation_font_color="white")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", coloraxis_showscale=False, xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="MSE", x=tabla_reg["Modelo"], y=tabla_reg["MSE"], marker_color=RED))
        fig2.add_trace(go.Bar(name="MAE", x=tabla_reg["Modelo"], y=tabla_reg["MAE"], marker_color=BLUE))
        fig2.update_layout(title="MSE vs MAE por Modelo",
                           barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", xaxis_tickangle=-20)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        fig3 = px.scatter(pdf_scatter, x="duracion_min", y="ingreso",
                          title="Datos Reales vs Predicción — Regresión Lineal Simple",
                          labels={"duracion_min": "Duración (min)", "ingreso": "Ingreso ($MXN)"},
                          color_discrete_sequence=[BLUE], opacity=0.5)
        fig3.add_scatter(x=pdf_scatter["duracion_min"], y=pdf_scatter["prediction"],
                         mode="markers", name="Predicción", marker=dict(color=GOLD, symbol="x", size=6))
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.subheader("Tabla Comparativa de Modelos")
        st.dataframe(
            tabla_reg.style.highlight_max(subset=["R²"], color="#2d4a1e")
                           .highlight_min(subset=["MSE", "MAE"], color="#2d4a1e")
                           .format({"R²": "{:.4f}", "MSE": "{:.2f}", "MAE": "{:.2f}"}),
            use_container_width=True, hide_index=True
        )
        mejor_idx = tabla_reg["R²"].idxmax()
        st.success(f"✅ Mejor modelo: **{tabla_reg.loc[mejor_idx, 'Modelo']}** — R²={tabla_reg.loc[mejor_idx, 'R²']:.4f}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ÁRBOL DE DECISIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Unidad III — Árbol de Decisión")
    st.caption("Clasificación: cita de ALTO VALOR (ingreso > $500 MXN) = 1  |  BAJO VALOR = 0")

    with st.spinner("Entrenando Árbol de Decisión…"):
        metricas_dt, conf_dt, feat_imp_dt = entrenar_arbol(spark, df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Accuracy",  f"{metricas_dt['Accuracy']*100:.1f}%")
    c2.metric("Precision", f"{metricas_dt['Precision']:.4f}")
    c3.metric("Recall",    f"{metricas_dt['Recall']:.4f}")
    c4.metric("F1-Score",  f"{metricas_dt['F1']:.4f}")
    c5.metric("AUC-ROC",   f"{metricas_dt['AUC']:.4f}")

    col_a, col_b = st.columns(2)

    with col_a:
        # Matriz de confusión como heatmap
        labels_map = {0: "Bajo (≤$500)", 1: "Alto (>$500)"}
        conf_dt["label_str"]      = conf_dt["label"].map(labels_map)
        conf_dt["prediction_str"] = conf_dt["prediction"].map(labels_map)
        pivot = conf_dt.pivot(index="label_str", columns="prediction_str", values="count").fillna(0)
        fig = px.imshow(pivot, text_auto=True, color_continuous_scale=[[0, DARK], [1, GOLD]],
                        title="Matriz de Confusión — Árbol de Decisión",
                        labels=dict(x="Predicción", y="Real", color="Cantidad"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Importancia de variables
        feat_names = ["duracion_min", "precio", "ingreso"]
        fig2 = px.bar(x=feat_names, y=feat_imp_dt,
                      title="Importancia de Variables — Árbol de Decisión",
                      color=feat_imp_dt, color_continuous_scale=[[0, "#333"], [1, GOLD]],
                      labels={"x": "Variable", "y": "Importancia", "color": "Importancia"})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Métricas en radar
    col_c, col_d = st.columns(2)
    with col_c:
        categorias = ["Accuracy", "Precision", "Recall", "F1", "AUC"]
        valores    = [metricas_dt[k] for k in categorias]
        fig3 = go.Figure(go.Scatterpolar(
            r=valores, theta=categorias, fill="toself",
            line_color=GOLD, fillcolor=f"rgba(212,175,55,0.2)"
        ))
        fig3.update_layout(title="Métricas del Modelo (Radar)",
                           polar=dict(radialaxis=dict(visible=True, range=[0, 1], color="white"),
                                      angularaxis=dict(color="white")),
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("### Interpretación")
        acc = metricas_dt["Accuracy"]
        auc = metricas_dt["AUC"]
        st.info(f"""
**Árbol de Decisión — Análisis Supervisado**

- **Accuracy {acc*100:.1f}%**: el modelo clasifica correctamente {acc*100:.1f}% de las citas
- **AUC {auc:.4f}**: capacidad discriminativa {'excelente' if auc > 0.9 else 'buena' if auc > 0.75 else 'moderada'}
- **Feature más importante**: `{feat_names[feat_imp_dt.index(max(feat_imp_dt))]}`
  ({max(feat_imp_dt)*100:.1f}% del poder predictivo)
- **Umbral**: citas con ingreso > $500 MXN se clasifican como ALTO VALOR
- **Aplicación**: identificar servicios premium para estrategias de fidelización
        """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — RANDOM FOREST
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Unidad III — Random Forest")
    st.caption("Clasificación: predicción de citas canceladas o no asistidas (label=1)")

    with st.spinner("Entrenando Random Forest (100 árboles)…"):
        metricas_rf, conf_rf, feat_imp_rf, dist_estados = entrenar_rf(spark, df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Accuracy",  f"{metricas_rf['Accuracy']*100:.1f}%")
    c2.metric("Precision", f"{metricas_rf['Precision']:.4f}")
    c3.metric("Recall",    f"{metricas_rf['Recall']:.4f}")
    c4.metric("F1-Score",  f"{metricas_rf['F1']:.4f}")
    c5.metric("AUC-ROC",   f"{metricas_rf['AUC']:.4f}")

    col_a, col_b = st.columns(2)

    with col_a:
        labels_rf = {0: "Normal", 1: "Cancelada/No asistió"}
        conf_rf["cat_str"]  = conf_rf["categoria"].map(labels_rf)
        conf_rf["pred_str"] = conf_rf["prediction"].map(labels_rf)
        pivot_rf = conf_rf.pivot(index="cat_str", columns="pred_str", values="count").fillna(0)
        fig = px.imshow(pivot_rf, text_auto=True, color_continuous_scale=[[0, DARK], [1, RED]],
                        title="Matriz de Confusión — Random Forest",
                        labels=dict(x="Predicción", y="Real", color="Cantidad"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        feat_names = ["duracion_min", "precio", "ingreso"]
        fig2 = px.bar(x=feat_names, y=feat_imp_rf,
                      title="Importancia de Variables — Random Forest",
                      color=feat_imp_rf, color_continuous_scale=[[0, "#333"], [1, RED]],
                      labels={"x": "Variable", "y": "Importancia"}, text_auto=".3f")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        fig3 = px.pie(dist_estados, values="count", names="estado",
                      title="Distribución Real de Estados en Datos de Entrenamiento",
                      hole=0.35, color_discrete_sequence=px.colors.qualitative.Set2)
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        categorias = ["Accuracy", "Precision", "Recall", "F1", "AUC"]
        valores    = [metricas_rf[k] for k in categorias]
        fig4 = go.Figure(go.Scatterpolar(
            r=valores, theta=categorias, fill="toself",
            line_color=RED, fillcolor="rgba(231,76,60,0.2)"
        ))
        fig4.update_layout(title="Métricas Random Forest (Radar)",
                           polar=dict(radialaxis=dict(visible=True, range=[0, 1], color="white"),
                                      angularaxis=dict(color="white")),
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — KMEANS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("Unidad IV — KMeans Clustering")
    st.caption("Segmentación no supervisada de citas por duración, precio e ingreso")

    with st.spinner(f"Ejecutando KMeans K={k_clusters} y Método del Codo…"):
        ks, wcss, sil_scores, km_pdf, sil, centers = entrenar_kmeans(df_vector, k_clusters)

    c1, c2, c3 = st.columns(3)
    c1.metric("Clusters (K)",        k_clusters)
    c2.metric("Silhouette Score",    sil, delta="Bueno" if sil > 0.5 else "Aceptable" if sil > 0.2 else "Débil")
    c3.metric("Total Registros",     f"{len(km_pdf):,}")

    col_a, col_b = st.columns(2)

    with col_a:
        fig = make_subplots(rows=1, cols=2, subplot_titles=("WCSS — Método del Codo", "Silhouette por K"))
        fig.add_trace(go.Scatter(x=ks, y=wcss, mode="lines+markers",
                                 line=dict(color=GOLD, width=2), marker=dict(size=8)), row=1, col=1)
        fig.add_trace(go.Scatter(x=ks, y=sil_scores, mode="lines+markers",
                                 line=dict(color=GREEN, width=2), marker=dict(size=8)), row=1, col=2)
        fig.add_vline(x=k_clusters, line_dash="dash", line_color=RED)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", showlegend=False, title_text="Evaluación de K")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.scatter(km_pdf, x="precio", y="ingreso",
                          color=km_pdf["cluster"].astype(str),
                          title=f"Segmentación K={k_clusters} — Precio vs Ingreso",
                          hover_data=["servicio", "barbero", "duracion_min", "estado"],
                          color_discrete_sequence=px.colors.qualitative.Set1,
                          labels={"color": "Cluster", "precio": "Precio ($MXN)", "ingreso": "Ingreso ($MXN)"})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        fig3 = px.scatter_3d(km_pdf, x="precio", y="duracion_min", z="ingreso",
                             color=km_pdf["cluster"].astype(str),
                             title="Clustering 3D — Precio / Duración / Ingreso",
                             hover_name="servicio",
                             color_discrete_sequence=px.colors.qualitative.Set1,
                             labels={"color": "Cluster", "duracion_min": "Duración (min)"})
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        svc_cluster = km_pdf.groupby(["cluster", "servicio"]).size().reset_index(name="count")
        fig4 = px.bar(svc_cluster, x="cluster", y="count", color="servicio",
                      title="Servicios por Cluster",
                      labels={"cluster": "Cluster", "count": "Citas", "servicio": "Servicio"},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Centroides de Clusters")
    centro_df = pd.DataFrame(centers, columns=["Duración (min)", "Precio ($)", "Ingreso ($)"])
    centro_df.index = [f"Cluster {i}" for i in range(len(centers))]
    st.dataframe(centro_df.style.format("{:.2f}"), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — PCA
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("Unidad IV — PCA + KMeans")
    st.caption("Reducción de dimensionalidad: 3 features → 2 componentes principales → clustering")

    with st.spinner("Ejecutando PCA + KMeans…"):
        pca_pdf, varianza, pca_sil = entrenar_pca(df_vector, df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Varianza PC1",        f"{varianza[0]:.1f}%")
    c2.metric("Varianza PC2",        f"{varianza[1]:.1f}%")
    c3.metric("Varianza Total",      f"{sum(varianza):.1f}%")
    c4.metric("Silhouette (PCA+KM)", pca_sil)

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.scatter(pca_pdf, x="PC1", y="PC2",
                         color=pca_pdf["cluster"].astype(str),
                         hover_data=["servicio", "barbero", "precio", "duracion_min", "ingreso"],
                         title=f"PCA + KMeans — Varianza explicada: {sum(varianza):.1f}%  |  Silhouette: {pca_sil}",
                         color_discrete_sequence=px.colors.qualitative.Set1,
                         labels={"color": "Cluster",
                                 "PC1": f"PC1 ({varianza[0]:.1f}% varianza)",
                                 "PC2": f"PC2 ({varianza[1]:.1f}% varianza)"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Varianza explicada
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=["PC1", "PC2"], y=varianza,
                              marker_color=[GOLD, BLUE], text=[f"{v:.1f}%" for v in varianza],
                              textposition="outside", textfont_color="white"))
        fig2.add_trace(go.Scatter(x=["PC1", "PC2"], y=[sum(varianza[:1]), sum(varianza)],
                                  mode="lines+markers+text", name="Varianza acumulada",
                                  line_color=GREEN, text=[f"{sum(varianza[:1]):.1f}%", f"{sum(varianza):.1f}%"],
                                  textposition="top right", textfont_color="white"))
        fig2.update_layout(title="Varianza Explicada por Componente Principal",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", yaxis_title="%", showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        svc_pca = pca_pdf.groupby(["cluster", "servicio"]).size().reset_index(name="count")
        fig3 = px.sunburst(svc_pca, path=["cluster", "servicio"], values="count",
                           title="Composición de Clusters por Servicio (Sunburst)",
                           color_discrete_sequence=px.colors.qualitative.Set1)
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        perfil = pca_pdf.groupby("cluster").agg(
            avg_precio=("precio", "mean"),
            avg_ingreso=("ingreso", "mean"),
            avg_duracion=("duracion_min", "mean"),
            total_citas=("precio", "count"),
        ).reset_index()
        fig4 = px.bar(perfil, x="cluster", y=["avg_precio", "avg_ingreso", "avg_duracion"],
                      barmode="group", title="Perfil de Clusters PCA (promedios)",
                      labels={"value": "Valor", "cluster": "Cluster", "variable": "Métrica"},
                      color_discrete_sequence=[GOLD, GREEN, BLUE])
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Interpretación de Clusters PCA")
    avg = pca_pdf.groupby("cluster")[["precio", "ingreso", "duracion_min"]].mean()
    for cl in sorted(pca_pdf["cluster"].unique()):
        row    = avg.loc[cl]
        global_avg = pca_pdf[["precio", "ingreso", "duracion_min"]].mean()
        perfil_txt = "Premium" if row["ingreso"] > global_avg["ingreso"] and row["precio"] > global_avg["precio"] \
                     else "Económico" if row["ingreso"] < global_avg["ingreso"] \
                     else "Estándar"
        st.info(f"**Cluster {cl} — {perfil_txt}**: "
                f"Precio ${row['precio']:.0f} | Ingreso ${row['ingreso']:.0f} | "
                f"Duración {row['duracion_min']:.0f} min")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f"<p style='text-align:center;color:#555;font-size:11px;'>"
    f"UrbanBlade Analytics · UTVT IDGS-84 · Extracción del conocimiento en bases de datos · "
    f"MGTI. Héctor Velázquez Estrada · KikeGonRam</p>",
    unsafe_allow_html=True
)
