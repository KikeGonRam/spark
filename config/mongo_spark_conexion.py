import sys
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus
import pandas as pd


def _resolve_barbero(brb: dict, users_map: dict) -> str:
    """Obtiene el nombre del barbero.

    El BarberFactory no llena el campo 'nombre', así que se resuelve
    a través de users.name usando el user_id del barbero.
    """
    nombre = brb.get("nombre")
    if nombre:
        return nombre
    uid = str(brb.get("user_id", ""))
    return users_map.get(uid, {}).get("name", "Sin nombre")


def get_spark_session():
    os.environ["PYSPARK_PYTHON"]        = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)

    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD"))
    cluster  = os.getenv("MONGO_CLUSTER")
    database = os.getenv("MONGO_DB")

    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

    spark = SparkSession.builder \
        .appName("UrbanBlade-BigData") \
        .config("spark.pyspark.python",        sys.executable) \
        .config("spark.pyspark.driver.python", sys.executable) \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    # Join de 4 colecciones: appointments + services + barbers + users
    client = MongoClient(mongo_uri)
    db     = client[database]

    appointments = list(db["appointments"].find(
        {},
        {"_id": 0, "service_id": 1, "barber_id": 1,
         "precio_cobrado": 1, "estado": 1, "fecha": 1}
    ))
    services_map = {
        str(s["_id"]): s
        for s in db["services"].find({}, {"_id": 1, "nombre": 1, "precio": 1, "duracion_min": 1})
    }
    barbers_map = {
        str(b["_id"]): b
        for b in db["barbers"].find({}, {"_id": 1, "nombre": 1, "user_id": 1})
    }
    users_map = {
        str(u["_id"]): u
        for u in db["users"].find({}, {"_id": 1, "name": 1})
    }
    client.close()

    records = []
    for apt in appointments:
        svc = services_map.get(str(apt.get("service_id", "")), {})
        brb = barbers_map.get(str(apt.get("barber_id", "")), {})

        precio_cobrado = apt.get("precio_cobrado")
        precio_base    = float(svc.get("precio") or 0)
        precio         = float(precio_cobrado) if precio_cobrado is not None else precio_base

        records.append({
            "servicio":    svc.get("nombre", "Desconocido"),
            "barbero":     _resolve_barbero(brb, users_map),
            "duracion_min": float(svc.get("duracion_min") or 30),
            "precio":      precio,
            "estado":      str(apt.get("estado", "")),
            "ingreso":     precio,
            "fecha":       str(apt.get("fecha", "")),
        })

    pandas_df = pd.DataFrame(records)
    print(f"Datos reales cargados desde MongoDB: {len(pandas_df)} citas")

    df = spark.createDataFrame(pandas_df)

    assembler = VectorAssembler(
        inputCols=["duracion_min", "precio", "ingreso"],
        outputCol="features"
    )
    df_vector = assembler.transform(df)

    return spark, df, df_vector
