import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.mongo_spark_conexion_sinnulos import get_spark_session

from pyspark.sql.functions import when, col
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

st.set_page_config(page_title="Dashboard ML – UrbanBlade", layout="wide")
st.title("Sistema Inteligente de Predicción de Ingresos – UrbanBlade")

if st.button("Ejecutar Modelo"):

    st.info("Iniciando Spark y cargando datos reales...")
    spark, df, _ = get_spark_session()

    st.info("Limpiando datos...")
    df = df.fillna({"duracion_min": 30, "precio": 0, "ingreso": 0})

    # Label: cita de ALTO INGRESO (> 500 MXN) = 1, bajo = 0
    df = df.withColumn(
        "categoria",
        when(col("ingreso") > 500, 1).otherwise(0)
    )

    train_data, test_data = df.randomSplit([0.7, 0.3], seed=42)

    assembler = VectorAssembler(
        inputCols=["duracion_min", "precio", "ingreso"],
        outputCol="features",
        handleInvalid="skip"
    )

    rf = RandomForestClassifier(
        labelCol="categoria",
        featuresCol="features",
        seed=42
    )

    pipeline = Pipeline(stages=[assembler, rf])

    st.info("Optimizando modelo...")
    paramGrid = ParamGridBuilder() \
        .addGrid(rf.numTrees, [20, 50]) \
        .addGrid(rf.maxDepth, [5, 10]) \
        .build()

    evaluator = BinaryClassificationEvaluator(
        labelCol="categoria",
        metricName="areaUnderROC"
    )

    crossval = CrossValidator(
        estimator=pipeline,
        estimatorParamMaps=paramGrid,
        evaluator=evaluator,
        numFolds=3
    )

    model = crossval.fit(train_data)

    predictions = model.transform(test_data)
    auc = evaluator.evaluate(predictions)
    st.success(f"Modelo entrenado | AUC: {round(auc, 4)}")

    pdf = predictions.select(
        "duracion_min", "precio", "ingreso", "prediction", "categoria"
    ).toPandas()

    st.subheader("Análisis de Datos")

    categoria = st.selectbox("Filtrar por categoría:", ["Todos", 0, 1])
    if categoria != "Todos":
        pdf = pdf[pdf["categoria"] == categoria]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total registros",  len(pdf))
    c2.metric("Ingreso promedio", f"${round(pdf['ingreso'].mean(), 2):,.0f}")
    c3.metric("AUC del modelo",   round(auc, 4))

    fig1 = px.histogram(pdf, x="ingreso", title="Distribución de Ingresos – UrbanBlade")
    st.plotly_chart(fig1, use_container_width=True)

    conf_matrix = pdf.groupby(["categoria", "prediction"]).size().reset_index(name="count")
    fig2 = px.density_heatmap(
        conf_matrix, x="prediction", y="categoria", z="count",
        title="Matriz de Confusión"
    )
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.scatter(
        pdf, x="precio", y="ingreso", color="prediction",
        title="Precio vs Ingreso – UrbanBlade"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Importancia de Variables")
    rf_model  = model.bestModel.stages[-1]
    features  = ["duracion_min", "precio", "ingreso"]
    importance = list(rf_model.featureImportances)
    fig4 = px.bar(x=features, y=importance,
                  labels={"x": "Variable", "y": "Importancia"},
                  title="Importancia de Variables (Random Forest)")
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Datos procesados")
    st.dataframe(pdf.head(100))

    spark.stop()
    st.info("Sesión Spark finalizada")
