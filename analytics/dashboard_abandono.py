"""
Dashboard: Predicción de Abandono de Clientes — UrbanBlade
Ejecutar: streamlit run analytics/dashboard_abandono.py
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
    page_title="UrbanBlade — Predicción de Abandono",
    page_icon="🚨",
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
            "fecha":     fecha_str,
        })
    return pd.DataFrame(rows)

def compute_churn(df_raw):
    g = df_raw.groupby(["client_id", "nombre", "email"]).agg(
        total_citas       = ("precio", "count"),
        gasto_promedio    = ("precio", "mean"),
        gasto_total       = ("precio", "sum"),
        tasa_cancelacion  = ("estado", lambda x: (x == "cancelada").mean() * 100),
        dias_sin_cita     = ("dias_desde_cita", "max"),
        primera_cita_dias = ("dias_desde_cita", "min"),
    ).reset_index()

    g["gasto_promedio"]   = g["gasto_promedio"].round(2)
    g["gasto_total"]      = g["gasto_total"].round(2)
    g["tasa_cancelacion"] = g["tasa_cancelacion"].round(1)

    meses = (g["dias_sin_cita"] - g["primera_cita_dias"]) / 30
    g["frecuencia_mensual"] = (g["total_citas"] / meses.clip(lower=1)).round(2)

    umbral_dias   = g["dias_sin_cita"].quantile(0.60)
    umbral_cancel = 30.0

    g["en_riesgo"] = (
        (g["dias_sin_cita"] > umbral_dias) |
        (g["tasa_cancelacion"] > umbral_cancel)
    ).astype(int)

    # Score de riesgo 0-100
    max_dias = g["dias_sin_cita"].max() or 1
    g["score_riesgo"] = (
        (g["dias_sin_cita"] / max_dias) * 60 +
        (g["tasa_cancelacion"] / 100) * 40
    ).clip(0, 100).round(1)

    return g, umbral_dias, umbral_cancel

# ── CARGA ──────────────────────────────────────────────────────────────────────
df_citas = load_data()
if df_citas.empty:
    st.error("No hay datos. Verifica la conexión a MongoDB.")
    st.stop()

df, umbral_dias, umbral_cancel = compute_churn(df_citas)

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title("🚨 UrbanBlade — Predicción de Abandono de Clientes")
st.markdown("Detecta clientes que podrían dejar de asistir antes de que suceda.")

col1, col2, col3, col4 = st.columns(4)
en_riesgo  = df[df["en_riesgo"] == 1]
sin_riesgo = df[df["en_riesgo"] == 0]

with col1:
    st.metric("Total clientes", len(df))
with col2:
    st.metric("⚠️ En riesgo", len(en_riesgo),
              delta=f"{len(en_riesgo)/len(df)*100:.0f}% del total",
              delta_color="inverse")
with col3:
    st.metric("✅ Estables", len(sin_riesgo))
with col4:
    ingresos_riesgo = en_riesgo["gasto_total"].sum()
    st.metric("Ingresos en riesgo", f"${ingresos_riesgo:,.0f}",
              help="Gasto total de clientes en riesgo")

st.divider()

# ── PARÁMETROS ─────────────────────────────────────────────────────────────────
with st.expander("⚙️ Ajustar umbrales de riesgo"):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        umbral_d = st.slider("Días sin cita → EN RIESGO si >",
                              min_value=5, max_value=60,
                              value=int(umbral_dias), step=1)
    with col_p2:
        umbral_c = st.slider("Tasa de cancelación → EN RIESGO si >",
                              min_value=10, max_value=80,
                              value=int(umbral_cancel), step=5)

    df["en_riesgo"] = (
        (df["dias_sin_cita"] > umbral_d) |
        (df["tasa_cancelacion"] > umbral_c)
    ).astype(int)
    en_riesgo  = df[df["en_riesgo"] == 1]
    sin_riesgo = df[df["en_riesgo"] == 0]

# ── GRÁFICAS ───────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("Score de riesgo por cliente")
    df_sorted = df.sort_values("score_riesgo", ascending=True)
    colors     = ["#E53935" if r else "#43A047" for r in df_sorted["en_riesgo"]]
    fig = go.Figure(go.Bar(
        x=df_sorted["score_riesgo"],
        y=df_sorted["nombre"],
        orientation="h",
        marker_color=colors,
        text=df_sorted["score_riesgo"].apply(lambda x: f"{x:.0f}"),
        textposition="outside",
    ))
    fig.update_layout(
        xaxis_title="Score de riesgo (0–100)",
        yaxis_title="",
        height=500,
        xaxis=dict(range=[0, 110]),
    )
    fig.add_vline(x=umbral_d / df["dias_sin_cita"].max() * 100,
                  line_dash="dash", line_color="orange",
                  annotation_text="Umbral")
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.subheader("Días inactivo vs Tasa de cancelación")
    fig2 = px.scatter(
        df, x="dias_sin_cita", y="tasa_cancelacion",
        color=df["en_riesgo"].map({1: "En riesgo", 0: "Estable"}),
        color_discrete_map={"En riesgo": "#E53935", "Estable": "#43A047"},
        size="gasto_total", hover_name="nombre",
        labels={
            "dias_sin_cita": "Días sin cita",
            "tasa_cancelacion": "Tasa cancelación (%)",
            "color": "Estado",
        },
        size_max=25,
    )
    fig2.add_vline(x=umbral_d, line_dash="dash", line_color="orange",
                   annotation_text=f">{umbral_d} días")
    fig2.add_hline(y=umbral_c, line_dash="dash", line_color="red",
                   annotation_text=f">{umbral_c}% cancel.")
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, use_container_width=True)

# ── TABLA DE CLIENTES EN RIESGO ────────────────────────────────────────────────
st.divider()
st.subheader("🚨 Clientes en riesgo — Lista de acción")

if len(en_riesgo) > 0:
    df_risk_show = en_riesgo.sort_values("score_riesgo", ascending=False)[[
        "nombre", "email", "total_citas", "gasto_total",
        "tasa_cancelacion", "dias_sin_cita", "frecuencia_mensual", "score_riesgo"
    ]].rename(columns={
        "nombre": "Cliente", "email": "Email",
        "total_citas": "Citas", "gasto_total": "Gasto total ($)",
        "tasa_cancelacion": "Cancelaciones (%)",
        "dias_sin_cita": "Días sin cita",
        "frecuencia_mensual": "Freq/mes",
        "score_riesgo": "Score riesgo",
    })

    def color_risk(val):
        if val >= 70:
            return "background-color: #ffcccc"
        elif val >= 40:
            return "background-color: #fff3cc"
        return ""

    st.dataframe(
        df_risk_show.style.applymap(color_risk, subset=["Score riesgo"]),
        use_container_width=True,
    )

    col_act1, col_act2, col_act3 = st.columns(3)
    with col_act1:
        high = df_risk_show[df_risk_show["Score riesgo"] >= 70]
        st.error(f"🔴 URGENTE: {len(high)} cliente(s)\nLlamar hoy + oferta especial")
    with col_act2:
        med = df_risk_show[(df_risk_show["Score riesgo"] >= 40) & (df_risk_show["Score riesgo"] < 70)]
        st.warning(f"🟡 ATENCIÓN: {len(med)} cliente(s)\nWhatsApp + descuento 15%")
    with col_act3:
        low = df_risk_show[df_risk_show["Score riesgo"] < 40]
        st.info(f"🟢 PREVENTIVO: {len(low)} cliente(s)\nNewsletter + recordatorio")
else:
    st.success("¡Ningún cliente en riesgo con los umbrales actuales!")

# ── CLIENTES ESTABLES ──────────────────────────────────────────────────────────
st.divider()
with st.expander("✅ Ver clientes estables"):
    st.dataframe(
        sin_riesgo.sort_values("gasto_total", ascending=False)[[
            "nombre", "total_citas", "gasto_total", "tasa_cancelacion", "dias_sin_cita"
        ]].rename(columns={
            "nombre": "Cliente",
            "total_citas": "Citas",
            "gasto_total": "Gasto total ($)",
            "tasa_cancelacion": "Cancelaciones (%)",
            "dias_sin_cita": "Días sin cita",
        }).reset_index(drop=True),
        use_container_width=True,
    )
