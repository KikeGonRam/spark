import sys
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

    # Garantiza que workers usen el mismo Python que el driver (evita VERSION_MISMATCH)
    os.environ["PYSPARK_PYTHON"]        = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

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
        .config("spark.pyspark.python",        sys.executable) \
        .config("spark.pyspark.driver.python", sys.executable) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    # PyMongo carga datos → Pandas → Spark DataFrame
    client    = MongoClient(mongo_uri)
    cursor    = client[database][coll].find(
        {},
        {"_id": 0, "servicio": 1, "barbero": 1, "cantidad": 1, "precio": 1, "estado": 1}
    )
    pandas_df = pd.DataFrame(list(cursor))
    client.close()

    df = spark.createDataFrame(pandas_df)
    df = df.withColumn("ingreso", col("cantidad") * col("precio"))

    assembler = VectorAssembler(
        inputCols=["cantidad", "precio", "ingreso"],
        outputCol="features"
    )
    df_vector = assembler.transform(df)

    return spark, df, df_vector
