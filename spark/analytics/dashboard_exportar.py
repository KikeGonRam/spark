"""
Dashboard – Centro de Exportación | UrbanBlade
Formatos: CSV · JSON · Excel · PDF · Parquet · SQL
Materia: Extracción del Conocimiento en BD ·  UTVT IDGS-93
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

st.set_page_config(
    page_title="UrbanBlade – Exportación",
    page_icon="📤",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0a0a0a; }
[data-testid="stSidebar"]          { background: #111111; }
h1 { color: #d4af37 !important; }
h2, h3 { color: #e8d5a3 !important; }
.stMetric label { color: #888 !important; font-size: 11px !important; }
.stMetric [data-testid="stMetricValue"] { color: #d4af37 !important; font-size: 24px !important; font-weight: 900; }
div[data-testid="stTabs"] button[aria-selected="true"] { color: #d4af37 !important; border-bottom: 2px solid #d4af37; }
.stDownloadButton button {
    background: linear-gradient(135deg, #1a1a1a, #2a2a2a) !important;
    color: #d4af37 !important;
    border: 1px solid #d4af37 !important;
    font-weight: 700 !important;
    width: 100%;
}
.stDownloadButton button:hover { background: #d4af37 !important; color: #000 !important; }
</style>""", unsafe_allow_html=True)

st.markdown("# 📤 UrbanBlade — Centro de Exportación de Datos")
st.markdown("**Extracción del Conocimiento en BD ·  UTVT IDGS-93 · Prof. Héctor Velázquez Estrada**")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.markdown("### ⚙️ Configuración")
max_rows   = st.sidebar.number_input("Máx. filas a exportar", 100, 100000, 5000, step=500)
separador  = st.sidebar.selectbox("Separador CSV", [",", ";", "|", "\t"])
json_orient= st.sidebar.selectbox("Orientación JSON",
                                  ["records", "split", "index", "columns"])
ejecutar   = st.sidebar.button("🚀 Cargar Datos", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("**Formatos disponibles:**")
st.sidebar.markdown("• 📄 CSV\n• 🔵 JSON\n• 📊 Excel (.xlsx)\n• 📑 PDF\n• 🗜️ Parquet\n• 🗄️ SQL")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Datos Raw",
    "📊 Analytics",
    "👥 Clientes RFM",
    "📅 Series de Tiempo",
    "📦 Exportación Masiva",
])

if not ejecutar:
    with tab1:
        st.info("👈 Haz clic en **Cargar Datos** para preparar los datasets.")
        mapa = pd.DataFrame([
            {"Formato": "📄 CSV",      "Extensión": ".csv",     "Uso recomendado": "Excel, Google Sheets, análisis rápido"},
            {"Formato": "🔵 JSON",     "Extensión": ".json",    "Uso recomendado": "APIs, aplicaciones web, MongoDB"},
            {"Formato": "📊 Excel",    "Extensión": ".xlsx",    "Uso recomendado": "Reportes ejecutivos, múltiples hojas"},
            {"Formato": "📑 PDF",      "Extensión": ".pdf",     "Uso recomendado": "Presentaciones, entrega al profesor"},
            {"Formato": "🗜️ Parquet", "Extensión": ".parquet", "Uso recomendado": "Big Data, Spark, almacenamiento eficiente"},
            {"Formato": "🗄️ SQL",     "Extensión": ".sql",     "Uso recomendado": "Migración a MySQL/PostgreSQL"},
        ])
        st.dataframe(mapa, use_container_width=True, hide_index=True)
    st.stop()


# ── Carga de datos ────────────────────────────────────────────
@st.cache_resource
def cargar_datos_exportacion(n_max):
    from pyspark.sql.functions import (col, year, month, hour, dayofweek,
                                       sum as _sum, count, avg, max as _max,
                                       datediff, lit, collect_set, size)
    from pyspark.ml.feature import VectorAssembler, StandardScaler
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.fpm import FPGrowth
    from config.mongo_spark_conexion_sinnulos import get_spark_session

    spark, df_base, _ = get_spark_session()

    # ── Raw data ──────────────────────────────────────────────
    df_full = spark.read.format("mongodb").load()
    df_full = df_full.withColumn(
        "ingreso", col("cantidad").cast("double") * col("precio").cast("double"))

    total = df_full.count()
    pdf_raw = df_full.limit(n_max).toPandas()

    # ── MapReduce / Resumen por servicio ──────────────────────
    resumen_serv = df_full.groupBy("servicio").agg(
        _sum("ingreso").alias("ingreso_total"),
        count("*").alias("num_citas"),
        avg("precio").alias("precio_promedio"),
        avg("ingreso").alias("ticket_promedio")
    ).orderBy("ingreso_total", ascending=False).toPandas()

    # ── Resumen por barbero ───────────────────────────────────
    resumen_barb = df_full.groupBy("barbero").agg(
        _sum("ingreso").alias("ingreso_total"),
        count("*").alias("num_citas"),
        avg("precio").alias("precio_promedio")
    ).orderBy("ingreso_total", ascending=False).toPandas()

    # ── Distribución por estado ───────────────────────────────
    estados = df_full.groupBy("estado").agg(
        count("*").alias("num_citas"),
        _sum("ingreso").alias("ingreso_total")
    ).toPandas()

    # ── KMeans clusters ───────────────────────────────────────
    pdf_km = df_base.withColumn("ingreso", col("cantidad") * col("precio"))
    a_km = VectorAssembler(inputCols=["cantidad","precio","ingreso"],
                           outputCol="features", handleInvalid="skip")
    df_v = a_km.transform(pdf_km.dropna(subset=["cantidad","precio"]))
    km_model = KMeans(k=3, seed=42).fit(df_v)
    df_cls = km_model.transform(df_v)
    pdf_clusters = df_cls.select("servicio","barbero","cantidad","precio","ingreso","prediction") \
                         .limit(n_max).toPandas()
    pdf_clusters.rename(columns={"prediction": "cluster"}, inplace=True)

    # Centroides
    centroids = pd.DataFrame(
        [c.tolist() for c in km_model.clusterCenters()],
        columns=["cantidad_centroide","precio_centroide","ingreso_centroide"]
    )
    centroids.index.name = "cluster"
    centroids = centroids.reset_index()

    # ── Series de tiempo ──────────────────────────────────────
    df_ts = df_full.filter(col("fecha").isNotNull()) \
                   .withColumn("anio", year(col("fecha"))) \
                   .withColumn("mes",  month(col("fecha")))
    mensual = df_ts.groupBy("anio","mes").agg(
        _sum("ingreso").alias("ingreso_total"),
        count("*").alias("num_citas"),
        avg("ingreso").alias("ticket_promedio")
    ).orderBy("anio","mes").toPandas()
    mensual["periodo"] = mensual["anio"].astype(str) + "-" + mensual["mes"].astype(str).str.zfill(2)

    # ── RFM ───────────────────────────────────────────────────
    df_rfm = df_full.filter(col("fecha").isNotNull() & col("cliente_id").isNotNull())
    fecha_ref = df_rfm.agg(_max("fecha")).collect()[0][0]
    df_comp = df_rfm.filter(col("estado") == "completada")

    recency  = df_rfm.groupBy("cliente_id").agg(_max("fecha").alias("ultima")) \
        .withColumn("recency", datediff(lit(fecha_ref.strftime("%Y-%m-%d")).cast("date"),
                                        col("ultima").cast("date")))
    frequency = df_comp.groupBy("cliente_id").agg(count("*").alias("frequency"))
    monetary  = df_comp.groupBy("cliente_id").agg(_sum("ingreso").alias("monetary"))

    rfm = recency.join(frequency,"cliente_id","left") \
                 .join(monetary, "cliente_id","left") \
                 .fillna({"frequency":0,"monetary":0.0}) \
                 .filter(col("frequency") > 0)

    rfm_clean = rfm.dropna(subset=["recency","frequency","monetary"])
    asm2 = VectorAssembler(inputCols=["recency","frequency","monetary"],
                           outputCol="features_raw", handleInvalid="skip")
    rfm_v = asm2.transform(rfm_clean)
    sc2   = StandardScaler(inputCol="features_raw", outputCol="features",
                           withMean=True, withStd=True)
    rfm_sc = sc2.fit(rfm_v).transform(rfm_v)
    km2    = KMeans(k=4, seed=42, featuresCol="features", predictionCol="segmento")
    rfm_seg = km2.fit(rfm_sc).transform(rfm_sc)
    pdf_rfm = rfm_seg.select("cliente_id","recency","frequency","monetary","segmento").toPandas()

    # ── FP-Growth reglas ──────────────────────────────────────
    trans = df_comp.filter(col("cliente_id").isNotNull() & col("servicio").isNotNull()) \
                   .groupBy("cliente_id").agg(collect_set("servicio").alias("items")) \
                   .filter(size(col("items")) >= 2)
    fp_model = FPGrowth(itemsCol="items", minSupport=0.05, minConfidence=0.3).fit(trans)
    reglas   = fp_model.associationRules.toPandas()
    if not reglas.empty:
        reglas["antecedente"] = reglas["antecedent"].apply(lambda x: " + ".join(sorted(list(x))))
        reglas["consecuente"] = reglas["consequent"].apply(lambda x: " + ".join(sorted(list(x))))
        reglas = reglas[["antecedente","consecuente","confidence","lift"]].copy()
        reglas["confidence"] = reglas["confidence"].round(4)
        reglas["lift"]       = reglas["lift"].round(4)

    spark.stop()

    kpis = {
        "Total Registros":    f"{total:,}",
        "Ingreso Total":      f"${resumen_serv['ingreso_total'].sum():,.0f}",
        "Ticket Promedio":    f"${resumen_serv['ticket_promedio'].mean():,.0f}",
        "Servicio Estrella":  resumen_serv.iloc[0]["servicio"],
        "Barbero Top":        resumen_barb.iloc[0]["barbero"],
        "Meses de historial": str(len(mensual)),
        "Clientes únicos":    f"{len(pdf_rfm):,}",
        "Reglas asociación":  f"{len(reglas):,}",
    }

    return {
        "raw":          pdf_raw,
        "serv":         resumen_serv,
        "barb":         resumen_barb,
        "estados":      estados,
        "clusters":     pdf_clusters,
        "centroids":    centroids,
        "mensual":      mensual,
        "rfm":          pdf_rfm,
        "reglas":       reglas,
        "kpis":         kpis,
        "total":        total,
        "fecha_ref":    fecha_ref.strftime("%Y-%m-%d"),
    }


with st.spinner("Cargando todos los datasets con PySpark..."):
    D = cargar_datos_exportacion(int(max_rows))

# Importar funciones de exportación
from utils.exportar import a_csv, a_json, a_excel, a_pdf, a_parquet, a_sql

ts = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M")

# ── KPIs globales ─────────────────────────────────────────────
kpis = D["kpis"]
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Registros",   kpis["Total Registros"])
c2.metric("Ingreso Total",      kpis["Ingreso Total"])
c3.metric("Clientes Únicos",   kpis["Clientes únicos"])
c4.metric("Meses Historial",   kpis["Meses de historial"])

# ════════════════════════════════════════════════════════════════
# TAB 1 – DATOS RAW
# ════════════════════════════════════════════════════════════════
with tab1:
    st.subheader(f"Datos Raw — {len(D['raw']):,} registros (primeros {max_rows:,})")
    st.dataframe(D["raw"].head(100), use_container_width=True, hide_index=True)
    st.caption(f"Vista previa: 100 de {len(D['raw']):,} filas. Los archivos descargados incluyen todas las filas.")

    st.divider()
    st.subheader("⬇️ Descargar Datos Raw")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.download_button(
            "📄 CSV",
            data    = a_csv(D["raw"], separador),
            file_name = f"urbanblade_raw_{ts}.csv",
            mime    = "text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "🔵 JSON",
            data    = a_json(D["raw"], json_orient),
            file_name = f"urbanblade_raw_{ts}.json",
            mime    = "application/json",
            use_container_width=True,
        )
    with c3:
        st.download_button(
            "📊 Excel",
            data    = a_excel({"Datos Raw": D["raw"]}, kpis),
            file_name = f"urbanblade_raw_{ts}.xlsx",
            mime    = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with c4:
        st.download_button(
            "🗜️ Parquet",
            data    = a_parquet(D["raw"]),
            file_name = f"urbanblade_raw_{ts}.parquet",
            mime    = "application/octet-stream",
            use_container_width=True,
        )
    with c5:
        st.download_button(
            "🗄️ SQL",
            data    = a_sql(D["raw"], "appointments"),
            file_name = f"urbanblade_raw_{ts}.sql",
            mime    = "text/plain",
            use_container_width=True,
        )
    with c6:
        pdf_raw_bytes = a_pdf(
            "Reporte de Datos Raw – UrbanBlade",
            [{"titulo": "KPIs Ejecutivos", "kpis": kpis},
             {"titulo": "Muestra de Datos",
              "texto": f"Los primeros {min(30, len(D['raw']))} registros del dataset.",
              "df":    D["raw"].head(30)}]
        )
        st.download_button(
            "📑 PDF",
            data    = pdf_raw_bytes,
            file_name = f"urbanblade_raw_{ts}.pdf",
            mime    = "application/pdf",
            use_container_width=True,
        )


# ════════════════════════════════════════════════════════════════
# TAB 2 – ANALYTICS (MapReduce + Clusters)
# ════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Resultados de Analytics (MapReduce + KMeans)")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Ingresos por Servicio**")
        st.dataframe(D["serv"], use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("**Ingresos por Barbero**")
        st.dataframe(D["barb"], use_container_width=True, hide_index=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**Distribución por Estado**")
        st.dataframe(D["estados"], use_container_width=True, hide_index=True)
    with col_d:
        st.markdown("**Centroides KMeans (K=3)**")
        st.dataframe(D["centroids"], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("⬇️ Descargar Analytics")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    hojas_analytics = {
        "Ingresos por Servicio": D["serv"],
        "Ingresos por Barbero":  D["barb"],
        "Estados de Citas":      D["estados"],
        "Clusters KMeans":       D["clusters"].head(5000),
        "Centroides":            D["centroids"],
    }

    with c1:
        st.download_button("📄 CSV – Servicios",
            data=a_csv(D["serv"], separador),
            file_name=f"analytics_servicios_{ts}.csv", mime="text/csv",
            use_container_width=True)
    with c2:
        st.download_button("🔵 JSON – Barberos",
            data=a_json(D["barb"]),
            file_name=f"analytics_barberos_{ts}.json", mime="application/json",
            use_container_width=True)
    with c3:
        st.download_button("📊 Excel – Completo",
            data=a_excel(hojas_analytics, kpis),
            file_name=f"urbanblade_analytics_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with c4:
        st.download_button("🗜️ Parquet – Clusters",
            data=a_parquet(D["clusters"]),
            file_name=f"clusters_{ts}.parquet", mime="application/octet-stream",
            use_container_width=True)
    with c5:
        st.download_button("🗄️ SQL – Servicios",
            data=a_sql(D["serv"], "resumen_servicios"),
            file_name=f"servicios_{ts}.sql", mime="text/plain",
            use_container_width=True)
    with c6:
        pdf_analytics = a_pdf(
            "Reporte Analytics – UrbanBlade",
            [{"titulo": "KPIs Ejecutivos",        "kpis": kpis},
             {"titulo": "Ingresos por Servicio",  "df": D["serv"]},
             {"titulo": "Ingresos por Barbero",   "df": D["barb"]},
             {"titulo": "Centroides KMeans",       "df": D["centroids"]}]
        )
        st.download_button("📑 PDF – Analytics",
            data=pdf_analytics,
            file_name=f"analytics_{ts}.pdf", mime="application/pdf",
            use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 3 – CLIENTES RFM
# ════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Segmentación RFM de Clientes")
    st.dataframe(D["rfm"].head(100), use_container_width=True, hide_index=True)

    perfil_rfm = D["rfm"].groupby("segmento").agg(
        clientes   =("cliente_id","count"),
        recency_avg=("recency","mean"),
        freq_avg   =("frequency","mean"),
        monetary_avg=("monetary","mean")
    ).reset_index().round(2)

    st.markdown("**Perfil por Segmento**")
    st.dataframe(perfil_rfm, use_container_width=True, hide_index=True)

    if not D["reglas"].empty:
        st.markdown("**Reglas de Asociación (FP-Growth)**")
        st.dataframe(D["reglas"].head(20), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("⬇️ Descargar Datos de Clientes")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    hojas_clientes = {
        "Segmentos RFM":        D["rfm"],
        "Perfil por Segmento":  perfil_rfm,
        "Reglas Asociación":    D["reglas"] if not D["reglas"].empty else pd.DataFrame({"info":["Sin reglas"]}),
    }

    with c1:
        st.download_button("📄 CSV – RFM",
            data=a_csv(D["rfm"], separador),
            file_name=f"rfm_clientes_{ts}.csv", mime="text/csv",
            use_container_width=True)
    with c2:
        st.download_button("🔵 JSON – RFM",
            data=a_json(D["rfm"]),
            file_name=f"rfm_{ts}.json", mime="application/json",
            use_container_width=True)
    with c3:
        st.download_button("📊 Excel – Clientes",
            data=a_excel(hojas_clientes, kpis),
            file_name=f"clientes_rfm_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with c4:
        st.download_button("🗜️ Parquet – RFM",
            data=a_parquet(D["rfm"]),
            file_name=f"rfm_{ts}.parquet", mime="application/octet-stream",
            use_container_width=True)
    with c5:
        st.download_button("🗄️ SQL – Clientes",
            data=a_sql(D["rfm"], "clientes_rfm"),
            file_name=f"rfm_{ts}.sql", mime="text/plain",
            use_container_width=True)
    with c6:
        pdf_rfm_b = a_pdf(
            "Análisis RFM de Clientes – UrbanBlade",
            [{"titulo": "KPIs Globales",       "kpis": kpis},
             {"titulo": "Perfil por Segmento", "df": perfil_rfm},
             {"titulo": "Reglas de Asociación","df": D["reglas"].head(20) if not D["reglas"].empty else pd.DataFrame({"info":["Sin reglas"]})}]
        )
        st.download_button("📑 PDF – Clientes",
            data=pdf_rfm_b,
            file_name=f"clientes_{ts}.pdf", mime="application/pdf",
            use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 – SERIES DE TIEMPO
# ════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Series de Tiempo — Datos Mensuales")
    st.dataframe(D["mensual"], use_container_width=True, hide_index=True)

    # Predicción simple con sklearn
    import numpy as np
    from sklearn.linear_model import LinearRegression as LR
    X_t = np.array(range(len(D["mensual"]))).reshape(-1,1)
    y_t = D["mensual"]["ingreso_total"].values
    lr  = LR().fit(X_t, y_t)
    n   = len(D["mensual"])
    pred_vals = [lr.predict([[n+i]])[0] for i in range(3)]
    ultimo = D["mensual"].iloc[-1]
    ultimo_mes, ultimo_anio = int(ultimo["mes"]), int(ultimo["anio"])
    pred_labs = []
    for i in range(1, 4):
        m = ultimo_mes + i
        a = ultimo_anio + (m-1)//12
        m = ((m-1) % 12) + 1
        pred_labs.append(f"{a}-{m:02d}")

    df_pred = pd.DataFrame({
        "Período":           pred_labs,
        "Predicción ($)":    [round(v) for v in pred_vals],
        "Cambio vs último":  [f"{(v-y_t[-1])/y_t[-1]*100:+.1f}%" for v in pred_vals],
        "R² modelo":         [round(lr.score(X_t,y_t),4)]*3
    })
    st.markdown("**Predicción próximos 3 meses**")
    st.dataframe(df_pred, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("⬇️ Descargar Series de Tiempo")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    hojas_ts = {
        "Tendencia Mensual":   D["mensual"],
        "Predicción 3 Meses":  df_pred,
    }

    with c1:
        st.download_button("📄 CSV",
            data=a_csv(D["mensual"], separador),
            file_name=f"series_tiempo_{ts}.csv", mime="text/csv",
            use_container_width=True)
    with c2:
        st.download_button("🔵 JSON",
            data=a_json(D["mensual"]),
            file_name=f"series_{ts}.json", mime="application/json",
            use_container_width=True)
    with c3:
        st.download_button("📊 Excel",
            data=a_excel(hojas_ts, kpis),
            file_name=f"series_tiempo_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    with c4:
        st.download_button("🗜️ Parquet",
            data=a_parquet(D["mensual"]),
            file_name=f"series_{ts}.parquet", mime="application/octet-stream",
            use_container_width=True)
    with c5:
        st.download_button("🗄️ SQL",
            data=a_sql(D["mensual"], "series_tiempo"),
            file_name=f"series_{ts}.sql", mime="text/plain",
            use_container_width=True)
    with c6:
        pdf_ts = a_pdf(
            "Análisis de Series de Tiempo – UrbanBlade",
            [{"titulo": "KPIs Globales",           "kpis": kpis},
             {"titulo": "Tendencia Mensual",        "df": D["mensual"]},
             {"titulo": "Predicción Próximos Meses","df": df_pred}]
        )
        st.download_button("📑 PDF",
            data=pdf_ts,
            file_name=f"series_{ts}.pdf", mime="application/pdf",
            use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 5 – EXPORTACIÓN MASIVA
# ════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("📦 Reporte Ejecutivo Completo — Un solo archivo con todo")

    st.markdown("""
    Descarga **un solo archivo** que contiene todos los análisis del proyecto
    en el formato que prefieras.
    """)

    # Excel maestro (todas las hojas)
    hojas_master = {
        "📊 KPIs":               pd.DataFrame(list(kpis.items()), columns=["Indicador","Valor"]),
        "Ingresos x Servicio":   D["serv"],
        "Ingresos x Barbero":    D["barb"],
        "Estados Citas":         D["estados"],
        "KMeans Clusters":       D["clusters"].head(5000),
        "Centroides":            D["centroids"],
        "Series de Tiempo":      D["mensual"],
        "RFM Clientes":          D["rfm"],
        "Reglas Asociacion":     D["reglas"] if not D["reglas"].empty else pd.DataFrame({"info":["Sin reglas"]}),
        "Datos Raw (muestra)":   D["raw"].head(1000),
    }

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 📊 Excel Maestro (10 hojas)")
        st.markdown("Contiene: KPIs, Servicios, Barberos, Clusters, Series, RFM, Reglas, Datos")
        st.download_button(
            "📊 Descargar Excel Completo",
            data      = a_excel(hojas_master, kpis),
            file_name = f"urbanblade_COMPLETO_{ts}.xlsx",
            mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with c2:
        st.markdown("### 📑 PDF Ejecutivo Completo")
        st.markdown("Reporte profesional con KPIs, tablas de resultados y análisis de cada módulo")
        pdf_maestro = a_pdf(
            "Reporte Ejecutivo Completo – UrbanBlade Big Data",
            [
                {"titulo": "Resumen Ejecutivo",
                 "texto":  f"Análisis de {kpis['Total Registros']} citas de la barbería UrbanBlade. "
                           f"Dataset de 18 meses ({D['fecha_ref']}). "
                           f"Pipeline: MongoDB → PySpark → ML → Dashboard.",
                 "kpis":   kpis},
                {"titulo": "Ingresos por Servicio (MapReduce)",
                 "texto":  "Agregación distribuida usando Apache Spark. "
                           "Servicio estrella: " + kpis["Servicio Estrella"],
                 "df":     D["serv"]},
                {"titulo": "Ingresos por Barbero",
                 "df":     D["barb"]},
                {"titulo": "Distribución por Estado de Cita",
                 "df":     D["estados"]},
                {"titulo": "Segmentación KMeans — Centroides (K=3)",
                 "texto":  "KMeans agrupa las citas en 3 segmentos según cantidad, precio e ingreso.",
                 "df":     D["centroids"]},
                {"titulo": "Series de Tiempo — Tendencia Mensual",
                 "texto":  f"Historial de {kpis['Meses de historial']} meses. "
                           "Tendencia positiva proyectada para los próximos 3 meses.",
                 "df":     D["mensual"]},
                {"titulo": "Análisis RFM de Clientes",
                 "texto":  f"{kpis['Clientes únicos']} clientes segmentados en VIP, Leal, En Riesgo e Inactivo.",
                 "df":     D["rfm"].groupby("segmento").agg(
                               clientes=("cliente_id","count"),
                               recency_avg=("recency","mean"),
                               monetary_avg=("monetary","mean")).reset_index().round(2)},
                {"titulo": "Reglas de Asociación FP-Growth",
                 "texto":  f"{kpis['Reglas asociación']} reglas encontradas. "
                           "Soporte mínimo: 5% | Confianza mínima: 30%",
                 "df":     D["reglas"].head(15) if not D["reglas"].empty else pd.DataFrame({"info":["Sin reglas con estos parámetros"]})},
            ]
        )
        st.download_button(
            "📑 Descargar PDF Completo",
            data      = pdf_maestro,
            file_name = f"urbanblade_REPORTE_{ts}.pdf",
            mime      = "application/pdf",
            use_container_width=True,
        )

    st.divider()
    st.subheader("Exportación individual por formato")
    c1, c2, c3, c4 = st.columns(4)
    df_all = pd.concat([D["serv"].assign(tipo="servicio"), D["barb"].assign(tipo="barbero")],
                       ignore_index=True)
    with c1:
        st.download_button("📄 CSV – Todo",
            data=a_csv(D["raw"], separador),
            file_name=f"urbanblade_all_{ts}.csv", mime="text/csv",
            use_container_width=True)
    with c2:
        st.download_button("🔵 JSON – Todo",
            data=a_json(D["raw"]),
            file_name=f"urbanblade_all_{ts}.json", mime="application/json",
            use_container_width=True)
    with c3:
        st.download_button("🗜️ Parquet – Todo",
            data=a_parquet(D["raw"]),
            file_name=f"urbanblade_all_{ts}.parquet", mime="application/octet-stream",
            use_container_width=True)
    with c4:
        st.download_button("🗄️ SQL – Todo",
            data=a_sql(D["raw"], "appointments"),
            file_name=f"urbanblade_all_{ts}.sql", mime="text/plain",
            use_container_width=True)

st.divider()
st.markdown("""<div style="text-align:center;color:#555;font-size:11px;">
📤 UrbanBlade Export Center · CSV · JSON · Excel · PDF · Parquet · SQL ·  UTVT IDGS-93
</div>""", unsafe_allow_html=True)
