"""
Dashboard – Análisis RFM de Clientes | UrbanBlade
Materia: Extracción del Conocimiento en BD ·  UTVT IDGS-93
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="UrbanBlade – RFM Clientes",
                   page_icon="👥", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0a0a0a; }
[data-testid="stSidebar"]          { background: #111111; }
h1 { color: #d4af37 !important; }
h2, h3 { color: #e8d5a3 !important; }
.stMetric label { color: #888 !important; font-size: 11px !important; }
.stMetric [data-testid="stMetricValue"] { color: #d4af37 !important; font-size: 26px !important; font-weight: 900; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #d4af37 !important; border-bottom: 2px solid #d4af37; }
</style>""", unsafe_allow_html=True)

st.markdown("# 👥 UrbanBlade — Análisis RFM de Clientes")
st.markdown("**Extracción del Conocimiento en BD ·  UTVT IDGS-93 · Prof. Héctor Velázquez Estrada**")
st.divider()

st.sidebar.markdown("### ⚙️ Configuración RFM")
k_rfm    = st.sidebar.slider("Segmentos (K)", 2, 6, 4)
ejecutar = st.sidebar.button("🚀 Calcular RFM", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("""
**¿Qué es RFM?**
- **R**ecency: cuándo visitó por última vez
- **F**requency: cuántas veces ha visitado
- **M**onetary: cuánto ha gastado
""")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Segmentos RFM",
    "🔵 Scatter 3D",
    "🏆 Clientes Top",
    "💡 Recomendaciones",
])

if not ejecutar:
    with tab1:
        st.info("👈 Haz clic en **Calcular RFM** para segmentar los clientes.")
        st.markdown("""
        ### ¿Por qué RFM?
        RFM es el estándar de la industria para análisis de clientes.
        Lo usan Amazon, Spotify, Netflix y cualquier empresa orientada a datos.

        | Segmento | Descripción | Acción |
        |----------|-------------|--------|
        | ⭐ VIP | Visita frecuente, gasto alto, reciente | Programa premium |
        | 💚 Leal | Viene regularmente, gasto medio | Comunicación constante |
        | ⚠️ En Riesgo | No viene hace tiempo pero gastó bien | Reactivación urgente |
        | 💤 Inactivo | Poca frecuencia, poco gasto | Oferta especial |
        """)
    st.stop()


@st.cache_resource
def calcular_rfm(k):
    from pyspark.sql.functions import (col, max as _max, count, sum as _sum,
                                       datediff, lit, avg)
    from pyspark.ml.feature import VectorAssembler, StandardScaler
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    from config.mongo_spark_conexion_sinnulos import get_spark_session

    spark, _, __ = get_spark_session()
    df = spark.read.format("mongodb").load()
    df = df.filter(col("fecha").isNotNull() & col("cliente_id").isNotNull()) \
           .withColumn("ingreso", col("cantidad").cast("double") * col("precio").cast("double"))

    fecha_ref = df.agg(_max("fecha")).collect()[0][0]
    fecha_str = fecha_ref.strftime("%Y-%m-%d")

    df_comp = df.filter(col("estado") == "completada")

    recency = df.groupBy("cliente_id").agg(
        _max("fecha").alias("ultima_visita")
    ).withColumn("recency",
        datediff(lit(fecha_str).cast("date"),
                 col("ultima_visita").cast("date")))

    frequency = df_comp.groupBy("cliente_id").agg(
        count("*").alias("frequency"))

    monetary = df_comp.groupBy("cliente_id").agg(
        _sum("ingreso").alias("monetary"))

    rfm = recency.join(frequency, "cliente_id", "left") \
                 .join(monetary,  "cliente_id", "left") \
                 .fillna({"frequency": 0, "monetary": 0.0}) \
                 .filter(col("frequency") > 0)

    asm    = VectorAssembler(inputCols=["recency","frequency","monetary"],
                             outputCol="features_raw", handleInvalid="skip")
    rfm_v  = asm.transform(rfm.dropna(subset=["recency","frequency","monetary"]))
    scaler = StandardScaler(inputCol="features_raw", outputCol="features",
                            withMean=True, withStd=True)
    rfm_sc = scaler.fit(rfm_v).transform(rfm_v)

    km    = KMeans(k=k, seed=42, featuresCol="features", predictionCol="segmento")
    model = km.fit(rfm_sc)
    rfm_seg = model.transform(rfm_sc)

    sil = ClusteringEvaluator(featuresCol="features", predictionCol="segmento").evaluate(rfm_seg)

    pdf = rfm_seg.select("cliente_id","recency","frequency","monetary","segmento").toPandas()
    total_clientes = rfm.count()

    perfil = pdf.groupby("segmento").agg(
        clientes=("cliente_id","count"),
        recency_avg=("recency","mean"),
        freq_avg=("frequency","mean"),
        monetary_avg=("monetary","mean"),
        monetary_total=("monetary","sum")
    ).reset_index().sort_values("monetary_avg", ascending=False)

    spark.stop()
    return pdf, perfil, sil, fecha_str, total_clientes


with st.spinner("Calculando RFM con PySpark... (30-60 seg)"):
    pdf, perfil, sil, fecha_ref, total_clientes = calcular_rfm(k_rfm)

# Etiquetar segmentos automáticamente
max_monetary = perfil["monetary_avg"].max()
min_recency  = perfil["recency_avg"].min()
sorted_mon   = sorted(perfil["monetary_avg"].tolist(), reverse=True)
sorted_rec   = sorted(perfil["recency_avg"].tolist())

COLORES   = {0: "#ffd700", 1: "#4ade80", 2: "#fb923c", 3: "#818cf8",
             4: "#f87171", 5: "#38bdf8"}
ETIQUETAS = {}
for _, row in perfil.iterrows():
    seg = int(row["segmento"])
    if row["monetary_avg"] == max_monetary and row["recency_avg"] == min_recency:
        ETIQUETAS[seg] = "⭐ VIP"
    elif row["monetary_avg"] >= sorted_mon[min(1, len(sorted_mon)-1)]:
        ETIQUETAS[seg] = "💚 Leal"
    elif row["recency_avg"] <= sorted_rec[min(1, len(sorted_rec)-1)]:
        ETIQUETAS[seg] = "⚠️ En Riesgo"
    else:
        ETIQUETAS[seg] = "💤 Inactivo"

perfil["etiqueta"] = perfil["segmento"].map(ETIQUETAS)
pdf["etiqueta"]    = pdf["segmento"].map(ETIQUETAS)
pdf["color"]       = pdf["segmento"].map(COLORES)

# KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Clientes Analizados", f"{total_clientes:,}")
c2.metric("Silhouette Score",    round(sil, 4))
c3.metric("Segmentos",           k_rfm)
vip_seg = perfil.loc[perfil["etiqueta"].str.contains("VIP")]
if not vip_seg.empty:
    c4.metric("Clientes VIP",    f"{int(vip_seg.iloc[0]['clientes']):,}")
c5.metric("Fecha Referencia",    fecha_ref)

# ════════════════════════════════════════════════════════════════
# TAB 1 – SEGMENTOS
# ════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Distribución de Segmentos RFM")

    col_a, col_b = st.columns(2)

    with col_a:
        fig_pie = px.pie(perfil, values="clientes", names="etiqueta",
                         color_discrete_sequence=list(COLORES.values()),
                         title="Distribución de Clientes por Segmento",
                         hole=0.4)
        fig_pie.update_layout(paper_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.subheader("Perfil de cada Segmento")
        perf_show = perfil[["etiqueta","clientes","recency_avg","freq_avg",
                             "monetary_avg","monetary_total"]].copy()
        perf_show["recency_avg"]   = perf_show["recency_avg"].apply(lambda x: f"{x:.0f} días")
        perf_show["freq_avg"]      = perf_show["freq_avg"].apply(lambda x: f"{x:.1f} visitas")
        perf_show["monetary_avg"]  = perf_show["monetary_avg"].apply(lambda x: f"${x:,.0f}")
        perf_show["monetary_total"]= perf_show["monetary_total"].apply(lambda x: f"${x:,.0f}")
        perf_show.columns = ["Segmento","Clientes","Recency Avg","Freq Avg",
                              "Gasto Avg","Gasto Total"]
        st.dataframe(perf_show, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Métricas RFM por Segmento (Barras)")
    col_c, col_d, col_e = st.columns(3)

    with col_c:
        fig_r = px.bar(perfil, x="etiqueta", y="recency_avg",
                       color="etiqueta", color_discrete_sequence=list(COLORES.values()),
                       text=perfil["recency_avg"].apply(lambda x: f"{x:.0f}d"),
                       title="Recency promedio (días)")
        fig_r.update_traces(textposition="outside")
        fig_r.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                            font_color="#ccc", showlegend=False)
        st.plotly_chart(fig_r, use_container_width=True)

    with col_d:
        fig_f = px.bar(perfil, x="etiqueta", y="freq_avg",
                       color="etiqueta", color_discrete_sequence=list(COLORES.values()),
                       text=perfil["freq_avg"].apply(lambda x: f"{x:.1f}"),
                       title="Frequency promedio (visitas)")
        fig_f.update_traces(textposition="outside")
        fig_f.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                            font_color="#ccc", showlegend=False)
        st.plotly_chart(fig_f, use_container_width=True)

    with col_e:
        fig_m = px.bar(perfil, x="etiqueta", y="monetary_avg",
                       color="etiqueta", color_discrete_sequence=list(COLORES.values()),
                       text=perfil["monetary_avg"].apply(lambda x: f"${x:,.0f}"),
                       title="Monetary promedio ($)")
        fig_m.update_traces(textposition="outside")
        fig_m.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                            font_color="#ccc", showlegend=False)
        st.plotly_chart(fig_m, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 – SCATTER 3D
# ════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Visualización 3D del Espacio RFM")

    sample = pdf.sample(min(2000, len(pdf)), random_state=42)
    fig_3d = px.scatter_3d(
        sample,
        x="recency", y="frequency", z="monetary",
        color="etiqueta",
        color_discrete_sequence=list(COLORES.values()),
        hover_data=["cliente_id"],
        opacity=0.7,
        title="Clientes en el espacio RFM 3D",
        labels={"recency": "Días sin visitar", "frequency": "Visitas",
                "monetary": "Gasto Total ($)"}
    )
    fig_3d.update_layout(paper_bgcolor="#111", font_color="#ccc")
    st.plotly_chart(fig_3d, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        fig_rf = px.scatter(sample, x="recency", y="frequency",
                            color="etiqueta",
                            color_discrete_sequence=list(COLORES.values()),
                            opacity=0.6, title="Recency vs Frequency")
        fig_rf.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_rf, use_container_width=True)

    with col_b:
        fig_fm = px.scatter(sample, x="frequency", y="monetary",
                            color="etiqueta",
                            color_discrete_sequence=list(COLORES.values()),
                            opacity=0.6, title="Frequency vs Monetary")
        fig_fm.update_layout(paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_fm, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 3 – CLIENTES TOP
# ════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Top 20 Clientes por Gasto Total")

    top_clientes = pdf.nlargest(20, "monetary")[
        ["cliente_id","etiqueta","recency","frequency","monetary"]
    ].copy()
    top_clientes["monetary"] = top_clientes["monetary"].apply(lambda x: f"${x:,.0f}")
    top_clientes["recency"]  = top_clientes["recency"].apply(lambda x: f"{x} días")
    top_clientes.columns     = ["Cliente","Segmento","Días sin visitar","Visitas","Gasto Total"]
    st.dataframe(top_clientes, use_container_width=True, hide_index=True)

    st.subheader("Distribución de Gasto por Segmento")
    fig_box = px.box(pdf, x="etiqueta", y="monetary",
                     color="etiqueta",
                     color_discrete_sequence=list(COLORES.values()),
                     title="Distribución del Gasto por Segmento",
                     labels={"monetary": "Gasto Total ($)", "etiqueta": "Segmento"})
    fig_box.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                          font_color="#ccc", showlegend=False)
    st.plotly_chart(fig_box, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 – RECOMENDACIONES
# ════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Plan de Acción por Segmento")

    acciones = [
        {"Segmento": "⭐ VIP",
         "Descripción": "Clientes frecuentes, alto gasto, visita reciente",
         "Acción inmediata": "Membresía premium, descuentos exclusivos VIP",
         "Acción a largo plazo": "Programa de referidos, acceso anticipado a nuevos servicios",
         "KPI objetivo": "Retención > 90%, ticket promedio +15%"},
        {"Segmento": "💚 Leal",
         "Descripción": "Clientes regulares con buen historial",
         "Acción inmediata": "Notificaciones personalizadas, recordatorio de cita",
         "Acción a largo plazo": "Subir a VIP: incentivar servicios de mayor precio",
         "KPI objetivo": "Frequency +20%, monetary +10%"},
        {"Segmento": "⚠️ En Riesgo",
         "Descripción": "Gastaron bien antes pero no han vuelto recientemente",
         "Acción inmediata": "Cupón de descuento urgente 20%, mensaje personalizado",
         "Acción a largo plazo": "Encuesta de satisfacción, campaña de reconexión",
         "KPI objetivo": "Reactivar 40% en próximos 30 días"},
        {"Segmento": "💤 Inactivo",
         "Descripción": "Poca actividad y/o hace mucho que no visitan",
         "Acción inmediata": "Campaña 'Te extrañamos' + oferta 30% off",
         "Acción a largo plazo": "Evaluar si vale la pena el costo de reactivación",
         "KPI objetivo": "Reactivar 15%, rest → marcar como perdidos"},
    ]

    for a in acciones:
        with st.expander(f"{a['Segmento']} — {a['Descripción']}", expanded=True):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Acción Inmediata**\n\n{a['Acción inmediata']}")
            c2.markdown(f"**Acción a Largo Plazo**\n\n{a['Acción a largo plazo']}")
            c3.markdown(f"**KPI Objetivo**\n\n{a['KPI objetivo']}")

    st.divider()
    st.markdown("""
    > **RFM en la práctica**: Esta metodología es usada por Amazon, Spotify, Netflix y toda empresa
    > que trabaja con datos de clientes para personalizar comunicaciones y maximizar el valor de vida del cliente (CLV).
    """)

st.divider()
st.markdown("""<div style="text-align:center;color:#555;font-size:11px;">
👥 UrbanBlade RFM Analysis · PySpark 3.5.1 ·  UTVT IDGS-93 · Prof. Héctor Velázquez Estrada
</div>""", unsafe_allow_html=True)
