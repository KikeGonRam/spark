"""
Capa de datos única y enriquecida — UrbanBlade Analytics
========================================================
Un solo punto de entrada que lee TODA la base real `barber_db` y la entrega
lista para cualquier análisis (supervisado, no supervisado, clientes, demanda).

Colecciones unidas (JOIN en memoria con PyMongo):
    appointments  →  service_id  →  services   (nombre, categoria, precio, duracion_min)
                  →  barber_id   →  barbers    →  user_id → users.name   (nombre barbero)
                  →  client_id   →  clients    →  user_id → users.name   (nombre cliente)
                                                 (+ nivel, puntos, fecha_nacimiento)

IMPORTANTE (compatibilidad):
    get_spark_session() sigue devolviendo (spark, df, df_vector) con las MISMAS
    columnas originales — los scripts 01–07 no se rompen. Solo se AGREGAN columnas
    nuevas (cliente, nivel, categoria, hora, dia_semana, mes, edad_cliente…).

Equipo : Equipo UrbanBlade — UTVT IDGS-93
Materia: Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys
import os
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml.feature import VectorAssembler
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Constantes reutilizables por todos los scripts (una sola fuente de verdad)
# ─────────────────────────────────────────────────────────────────────────────
ESTADOS_VALIDOS   = ["cancelada", "completada", "confirmada", "pendiente"]
ESTADOS_PERDIDA   = ["cancelada"]          # estados que representan ingreso perdido
CATEGORIAS        = ["barba", "combo", "corte", "tratamiento"]
DIAS_SEMANA       = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves",
                     5: "Viernes", 6: "Sábado", 7: "Domingo"}
MESES             = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo",
                     6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre",
                     10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

# Features "clásicas" (compatibilidad con scripts 01–07)
FEATURES_BASE     = ["duracion_min", "precio", "ingreso"]
# Features honestas para clasificación de cancelación (sin fuga de datos)
FEATURES_CANCEL   = ["duracion_min", "precio", "hora", "dia_semana", "mes"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de resolución de nombres / fechas
# ─────────────────────────────────────────────────────────────────────────────
def _to_dt(v):
    """Convierte un valor de Mongo (datetime | str | None) a datetime o None."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    try:
        return datetime.strptime(str(v)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.strptime(str(v)[:10], "%Y-%m-%d")
        except Exception:
            return None


def _hora_int(hora_str, default=10):
    """'12:30' → 12. Robustez ante None / formatos raros."""
    try:
        return int(str(hora_str)[:2])
    except Exception:
        return default


def _edad(fecha_nac, ref_year=None):
    dt = _to_dt(fecha_nac)
    if dt is None:
        return None
    ref = ref_year or datetime.now().year
    edad = ref - dt.year
    return float(edad) if 0 < edad < 120 else None


# ─────────────────────────────────────────────────────────────────────────────
# Extracción cruda (PyMongo, SIN Spark) — testeable de forma aislada
# ─────────────────────────────────────────────────────────────────────────────
def _build_maps(db):
    services_map = {
        str(s["_id"]): s
        for s in db["services"].find(
            {}, {"_id": 1, "nombre": 1, "precio": 1, "duracion_min": 1, "categoria": 1})
    }
    barbers_map = {
        str(b["_id"]): b
        for b in db["barbers"].find({}, {"_id": 1, "user_id": 1})
    }
    clients_map = {
        str(c["_id"]): c
        for c in db["clients"].find(
            {}, {"_id": 1, "user_id": 1, "nivel": 1, "puntos": 1,
                 "total_citas": 1, "fecha_nacimiento": 1})
    }
    users_map = {
        str(u["_id"]): u
        for u in db["users"].find({}, {"_id": 1, "name": 1, "email": 1})
    }
    return services_map, barbers_map, clients_map, users_map


def _extract_records(db):
    """Devuelve una lista de dicts (una fila por cita) uniendo las 4 colecciones.

    Función pura sobre PyMongo → se puede probar sin levantar Spark.
    """
    services_map, barbers_map, clients_map, users_map = _build_maps(db)

    def nombre_barbero(bid):
        brb = barbers_map.get(str(bid), {})
        uid = str(brb.get("user_id", ""))
        return users_map.get(uid, {}).get("name", "Sin nombre")

    def datos_cliente(cid):
        cli = clients_map.get(str(cid), {})
        uid = str(cli.get("user_id", ""))
        nombre = users_map.get(uid, {}).get("name", "Cliente")
        return {
            "cliente": nombre,
            "nivel":   str(cli.get("nivel", "regular")),
            "puntos_cliente": float(cli.get("puntos") or 0),
            "edad_cliente":   _edad(cli.get("fecha_nacimiento")),
        }

    appointments = db["appointments"].find(
        {"deleted_at": None},
        {"_id": 0, "client_id": 1, "barber_id": 1, "service_id": 1,
         "precio_cobrado": 1, "estado": 1, "fecha": 1, "hora_inicio": 1,
         "metodo_pago": 1}
    )

    records = []
    for apt in appointments:
        svc = services_map.get(str(apt.get("service_id", "")), {})
        cli = datos_cliente(apt.get("client_id"))

        precio_cobrado = apt.get("precio_cobrado")
        precio_base    = float(svc.get("precio") or 0)
        precio         = float(precio_cobrado) if precio_cobrado is not None else precio_base

        fdt   = _to_dt(apt.get("fecha"))
        estado = str(apt.get("estado", ""))

        records.append({
            # ── columnas originales (compatibilidad scripts 01–07) ──────────
            "servicio":     svc.get("nombre", "Desconocido"),
            "barbero":      nombre_barbero(apt.get("barber_id")),
            "duracion_min": float(svc.get("duracion_min") or 30),
            "precio":       precio,
            "estado":       estado,
            "ingreso":      precio,                     # revenue real = precio_cobrado
            "fecha":        str(apt.get("fecha", ""))[:19],
            # ── dimensión CLIENTE (nueva, arregla el bug client_id→users) ────
            "cliente":        cli["cliente"],
            "nivel":          cli["nivel"],
            "puntos_cliente": cli["puntos_cliente"],
            "edad_cliente":   cli["edad_cliente"] if cli["edad_cliente"] is not None else 0.0,
            # ── dimensión SERVICIO ───────────────────────────────────────────
            "categoria":    str(svc.get("categoria", "otros")),
            "precio_base":  precio_base,
            # ── dimensión TIEMPO (derivada de fecha / hora_inicio) ───────────
            "anio":         fdt.year          if fdt else 0,
            "mes":          fdt.month         if fdt else 0,
            "dia":          fdt.day           if fdt else 0,
            "dia_semana":   fdt.isoweekday()  if fdt else 0,   # 1=Lun … 7=Dom
            "hora":         _hora_int(apt.get("hora_inicio")),
            # ── operativo ────────────────────────────────────────────────────
            "metodo_pago":  str(apt.get("metodo_pago", "efectivo")),
            "es_cancelada": 1 if estado == "cancelada" else 0,
            "client_id":    str(apt.get("client_id", "")),
        })

    return records


# ─────────────────────────────────────────────────────────────────────────────
# Sesión Spark + DataFrame enriquecido (API pública, compatible)
# ─────────────────────────────────────────────────────────────────────────────
def _connect_db():
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD"))
    cluster  = os.getenv("MONGO_CLUSTER")
    database = os.getenv("MONGO_DB")
    uri = f"mongodb+srv://{user}:{password}@{cluster}"
    return MongoClient(uri), database


def _build_spark():
    os.environ["PYSPARK_PYTHON"]        = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    spark = (SparkSession.builder
             .appName("UrbanBlade-BigData")
             .config("spark.pyspark.python",        sys.executable)
             .config("spark.pyspark.driver.python", sys.executable)
             .getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def get_spark_session():
    """API pública. Devuelve (spark, df, df_vector) — misma firma de siempre.

    `df` conserva las 7 columnas originales y AGREGA la dimensión cliente,
    categoría y tiempo. `df_vector` mantiene las FEATURES_BASE por compatibilidad.
    """
    spark = _build_spark()

    client, database = _connect_db()
    db = client[database]
    records = _extract_records(db)
    client.close()

    pandas_df = pd.DataFrame(records)
    print(f"Datos reales cargados desde MongoDB: {len(pandas_df)} citas "
          f"| {pandas_df['cliente'].nunique()} clientes "
          f"| {pandas_df['barbero'].nunique()} barberos")

    df = spark.createDataFrame(pandas_df)

    # Tipado explícito (columnas originales) + limpieza de nulos clave
    df = df.select(
        col("servicio").cast("string"),
        col("categoria").cast("string"),
        col("barbero").cast("string"),
        col("cliente").cast("string"),
        col("nivel").cast("string"),
        col("duracion_min").cast("double"),
        col("precio").cast("double"),
        col("precio_base").cast("double"),
        col("estado").cast("string"),
        col("ingreso").cast("double"),
        col("es_cancelada").cast("int"),
        col("fecha").cast("string"),
        col("anio").cast("int"),
        col("mes").cast("int"),
        col("dia").cast("int"),
        col("dia_semana").cast("int"),
        col("hora").cast("int"),
        col("puntos_cliente").cast("double"),
        col("edad_cliente").cast("double"),
        col("metodo_pago").cast("string"),
        col("client_id").cast("string"),
    )
    df = df.dropna(subset=["duracion_min", "precio", "ingreso"])

    assembler = VectorAssembler(
        inputCols=FEATURES_BASE,
        outputCol="features",
        handleInvalid="skip"
    )
    df_vector = assembler.transform(df)

    return spark, df, df_vector


# ─────────────────────────────────────────────────────────────────────────────
# Helper: DataFrame agregado POR CLIENTE (RFM) — usado por 08 y 09
# ─────────────────────────────────────────────────────────────────────────────
def get_clientes_df(spark, df=None, fecha_ref=None):
    """Devuelve un DataFrame con una fila por cliente y métricas RFM reales:

        total_citas, gasto_total, gasto_promedio, tasa_cancelacion_pct,
        dias_sin_cita (recencia), meses_activo, frecuencia_mensual,
        nivel, puntos_cliente, edad_cliente.

    Resuelve correctamente el nombre del cliente (client_id → clients → users).
    `fecha_ref` ancla la recencia; por defecto = fecha máxima del dataset.
    """
    from pyspark.sql.functions import (
        col, count, sum as ssum, avg, max as smax, min as smin,
        when, round as sround, to_date, datediff, lit, first
    )

    if df is None:
        _, df, _ = get_spark_session()

    d = (df
         .filter(col("client_id") != "")
         .withColumn("fecha_dt", to_date(col("fecha").substr(1, 10), "yyyy-MM-dd")))

    if fecha_ref is None:
        fecha_ref = d.agg(smax("fecha_dt")).first()[0]
    d = d.withColumn("ref", to_date(lit(str(fecha_ref)), "yyyy-MM-dd")) \
         .withColumn("dias_desde", datediff(col("ref"), col("fecha_dt")))

    clientes = d.groupBy("client_id", "cliente").agg(
        first("nivel").alias("nivel"),
        first("puntos_cliente").alias("puntos_cliente"),
        first("edad_cliente").alias("edad_cliente"),
        count("*").alias("total_citas"),
        sround(ssum("ingreso"), 2).alias("gasto_total"),
        sround(avg("ingreso"), 2).alias("gasto_promedio"),
        sround((count(when(col("estado") == "cancelada", True)) / count("*")) * 100, 1)
            .alias("tasa_cancelacion_pct"),
        sround(smin(col("dias_desde").cast("double")), 0).alias("dias_sin_cita"),
        sround((smax(col("dias_desde").cast("double")) -
                smin(col("dias_desde").cast("double"))) / 30.0, 2).alias("meses_activo"),
    )
    clientes = clientes.withColumn(
        "frecuencia_mensual",
        sround(col("total_citas") /
               when(col("meses_activo") < 1, lit(1.0)).otherwise(col("meses_activo")), 2)
    )
    return clientes


# ─────────────────────────────────────────────────────────────────────────────
# Prueba rápida de la capa de datos (sin Spark): python config/mongo_..._sinnulos.py
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    client, database = _connect_db()
    db = client[database]
    recs = _extract_records(db)
    client.close()
    pdf = pd.DataFrame(recs)
    print(f"\nCitas extraídas: {len(pdf)}")
    print(f"Clientes únicos: {pdf['cliente'].nunique()}  (nombres reales, no 'Cliente')")
    print(f"Barberos únicos: {pdf['barbero'].nunique()}")
    print(f"Categorías: {sorted(pdf['categoria'].unique())}")
    print(f"Estados: {sorted(pdf['estado'].unique())}")
    print(f"Niveles: {sorted(pdf['nivel'].unique())}")
    print(f"Rango fechas: {pdf['fecha'].min()} → {pdf['fecha'].max()}")
    print("\nMuestra:")
    print(pdf[["servicio", "categoria", "barbero", "cliente", "nivel",
               "precio", "estado", "dia_semana", "hora"]].head(8).to_string(index=False))
