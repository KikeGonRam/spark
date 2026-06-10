"""
Dashboard: Predicción de Demanda y Análisis de Horarios — UrbanBlade
Ejecutar: streamlit run analytics/dashboard_demanda.py
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

DIAS = {1:"Lunes",2:"Martes",3:"Miércoles",4:"Jueves",
        5:"Viernes",6:"Sábado",7:"Domingo"}
MESES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
         7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

st.set_page_config(
    page_title="UrbanBlade — Predicción de Demanda",
    page_icon="📊",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_data():
    mc = MongoClient(mongo_uri)
    db = mc[db_name]
    services_map = {str(s["_id"]): s for s in db["services"].find(
        {}, {"_id":1,"precio":1,"nombre":1})}
    barbers_map  = {str(b["_id"]): b for b in db["barbers"].find(
        {}, {"_id":1,"user_id":1,"nombre":1})}
    users_map    = {str(u["_id"]): u for u in db["users"].find(
        {}, {"_id":1,"name":1})}
    raw_apts = list(db["appointments"].find({}, {
        "_id":0,"service_id":1,"barber_id":1,"precio_cobrado":1,
        "estado":1,"fecha":1,"hora_inicio":1
    }))
    mc.close()

    rows = []
    for apt in raw_apts:
        svc  = services_map.get(str(apt.get("service_id","")), {})
        brb  = barbers_map.get(str(apt.get("barber_id","")), {})
        uid  = str(brb.get("user_id",""))
        barbero = brb.get("nombre") or users_map.get(uid,{}).get("name","Sin nombre")
        pc   = apt.get("precio_cobrado")
        precio = float(pc) if pc is not None else float(svc.get("precio") or 0)
        fecha_str = str(apt.get("fecha",""))[:10]
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        except Exception:
            continue
        try:
            hora = int(str(apt.get("hora_inicio","09"))[:2])
        except Exception:
            hora = 9
        rows.append({
            "fecha":      fecha_str,
            "mes":        dt.month,
            "dia_semana": dt.isoweekday(),
            "hora":       hora,
            "precio":     precio,
            "barbero":    barbero,
            "estado":     str(apt.get("estado","")),
            "cancelada":  1 if apt.get("estado") == "cancelada" else 0,
        })
    return pd.DataFrame(rows)

# ── CARGA ──────────────────────────────────────────────────────────────────────
df = load_data()
if df.empty:
    st.error("No hay datos. Verifica la conexión a MongoDB.")
    st.stop()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title("📊 UrbanBlade — Predicción de Demanda")
st.markdown("Anticipa los horarios pico, temporadas de alta demanda y días con mayor ingreso.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total citas", len(df))
with col2:
    hora_pico = df.groupby("hora").size().idxmax()
    st.metric("Hora pico", f"{hora_pico:02d}:00 hrs")
with col3:
    dia_pico = df.groupby("dia_semana").size().idxmax()
    st.metric("Día más activo", DIAS.get(dia_pico, "?"))
with col4:
    ingreso_total = df["precio"].sum()
    st.metric("Ingreso total", f"${ingreso_total:,.0f}")

st.divider()

# ── TABS ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["⏰ Por horario", "📅 Por día", "🗓️ Por mes/temporada", "🔮 Predictor"]
)

# ── TAB 1: HORARIOS ────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Demanda por hora del día")

    por_hora = df.groupby("hora").agg(
        total_citas=("precio","count"),
        ingreso_total=("precio","sum"),
        ticket_prom=("precio","mean"),
    ).reset_index()
    por_hora["ingreso_total"] = por_hora["ingreso_total"].round(0)
    por_hora["ticket_prom"]   = por_hora["ticket_prom"].round(0)
    max_c = por_hora["total_citas"].max()
    por_hora["intensidad"] = por_hora["total_citas"] / max_c

    fig_hora = go.Figure()
    fig_hora.add_trace(go.Bar(
        x=[f"{h:02d}:00" for h in por_hora["hora"]],
        y=por_hora["total_citas"],
        name="Citas",
        marker_color=[
            "#E53935" if c >= max_c * 0.8
            else "#FB8C00" if c >= max_c * 0.5
            else "#43A047"
            for c in por_hora["total_citas"]
        ],
        text=por_hora["total_citas"],
        textposition="outside",
    ))
    fig_hora.add_trace(go.Scatter(
        x=[f"{h:02d}:00" for h in por_hora["hora"]],
        y=por_hora["ingreso_total"],
        name="Ingreso ($)", yaxis="y2",
        line=dict(color="#1565C0", width=2), mode="lines+markers",
    ))
    fig_hora.update_layout(
        title="Citas e ingresos por hora",
        xaxis_title="Hora del día",
        yaxis_title="Número de citas",
        yaxis2=dict(title="Ingreso ($)", overlaying="y", side="right"),
        height=430,
        legend=dict(x=0, y=1),
    )
    st.plotly_chart(fig_hora, use_container_width=True)

    col_h1, col_h2, col_h3 = st.columns(3)
    top3 = por_hora.nlargest(3, "total_citas")["hora"].tolist()
    low3 = por_hora.nsmallest(3, "total_citas")["hora"].tolist()
    with col_h1:
        st.success(f"**Horas pico:** {', '.join(f'{h:02d}:00' for h in top3)}\n\nTener 3 barberos disponibles")
    with col_h2:
        st.warning(f"**Horas intermedias:** 12:00–14:00\n\nDescanso escalonado de personal")
    with col_h3:
        st.error(f"**Horas muertas:** {', '.join(f'{h:02d}:00' for h in low3)}\n\nLanzar promo en esos slots")

# ── TAB 2: DÍA DE LA SEMANA ───────────────────────────────────────────────────
with tab2:
    st.subheader("Demanda por día de la semana")

    por_dia = df.groupby("dia_semana").agg(
        total_citas=("precio","count"),
        ingreso_total=("precio","sum"),
        cancelaciones=("cancelada","sum"),
    ).reset_index()
    por_dia["nombre_dia"] = por_dia["dia_semana"].map(DIAS)
    por_dia["ingreso_total"] = por_dia["ingreso_total"].round(0)
    por_dia["tasa_cancel"] = (por_dia["cancelaciones"] / por_dia["total_citas"] * 100).round(1)

    fig_dia = px.bar(
        por_dia.sort_values("dia_semana"),
        x="nombre_dia", y="total_citas",
        color="tasa_cancel",
        color_continuous_scale="RdYlGn_r",
        text="total_citas",
        labels={"nombre_dia": "Día", "total_citas": "Citas",
                "tasa_cancel": "% cancelación"},
        title="Citas por día (color = tasa de cancelación)",
    )
    fig_dia.update_traces(textposition="outside")
    fig_dia.update_layout(height=420, coloraxis_colorbar_title="%cancel.")
    st.plotly_chart(fig_dia, use_container_width=True)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.subheader("Ingreso total por día")
        fig_ing = px.bar(
            por_dia.sort_values("dia_semana"),
            x="nombre_dia", y="ingreso_total",
            color_discrete_sequence=["#1565C0"],
            text_auto=".0f",
        )
        fig_ing.update_traces(texttemplate="$%{text}", textposition="outside")
        fig_ing.update_layout(height=300)
        st.plotly_chart(fig_ing, use_container_width=True)
    with col_b2:
        st.subheader("Distribución por barbero × día")
        por_barb_dia = df.groupby(["dia_semana","barbero"]).size().reset_index(name="citas")
        por_barb_dia["dia"] = por_barb_dia["dia_semana"].map(DIAS)
        fig_bd = px.bar(
            por_barb_dia.sort_values("dia_semana"),
            x="dia", y="citas", color="barbero",
            barmode="stack", height=300,
        )
        st.plotly_chart(fig_bd, use_container_width=True)

# ── TAB 3: TEMPORADAS ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("Análisis de temporadas y meses")

    por_mes = df.groupby("mes").agg(
        total_citas=("precio","count"),
        ingreso_total=("precio","sum"),
        cancelaciones=("cancelada","sum"),
        ticket_prom=("precio","mean"),
    ).reset_index()
    por_mes["nombre_mes"] = por_mes["mes"].map(MESES)
    por_mes["ingreso_total"] = por_mes["ingreso_total"].round(0)
    por_mes["ticket_prom"]   = por_mes["ticket_prom"].round(0)
    por_mes["tasa_cancel"]   = (por_mes["cancelaciones"] / por_mes["total_citas"] * 100).round(1)

    fig_mes = go.Figure()
    fig_mes.add_trace(go.Bar(
        x=por_mes["nombre_mes"], y=por_mes["total_citas"],
        name="Citas", marker_color="#1565C0",
        text=por_mes["total_citas"], textposition="outside",
    ))
    fig_mes.add_trace(go.Scatter(
        x=por_mes["nombre_mes"], y=por_mes["ingreso_total"],
        name="Ingreso ($)", yaxis="y2",
        line=dict(color="#E53935", width=2), mode="lines+markers",
    ))
    fig_mes.update_layout(
        title="Citas e ingresos por mes",
        yaxis_title="Número de citas",
        yaxis2=dict(title="Ingreso ($)", overlaying="y", side="right"),
        height=420,
    )
    st.plotly_chart(fig_mes, use_container_width=True)

    # Heatmap día × hora
    st.subheader("Mapa de calor: Hora × Día de la semana")
    pivot = df.groupby(["dia_semana","hora"]).size().reset_index(name="citas")
    pivot["dia"] = pivot["dia_semana"].map(DIAS)
    heat_data = pivot.pivot(index="dia", columns="hora", values="citas").fillna(0)
    dias_order = [DIAS[d] for d in sorted(DIAS.keys()) if DIAS[d] in heat_data.index]
    heat_data = heat_data.reindex(dias_order)
    heat_data.columns = [f"{int(c):02d}:00" for c in heat_data.columns]

    fig_heat = px.imshow(
        heat_data,
        color_continuous_scale="YlOrRd",
        labels=dict(x="Hora", y="Día", color="Citas"),
        title="Densidad de citas (rojo = mayor demanda)",
        aspect="auto",
    )
    fig_heat.update_layout(height=380)
    st.plotly_chart(fig_heat, use_container_width=True)

# ── TAB 4: PREDICTOR ──────────────────────────────────────────────────────────
with tab4:
    st.subheader("🔮 Predictor de demanda")
    st.markdown("Estima cuántas citas se esperan para un horario específico.")

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        mes_sel = st.selectbox("Mes", list(MESES.keys()),
                               format_func=lambda x: MESES[x],
                               index=4)
    with col_p2:
        dia_sel = st.selectbox("Día de la semana", list(DIAS.keys()),
                               format_func=lambda x: DIAS[x],
                               index=5)
    with col_p3:
        hora_sel = st.slider("Hora del día", 7, 20, 10)

    # Predicción basada en promedios históricos (sin Spark en el dashboard)
    slot_hist = df[
        (df["mes"] == mes_sel) &
        (df["dia_semana"] == dia_sel) &
        (df["hora"] == hora_sel)
    ]
    citas_slot = len(slot_hist)
    semanas_activas = max(1, (df["mes"] == mes_sel).sum() // 7)

    similar_hora = df[df["hora"] == hora_sel]
    promedio_hora = len(similar_hora) / max(1, df["mes"].nunique() * df["dia_semana"].nunique())

    similar_dia = df[df["dia_semana"] == dia_sel]
    factor_dia  = len(similar_dia) / max(1, len(df)) * len(DIAS)

    estimacion = round(max(0, promedio_hora * factor_dia), 1)

    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.metric("Citas históricas en este slot", citas_slot,
                  help="Datos reales registrados para este mes/día/hora")
    with col_r2:
        st.metric("Estimación de demanda", f"{estimacion:.1f} citas",
                  help="Basada en patrones históricos")
    with col_r3:
        nivel = "🔴 ALTO" if estimacion > 3 else "🟡 MEDIO" if estimacion > 1.5 else "🟢 BAJO"
        st.metric("Nivel de demanda", nivel)

    if estimacion > 3:
        st.error(f"**Slot de alta demanda** — {DIAS[dia_sel]} {hora_sel:02d}:00 en {MESES[mes_sel]}\n\n"
                 f"Recomendación: Tener los 3 barberos disponibles, evitar descansos.")
    elif estimacion > 1.5:
        st.warning(f"**Demanda moderada** — Tener 2 barberos disponibles.")
    else:
        st.success(f"**Baja demanda** — Buen momento para mantenimiento / capacitación.")

    # Comparativa del día seleccionado
    st.subheader(f"Curva de demanda — {DIAS[dia_sel]} en {MESES[mes_sel]}")
    curva = df[(df["mes"] == mes_sel) & (df["dia_semana"] == dia_sel)] \
        .groupby("hora").size().reset_index(name="citas")

    if not curva.empty:
        fig_curva = px.area(
            curva, x=[f"{h:02d}:00" for h in curva["hora"]], y="citas",
            color_discrete_sequence=["#1565C0"],
            labels={"x": "Hora", "citas": "Citas"},
        )
        fig_curva.add_vline(x=f"{hora_sel:02d}:00",
                            line_dash="dash", line_color="red",
                            annotation_text="Hora seleccionada")
        fig_curva.update_layout(height=300)
        st.plotly_chart(fig_curva, use_container_width=True)
    else:
        st.info(f"No hay datos históricos para {DIAS[dia_sel]} en {MESES[mes_sel]}.")
