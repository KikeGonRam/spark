from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus


def get_spark_session():

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    database        = os.getenv("MONGO_DB",         "barberpro")
    collection_name = os.getenv("MONGO_COLLECTION", "appointments")

    # Soportar varias formas de configuración:
    # 1) MONGO_URI (preferred) - e.g. mongodb://mongodb:27017
    # 2) MONGO_HOST + MONGO_PORT (+ optional MONGO_USER/MONGO_PASSWORD)
    # 3) MONGO_CLUSTER + MONGO_USER/MONGO_PASSWORD (Atlas mongodb+srv)
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        host = os.getenv("MONGO_HOST")
        port = os.getenv("MONGO_PORT")
        user = os.getenv("MONGO_USER")
        password_raw = os.getenv("MONGO_PASSWORD")
        cluster = os.getenv("MONGO_CLUSTER")

        # Case A: explicit host/port (typical docker compose local mongo)
        if host and port:
            if user and password_raw:
                password = quote_plus(password_raw)
                mongo_uri = f"mongodb://{user}:{password}@{host}:{port}"
            else:
                mongo_uri = f"mongodb://{host}:{port}"
        # Case B: Atlas cluster string
        elif cluster:
            password = quote_plus(password_raw or "")
            # If user provided, include credentials, otherwise attempt SRV without creds
            if user:
                mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"
            else:
                mongo_uri = f"mongodb+srv://{cluster}"
        else:
            # Fallback to docker-compose default (local mongo service)
            mongo_uri = "mongodb://mongodb:27017"  

    spark = SparkSession.builder \
        .appName("UrbanBlade-BigData") \
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
        .config("spark.mongodb.read.connection.uri",  mongo_uri) \
        .config("spark.mongodb.read.database",        database) \
        .config("spark.mongodb.read.collection",      collection_name) \
        .config("spark.mongodb.write.connection.uri", mongo_uri) \
        .getOrCreate()

    df = spark.read.format("mongodb").load()

    df = df.withColumn("ingreso", col("cantidad") * col("precio"))

    assembler = VectorAssembler(
        inputCols=["cantidad", "precio", "ingreso"],
        outputCol="features"
    )

    df_vector = assembler.transform(df)

    return spark, df, df_vector
