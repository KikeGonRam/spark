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

Actualizacion (features de negocio P1 — gift cards, membresias, paquetes,
combos, referidos, lista de espera, rifas, reseñas, comision de barberos):
    Nueve helpers nuevos, cada uno leyendo su(s) coleccion(es) real(es) y
    resolviendo nombres via clients/barbers -> users (mismo patron que el
    resto del archivo). Campos verificados contra los modelos Eloquent reales
    en `barber/app/Models/` (fillable + casts), no inferidos de datos —
    ver el docstring de cada funcion para el modelo de origen.
        get_barberos_df()          Barber (catalogo + comision_pct)
        get_comisiones_df(df)      Barber.comision_pct x ingreso real (df ya cargado)
        get_giftcards_df()         GiftCard
        get_membresias_df()        ClientMembership + MembershipPlan
        get_membership_invoices_df()  MembershipInvoice (cobros reales, para MRR)
        get_paquetes_df()          ClientPackage + ServicePackage
        get_combos_df()            ServiceCombo + pivote combo_service
        get_referidos_df()         Referral
        get_waitlist_df()          Waitlist
        get_rifas_df()             RaffleResult
        get_resenas_df()           BarberReview (distinto del muro social)
    Todas devuelven pandas.DataFrame (nunca None) — DataFrame vacio si la
    coleccion no tiene documentos, igual que get_horarios_df()/get_productos_df().

Equipo: Equipo UrbanBlade
"""
import sys
import os
import json
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from pyspark.ml.feature import VectorAssembler
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Constantes reutilizables por todos los scripts (una sola fuente de verdad)
# ─────────────────────────────────────────────────────────────────────────────
ESTADOS_VALIDOS   = ["cancelada", "completada", "confirmada", "en_proceso", "no_asistio", "pendiente"]
ESTADOS_PERDIDA   = ["cancelada", "no_asistio"]  # estados que representan ingreso perdido
ESTADOS_TERMINALES = ["completada", "cancelada", "no_asistio"]  # ya no cambian de estado
# Estado real de Payment (barber: App\Models\Payment::ESTADO_VERIFICADO) — el
# único que representa dinero efectivamente recibido. 'pendiente_verificacion'
# es una transferencia sin revisar todavía y 'rechazado' nunca se cobró; get_pagos_df()
# los incluye a los tres para que el DataFrame sirva también de auditoría de calidad
# (cuántos pagos se rechazan, cuántos quedan sin revisar), pero cualquier suma de
# dinero (propina, monto) debe filtrar por este estado antes de sumar — mismo
# criterio que CashCloseService/PaymentController::index() en barber.
PAGO_ESTADO_VERIFICADO = "verificado"
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

# Schema explicito del DataFrame crudo (una fila por cita). Necesario para
# spark.createDataFrame() cuando `records` viene vacio (barber_db sin citas
# todavia) — Spark no puede inferir tipos de un dataset sin filas.
RAW_SCHEMA = StructType([
    StructField("servicio",       StringType(),  True),
    StructField("barbero",        StringType(),  True),
    StructField("duracion_min",   DoubleType(),  True),
    StructField("precio",         DoubleType(),  True),
    StructField("estado",         StringType(),  True),
    StructField("ingreso",        DoubleType(),  True),
    StructField("fecha",          StringType(),  True),
    StructField("cliente",        StringType(),  True),
    StructField("nivel",          StringType(),  True),
    StructField("puntos_cliente", DoubleType(),  True),
    StructField("edad_cliente",   DoubleType(),  True),
    StructField("categoria",      StringType(),  True),
    StructField("precio_base",    DoubleType(),  True),
    StructField("anio",           IntegerType(), True),
    StructField("mes",            IntegerType(), True),
    StructField("dia",            IntegerType(), True),
    StructField("dia_semana",     IntegerType(), True),
    StructField("hora",           IntegerType(), True),
    StructField("metodo_pago",    StringType(),  True),
    StructField("es_cancelada",   IntegerType(), True),
    StructField("es_no_asistio",  IntegerType(), True),
    StructField("es_perdida",     IntegerType(), True),
    StructField("client_id",      StringType(),  True),
])


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


def _items_list(raw):
    """Normaliza `orders.items`: el cast `'items' => 'array'` de Eloquent
    (laravel-mongodb) lo persiste como STRING JSON, no como arreglo BSON
    embebido — confirmado inspeccionando un documento real. Sin esto,
    iterar cada item como dict revienta con 'str' object has no attribute 'get'."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            return []
    return raw if isinstance(raw, list) else []


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


# Roles reales de `barber` (RolePermissionSeeder) autorizados a ver este
# dashboard de negocio. 'ingeniero' es el nombre real del rol en la base de
# datos (compartido con barber/frontend-urban) — aqui se presenta como
# "Analista" solo dentro de spark, sin renombrar el rol real todavia (eso
# implica tocar ~14 archivos entre barber y frontend-urban, incluido uno con
# cambios sin commitear de otra persona ahora mismo).
ROLES_AUTORIZADOS = ["administrador", "ingeniero"]


def autenticar_usuario(email: str, password: str):
    """Verifica credenciales contra la coleccion `users` real de barber
    (mismo hash bcrypt que usa Laravel Hash::make(), compatible con la
    libreria bcrypt de Python) y que el usuario tenga un rol autorizado
    (ROLES_AUTORIZADOS). Devuelve {"name", "email", "rol"} o None."""
    import bcrypt

    client, database = _connect_db()
    db = client[database]
    user = db["users"].find_one({"email": str(email).strip().lower()})
    if not user or not user.get("password"):
        client.close()
        return None

    stored_hash = user["password"].encode("utf-8")
    try:
        password_ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash)
    except ValueError:
        client.close()
        return None
    if not password_ok:
        client.close()
        return None

    role_ids = {str(r) for r in (user.get("role_id") or [])}
    nombre_por_id = {
        str(r["_id"]): r.get("name")
        for r in db["roles"].find({"name": {"$in": ROLES_AUTORIZADOS}})
    }
    client.close()

    rol_encontrado = next((nombre_por_id[rid] for rid in role_ids if rid in nombre_por_id), None)
    if rol_encontrado is None:
        return None
    return {"name": user.get("name", "Usuario"), "email": user.get("email", ""), "rol": rol_encontrado}


def google_login_url() -> str:
    """URL para iniciar el login con Google — reutiliza el OAuth de barber
    (SocialAuthController::redirect) con ?target=spark, que hace que
    barber regrese aqui en vez de a frontend-urban. No requiere una
    redirect_uri nueva en Google Cloud Console: la URL de callback
    registrada en Google no cambia, solo el destino final despues de que
    barber emite el token.

    Usa BARBER_PUBLIC_URL, NO BARBER_API_URL: este link lo abre el
    NAVEGADOR del usuario, no el proceso de Python. Dentro de Docker,
    BARBER_API_URL suele ser un nombre de servicio interno (ej. "http://web",
    solo resoluble entre contenedores) que un navegador en el host no puede
    resolver — por eso son dos variables separadas."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    base = os.getenv("BARBER_PUBLIC_URL") or os.getenv("BARBER_API_URL", "http://localhost:8000")
    return f"{base.rstrip('/')}/api/v1/auth/google/redirect?target=spark"


def verificar_google_token(token: str):
    """Verifica un token emitido por barber tras un login con Google exitoso,
    llamando a GET /api/v1/auth/me (la propia API de barber, no Mongo
    directo) — barber es la fuente de verdad de la identidad y el rol.
    Devuelve {"name", "email", "rol"} si el rol esta en ROLES_AUTORIZADOS,
    o None si el token es invalido o el rol no esta autorizado."""
    import requests

    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    base = os.getenv("BARBER_API_URL", "http://localhost:8000").rstrip("/")

    try:
        resp = requests.get(
            f"{base}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=8,
        )
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None

    user = resp.json().get("user", {})
    roles = user.get("roles") or []
    rol_encontrado = next((r for r in roles if r in ROLES_AUTORIZADOS), None)
    if rol_encontrado is None:
        return None
    return {"name": user.get("name", "Usuario"), "email": user.get("email", ""), "rol": rol_encontrado}


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
    if pandas_df.empty:
        # barber_db sin citas todavia (p.ej. tras un reseed) — sin esto, pandas
        # crea un DataFrame sin columnas (pandas_df['cliente'] revienta con
        # KeyError) y Spark tampoco puede inferir tipos de un dataset sin filas
        # ("can not infer schema from empty dataset"). Se usa RAW_SCHEMA en su
        # lugar solo en este caso — con filas reales la inferencia normal basta.
        pandas_df = pd.DataFrame(columns=[f.name for f in RAW_SCHEMA.fields])
        print("Datos reales cargados desde MongoDB: 0 citas (barber_db esta vacia)")
        df = spark.createDataFrame(pandas_df, schema=RAW_SCHEMA)
    else:
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
# Helper: COHORTES DE RETENCIÓN — plan spark-advanced-analytics-plan, Fase 1
# ─────────────────────────────────────────────────────────────────────────────
def get_cohortes_df(pdf: pd.DataFrame) -> pd.DataFrame:
    """Tabla de cohortes de retención (patrón Mixpanel/Amplitude): agrupa
    clientes por el mes de su PRIMERA cita (cohorte) y calcula qué % de esa
    cohorte tuvo al menos otra cita en cada mes siguiente. Responde "¿los
    clientes que llegan se quedan?", no solo "¿cuántos clientes tenemos?".
    100% en pandas sobre el `pdf` principal ya cargado — no consulta Mongo
    de nuevo. `pdf` es el DataFrame pandas de `get_spark_session()`/`cargar_datos()`."""
    if pdf is None or pdf.empty or "client_id" not in pdf:
        return pd.DataFrame()

    d = pdf[pdf["client_id"] != ""].copy()
    if d.empty:
        return pd.DataFrame()
    d["fecha_dt"] = pd.to_datetime(d["fecha"].str[:10], errors="coerce")
    d = d.dropna(subset=["fecha_dt"])
    if d.empty:
        return pd.DataFrame()

    d["mes_cita"] = d["fecha_dt"].dt.to_period("M")
    primera_cita = d.groupby("client_id")["mes_cita"].min().rename("cohorte")
    d = d.join(primera_cita, on="client_id")
    d["mes_desde_cohorte"] = (
        (d["mes_cita"].dt.year - d["cohorte"].dt.year) * 12
        + (d["mes_cita"].dt.month - d["cohorte"].dt.month)
    )

    tamano_cohorte = d.loc[d["mes_desde_cohorte"] == 0].groupby("cohorte")["client_id"].nunique()
    activos = (d.groupby(["cohorte", "mes_desde_cohorte"])["client_id"].nunique()
               .reset_index(name="clientes_activos"))
    activos["tamano_cohorte"] = activos["cohorte"].map(tamano_cohorte)
    activos["retencion_pct"] = (activos["clientes_activos"] / activos["tamano_cohorte"] * 100).round(1)
    activos["cohorte"] = activos["cohorte"].astype(str)
    return activos.sort_values(["cohorte", "mes_desde_cohorte"]).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: CLV PROYECTADO — plan spark-advanced-analytics-plan, Fase 1
# ─────────────────────────────────────────────────────────────────────────────
def get_clv_df(spark, df, horizonte_meses: int = 12) -> pd.DataFrame:
    """CLV (Customer Lifetime Value) proyectado con la fórmula simplificada
    estándar de e-commerce (la misma que usa el CLV básico de Shopify):
    gasto_promedio × frecuencia_mensual × horizonte_meses. Se construye
    sobre get_clientes_df() (RFM), que ya calcula gasto_promedio/
    frecuencia_mensual — no requiere datos nuevos ni consultas extra."""
    clientes = get_clientes_df(spark, df).toPandas()
    if clientes.empty:
        return clientes
    clientes[f"clv_proyectado_{horizonte_meses}m"] = (
        clientes["gasto_promedio"] * clientes["frecuencia_mensual"] * horizonte_meses
    ).round(2)
    return clientes


# ─────────────────────────────────────────────────────────────────────────────
# Helper: FORECASTING — plan spark-advanced-analytics-plan, Fase 3
# ─────────────────────────────────────────────────────────────────────────────
def get_forecast_df(pdf: pd.DataFrame, semanas_adelante: int = 4, minimo_semanas: int = 4):
    """Proyección honesta de citas/ingreso para las próximas semanas: regresión
    lineal simple (numpy.polyfit) sobre la serie semanal histórica, con banda
    de incertidumbre de ±1.96 desviaciones estándar del residuo.

    A propósito NO se usa un modelo mas complejo (ARIMA/Prophet/LSTM): con
    unos pocos meses de historial real esos modelos sobreajustarían y
    darían una falsa sensación de precisión. Una tendencia lineal simple con
    su R² visible es más honesta sobre lo que sí se puede saber con estos
    datos.

    Devuelve None si hay menos de `minimo_semanas` semanas de historial (no
    tiene sentido proyectar con casi nada de datos), o un dict:
        {"citas": {...}, "ingreso": {...}}
    donde cada entrada tiene "historico" (DataFrame fecha/valor real),
    "proyeccion" (DataFrame fecha/valor/min/max), "r2" y "tendencia_semanal"."""
    if pdf is None or pdf.empty or "fecha" not in pdf:
        return None
    d = pdf.copy()
    d["fecha_dt"] = pd.to_datetime(d["fecha"].str[:10], errors="coerce")
    d = d.dropna(subset=["fecha_dt"])
    if d.empty:
        return None
    d["ingreso_real"] = d["ingreso"].where(d["estado"] != "cancelada", 0.0)

    semanal = (d.set_index("fecha_dt")
               .resample("W")
               .agg(citas=("estado", "size"), ingreso=("ingreso_real", "sum"))
               .reset_index())
    if len(semanal) < minimo_semanas:
        return None

    resultado = {}
    x = np.arange(len(semanal), dtype=float)
    for columna in ["citas", "ingreso"]:
        y = semanal[columna].to_numpy(dtype=float)
        pendiente, intercepto = np.polyfit(x, y, 1)
        pred_hist = pendiente * x + intercepto
        residuos = y - pred_hist
        error_std = float(residuos.std(ddof=2)) if len(y) > 2 else float(residuos.std())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        ss_res = float((residuos ** 2).sum())
        r2 = round(1 - ss_res / ss_tot, 3) if ss_tot > 0 else 0.0

        x_fut = np.arange(len(semanal), len(semanal) + semanas_adelante, dtype=float)
        y_fut = pendiente * x_fut + intercepto
        banda = 1.96 * error_std
        fechas_fut = [semanal["fecha_dt"].max() + pd.Timedelta(weeks=i + 1) for i in range(semanas_adelante)]

        resultado[columna] = {
            "historico": pd.DataFrame({"fecha": semanal["fecha_dt"], "valor": y}),
            "proyeccion": pd.DataFrame({
                "fecha": fechas_fut,
                "valor": np.clip(y_fut, 0, None),
                "min": np.clip(y_fut - banda, 0, None),
                "max": y_fut + banda,
            }),
            "r2": r2,
            "tendencia_semanal": round(float(pendiente), 2),
        }
    return resultado


def get_anomalias_df(pdf: pd.DataFrame, ventana: int = 4, umbral_std: float = 1.5, minimo_semanas: int = 6) -> pd.DataFrame:
    """Detecta semanas donde citas/ingreso se desvian mas de `umbral_std`
    desviaciones estandar del promedio movil de las `ventana` semanas
    anteriores (metodo simple, honesto para el poco historial disponible --
    no un modelo estadistico complejo de deteccion de anomalias). Devuelve
    un DataFrame con una fila por semana marcada como anomalia, o vacio si
    no hay suficiente historial o no se detecto ninguna."""
    if pdf is None or pdf.empty or "fecha" not in pdf:
        return pd.DataFrame()
    d = pdf.copy()
    d["fecha_dt"] = pd.to_datetime(d["fecha"].str[:10], errors="coerce")
    d = d.dropna(subset=["fecha_dt"])
    if d.empty:
        return pd.DataFrame()
    d["ingreso_real"] = d["ingreso"].where(d["estado"] != "cancelada", 0.0)
    semanal = (d.set_index("fecha_dt")
               .resample("W")
               .agg(citas=("estado", "size"), ingreso=("ingreso_real", "sum"))
               .reset_index())
    if len(semanal) < minimo_semanas:
        return pd.DataFrame()

    filas = []
    for columna in ["citas", "ingreso"]:
        serie = semanal[columna]
        for i in range(ventana, len(semanal)):
            base = serie.iloc[i - ventana:i]
            promedio = base.mean()
            desviacion = base.std(ddof=1) if len(base) > 1 else 0.0
            actual = serie.iloc[i]
            if desviacion == 0:
                continue
            z = (actual - promedio) / desviacion
            if abs(z) >= umbral_std:
                pct = (actual - promedio) / promedio * 100 if promedio else 0.0
                filas.append({
                    "fecha": semanal["fecha_dt"].iloc[i],
                    "metrica": "Citas" if columna == "citas" else "Ingreso",
                    "valor_real": actual,
                    "valor_esperado": round(promedio, 1),
                    "desviacion_pct": round(pct, 1),
                    "z_score": round(z, 2),
                    "tipo": "arriba" if z > 0 else "abajo",
                })
    return pd.DataFrame(filas).sort_values("fecha", ascending=False) if filas else pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: DataFrame de PAGOS (colección `payments`) — control de calidad
# ─────────────────────────────────────────────────────────────────────────────
def get_pagos_df(spark):
    """Une `payments` con `appointments` para reconciliar cobros y detectar
    quién procesó cada pago (created_by → users.name).

    Incluye pagos en cualquier estado (verificado/pendiente_verificacion/
    rechazado) a propósito — es lo que hace posible la auditoría de calidad
    de 08_calidad_pagos.py (cuántos se rechazan, cuántos quedan sin
    revisar). La columna 'estado' viaja en cada registro precisamente para
    que quien sume dinero (propina, monto) pueda y deba filtrar primero por
    PAGO_ESTADO_VERIFICADO — antes esta función ni siquiera devolvía el
    estado del pago, así que un rechazo o una transferencia sin revisar
    entraban a cualquier suma de ingresos sin forma de excluirlos."""
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
             "metodo_pago": 1, "created_by": 1, "created_at": 1, "estado": 1}))
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
            # Sin PAGO_ESTADO_VERIFICADO como default: un registro con
            # 'estado' ausente es un dato dudoso, y el punto de este campo
            # es justo no contar como ingreso nada que no esté confirmado.
            "estado_pago":  str(p.get("estado", "")),
            "tiene_cita":   1 if apt else 0,
        })

    pdf = pd.DataFrame(records)
    return spark.createDataFrame(pdf) if len(pdf) else None


# ─────────────────────────────────────────────────────────────────────────────
# Helper: DataFrame de FIDELIZACIÓN (colección `loyalty_transactions`)
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
# Helper: HORARIOS de barberos (colección `barber_schedules`)
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
# Helper: INVENTARIO (colección `products`)
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
        items = _items_list(p.get("items"))
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
        for it in _items_list(p.get("items")):
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
# Helper: BARBEROS (coleccion `barbers`) — catalogo + comision configurada
# ─────────────────────────────────────────────────────────────────────────────
def get_barberos_df():
    """DataFrame pandas (tabla pequeña) con el catalogo de barberos: nombre,
    especialidad, si esta activo y su % de comision (Barber::comision_pct,
    0 si nunca se configuro — ver BarberCommissionService)."""
    client, database = _connect_db()
    db = client[database]
    users_map = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}
    rows = []
    for b in db["barbers"].find({}):
        rows.append({
            "barbero":      _resolve_barbero(b, users_map),
            "especialidad": str(b.get("especialidad", "") or ""),
            "activo":       bool(b.get("activo", True)),
            "comision_pct": _num(b.get("comision_pct"), 0.0),
        })
    client.close()
    return pd.DataFrame(rows)


def get_comisiones_df(df):
    """Comisión ganada por barbero: ingreso real (citas no canceladas) ×
    Barber.comision_pct — mismo calculo que BarberCommissionService en el
    panel admin. `df` es el DataFrame principal ya cargado (pandas, de
    `get_spark_session().toPandas()` o el propio `pdf` del dashboard) —
    se reutiliza en vez de volver a consultar Mongo."""
    barberos = get_barberos_df()
    if barberos.empty or df.empty:
        return pd.DataFrame()
    ingreso_barbero = (df[df["estado"] != "cancelada"]
                       .groupby("barbero")
                       .agg(citas=("ingreso", "size"), ingreso_total=("ingreso", "sum"))
                       .reset_index())
    out = barberos.merge(ingreso_barbero, on="barbero", how="left")
    out["citas"] = out["citas"].fillna(0).astype(int)
    out["ingreso_total"] = out["ingreso_total"].fillna(0.0)
    out["comision_ganada"] = (out["ingreso_total"] * out["comision_pct"] / 100).round(2)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Helper: GIFT CARDS (coleccion `gift_cards`) — saldo prepagado, no ligado a
# ningun servicio (a diferencia de ClientPackage)
# ─────────────────────────────────────────────────────────────────────────────
def get_giftcards_df():
    """Una fila por gift card (GiftCard::$fillable): comprador (cliente
    registrado si `comprador_client_id` resuelve, si no el nombre libre
    `comprador_nombre` de un invitado), saldo restante y consumo."""
    client, database = _connect_db()
    db = client[database]
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    rows = []
    for g in db["gift_cards"].find({}):
        cli = clients_map.get(str(g.get("comprador_client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        comprador = users_map.get(uid, {}).get("name") or g.get("comprador_nombre") or "Invitado"
        monto_inicial = _num(g.get("monto_inicial"))
        saldo = _num(g.get("saldo"))
        fdt = _to_dt(g.get("comprado_en"))
        rows.append({
            "code":          str(g.get("code", "")),
            "comprador":     comprador,
            "monto_inicial": monto_inicial,
            "saldo":         saldo,
            "monto_usado":   round(monto_inicial - saldo, 2),
            "pct_usado":     round((monto_inicial - saldo) / monto_inicial * 100, 1) if monto_inicial else 0.0,
            "metodo_pago":   str(g.get("metodo_pago", "")),
            "estado":        str(g.get("estado", "")),
            "mes":           fdt.month if fdt else 0,
            "anio":          fdt.year if fdt else 0,
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: MEMBRESÍAS (colecciones `client_memberships` + `membership_plans`
# + `membership_invoices`) — suscripcion recurrente respaldada por Stripe
# ─────────────────────────────────────────────────────────────────────────────
def get_membresias_df():
    """Una fila por suscripcion (ClientMembership), con nombre/precio/
    descuento del MembershipPlan ya resuelto."""
    client, database = _connect_db()
    db = client[database]
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1, "nivel": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}
    plans_map   = {str(p["_id"]): p for p in db["membership_plans"].find({})}

    rows = []
    for m in db["client_memberships"].find({}):
        cli = clients_map.get(str(m.get("client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        plan = plans_map.get(str(m.get("membership_plan_id", "")), {})
        rows.append({
            "cliente":               users_map.get(uid, {}).get("name", "Cliente"),
            "nivel":                 str(cli.get("nivel", "regular")),
            "plan":                  plan.get("nombre", "Desconocido"),
            "precio_mensual":        _num(plan.get("precio_mensual")),
            "descuento_pct":         _num(plan.get("descuento_pct")),
            "estado":                str(m.get("estado", "")),
            "cancelar_al_finalizar": bool(m.get("cancelar_al_finalizar", False)),
            "periodo_actual_fin":    str(m.get("periodo_actual_fin", ""))[:10],
        })
    client.close()
    return pd.DataFrame(rows)


def get_membership_invoices_df():
    """Cobros reales (alta/renovacion) de membresias — MembershipInvoice,
    para ingresos por mes (MRR). Stripe cobra estas renovaciones solo, sin
    que el staff capture nada localmente — por eso este registro existe."""
    client, database = _connect_db()
    db = client[database]
    memberships_map = {str(m["_id"]): m for m in db["client_memberships"].find(
        {}, {"_id": 1, "client_id": 1, "membership_plan_id": 1})}
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}
    plans_map   = {str(p["_id"]): p for p in db["membership_plans"].find({}, {"_id": 1, "nombre": 1})}

    rows = []
    for inv in db["membership_invoices"].find({}):
        mem = memberships_map.get(str(inv.get("client_membership_id", "")), {})
        cli = clients_map.get(str(mem.get("client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        plan = plans_map.get(str(mem.get("membership_plan_id", "")), {})
        fdt = _to_dt(inv.get("pagado_en"))
        rows.append({
            "cliente": users_map.get(uid, {}).get("name", "Cliente"),
            "plan":    plan.get("nombre", "Desconocido"),
            "monto":   _num(inv.get("monto")),
            "mes":     fdt.month if fdt else 0,
            "anio":    fdt.year if fdt else 0,
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: PAQUETES (colecciones `client_packages` + `service_packages`) — N
# usos de UN servicio prepagados, distinto de un ServiceCombo
# ─────────────────────────────────────────────────────────────────────────────
def get_paquetes_df():
    """Una fila por paquete COMPRADO (ClientPackage): servicio, usos
    totales/restantes/consumidos, precio pagado. `service_id` viene
    denormalizado en ClientPackage (copiado al comprar), no requiere pasar
    por ServicePackage para resolverlo."""
    client, database = _connect_db()
    db = client[database]
    clients_map    = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1, "nivel": 1})}
    users_map      = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}
    services_map   = {str(s["_id"]): s for s in db["services"].find({}, {"_id": 1, "nombre": 1})}
    plantillas_map = {str(p["_id"]): p for p in db["service_packages"].find({}, {"_id": 1, "nombre": 1})}

    rows = []
    for cp in db["client_packages"].find({}):
        cli = clients_map.get(str(cp.get("client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        fdt = _to_dt(cp.get("comprado_en"))
        usos_totales   = _num(cp.get("usos_totales"))
        usos_restantes = _num(cp.get("usos_restantes"))
        rows.append({
            "cliente":         users_map.get(uid, {}).get("name", "Cliente"),
            "nivel":           str(cli.get("nivel", "regular")),
            "paquete":         plantillas_map.get(str(cp.get("service_package_id", "")), {}).get("nombre", "Desconocido"),
            "servicio":        services_map.get(str(cp.get("service_id", "")), {}).get("nombre", "Desconocido"),
            "usos_totales":    usos_totales,
            "usos_restantes":  usos_restantes,
            "usos_consumidos": usos_totales - usos_restantes,
            "precio_pagado":   _num(cp.get("precio_pagado")),
            "metodo_pago":     str(cp.get("metodo_pago", "")),
            "estado":          str(cp.get("estado", "")),
            "mes":             fdt.month if fdt else 0,
            "anio":            fdt.year if fdt else 0,
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: COMBOS (coleccion `service_combos` + pivote `combo_service`) —
# catalogo de varios servicios a precio conjunto (definido por admin, no
# hay una instancia "comprada" como ClientPackage)
# ─────────────────────────────────────────────────────────────────────────────
def get_combos_df():
    """Catalogo de combos (ServiceCombo): precio conjunto, descuento y
    cuantos servicios incluye (cuenta del pivote `combo_service`, campos
    reales `combo_id`/`service_id` — ver ServiceCombo::services())."""
    client, database = _connect_db()
    db = client[database]
    conteo = {}
    for row in db["combo_service"].find({}):
        cid = str(row.get("combo_id", ""))
        conteo[cid] = conteo.get(cid, 0) + 1

    rows = []
    for c in db["service_combos"].find({}):
        rows.append({
            "combo":         str(c.get("nombre", "Desconocido")),
            "precio_combo":  _num(c.get("precio_combo")),
            "descuento":     _num(c.get("descuento")),
            "num_servicios": conteo.get(str(c["_id"]), 0),
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: REFERIDOS (coleccion `referrals`)
# ─────────────────────────────────────────────────────────────────────────────
def get_referidos_df():
    """Un renglon por referido (Referral): quien invito (referrer) a quien
    (referee) y si ya se otorgo la recompensa — solo pasa cuando el referido
    completa su PRIMERA cita, nunca por solo registrarse."""
    client, database = _connect_db()
    db = client[database]
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    def nombre_cliente(cid):
        cli = clients_map.get(str(cid), {})
        return users_map.get(str(cli.get("user_id", "")), {}).get("name", "Cliente")

    rows = []
    for r in db["referrals"].find({}):
        fdt = _to_dt(r.get("recompensa_otorgada_en"))
        rows.append({
            "referente":           nombre_cliente(r.get("referrer_client_id")),
            "referido":            nombre_cliente(r.get("referee_client_id")),
            "estado":              str(r.get("estado", "pendiente")),
            "recompensa_otorgada": fdt is not None,
            "mes":                 fdt.month if fdt else 0,
            "anio":                fdt.year if fdt else 0,
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: LISTA DE ESPERA (coleccion `waitlists`)
# ─────────────────────────────────────────────────────────────────────────────
def get_waitlist_df():
    """Un renglon por entrada en lista de espera (Waitlist): cliente,
    barbero, servicio, fecha deseada y estado (activo/notificado/reservado/
    cancelado/expirado)."""
    client, database = _connect_db()
    db = client[database]
    clients_map  = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1})}
    barbers_map  = {str(b["_id"]): b for b in db["barbers"].find({}, {"_id": 1, "user_id": 1, "nombre": 1})}
    services_map = {str(s["_id"]): s for s in db["services"].find({}, {"_id": 1, "nombre": 1})}
    users_map    = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    rows = []
    for w in db["waitlists"].find({}):
        cli = clients_map.get(str(w.get("client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        rows.append({
            "cliente":  users_map.get(uid, {}).get("name", "Cliente"),
            "barbero":  _resolve_barbero(barbers_map.get(str(w.get("barber_id", "")), {}), users_map),
            "servicio": services_map.get(str(w.get("service_id", "")), {}).get("nombre", "Desconocido"),
            "fecha":    str(w.get("fecha", ""))[:10],
            "estado":   str(w.get("estado", "")),
            "activa":   bool(w.get("activa", False)),
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: RIFAS (coleccion `raffle_results`) — sorteo mensual de lealtad
# ─────────────────────────────────────────────────────────────────────────────
def get_rifas_df():
    """Resultados del sorteo mensual (RaffleResult): quien gano que premio y
    si ya lo reclamo o caduco sin usarse (VIGENCIA_DIAS=60 desde que se gana)."""
    client, database = _connect_db()
    db = client[database]
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    now = datetime.now()
    rows = []
    for r in db["raffle_results"].find({}):
        cli = clients_map.get(str(r.get("client_id", "")), {})
        uid = str(cli.get("user_id", ""))
        reclamado = r.get("reclamado_en") is not None
        vence_en  = _to_dt(r.get("vence_en"))
        vencido   = (not reclamado) and (vence_en is not None) and (vence_en < now)
        rows.append({
            "cliente":       users_map.get(uid, {}).get("name", "Cliente"),
            "mes":           str(r.get("mes", "")),
            "premio":        str(r.get("premio", "")),
            "nivel_ganador": str(r.get("nivel_ganador", "")),
            "reclamado":     reclamado,
            "vencido":       vencido,
        })
    client.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: RESEÑAS DE BARBEROS (coleccion `barber_reviews`) — distinto del
# muro social (Work/Comment), ver get_publicaciones_df()
# ─────────────────────────────────────────────────────────────────────────────
def get_resenas_df():
    """Reseñas de clientes sobre barberos (BarberReview: rating 1-5 +
    comentario libre)."""
    client, database = _connect_db()
    db = client[database]
    barbers_map = {str(b["_id"]): b for b in db["barbers"].find({}, {"_id": 1, "user_id": 1, "nombre": 1})}
    clients_map = {str(c["_id"]): c for c in db["clients"].find({}, {"_id": 1, "user_id": 1})}
    users_map   = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}

    rows = []
    for r in db["barber_reviews"].find({}):
        cli = clients_map.get(str(r.get("client_id", "")), {})
        rows.append({
            "barbero": _resolve_barbero(barbers_map.get(str(r.get("barber_id", "")), {}), users_map),
            "cliente": users_map.get(str(cli.get("user_id", "")), {}).get("name", "Cliente"),
            "rating":  _num(r.get("rating")),
            "comment": str(r.get("comment", "") or ""),
        })
    client.close()
    return pd.DataFrame(rows)


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
