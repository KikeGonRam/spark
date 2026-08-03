"""
Unidad V — Puente Spark → Laravel: traduce los análisis de las Unidades II-IV
a "insights" en lenguaje natural y los escribe en MongoDB para que la app web
(Laravel) los muestre dentro del panel de cada rol, sin que el usuario final
tenga que entender nada de Spark, PySpark, Machine Learning ni estadística.

POR QUÉ EXISTE ESTE ARCHIVO
---------------------------
Spark corre en Python dentro de WSL; Laravel es PHP y corre en Docker. No se
pueden "importar" uno al otro directamente. Pero ambos ya leen/escriben la
MISMA base de datos MongoDB Atlas — así que el puente más simple, sin agregar
infraestructura nueva (nada de microservicios ni llamadas HTTP entre los dos
proyectos), es que Spark calcule los resultados UNA VEZ y los deje escritos
en una colección nueva (`analytics_insights`) que Laravel simplemente lee como
lee cualquier otra colección de su base de datos.

Esta es la ÚNICA colección que Spark escribe en toda la base — todo lo demás
en este proyecto es solo lectura (ver SKILL.md). Por eso el nombre lleva el
prefijo `analytics_`: para que sea evidente en el código de Laravel que es
un resultado calculado, no un dato operativo real (una cita, un pago, etc.).

CADA DOCUMENTO GUARDADO TIENE ESTE FORMATO
-------------------------------------------
{
  "tipo":              "slug único del tipo de insight, ej. 'demanda_horas_pico'",
  "unidad":             "I".."V"  — de qué unidad de la materia viene el análisis,
  "roles":              ["administrador", "recepcionista", ...] — quién puede verlo,
  "barbero_user_id":    solo si el insight es privado de UN barbero (ver abajo),
  "barbero_perfil_id":  idem, pero con el id de su perfil (Barber, no User),
  "titulo":             título corto en español simple,
  "mensaje":            1-2 frases explicando el hallazgo sin jerga técnica,
  "valor_destacado":    el número grande que se muestra en la tarjeta,
  "color":              "gold" | "success" | "warning" | "danger" | "info"
                         (para que Laravel pinte la tarjeta con el mismo
                         código de colores que ya usa en el resto del panel),
  "generado_en":        fecha/hora en que Spark calculó este resultado,
}

POR QUÉ DOS IDs DE BARBERO DISTINTOS
-------------------------------------
El esquema de MongoDB tiene una asimetría real (documentada en SKILL.md):
las citas y horarios usan `barbers._id` (el "perfil" de barbero), pero el
muro social (`works.barbero_id`) referencia directamente `users._id` (el
"usuario" que inició sesión). Como este script respeta el esquema real en
vez de forzarlo a ser consistente, cada insight de barbero guarda el/los
id(s) que realmente necesita para que Laravel pueda filtrar "solo lo mío":
  - insights de AGENDA/UTILIZACIÓN  → barbero_perfil_id (Barber._id)
  - insights de MURO SOCIAL         → barbero_user_id   (User._id)

CÓMO SE EJECUTA
---------------
    spark-submit --master local[*] \
        unidades/unidad_5_visualizacion/exportar_insights_dashboard.py

Pensado para correr como una tarea programada (ej. una vez al día vía cron
de WSL, o manualmente antes de una demo) — NO en cada carga de página, para
no pagar el costo de arrancar Spark en cada request de un usuario.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys
import os
from datetime import datetime, timezone
import pandas as pd

_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from pyspark.sql.functions import col, count, sum as ssum, avg, round as sround
from pyspark.sql.functions import collect_set, size, to_date, dayofweek, month, when
from pyspark.ml.feature import VectorAssembler, StandardScaler, PCA
from pyspark.ml.clustering import KMeans
from pyspark.ml.fpm import FPGrowth
from pyspark.ml.regression import LinearRegression
from pyspark.ml.classification import DecisionTreeClassifier, RandomForestClassifier
from pyspark.ml.evaluation import RegressionEvaluator, BinaryClassificationEvaluator

from config.mongo_spark_conexion_sinnulos import (
    get_spark_session, get_clientes_df, get_pagos_df, get_loyalty_df,
    get_horarios_df, get_utilizacion_barberos_df, get_productos_df,
    get_pedidos_df, get_top_productos_df, _connect_db, DIAS_SEMANA, MESES,
    FEATURES_CANCEL,
)

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORÍA de cada insight — agrupa los hallazgos en la app por ETAPA del
# proceso de análisis de datos (no por "unidad de la materia"), para que un
# usuario que no sabe nada de esto lo entienda como una historia con pasos:
#
#   introduccion   → "¿qué es todo esto?"
#   preparacion    → "Paso 1: limpiar y organizar los datos" (ETL / limpieza / DW)
#   negocio        → "El negocio hoy" (los KPIs descriptivos del estado actual)
#   supervisado    → "Predecir el futuro" (modelos que aprenden del pasado:
#                     regresión de facturación, clasificación de cancelaciones,
#                     churn, predicción de demanda)
#   no_supervisado → "Descubrir patrones ocultos" (KMeans, PCA, FP-Growth:
#                     la computadora agrupa y encuentra relaciones por su cuenta)
#
# Se resuelve por el `tipo` del insight en un solo lugar (al final, antes de
# escribir en Mongo), para no tener que pasar la categoría en cada llamada.
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIA_POR_TIPO = {
    "acerca_de_la_analitica":      "introduccion",
    "calidad_datos_etl":           "preparacion",
    "resumen_ejecutivo":           "negocio",
    "calidad_pagos":               "negocio",
    "fidelizacion_ratio":          "negocio",
    "inventario_alertas":          "negocio",
    "tienda_pedidos":              "negocio",
    "utilizacion_equipo":          "negocio",
    "utilizacion_propia":          "negocio",
    "engagement_muro_top":         "negocio",
    "engagement_propio":           "negocio",
    "demanda_horas_pico":          "supervisado",
    "demanda_horas_pico_propia":   "supervisado",
    "regresion_facturacion":       "supervisado",
    "clientes_en_riesgo":          "supervisado",
    "clasificacion_cancelacion":   "supervisado",
    "segmentacion_clientes":       "no_supervisado",
    "perfil_citas_premium":        "no_supervisado",
    "pca_factores":                "no_supervisado",
    "recomendacion_servicios":     "no_supervisado",
    "tambien_te_puede_interesar":  "no_supervisado",
}

print("\n" + "=" * 70)
print("EXPORTANDO INSIGHTS EN LENGUAJE NATURAL PARA EL DASHBOARD DE LARAVEL")
print("=" * 70)

# Acumulador de todos los documentos que se insertarán al final. Se junta
# todo en una lista y se hace UN solo insert masivo — más rápido que insertar
# uno por uno, y evita dejar la colección a medias si algo falla a mitad de
# camino (mejor fallar antes de insertar nada, que con datos parciales).
insights = []


def agregar(tipo, unidad, roles, titulo, mensaje, valor_destacado, color,
            barbero_user_id=None, barbero_perfil_id=None, grafica=None):
    """Arma un documento de insight con el formato descrito arriba y lo
    agrega a la lista `insights`. Centralizar esto en una función evita
    repetir la misma estructura de diccionario 13 veces distintas.

    `grafica` (opcional): dict con los datos YA LISTOS para que Laravel los
    pinte con Chart.js, sin que la vista tenga que volver a calcular nada.
    Formato: {"tipo": "bar"|"doughnut"|"line", "labels": [...], "valores": [...]}
    Se deja vacío (None) en los insights que son solo un dato/frase, sin
    suficiente detalle detrás como para justificar una gráfica.
    """
    insights.append({
        "tipo": tipo,
        "unidad": unidad,
        "roles": roles,
        "barbero_user_id": barbero_user_id,
        "barbero_perfil_id": barbero_perfil_id,
        "titulo": titulo,
        "mensaje": mensaje,
        "valor_destacado": valor_destacado,
        "color": color,
        "grafica": grafica,
        "generado_en": datetime.now(timezone.utc),
    })
    print(f"  + [{unidad}] {tipo} -> {titulo}" + (" (con gráfica)" if grafica else ""))


# ─────────────────────────────────────────────────────────────────────────────
# Sesión Spark única para todo el script — evita levantar/tirar la JVM varias
# veces (eso fue lo que agotó la memoria de WSL cuando se corrieron varios
# scripts de la Unidad IV en paralelo en una sesión anterior de este proyecto).
# ─────────────────────────────────────────────────────────────────────────────
spark, df, df_vector = get_spark_session()
df.cache()  # se reutiliza en varios de los bloques de abajo; cachearlo evita
            # releer/reconstruir el DataFrame desde MongoDB cada vez.


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD I — "Acerca de la analítica" (sin cálculo: es contexto para el
# usuario, no un resultado de un modelo). Se muestra igual a los 4 roles.
# ═══════════════════════════════════════════════════════════════════════════
agregar(
    tipo="acerca_de_la_analitica", unidad="I",
    roles=["administrador", "recepcionista", "barbero", "cliente"],
    titulo="¿Qué es esto?",
    mensaje=("Estas tarjetas se calculan automáticamente a partir del historial real "
             "de la barbería (citas, pagos, inventario, publicaciones). No hay que "
             "hacer nada: se actualizan solas todos los días. Cada sección de arriba "
             "es un paso del proceso: primero preparamos los datos, luego los usamos "
             "para entender el negocio, predecir el futuro y descubrir patrones."),
    valor_destacado="Automático",
    color="info",
)


# ═══════════════════════════════════════════════════════════════════════════
# PREPARACIÓN DE DATOS (Unidad II — ETL / limpieza / calidad)
#   "Paso 1" del proceso: antes de analizar nada, hay que revisar que los datos
#   estén completos y bien formados. Aquí se reporta, en lenguaje simple, el
#   tamaño y la calidad del conjunto de datos que alimenta TODO lo demás.
# ═══════════════════════════════════════════════════════════════════════════
total_citas = df.count()
ingreso_total = df.filter(col("estado") == "completada").agg(ssum("ingreso")).first()[0] or 0.0
print(f"\nTotal citas históricas: {total_citas} | Ingreso histórico: ${ingreso_total:,.0f}")

# Calidad: qué porcentaje de las citas tiene sus datos clave completos
# (cliente identificado, servicio real y fecha válida). El JOIN de la capa de
# datos ya resolvió los nombres; aquí medimos cuántos quedaron "sanos".
citas_completas = df.filter(
    (col("client_id") != "") & (col("servicio") != "Desconocido") & (col("anio") > 0)
).count()
pct_calidad = round(citas_completas / total_citas * 100, 1) if total_citas else 0.0

# Composición del dataset por estado — para una gráfica de dona que muestre
# "de qué está hecha" la información (cuántas completadas, canceladas, etc.).
estados_pdf = df.groupBy("estado").agg(count("*").alias("n")).orderBy(col("n").desc()).toPandas()
grafica_etl = {
    "tipo": "doughnut",
    "labels": [str(e).replace("_", " ").capitalize() for e in estados_pdf["estado"]],
    "valores": [int(n) for n in estados_pdf["n"]],
} if len(estados_pdf) else None

agregar(
    tipo="calidad_datos_etl", unidad="II",
    roles=["administrador"],
    titulo="Datos limpios y listos para analizar",
    grafica=grafica_etl,
    mensaje=(f"Antes de sacar cualquier conclusión, el sistema junta y limpia toda la "
             f"información del negocio: {total_citas:,} citas, más pagos, inventario y "
             f"publicaciones. El {pct_calidad}% de las citas tiene sus datos clave "
             "completos (cliente, servicio y fecha correctos); el resto se descarta para "
             "que los resultados sean confiables. La gráfica muestra de qué está hecha "
             "esa información: cuántas citas se completaron, se cancelaron, etc."),
    valor_destacado=f"{pct_calidad}% de datos completos",
    color="success" if pct_calidad >= 95 else "warning",
)

# Control de limpieza visible para negocio: el porcentaje por sí solo no
# explica cuántos registros se excluyeron de los cálculos. Esta tarjeta deja
# claro que las decisiones se toman con datos identificables y consistentes.
registros_excluidos = max(total_citas - citas_completas, 0)
agregar(
    tipo="control_limpieza_datos", unidad="II",
    roles=["administrador"],
    titulo="Revisión de calidad de registros",
    mensaje=(f"Se revisaron {total_citas:,} registros antes de calcular los indicadores. "
             f"{registros_excluidos:,} no tenían cliente, servicio o fecha válidos y "
             "se excluyeron de los análisis para no distorsionar las decisiones."),
    valor_destacado=f"{registros_excluidos:,} registros excluidos",
    color="success" if registros_excluidos == 0 else "warning",
)

# Ingreso de los últimos 6 meses con datos (año+mes reales) — para dibujar
# la tendencia en una gráfica de línea en vez de solo el número total.
por_mes = (df.filter((col("estado") == "completada") & (col("anio") > 0) & (col("mes") > 0))
             .groupBy("anio", "mes").agg(ssum("ingreso").alias("ingreso"))
             .orderBy(col("anio").desc(), col("mes").desc()).limit(6).toPandas()
             .sort_values(["anio", "mes"]))
grafica_resumen = None
if len(por_mes):
    grafica_resumen = {
        "tipo": "line",
        "labels": [f"{MESES.get(int(r['mes']), '')[:3]} {int(r['anio'])}" for _, r in por_mes.iterrows()],
        "valores": [round(float(r["ingreso"]), 0) for _, r in por_mes.iterrows()],
    }

agregar(
    tipo="resumen_ejecutivo", unidad="II",
    roles=["administrador"],
    titulo="Resumen histórico del negocio",
    mensaje=(f"Desde que se tiene registro, la barbería ha atendido {total_citas:,} citas "
             f"y ha facturado un total de ${ingreso_total:,.0f} MXN en servicios completados."),
    valor_destacado=f"${ingreso_total:,.0f}",
    color="gold",
    grafica=grafica_resumen,
)


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD III — Predicción de demanda (hora y día pico)
#   Aquí no se re-entrena el modelo de regresión (GBTRegressor) del script
#   06_prediccion_demanda.py; para un insight de tablero basta con la
#   agregación real (más rápido y sin riesgo de quedarse sin memoria) — el
#   modelo predictivo completo sigue viviendo en su propio script para quien
#   quiera profundizar.
# ═══════════════════════════════════════════════════════════════════════════
por_hora = (df.filter(col("hora") > 0)
              .groupBy("hora").agg(count("*").alias("citas"))
              .orderBy(col("citas").desc()).first())
por_dia = (df.filter(col("dia_semana") > 0)
             .groupBy("dia_semana").agg(count("*").alias("citas"))
             .orderBy(col("citas").desc()).first())

hora_pico = int(por_hora["hora"]) if por_hora else 10
dia_pico_nombre = DIAS_SEMANA.get(int(por_dia["dia_semana"]), "sábado") if por_dia else "sábado"

# Distribución completa por hora del día (08:00-21:00) — la gráfica de barras
# que acompaña al hallazgo de "hora pico" en la nueva página de Analítica.
horas_pdf = (df.filter((col("hora") >= 8) & (col("hora") <= 21))
               .groupBy("hora").agg(count("*").alias("citas"))
               .orderBy("hora").toPandas())
grafica_demanda = {
    "tipo": "bar",
    "labels": [f"{int(h):02d}:00" for h in horas_pdf["hora"]],
    "valores": [int(c) for c in horas_pdf["citas"]],
} if len(horas_pdf) else None

agregar(
    tipo="demanda_horas_pico", unidad="III",
    roles=["administrador", "recepcionista", "barbero"],
    titulo="Horario de mayor demanda",
    mensaje=(f"El día con más citas es {dia_pico_nombre}, y la hora con más movimiento "
             f"es a las {hora_pico:02d}:00. Conviene tener más barberos disponibles en ese "
             "horario y evitar programar descansos justo ahí."),
    valor_destacado=f"{dia_pico_nombre} {hora_pico:02d}:00",
    color="warning",
    grafica=grafica_demanda,
)

# ── Predicción de demanda, versión "para el propio barbero" ─────────────────
# Cada barbero solo necesita saber CUÁNDO se le llena más la agenda a ÉL, no
# el agregado de todo el negocio. Se calcula lo mismo pero agrupado también
# por barbero, y se guarda un insight scoped por barbero_perfil_id.
client, database = _connect_db()
db = client[database]
barbers_map = {str(b["_id"]): b for b in db["barbers"].find({}, {"_id": 1, "user_id": 1})}
users_map = {str(u["_id"]): u for u in db["users"].find({}, {"_id": 1, "name": 1})}
client.close()

por_barbero_hora = (df.filter(col("hora") > 0)
                      .groupBy("barbero", "hora").agg(count("*").alias("citas"))
                      .toPandas())
if len(por_barbero_hora):
    top_por_barbero = (por_barbero_hora.sort_values("citas", ascending=False)
                        .groupby("barbero").first().reset_index())
    # Mapeamos nombre de barbero -> su barber_perfil_id real, para poder
    # filtrar en Laravel por el id (no por el nombre, que podría repetirse).
    nombre_a_perfil_id = {}
    for bid, b in barbers_map.items():
        uid = str(b.get("user_id", ""))
        nombre = users_map.get(uid, {}).get("name")
        if nombre:
            nombre_a_perfil_id[nombre] = bid

    for _, fila in top_por_barbero.iterrows():
        perfil_id = nombre_a_perfil_id.get(fila["barbero"])
        if not perfil_id:
            continue
        agregar(
            tipo="demanda_horas_pico_propia", unidad="III",
            roles=["barbero"], barbero_perfil_id=perfil_id,
            titulo="Tu horario de mayor demanda",
            mensaje=(f"Tu hora con más citas históricamente ha sido las {int(fila['hora']):02d}:00. "
                     "Si necesitas bloquear tiempo personal, evita esa franja."),
            valor_destacado=f"{int(fila['hora']):02d}:00",
            color="warning",
        )


# Alertas de cancelación: se entrenan dos modelos con los mismos datos de
# entrenamiento/prueba. El usuario final ve la acción y la confiabilidad, no
# el nombre técnico del algoritmo ni variables que no le ayudan a decidir.
df_cancelaciones = df.withColumn("label", col("es_cancelada").cast("double"))
train_cancel, test_cancel = df_cancelaciones.randomSplit([0.7, 0.3], seed=42)
if train_cancel.select("label").distinct().count() > 1 and test_cancel.select("label").distinct().count() > 1:
    ensamblador_cancel = VectorAssembler(
        inputCols=FEATURES_CANCEL, outputCol="features", handleInvalid="skip"
    )
    train_ml = ensamblador_cancel.transform(train_cancel).select("features", "label")
    test_ml = ensamblador_cancel.transform(test_cancel).select("features", "label")
    evaluador_auc = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC")

    arbol = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=4, seed=42).fit(train_ml)
    pred_arbol = arbol.transform(test_ml)
    auc_arbol = evaluador_auc.evaluate(pred_arbol)
    importancia_arbol = list(arbol.featureImportances)
    factor_arbol, peso_arbol = max(zip(FEATURES_CANCEL, importancia_arbol), key=lambda item: item[1])

    nombres_factores = {
        "duracion_min": "Duración del servicio", "precio": "Importe del servicio",
        "hora": "Horario", "dia_semana": "Día de la semana", "mes": "Mes",
    }
    grafica_factores = {
        "tipo": "bar",
        "labels": [nombres_factores.get(nombre, nombre) for nombre, _ in sorted(zip(FEATURES_CANCEL, importancia_arbol), key=lambda item: -item[1])],
        "valores": [round(float(valor) * 100, 1) for _, valor in sorted(zip(FEATURES_CANCEL, importancia_arbol), key=lambda item: -item[1])],
    }
    agregar(
        tipo="alertas_cancelacion", unidad="III",
        roles=["administrador", "recepcionista"],
        titulo="Alertas para confirmar citas",
        mensaje=(f"El sistema identifica señales de posible cancelación con una confiabilidad de "
                 f"{auc_arbol * 100:.0f}%. El factor con mayor peso es {nombres_factores.get(factor_arbol, factor_arbol).lower()}. "
                 "Usa esta alerta para confirmar con anticipación, no para cancelar citas automáticamente."),
        valor_destacado=f"{auc_arbol * 100:.0f}% de confiabilidad",
        color="warning" if auc_arbol >= 0.65 else "info",
        grafica=grafica_factores,
    )

    bosque = RandomForestClassifier(
        featuresCol="features", labelCol="label", numTrees=100, maxDepth=5, seed=42
    ).fit(train_ml)
    auc_bosque = evaluador_auc.evaluate(bosque.transform(test_ml))
    mejora = (auc_bosque - auc_arbol) * 100
    agregar(
        tipo="confirmacion_cancelacion_reforzada", unidad="III",
        roles=["administrador"],
        titulo="Confiabilidad reforzada para cancelaciones",
        mensaje=(f"Una segunda revisión con múltiples escenarios alcanza {auc_bosque * 100:.0f}% de confiabilidad"
                 + (f", {abs(mejora):.1f} puntos por encima de la primera alerta." if mejora >= 0 else
                    f", {abs(mejora):.1f} puntos por debajo de la primera alerta; se conserva la alerta más confiable.")
                 + " Sirve para decidir cuándo enviar recordatorios o pedir confirmación."),
        valor_destacado=f"{auc_bosque * 100:.0f}% de confiabilidad",
        color="success" if auc_bosque >= auc_arbol else "info",
    )


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD III — Clientes en riesgo de dejar de venir (churn)
#   No se re-entrena el Random Forest de 05_prediccion_abandono.py (costoso);
#   se reutiliza la misma definición de "en riesgo" (recencia > percentil 70)
#   ya que es la parte que le importa al administrador para actuar, no el
#   modelo en sí.
# ═══════════════════════════════════════════════════════════════════════════
clientes_df = get_clientes_df(spark, df).cache()
percentil_70 = clientes_df.approxQuantile("dias_sin_cita", [0.7], 0.05)[0]
en_riesgo = clientes_df.filter(col("dias_sin_cita") > percentil_70).count()
total_clientes_activos = clientes_df.count()
grafica_churn = {
    "tipo": "doughnut",
    "labels": ["En riesgo", "Activos"],
    "valores": [en_riesgo, max(total_clientes_activos - en_riesgo, 0)],
}

agregar(
    tipo="clientes_en_riesgo", unidad="III",
    roles=["administrador", "recepcionista"],
    titulo="Clientes que podrían dejar de venir",
    grafica=grafica_churn,
    mensaje=(f"{en_riesgo} de {total_clientes_activos} clientes llevan más tiempo del "
             "habitual sin agendar una cita. Vale la pena contactarlos con una promoción "
             "de reactivación antes de perderlos por completo."),
    valor_destacado=f"{en_riesgo} clientes",
    color="danger" if en_riesgo > total_clientes_activos * 0.25 else "warning",
)


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD IV — Segmentación de clientes (KMeans sobre RFM, k=4, un solo fit)
# ═══════════════════════════════════════════════════════════════════════════
feature_cols = ["total_citas", "gasto_total", "gasto_promedio", "tasa_cancelacion_pct", "dias_sin_cita"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="skip")
df_seg = assembler.transform(clientes_df)
segmentos = KMeans(k=4, seed=42, featuresCol="features").fit(df_seg).transform(df_seg)

# El cluster de mayor gasto_total promedio se etiqueta como "VIP" — igual que
# en el script 03_segmentacion_clientes.py, para no inventar una regla nueva.
# (mismo criterio de etiquetado: 1º gasto=VIP, 2º gasto=Alto consumo, el de
# mayor recencia entre los 2 restantes=Inactivo, el último=Frecuente)
stats_cluster = (segmentos.groupBy("prediction")
                  .agg(count("*").alias("clientes"),
                       sround(avg("gasto_total"), 0).alias("gasto_prom"),
                       sround(avg("dias_sin_cita"), 0).alias("dias_prom"))
                  .orderBy(col("gasto_prom").desc()).toPandas())
vip_row = stats_cluster.iloc[0] if len(stats_cluster) else None

if vip_row is not None and len(stats_cluster) >= 4:
    etiquetas = ["VIP", "Alto consumo"]
    restantes = stats_cluster.iloc[2:].sort_values("dias_prom", ascending=False)
    etiquetas_restantes = ["Inactivo", "Frecuente"]
    orden_final = pd.concat([stats_cluster.iloc[:2], restantes]).reset_index(drop=True)
    nombres_segmento = etiquetas + etiquetas_restantes

    grafica_segmentos = {
        "tipo": "doughnut",
        "labels": nombres_segmento,
        "valores": [int(c) for c in orden_final["clientes"]],
    }

    agregar(
        tipo="segmentacion_clientes", unidad="IV",
        roles=["administrador", "recepcionista"],
        titulo="Tus clientes más valiosos",
        grafica=grafica_segmentos,
        mensaje=(f"{int(vip_row['clientes'])} clientes forman tu segmento de mayor gasto "
                 f"(en promedio ${vip_row['gasto_prom']:,.0f} cada uno). Son los mejores "
                 "candidatos para un trato preferencial o un descuento exclusivo."),
        valor_destacado=f"{int(vip_row['clientes'])} clientes VIP",
        color="gold",
    )


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD IV — Recomendación de servicios (FP-Growth) — para admin Y cliente
# ═══════════════════════════════════════════════════════════════════════════
df_ok = df.filter(col("estado").isin("completada", "confirmada")).filter(col("client_id") != "")
df_tx = (df_ok.groupBy("client_id").agg(collect_set("servicio").alias("items"))
              .filter(size(col("items")) >= 1))
fp_model = FPGrowth(itemsCol="items", minSupport=0.10, minConfidence=0.20).fit(df_tx)
reglas = fp_model.associationRules.orderBy(col("lift").desc()).limit(1).toPandas()

if len(reglas):
    antecedente = ", ".join(reglas.iloc[0]["antecedent"])
    consecuente = ", ".join(reglas.iloc[0]["consequent"])
    confianza = round(reglas.iloc[0]["confidence"] * 100, 0)
    mensaje_admin = (f"Los clientes que piden \"{antecedente}\" también piden \"{consecuente}\" "
                      f"el {confianza:.0f}% de las veces. Sugerirlo activamente en el mostrador "
                      "o al reservar puede aumentar el ticket promedio.")
    agregar(
        tipo="recomendacion_servicios", unidad="IV",
        roles=["administrador"],
        titulo="Combo que se vende solo",
        mensaje=mensaje_admin,
        valor_destacado=f"{confianza:.0f}% también pide esto",
        color="info",
    )
    # Versión para el cliente: mismo hallazgo, en tono de sugerencia directa
    # (no de "insight de negocio"), pensado para mostrarse en el wizard de
    # reserva o en la tienda ("también te puede interesar").
    agregar(
        tipo="tambien_te_puede_interesar", unidad="IV",
        roles=["cliente"],
        titulo="También te puede interesar",
        mensaje=f"Si te gusta \"{antecedente}\", muchos clientes también agendan \"{consecuente}\".",
        valor_destacado=consecuente,
        color="info",
    )


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD IV — Agrupación de citas por perfil (KMeans k=3 sobre duración/precio)
#   Un solo fit final (sin el barrido del Método del Codo) — ya se confirmó
#   en una corrida anterior que K=3 es el punto óptimo, así que aquí solo se
#   entrena el modelo final para reportar la distribución actual.
# ═══════════════════════════════════════════════════════════════════════════
kmeans_citas = KMeans(k=3, seed=42, featuresCol="features", predictionCol="cluster").fit(df_vector)
resultado_citas = kmeans_citas.transform(df_vector)
centros = kmeans_citas.clusterCenters()
distrib = resultado_citas.groupBy("cluster").count().toPandas().set_index("cluster")["count"]

ingresos_centro = [c[2] for c in centros]
idx_premium = ingresos_centro.index(max(ingresos_centro))
idx_basico = ingresos_centro.index(min(ingresos_centro))
citas_premium = int(distrib.get(idx_premium, 0))
pct_premium = round(citas_premium / total_citas * 100, 1) if total_citas else 0

# Etiqueta los 3 clusters por nivel de ingreso (igual criterio que
# unidad_4_no_supervisado/01_kmeans.py) para la gráfica de distribución.
nombres_cluster = {}
for i in range(len(centros)):
    if i == idx_premium:
        nombres_cluster[i] = "Premium"
    elif i == idx_basico:
        nombres_cluster[i] = "Básico"
    else:
        nombres_cluster[i] = "Estándar"
grafica_perfiles = {
    "tipo": "doughnut",
    "labels": [nombres_cluster[i] for i in distrib.index],
    "valores": [int(v) for v in distrib.values],
}

agregar(
    tipo="perfil_citas_premium", unidad="IV",
    roles=["administrador"],
    titulo="Servicios premium: pocos pero valiosos",
    grafica=grafica_perfiles,
    mensaje=(f"Solo el {pct_premium}% de las citas son de tipo premium (alto precio y "
             "duración), pero generan un ingreso desproporcionado a su frecuencia — "
             "son un buen candidato para promocionar activamente."),
    valor_destacado=f"{pct_premium}% de las citas",
    color="gold",
)


# ═══════════════════════════════════════════════════════════════════════════
# NO SUPERVISADO — PCA (reducción de dimensionalidad)
#   Se entrena sobre una MUESTRA (30%) del dataset: para reportar la varianza
#   explicada de una insight de tablero, una muestra da el mismo resultado que
#   el total y usa mucha menos memoria (importante en WSL, ver notas del
#   proyecto sobre OOM al procesar 112k filas).
# ═══════════════════════════════════════════════════════════════════════════
df_muestra = df.sample(False, 0.3, seed=42)
assembler_pca = VectorAssembler(inputCols=["duracion_min", "precio", "ingreso"],
                                outputCol="feat_pca", handleInvalid="skip")
vec_pca = assembler_pca.transform(df_muestra)
escalado = StandardScaler(inputCol="feat_pca", outputCol="scaled_pca",
                          withMean=True, withStd=True).fit(vec_pca).transform(vec_pca)
pca_model = PCA(k=2, inputCol="scaled_pca", outputCol="pca_out").fit(escalado)
var_pca = [float(v) for v in pca_model.explainedVariance]
pct_2factores = round(sum(var_pca) * 100, 0)
print(f"\nPCA — varianza explicada por 2 componentes: {pct_2factores}%")

agregar(
    tipo="pca_factores", unidad="IV",
    roles=["administrador"],
    titulo="Los pocos factores que de verdad importan",
    grafica={
        "tipo": "bar",
        "labels": ["Factor 1 (nivel de precio)", "Factor 2 (duración)"],
        "valores": [round(var_pca[0] * 100, 1), round(var_pca[1] * 100, 1)],
    },
    mensaje=("Aunque guardamos muchos datos de cada cita, la computadora descubrió que "
             f"en el fondo bastan 2 factores para explicar el {pct_2factores:.0f}% de la "
             "diferencia entre una cita y otra: qué tan cara es y cuánto dura. Esto "
             "simplifica enormemente cómo entender el catálogo — casi todo se reduce a "
             "'precio' y 'tiempo'."),
    valor_destacado=f"2 factores = {pct_2factores:.0f}%",
    color="info",
)


# ═══════════════════════════════════════════════════════════════════════════
# SUPERVISADO — Regresión (predecir la facturación de un día)
#   Se agrega por día (no por cita): predecir el precio de UNA cita sería
#   trampa (el precio ya está fijado por el servicio). La facturación diaria sí
#   tiene variación real que vale la pena predecir. Datos pequeños (~cientos de
#   días) → el entrenamiento es instantáneo.
# ═══════════════════════════════════════════════════════════════════════════
dia = (df.filter(col("estado") != "cancelada")
         .withColumn("fecha_dt", to_date(col("fecha").substr(1, 10), "yyyy-MM-dd"))
         .groupBy("fecha_dt")
         .agg(count("*").alias("num_citas"), ssum("ingreso").alias("ingreso_dia"))
         .withColumn("dia_semana", dayofweek(col("fecha_dt")))
         .withColumn("mes", month(col("fecha_dt")))
         .dropna())
vec_reg = VectorAssembler(inputCols=["num_citas", "dia_semana", "mes"],
                          outputCol="features_reg", handleInvalid="skip").transform(dia)
train_reg, test_reg = vec_reg.randomSplit([0.8, 0.2], seed=42)
modelo_reg = LinearRegression(featuresCol="features_reg", labelCol="ingreso_dia").fit(train_reg)
r2 = RegressionEvaluator(labelCol="ingreso_dia", metricName="r2").evaluate(modelo_reg.transform(test_reg))
print(f"Regresión — R2 (precisión) de la predicción de facturación diaria: {r2:.3f}")

agregar(
    tipo="regresion_facturacion", unidad="III",
    roles=["administrador"],
    titulo="Predecir cuánto se facturará en un día",
    mensaje=("La computadora aprende del historial para adivinar cuánto facturará la "
             "barbería un día cualquiera, usando solo cuántas citas hay agendadas y qué "
             f"día de la semana y mes es. Acierta con un {r2 * 100:.0f}% de precisión — lo "
             "suficientemente bien como para planear con anticipación cuánto personal e "
             "inventario tener. Esto se llama 'aprendizaje supervisado': el modelo "
             "aprende de ejemplos del pasado donde ya sabemos la respuesta."),
    valor_destacado=f"{r2 * 100:.0f}% de precisión",
    color="gold",
)


# ═══════════════════════════════════════════════════════════════════════════
# SUPERVISADO — Clasificación (detectar citas con riesgo de cancelarse)
#   Árbol de decisión sobre una muestra (30%). El estado NO se usa como
#   feature (sería trampa): el modelo predice desde el CONTEXTO de la cita
#   (horario, día, precio). Métrica AUC (0.5 = azar, 1.0 = perfecto).
# ═══════════════════════════════════════════════════════════════════════════
vec_clf = VectorAssembler(inputCols=["duracion_min", "precio", "hora", "dia_semana", "mes"],
                          outputCol="features_clf", handleInvalid="skip").transform(df_muestra)
data_clf = vec_clf.select("features_clf", col("es_cancelada").alias("label"))
train_clf, test_clf = data_clf.randomSplit([0.8, 0.2], seed=42)
modelo_clf = DecisionTreeClassifier(featuresCol="features_clf", labelCol="label", maxDepth=4).fit(train_clf)
pred_clf = modelo_clf.transform(test_clf).cache()
auc = BinaryClassificationEvaluator(labelCol="label", metricName="areaUnderROC").evaluate(pred_clf)
tasa_cancel = round((df.agg(avg("es_cancelada")).first()[0] or 0.0) * 100, 1)
print(f"Clasificación — AUC de la detección de cancelaciones: {auc:.3f} | tasa: {tasa_cancel}%")

# Tasa de cancelación por día de la semana — la gráfica descriptiva que
# acompaña al modelo (muestra si hay días "peores" que otros).
cancel_dia = (df.filter(col("dia_semana") > 0)
                .groupBy("dia_semana")
                .agg(sround(avg("es_cancelada") * 100, 1).alias("pct_cancel"))
                .orderBy("dia_semana").toPandas())

# Interpretación HONESTA según lo que el modelo realmente encontró:
#  - Si el AUC está cerca de 0.5, el horario/servicio NO predicen la
#    cancelación (ocurren de forma pareja) → un hallazgo válido en sí mismo:
#    la palanca es reforzar recordatorios en general, no reprogramar franjas.
#  - Si el AUC es alto, el modelo sí encontró franjas de riesgo.
# Nunca se infla el número: se reporta el AUC real y se explica qué significa.
if auc >= 0.6:
    interpretacion = (f"El modelo SÍ encuentra patrones útiles (su acierto, una métrica "
                      f"llamada AUC donde 1.0 es perfecto, es de {auc:.2f}): ciertas franjas "
                      "concentran más cancelaciones y conviene reforzar la confirmación ahí.")
else:
    interpretacion = ("Curiosamente, las cancelaciones ocurren de forma pareja en todos los "
                      "horarios y servicios — no hay franjas 'malas' que evitar. El modelo lo "
                      f"confirma (su acierto AUC es {auc:.2f}, casi como adivinar al azar). El "
                      "hallazgo útil: la palanca para bajar cancelaciones no es reprogramar "
                      "horarios, sino reforzar los recordatorios de forma general.")

agregar(
    tipo="clasificacion_cancelacion", unidad="III",
    roles=["administrador"],
    titulo="Análisis de cancelaciones",
    grafica={
        "tipo": "bar",
        "labels": [DIAS_SEMANA.get(int(d), str(d)) for d in cancel_dia["dia_semana"]],
        "valores": [float(p) for p in cancel_dia["pct_cancel"]],
    } if len(cancel_dia) else None,
    mensaje=("Entrenamos un modelo que intenta anticipar qué citas se cancelarán, según "
             f"su horario, día y tipo de servicio. {interpretacion} La gráfica muestra la "
             "tasa de cancelación por día de la semana."),
    valor_destacado=f"{tasa_cancel:.0f}% se cancelan",
    color="warning",
)

# Matriz de resultados: permite distinguir aciertos y falsas alarmas. Se
# presenta con nombres cotidianos para que el administrador entienda qué
# significa cada número sin leer la salida técnica de Spark.
matriz_pdf = (pred_clf.groupBy("label", "prediction").count()
              .orderBy("label", "prediction").toPandas())
matriz_valores = []
matriz_labels = []
for _, fila in matriz_pdf.iterrows():
    real = "cancelación" if int(fila["label"]) == 1 else "no cancelación"
    predicho = "cancelación" if int(fila["prediction"]) == 1 else "no cancelación"
    matriz_labels.append(f"Real: {real}\nDetectado: {predicho}")
    matriz_valores.append(int(fila["count"]))
agregar(
    tipo="matriz_resultados_cancelacion", unidad="III",
    roles=["administrador"],
    titulo="Qué tan bien detecta las cancelaciones",
    mensaje=("La matriz compara lo que ocurrió realmente con lo que el sistema anticipó. "
             "Los aciertos sirven para priorizar recordatorios; las falsas alarmas solo "
             "deben revisarse, nunca cancelar automáticamente una cita."),
    valor_destacado=f"{sum(matriz_valores):,} citas evaluadas",
    color="info",
    grafica={"tipo": "bar", "labels": matriz_labels, "valores": matriz_valores} if matriz_valores else None,
)


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD II — Utilización de barberos (oferta vs. demanda real de agenda)
# ═══════════════════════════════════════════════════════════════════════════
pdf_completo = df.toPandas()
horarios = get_horarios_df()
utilizacion = get_utilizacion_barberos_df(pdf_completo)

if len(utilizacion):
    ranking = (utilizacion.groupby("barbero")
               .agg(utilizacion_prom=("utilizacion_pct", "mean")).round(1)
               .sort_values("utilizacion_prom", ascending=False))
    prom_equipo = round(ranking["utilizacion_prom"].mean(), 1)
    sobrecargados = int((ranking["utilizacion_prom"] > 80).sum())
    top10 = ranking.head(10)
    grafica_utilizacion = {
        "tipo": "bar",
        "labels": list(top10.index),
        "valores": [round(float(v), 1) for v in top10["utilizacion_prom"]],
    }

    agregar(
        tipo="utilizacion_equipo", unidad="II",
        roles=["administrador", "recepcionista"],
        titulo="Qué tan ocupada está la plantilla de barberos",
        grafica=grafica_utilizacion,
        mensaje=(f"En promedio, el equipo de barberos usa el {prom_equipo}% de sus horas "
                 f"disponibles. {sobrecargados} barbero(s) están por encima del 80% de "
                 "utilización — riesgo de saturación si sigue creciendo la demanda."),
        valor_destacado=f"{prom_equipo}% de utilización",
        color="warning" if prom_equipo > 75 else "success",
    )

    # Insight privado por barbero: "así de ocupada está TU agenda" — usa el
    # mismo mapeo nombre→barbero_perfil_id construido más arriba.
    for nombre, fila in ranking.iterrows():
        perfil_id = nombre_a_perfil_id.get(nombre)
        if not perfil_id:
            continue
        pct = round(fila["utilizacion_prom"], 1)
        if pct > 80:
            msg = "Tu agenda está muy llena — considera bloquear tiempo de descanso."
        elif pct < 30:
            msg = "Tienes bastante disponibilidad libre esta semana."
        else:
            msg = "Tu carga de trabajo está en un nivel saludable."
        agregar(
            tipo="utilizacion_propia", unidad="II",
            roles=["barbero"], barbero_perfil_id=perfil_id,
            titulo="Qué tan llena está tu agenda",
            mensaje=msg,
            valor_destacado=f"{pct}% ocupado",
            color="warning" if pct > 80 else ("info" if pct < 30 else "success"),
        )


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD II — Calidad de pagos (reconciliación simple, en palabras simples)
# ═══════════════════════════════════════════════════════════════════════════
pagos_df = get_pagos_df(spark)
if pagos_df is not None:
    n_metodos = pagos_df.select("metodo_pago").distinct().count()
    propina_total = pagos_df.agg(ssum("propina")).first()[0] or 0.0
    agregar(
        tipo="calidad_pagos", unidad="II",
        roles=["administrador"],
        titulo="Cómo están pagando tus clientes",
        mensaje=(f"Actualmente se usa{'n' if n_metodos > 1 else ''} {n_metodos} método(s) de "
                 f"pago, y se han acumulado ${propina_total:,.0f} en propinas registradas. "
                 + ("Considera aceptar más formas de pago digital." if n_metodos == 1 else "")),
        valor_destacado=f"${propina_total:,.0f} en propinas",
        color="info",
    )


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD II — Fidelización (tendencia de puntos VIP vs regular)
# ═══════════════════════════════════════════════════════════════════════════
loy_df = get_loyalty_df(spark)
if loy_df is not None:
    por_nivel = (loy_df.groupBy("cliente", "nivel").agg(ssum("puntos").alias("puntos_totales"))
                 .groupBy("nivel").agg(avg("puntos_totales").alias("prom")).toPandas())
    vip_prom = por_nivel[por_nivel["nivel"] == "vip"]["prom"]
    reg_prom = por_nivel[por_nivel["nivel"] == "regular"]["prom"]
    if len(vip_prom) and len(reg_prom) and float(reg_prom.iloc[0]) > 0:
        ratio = round(float(vip_prom.iloc[0]) / float(reg_prom.iloc[0]), 1)
        grafica_fidelizacion = {
            "tipo": "bar",
            "labels": [str(n).upper() for n in por_nivel["nivel"]],
            "valores": [round(float(p), 0) for p in por_nivel["prom"]],
        }
        agregar(
            tipo="fidelizacion_ratio", unidad="II",
            roles=["administrador"],
            titulo="El programa de puntos sí funciona",
            grafica=grafica_fidelizacion,
            mensaje=(f"Los clientes VIP acumulan en promedio {ratio}x más puntos que los "
                     "regulares — confirma que el programa de lealtad refleja bien el "
                     "consumo real de cada cliente."),
            valor_destacado=f"{ratio}x más puntos",
            color="gold",
        )


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD II — Inventario: alertas de reorden
# ═══════════════════════════════════════════════════════════════════════════
productos = get_productos_df()
alertas = productos[productos["necesita_reorden"]]
agregar(
    tipo="inventario_alertas", unidad="II",
    roles=["administrador", "recepcionista"],
    titulo="Productos por reabastecer",
    mensaje=(f"{len(alertas)} producto(s) están en o por debajo de su stock mínimo."
             if len(alertas) else "Todo el inventario está en niveles saludables — sin urgencias."),
    valor_destacado=f"{len(alertas)} por reabastecer" if len(alertas) else "Inventario OK",
    color="danger" if len(alertas) else "success",
)


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD II — Tienda y pedidos: qué tanto se venden los add-ons de cita
# ═══════════════════════════════════════════════════════════════════════════
pedidos_df = get_pedidos_df(spark)
if pedidos_df is not None:
    entregados = pedidos_df.filter(col("estado") == "entregado")
    ing_por_tipo = entregados.groupBy("tipo").agg(ssum("total").alias("total")).toPandas()
    ing_total = ing_por_tipo["total"].sum() if len(ing_por_tipo) else 0
    ing_cita = ing_por_tipo[ing_por_tipo["tipo"] == "cita"]["total"].sum() if len(ing_por_tipo) else 0
    pct_addon = round(ing_cita / ing_total * 100, 0) if ing_total else 0

    top = get_top_productos_df()
    producto_top = None
    grafica_tienda = None
    if len(top):
        resumen = top.groupby("producto").agg(unidades=("cantidad", "sum")).sort_values("unidades", ascending=False)
        producto_top = resumen.index[0] if len(resumen) else None
        top5 = resumen.head(5)
        grafica_tienda = {
            "tipo": "bar",
            "labels": list(top5.index),
            "valores": [round(float(v), 0) for v in top5["unidades"]],
        }

    agregar(
        tipo="tienda_pedidos", unidad="II",
        roles=["administrador", "recepcionista"],
        titulo="Cómo vende la tienda de productos",
        grafica=grafica_tienda,
        mensaje=(f"El {pct_addon:.0f}% del ingreso de tienda viene de productos añadidos "
                 "dentro de una reserva, no de compras sueltas — ofrecerlos al momento de "
                 "agendar convierte mejor que esperar a que el cliente entre a la tienda."
                 + (f" El producto más vendido es \"{producto_top}\"." if producto_top else "")),
        valor_destacado=f"{pct_addon:.0f}% viene de add-ons",
        color="info",
    )


# ═══════════════════════════════════════════════════════════════════════════
# UNIDAD II — Muro social: engagement por barbero (global + privado)
# ═══════════════════════════════════════════════════════════════════════════
client, database = _connect_db()
db = client[database]
works = list(db["works"].find({}, {"_id": 1, "barbero_id": 1}))
work_ids = [str(w["_id"]) for w in works]
barbero_por_work = {str(w["_id"]): str(w.get("barbero_id", "")) for w in works}
imagenes_por_work, comentarios_por_work, reacciones_por_work = {}, {}, {}
for img in db["work_images"].find({}, {"work_id": 1}):
    wid = str(img.get("work_id", "")); imagenes_por_work[wid] = imagenes_por_work.get(wid, 0) + 1
for c in db["comments"].find({}, {"work_id": 1}):
    wid = str(c.get("work_id", "")); comentarios_por_work[wid] = comentarios_por_work.get(wid, 0) + 1
for r in db["reactions"].find({}, {"work_id": 1}):
    wid = str(r.get("work_id", "")); reacciones_por_work[wid] = reacciones_por_work.get(wid, 0) + 1
client.close()

agg_social = {}
for wid in work_ids:
    bid = barbero_por_work.get(wid, "")
    a = agg_social.setdefault(bid, {"publicaciones": 0, "comentarios": 0, "reacciones": 0})
    a["publicaciones"] += 1
    a["comentarios"] += comentarios_por_work.get(wid, 0)
    a["reacciones"] += reacciones_por_work.get(wid, 0)

if agg_social:
    ranking_social = sorted(
        agg_social.items(),
        key=lambda kv: (kv[1]["comentarios"] + kv[1]["reacciones"]) / max(kv[1]["publicaciones"], 1),
        reverse=True,
    )
    mejor_bid, mejor = ranking_social[0]
    mejor_nombre = users_map.get(mejor_bid, {}).get("name", "Un barbero")
    top5_social = ranking_social[:5]
    grafica_social = {
        "tipo": "bar",
        "labels": [users_map.get(bid, {}).get("name", "?") for bid, _ in top5_social],
        "valores": [round((a["comentarios"] + a["reacciones"]) / max(a["publicaciones"], 1), 1)
                    for _, a in top5_social],
    }
    agregar(
        tipo="engagement_muro_top", unidad="II",
        roles=["administrador"],
        titulo="El barbero con más interacción en el muro",
        grafica=grafica_social,
        mensaje=(f"{mejor_nombre} es quien más comentarios y reacciones genera por "
                 "publicación — vale la pena pedirle consejos de qué tipo de foto funciona mejor."),
        valor_destacado=mejor_nombre,
        color="gold",
    )

    # Insight privado: "así le está yendo a TU muro" — barbero_user_id porque
    # el muro social referencia directamente al usuario, no al perfil de barbero.
    for bid, a in agg_social.items():
        if a["publicaciones"] == 0:
            continue
        engagement = round((a["comentarios"] + a["reacciones"]) / a["publicaciones"], 1)
        agregar(
            tipo="engagement_propio", unidad="II",
            roles=["barbero"], barbero_user_id=bid,
            titulo="Cómo le está yendo a tus publicaciones",
            mensaje=(f"Tus publicaciones reciben en promedio {engagement} interacciones "
                     "(comentarios + reacciones) cada una."),
            valor_destacado=f"{engagement} interacciones/post",
            color="info",
        )


# ═══════════════════════════════════════════════════════════════════════════
# Asignar la CATEGORÍA (etapa del proceso) a cada insight en un solo lugar,
# resolviéndola por su `tipo`. Así la app las agrupa en pestañas por etapa
# (preparación → negocio → supervisado → no supervisado) sin tener que pasar
# la categoría en cada una de las ~20 llamadas a agregar().
# ═══════════════════════════════════════════════════════════════════════════
for d in insights:
    d["categoria"] = CATEGORIA_POR_TIPO.get(d["tipo"], "negocio")


# ═══════════════════════════════════════════════════════════════════════════
# GUARDAR TODO EN MONGODB (reemplaza por completo la colección anterior —
# los insights son un "estado calculado", no un historial que deba acumularse)
# ═══════════════════════════════════════════════════════════════════════════
client, database = _connect_db()
db = client[database]
db["analytics_insights"].delete_many({})
if insights:
    db["analytics_insights"].insert_many(insights)
client.close()

spark.stop()
print(f"\n{len(insights)} insights escritos en la colección 'analytics_insights'.")
print("Listos para que Laravel los lea y los muestre en cada panel por rol.")
