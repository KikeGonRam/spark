import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pyspark.ml.feature import VectorAssembler, PolynomialExpansion
from pyspark.ml.regression import LinearRegression
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from config.mongo_spark_conexion_sinnulos import get_spark_session

st.set_page_config(
    page_title="UrbanBlade – Modelos de Regresión",
    page_icon="💈",
    layout="wide"
)

st.title("💈 Plataforma de Analítica Predictiva – UrbanBlade")
st.markdown("*6 Modelos de Regresión con PySpark | Extracción del Conocimiento en BD*")

st.sidebar.header("Filtros")


@st.cache_resource
def cargar_datos():
    spark, df, _ = get_spark_session()
    pdf = df.select("servicio", "barbero", "cantidad", "precio", "ingreso").toPandas()
    spark.stop()
    return pdf


df_pandas = cargar_datos()

servicios = ["Todos"] + sorted(df_pandas["servicio"].unique().tolist())
servicio_sel = st.sidebar.selectbox("Filtrar por Servicio", servicios)

if servicio_sel != "Todos":
    df_filtrado = df_pandas[df_pandas["servicio"] == servicio_sel]
else:
    df_filtrado = df_pandas

# ANÁLISIS EXPLORATORIO
st.subheader("Análisis Exploratorio")
col1, col2, col3 = st.columns(3)
col1.metric("Citas",            f"{len(df_filtrado):,}")
col2.metric("Ingreso Total",    f"${df_filtrado['ingreso'].sum():,.0f}")
col3.metric("Precio Promedio",  f"${df_filtrado['precio'].mean():,.0f}")

c1, c2 = st.columns(2)
with c1:
    fig1 = px.scatter(df_filtrado, x="cantidad", y="ingreso",
                      color="servicio", title="Cantidad vs Ingreso")
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    fig2 = px.scatter(df_filtrado, x="precio", y="ingreso",
                      color="servicio", title="Precio vs Ingreso")
    st.plotly_chart(fig2, use_container_width=True)

fig3 = px.histogram(df_filtrado, x="ingreso", nbins=30,
                    title="Distribución de Ingresos", color_discrete_sequence=["#d4af37"])
st.plotly_chart(fig3, use_container_width=True)

# MODELOS ML
st.subheader("Modelos de Machine Learning")

if st.button("Ejecutar los 6 modelos de regresión"):
    with st.spinner("Entrenando modelos con PySpark..."):

        spark, df_spark, _ = get_spark_session()

        if servicio_sel != "Todos":
            df_spark = df_spark.filter(df_spark.servicio == servicio_sel)

        train, test = df_spark.randomSplit([0.8, 0.2], seed=42)
        evaluator = RegressionEvaluator(labelCol="ingreso", predictionCol="prediction", metricName="r2")

        resultados = {}

        # Modelo 1 – Lineal Simple
        a1 = VectorAssembler(inputCols=["cantidad"], outputCol="features", handleInvalid="skip")
        m1 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(a1.transform(train))
        resultados["Lineal Simple"] = evaluator.evaluate(m1.transform(a1.transform(test)))

        # Modelo 2 – Lineal Múltiple
        a2 = VectorAssembler(inputCols=["cantidad", "precio"], outputCol="features", handleInvalid="skip")
        tr2 = a2.transform(train); te2 = a2.transform(test)
        m2 = LinearRegression(featuresCol="features", labelCol="ingreso").fit(tr2)
        resultados["Lineal Múltiple"] = evaluator.evaluate(m2.transform(te2))

        # Modelo 3 – Ridge
        m3 = LinearRegression(featuresCol="features", labelCol="ingreso",
                               regParam=0.5, elasticNetParam=0).fit(tr2)
        resultados["Ridge"] = evaluator.evaluate(m3.transform(te2))

        # Modelo 4 – Lasso
        m4 = LinearRegression(featuresCol="features", labelCol="ingreso",
                               regParam=0.5, elasticNetParam=1).fit(tr2)
        resultados["Lasso"] = evaluator.evaluate(m4.transform(te2))

        # Modelo 5 – Polinómico
        poly  = PolynomialExpansion(inputCol="features", outputCol="poly_features", degree=2)
        tr5   = poly.transform(tr2); te5 = poly.transform(te2)
        m5    = LinearRegression(featuresCol="poly_features", labelCol="ingreso").fit(tr5)
        resultados["Polinomial"] = evaluator.evaluate(m5.transform(te5))

        # Modelo 6 – Cross Validation
        lr_cv = LinearRegression(featuresCol="features", labelCol="ingreso")
        grid  = ParamGridBuilder() \
            .addGrid(lr_cv.regParam, [0.01, 0.1, 1]) \
            .addGrid(lr_cv.elasticNetParam, [0, 0.5, 1]).build()
        cv    = CrossValidator(estimator=lr_cv, estimatorParamMaps=grid,
                               evaluator=evaluator, numFolds=3)
        m6    = cv.fit(tr2)
        resultados["Cross Validation"] = evaluator.evaluate(m6.transform(te2))

        spark.stop()

    # Gráfica de comparación
    import pandas as pd
    df_res = pd.DataFrame(list(resultados.items()), columns=["Modelo", "R2"])
    df_res = df_res.sort_values("R2", ascending=False)

    fig_comp = px.bar(df_res, x="Modelo", y="R2",
                      color="R2", color_continuous_scale="Viridis",
                      title="Comparación de Modelos de Regresión – R² Score",
                      text=df_res["R2"].round(4))
    fig_comp.update_traces(textposition="outside")
    fig_comp.update_layout(yaxis_range=[0, 1.05])
    st.plotly_chart(fig_comp, use_container_width=True)

    mejor = df_res.iloc[0]
    st.success(f"Mejor modelo: **{mejor['Modelo']}** con R² = {round(mejor['R2'], 4)}")
    st.dataframe(df_res)
