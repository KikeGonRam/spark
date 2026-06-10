"""
Dashboard: Segmentación de Clientes Premium — UrbanBlade
Ejecutar: streamlit run analytics/dashboard_segmentacion_clientes.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus
from datetime import date, datetime
from pathlib import Path
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

mongo_uri = (f"mongodb+srv://{os.getenv('MONGO_USER')}:"
             f"{quote_plus(os.getenv('MONGO_PASSWORD'))}@"
             f"{os.getenv('MONGO_CLUSTER')}")
db_name = os.getenv("MONGO_DB")

st.set_page_config(
    page_title="UrbanBlade — Segmentación de Clientes",
    page_icon="✂️",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_data():
    mc = MongoClient(mongo_uri)
    db = mc[db_name]
    users_map    = {str(u["_id"]): u for u in db["users"].find({}, {"_id":1,"name":1,"email":1})}
    services_map = {str(s["_id"]): s for s in db["services"].find({}, {"_id":1,"precio":1})}
    raw_apts     = list(db["appointments"].find({}, {
        "_id":0,"client_id":1,"service_id":1,"precio_cobrado":1,"estado":1,"fecha":1
    }))
    mc.close()

    today = date.today()
    rows  = []
    for apt in raw_apts:
        cid = str(apt.get("client_id", ""))
        if not cid or cid in ("None", ""):
            continue
        svc   = services_map.get(str(apt.get("service_id", "")), {})
        pc    = apt.get("precio_cobrado")
        precio = float(pc) if pc is not None else float(svc.get("precio") or 0)
        fecha_str = str(apt.get("fecha", ""))[:10]
        try:
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()
            dias = (today - fecha_dt).days
        except Exception:
            dias = 0
        rows.append({
            "client_id": cid,
            "nombre":    users_map.get(cid, {}).get("name", "Cliente"),
            "email":     users_map.get(cid, {}).get("email", ""),
            "precio":    precio,
            "estado":    str(apt.get("estado", "")),
            "dias_desde_cita": dias,
        })
    return pd.DataFrame(rows)

def segment_clients(df):
    g = df.groupby(["client_id", "nombre", "email"]).agg(
        total_citas     = ("precio", "count"),
        total_gasto     = ("precio", "sum"),
        promedio_gasto  = ("precio", "mean"),
        tasa_cancelacion= ("estado", lambda x: (x == "cancelada").mean() * 100),
        dias_inactivo   = ("dias_desde_cita", "max"),
    ).reset_index()
    g["total_gasto"]    = g["total_gasto"].round(2)
    g["promedio_gasto"] = g["promedio_gasto"].round(2)
    g["tasa_cancelacion"] = g["tasa_cancelacion"].round(1)

    # Segmentar con reglas de negocio + puntuación
    def asignar_segmento(row):
        if row["total_gasto"] >= g["total_gasto"].quantile(0.75) and row["tasa_cancelacion"] < 20:
            return "VIP"
        elif row["promedio_gasto"] >= g["promedio_gasto"].quantile(0.60):
            return "Alto consumo"
        elif row["dias_inactivo"] >= g["dias_inactivo"].quantile(0.65):
            return "Inactivo"
        else:
            return "Frecuente"

    g["segmento"] = g.apply(asignar_segmento, axis=1)
    return g

# ── CARGA ──────────────────────────────────────────────────────────────────────
df_citas = load_data()
if df_citas.empty:
    st.error("No hay datos. Verifica la conexión a MongoDB.")
    st.stop()

df = segment_clients(df_citas)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title("✂️ UrbanBlade — Segmentación de Clientes Premium")
st.markdown("Sistema de inteligencia para identificar el perfil de cada cliente y personalizar la experiencia.")
st.divider()

# ── KPIs ───────────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
total_cl = len(df)
with col1:
    st.metric("Total clientes", total_cl)
with col2:
    vip = len(df[df["segmento"] == "VIP"])
    st.metric("VIP", vip, help="Alto gasto + baja cancelación")
with col3:
    alto = len(df[df["segmento"] == "Alto consumo"])
    st.metric("Alto consumo", alto)
with col4:
    frec = len(df[df["segmento"] == "Frecuente"])
    st.metric("Frecuentes", frec)
with col5:
    inac = len(df[df["segmento"] == "Inactivo"])
    st.metric("Inactivos", inac, help="Requieren campaña de reactivación")

st.divider()

# ── GRÁFICAS ───────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

COLORES = {
    "VIP":          "#FFD700",
    "Alto consumo": "#FF6B35",
    "Frecuente":    "#4CAF50",
    "Inactivo":     "#9E9E9E",
}

with col_left:
    st.subheader("Distribución de segmentos")
    dist = df["segmento"].value_counts().reset_index()
    dist.columns = ["segmento", "clientes"]
    fig_pie = px.pie(
        dist, values="clientes", names="segmento",
        color="segmento", color_discrete_map=COLORES,
        hole=0.4,
    )
    fig_pie.update_traces(textposition="outside", textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("Gasto total por segmento")
    gasto_seg = df.groupby("segmento")["total_gasto"].mean().reset_index()
    gasto_seg.columns = ["segmento", "gasto_promedio"]
    fig_bar = px.bar(
        gasto_seg.sort_values("gasto_promedio", ascending=False),
        x="segmento", y="gasto_promedio",
        color="segmento", color_discrete_map=COLORES,
        text_auto=".0f",
        labels={"gasto_promedio": "Gasto promedio ($)", "segmento": "Segmento"},
    )
    fig_bar.update_traces(texttemplate="$%{text}", textposition="outside")
    st.plotly_chart(fig_bar, use_container_width=True)

# ── SCATTER ────────────────────────────────────────────────────────────────────
st.subheader("Mapa de clientes: Gasto total vs Frecuencia de visitas")
fig_scatter = px.scatter(
    df, x="total_citas", y="total_gasto",
    color="segmento", color_discrete_map=COLORES,
    size="promedio_gasto", hover_name="nombre",
    hover_data={"tasa_cancelacion": ":.1f", "dias_inactivo": True},
    labels={
        "total_citas": "Total de citas",
        "total_gasto": "Gasto total ($)",
        "segmento": "Segmento",
    },
    size_max=30,
)
fig_scatter.update_layout(height=450)
st.plotly_chart(fig_scatter, use_container_width=True)

# ── TABLA POR SEGMENTO ─────────────────────────────────────────────────────────
st.divider()
st.subheader("Detalle por segmento")

segmento_sel = st.selectbox(
    "Filtrar por segmento:",
    ["Todos"] + sorted(df["segmento"].unique().tolist())
)

df_show = df if segmento_sel == "Todos" else df[df["segmento"] == segmento_sel]
df_show = df_show.sort_values("total_gasto", ascending=False)

st.dataframe(
    df_show[["nombre", "email", "total_citas", "total_gasto",
             "promedio_gasto", "tasa_cancelacion", "dias_inactivo", "segmento"]]
    .rename(columns={
        "nombre": "Cliente", "email": "Email",
        "total_citas": "Citas", "total_gasto": "Gasto total ($)",
        "promedio_gasto": "Ticket prom ($)",
        "tasa_cancelacion": "Cancelaciones (%)",
        "dias_inactivo": "Días sin visita",
        "segmento": "Segmento",
    })
    .reset_index(drop=True),
    use_container_width=True,
    height=400,
)

# ── ACCIONES DE MARKETING ──────────────────────────────────────────────────────
st.divider()
st.subheader("Acciones recomendadas por segmento")
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.markdown("### 🥇 VIP")
    st.success("Tarjeta premium\nDescuento 15%\nCita preferente\nAcceso anticipado a nuevos servicios")
with col_b:
    st.markdown("### 🔥 Alto consumo")
    st.warning("Membresía mensual\nPaquete todo incluido\nProductos exclusivos")
with col_c:
    st.markdown("### ⭐ Frecuente")
    st.info("Programa de puntos\nCita #10 gratis\nReferido: $50 de descuento")
with col_d:
    st.markdown("### 💤 Inactivo")
    st.error("WhatsApp: 'Te extrañamos'\nOferta reactivación 20%\nRecordatorio automático")
