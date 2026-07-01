"""
Dashboard Principal – UrbanBlade Analytics
Unidades II–V | Materia: Extracción del conocimiento en bases de datos
UTVT IDGS-93 | MGTI. Héctor Velázquez Estrada | Mayo–Agosto 2026
Equipo: Equipo UrbanBlade

Ejecutar:  streamlit run analytics/main_dashboard.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from config.mongo_spark_conexion_sinnulos import (
    FEATURES_CANCEL, DIAS_SEMANA, MESES, get_clientes_df
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UrbanBlade Analytics",
    page_icon="UB",
    layout="wide",
    initial_sidebar_state="expanded",
)

GOLD   = "#d4af37"
DARK   = "#0e0e0e"
CARD   = "#1a1a1a"
GREEN  = "#2ecc71"
RED    = "#e74c3c"
BLUE   = "#3498db"
PURPLE = "#9b59b6"

st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
""", unsafe_allow_html=True)

st.markdown(f"""
<style>
  [data-testid="stAppViewContainer"] {{ background-color: {DARK}; }}
  [data-testid="stSidebar"]          {{ background-color: #111; }}
  h1, h2, h3, h4                     {{ color: {GOLD}; }}
  .stMetric label                    {{ color: #aaa !important; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }}
  .stMetric [data-testid="stMetricValue"] {{ color: white !important; font-size: 1.6rem; font-weight: 900; }}
  .stTabs [data-baseweb="tab"]        {{ color: #888; font-weight: 700; font-size: 13px; }}
  .stTabs [aria-selected="true"]      {{ color: {GOLD} !important; border-bottom: 2px solid {GOLD}; }}
  div[data-testid="stHorizontalBlock"] > div {{ border-radius: 12px; }}
  .block-container {{ padding-top: 1.5rem; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS (UNA VEZ POR SESIÓN)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Conectando a MongoDB Atlas y cargando datos reales…")
def cargar_datos():
    from config.mongo_spark_conexion_sinnulos import get_spark_session
    from pyspark.sql.functions import when, col
    spark, df, df_vector = get_spark_session()
    pdf = df.toPandas()
    return spark, df, df_vector, pdf

@st.cache_resource(show_spinner="Entrenando modelos de regresión…")
def entrenar_regresion(_spark, _df):
    """Regresión HONESTA: predice la facturación DIARIA (no el precio por cita,
    que sería trivial porque precio_cobrado==precio_servicio). Target=ingreso_dia,
    features=num_citas/duración/calendario → sin fuga de datos."""
    from pyspark.ml.feature import VectorAssembler, PolynomialExpansion
    from pyspark.ml.regression import LinearRegression
    from pyspark.ml.evaluation import RegressionEvaluator
    from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
    from pyspark.sql.functions import col, count, sum as ssum, to_date, dayofweek, month

    dia = (_df.filter(col("estado") != "cancelada")
              .withColumn("fecha_dt", to_date(col("fecha").substr(1, 10), "yyyy-MM-dd"))
              .groupBy("fecha_dt").agg(
                  count("*").alias("num_citas"),
                  ssum("ingreso").alias("ingreso_dia"),
                  ssum("duracion_min").alias("duracion_total"))
              .withColumn("dia_semana", dayofweek(col("fecha_dt")))
              .withColumn("mes", month(col("fecha_dt")))
              .dropna())
    train, test = dia.randomSplit([0.8, 0.2], seed=42)

    def evaluar(preds):
        e = lambda mt: RegressionEvaluator(labelCol="ingreso_dia", predictionCol="prediction", metricName=mt).evaluate(preds)
        return round(e("r2"), 4), round(e("mse"), 2), round(e("mae"), 2)

    a1   = VectorAssembler(inputCols=["num_citas"], outputCol="features", handleInvalid="skip")
    p1   = LinearRegression(featuresCol="features", labelCol="ingreso_dia").fit(a1.transform(train)).transform(a1.transform(test))
    r1   = evaluar(p1)
    pdf1 = p1.select("num_citas", "ingreso_dia", "prediction").toPandas()

    feat = ["num_citas", "duracion_total", "dia_semana", "mes"]
    a2   = VectorAssembler(inputCols=feat, outputCol="features", handleInvalid="skip")
    tr2  = a2.transform(train); te2 = a2.transform(test)
    m2   = LinearRegression(featuresCol="features", labelCol="ingreso_dia").fit(tr2)
    r2   = evaluar(m2.transform(te2))

    m3   = LinearRegression(featuresCol="features", labelCol="ingreso_dia", regParam=0.5, elasticNetParam=0).fit(tr2)
    r3   = evaluar(m3.transform(te2))
    m4   = LinearRegression(featuresCol="features", labelCol="ingreso_dia", regParam=0.5, elasticNetParam=1).fit(tr2)
    r4   = evaluar(m4.transform(te2))

    poly = PolynomialExpansion(inputCol="features", outputCol="pf", degree=2)
    m5   = LinearRegression(featuresCol="pf", labelCol="ingreso_dia").fit(poly.transform(tr2))
    r5   = evaluar(m5.transform(poly.transform(te2)))

    ev   = RegressionEvaluator(labelCol="ingreso_dia", predictionCol="prediction", metricName="r2")
    lr   = LinearRegression(featuresCol="features", labelCol="ingreso_dia")
    pg   = ParamGridBuilder().addGrid(lr.regParam, [0.01, 0.1, 1]).addGrid(lr.elasticNetParam, [0, 0.5, 1]).build()
    cv   = CrossValidator(estimator=lr, estimatorParamMaps=pg, evaluator=ev, numFolds=3)
    r6   = evaluar(cv.fit(tr2).transform(te2))

    tabla = pd.DataFrame({
        "Modelo":  ["Lineal Simple", "Lineal Múltiple", "Ridge (L2)", "Lasso (L1)", "Polinomial", "Cross Validation"],
        "R²":      [r1[0], r2[0], r3[0], r4[0], r5[0], r6[0]],
        "MSE":     [r1[1], r2[1], r3[1], r4[1], r5[1], r6[1]],
        "MAE":     [r1[2], r2[2], r3[2], r4[2], r5[2], r6[2]],
    })
    return tabla, pdf1

@st.cache_resource(show_spinner="Entrenando Árbol de Decisión…")
def entrenar_arbol(_spark, _df):
    """Clasificación HONESTA: ¿se cancelará la cita? Target=es_cancelada,
    features de contexto (sin el estado dentro) → sin fuga de datos."""
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.classification import DecisionTreeClassifier
    from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator
    from pyspark.sql.functions import col
    from config.mongo_spark_conexion_sinnulos import FEATURES_CANCEL

    asm   = VectorAssembler(inputCols=FEATURES_CANCEL, outputCol="features", handleInvalid="skip")
    ds    = asm.transform(_df).select("features", col("es_cancelada").alias("label"))
    tr, te = ds.randomSplit([0.8, 0.2], seed=42)
    model = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=5, seed=42).fit(tr)
    preds = model.transform(te)

    def m(name): return MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName=name).evaluate(preds)
    metrics = {"Accuracy": round(m("accuracy"), 4), "Precision": round(m("weightedPrecision"), 4),
               "Recall": round(m("weightedRecall"), 4), "F1": round(m("f1"), 4),
               "AUC": round(BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC").evaluate(preds), 4)}

    conf = preds.groupBy("label", "prediction").count().toPandas()
    feat_imp = list(model.featureImportances)
    return metrics, conf, feat_imp

@st.cache_resource(show_spinner="Entrenando Random Forest…")
def entrenar_rf(_spark, _df):
    """Mismo problema que el árbol (cancelación) pero con bosque de 100 árboles."""
    from pyspark.ml import Pipeline
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
    from pyspark.sql.functions import col
    from config.mongo_spark_conexion_sinnulos import FEATURES_CANCEL

    df2  = _df.withColumn("categoria", col("es_cancelada").cast("int"))
    tr, te = df2.randomSplit([0.7, 0.3], seed=42)
    asm  = VectorAssembler(inputCols=FEATURES_CANCEL, outputCol="features", handleInvalid="skip")
    rf   = RandomForestClassifier(featuresCol="features", labelCol="categoria", numTrees=100, maxDepth=5, seed=42)
    model = Pipeline(stages=[asm, rf]).fit(tr)
    preds = model.transform(te)

    auc  = round(BinaryClassificationEvaluator(labelCol="categoria", metricName="areaUnderROC").evaluate(preds), 4)
    def m(name): return round(MulticlassClassificationEvaluator(labelCol="categoria", predictionCol="prediction", metricName=name).evaluate(preds), 4)
    metrics = {"Accuracy": m("accuracy"), "Precision": m("weightedPrecision"),
               "Recall": m("weightedRecall"), "F1": m("f1"), "AUC": auc}
    conf     = preds.groupBy("categoria", "prediction").count().toPandas()
    feat_imp = list(model.stages[-1].featureImportances)
    dist     = df2.groupBy("estado").count().toPandas()
    return metrics, conf, feat_imp, dist

@st.cache_resource(show_spinner="Ejecutando KMeans y Método del Codo…")
def entrenar_kmeans(_df_vector, k=3):
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    wcss, sil_scores = [], []
    for ki in range(2, 9):
        m  = KMeans(k=ki, seed=42, featuresCol="features", predictionCol="cluster").fit(_df_vector)
        r  = m.transform(_df_vector)
        ev = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette")
        wcss.append(m.summary.trainingCost)
        sil_scores.append(round(ev.evaluate(r), 4))
    model  = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster").fit(_df_vector)
    result = model.transform(_df_vector)
    ev     = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette")
    sil    = round(ev.evaluate(result), 4)
    pdf    = result.select("servicio", "barbero", "duracion_min", "precio", "ingreso", "estado", "cluster").toPandas()
    centers = [(round(c[0],1), round(c[1],2), round(c[2],2)) for c in model.clusterCenters()]
    return list(range(2, 9)), wcss, sil_scores, pdf, sil, centers

@st.cache_resource(show_spinner="Ejecutando PCA + KMeans…")
def entrenar_pca(_df_vector, _df):
    from pyspark.ml.feature import StandardScaler, PCA, VectorAssembler
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    from pyspark.sql.functions import udf
    from pyspark.sql.types import ArrayType, DoubleType
    df2  = _df.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})
    asm  = VectorAssembler(inputCols=["duracion_min", "precio", "ingreso"], outputCol="features", handleInvalid="skip")
    dv   = asm.transform(df2)
    sc   = StandardScaler(inputCol="features", outputCol="sf", withStd=True, withMean=True).fit(dv).transform(dv)
    pca  = PCA(k=2, inputCol="sf", outputCol="pf")
    pm   = pca.fit(sc); dp = pm.transform(sc)
    km   = KMeans(k=3, seed=42, featuresCol="pf", predictionCol="cluster").fit(dp)
    dc   = km.transform(dp)
    sil  = round(ClusteringEvaluator(featuresCol="pf", predictionCol="cluster").evaluate(dc), 4)
    v2a  = udf(lambda v: v.toArray().tolist(), ArrayType(DoubleType()))
    dc   = dc.withColumn("arr", v2a("pf"))
    pdf  = dc.select("arr", "cluster", "servicio", "barbero", "duracion_min", "precio", "ingreso").toPandas()
    pdf["PC1"] = pdf["arr"].apply(lambda x: x[0])
    pdf["PC2"] = pdf["arr"].apply(lambda x: x[1])
    var  = [round(float(v)*100, 1) for v in pm.explainedVariance]
    return pdf, var, sil

@st.cache_resource(show_spinner="Segmentando clientes (RFM + KMeans)…")
def entrenar_segmentacion(_spark, _df):
    from pyspark.ml.feature import VectorAssembler, StandardScaler
    from pyspark.ml.clustering import KMeans
    from pyspark.ml.evaluation import ClusteringEvaluator
    from pyspark.sql.functions import col, count, avg, round as sround, udf
    from pyspark.sql.types import StringType

    clientes = get_clientes_df(_spark, _df)
    feats = ["total_citas", "gasto_total", "gasto_promedio", "tasa_cancelacion_pct", "dias_sin_cita"]
    asm   = VectorAssembler(inputCols=feats, outputCol="raw", handleInvalid="skip")
    dv    = asm.transform(clientes)
    sc    = StandardScaler(inputCol="raw", outputCol="features", withMean=True, withStd=True).fit(dv).transform(dv)
    km    = KMeans(k=4, seed=42, featuresCol="features").fit(sc)
    pred  = km.transform(sc)
    sil   = round(ClusteringEvaluator(featuresCol="features").evaluate(pred), 4)

    stats = (pred.groupBy("prediction").agg(
                count("*").alias("num_clientes"),
                sround(avg("total_citas"), 1).alias("citas_prom"),
                sround(avg("gasto_total"), 0).alias("gasto_total_prom"),
                sround(avg("gasto_promedio"), 0).alias("ticket_prom"),
                sround(avg("tasa_cancelacion_pct"), 1).alias("cancelacion_pct"),
                sround(avg("dias_sin_cita"), 0).alias("dias_inactivo_prom"))
             .orderBy("gasto_total_prom", ascending=False).toPandas())

    label_map = {int(stats.iloc[0]["prediction"]): "VIP",
                 int(stats.iloc[1]["prediction"]): "Alto consumo"}
    rem = [int(stats.iloc[2]["prediction"]), int(stats.iloc[3]["prediction"])]
    sub = stats[stats["prediction"].astype(int).isin(rem)]
    inact = int(sub.sort_values("dias_inactivo_prom", ascending=False).iloc[0]["prediction"])
    label_map[inact] = "Inactivo"
    for p in rem:
        label_map.setdefault(p, "Frecuente")
    stats["segmento"] = stats["prediction"].astype(int).map(label_map)

    seg_udf = udf(lambda p: label_map.get(int(p), "?"), StringType())
    seg_pdf = (pred.withColumn("segmento", seg_udf(col("prediction")))
                   .select("cliente", "nivel", "total_citas", "gasto_total",
                           "gasto_promedio", "tasa_cancelacion_pct", "dias_sin_cita", "segmento")
                   .toPandas())
    return seg_pdf, sil, stats

@st.cache_resource(show_spinner="Prediciendo abandono de clientes (churn)…")
def entrenar_churn(_spark, _df):
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.classification import RandomForestClassifier
    from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
    from pyspark.sql.functions import col, when

    clientes = get_clientes_df(_spark, _df)
    umbral = clientes.approxQuantile("dias_sin_cita", [0.70], 0.01)[0]
    clientes = clientes.withColumn("label", when(col("dias_sin_cita") > umbral, 1.0).otherwise(0.0))

    feats = ["total_citas", "gasto_promedio", "gasto_total",
             "tasa_cancelacion_pct", "frecuencia_mensual", "meses_activo"]
    data  = VectorAssembler(inputCols=feats, outputCol="features", handleInvalid="skip").transform(clientes)
    tr, te = data.randomSplit([0.7, 0.3], seed=42)
    model  = RandomForestClassifier(featuresCol="features", labelCol="label",
                                    numTrees=100, maxDepth=5, seed=42).fit(tr)
    preds  = model.transform(te)
    auc = round(BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction",
                                              metricName="areaUnderROC").evaluate(preds), 4)
    acc = round(MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction",
                                                  metricName="accuracy").evaluate(preds), 4)
    f1  = round(MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction",
                                                  metricName="f1").evaluate(preds), 4)
    metrics  = {"AUC": auc, "Accuracy": acc, "F1": f1, "umbral": round(umbral, 0)}
    feat_imp = list(zip(feats, [round(float(x), 4) for x in model.featureImportances.toArray()]))

    try:
        from pyspark.ml.functions import vector_to_array
        scored = model.transform(data).withColumn("prob", vector_to_array(col("probability"))[1] * 100)
    except Exception:
        from pyspark.sql.functions import udf
        from pyspark.sql.types import DoubleType
        p1 = udf(lambda v: float(v[1]) * 100, DoubleType())
        scored = model.transform(data).withColumn("prob", p1(col("probability")))
    riesgo = (scored.filter(col("label") == 1)
                    .select("cliente", "nivel", "total_citas", "gasto_promedio",
                            "tasa_cancelacion_pct", "dias_sin_cita", "prob")
                    .orderBy(col("prob").desc()).limit(25).toPandas())
    total   = clientes.count()
    n_riesgo = clientes.filter(col("label") == 1).count()
    return metrics, feat_imp, riesgo, (n_riesgo, total)

@st.cache_resource(show_spinner="Buscando reglas de recomendación (FP-Growth)…")
def entrenar_recomendacion(_spark, _df):
    from pyspark.ml.fpm import FPGrowth
    from pyspark.sql.functions import col, count, collect_set, size, round as sround, desc

    df_ok = _df.filter(col("estado").isin("completada", "confirmada")).filter(col("client_id") != "")
    tx    = (df_ok.groupBy("client_id").agg(collect_set("servicio").alias("items"))
                  .filter(size(col("items")) >= 1))
    fp    = FPGrowth(itemsCol="items", minSupport=0.10, minConfidence=0.20).fit(tx)
    freq  = fp.freqItemsets.orderBy("freq", ascending=False).limit(15).toPandas()
    rules = fp.associationRules
    rules_pdf = (rules.select(
                    col("antecedent").alias("si_pide"),
                    col("consequent").alias("tambien_pedira"),
                    sround(col("confidence") * 100, 1).alias("confianza_pct"),
                    sround(col("lift"), 3).alias("lift"),
                    sround(col("support") * 100, 1).alias("support_pct"))
                 .orderBy(desc("lift")).limit(20).toPandas())
    pop = (df_ok.groupBy("servicio", "categoria").agg(count("*").alias("veces_pedido"))
                .orderBy("veces_pedido", ascending=False).toPandas())
    freq["items"] = freq["items"].apply(lambda x: ", ".join(x))
    for c in ["si_pide", "tambien_pedira"]:
        if c in rules_pdf:
            rules_pdf[c] = rules_pdf[c].apply(lambda x: ", ".join(x))
    return freq, rules_pdf, pop

@st.cache_resource(show_spinner="Analizando demanda temporal…")
def analizar_demanda(_spark, _df):
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.regression import GBTRegressor
    from pyspark.ml.evaluation import RegressionEvaluator
    from pyspark.sql.functions import col, count, sum as ssum, avg, round as sround

    d = _df.filter((col("hora") > 0) & (col("dia_semana") > 0))
    hora = d.groupBy("hora").agg(count("*").alias("citas"),
                                 sround(ssum("ingreso"), 0).alias("ingreso")).orderBy("hora").toPandas()
    dia  = d.groupBy("dia_semana").agg(count("*").alias("citas"),
                                       sround(ssum("ingreso"), 0).alias("ingreso")).orderBy("dia_semana").toPandas()
    mes  = d.groupBy("mes").agg(count("*").alias("citas"),
                                sround(ssum("ingreso"), 0).alias("ingreso"),
                                sround(avg("es_cancelada") * 100, 1).alias("cancel_pct")).orderBy("mes").toPandas()
    dia["dia_nombre"] = dia["dia_semana"].map(DIAS_SEMANA)
    mes["mes_nombre"] = mes["mes"].map(MESES)

    slots = d.groupBy("mes", "dia_semana", "hora").agg(count("*").alias("num_citas")) \
             .withColumn("num_citas", col("num_citas").cast("double"))
    data = VectorAssembler(inputCols=["mes", "dia_semana", "hora"],
                           outputCol="features", handleInvalid="skip").transform(slots)
    tr, te = data.randomSplit([0.8, 0.2], seed=42)
    gbt = GBTRegressor(featuresCol="features", labelCol="num_citas", maxDepth=3, maxIter=20, seed=42).fit(tr)
    pr  = gbt.transform(te)
    r2  = round(RegressionEvaluator(labelCol="num_citas", predictionCol="prediction", metricName="r2").evaluate(pr), 4)
    imp = list(zip(["mes", "dia_semana", "hora"], [round(float(x), 4) for x in gbt.featureImportances.toArray()]))
    return hora, dia, mes, r2, imp

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h1 style='color:{GOLD};font-size:28px;margin-bottom:0'><i class='fas fa-scissors'></i>&nbsp; UrbanBlade</h1>", unsafe_allow_html=True)
    st.caption("Extracción del conocimiento en BD · UTVT IDGS-93")
    st.divider()
    st.markdown("**Equipo:** Equipo UrbanBlade")
    st.markdown("**Docente:** MGTI. Héctor Velázquez Estrada")
    st.markdown("**Período:** Mayo–Agosto 2026")
    st.divider()
    st.markdown("**Filtros**")
    k_clusters = st.slider("Clusters KMeans (K)", 2, 8, 3)
    st.divider()
    st.caption("MongoDB Atlas → barber_db")

# ─────────────────────────────────────────────────────────────────────────────
# CARGAR DATOS
# ─────────────────────────────────────────────────────────────────────────────
try:
    spark, df, df_vector, pdf = cargar_datos()
except Exception as e:
    st.error(f"Error al conectar con MongoDB Atlas: {e}")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER + KPIs GLOBALES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"<h1 style='text-align:center;color:{GOLD};font-size:2.2rem;'><i class='fas fa-scissors'></i>&nbsp; UrbanBlade Analytics Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#888;margin-top:-10px;'>Extracción del conocimiento en bases de datos · Datos reales MongoDB Atlas</p>", unsafe_allow_html=True)
st.divider()

c1, c2, c3, c4, c5, c6 = st.columns(6)
canceladas   = pdf["es_cancelada"].sum() if "es_cancelada" in pdf else (pdf["estado"] == "cancelada").sum()
ingreso_real = pdf.loc[pdf["estado"] != "cancelada", "ingreso"].sum()
c1.metric("Total Citas",       f"{len(pdf):,}")
c2.metric("Clientes Únicos",   f"{pdf['cliente'].nunique():,}")
c3.metric("Ingreso Real",      f"${ingreso_real:,.0f}", help="Excluye citas canceladas")
c4.metric("Ticket Promedio",   f"${pdf['ingreso'].mean():,.0f}")
c5.metric("Tasa Cancelación",  f"{canceladas/len(pdf)*100:.1f}%")
c6.metric("Barberos",          pdf["barbero"].nunique())

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "Resumen Ejecutivo",
    "MapReduce / ETL",
    "Regresion",
    "Arbol de Decision",
    "Random Forest",
    "KMeans",
    "PCA",
    "Segmentacion Clientes",
    "Churn / Abandono",
    "Recomendacion",
    "Demanda",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — RESUMEN GENERAL
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.subheader("Resumen Ejecutivo del Negocio")

    col_a, col_b = st.columns(2)

    with col_a:
        # Distribución de estados
        estados = pdf["estado"].value_counts().reset_index()
        estados.columns = ["estado", "count"]
        fig = px.pie(estados, values="count", names="estado",
                     title="Distribución de Estados de Citas",
                     color_discrete_sequence=px.colors.qualitative.Set3,
                     hole=0.4)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", legend_font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Top barberos por citas
        top_barberos = pdf.groupby("barbero").size().reset_index(name="citas").sort_values("citas", ascending=False).head(10)
        fig2 = px.bar(top_barberos, x="citas", y="barbero", orientation="h",
                      title="Top 10 Barberos por Número de Citas",
                      color="citas", color_continuous_scale=[[0, "#444"], [1, GOLD]])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", yaxis=dict(autorange="reversed"),
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        # Ingresos por servicio
        por_svc = pdf.groupby("servicio")["ingreso"].sum().reset_index().sort_values("ingreso", ascending=False)
        fig3 = px.bar(por_svc, x="servicio", y="ingreso",
                      title="Ingreso Total por Tipo de Servicio",
                      color="ingreso", color_continuous_scale=[[0, "#444"], [1, GOLD]],
                      labels={"ingreso": "Ingreso ($MXN)", "servicio": "Servicio"})
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        # Histograma de precios
        fig4 = px.histogram(pdf, x="precio", nbins=30,
                            title="Distribución de Precios de Citas",
                            color_discrete_sequence=[GOLD],
                            labels={"precio": "Precio ($MXN)", "count": "Frecuencia"})
        fig4.add_vline(x=pdf["precio"].mean(), line_dash="dash", line_color=RED,
                       annotation_text=f"Media: ${pdf['precio'].mean():.0f}", annotation_font_color="white")
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MAPREDUCE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.subheader("Unidad II — MapReduce / ETL Distribuido")
    st.caption("MAP → agrupa | REDUCE → agrega métricas por servicio y barbero")

    resumen = pdf.groupby("servicio").agg(
        ingreso_total=("ingreso", "sum"),
        citas=("ingreso", "count"),
        precio_promedio=("precio", "mean"),
        duracion_promedio=("duracion_min", "mean"),
    ).reset_index().sort_values("ingreso_total", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(resumen, x="servicio", y="ingreso_total",
                     title="REDUCE → Ingreso Total por Servicio",
                     color="ingreso_total", color_continuous_scale=[[0, "#333"], [1, GOLD]],
                     labels={"ingreso_total": "Ingreso Total ($MXN)", "servicio": ""})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(resumen.sort_values("citas", ascending=False), x="servicio", y="citas",
                      title="REDUCE → Número de Citas por Servicio",
                      color="citas", color_continuous_scale=[[0, "#333"], [1, BLUE]],
                      labels={"citas": "Número de Citas", "servicio": ""})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False, xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig3 = px.scatter(resumen, x="citas", y="ingreso_total", size="precio_promedio",
                          text="servicio", title="Citas vs Ingreso Total (tamaño = precio promedio)",
                          color="ingreso_total", color_continuous_scale=[[0, "#333"], [1, GOLD]])
        fig3.update_traces(textposition="top center", textfont_color="white")
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        # Ingreso por barbero
        por_barbero = pdf.groupby("barbero")["ingreso"].sum().reset_index().sort_values("ingreso", ascending=False).head(12)
        fig4 = px.bar(por_barbero, x="ingreso", y="barbero", orientation="h",
                      title="Ingreso Total por Barbero (Top 12)",
                      color="ingreso", color_continuous_scale=[[0, "#333"], [1, PURPLE]])
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", yaxis=dict(autorange="reversed"), coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Tabla MapReduce — Resumen por Servicio")
    resumen_display = resumen.copy()
    resumen_display["ingreso_total"]     = resumen_display["ingreso_total"].apply(lambda x: f"${x:,.2f}")
    resumen_display["precio_promedio"]   = resumen_display["precio_promedio"].apply(lambda x: f"${x:,.2f}")
    resumen_display["duracion_promedio"] = resumen_display["duracion_promedio"].apply(lambda x: f"{x:.1f} min")
    resumen_display.columns = ["Servicio", "Ingreso Total", "Núm. Citas", "Precio Promedio", "Duración Promedio"]
    st.dataframe(resumen_display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — REGRESIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.subheader("Unidad III — Análisis Supervisado: Regresión")
    st.caption("Predicción de la FACTURACIÓN DIARIA (target real, sin fuga) · 6 modelos · R², MSE, MAE")
    st.info("Se predice el ingreso **por día** a partir del volumen de citas y el calendario. "
            "Predecir el precio de una sola cita sería trivial (precio_cobrado==precio_servicio), "
            "por eso agregamos por día: ahí sí hay varianza real.", icon=":material/info:")

    with st.spinner("Entrenando 6 modelos de regresión sobre datos reales…"):
        tabla_reg, pdf_scatter = entrenar_regresion(spark, df)

    mejor = tabla_reg.loc[tabla_reg["R²"].idxmax()]
    peor  = tabla_reg.loc[tabla_reg["MSE"].idxmax()]

    c1, c2, c3 = st.columns(3)
    c1.metric("Mejor R²",       f"{mejor['R²']:.4f}",  delta=mejor["Modelo"])
    c2.metric("Menor MAE",      f"${tabla_reg['MAE'].min():.2f}")
    c3.metric("Menor MSE",      f"{tabla_reg['MSE'].min():.2f}")

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.bar(tabla_reg, x="Modelo", y="R²",
                     title="Comparación R² — 6 Modelos de Regresión",
                     color="R²", color_continuous_scale=[[0, "#333"], [1, GOLD]],
                     text_auto=".4f")
        fig.add_hline(y=0.9, line_dash="dot", line_color=GREEN, annotation_text="R²=0.9 excelente", annotation_font_color="white")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", coloraxis_showscale=False, xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="MSE", x=tabla_reg["Modelo"], y=tabla_reg["MSE"], marker_color=RED))
        fig2.add_trace(go.Bar(name="MAE", x=tabla_reg["Modelo"], y=tabla_reg["MAE"], marker_color=BLUE))
        fig2.update_layout(title="MSE vs MAE por Modelo",
                           barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", xaxis_tickangle=-20)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        fig3 = px.scatter(pdf_scatter, x="num_citas", y="ingreso_dia",
                          title="Facturación diaria real vs Predicción (Lineal Simple)",
                          labels={"num_citas": "Citas en el día", "ingreso_dia": "Facturación del día ($MXN)"},
                          color_discrete_sequence=[BLUE], opacity=0.5)
        fig3.add_scatter(x=pdf_scatter["num_citas"], y=pdf_scatter["prediction"],
                         mode="markers", name="Predicción", marker=dict(color=GOLD, symbol="x", size=6))
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.subheader("Tabla Comparativa de Modelos")
        st.dataframe(
            tabla_reg.style.highlight_max(subset=["R²"], color="#2d4a1e")
                           .highlight_min(subset=["MSE", "MAE"], color="#2d4a1e")
                           .format({"R²": "{:.4f}", "MSE": "{:.2f}", "MAE": "{:.2f}"}),
            use_container_width=True, hide_index=True
        )
        mejor_idx = tabla_reg["R²"].idxmax()
        st.success(f"Mejor modelo: **{tabla_reg.loc[mejor_idx, 'Modelo']}** — R²={tabla_reg.loc[mejor_idx, 'R²']:.4f}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ÁRBOL DE DECISIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.subheader("Unidad III — Árbol de Decisión")
    st.caption("Clasificación honesta: ¿se CANCELARÁ la cita?  1 = cancelada  |  0 = resto  ·  clases desbalanceadas → AUC")

    with st.spinner("Entrenando Árbol de Decisión…"):
        metricas_dt, conf_dt, feat_imp_dt = entrenar_arbol(spark, df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Accuracy",  f"{metricas_dt['Accuracy']*100:.1f}%")
    c2.metric("Precision", f"{metricas_dt['Precision']:.4f}")
    c3.metric("Recall",    f"{metricas_dt['Recall']:.4f}")
    c4.metric("F1-Score",  f"{metricas_dt['F1']:.4f}")
    c5.metric("AUC-ROC",   f"{metricas_dt['AUC']:.4f}")

    col_a, col_b = st.columns(2)

    with col_a:
        # Matriz de confusión como heatmap
        labels_map = {0: "No cancela", 1: "Cancela"}
        conf_dt["label_str"]      = conf_dt["label"].map(labels_map)
        conf_dt["prediction_str"] = conf_dt["prediction"].map(labels_map)
        pivot = conf_dt.pivot(index="label_str", columns="prediction_str", values="count").fillna(0)
        fig = px.imshow(pivot, text_auto=True, color_continuous_scale=[[0, DARK], [1, GOLD]],
                        title="Matriz de Confusión — Árbol de Decisión",
                        labels=dict(x="Predicción", y="Real", color="Cantidad"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Importancia de variables
        feat_names = FEATURES_CANCEL
        fig2 = px.bar(x=feat_names, y=feat_imp_dt,
                      title="Importancia de Variables — Árbol de Decisión",
                      color=feat_imp_dt, color_continuous_scale=[[0, "#333"], [1, GOLD]],
                      labels={"x": "Variable", "y": "Importancia", "color": "Importancia"})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Métricas en radar
    col_c, col_d = st.columns(2)
    with col_c:
        categorias = ["Accuracy", "Precision", "Recall", "F1", "AUC"]
        valores    = [metricas_dt[k] for k in categorias]
        fig3 = go.Figure(go.Scatterpolar(
            r=valores, theta=categorias, fill="toself",
            line_color=GOLD, fillcolor=f"rgba(212,175,55,0.2)"
        ))
        fig3.update_layout(title="Métricas del Modelo (Radar)",
                           polar=dict(radialaxis=dict(visible=True, range=[0, 1], color="white"),
                                      angularaxis=dict(color="white")),
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        st.markdown("### Interpretación")
        acc = metricas_dt["Accuracy"]
        auc = metricas_dt["AUC"]
        st.info(f"""
**Árbol de Decisión — predicción de cancelación**

- **AUC {auc:.4f}**: capacidad discriminativa {'excelente' if auc > 0.8 else 'buena' if auc > 0.7 else 'moderada'}
  (métrica clave: las clases están desbalanceadas ~8% cancelaciones)
- **Accuracy {acc*100:.1f}%**: con clases desbalanceadas, el accuracy engaña → mirar AUC/Recall
- **Feature más importante**: `{feat_names[feat_imp_dt.index(max(feat_imp_dt))]}`
  ({max(feat_imp_dt)*100:.1f}% del poder predictivo)
- **Sin fuga de datos**: se predice desde el contexto (hora, día, servicio), no desde el estado
- **Aplicación**: reforzar recordatorios en los horarios/servicios de mayor riesgo
        """)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — RANDOM FOREST
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.subheader("Unidad III — Random Forest")
    st.caption("Mismo problema que el Árbol (cancelación) pero con 100 árboles → comparar AUC: el bosque suele ganar")

    with st.spinner("Entrenando Random Forest (100 árboles)…"):
        metricas_rf, conf_rf, feat_imp_rf, dist_estados = entrenar_rf(spark, df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Accuracy",  f"{metricas_rf['Accuracy']*100:.1f}%")
    c2.metric("Precision", f"{metricas_rf['Precision']:.4f}")
    c3.metric("Recall",    f"{metricas_rf['Recall']:.4f}")
    c4.metric("F1-Score",  f"{metricas_rf['F1']:.4f}")
    c5.metric("AUC-ROC",   f"{metricas_rf['AUC']:.4f}")

    col_a, col_b = st.columns(2)

    with col_a:
        labels_rf = {0: "No cancela", 1: "Cancela"}
        conf_rf["cat_str"]  = conf_rf["categoria"].map(labels_rf)
        conf_rf["pred_str"] = conf_rf["prediction"].map(labels_rf)
        pivot_rf = conf_rf.pivot(index="cat_str", columns="pred_str", values="count").fillna(0)
        fig = px.imshow(pivot_rf, text_auto=True, color_continuous_scale=[[0, DARK], [1, RED]],
                        title="Matriz de Confusión — Random Forest",
                        labels=dict(x="Predicción", y="Real", color="Cantidad"))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        feat_names = FEATURES_CANCEL
        fig2 = px.bar(x=feat_names, y=feat_imp_rf,
                      title="Importancia de Variables — Random Forest",
                      color=feat_imp_rf, color_continuous_scale=[[0, "#333"], [1, RED]],
                      labels={"x": "Variable", "y": "Importancia"}, text_auto=".3f")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        fig3 = px.pie(dist_estados, values="count", names="estado",
                      title="Distribución Real de Estados en Datos de Entrenamiento",
                      hole=0.35, color_discrete_sequence=px.colors.qualitative.Set2)
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        categorias = ["Accuracy", "Precision", "Recall", "F1", "AUC"]
        valores    = [metricas_rf[k] for k in categorias]
        fig4 = go.Figure(go.Scatterpolar(
            r=valores, theta=categorias, fill="toself",
            line_color=RED, fillcolor="rgba(231,76,60,0.2)"
        ))
        fig4.update_layout(title="Métricas Random Forest (Radar)",
                           polar=dict(radialaxis=dict(visible=True, range=[0, 1], color="white"),
                                      angularaxis=dict(color="white")),
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — KMEANS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.subheader("Unidad IV — KMeans Clustering")
    st.caption("Segmentación no supervisada de citas por duración, precio e ingreso")

    with st.spinner(f"Ejecutando KMeans K={k_clusters} y Método del Codo…"):
        ks, wcss, sil_scores, km_pdf, sil, centers = entrenar_kmeans(df_vector, k_clusters)

    c1, c2, c3 = st.columns(3)
    c1.metric("Clusters (K)",        k_clusters)
    c2.metric("Silhouette Score",    sil, delta="Bueno" if sil > 0.5 else "Aceptable" if sil > 0.2 else "Débil")
    c3.metric("Total Registros",     f"{len(km_pdf):,}")

    col_a, col_b = st.columns(2)

    with col_a:
        fig = make_subplots(rows=1, cols=2, subplot_titles=("WCSS — Método del Codo", "Silhouette por K"))
        fig.add_trace(go.Scatter(x=ks, y=wcss, mode="lines+markers",
                                 line=dict(color=GOLD, width=2), marker=dict(size=8)), row=1, col=1)
        fig.add_trace(go.Scatter(x=ks, y=sil_scores, mode="lines+markers",
                                 line=dict(color=GREEN, width=2), marker=dict(size=8)), row=1, col=2)
        fig.add_vline(x=k_clusters, line_dash="dash", line_color=RED)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", showlegend=False, title_text="Evaluación de K")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.scatter(km_pdf, x="precio", y="ingreso",
                          color=km_pdf["cluster"].astype(str),
                          title=f"Segmentación K={k_clusters} — Precio vs Ingreso",
                          hover_data=["servicio", "barbero", "duracion_min", "estado"],
                          color_discrete_sequence=px.colors.qualitative.Set1,
                          labels={"color": "Cluster", "precio": "Precio ($MXN)", "ingreso": "Ingreso ($MXN)"})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        fig3 = px.scatter_3d(km_pdf, x="precio", y="duracion_min", z="ingreso",
                             color=km_pdf["cluster"].astype(str),
                             title="Clustering 3D — Precio / Duración / Ingreso",
                             hover_name="servicio",
                             color_discrete_sequence=px.colors.qualitative.Set1,
                             labels={"color": "Cluster", "duracion_min": "Duración (min)"})
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        svc_cluster = km_pdf.groupby(["cluster", "servicio"]).size().reset_index(name="count")
        fig4 = px.bar(svc_cluster, x="cluster", y="count", color="servicio",
                      title="Servicios por Cluster",
                      labels={"cluster": "Cluster", "count": "Citas", "servicio": "Servicio"},
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Centroides de Clusters")
    centro_df = pd.DataFrame(centers, columns=["Duración (min)", "Precio ($)", "Ingreso ($)"])
    centro_df.index = [f"Cluster {i}" for i in range(len(centers))]
    st.dataframe(centro_df.style.format("{:.2f}"), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — PCA
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.subheader("Unidad IV — PCA + KMeans")
    st.caption("Reducción de dimensionalidad: 3 features → 2 componentes principales → clustering")

    with st.spinner("Ejecutando PCA + KMeans…"):
        pca_pdf, varianza, pca_sil = entrenar_pca(df_vector, df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Varianza PC1",        f"{varianza[0]:.1f}%")
    c2.metric("Varianza PC2",        f"{varianza[1]:.1f}%")
    c3.metric("Varianza Total",      f"{sum(varianza):.1f}%")
    c4.metric("Silhouette (PCA+KM)", pca_sil)

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.scatter(pca_pdf, x="PC1", y="PC2",
                         color=pca_pdf["cluster"].astype(str),
                         hover_data=["servicio", "barbero", "precio", "duracion_min", "ingreso"],
                         title=f"PCA + KMeans — Varianza explicada: {sum(varianza):.1f}%  |  Silhouette: {pca_sil}",
                         color_discrete_sequence=px.colors.qualitative.Set1,
                         labels={"color": "Cluster",
                                 "PC1": f"PC1 ({varianza[0]:.1f}% varianza)",
                                 "PC2": f"PC2 ({varianza[1]:.1f}% varianza)"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Varianza explicada
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=["PC1", "PC2"], y=varianza,
                              marker_color=[GOLD, BLUE], text=[f"{v:.1f}%" for v in varianza],
                              textposition="outside", textfont_color="white"))
        fig2.add_trace(go.Scatter(x=["PC1", "PC2"], y=[sum(varianza[:1]), sum(varianza)],
                                  mode="lines+markers+text", name="Varianza acumulada",
                                  line_color=GREEN, text=[f"{sum(varianza[:1]):.1f}%", f"{sum(varianza):.1f}%"],
                                  textposition="top right", textfont_color="white"))
        fig2.update_layout(title="Varianza Explicada por Componente Principal",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", yaxis_title="%", showlegend=True)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        svc_pca = pca_pdf.groupby(["cluster", "servicio"]).size().reset_index(name="count")
        fig3 = px.sunburst(svc_pca, path=["cluster", "servicio"], values="count",
                           title="Composición de Clusters por Servicio (Sunburst)",
                           color_discrete_sequence=px.colors.qualitative.Set1)
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    with col_d:
        perfil = pca_pdf.groupby("cluster").agg(
            avg_precio=("precio", "mean"),
            avg_ingreso=("ingreso", "mean"),
            avg_duracion=("duracion_min", "mean"),
            total_citas=("precio", "count"),
        ).reset_index()
        fig4 = px.bar(perfil, x="cluster", y=["avg_precio", "avg_ingreso", "avg_duracion"],
                      barmode="group", title="Perfil de Clusters PCA (promedios)",
                      labels={"value": "Valor", "cluster": "Cluster", "variable": "Métrica"},
                      color_discrete_sequence=[GOLD, GREEN, BLUE])
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Interpretación de Clusters PCA")
    avg = pca_pdf.groupby("cluster")[["precio", "ingreso", "duracion_min"]].mean()
    for cl in sorted(pca_pdf["cluster"].unique()):
        row    = avg.loc[cl]
        global_avg = pca_pdf[["precio", "ingreso", "duracion_min"]].mean()
        perfil_txt = "Premium" if row["ingreso"] > global_avg["ingreso"] and row["precio"] > global_avg["precio"] \
                     else "Económico" if row["ingreso"] < global_avg["ingreso"] \
                     else "Estándar"
        st.info(f"**Cluster {cl} — {perfil_txt}**: "
                f"Precio ${row['precio']:.0f} | Ingreso ${row['ingreso']:.0f} | "
                f"Duración {row['duracion_min']:.0f} min")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — SEGMENTACIÓN DE CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.subheader("Unidad IV — Segmentación de Clientes (RFM + KMeans)")
    st.caption("1000 clientes reales agrupados en 4 segmentos por comportamiento de consumo")

    seg_pdf, seg_sil, seg_stats = entrenar_segmentacion(spark, df)

    dist = seg_pdf["segmento"].value_counts().reset_index()
    dist.columns = ["segmento", "clientes"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clientes", f"{len(seg_pdf):,}")
    c2.metric("Segmentos", seg_pdf["segmento"].nunique())
    c3.metric("Silhouette", seg_sil, delta="Bueno" if seg_sil > 0.5 else "Aceptable" if seg_sil > 0.2 else "Débil")
    vip = int(dist.loc[dist["segmento"] == "VIP", "clientes"].sum())
    c4.metric("Clientes VIP", vip)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.pie(dist, values="clientes", names="segmento", hole=0.45,
                     title="Distribución de Clientes por Segmento",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig2 = px.scatter(seg_pdf, x="total_citas", y="gasto_total", color="segmento",
                          size="gasto_promedio", hover_name="cliente",
                          title="Clientes: Frecuencia vs Gasto (color = segmento)",
                          labels={"total_citas": "Total de citas", "gasto_total": "Gasto total ($MXN)"},
                          color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Perfil promedio de cada segmento")
    st.dataframe(seg_stats[["segmento", "num_clientes", "citas_prom", "gasto_total_prom",
                            "ticket_prom", "cancelacion_pct", "dias_inactivo_prom"]],
                 use_container_width=True, hide_index=True)
    st.subheader("Top clientes VIP")
    st.dataframe(seg_pdf[seg_pdf["segmento"] == "VIP"]
                 .sort_values("gasto_total", ascending=False)
                 .head(10)[["cliente", "nivel", "total_citas", "gasto_total", "gasto_promedio"]],
                 use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 — CHURN / ABANDONO
# ══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.subheader("Unidad III — Predicción de Abandono (Churn)")
    st.caption("Random Forest · churn = cliente con recencia > percentil 70 · features SIN la recencia (sin fuga)")

    ch_metrics, ch_imp, ch_riesgo, (n_riesgo, n_total) = entrenar_churn(spark, df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AUC-ROC", ch_metrics["AUC"], help="Evaluado en datos no vistos")
    c2.metric("F1-Score", ch_metrics["F1"])
    c3.metric("Clientes en riesgo", f"{n_riesgo:,}", delta=f"{n_riesgo/n_total*100:.0f}% del total")
    c4.metric("Umbral recencia", f"{ch_metrics['umbral']:.0f} días")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        imp_df = pd.DataFrame(ch_imp, columns=["variable", "importancia"]).sort_values("importancia")
        fig = px.bar(imp_df, x="importancia", y="variable", orientation="h",
                     title="Qué anticipa el abandono (importancia de variables)",
                     color="importancia", color_continuous_scale=[[0, "#333"], [1, RED]], text_auto=".3f")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig2 = go.Figure(go.Pie(values=[n_riesgo, n_total - n_riesgo],
                                labels=["En riesgo", "Estables"], hole=0.5,
                                marker_colors=[RED, GREEN]))
        fig2.update_layout(title="Clientes en riesgo vs estables",
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Clientes con mayor probabilidad de abandono")
    ch_show = ch_riesgo.copy()
    ch_show["prob"] = ch_show["prob"].apply(lambda x: f"{x:.1f}%")
    ch_show.columns = ["Cliente", "Nivel", "Citas", "Ticket prom.", "Cancel %", "Días sin cita", "Prob. abandono"]
    st.dataframe(ch_show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 10 — RECOMENDACIÓN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.subheader("Unidad IV — Recomendación de Servicios (FP-Growth)")
    st.caption("Market Basket Analysis: 'los clientes que piden A también piden B'")

    freq_pdf, rules_pdf, pop_pdf = entrenar_recomendacion(spark, df)

    c1, c2 = st.columns(2)
    c1.metric("Reglas encontradas", len(rules_pdf))
    c2.metric("Servicios analizados", pop_pdf["servicio"].nunique())

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(pop_pdf.head(12).sort_values("veces_pedido"),
                     x="veces_pedido", y="servicio", orientation="h", color="categoria",
                     title="Servicios más solicitados",
                     labels={"veces_pedido": "Veces pedido", "servicio": ""},
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        st.markdown("**Itemsets frecuentes (servicios que aparecen juntos)**")
        st.dataframe(freq_pdf.rename(columns={"items": "Servicios", "freq": "Frecuencia"}),
                     use_container_width=True, hide_index=True)

    st.subheader("Reglas de asociación (ordenadas por lift)")
    if len(rules_pdf) > 0:
        st.dataframe(rules_pdf.rename(columns={
            "si_pide": "Si pide", "tambien_pedira": "También pedirá",
            "confianza_pct": "Confianza %", "lift": "Lift", "support_pct": "Support %"}),
            use_container_width=True, hide_index=True)
        st.caption("lift > 1.5 → recomendación fuerte · lift > 1.0 → válida · lift < 1.0 → no recomendar")
    else:
        st.warning("No se encontraron reglas con los umbrales actuales (dataset con poca co-ocurrencia por cliente).")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 11 — DEMANDA
# ══════════════════════════════════════════════════════════════════════════════
with tabs[10]:
    st.subheader("Unidad IV — Predicción de Demanda y Horarios")
    st.caption("Patrones temporales + GBT: ¿cuántas citas esperar por hora, día y mes?")

    dem_hora, dem_dia, dem_mes, dem_r2, dem_imp = analizar_demanda(spark, df)

    hora_pico = dem_hora.loc[dem_hora["citas"].idxmax()]
    dia_pico  = dem_dia.loc[dem_dia["citas"].idxmax()]
    c1, c2, c3 = st.columns(3)
    c1.metric("Hora pico", f"{int(hora_pico['hora']):02d}:00", delta=f"{int(hora_pico['citas'])} citas")
    c2.metric("Día más activo", dia_pico["dia_nombre"], delta=f"{int(dia_pico['citas'])} citas")
    c3.metric("R² modelo GBT", dem_r2)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(dem_hora, x="hora", y="citas", title="Demanda por hora del día",
                     color="citas", color_continuous_scale=[[0, "#333"], [1, GOLD]],
                     labels={"hora": "Hora", "citas": "Citas"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with col_b:
        fig2 = px.bar(dem_dia, x="dia_nombre", y="citas", title="Demanda por día de la semana",
                      color="citas", color_continuous_scale=[[0, "#333"], [1, BLUE]],
                      labels={"dia_nombre": "", "citas": "Citas"})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns([2, 1])
    with col_c:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=dem_mes["mes_nombre"], y=dem_mes["citas"], name="Citas", marker_color=GOLD))
        fig3.add_trace(go.Scatter(x=dem_mes["mes_nombre"], y=dem_mes["cancel_pct"], name="Cancelación %",
                                  yaxis="y2", line=dict(color=RED, width=2)))
        fig3.update_layout(title="Estacionalidad mensual: citas y % cancelación",
                           yaxis=dict(title="Citas"), yaxis2=dict(title="Cancel %", overlaying="y", side="right"),
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)
    with col_d:
        imp_df = pd.DataFrame(dem_imp, columns=["variable", "importancia"]).sort_values("importancia")
        fig4 = px.bar(imp_df, x="importancia", y="variable", orientation="h",
                      title="Qué determina la demanda", color="importancia",
                      color_continuous_scale=[[0, "#333"], [1, GREEN]], text_auto=".3f")
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f"<p style='text-align:center;color:#555;font-size:11px;'>"
    f"UrbanBlade Analytics · UTVT IDGS-93 · Extracción del conocimiento en bases de datos · "
    f"MGTI. Héctor Velázquez Estrada · Equipo UrbanBlade | IDGS-93</p>",
    unsafe_allow_html=True
)
