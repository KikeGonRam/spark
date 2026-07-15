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
    nuevas (cliente, nivel, categoria, hora, dia_semana, mes, edad_cliente,
    es_no_asistio, es_perdida).

Actualizacion (maquina de estados + tienda + social):
    - ESTADOS_VALIDOS ahora tiene 6 estados (agrega en_proceso, no_asistio).
      es_cancelada se mantiene estricto por compatibilidad; es_perdida (nuevo)
      cubre cancelada+no_asistio para "ingreso perdido" real.
    - get_pedidos_df() / get_top_productos_df(): coleccion `orders` (tienda).
    - get_publicaciones_df(): colecciones `works/work_images/comments/
      reactions` (muro de inspiracion) — antes documentadas como vacias,
      ya no lo estan.

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
ESTADOS_VALIDOS   = ["cancelada", "completada", "confirmada", "en_proceso", "no_asistio", "pendiente"]
ESTADOS_PERDIDA   = ["cancelada", "no_asistio"]  # estados que representan ingreso perdido
ESTADOS_TERMINALES = ["completada", "cancelada", "no_asistio"]  # ya no cambian de estado
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
# Helpers de resolución de nombres / fechas / tipos
# ─────────────────────────────────────────────────────────────────────────────
def _num(v, default=0.0):
    """Convierte a float valores numéricos de Mongo, incluyendo BSON Decimal128
    (usado en `products.precio_compra/precio_venta`, no soportado por float() directo)."""
    if v is None:
        return default
    if hasattr(v, "to_decimal"):   # bson.decimal128.Decimal128
        return float(v.to_decimal())
    return float(v)


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
# Resolución de nombre de barbero (usada por _extract_records, get_pagos_df,
# get_horarios_df — el campo 'nombre' no existe en `barbers`, se resuelve por
# barbers.user_id → users.name)
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_barbero(brb: dict, users_map: dict) -> str:
    nombre = brb.get("nombre")
    if nombre:
        return nombre
    uid = str(brb.get("user_id", ""))
    return users_map.get(uid, {}).get("name", "Sin nombre")


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
        return _resolve_barbero(barbers_map.get(str(bid), {}), users_map)

    def datos_cliente(cid):
        cli = clients_map.get(str(cid), {})
        uid = str(cli.get("user_id", ""))
        nombre = users_map.get(uid, {}).get("name", "Cliente")
        return {
            "cliente": nombre,
            "nivel":   str(cli.get("nivel", "regular")),
            "puntos_cliente": _num(cli.get("puntos")),
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
        precio_base    = _num(svc.get("precio"))
        precio         = _num(precio_cobrado) if precio_cobrado is not None else precio_base

        fdt   = _to_dt(apt.get("fecha"))
        estado = str(apt.get("estado", ""))

        records.append({
            # ── columnas originales (compatibilidad scripts 01–07) ──────────
            "servicio":     svc.get("nombre", "Desconocido"),
            "barbero":      nombre_barbero(apt.get("barber_id")),
            "duracion_min": _num(svc.get("duracion_min"), default=30.0),
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
            # es_cancelada: se conserva estricto (solo "cancelada") por
            # compatibilidad con scripts 01-07 que ya lo usan como target.
            "es_cancelada": 1 if estado == "cancelada" else 0,
            # es_no_asistio / es_perdida: nuevos — la maquina de estados real
            # tiene 6 estados (agrega en_proceso y no_asistio); un no-show es
            # ingreso perdido igual que una cancelacion, pero es un fenomeno
            # distinto (cliente no avisa vs. cancela con antelacion) y por eso
            # se modela aparte en vez de fusionarlo dentro de es_cancelada.
            "es_no_asistio": 1 if estado == "no_asistio" else 0,
            "es_perdida":   1 if estado in ESTADOS_PERDIDA else 0,
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
        col("es_no_asistio").cast("int"),
        col("es_perdida").cast("int"),
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
# Helper: DataFrame de PAGOS (colección `payments`, 11,016 docs) — control de calidad
# ─────────────────────────────────────────────────────────────────────────────
def get_pagos_df(spark):
    """Une `payments` con `appointments` para reconciliar cobros y detectar
    quién procesó cada pago (created_by → users.name)."""
    client, database = _connect_db()
    db = client[database]
    services_map, barbers_map, clients_map, users_map = _build_maps(db)

    apt_map = {
        str(a["_id"]): a
        for a in db["appointments"].find(
            {}, {"_id": 1, "service_id": 1, "barber_id": 1, "estado": 1, "fecha": 1})
    }
    pagos = list(db["payments"].find(
        {}, {"_id": 0, "appointment_id": 1, "monto": 1, "propina": 1,
             "metodo_pago": 1, "created_by": 1, "created_at": 1}))
    client.close()

    records = []
    for p in pagos:
        apt = apt_map.get(str(p.get("appointment_id", "")), {})
        svc = services_map.get(str(apt.get("service_id", "")), {})
        records.append({
            "servicio":     svc.get("nombre", "Desconocido"),
            "barbero":      _resolve_barbero(barbers_map.get(str(apt.get("barber_id", "")), {}), users_map),
            "monto":        _num(p.get("monto")),
            "propina":      _num(p.get("propina")),
            "metodo_pago":  str(p.get("metodo_pago", "efectivo")),
            "procesado_por": users_map.get(str(p.get("created_by", "")), {}).get("name", "Desconocido"),
            "estado_cita":  str(apt.get("estado", "")),
            "tiene_cita":   1 if apt else 0,
        })

    pdf = pd.DataFrame(records)
    return spark.createDataFrame(pdf) if len(pdf) else None


# ─────────────────────────────────────────────────────────────────────────────
# Helper: DataFrame de FIDELIZACIÓN (colección `loyalty_transactions`, 11,016 docs)
# ─────────────────────────────────────────────────────────────────────────────
def get_loyalty_df(spark):
    """Puntos de lealtad por cliente con nombre real y fecha para análisis de tendencia."""
    client, database = _connect_db()
    db = client[database]
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1, "nivel": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    txs = list(db["loyalty_transactions"].find(
        {}, {"_id": 0, "client_id": 1, "tipo": 1, "puntos": 1, "created_at": 1}))
    client.close()

    records = []
    for t in txs:
        cli = clients_map.get(str(t.get("client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        fdt = _to_dt(t.get("created_at"))
        records.append({
            "cliente":  users_map.get(uid, {}).get("name", "Cliente"),
            "nivel":    str(cli.get("nivel", "regular")),
            "tipo":     str(t.get("tipo", "ganado")),
            "puntos":   _num(t.get("puntos")),
            "mes":      fdt.month if fdt else 0,
            "anio":     fdt.year if fdt else 0,
        })
    pdf = pd.DataFrame(records)
    return spark.createDataFrame(pdf) if len(pdf) else None


# ─────────────────────────────────────────────────────────────────────────────
# Helper: HORARIOS de barberos (colección `barber_schedules`, 175 docs = 25×7 días)
# ─────────────────────────────────────────────────────────────────────────────
def get_horarios_df():
    """DataFrame pandas (tabla pequeña) con horas disponibles por barbero y día.

    `day_of_week` en Mongo usa convención Laravel/Carbon (0=Domingo…6=Sábado);
    se convierte a ISO (1=Lunes…7=Domingo) para cruzar con `dia_semana` del resto
    del proyecto.
    """
    client, database = _connect_db()
    db = client[database]
    barbers_map = {str(b["_id"]): b for b in db["barbers"].find({}, {"_id": 1, "user_id": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    def _hhmm_to_horas(hhmmss):
        try:
            h, m, *_ = str(hhmmss).split(":")
            return int(h) + int(m) / 60.0
        except Exception:
            return 0.0

    rows = []
    for s in db["barber_schedules"].find({}):
        dow_laravel = int(s.get("day_of_week", 0))
        dia_iso = 7 if dow_laravel == 0 else dow_laravel
        trabaja = str(s.get("is_working", "False")) == "True"
        horas = max(0.0, _hhmm_to_horas(s.get("end_time")) - _hhmm_to_horas(s.get("start_time"))) if trabaja else 0.0
        rows.append({
            "barbero":          _resolve_barbero(barbers_map.get(str(s.get("barber_id", "")), {}), users_map),
            "dia_semana":       dia_iso,
            "is_working":       trabaja,
            "horas_disponibles": horas,
        })
    client.close()
    return pd.DataFrame(rows)


def get_utilizacion_barberos_df(df):
    """Compara horas DISPONIBLES (agenda) vs horas TRABAJADAS (duración real de
    citas no canceladas) por barbero y día de la semana → tasa de utilización %.

    `df` es el DataFrame principal (de `get_spark_session`); se usa su versión
    pandas ya cargada para evitar una segunda pasada por Spark.
    """
    horarios = get_horarios_df()
    if horarios.empty:
        return pd.DataFrame()

    ocupado = (df[df["estado"] != "cancelada"]
               .groupby(["barbero", "dia_semana"])["duracion_min"]
               .sum().div(60.0).reset_index()
               .rename(columns={"duracion_min": "horas_ocupadas"}))

    # nº de semanas cubiertas por el dataset (para escalar la disponibilidad semanal)
    n_semanas = max(1, (pd.to_datetime(df["fecha"].str[:10]).max()
                         - pd.to_datetime(df["fecha"].str[:10]).min()).days / 7.0)

    disp = horarios.groupby(["barbero", "dia_semana"])["horas_disponibles"].sum().reset_index()
    disp["horas_disponibles_total"] = disp["horas_disponibles"] * n_semanas

    out = disp.merge(ocupado, on=["barbero", "dia_semana"], how="left")
    out["horas_ocupadas"] = out["horas_ocupadas"].fillna(0.0)
    out["utilizacion_pct"] = (out["horas_ocupadas"] /
                              out["horas_disponibles_total"].replace(0, pd.NA) * 100).fillna(0.0).round(1)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Helper: INVENTARIO (colección `products`, 31 docs)
# ─────────────────────────────────────────────────────────────────────────────
def get_productos_df():
    """DataFrame pandas con salud de inventario, márgenes y categoría."""
    client, database = _connect_db()
    db = client[database]
    rows = []
    for p in db["products"].find({}):
        precio_compra = _num(p.get("precio_compra"))
        precio_venta  = _num(p.get("precio_venta"))
        stock_actual  = _num(p.get("stock_actual"))
        stock_minimo  = _num(p.get("stock_minimo"))
        rows.append({
            "producto":      p.get("nombre", "Sin nombre"),
            "categoria":     str(p.get("categoria", "otros")),
            # valores reales en `products.tipo`: "venta" (venta al cliente) /
            # "uso_interno" (insumo de trabajo, no se vende). Antes se
            # comparaba contra "venta_cliente"/"insumo_trabajo" (nunca
            # coincidian con ningun documento real).
            "tipo":          str(p.get("tipo", "uso_interno")),
            "precio_compra": precio_compra,
            "precio_venta":  precio_venta,
            "margen":        round(precio_venta - precio_compra, 2),
            "margen_pct":    round((precio_venta - precio_compra) / precio_compra * 100, 1) if precio_compra else 0.0,
            "stock_actual":  stock_actual,
            "stock_minimo":  stock_minimo,
            "necesita_reorden": stock_actual <= stock_minimo,
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: PEDIDOS DE TIENDA (colección `orders`) — carrito/checkout de productos
# ─────────────────────────────────────────────────────────────────────────────
def get_pedidos_df(spark):
    """Una fila por pedido de tienda. `tipo` distingue:
        'cita'   → add-on de producto comprado dentro de la reserva de una cita
        'tienda' → compra suelta en la tienda del cliente

    `items` es un array embebido de Mongo (nombre, cantidad, precio, subtotal
    por producto); aquí se resume a num_items/num_unidades por pedido — el
    detalle producto-por-producto no hace falta para los análisis agregados
    (ingresos, attach-rate, top productos se calculan aparte, ver punto 2).
    """
    client, database = _connect_db()
    db = client[database]
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1, "nivel": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    pedidos = list(db["orders"].find(
        {}, {"_id": 0, "folio": 1, "client_id": 1, "tipo": 1, "estado": 1,
             "total": 1, "items": 1, "metodo_pago": 1, "appointment_id": 1,
             "entregado_en": 1, "created_at": 1}))
    client.close()

    records = []
    for p in pedidos:
        cli = clients_map.get(str(p.get("client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        items = p.get("items") or []
        fdt = _to_dt(p.get("created_at"))
        records.append({
            "folio":        str(p.get("folio", "")),
            "cliente":      users_map.get(uid, {}).get("name", "Cliente"),
            "nivel":        str(cli.get("nivel", "regular")),
            "tipo":         str(p.get("tipo", "tienda")),
            "estado":       str(p.get("estado", "pendiente")),
            "total":        _num(p.get("total")),
            "num_items":    len(items),
            "num_unidades": sum(_num(it.get("cantidad"), 0) for it in items),
            "metodo_pago":  str(p.get("metodo_pago") or "sin_definir"),
            "es_addon_cita": 1 if p.get("appointment_id") else 0,
            "entregado":    1 if p.get("entregado_en") else 0,
            "mes":          fdt.month if fdt else 0,
            "anio":         fdt.year if fdt else 0,
        })

    pdf = pd.DataFrame(records)
    return spark.createDataFrame(pdf) if len(pdf) else None


def get_top_productos_df():
    """DataFrame pandas (una fila por producto vendido) explotando el array
    `items` de todos los pedidos entregados — para ranking de productos top.
    Aparte de `get_pedidos_df` porque el nivel de detalle es distinto
    (producto, no pedido)."""
    client, database = _connect_db()
    db = client[database]
    rows = []
    for p in db["orders"].find({"estado": "entregado"}, {"_id": 0, "items": 1, "tipo": 1}):
        for it in (p.get("items") or []):
            rows.append({
                "producto":  str(it.get("nombre", "Desconocido")),
                "cantidad":  _num(it.get("cantidad"), 0),
                "subtotal":  _num(it.get("subtotal"), 0),
                "tipo_pedido": str(p.get("tipo", "tienda")),
            })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: PUBLICACIONES SOCIALES (colecciones `works`, `work_images`,
# `comments`, `reactions`) — engagement del muro de inspiración por barbero.
#
# NOTA: en el snapshot original del proyecto estas colecciones estaban vacías
# y se documentaron como "NO usar"; ya no es el caso (contenido real sembrado),
# asi que se agrega este helper nuevo en vez de reactivar el aviso obsoleto.
# ─────────────────────────────────────────────────────────────────────────────
def get_publicaciones_df(spark):
    """Una fila por barbero con sus métricas de engagement en el muro.

    `Work.barbero_id` referencia `users._id` directamente (no `barbers._id`),
    a diferencia del resto del esquema donde las citas pasan por `barbers`.
    """
    client, database = _connect_db()
    db = client[database]
    users_map = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    works = list(db["works"].find({}, {"_id": 1, "barbero_id": 1}))
    work_ids = [str(w["_id"]) for w in works]
    barbero_por_work = {str(w["_id"]): str(w.get("barbero_id", "")) for w in works}

    imagenes_por_work = {}
    for img in db["work_images"].find({}, {"work_id": 1}):
        wid = str(img.get("work_id", ""))
        imagenes_por_work[wid] = imagenes_por_work.get(wid, 0) + 1

    comentarios_por_work, suma_rating_por_work = {}, {}
    for c in db["comments"].find({}, {"work_id": 1, "rating": 1}):
        wid = str(c.get("work_id", ""))
        comentarios_por_work[wid] = comentarios_por_work.get(wid, 0) + 1
        suma_rating_por_work[wid] = suma_rating_por_work.get(wid, 0) + _num(c.get("rating"), 0)

    reacciones_por_work = {}
    for r in db["reactions"].find({}, {"work_id": 1}):
        wid = str(r.get("work_id", ""))
        reacciones_por_work[wid] = reacciones_por_work.get(wid, 0) + 1
    client.close()

    agg = {}
    for wid in work_ids:
        bid = barbero_por_work.get(wid, "")
        a = agg.setdefault(bid, {
            "publicaciones": 0, "fotos": 0, "comentarios": 0,
            "suma_rating": 0.0, "reacciones": 0,
        })
        a["publicaciones"] += 1
        a["fotos"]         += imagenes_por_work.get(wid, 0)
        a["comentarios"]   += comentarios_por_work.get(wid, 0)
        a["suma_rating"]   += suma_rating_por_work.get(wid, 0.0)
        a["reacciones"]    += reacciones_por_work.get(wid, 0)

    records = []
    for bid, a in agg.items():
        records.append({
            "barbero":       users_map.get(bid, {}).get("name", "Sin nombre"),
            "publicaciones": a["publicaciones"],
            "fotos":         a["fotos"],
            "comentarios":   a["comentarios"],
            "rating_promedio": round(a["suma_rating"] / a["comentarios"], 2) if a["comentarios"] else 0.0,
            "reacciones":    a["reacciones"],
            "engagement_por_post": round((a["comentarios"] + a["reacciones"]) / a["publicaciones"], 2)
                                    if a["publicaciones"] else 0.0,
        })

    pdf = pd.DataFrame(records)
    return spark.createDataFrame(pdf) if len(pdf) else None


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
