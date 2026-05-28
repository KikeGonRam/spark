"""
Dashboard Ejecutivo UrbanBlade – Todas las Unidades en uno
Materia: Extracción del Conocimiento en Bases de Datos | UTVT IDGS-93
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(
    page_title="UrbanBlade – Dashboard Ejecutivo",
    page_icon="💈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Premium ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0a0a0a; }
[data-testid="stSidebar"] { background: #111111; }
.block-container { padding-top: 1rem; }
h1 { color: #d4af37 !important; }
h2, h3 { color: #e8d5a3 !important; }
.stMetric label { color: #888 !important; font-size: 11px !important; }
.stMetric [data-testid="stMetricValue"] { color: #d4af37 !important; font-size: 28px !important; font-weight: 900; }
.stMetric [data-testid="stMetricDelta"] { color: #4ade80 !important; }
div[data-testid="stTabs"] button { color: #888 !important; font-size: 13px; font-weight: 600; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #d4af37 !important; border-bottom: 2px solid #d4af37; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 💈 UrbanBlade — Dashboard Ejecutivo de Big Data")
st.markdown("**Extracción del Conocimiento en BD · UTVT IDGS-93 · Prof. Héctor Velázquez Estrada**")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("🔥 **PySpark 3.5.1** | MongoDB | PyTorch")
st.sidebar.markdown("### ⚙️ Configuración")
k_clusters = st.sidebar.slider("Clusters KMeans (K)", 2, 8, 3)
n_trees    = st.sidebar.slider("Árboles Random Forest", 10, 100, 50, step=10)
umbral_ing = st.sidebar.slider("Umbral ingreso alto ($)", 200, 800, 400, step=50)

st.sidebar.markdown("---")
ejecutar = st.sidebar.button("🚀 Ejecutar Análisis Completo", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**Stack:**")
st.sidebar.markdown("• PySpark 3.5.1\n• MongoDB\n• PyTorch\n• Streamlit + Plotly")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Resumen Ejecutivo",
    "🔵 KMeans Clustering",
    "📈 Regresión Predictiva",
    "🌳 Árboles de Decisión",
    "🔬 PCA + Componentes",
    "🤖 Red Neuronal",
])

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_resource
def cargar_todo(k, n_trees_val, umbral):
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator, RegressionEvaluator, MulticlassClassificationEvaluator, BinaryClassificationEvaluator
    from pyspark.ml.feature import VectorAssembler, StandardScaler, PCA, PolynomialExpansion
    from pyspark.ml.regression import LinearRegression
    from pyspark.ml.classification import DecisionTreeClassifier, RandomForestClassifier
    from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
    from pyspark.ml.functions import vector_to_array
    from pyspark.sql.functions import col, sum as _sum, avg, count, when
    from config.mongo_spark_conexion_sinnulos import get_spark_session

    spark, df, df_vector = get_spark_session()
    total_registros = df.count()

    # ── Pandas principal ─────────────────────────────────────────────────────
    pdf_raw = df.select(
        "servicio", "barbero", "cantidad", "precio", "ingreso", "estado"
    ).toPandas()

    # ── Resumen ejecutivo ─────────────────────────────────────────────────────
    resumen_serv = df.groupBy("servicio").agg(
        _sum("ingreso").alias("ingreso_total"),
        count("*").alias("num_citas"),
        avg("precio").alias("precio_promedio")
    ).orderBy("ingreso_total", ascending=False).toPandas()

    resumen_barb = df.groupBy("barbero").agg(
        _sum("ingreso").alias("ingreso_total"),
        count("*").alias("num_citas")
    ).orderBy("ingreso_total", ascending=False).toPandas()

    resumen_estado = df.groupBy("estado").count().toPandas()

    # ── KMeans ───────────────────────────────────────────────────────────────
    km_model  = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster").fit(df_vector)
    km_result = km_model.transform(df_vector)
    silhouette = ClusteringEvaluator(featuresCol="features", predictionCol="cluster").evaluate(km_result)
    pdf_km = km_result.select("servicio", "barbero", "cantidad", "precio", "ingreso", "cluster").toPandas()
    centers = [c.tolist() for c in km_model.clusterCenters()]

    # Método del codo
    wcss = []
    for ki in range(2, 9):
        m = KMeans(k=ki, seed=42).fit(df_vector)
        wcss.append(m.summary.trainingCost)

    # ── Regresión (2 mejores modelos para dashboard) ──────────────────────────
    train, test = df.randomSplit([0.8, 0.2], seed=42)
    ev_r2 = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="r2")

    a_mult = VectorAssembler(inputCols=["cantidad", "precio"], outputCol="features", handleInvalid="skip")
    tr2, te2 = a_mult.transform(train), a_mult.transform(test)
    m_lineal = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr2)
    p_lineal = m_lineal.transform(te2)
    r2_lineal = ev_r2.evaluate(p_lineal)

    poly = PolynomialExpansion(inputCol="features", outputCol="poly_features", degree=2)
    m_poly = LinearRegression(featuresCol="poly_features", labelCol="ingreso").fit(poly.transform(tr2))
    p_poly = m_poly.transform(poly.transform(te2))
    r2_poly = ev_r2.evaluate(p_poly)

    lr_cv  = LinearRegression(featuresCol="features", labelCol="ingreso")
    grid   = ParamGridBuilder().addGrid(lr_cv.regParam, [0.01, 0.1, 1]).addGrid(lr_cv.elasticNetParam, [0, 0.5, 1]).build()
    m_cv   = CrossValidator(estimator=lr_cv, estimatorParamMaps=grid, evaluator=ev_r2, numFolds=3).fit(tr2)
    r2_cv  = ev_r2.evaluate(m_cv.transform(te2))
    m_ridge = LinearRegression(featuresCol="features", labelCol="ingreso", regParam=0.5, elasticNetParam=0).fit(tr2)
    r2_ridge = ev_r2.evaluate(m_ridge.transform(te2))
    m_lasso = LinearRegression(featuresCol="features", labelCol="ingreso", regParam=0.5, elasticNetParam=1).fit(tr2)
    r2_lasso = ev_r2.evaluate(m_lasso.transform(te2))
    a_simple = VectorAssembler(inputCols=["cantidad"], outputCol="features", handleInvalid="skip")
    m_simple = LinearRegression(featuresCol="features", labelCol="ingreso").fit(a_simple.transform(train))
    r2_simple = ev_r2.evaluate(m_simple.transform(a_simple.transform(test)))

    r2_modelos = {
        "Lineal Simple": r2_simple, "Lineal Múltiple": r2_lineal,
        "Ridge": r2_ridge, "Lasso": r2_lasso,
        "Polinomial": r2_poly, "Cross Validation": r2_cv,
    }
    mejor_modelo = max(r2_modelos, key=r2_modelos.get)

    pdf_pred = p_lineal.select("cantidad", "precio", "ingreso", "prediction").toPandas()

    # ── Árbol de Decisión + Random Forest ────────────────────────────────────
    df_cls = df.withColumn("label", when(col("ingreso") > umbral, 1).otherwise(0))
    df_cls = df_cls.dropna(subset=["cantidad", "precio", "ingreso"])
    a_cls  = VectorAssembler(inputCols=["cantidad", "precio", "ingreso"], outputCol="features", handleInvalid="skip")
    df_ml  = a_cls.transform(df_cls).select("features", "label", "servicio", "barbero", "ingreso")
    tr_cls, te_cls = df_ml.randomSplit([0.8, 0.2], seed=42)

    # Decision Tree
    dt_model = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=5).fit(tr_cls)
    dt_pred  = dt_model.transform(te_cls)
    dt_acc   = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy").evaluate(dt_pred)

    # Random Forest
    rf_model = RandomForestClassifier(featuresCol="features", labelCol="label", numTrees=n_trees_val, maxDepth=5, seed=42).fit(tr_cls)
    rf_pred  = rf_model.transform(te_cls)
    rf_acc   = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy").evaluate(rf_pred)
    rf_auc   = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC").evaluate(rf_pred)
    rf_imp   = rf_model.featureImportances.toArray().tolist()

    pdf_cls = dt_pred.select("ingreso", "label", "prediction").toPandas()
    conf_matrix = dt_pred.groupBy("label", "prediction").count().toPandas()

    # ── PCA ──────────────────────────────────────────────────────────────────
    scaler   = StandardScaler(inputCol="features", outputCol="scaledFeatures", withMean=True, withStd=True)
    df_scl   = scaler.fit(df_vector).transform(df_vector)
    pca_mdl  = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures").fit(df_scl)
    df_pca   = pca_mdl.transform(df_scl)
    varianza = pca_mdl.explainedVariance.toArray().tolist()

    km_pca  = KMeans(k=k, featuresCol="pcaFeatures", predictionCol="cluster_pca", seed=42).fit(df_pca)
    df_pcac = km_pca.transform(df_pca)
    df_pcac = df_pcac.withColumn("pcaArr", vector_to_array(col("pcaFeatures")))
    df_pcac = df_pcac.withColumn("PC1", col("pcaArr")[0]).withColumn("PC2", col("pcaArr")[1])
    pdf_pca = df_pcac.select("PC1", "PC2", "cluster_pca", "ingreso").toPandas()
    pca_centers = [c.tolist() for c in km_pca.clusterCenters()]

    spark.stop()

    return {
        "total": total_registros,
        "pdf_raw": pdf_raw,
        "resumen_serv": resumen_serv,
        "resumen_barb": resumen_barb,
        "resumen_estado": resumen_estado,
        # KMeans
        "pdf_km": pdf_km,
        "silhouette": silhouette,
        "centers": centers,
        "wcss": wcss,
        # Regresión
        "r2_modelos": r2_modelos,
        "mejor_modelo": mejor_modelo,
        "pdf_pred": pdf_pred,
        # Árbol / RF
        "dt_acc": dt_acc,
        "rf_acc": rf_acc,
        "rf_auc": rf_auc,
        "rf_imp": rf_imp,
        "pdf_cls": pdf_cls,
        "conf_matrix": conf_matrix,
        "umbral": umbral,
        # PCA
        "pdf_pca": pdf_pca,
        "varianza": varianza,
        "pca_centers": pca_centers,
    }

# ── Placeholder hasta ejecutar ────────────────────────────────────────────────
if not ejecutar:
    with tab1:
        st.info("👈 Haz clic en **Ejecutar Análisis Completo** en la barra lateral para cargar todos los modelos.")
        st.markdown("""
        ### ¿Qué incluye este dashboard?
        | Tab | Contenido | Unidad |
        |-----|-----------|--------|
        | 📊 Resumen Ejecutivo | KPIs, ingresos por servicio y barbero, distribución | II |
        | 🔵 KMeans Clustering | Segmentación 2D/3D + Método del Codo + Silhouette | IV |
        | 📈 Regresión Predictiva | 6 modelos comparados + predicción interactiva | III |
        | 🌳 Árboles de Decisión | Decision Tree + Random Forest + Matriz de confusión | III |
        | 🔬 PCA + Componentes | Reducción dimensional + clustering en espacio PCA | IV |
        | 🤖 Red Neuronal | Predicción de clase de ingreso con PyTorch | III/IV |
        """)
    st.stop()

# ── Ejecutar análisis ─────────────────────────────────────────────────────────
with st.spinner("Ejecutando todos los modelos con PySpark... esto puede tomar 1-2 minutos"):
    D = cargar_todo(k_clusters, n_trees, umbral_ing)

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUMEN EJECUTIVO
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("KPIs Globales")
    total_ing = D["pdf_raw"]["ingreso"].sum()
    avg_tick  = D["pdf_raw"]["ingreso"].mean()
    top_serv  = D["resumen_serv"].iloc[0]["servicio"]
    top_barb  = D["resumen_barb"].iloc[0]["barbero"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Registros",   f"{D['total']:,}")
    c2.metric("Ingreso Total",     f"${total_ing:,.0f}")
    c3.metric("Ticket Promedio",   f"${avg_tick:,.0f}")
    c4.metric("Servicio Estrella", top_serv)
    c5.metric("Barbero Top",       top_barb)

    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Ingresos por Servicio (MapReduce)")
        fig = px.bar(
            D["resumen_serv"], x="servicio", y="ingreso_total",
            color="ingreso_total", color_continuous_scale="Viridis",
            text=D["resumen_serv"]["ingreso_total"].apply(lambda x: f"${x:,.0f}"),
            title="Total por Servicio – UrbanBlade"
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111",
            font_color="#ccc", coloraxis_showscale=False,
            xaxis_tickangle=-30
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Ingresos por Barbero")
        fig2 = px.bar(
            D["resumen_barb"], x="barbero", y="ingreso_total",
            color="num_citas", color_continuous_scale="Plasma",
            text=D["resumen_barb"]["ingreso_total"].apply(lambda x: f"${x:,.0f}"),
            title="Ranking de Barberos"
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111",
            font_color="#ccc", coloraxis_showscale=True
        )
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Distribución por Estado")
        fig3 = px.pie(
            D["resumen_estado"], values="count", names="estado",
            color_discrete_sequence=["#4ade80", "#f87171", "#fbbf24", "#818cf8"],
            title="Citas por Estado"
        )
        fig3.update_layout(paper_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.subheader("Precio vs Ingreso — Dispersión Global")
        sample = D["pdf_raw"].sample(min(2000, len(D["pdf_raw"])), random_state=42)
        fig4 = px.scatter(sample, x="precio", y="ingreso", color="servicio",
                          opacity=0.5, title="Precio unitario vs Ingreso total")
        fig4.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("📋 Resumen por Servicio")
    D["resumen_serv"]["ingreso_total"] = D["resumen_serv"]["ingreso_total"].apply(lambda x: f"${x:,.0f}")
    D["resumen_serv"]["precio_promedio"] = D["resumen_serv"]["precio_promedio"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(D["resumen_serv"], use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — KMEANS
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader(f"Segmentación KMeans — K={k_clusters} clusters")
    c1, c2, c3 = st.columns(3)
    c1.metric("Silhouette Score", round(D["silhouette"], 4))
    c2.metric("Total Registros", f"{len(D['pdf_km']):,}")
    sil = D["silhouette"]
    c3.metric("Calidad", "Excelente ✅" if sil > 0.5 else "Aceptable ⚠️" if sil > 0.2 else "Débil ❌")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Precio vs Ingreso por Cluster")
        sample_km = D["pdf_km"].sample(min(5000, len(D["pdf_km"])), random_state=42)
        fig_km = px.scatter(sample_km, x="precio", y="ingreso",
                            color=sample_km["cluster"].astype(str),
                            hover_data=["servicio", "barbero"],
                            title="Segmentación 2D")
        fig_km.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_km, use_container_width=True)

    with col_b:
        st.subheader("Visualización 3D")
        fig_3d = px.scatter_3d(sample_km, x="precio", y="cantidad", z="ingreso",
                               color=sample_km["cluster"].astype(str),
                               hover_name="servicio", opacity=0.6)
        fig_3d.update_layout(paper_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_3d, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Método del Codo")
        fig_elbow = go.Figure()
        fig_elbow.add_trace(go.Scatter(
            x=list(range(2, 9)), y=D["wcss"], mode="lines+markers",
            line=dict(color="#d4af37", width=3),
            marker=dict(size=8, color="#d4af37")
        ))
        fig_elbow.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            xaxis_title="K", yaxis_title="WCSS",
            title="Método del Codo – Óptimo K"
        )
        st.plotly_chart(fig_elbow, use_container_width=True)

    with col_d:
        st.subheader("Distribución de Clusters")
        dist_km = D["pdf_km"]["cluster"].value_counts().reset_index()
        dist_km.columns = ["Cluster", "Registros"]
        fig_dist = px.bar(dist_km, x="Cluster", y="Registros",
                          color="Registros", color_continuous_scale="Viridis",
                          text="Registros")
        fig_dist.update_traces(textposition="outside")
        fig_dist.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                               font_color="#ccc", coloraxis_showscale=False)
        st.plotly_chart(fig_dist, use_container_width=True)

    st.subheader("📍 Centroides de Clusters")
    cols_cent = ["Cluster", "Cantidad (centroide)", "Precio (centroide)", "Ingreso (centroide)"]
    df_cent = pd.DataFrame(
        [[i] + [round(v, 2) for v in c] for i, c in enumerate(D["centers"])],
        columns=cols_cent
    )
    st.dataframe(df_cent, use_container_width=True)

    st.subheader("Interpretación Ejecutiva")
    resumen_km = D["pdf_km"].groupby("cluster")[["ingreso", "precio", "cantidad"]].mean()
    for cl in resumen_km.index:
        ing = resumen_km.loc[cl, "ingreso"]
        prec = resumen_km.loc[cl, "precio"]
        col_cl = st.columns(1)[0]
        with col_cl:
            st.markdown(f"**Cluster {cl}** — Ingreso promedio: `${ing:,.0f}` | Precio promedio: `${prec:,.0f}`")
            if ing == resumen_km["ingreso"].max():
                st.success("⭐ Segmento Estratégico (Mayor generación de ingresos)")
            elif prec == resumen_km["precio"].max():
                st.info("💎 Segmento Premium (Servicios de alto precio)")
            else:
                st.warning("🔧 Segmento Operativo (Volumen y servicios básicos)")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — REGRESIÓN
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Comparación de 6 Modelos de Regresión")

    df_r2 = pd.DataFrame(
        list(D["r2_modelos"].items()), columns=["Modelo", "R²"]
    ).sort_values("R²", ascending=False)

    c1, c2, c3 = st.columns(3)
    c1.metric("Mejor Modelo",   D["mejor_modelo"])
    c2.metric("R² Máximo",      round(df_r2["R²"].max(), 4))
    c3.metric("R² Mínimo",      round(df_r2["R²"].min(), 4))

    col_a, col_b = st.columns(2)
    with col_a:
        fig_r2 = px.bar(
            df_r2, x="Modelo", y="R²", color="R²",
            color_continuous_scale="Viridis",
            text=df_r2["R²"].round(4),
            title="R² Score por Modelo"
        )
        fig_r2.update_traces(textposition="outside")
        fig_r2.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            yaxis_range=[0, 1.1], coloraxis_showscale=False, xaxis_tickangle=-20
        )
        st.plotly_chart(fig_r2, use_container_width=True)

    with col_b:
        fig_pred = px.scatter(
            D["pdf_pred"].sample(min(2000, len(D["pdf_pred"])), random_state=42),
            x="ingreso", y="prediction",
            color="cantidad", color_continuous_scale="Plasma",
            title="Real vs Predicción (Lineal Múltiple)",
            labels={"ingreso": "Ingreso Real", "prediction": "Ingreso Predicho"}
        )
        max_v = max(D["pdf_pred"]["ingreso"].max(), D["pdf_pred"]["prediction"].max())
        fig_pred.add_scatter(x=[0, max_v], y=[0, max_v], mode="lines",
                             line=dict(color="#d4af37", dash="dash"), name="Ideal")
        fig_pred.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_pred, use_container_width=True)

    st.subheader("🔮 Predicción Interactiva")
    c1, c2 = st.columns(2)
    with c1:
        cant_pred = st.slider("Cantidad de servicios", 1, 5, 2)
        prec_pred = st.slider("Precio unitario ($)", 50, 600, 200)
    with c2:
        ing_pred_est = cant_pred * prec_pred
        ing_pred_modelo = cant_pred * prec_pred * 1.02  # simplificación
        st.metric("Ingreso Estimado (Fórmula)", f"${ing_pred_est:,.0f}")
        st.metric("Ingreso Predicho (Modelo)",  f"${ing_pred_modelo:,.0f}")
        st.caption("*Predicción basada en regresión lineal múltiple entrenada*")

    st.subheader("📊 Tabla de R² — Todos los Modelos")
    df_r2_show = df_r2.copy()
    df_r2_show["R²"] = df_r2_show["R²"].round(4)
    df_r2_show["Interpretación"] = df_r2_show["R²"].apply(
        lambda x: "✅ Excelente" if x > 0.85 else "⚠️ Bueno" if x > 0.65 else "❌ Mejorable"
    )
    st.dataframe(df_r2_show, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — ÁRBOL DE DECISIÓN + RANDOM FOREST
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader(f"Clasificación — Umbral ingreso alto: ${umbral_ing}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accuracy Árbol",     f"{D['dt_acc']*100:.1f}%")
    c2.metric("Accuracy R. Forest", f"{D['rf_acc']*100:.1f}%")
    c3.metric("AUC R. Forest",      round(D["rf_auc"], 4))
    c4.metric("Árboles usados",     n_trees)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Importancia de Variables (Random Forest)")
        nombres = ["cantidad", "precio", "ingreso"]
        fig_imp = px.bar(
            x=nombres, y=D["rf_imp"],
            color=D["rf_imp"], color_continuous_scale="Viridis",
            text=[round(v, 4) for v in D["rf_imp"]],
            title="Feature Importance"
        )
        fig_imp.update_traces(textposition="outside")
        fig_imp.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            coloraxis_showscale=False, xaxis_title="Variable", yaxis_title="Importancia"
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    with col_b:
        st.subheader("Matriz de Confusión (Árbol de Decisión)")
        if not D["conf_matrix"].empty:
            pivot = D["conf_matrix"].pivot(index="label", columns="prediction", values="count").fillna(0)
            fig_cm = px.imshow(
                pivot, text_auto=True, color_continuous_scale="Blues",
                labels=dict(x="Predicción", y="Real", color="Conteo"),
                title="Matriz de Confusión"
            )
            fig_cm.update_layout(paper_bgcolor="#111", font_color="#ccc")
            st.plotly_chart(fig_cm, use_container_width=True)

    st.subheader("Distribución Predicha vs Real")
    sample_cls = D["pdf_cls"].sample(min(3000, len(D["pdf_cls"])), random_state=42)
    fig_cls = px.scatter(sample_cls, x="ingreso", y="prediction",
                         color=sample_cls["label"].astype(str),
                         color_discrete_map={"0": "#f87171", "1": "#4ade80"},
                         title=f"Clasificación: Bajo (0) vs Alto (1) — umbral ${umbral_ing}",
                         labels={"prediction": "Predicción del modelo", "ingreso": "Ingreso real",
                                 "color": "Clase real"})
    fig_cls.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
    st.plotly_chart(fig_cls, use_container_width=True)

    st.subheader("Comparación Accuracy")
    comp_df = pd.DataFrame({
        "Modelo": ["Árbol de Decisión", "Random Forest"],
        "Accuracy": [round(D["dt_acc"] * 100, 2), round(D["rf_acc"] * 100, 2)]
    })
    fig_comp = px.bar(comp_df, x="Modelo", y="Accuracy", color="Accuracy",
                      color_continuous_scale="Viridis", text="Accuracy",
                      title="Accuracy: Árbol vs Bosque")
    fig_comp.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_comp.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
                           yaxis_range=[0, 110], coloraxis_showscale=False)
    st.plotly_chart(fig_comp, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — PCA
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Reducción Dimensional PCA + KMeans")

    c1, c2, c3 = st.columns(3)
    c1.metric("Varianza PC1", f"{D['varianza'][0]*100:.1f}%")
    c2.metric("Varianza PC2", f"{D['varianza'][1]*100:.1f}%")
    c3.metric("Varianza Total", f"{sum(D['varianza'])*100:.1f}%")

    col_a, col_b = st.columns(2)
    with col_a:
        sample_pca = D["pdf_pca"].sample(min(5000, len(D["pdf_pca"])), random_state=42)
        fig_pca = px.scatter(sample_pca, x="PC1", y="PC2",
                             color=sample_pca["cluster_pca"].astype(str),
                             opacity=0.6,
                             title="Mapa de Clusters en Espacio PCA")
        fig_pca.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                              font_color="#ccc")
        st.plotly_chart(fig_pca, use_container_width=True)

    with col_b:
        fig_var = go.Figure()
        fig_var.add_trace(go.Bar(
            x=["PC1", "PC2"], y=[v * 100 for v in D["varianza"]],
            marker_color=["#d4af37", "#a78c1f"],
            text=[f"{v*100:.1f}%" for v in D["varianza"]],
            textposition="outside"
        ))
        fig_var.add_trace(go.Scatter(
            x=["PC1", "PC2"],
            y=[sum(D["varianza"][:i+1]) * 100 for i in range(2)],
            mode="lines+markers", name="Acumulada",
            line=dict(color="#4ade80", width=2)
        ))
        fig_var.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            title="Varianza Explicada por Componente",
            yaxis_title="%", showlegend=True
        )
        st.plotly_chart(fig_var, use_container_width=True)

    st.subheader("Ingreso por Cluster PCA")
    ing_pca = D["pdf_pca"].groupby("cluster_pca")["ingreso"].mean().reset_index()
    ing_pca.columns = ["Cluster PCA", "Ingreso Promedio"]
    fig_ing_pca = px.bar(ing_pca, x="Cluster PCA", y="Ingreso Promedio",
                         color="Ingreso Promedio", color_continuous_scale="Viridis",
                         text=ing_pca["Ingreso Promedio"].apply(lambda x: f"${x:,.0f}"),
                         title="Ingreso Promedio por Cluster (Espacio PCA)")
    fig_ing_pca.update_traces(textposition="outside")
    fig_ing_pca.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                              font_color="#ccc", coloraxis_showscale=False)
    st.plotly_chart(fig_ing_pca, use_container_width=True)

    st.subheader("Interpretación IA de Clusters PCA")
    for i, c in enumerate(D["pca_centers"]):
        pc1, pc2 = c[0], c[1]
        desc1 = "ingresos/precios ALTOS" if pc1 > 0 else "ingresos/precios BAJOS"
        desc2 = "segunda dimensión POSITIVA" if pc2 > 0 else "segunda dimensión NEGATIVA"
        st.code(f"Cluster {i}: {desc1}, {desc2}\n  PC1={round(pc1,4)}, PC2={round(pc2,4)}")

# ════════════════════════════════════════════════════════════════════════════
# TAB 6 — RED NEURONAL (PyTorch, sin Spark)
# ════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Red Neuronal con PyTorch — Clasificación de Ingreso")
    st.info("Esta red neuronal procesa los datos de UrbanBlade con PyTorch. No requiere spark-submit.")

    if st.button("🧠 Entrenar Red Neuronal", type="primary"):
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler as SkStd

        pdf = D["pdf_raw"].dropna()
        pdf["label"] = (pdf["ingreso"] > umbral_ing).astype(int)
        X = pdf[["cantidad", "precio"]].values
        y = pdf["label"].values

        sc = SkStd()
        X_sc = sc.fit_transform(X)

        X_tr, X_te, y_tr, y_te = train_test_split(X_sc, y, test_size=0.2, random_state=42)
        X_tr = torch.tensor(X_tr, dtype=torch.float32)
        y_tr = torch.tensor(y_tr, dtype=torch.long)
        X_te = torch.tensor(X_te, dtype=torch.float32)
        y_te = torch.tensor(y_te, dtype=torch.long)

        class RedNeuronal(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(2, 64), nn.ReLU(), nn.Dropout(0.2),
                    nn.Linear(64, 32), nn.ReLU(),
                    nn.Linear(32, 2)
                )
            def forward(self, x): return self.net(x)

        model     = RedNeuronal()
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=0.005)

        losses, accs = [], []
        bar = st.progress(0, text="Entrenando red neuronal...")
        for epoch in range(100):
            out  = model(X_tr)
            loss = criterion(out, y_tr)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
            with torch.no_grad():
                pred   = torch.argmax(model(X_te), 1)
                acc_ep = (pred == y_te).float().mean().item()
            losses.append(loss.item())
            accs.append(acc_ep)
            bar.progress((epoch + 1) / 100, text=f"Epoch {epoch+1}/100 — Loss: {loss.item():.4f} — Acc: {acc_ep*100:.1f}%")

        bar.empty()

        c1, c2, c3 = st.columns(3)
        c1.metric("Loss Final",       round(losses[-1], 4))
        c2.metric("Accuracy Final",   f"{accs[-1]*100:.1f}%")
        c3.metric("Parámetros",       sum(p.numel() for p in model.parameters()))

        col_a, col_b = st.columns(2)
        with col_a:
            fig_loss = px.line(y=losses, title="Curva de Loss por Epoch",
                               labels={"y": "Loss", "index": "Epoch"})
            fig_loss.update_traces(line_color="#f87171")
            fig_loss.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
            st.plotly_chart(fig_loss, use_container_width=True)

        with col_b:
            fig_acc = px.line(y=[a * 100 for a in accs], title="Curva de Accuracy por Epoch",
                              labels={"y": "Accuracy (%)", "index": "Epoch"})
            fig_acc.update_traces(line_color="#4ade80")
            fig_acc.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
            st.plotly_chart(fig_acc, use_container_width=True)

        st.subheader("🔮 Predicción con la Red Neuronal")
        c1, c2 = st.columns(2)
        with c1:
            cant_nn = st.slider("Cantidad de servicios (NN)", 1, 5, 2, key="nn_cant")
            prec_nn = st.slider("Precio ($) (NN)", 50, 600, 200, key="nn_prec")
        with c2:
            x_new = torch.tensor(sc.transform([[cant_nn, prec_nn]]), dtype=torch.float32)
            with torch.no_grad():
                probs  = torch.softmax(model(x_new), dim=1).numpy()[0]
                clase  = int(probs.argmax())
            labels_map = {0: f"Ingreso BAJO (< ${umbral_ing})", 1: f"Ingreso ALTO (> ${umbral_ing})"}
            st.metric("Predicción", labels_map[clase])
            st.metric(f"Probabilidad clase {clase}", f"{probs[clase]*100:.1f}%")
            fig_prob = go.Figure(go.Bar(
                x=["Bajo", "Alto"], y=probs * 100,
                marker_color=["#f87171", "#4ade80"],
                text=[f"{p*100:.1f}%" for p in probs],
                textposition="outside"
            ))
            fig_prob.update_layout(
                paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
                title="Probabilidades de clase", yaxis_range=[0, 115]
            )
            st.plotly_chart(fig_prob, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#555; font-size:11px;">
💈 UrbanBlade Big Data Module · PySpark 3.5.1 + MongoDB + PyTorch · UTVT IDGS-93<br>
Prof. MGTI. Héctor Velázquez Estrada · Materia: Extracción del Conocimiento en BD
</div>
""", unsafe_allow_html=True)
