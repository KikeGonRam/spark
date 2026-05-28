"""
Dashboard – Series de Tiempo | UrbanBlade
Materia: Extracción del Conocimiento en BD ·  UTVT IDGS-93
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="UrbanBlade – Series de Tiempo",
                   page_icon="📅", layout="wide")

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

st.markdown("# 📅 UrbanBlade — Análisis de Series de Tiempo")
st.markdown("**Extracción del Conocimiento en BD ·  UTVT IDGS-93 · Prof. Héctor Velázquez Estrada**")
st.divider()

st.sidebar.markdown("### ⚙️ Configuración")
n_pred     = st.sidebar.slider("Meses a predecir", 1, 6, 3)
estado_fil = st.sidebar.multiselect("Estados a incluir",
    ["completada", "cancelada", "pendiente", "no_asistio"],
    default=["completada"])
ejecutar = st.sidebar.button("🚀 Analizar Serie Temporal", type="primary", use_container_width=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Tendencia Mensual",
    "🔥 Heatmap Horas",
    "🏆 Top por Período",
    "🔮 Predicción",
])

if not ejecutar:
    with tab1:
        st.info("👈 Selecciona los estados y haz clic en **Analizar Serie Temporal**.")
    st.stop()


@st.cache_resource
def cargar_series(estados):
    from pyspark.sql.functions import (col, year, month, hour, dayofweek,
                                       sum as _sum, count, avg, date_format)
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.regression import LinearRegression
    from config.mongo_spark_conexion_sinnulos import get_spark_session

    spark, _, __ = get_spark_session()

    df = spark.read.format("mongodb").load()
    df = df.filter(col("fecha").isNotNull()) \
           .withColumn("anio",    year(col("fecha"))) \
           .withColumn("mes",     month(col("fecha"))) \
           .withColumn("hora",    hour(col("fecha"))) \
           .withColumn("dia_sem", dayofweek(col("fecha"))) \
           .withColumn("ingreso", col("cantidad").cast("double") * col("precio").cast("double"))

    if estados:
        df = df.filter(col("estado").isin(estados))

    # Mensual
    mensual = df.groupBy("anio", "mes").agg(
        _sum("ingreso").alias("ingreso_total"),
        count("*").alias("num_citas"),
        avg("ingreso").alias("ticket_promedio")
    ).orderBy("anio", "mes").toPandas()

    # Por hora
    por_hora = df.groupBy("hora").agg(
        count("*").alias("citas"),
        _sum("ingreso").alias("ingreso")
    ).orderBy("hora").toPandas()

    # Heatmap hora × día de semana
    heatmap = df.groupBy("dia_sem", "hora").agg(
        count("*").alias("citas")
    ).toPandas()

    # Por servicio mensual
    serv_mes = df.groupBy("anio", "mes", "servicio").agg(
        _sum("ingreso").alias("ingreso_total")
    ).orderBy("anio", "mes").toPandas()

    # Por barbero mensual
    barb_mes = df.groupBy("anio", "mes", "barbero").agg(
        count("*").alias("citas")
    ).orderBy("anio", "mes").toPandas()

    spark.stop()
    return mensual, por_hora, heatmap, serv_mes, barb_mes


with st.spinner("Procesando series de tiempo con PySpark..."):
    mensual, por_hora, heatmap, serv_mes, barb_mes = cargar_series(tuple(estado_fil))

if mensual.empty:
    st.error("Sin datos. Revisa los filtros de estado.")
    st.stop()

# Predicción con sklearn (sin Spark)
from sklearn.linear_model import LinearRegression as LR
import numpy as np

mensual["t"] = range(len(mensual))
mensual["periodo"] = mensual["anio"].astype(str) + "-" + mensual["mes"].astype(str).str.zfill(2)

X = mensual[["t"]].values
y = mensual["ingreso_total"].values
lr = LR().fit(X, y)
r2 = lr.score(X, y)

n = len(mensual)
futuros_t    = np.array([[n + i] for i in range(n_pred)])
futuros_pred = lr.predict(futuros_t)

# Generar etiquetas de meses futuros
ultimo_anio = int(mensual["anio"].iloc[-1])
ultimo_mes  = int(mensual["mes"].iloc[-1])
futuros_lab = []
for i in range(1, n_pred + 1):
    m = ultimo_mes + i
    a = ultimo_anio + (m - 1) // 12
    m = ((m - 1) % 12) + 1
    futuros_lab.append(f"{a}-{m:02d}")

# ─── KPIs ────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Meses analizados",  f"{len(mensual)}")
c2.metric("Ingreso Total",     f"${mensual['ingreso_total'].sum():,.0f}")
c3.metric("Mejor Mes",         mensual.loc[mensual['ingreso_total'].idxmax(), 'periodo'])
c4.metric("R² Modelo",         round(r2, 4))
c5.metric("Predicción Mes +1", f"${futuros_pred[0]:,.0f}")

# ════════════════════════════════════════════════════════════════
# TAB 1 – TENDENCIA MENSUAL
# ════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Ingresos Mensuales — 18 Meses de Historial")

    # Línea histórica + tendencia + predicción
    hist_x    = mensual["periodo"].tolist()
    hist_y    = mensual["ingreso_total"].tolist()
    tend_y    = lr.predict(X).tolist()
    pred_x    = futuros_lab
    pred_y    = futuros_pred.tolist()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_x, y=hist_y, mode="lines+markers",
                             name="Ingreso Real",
                             line=dict(color="#d4af37", width=2.5),
                             marker=dict(size=6)))
    fig.add_trace(go.Scatter(x=hist_x, y=tend_y, mode="lines",
                             name=f"Tendencia (R²={r2:.3f})",
                             line=dict(color="#818cf8", width=2, dash="dash")))
    fig.add_trace(go.Scatter(x=pred_x, y=pred_y, mode="lines+markers",
                             name="Predicción",
                             line=dict(color="#4ade80", width=2, dash="dot"),
                             marker=dict(size=8, symbol="star")))
    fig.add_vrect(x0=hist_x[-1], x1=pred_x[-1],
                  fillcolor="#4ade80", opacity=0.05,
                  annotation_text="Zona predicha", annotation_position="top left")
    fig.update_layout(
        paper_bgcolor="#111", plot_bgcolor="#111", font_color="#ccc",
        title="Tendencia de Ingresos UrbanBlade", xaxis_tickangle=-30,
        legend=dict(orientation="h", y=-0.25)
    )
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Número de Citas por Mes")
        fig_citas = px.bar(mensual, x="periodo", y="num_citas",
                           color="num_citas", color_continuous_scale="Viridis",
                           title="Volumen de Citas Mensual")
        fig_citas.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                                font_color="#ccc", coloraxis_showscale=False,
                                xaxis_tickangle=-30)
        st.plotly_chart(fig_citas, use_container_width=True)

    with col_b:
        st.subheader("Ticket Promedio por Mes")
        fig_tick = px.line(mensual, x="periodo", y="ticket_promedio",
                           markers=True, title="Ticket Promedio ($)",
                           color_discrete_sequence=["#fb923c"])
        fig_tick.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                               font_color="#ccc", xaxis_tickangle=-30)
        st.plotly_chart(fig_tick, use_container_width=True)

    st.subheader("Predicción próximos meses")
    pred_df = pd.DataFrame({"Período": futuros_lab,
                             "Ingreso Predicho": [f"${v:,.0f}" for v in futuros_pred]})
    st.dataframe(pred_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 – HEATMAP HORAS
# ════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Heatmap de Intensidad: Hora del Día × Día de Semana")

    dias_map = {1: "Dom", 2: "Lun", 3: "Mar", 4: "Mié", 5: "Jue", 6: "Vie", 7: "Sáb"}
    if not heatmap.empty:
        heatmap["dia_nombre"] = heatmap["dia_sem"].map(dias_map)
        pivot = heatmap.pivot_table(index="dia_nombre", columns="hora",
                                    values="citas", fill_value=0)
        orden_dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        pivot = pivot.reindex([d for d in orden_dias if d in pivot.index])

        fig_heat = px.imshow(pivot,
                             color_continuous_scale="YlOrRd",
                             title="Intensidad de citas: más oscuro = más demanda",
                             labels=dict(x="Hora del día", y="Día de semana", color="Citas"),
                             aspect="auto")
        fig_heat.update_layout(paper_bgcolor="#111", font_color="#ccc")
        st.plotly_chart(fig_heat, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Citas por Hora del Día")
        fig_hora = px.bar(por_hora, x="hora", y="citas",
                          color="citas", color_continuous_scale="Plasma",
                          text="citas", title="Distribución horaria")
        fig_hora.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig_hora.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                               font_color="#ccc", coloraxis_showscale=False)
        st.plotly_chart(fig_hora, use_container_width=True)

    with col_b:
        st.subheader("Ingresos por Hora del Día")
        fig_ing_hora = px.bar(por_hora, x="hora", y="ingreso",
                              color="ingreso", color_continuous_scale="Viridis",
                              title="Ingreso por franja horaria")
        fig_ing_hora.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                                   font_color="#ccc", coloraxis_showscale=False)
        st.plotly_chart(fig_ing_hora, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 3 – TOP POR PERÍODO
# ════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Evolución por Servicio y Barbero")

    if not serv_mes.empty:
        serv_mes["periodo"] = serv_mes["anio"].astype(str) + "-" + \
                              serv_mes["mes"].astype(str).str.zfill(2)
        fig_serv = px.line(serv_mes, x="periodo", y="ingreso_total",
                           color="servicio", markers=True,
                           title="Ingreso por Servicio a lo Largo del Tiempo")
        fig_serv.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                               font_color="#ccc", xaxis_tickangle=-30,
                               legend=dict(orientation="h", y=-0.3))
        st.plotly_chart(fig_serv, use_container_width=True)

    if not barb_mes.empty:
        barb_mes["periodo"] = barb_mes["anio"].astype(str) + "-" + \
                              barb_mes["mes"].astype(str).str.zfill(2)
        fig_barb = px.area(barb_mes, x="periodo", y="citas",
                           color="barbero",
                           title="Volumen de Citas por Barbero (Area Chart)")
        fig_barb.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                               font_color="#ccc", xaxis_tickangle=-30,
                               legend=dict(orientation="h", y=-0.3))
        st.plotly_chart(fig_barb, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 – PREDICCIÓN INTERACTIVA
# ════════════════════════════════════════════════════════════════
with tab4:
    st.subheader(f"Proyección de Ingresos — Próximos {n_pred} Meses")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Tendencia mensual", f"${lr.coef_[0]:,.0f}/mes",
                  delta="Positiva ↗" if lr.coef_[0] > 0 else "Negativa ↘")
        st.metric("R² del modelo", round(r2, 4))
        crecimiento = ((futuros_pred[-1] - hist_y[-1]) / hist_y[-1] * 100) if hist_y[-1] != 0 else 0
        st.metric(f"Crecimiento proyectado ({n_pred} meses)", f"{crecimiento:+.1f}%")

    with col_b:
        pred_df2 = pd.DataFrame({
            "Período": futuros_lab,
            "Predicción ($)": [round(v) for v in futuros_pred],
            "vs Último Mes": [f"{(v - hist_y[-1])/hist_y[-1]*100:+.1f}%" if hist_y[-1] != 0 else "N/A"
                              for v in futuros_pred]
        })
        st.dataframe(pred_df2, use_container_width=True, hide_index=True)

    st.caption("Modelo: Regresión Lineal Simple sobre índice temporal t=0,1,...,n")
    st.caption(f"Fórmula: ingreso = {lr.coef_[0]:,.0f}·t + {lr.intercept_:,.0f}")

st.divider()
st.markdown("""<div style="text-align:center;color:#555;font-size:11px;">
📅 UrbanBlade Series de Tiempo · PySpark 3.5.1 ·  UTVT IDGS-93 · Prof. Héctor Velázquez Estrada
</div>""", unsafe_allow_html=True)
