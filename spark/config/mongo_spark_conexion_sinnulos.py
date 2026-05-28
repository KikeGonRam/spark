from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus


def get_spark_session():

    # 1.- Cargar variables de entorno desde /spark/.env
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    database        = os.getenv("MONGO_DB",         "barberpro")
    collection_name = os.getenv("MONGO_COLLECTION", "appointments")

    # Soportar URI directa (local/Docker) O variables Atlas (patrón del profesor)
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        user     = os.getenv("MONGO_USER")
        password = quote_plus(os.getenv("MONGO_PASSWORD", ""))
        cluster  = os.getenv("MONGO_CLUSTER")
        mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

    # 2.- Crear sesión Spark
    spark = SparkSession.builder \
        .appName("UrbanBlade-BigData") \
        .config("spark.jars.packages",
                "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0") \
        .config("spark.mongodb.read.connection.uri",  mongo_uri) \
        .config("spark.mongodb.read.database",        database) \
        .config("spark.mongodb.read.collection",      collection_name) \
        .config("spark.mongodb.write.connection.uri", mongo_uri) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    # 3.- Leer datos
    df = spark.read.format("mongodb").load()
    print("Datos UrbanBlade cargados desde MongoDB")
    df.show(10)

    # 4.- Limpieza y tipado (CRÍTICO)
    df = df.select(
        col("servicio"),
        col("barbero"),
        col("cantidad").cast("double"),
        col("precio").cast("double"),
        col("estado")
    )

    # 5.- Eliminar nulos antes de crear features
    df = df.dropna(subset=["cantidad", "precio"])

    # 6.- Feature Engineering — ingreso = cantidad * precio
    df = df.withColumn("ingreso", col("cantidad") * col("precio"))

    # 7.- Vectorización segura
    assembler = VectorAssembler(
        inputCols=["cantidad", "precio", "ingreso"],
        outputCol="features",
        handleInvalid="skip"
    )

    df_vector = assembler.transform(df)

    return spark, df, df_vector
