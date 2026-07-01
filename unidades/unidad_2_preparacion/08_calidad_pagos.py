"""
Unidad II — Script 08: Calidad de datos — Pagos y horarios de negocio

Usa 2 colecciones reales que antes NO se explotaban:
  - `payments`             (11,016 documentos)
  - `barbershop_settings`  (1 documento: horario oficial de apertura/cierre)

Objetivo (control de calidad, tema de la Unidad II):
  1. Reconciliar: ¿toda cita completada tiene su pago registrado?
  2. ¿Todas las citas ocurren dentro del horario oficial del negocio?
  3. Distribución de métodos de pago y quién procesa los cobros.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session, get_pagos_df, _connect_db

print("\n" + "=" * 60)
print("CALIDAD DE DATOS — PAGOS Y HORARIOS DE NEGOCIO")
print("=" * 60)

spark, df, _ = get_spark_session()

# ── 1. Reconciliación: citas completadas vs pagos registrados ─────────────────
client, database = _connect_db()
db = client[database]
n_completadas = db["appointments"].count_documents({"estado": "completada"})
apt_pagados = set(str(p["appointment_id"]) for p in db["payments"].find({}, {"appointment_id": 1}))
completadas = list(db["appointments"].find({"estado": "completada"}, {"_id": 1}))
sin_pago = sum(1 for a in completadas if str(a["_id"]) not in apt_pagados)
settings = db["barbershop_settings"].find_one() or {}
client.close()

print(f"\nCitas completadas: {n_completadas}")
print(f"Citas completadas SIN pago registrado: {sin_pago} "
      f"({sin_pago/n_completadas*100:.1f}%)")
if sin_pago == 0:
    print("  -> Integridad OK: toda cita completada tiene su pago reconciliado.")
else:
    print("  -> ALERTA de calidad: revisar el flujo de cobro en esos casos.")

# ── 2. Horario oficial vs horas reales de las citas ────────────────────────────
apertura = settings.get("horario_apertura", "09:00")
cierre   = settings.get("horario_cierre", "21:00")
print(f"\nHorario oficial del negocio: {apertura} - {cierre}")

from pyspark.sql.functions import col
h_ini = int(apertura.split(":")[0])
h_fin = int(cierre.split(":")[0])
fuera_horario = df.filter((col("hora") < h_ini) | (col("hora") >= h_fin)).count()
total = df.count()
print(f"Citas fuera del horario oficial: {fuera_horario} ({fuera_horario/total*100:.1f}%)")
if fuera_horario == 0:
    print("  -> Todas las citas respetan el horario configurado (buena calidad de datos).")

politica = settings.get("politica_cancelacion", "24")
print(f"Política de cancelación configurada: {politica} horas de anticipación")

# ── 3. Métodos de pago y quién los procesa ─────────────────────────────────────
print("\n" + "=" * 60)
print("MÉTODOS DE PAGO Y PROCESAMIENTO")
print("=" * 60)
pagos_df = get_pagos_df(spark)
if pagos_df is not None:
    print("\nDistribución por método de pago:")
    pagos_df.groupBy("metodo_pago").count().orderBy("count", ascending=False).show()

    print("Quién procesa los cobros:")
    pagos_df.groupBy("procesado_por").count().orderBy("count", ascending=False).show()

    print("Propinas registradas:")
    from pyspark.sql.functions import sum as ssum, avg
    pagos_df.agg(
        ssum("propina").alias("propina_total"),
        avg("propina").alias("propina_promedio")
    ).show()

    n_metodos = pagos_df.select("metodo_pago").distinct().count()
    n_procesadores = pagos_df.select("procesado_por").distinct().count()
    print("INTERPRETACIÓN:")
    if n_metodos == 1:
        print(f"  Un solo método de pago en uso -> oportunidad: habilitar tarjeta/transferencia")
        print("  podría capturar clientes que prefieren pago digital.")
    if n_procesadores == 1:
        print("  Todos los cobros los procesa la misma cuenta (Administrador) ->")
        print("  el sistema centraliza el cobro; los barberos no registran pagos directamente.")

spark.stop()
print("\nAnálisis de calidad de pagos y horarios completado.")
