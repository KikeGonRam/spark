"""
Dashboard – Validación y Limpieza de Datos | UrbanBlade
Materia: Extracción del Conocimiento en BD · UTVT IDGS-93
Prof. MGTI. Héctor Velázquez Estrada
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(
    page_title="UrbanBlade – Limpieza de Datos",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Premium ───────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0a0a0a; }
[data-testid="stSidebar"]          { background: #111111; }
h1 { color: #d4af37 !important; }
h2, h3 { color: #e8d5a3 !important; }
.stMetric label { color: #888 !important; font-size: 11px !important; }
.stMetric [data-testid="stMetricValue"] { color: #d4af37 !important; font-size: 26px !important; font-weight: 900; }
div[data-testid="stTabs"] button { color: #888 !important; font-size: 13px; font-weight: 600; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #d4af37 !important; border-bottom: 2px solid #d4af37; }
code { background: #1a1a1a !important; color: #4ade80 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🧹 UrbanBlade — Validación y Limpieza de Datos")
st.markdown("**Extracción del Conocimiento en BD · UTVT IDGS-93 · Prof. Héctor Velázquez Estrada**")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.markdown("### ⚙️ Parámetros ETL")
iqr_factor     = st.sidebar.slider("Factor IQR (outliers)", 1.0, 3.0, 1.5, 0.1)
imput_strategy = st.sidebar.selectbox("Estrategia de Imputación", ["mean", "median"])
min_precio     = st.sidebar.number_input("Precio mínimo válido ($)", 0, 500, 0)
max_precio     = st.sidebar.number_input("Precio máximo válido ($)", 500, 10000, 5000)
ejecutar = st.sidebar.button("🚀 Ejecutar ETL Completo", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**Stack:** PySpark · MongoDB · MLlib · Streamlit")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Diagnóstico & KDD",
    "🧼 Limpieza Básica",
    "⚗️ Limpieza Avanzada",
    "🔄 Pipeline ETL",
    "📐 Métricas de Evaluación",
])

if not ejecutar:
    with tab1:
        st.info("👈 Configura los parámetros en la barra lateral y haz clic en **Ejecutar ETL Completo**.")
        st.markdown("""
        ### ¿Qué cubre este dashboard?
        | Tab | Tema | Contenido |
        |-----|------|-----------|
        | 📋 Diagnóstico & KDD | Minería de Datos | Diagrama KDD, análisis de calidad, schema |
        | 🧼 Limpieza Básica | Técnicas básicas | dropDuplicates, fillna, filter, cast, reclasificación |
        | ⚗️ Limpieza Avanzada | Técnicas avanzadas | Imputer, IQR, StandardScaler, MinMaxScaler, reglas negocio |
        | 🔄 Pipeline ETL | Tipos ETL | Extracción NoSQL, Transformación, Carga in-memory |
        | 📐 Métricas | Evaluación | R², RMSE, MAE, Accuracy, Silhouette, calidad ETL |
        """)
    st.stop()

# ── Carga y procesamiento ─────────────────────────────────────
@st.cache_resource
def ejecutar_etl(iqr_f, strat, min_p, max_p):
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, mean, stddev, count, when, isnull
    from pyspark.ml.feature import Imputer, StandardScaler, MinMaxScaler, VectorAssembler
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    from pyspark.ml.regression import LinearRegression
    from pyspark.ml.evaluation import RegressionEvaluator
    from config.mongo_spark_conexion_sinnulos import get_spark_session

    spark, df_base, _ = get_spark_session()

    # También leemos campos extendidos del mismo MongoDB
    mongo_uri = spark.sparkContext.getConf().get("spark.mongodb.read.connection.uri")
    database  = spark.sparkContext.getConf().get("spark.mongodb.read.database", "urbanblade")
    collection = spark.sparkContext.getConf().get("spark.mongodb.read.collection", "appointments")

    df_raw = spark.read.format("mongodb").load()
    total_raw = df_raw.count()

    # Columnas disponibles
    columnas = df_raw.columns

    # ── Diagnóstico de calidad ────────────────────────────────
    campos_revisar = [c for c in ["servicio","barbero","cantidad","precio","estado",
                                  "propina","rating","duracion_min","cliente_id"] if c in columnas]
    calidad_rows = []
    for campo in campos_revisar:
        nulos = df_raw.filter(col(campo).isNull()).count()
        pct   = (nulos / total_raw) * 100
        calidad_rows.append({"Campo": campo, "Nulos": nulos, "% Nulo": round(pct, 2)})
    df_calidad = pd.DataFrame(calidad_rows)

    # Tipos de datos
    schema_rows = [{"Campo": f.name, "Tipo": str(f.dataType)} for f in df_raw.schema.fields]
    df_schema   = pd.DataFrame(schema_rows)

    # ── Limpieza básica ───────────────────────────────────────
    antes_dedup  = total_raw
    df_t1 = df_raw.dropDuplicates()
    desp_dedup   = df_t1.count()

    df_t2 = df_t1.filter(
        col("servicio").isNotNull() &
        col("barbero").isNotNull()  &
        col("cantidad").isNotNull() &
        col("precio").isNotNull()
    )
    desp_filter = df_t2.count()

    df_t3 = df_t2.fillna({"estado": "desconocido", "propina": 0.0, "duracion_min": 30})

    df_t4 = df_t3 \
        .withColumn("cantidad",     col("cantidad").cast("double")) \
        .withColumn("precio",       col("precio").cast("double")) \
        .withColumn("propina",      col("propina").cast("double")) \
        .withColumn("duracion_min", col("duracion_min").cast("double") if "duracion_min" in columnas else col("cantidad"))

    basicas_pasos = pd.DataFrame([
        {"Técnica": "1. dropDuplicates()", "Antes": antes_dedup, "Después": desp_dedup,
         "Reducción": antes_dedup - desp_dedup,
         "Descripción": "Elimina registros exactamente iguales"},
        {"Técnica": "2. filter(isNotNull)", "Antes": desp_dedup, "Después": desp_filter,
         "Reducción": desp_dedup - desp_filter,
         "Descripción": "Filtra nulos en campos obligatorios"},
        {"Técnica": "3. fillna()", "Antes": desp_filter, "Después": desp_filter,
         "Reducción": 0,
         "Descripción": "Rellena nulos opcionales con valor por defecto"},
        {"Técnica": "4. cast(double)", "Antes": desp_filter, "Después": desp_filter,
         "Reducción": 0,
         "Descripción": "Convierte tipos de datos (string → double)"},
    ])

    # ── Limpieza avanzada ─────────────────────────────────────
    # Imputación
    campos_imp = [c for c in ["cantidad", "precio", "propina"] if c in df_t4.columns]
    imputer    = Imputer(inputCols=campos_imp,
                         outputCols=[f"{c}_imp" for c in campos_imp],
                         strategy=strat)
    df_imp = imputer.fit(df_t4).transform(df_t4)

    # IQR
    q1, q3 = df_imp.approxQuantile("precio", [0.25, 0.75], 0.01)
    iqr    = q3 - q1
    lower  = q1 - iqr_f * iqr
    upper  = q3 + iqr_f * iqr
    df_iqr = df_imp.filter((col("precio") >= lower) & (col("precio") <= upper))
    antes_iqr = df_imp.count()
    desp_iqr  = df_iqr.count()

    # Reglas de negocio
    df_biz = df_iqr.filter(
        (col("precio") >= min_p) & (col("precio") <= max_p) &
        (col("cantidad") > 0)    & (col("cantidad") <= 20)
    )
    desp_biz = df_biz.count()

    # StandardScaler y MinMaxScaler (sample pequeño para mostrar)
    asm  = VectorAssembler(inputCols=["cantidad_imp", "precio_imp"],
                           outputCol="features_raw", handleInvalid="skip")
    df_vec = asm.transform(df_biz)
    scaler = StandardScaler(inputCol="features_raw", outputCol="features_std",
                            withMean=True, withStd=True)
    norm   = MinMaxScaler(inputCol="features_raw", outputCol="features_norm")
    df_std  = scaler.fit(df_vec).transform(df_vec)
    df_norm = norm.fit(df_vec).transform(df_vec)

    avanzadas_pasos = pd.DataFrame([
        {"Técnica": "6. Imputer (media/mediana)", "Antes": desp_filter,
         "Después": desp_filter, "Reducción": 0,
         "Descripción": f"Imputa faltantes con {strat}"},
        {"Técnica": "7. IQR Outlier Removal", "Antes": antes_iqr,
         "Después": desp_iqr, "Reducción": antes_iqr - desp_iqr,
         "Descripción": f"Factor IQR={iqr_f}, rango [${lower:.0f}, ${upper:.0f}]"},
        {"Técnica": "8. Reglas de Negocio", "Antes": desp_iqr,
         "Después": desp_biz, "Reducción": desp_iqr - desp_biz,
         "Descripción": f"Precio [{min_p}, {max_p}], Cantidad [1, 20]"},
        {"Técnica": "9. StandardScaler (Z-score)", "Antes": desp_biz,
         "Después": desp_biz, "Reducción": 0,
         "Descripción": "μ=0, σ=1 → neutraliza escala"},
        {"Técnica": "10. MinMaxScaler [0,1]", "Antes": desp_biz,
         "Después": desp_biz, "Reducción": 0,
         "Descripción": "Normaliza al rango [0, 1]"},
    ])

    # ── Distribución precio antes/después ────────────────────
    pdf_precio_raw = df_t4.select("precio").dropna().limit(5000).toPandas()
    pdf_precio_lim = df_biz.select("precio").dropna().limit(5000).toPandas()

    # ── Dataset final ─────────────────────────────────────────
    df_final = df_biz.select(
        col("servicio"), col("barbero"), col("estado"),
        col("cantidad").cast("double"),
        col("precio").cast("double"),
        col("propina").cast("double") if "propina" in columnas else col("cantidad").alias("propina")
    ).dropna()

    total_final = df_final.count()

    # ── Estadísticas descriptivas ─────────────────────────────
    stats_rows = []
    for campo in ["cantidad", "precio", "propina"]:
        if campo in df_final.columns:
            r = df_final.select(
                mean(campo).alias("media"),
                stddev(campo).alias("std")
            ).collect()[0]
            mn = df_final.agg({campo: "min"}).collect()[0][0]
            mx = df_final.agg({campo: "max"}).collect()[0][0]
            stats_rows.append({
                "Campo": campo,
                "Media": round(r["media"], 2) if r["media"] else 0,
                "Std":   round(r["std"],   2) if r["std"] else 0,
                "Min":   round(mn, 2) if mn else 0,
                "Max":   round(mx, 2) if mx else 0,
            })
    df_stats = pd.DataFrame(stats_rows)

    # ── Métricas de evaluación de modelos ────────────────────
    from pyspark.ml.feature import VectorAssembler as VA
    df_ml = df_final.dropna()
    df_ml = df_ml.withColumn("ingreso", col("cantidad") * col("precio"))
    a = VA(inputCols=["cantidad", "precio", "ingreso"], outputCol="features", handleInvalid="skip")
    df_v = a.transform(df_ml)
    train, test = df_v.randomSplit([0.8, 0.2], seed=42)

    lr = LinearRegression(featuresCol="features", labelCol="ingreso")
    m  = lr.fit(train)
    p  = m.transform(test)

    ev_rmse = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="rmse")
    ev_mae  = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="mae")
    ev_r2   = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="r2")

    rmse = ev_rmse.evaluate(p)
    mae  = ev_mae.evaluate(p)
    r2   = ev_r2.evaluate(p)

    km    = KMeans(k=3, seed=42).fit(df_v)
    res   = km.transform(df_v)
    sil   = ClusteringEvaluator().evaluate(res)

    metricas = pd.DataFrame([
        {"Métrica": "R² (Coef. Determinación)", "Valor": round(r2, 4),
         "Rango": "[0, 1]", "Ideal": "→ 1.0",
         "Interpretación": "% varianza explicada por el modelo"},
        {"Métrica": "RMSE (Raíz Error Cuadrático)", "Valor": round(rmse, 2),
         "Rango": "[0, ∞]", "Ideal": "→ 0",
         "Interpretación": "Error promedio en unidades originales"},
        {"Métrica": "MAE (Error Absoluto Medio)", "Valor": round(mae, 2),
         "Rango": "[0, ∞]", "Ideal": "→ 0",
         "Interpretación": "Diferencia media predicho vs real"},
        {"Métrica": "Silhouette Score (KMeans)", "Valor": round(sil, 4),
         "Rango": "[-1, 1]", "Ideal": "→ 1.0",
         "Interpretación": "> 0.5 excelente | > 0.2 aceptable"},
    ])

    pdf_pred = p.select("ingreso", "prediction").toPandas()

    spark.stop()

    return {
        "total_raw":       total_raw,
        "total_final":     total_final,
        "df_calidad":      df_calidad,
        "df_schema":       df_schema,
        "basicas_pasos":   basicas_pasos,
        "avanzadas_pasos": avanzadas_pasos,
        "q1": q1, "q3": q3, "iqr": iqr, "lower": lower, "upper": upper,
        "pdf_precio_raw":  pdf_precio_raw,
        "pdf_precio_lim":  pdf_precio_lim,
        "df_stats":        df_stats,
        "metricas":        metricas,
        "pdf_pred":        pdf_pred,
        "r2": r2, "rmse": rmse, "mae": mae, "sil": sil,
    }


with st.spinner("⚙️ Ejecutando pipeline ETL con PySpark... (30-60 seg)"):
    D = ejecutar_etl(iqr_factor, imput_strategy, min_precio, max_precio)

retencion = D["total_final"] / D["total_raw"] * 100

# ════════════════════════════════════════════════════════════════
# TAB 1 – DIAGNÓSTICO & KDD
# ════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Diagrama de Minería de Datos (KDD)")

    # Diagrama KDD como tabla visual
    kdd_df = pd.DataFrame([
        {"#": "1", "Fase": "📥 DATOS RAW",        "Herramienta": "MongoDB Atlas / Local",
         "Descripción": "104,000 citas UrbanBlade con 14 campos"},
        {"#": "2", "Fase": "🔍 SELECCIÓN",         "Herramienta": "Spark .select()",
         "Descripción": "Elegir campos relevantes: servicio, barbero, precio, cantidad"},
        {"#": "3", "Fase": "🧹 PREPROCESADO",      "Herramienta": "dropna, fillna, filter",
         "Descripción": "Eliminar nulos, duplicados, rellenar valores faltantes"},
        {"#": "4", "Fase": "⚗️ TRANSFORMACIÓN",   "Herramienta": "Imputer, IQR, Scaler",
         "Descripción": "Imputar, detectar outliers, estandarizar y normalizar"},
        {"#": "5", "Fase": "⛏️ MINERÍA",           "Herramienta": "KMeans, Regresión, RF, PCA",
         "Descripción": "Aplicar algoritmos de aprendizaje automático"},
        {"#": "6", "Fase": "📊 INTERPRETACIÓN",    "Herramienta": "Streamlit + Plotly",
         "Descripción": "Dashboard ejecutivo con visualizaciones interactivas"},
        {"#": "7", "Fase": "💡 CONOCIMIENTO",      "Herramienta": "Decisiones de negocio",
         "Descripción": "Optimizar precios, identificar barberos estrella, retener clientes"},
    ])
    st.dataframe(kdd_df, use_container_width=True, hide_index=True)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros RAW",      f"{D['total_raw']:,}")
    c2.metric("Registros Limpios",  f"{D['total_final']:,}")
    c3.metric("Tasa Retención",     f"{retencion:.1f}%")
    c4.metric("Campos en Schema",   f"{len(D['df_schema'])}")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Diagnóstico de Calidad por Campo")
        df_cal = D["df_calidad"].copy()
        df_cal["Calidad"] = df_cal["% Nulo"].apply(
            lambda x: "✅ OK" if x < 5 else "⚠️ Revisar" if x < 30 else "❌ Crítico"
        )
        fig_cal = px.bar(
            df_cal, x="Campo", y="% Nulo", color="% Nulo",
            color_continuous_scale="RdYlGn_r",
            text=df_cal["% Nulo"].apply(lambda x: f"{x:.1f}%"),
            title="% de valores nulos por campo"
        )
        fig_cal.update_traces(textposition="outside")
        fig_cal.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            coloraxis_showscale=False, xaxis_tickangle=-30
        )
        st.plotly_chart(fig_cal, use_container_width=True)
        st.dataframe(df_cal, use_container_width=True, hide_index=True)

    with col_b:
        st.subheader("Schema de Datos (Tipos)")
        fig_schema = px.bar(
            D["df_schema"], x="Campo", y=[1]*len(D["df_schema"]),
            color="Tipo", text="Tipo",
            title="Campos y sus tipos de dato"
        )
        fig_schema.update_traces(textposition="inside")
        fig_schema.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            yaxis_visible=False, xaxis_tickangle=-30, showlegend=True
        )
        st.plotly_chart(fig_schema, use_container_width=True)
        st.dataframe(D["df_schema"], use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 – LIMPIEZA BÁSICA
# ════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Técnicas Básicas de Limpieza")

    st.markdown("""
    > Las técnicas básicas son el primer filtro de calidad. Se aplican **antes** de cualquier modelo.
    > En Big Data: **primero se limpia, luego se transforma, después se agrega.**
    """)

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Reducción de Registros por Técnica")
        bp = D["basicas_pasos"]
        fig_basic = go.Figure()
        fig_basic.add_trace(go.Bar(
            name="Registros Después",
            x=bp["Técnica"], y=bp["Después"],
            marker_color="#4ade80",
            text=bp["Después"].apply(lambda x: f"{x:,}"),
            textposition="outside"
        ))
        fig_basic.add_trace(go.Bar(
            name="Reducción",
            x=bp["Técnica"], y=bp["Reducción"],
            marker_color="#f87171",
            text=bp["Reducción"].apply(lambda x: f"-{x:,}" if x > 0 else ""),
            textposition="outside"
        ))
        fig_basic.update_layout(
            barmode="stack",
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            title="Impacto de cada técnica básica",
            xaxis_tickangle=-20, legend_font_size=11
        )
        st.plotly_chart(fig_basic, use_container_width=True)

    with col_b:
        st.subheader("Detalle de Técnicas Básicas")
        for _, row in bp.iterrows():
            delta = f"-{row['Reducción']:,}" if row["Reducción"] > 0 else "Sin pérdida"
            color = "🔴" if row["Reducción"] > 0 else "🟢"
            st.markdown(f"""
**{row['Técnica']}** {color}
- {row['Descripción']}
- Antes: `{row['Antes']:,}` → Después: `{row['Después']:,}` ({delta})
""")

    st.divider()
    st.subheader("Referencia de Código — Técnicas Básicas")
    st.code("""
# 1. Eliminar duplicados
df = df.dropDuplicates()

# 2. Filtrar nulos en campos críticos
df = df.filter(
    col("servicio").isNotNull() &
    col("precio").isNotNull()   &
    col("cantidad").isNotNull()
)

# 3. Rellenar nulos opcionales
df = df.fillna({
    "estado":      "desconocido",
    "propina":     0.0,
    "duracion_min": 30
})

# 4. Conversión de tipos de datos
df = df.withColumn("precio",   col("precio").cast("double"))
df = df.withColumn("cantidad", col("cantidad").cast("double"))

# 5. Reclasificación (no perder datos)
df = df.fillna({"producto": "SIN_CLASIFICAR"})
""", language="python")


# ════════════════════════════════════════════════════════════════
# TAB 3 – LIMPIEZA AVANZADA
# ════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Técnicas Avanzadas de Limpieza")

    c1, c2, c3 = st.columns(3)
    c1.metric("Q1 Precio",  f"${D['q1']:.0f}")
    c2.metric("Q3 Precio",  f"${D['q3']:.0f}")
    c3.metric("Rango IQR",  f"[${D['lower']:.0f}, ${D['upper']:.0f}]")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Distribución Precio: Antes vs Después de IQR")
        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=D["pdf_precio_raw"]["precio"], name="Antes",
            marker_color="#f87171", opacity=0.6, nbinsx=50
        ))
        fig_dist.add_trace(go.Histogram(
            x=D["pdf_precio_lim"]["precio"], name="Después IQR",
            marker_color="#4ade80", opacity=0.6, nbinsx=50
        ))
        fig_dist.add_vline(x=D["lower"], line_color="#fbbf24", line_dash="dash",
                           annotation_text=f"Límite inferior ${D['lower']:.0f}")
        fig_dist.add_vline(x=D["upper"], line_color="#fbbf24", line_dash="dash",
                           annotation_text=f"Límite superior ${D['upper']:.0f}")
        fig_dist.update_layout(
            barmode="overlay", paper_bgcolor="#111", plot_bgcolor="#111",
            font_color="#ccc", title="Efecto del filtro IQR en precios",
            xaxis_title="Precio ($)", yaxis_title="Frecuencia"
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_b:
        st.subheader("Box Plot — Detección Visual de Outliers")
        fig_box = go.Figure()
        fig_box.add_trace(go.Box(
            y=D["pdf_precio_raw"]["precio"], name="Antes",
            marker_color="#f87171", boxmean=True
        ))
        fig_box.add_trace(go.Box(
            y=D["pdf_precio_lim"]["precio"], name="Después IQR",
            marker_color="#4ade80", boxmean=True
        ))
        fig_box.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            title="Box Plot: Identificación de Outliers",
            yaxis_title="Precio ($)"
        )
        st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Detalle de Técnicas Avanzadas")
    for _, row in D["avanzadas_pasos"].iterrows():
        delta = f"-{row['Reducción']:,}" if row["Reducción"] > 0 else "Sin pérdida de registros"
        color = "🔴" if row["Reducción"] > 0 else "🟢"
        st.markdown(f"**{row['Técnica']}** {color} — {row['Descripción']} → {delta}")

    st.divider()
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Estandarización vs Normalización")
        comparativa = pd.DataFrame({
            "Técnica":         ["StandardScaler (Z-score)", "MinMaxScaler [0,1]"],
            "Fórmula":         ["(x - μ) / σ",              "(x - min) / (max - min)"],
            "Media resultante":["0",                         "Varía [0,1]"],
            "Rango resultado": ["(-∞, +∞)",                  "[0, 1]"],
            "Usar con":        ["Regresión, SVM, PCA",       "KNN, Redes Neuronales"],
        })
        st.dataframe(comparativa, use_container_width=True, hide_index=True)

    with col_d:
        st.subheader("Referencia de Código — Técnicas Avanzadas")
        st.code("""
# Imputación con media/mediana (MLlib)
from pyspark.ml.feature import Imputer
imputer = Imputer(inputCols=["precio","cantidad"],
                  outputCols=["precio_imp","cantidad_imp"],
                  strategy="mean")  # o "median"
df = imputer.fit(df).transform(df)

# IQR – Remoción de outliers
q1, q3 = df.approxQuantile("precio", [0.25, 0.75], 0.01)
iqr    = q3 - q1
df     = df.filter(
    (col("precio") >= q1 - 1.5*iqr) &
    (col("precio") <= q3 + 1.5*iqr)
)

# Estandarización Z-score
from pyspark.ml.feature import StandardScaler
scaler = StandardScaler(inputCol="features",
                        outputCol="features_std",
                        withMean=True, withStd=True)
df = scaler.fit(df).transform(df)

# Normalización [0,1]
from pyspark.ml.feature import MinMaxScaler
norm = MinMaxScaler(inputCol="features",
                    outputCol="features_norm")
df = norm.fit(df).transform(df)
""", language="python")

    st.subheader("Estadísticas Descriptivas Post-ETL")
    st.dataframe(D["df_stats"], use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 – PIPELINE ETL
# ════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Tipos de Extracción, Transformación y Carga (ETL)")

    # Tipos de Extracción
    st.markdown("### 📥 Tipos de Extracción del Dato")
    extraccion_df = pd.DataFrame([
        {"Tipo":     "Full Load (Carga Completa)",
         "Descripción": "Se extraen TODOS los registros de la fuente",
         "Cuándo usar": "Primera carga o dataset pequeño",
         "UrbanBlade": "✅ Usamos en este proyecto"},
        {"Tipo":     "Incremental Load",
         "Descripción": "Solo registros nuevos o modificados desde última extracción",
         "Cuándo usar": "Actualizaciones diarias en producción",
         "UrbanBlade": "⚙️ Futuro: filtrar por fecha.hora"},
        {"Tipo":     "Delta Load",
         "Descripción": "Solo los cambios (inserts + updates + deletes) desde un punto",
         "Cuándo usar": "Sistemas con alta frecuencia de cambios",
         "UrbanBlade": "⚙️ Requiere change streams MongoDB"},
        {"Tipo":     "Streaming (Tiempo Real)",
         "Descripción": "Flujo continuo de datos, procesamiento inmediato",
         "Cuándo usar": "IoT, eventos en tiempo real",
         "UrbanBlade": "⚙️ Kafka + Spark Streaming"},
    ])
    st.dataframe(extraccion_df, use_container_width=True, hide_index=True)

    st.divider()

    # Tipos de Transformación
    st.markdown("### ⚗️ Tipos de Transformación del Dato")
    transform_df = pd.DataFrame([
        {"Tipo":     "Limpieza",
         "Técnica":  "dropDuplicates, fillna, filter",
         "Ejemplo UrbanBlade": "Eliminar citas sin precio o servicio"},
        {"Tipo":     "Conversión de tipos",
         "Técnica":  "cast(DoubleType), cast(IntegerType)",
         "Ejemplo UrbanBlade": "cantidad: StringType → DoubleType"},
        {"Tipo":     "Imputación",
         "Técnica":  "Imputer(strategy='mean'/'median')",
         "Ejemplo UrbanBlade": "Propina faltante → media de propinas"},
        {"Tipo":     "Estandarización",
         "Técnica":  "StandardScaler (Z-score μ=0, σ=1)",
         "Ejemplo UrbanBlade": "precio y cantidad para PCA/Regresión"},
        {"Tipo":     "Normalización",
         "Técnica":  "MinMaxScaler [0, 1]",
         "Ejemplo UrbanBlade": "Features para Red Neuronal PyTorch"},
        {"Tipo":     "Ingeniería de características",
         "Técnica":  "withColumn(), VectorAssembler",
         "Ejemplo UrbanBlade": "ingreso = cantidad × precio"},
        {"Tipo":     "Remoción de outliers",
         "Técnica":  "IQR, Z-score threshold",
         "Ejemplo UrbanBlade": "Precios fuera de rango [Q1-1.5IQR, Q3+1.5IQR]"},
        {"Tipo":     "Agregación (MapReduce)",
         "Técnica":  "groupBy().agg(sum, avg, count)",
         "Ejemplo UrbanBlade": "Ingreso total por barbero y servicio"},
    ])
    st.dataframe(transform_df, use_container_width=True, hide_index=True)

    st.divider()

    # Tipos de Carga
    st.markdown("### 📤 Tipos de Carga de Datos")
    carga_df = pd.DataFrame([
        {"Tipo":     "In-Memory (Spark DataFrame)",
         "Ventaja":  "Ultra rápido, distribución en clústeres",
         "UrbanBlade": "✅ Usado — DataFrame en memoria para ML"},
        {"Tipo":     "Data Warehouse (Parquet/CSV)",
         "Ventaja":  "Persistencia, consultas BI, columnar",
         "UrbanBlade": "⚙️ Futuro: exportar a .parquet"},
        {"Tipo":     "MongoDB (misma o nueva colección)",
         "Ventaja":  "Escritura de vuelta al origen enriquecida",
         "UrbanBlade": "⚙️ Escribir predicciones → appointments_clean"},
        {"Tipo":     "Dashboard / Visualización (Pandas)",
         "Ventaja":  "Muestra resultados a usuarios finales",
         "UrbanBlade": "✅ toPandas() → Streamlit + Plotly"},
        {"Tipo":     "API REST (FastAPI)",
         "Ventaja":  "Exponer predicciones como endpoints HTTP",
         "UrbanBlade": "✅ BarberPro backend FastAPI integrado"},
    ])
    st.dataframe(carga_df, use_container_width=True, hide_index=True)

    st.divider()

    # Flujo ETL Visual
    st.subheader("Flujo ETL Visual — UrbanBlade")
    fig_etl = go.Figure()

    fases  = ["MongoDB\n104K registros", "Extracción\n(Full Load)",
              "Transformación\nBásica", "Transformación\nAvanzada",
              "Carga\nDataFrame", "ML Pipeline\nKMeans/RF/PCA"]
    colores = ["#818cf8", "#fbbf24", "#f87171", "#fb923c", "#4ade80", "#d4af37"]
    x_pos  = list(range(len(fases)))

    for i, (fase, color) in enumerate(zip(fases, colores)):
        fig_etl.add_trace(go.Scatter(
            x=[i], y=[0], mode="markers+text",
            marker=dict(size=40, color=color, symbol="square"),
            text=[fase], textposition="top center",
            name=fase.split("\n")[0], showlegend=False
        ))
        if i < len(fases) - 1:
            fig_etl.add_annotation(
                x=i+0.5, y=0,
                text="→", font=dict(size=24, color="#888"),
                showarrow=False
            )

    fig_etl.update_layout(
        paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
        title="Pipeline ETL Completo – UrbanBlade Big Data",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=250, margin=dict(t=60, b=80)
    )
    st.plotly_chart(fig_etl, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Registros entrada (RAW)",  f"{D['total_raw']:,}")
        st.metric("Registros salida (CLEAN)",  f"{D['total_final']:,}")
    with col_b:
        st.metric("Retención de datos",        f"{retencion:.1f}%")
        st.metric("Registros eliminados",      f"{D['total_raw'] - D['total_final']:,}")


# ════════════════════════════════════════════════════════════════
# TAB 5 – MÉTRICAS DE EVALUACIÓN
# ════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Métricas de Evaluación de Modelos de Procesamiento")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("R² Score",      round(D["r2"],   4), help="Coeficiente de determinación (0→1)")
    c2.metric("RMSE",          f"${D['rmse']:.2f}", help="Raíz error cuadrático medio")
    c3.metric("MAE",           f"${D['mae']:.2f}",  help="Error absoluto medio")
    c4.metric("Silhouette",    round(D["sil"],  4), help="Calidad clustering KMeans (−1→1)")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Comparativa de Métricas")
        fig_met = go.Figure()
        fig_met.add_trace(go.Bar(
            x=["R²", "Silhouette"],
            y=[D["r2"], D["sil"]],
            name="Mayor es mejor [0,1]",
            marker_color="#4ade80",
            text=[round(D["r2"], 4), round(D["sil"], 4)],
            textposition="outside"
        ))
        fig_met.update_layout(
            paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
            title="Métricas normalizadas [0, 1]",
            yaxis_range=[0, 1.2]
        )
        st.plotly_chart(fig_met, use_container_width=True)

    with col_b:
        st.subheader("Real vs Predicho (Regresión Lineal)")
        sample_p = D["pdf_pred"].sample(min(2000, len(D["pdf_pred"])), random_state=42)
        max_v = max(sample_p["ingreso"].max(), sample_p["prediction"].max())
        fig_pred = px.scatter(sample_p, x="ingreso", y="prediction",
                              opacity=0.4, color_discrete_sequence=["#d4af37"],
                              labels={"ingreso": "Real ($)", "prediction": "Predicho ($)"},
                              title="Predicción vs Valor Real")
        fig_pred.add_scatter(x=[0, max_v], y=[0, max_v], mode="lines",
                             line=dict(color="#4ade80", dash="dash"), name="Ideal")
        fig_pred.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_pred, use_container_width=True)

    st.subheader("📋 Tabla Completa de Métricas")
    df_met = D["metricas"].copy()
    df_met["Estado"] = df_met.apply(lambda row: (
        "✅ Excelente" if (row["Métrica"].startswith("R²") and row["Valor"] > 0.85) else
        "✅ Excelente" if (row["Métrica"].startswith("Silhouette") and row["Valor"] > 0.5) else
        "⚠️ Aceptable" if (row["Métrica"].startswith("R²") and row["Valor"] > 0.6) else
        "⚠️ Aceptable" if (row["Métrica"].startswith("Silhouette") and row["Valor"] > 0.2) else
        "📊 Informativo"
    ), axis=1)
    st.dataframe(df_met, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Guía de Métricas — Cuándo usar cada una")
    guia_df = pd.DataFrame([
        {"Métrica": "R² (R cuadrado)",
         "Tipo modelo": "Regresión",
         "Fórmula": "1 - SS_res/SS_tot",
         "Rango": "[0, 1]",
         "Cuándo usarla": "Evaluar qué tan bien la regresión explica los datos"},
        {"Métrica": "RMSE",
         "Tipo modelo": "Regresión",
         "Fórmula": "√(Σ(y-ŷ)²/n)",
         "Rango": "[0, ∞)",
         "Cuándo usarla": "Penaliza errores grandes; sensible a outliers"},
        {"Métrica": "MAE",
         "Tipo modelo": "Regresión",
         "Fórmula": "Σ|y-ŷ|/n",
         "Rango": "[0, ∞)",
         "Cuándo usarla": "Interpretable en unidades originales; robusto a outliers"},
        {"Métrica": "Accuracy",
         "Tipo modelo": "Clasificación",
         "Fórmula": "Correctas / Total",
         "Rango": "[0, 1]",
         "Cuándo usarla": "Dataset balanceado; fácil interpretación"},
        {"Métrica": "AUC-ROC",
         "Tipo modelo": "Clasificación Binaria",
         "Fórmula": "Área bajo curva ROC",
         "Rango": "[0.5, 1]",
         "Cuándo usarla": "Dataset desbalanceado; mide discriminación"},
        {"Métrica": "Silhouette Score",
         "Tipo modelo": "Clustering (KMeans)",
         "Fórmula": "(b-a)/max(a,b)",
         "Rango": "[-1, 1]",
         "Cuándo usarla": "Evaluar cohesión y separación de clusters"},
    ])
    st.dataframe(guia_df, use_container_width=True, hide_index=True)


# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style="text-align:center; color:#555; font-size:11px;">
🧹 UrbanBlade – Validación y Limpieza de Datos · PySpark 3.5.1 + MongoDB + MLlib · UTVT IDGS-93<br>
Prof. MGTI. Héctor Velázquez Estrada · Materia: Extracción del Conocimiento en BD
</div>
""", unsafe_allow_html=True)
