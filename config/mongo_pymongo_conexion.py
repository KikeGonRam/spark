# Conexión alternativa: PyMongo → Pandas → Spark
# Funciona con cualquier versión de PySpark (no requiere conector MongoDB Spark)
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus
import pandas as pd


def get_spark_session():

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD"))
    cluster  = os.getenv("MONGO_CLUSTER")
    database = os.getenv("MONGO_DB")
    coll     = os.getenv("MONGO_COLLECTION")

    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

    spark = SparkSession.builder \
        .appName("UrbanBlade-BigData") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    # PyMongo → Pandas → Spark DataFrame
    client    = MongoClient(mongo_uri)
    db        = client[database]
    cursor    = db[coll].find(
        {},
        {"_id": 0, "servicio": 1, "barbero": 1, "cantidad": 1, "precio": 1, "estado": 1}
    )
    pandas_df = pd.DataFrame(list(cursor))
    client.close()

    print(f"Datos cargados: {len(pandas_df)} registros desde '{coll}'")

    df = spark.createDataFrame(pandas_df)
    df = df.select(
        col("servicio").cast("string"),
        col("barbero").cast("string"),
        col("cantidad").cast("double"),
        col("precio").cast("double"),
        col("estado").cast("string")
    )
    df = df.dropna(subset=["cantidad", "precio"])
    df = df.withColumn("ingreso", col("cantidad") * col("precio"))

    assembler = VectorAssembler(
        inputCols=["cantidad", "precio", "ingreso"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_vector = assembler.transform(df)

    return spark, df, df_vector
