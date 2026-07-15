"""
Dashboard: Pedidos de Tienda — UrbanBlade
Ejecutar: streamlit run unidades/unidad_5_visualizacion/dashboards_individuales/dashboard_pedidos_tienda.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus
from pathlib import Path
import os

_p = Path(__file__).resolve()
env_path = next((c / ".env" for c in _p.parents if (c / ".env").exists()), _p.parent / ".env")
load_dotenv(dotenv_path=env_path)

mongo_uri = (f"mongodb+srv://{os.getenv('MONGO_USER')}:"
             f"{quote_plus(os.getenv('MONGO_PASSWORD'))}@"
             f"{os.getenv('MONGO_CLUSTER')}")
db_name = os.getenv("MONGO_DB")

st.set_page_config(
    page_title="UrbanBlade — Pedidos de Tienda",
    layout="wide"
)


def _num(v):
    if v is None:
        return 0.0
    if hasattr(v, "to_decimal"):
        return float(v.to_decimal())
    return float(v)


@st.cache_data(ttl=300)
def load_data():
    mc = MongoClient(mongo_uri)
    db = mc[db_name]
    orders = list(db["orders"].find({}, {
        "_id": 0, "folio": 1, "tipo": 1, "estado": 1, "total": 1,
        "metodo_pago": 1, "items": 1, "created_at": 1,
    }))
    mc.close()

    rows, items_rows = [], []
    for o in orders:
        items = o.get("items") or []
        rows.append({
            "folio": o.get("folio", ""),
            "tipo": str(o.get("tipo", "")),
            "estado": str(o.get("estado", "")),
            "total": _num(o.get("total")),
            "metodo_pago": str(o.get("metodo_pago") or "N/A"),
            "num_items": len(items),
        })
        if str(o.get("estado", "")) == "entregado":
            for it in items:
                items_rows.append({
                    "producto": str(it.get("nombre", "N/A")),
                    "cantidad": _num(it.get("cantidad", 1)),
                    "subtotal": _num(it.get("subtotal")),
                    "tipo_pedido": str(o.get("tipo", "")),
                })
    return pd.DataFrame(rows), pd.DataFrame(items_rows)


# ── CARGA ──────────────────────────────────────────────────────────────────────
df, items_df = load_data()
if df.empty:
    st.error("No hay pedidos registrados. Verifica la conexión a MongoDB.")
    st.stop()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title("UrbanBlade — Pedidos de Tienda")
st.markdown("Add-ons de cita ('cita') vs compras sueltas ('tienda') — checkout de productos.")

entregados = df[df["estado"] == "entregado"]
tienda = df[df["tipo"] == "tienda"]
cancelados = tienda[tienda["estado"] == "cancelado"]
tasa_cancel = round(len(cancelados) / len(tienda) * 100, 1) if len(tienda) else 0.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Pedidos totales", f"{len(df):,}")
with col2:
    st.metric("Ingreso entregado", f"${entregados['total'].sum():,.0f}")
with col3:
    st.metric("Ticket promedio", f"${entregados['total'].mean():,.0f}" if len(entregados) else "N/A")
with col4:
    st.metric("Cancelación tienda", f"{tasa_cancel}%")

st.divider()

# ── TABS ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Distribución", "Top productos", "Métodos de pago"])

with tab1:
    st.subheader("Distribución por tipo y estado")
    dist = df.groupby(["tipo", "estado"]).size().reset_index(name="pedidos")
    fig = px.bar(dist, x="tipo", y="pedidos", color="estado", barmode="stack",
                 title="Pedidos por tipo y estado",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        ing_tipo = entregados.groupby("tipo")["total"].sum().reset_index()
        fig2 = px.pie(ing_tipo, values="total", names="tipo", hole=0.45,
                      title="Ingreso entregado por tipo (cita vs tienda)")
        st.plotly_chart(fig2, use_container_width=True)
    with col_b:
        citas_addon = len(df[df["tipo"] == "cita"])
        ingreso_total = entregados["total"].sum()
        pct_addon = round(ing_tipo.set_index("tipo")["total"].get("cita", 0) / ingreso_total * 100, 1) if ingreso_total else 0
        st.info(f"**{citas_addon:,} pedidos** son add-ons dentro de una cita.\n\n"
                f"Representan el **{pct_addon}%** del ingreso total de tienda — "
                f"el checkout durante la reserva convierte mejor que la compra suelta.")
        if tasa_cancel > 15:
            st.warning(f"Tasa de cancelación de tienda ({tasa_cancel}%) es alta — "
                       f"revisar tiempos de entrega o disponibilidad de stock.")

with tab2:
    st.subheader("Top 10 productos más vendidos (pedidos entregados)")
    if items_df.empty:
        st.info("Sin líneas de producto en pedidos entregados.")
    else:
        resumen = (items_df.groupby("producto")
                   .agg(unidades=("cantidad", "sum"), ingreso=("subtotal", "sum"))
                   .sort_values("unidades", ascending=False).head(10).reset_index())
        fig3 = px.bar(resumen, x="unidades", y="producto", orientation="h",
                      title="Unidades vendidas por producto",
                      color="unidades", color_continuous_scale=[[0, "#ccc"], [1, "#1565C0"]])
        fig3.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(resumen, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Métodos de pago (pedidos entregados)")
    metodos = entregados["metodo_pago"].value_counts().reset_index()
    metodos.columns = ["metodo", "pedidos"]
    fig4 = px.pie(metodos, values="pedidos", names="metodo", hole=0.45,
                  title="Distribución por método de pago")
    st.plotly_chart(fig4, use_container_width=True)
