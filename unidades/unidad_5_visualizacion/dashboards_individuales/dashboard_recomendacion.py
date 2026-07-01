"""
Dashboard: Recomendación de Servicios — UrbanBlade
Ejecutar: streamlit run unidades/unidad_5_visualizacion/dashboards_individuales/dashboard_recomendacion.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus
from collections import defaultdict
from itertools import combinations
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
    page_title="UrbanBlade — Recomendación de Servicios",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_data():
    mc = MongoClient(mongo_uri)
    db = mc[db_name]
    services_map = {str(s["_id"]): s for s in db["services"].find(
        {}, {"_id":1,"nombre":1,"precio":1,"categoria":1})}
    users_map = {str(u["_id"]): u for u in db["users"].find(
        {}, {"_id":1,"name":1})}
    raw_apts = list(db["appointments"].find(
        {"estado": {"$in": ["completada", "confirmada"]}},
        {"_id":0,"client_id":1,"service_id":1,"precio_cobrado":1,"estado":1}
    ))
    mc.close()

    rows = []
    for apt in raw_apts:
        cid = str(apt.get("client_id", ""))
        sid = str(apt.get("service_id", ""))
        if not cid or cid in ("None", ""):
            continue
        svc = services_map.get(sid, {})
        if not svc.get("nombre"):
            continue
        rows.append({
            "client_id":     cid,
            "nombre_cliente": users_map.get(cid, {}).get("name", "Cliente"),
            "servicio":      svc["nombre"],
            "categoria":     svc.get("categoria", "sin categoría"),
            "precio":        float(apt.get("precio_cobrado") or svc.get("precio") or 0),
        })
    return pd.DataFrame(rows), services_map

def compute_association_rules(df, min_support=0.05, min_confidence=0.15):
    transactions = df.groupby("client_id")["servicio"].apply(set).to_dict()
    n = len(transactions)
    if n == 0:
        return pd.DataFrame(), {}

    item_counts = defaultdict(int)
    for items in transactions.values():
        for item in items:
            item_counts[item] += 1

    pair_counts = defaultdict(int)
    for items in transactions.values():
        sorted_items = sorted(items)
        for a, b in combinations(sorted_items, 2):
            pair_counts[(a, b)] += 1

    rules = []
    for (a, b), count in pair_counts.items():
        sup = count / n
        if sup < min_support:
            continue
        conf_ab = count / item_counts[a] if item_counts[a] > 0 else 0
        conf_ba = count / item_counts[b] if item_counts[b] > 0 else 0
        lift_ab = conf_ab / (item_counts[b] / n) if item_counts[b] > 0 else 0
        lift_ba = conf_ba / (item_counts[a] / n) if item_counts[a] > 0 else 0

        if conf_ab >= min_confidence:
            rules.append({"si_pide": a, "recomendar": b,
                          "confianza": round(conf_ab * 100, 1),
                          "lift": round(lift_ab, 3),
                          "support": round(sup * 100, 1),
                          "co_ocurrencias": count})
        if conf_ba >= min_confidence:
            rules.append({"si_pide": b, "recomendar": a,
                          "confianza": round(conf_ba * 100, 1),
                          "lift": round(lift_ba, 3),
                          "support": round(sup * 100, 1),
                          "co_ocurrencias": count})

    return pd.DataFrame(rules).sort_values("lift", ascending=False), item_counts

# ── CARGA ──────────────────────────────────────────────────────────────────────
df_citas, services_map = load_data()
if df_citas.empty:
    st.error("No hay datos. Verifica la conexión a MongoDB.")
    st.stop()

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.title("UrbanBlade — Recomendación de Servicios")
st.markdown("Descubre qué servicios adicionales ofrecerle a cada cliente según su historial de compras.")
st.divider()

# ── CONTROLES ──────────────────────────────────────────────────────────────────
col_p1, col_p2 = st.columns(2)
with col_p1:
    min_sup  = st.slider("Support mínimo (%)", 3, 30, 5, 1,
                          help="% de clientes que usan ambos servicios")
with col_p2:
    min_conf = st.slider("Confianza mínima (%)", 10, 80, 15, 5,
                          help="% de quienes piden A que también piden B")

rules_df, item_counts = compute_association_rules(
    df_citas, min_support=min_sup/100, min_confidence=min_conf/100
)

# ── KPIs ───────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    n_cl = df_citas["client_id"].nunique()
    st.metric("Clientes analizados", n_cl)
with col2:
    n_svc = df_citas["servicio"].nunique()
    st.metric("Servicios distintos", n_svc)
with col3:
    st.metric("Reglas encontradas", len(rules_df))
with col4:
    if not rules_df.empty:
        best_lift = rules_df["lift"].max()
        st.metric("Mejor lift", f"{best_lift:.2f}", help="Lift > 1 = asociación positiva")
    else:
        st.metric("Mejor lift", "—")

st.divider()

# ── REGLAS DE ASOCIACIÓN ───────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("Reglas de recomendación encontradas")
    if not rules_df.empty:
        rules_show = rules_df.copy()
        rules_show["Regla"] = rules_show.apply(
            lambda r: f"Si pide '{r['si_pide']}' → recomendar '{r['recomendar']}'", axis=1
        )
        st.dataframe(
            rules_show[["Regla", "confianza", "lift", "support", "co_ocurrencias"]]
            .rename(columns={
                "confianza": "Confianza (%)",
                "lift": "Lift",
                "support": "Support (%)",
                "co_ocurrencias": "Clientes en común",
            }).reset_index(drop=True),
            use_container_width=True,
            height=400,
        )
    else:
        st.info("No se encontraron reglas con los umbrales actuales. Reduce el support o la confianza.")

with col_right:
    st.subheader("Servicios más populares")
    pop_df = df_citas.groupby("servicio").agg(
        veces=("client_id", "count"),
        clientes=("client_id", "nunique"),
    ).reset_index().sort_values("veces", ascending=False)
    fig_pop = px.bar(
        pop_df.head(10),
        x="veces", y="servicio",
        orientation="h",
        color="clientes",
        color_continuous_scale="Blues",
        labels={"veces": "Veces pedido", "servicio": "", "clientes": "Clientes"},
    )
    fig_pop.update_layout(height=400, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_pop, use_container_width=True)

# ── SIMULADOR DE RECOMENDACIÓN ─────────────────────────────────────────────────
st.divider()
st.subheader("Simulador: que recomendar")

col_sim1, col_sim2 = st.columns(2)
with col_sim1:
    servicio_sel = st.selectbox(
        "El cliente quiere agendar:",
        sorted(df_citas["servicio"].unique().tolist())
    )

with col_sim2:
    if not rules_df.empty:
        sugerencias = rules_df[rules_df["si_pide"] == servicio_sel] \
            .sort_values("lift", ascending=False)
        if not sugerencias.empty:
            st.markdown("**Servicios a recomendar:**")
            for _, row in sugerencias.head(3).iterrows():
                st.success(
                    f"**{row['recomendar']}**  \n"
                    f"Confianza: {row['confianza']}% | Lift: {row['lift']} | "
                    f"{int(row['co_ocurrencias'])} clientes en comun"
                )
        else:
            st.info("No hay reglas para este servicio con los umbrales actuales.")
    else:
        cat_sel = df_citas[df_citas["servicio"] == servicio_sel]["categoria"].iloc[0] \
            if len(df_citas[df_citas["servicio"] == servicio_sel]) > 0 else ""
        otros = df_citas[
            (df_citas["categoria"] == cat_sel) & (df_citas["servicio"] != servicio_sel)
        ]["servicio"].value_counts().head(3)
        st.markdown("**Mas populares en la misma categoria:**")
        for svc, cnt in otros.items():
            st.info(f"**{svc}** — {cnt} citas")

# ── MAPA DE CALOR: CO-OCURRENCIA ───────────────────────────────────────────────
st.divider()
st.subheader("Mapa de co-ocurrencia de servicios")

servicios_top = df_citas["servicio"].value_counts().head(8).index.tolist()
df_top = df_citas[df_citas["servicio"].isin(servicios_top)]
transactions_top = df_top.groupby("client_id")["servicio"].apply(set)

matrix = pd.DataFrame(0, index=servicios_top, columns=servicios_top)
for items in transactions_top:
    items_in = [s for s in items if s in servicios_top]
    for a in items_in:
        for b in items_in:
            if a != b:
                matrix.loc[a, b] += 1

fig_heat = px.imshow(
    matrix,
    color_continuous_scale="YlOrRd",
    labels=dict(color="Co-ocurrencias"),
    title="Número de clientes que piden ambos servicios",
    aspect="auto",
)
fig_heat.update_layout(height=450)
st.plotly_chart(fig_heat, use_container_width=True)

# ── ANÁLISIS POR CATEGORÍA ─────────────────────────────────────────────────────
st.divider()
st.subheader("Clientes multi-categoría")

cat_tx = df_citas.groupby("client_id")["categoria"].apply(set)
multi  = cat_tx[cat_tx.apply(len) >= 2]
st.metric(
    "Clientes que usan 2+ categorías",
    len(multi),
    help="Son los mejores candidatos para upsell cruzado"
)

fig_cat = px.histogram(
    cat_tx.apply(len).reset_index(name="num_categorias"),
    x="num_categorias",
    color_discrete_sequence=["#4CAF50"],
    labels={"num_categorias": "Categorías distintas usadas", "count": "Clientes"},
    title="Distribución de diversidad de servicios por cliente",
)
fig_cat.update_layout(bargap=0.2)
st.plotly_chart(fig_cat, use_container_width=True)
