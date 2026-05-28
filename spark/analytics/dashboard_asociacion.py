"""
Dashboard – Reglas de Asociación FP-Growth | UrbanBlade
Materia: Extracción del Conocimiento en BD ·  UTVT IDGS-93
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(page_title="UrbanBlade – Reglas de Asociación",
                   page_icon="🔗", layout="wide")

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

st.markdown("# 🔗 UrbanBlade — Reglas de Asociación (FP-Growth)")
st.markdown("**Extracción del Conocimiento en BD ·  UTVT IDGS-93 · Prof. Héctor Velázquez Estrada**")
st.divider()

st.sidebar.markdown("### ⚙️ Parámetros FP-Growth")
min_sup  = st.sidebar.slider("Soporte mínimo", 0.01, 0.30, 0.05, 0.01)
min_conf = st.sidebar.slider("Confianza mínima", 0.10, 0.90, 0.30, 0.05)
ejecutar = st.sidebar.button("🚀 Ejecutar FP-Growth", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Métricas clave:**
- **Soporte**: frecuencia del conjunto
- **Confianza**: P(B | A)
- **Lift > 1**: relación real (no aleatoria)
""")

tab1, tab2, tab3 = st.tabs([
    "📋 Reglas de Asociación",
    "🔥 Heatmap de Servicios",
    "📚 Teoría FP-Growth",
])

if not ejecutar:
    with tab1:
        st.info("👈 Ajusta el soporte y confianza, luego haz clic en **Ejecutar FP-Growth**.")
        st.markdown("""
        ### ¿Qué es FP-Growth?
        FP-Growth (Frequent Pattern Growth) es un algoritmo de **minería de reglas de asociación**
        más eficiente que Apriori porque usa un árbol comprimido (FP-Tree) en lugar de generar candidatos.

        **Ejemplo de regla:**
        > Si un cliente pide **[Corte Fade]** → también pide **[Barba]** con 70% de confianza y Lift=1.8

        **Aplicación en UrbanBlade:**
        - Identificar qué servicios van juntos
        - Crear paquetes y combos de mayor valor
        - Personalizar recomendaciones al cliente
        """)
    st.stop()


@st.cache_resource
def ejecutar_fpgrowth(soporte, confianza):
    from pyspark.sql.functions import col, collect_set, count, size
    from pyspark.ml.fpm import FPGrowth
    from config.mongo_spark_conexion_sinnulos import get_spark_session

    spark, _, __ = get_spark_session()
    df = spark.read.format("mongodb").load()
    df = df.filter(
        col("cliente_id").isNotNull() &
        col("servicio").isNotNull()   &
        (col("estado") == "completada")
    )

    total_citas  = df.count()
    total_clientes = df.select("cliente_id").distinct().count()

    transacciones = df.groupBy("cliente_id").agg(
        collect_set("servicio").alias("items")
    ).filter(size(col("items")) >= 2)
    total_trans = transacciones.count()

    fp = FPGrowth(itemsCol="items", minSupport=soporte, minConfidence=confianza)
    model = fp.fit(transacciones)

    freq_items = model.freqItemsets.orderBy("freq", ascending=False).toPandas()
    reglas     = model.associationRules.orderBy("confidence", ascending=False).toPandas()

    # Frecuencia de cada servicio individualmente
    serv_freq = df.groupBy("servicio").agg(count("*").alias("freq")).toPandas()
    serv_freq = serv_freq.sort_values("freq", ascending=False)

    spark.stop()
    return freq_items, reglas, serv_freq, total_trans, total_citas, total_clientes


with st.spinner("Ejecutando FP-Growth con PySpark... (30-60 seg)"):
    freq_items, reglas, serv_freq, total_trans, total_citas, total_clientes = \
        ejecutar_fpgrowth(min_sup, min_conf)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Citas Totales",      f"{total_citas:,}")
c2.metric("Clientes Únicos",    f"{total_clientes:,}")
c3.metric("Conjuntos Frecuentes", f"{len(freq_items):,}")
c4.metric("Reglas Generadas",   f"{len(reglas):,}")

# ════════════════════════════════════════════════════════════════
# TAB 1 – REGLAS
# ════════════════════════════════════════════════════════════════
with tab1:

    if reglas.empty:
        st.warning(f"No se generaron reglas con soporte={min_sup} y confianza={min_conf}. "
                   "Reduce los valores en la barra lateral.")
    else:
        reglas["antecedente"] = reglas["antecedent"].apply(
            lambda x: " + ".join(sorted(list(x))))
        reglas["consecuente"] = reglas["consequent"].apply(
            lambda x: " + ".join(sorted(list(x))))
        reglas["nivel"] = reglas["lift"].apply(
            lambda x: "⭐ Fuerte" if x > 1.5 else "✅ Útil" if x > 1.1 else "⚠️ Débil")

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Top 10 Reglas por Confianza")
            fig_conf = px.bar(
                reglas.head(10),
                x="confianza" if "confianza" in reglas.columns else "confidence",
                y="antecedente",
                color="lift",
                color_continuous_scale="Viridis",
                text=reglas.head(10)["confidence"].apply(lambda x: f"{x*100:.1f}%"),
                orientation="h",
                title="Confianza de las reglas (SI → ENTONCES)"
            )
            fig_conf.update_traces(textposition="outside")
            fig_conf.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                                   font_color="#ccc", xaxis_range=[0, 1.15],
                                   coloraxis_showscale=True)
            st.plotly_chart(fig_conf, use_container_width=True)

        with col_b:
            st.subheader("Top 10 Reglas por Lift")
            top_lift = reglas.nlargest(10, "lift")
            fig_lift = px.bar(
                top_lift,
                x="lift",
                y="antecedente",
                color="lift",
                color_continuous_scale="Plasma",
                text=top_lift["lift"].apply(lambda x: f"{x:.2f}"),
                orientation="h",
                title="Lift (>1 = relación real, no aleatoria)"
            )
            fig_lift.add_vline(x=1, line_color="#f87171", line_dash="dash",
                               annotation_text="Lift=1 (aleatorio)")
            fig_lift.update_traces(textposition="outside")
            fig_lift.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                                   font_color="#ccc", coloraxis_showscale=False)
            st.plotly_chart(fig_lift, use_container_width=True)

        st.subheader("Tabla Completa de Reglas")
        tabla = reglas[["antecedente","consecuente","confidence","lift","nivel"]].copy()
        tabla["confidence"] = tabla["confidence"].apply(lambda x: f"{x*100:.1f}%")
        tabla["lift"]       = tabla["lift"].apply(lambda x: f"{x:.3f}")
        tabla.columns       = ["SI (Antecedente)","ENTONCES (Consecuente)",
                                "Confianza","Lift","Nivel"]
        st.dataframe(tabla, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Conjuntos de Servicios Frecuentes")
    if not freq_items.empty:
        freq_items["items_str"] = freq_items["items"].apply(
            lambda x: " + ".join(sorted(list(x))))
        freq_items["soporte"] = (freq_items["freq"] / total_trans * 100).round(1)
        top_freq = freq_items.head(15)
        fig_freq = px.bar(top_freq, x="freq", y="items_str",
                          color="soporte", color_continuous_scale="Viridis",
                          text=top_freq["soporte"].apply(lambda x: f"{x}%"),
                          orientation="h",
                          title="Top 15 Conjuntos de Ítems Más Frecuentes")
        fig_freq.update_traces(textposition="outside")
        fig_freq.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                               font_color="#ccc", coloraxis_showscale=True)
        st.plotly_chart(fig_freq, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 – HEATMAP
# ════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Heatmap de Correlación entre Servicios")

    servicios = sorted(serv_freq["servicio"].tolist())
    matrix_df = pd.DataFrame(0.0, index=servicios, columns=servicios)

    if not reglas.empty:
        for _, row in reglas.iterrows():
            ante = list(row["antecedent"])
            cons = list(row["consequent"])
            if len(ante) == 1 and len(cons) == 1:
                a, c = ante[0], cons[0]
                if a in servicios and c in servicios:
                    matrix_df.loc[a, c] = round(row["confidence"], 3)

    fig_heat = px.imshow(matrix_df,
                         color_continuous_scale="Blues",
                         title="Confianza: fila → columna (ej: 0.70 = 70% de prob)",
                         text_auto=".2f",
                         aspect="auto")
    fig_heat.update_layout(paper_bgcolor="#111", font_color="#ccc",
                           xaxis_tickangle=-30)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.subheader("Popularidad Individual de Servicios")
    fig_pop = px.bar(serv_freq.head(10), x="servicio", y="freq",
                     color="freq", color_continuous_scale="Viridis",
                     text="freq", title="Servicios más contratados")
    fig_pop.update_traces(textposition="outside")
    fig_pop.update_layout(paper_bgcolor="#111", plot_bgcolor="#111",
                          font_color="#ccc", coloraxis_showscale=False)
    st.plotly_chart(fig_pop, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 3 – TEORÍA
# ════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Marco Teórico — FP-Growth")

    conceptos = pd.DataFrame([
        {"Concepto": "Transacción",
         "Definición": "Conjunto de ítems de una compra/visita de cliente",
         "Ejemplo UrbanBlade": "Cliente C0042: {Corte Fade, Barba, Diseño}"},
        {"Concepto": "Ítem",
         "Definición": "Elemento individual dentro de una transacción",
         "Ejemplo UrbanBlade": "Corte Fade, Barba, Tintura, etc."},
        {"Concepto": "Soporte",
         "Definición": "P(A ∪ B) = freq(A,B) / total_transacciones",
         "Ejemplo UrbanBlade": "soporte(Fade,Barba) = 0.18 → aparecen juntos en 18% clientes"},
        {"Concepto": "Confianza",
         "Definición": "P(B | A) = soporte(A,B) / soporte(A)",
         "Ejemplo UrbanBlade": "conf(Fade→Barba) = 0.70 → 70% de quien pide Fade también pide Barba"},
        {"Concepto": "Lift",
         "Definición": "conf(A→B) / soporte(B)  —  >1 indica asociación real",
         "Ejemplo UrbanBlade": "lift=1.8 → Barba es 1.8x más probable si se pidió Fade"},
        {"Concepto": "FP-Tree",
         "Definición": "Estructura de datos comprimida que evita re-escaneados",
         "Ejemplo UrbanBlade": "Procesa 100K citas sin generar candidatos como Apriori"},
        {"Concepto": "Apriori vs FP-Growth",
         "Definición": "Apriori: genera todos los candidatos. FP-Growth: usa árbol, más rápido",
         "Ejemplo UrbanBlade": "En Big Data (100K+ registros) FP-Growth es hasta 10x más rápido"},
    ])
    st.dataframe(conceptos, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Casos de Uso en Negocio")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        **UrbanBlade — Aplicaciones directas:**
        - Crear **paquetes combo**: "Corte + Barba = 15% off"
        - **Recomendación automática** al agendar: "Clientes como tú también piden..."
        - Diseñar el **menú de servicios** priorizando combos frecuentes
        - **Cross-selling** en la caja: ofrecer el servicio complementario
        """)
    with col_b:
        st.markdown("""
        **Industria — Casos conocidos:**
        - Amazon: "Otros clientes también compraron..."
        - Supermercados: colocar cervezas junto a botanas (Lift alto)
        - Netflix: "Porque viste X, te recomendamos Y"
        - Spotify: playlists de descubrimiento semanal
        """)

st.divider()
st.markdown("""<div style="text-align:center;color:#555;font-size:11px;">
🔗 UrbanBlade FP-Growth · PySpark MLlib ·  UTVT IDGS-93 · Prof. Héctor Velázquez Estrada
</div>""", unsafe_allow_html=True)
