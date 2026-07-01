"""
Unidad II — Script 09: Programa de fidelización (puntos de lealtad)

Usa la colección real `loyalty_transactions` (11,016 documentos, antes sin usar)
para analizar el sistema de puntos: quién gana más puntos, tendencia mensual y
su relación con el nivel de cliente (regular vs VIP).

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session, get_loyalty_df
from pyspark.sql.functions import col, count, sum as ssum, avg, round as sround

print("\n" + "=" * 60)
print("PROGRAMA DE FIDELIZACIÓN — UrbanBlade")
print("=" * 60)

spark, _, _ = get_spark_session()
loy = get_loyalty_df(spark)

if loy is None:
    print("Sin transacciones de lealtad registradas.")
    spark.stop()
    raise SystemExit

n_tx = loy.count()
print(f"\nTransacciones de lealtad: {n_tx}")
print("Tipos de transacción registrados:")
loy.groupBy("tipo").agg(count("*").alias("n"), ssum("puntos").alias("puntos_totales")).show()

# ── Top clientes por puntos acumulados ─────────────────────────────────────────
print("Top 10 clientes por puntos acumulados:")
top = (loy.groupBy("cliente", "nivel")
          .agg(ssum("puntos").alias("puntos_totales"), count("*").alias("transacciones"))
          .orderBy(col("puntos_totales").desc()))
top.show(10, truncate=False)

# ── Puntos por nivel de cliente (regular vs VIP) ───────────────────────────────
print("Puntos promedio por nivel de cliente:")
por_nivel = loy.groupBy("cliente", "nivel").agg(ssum("puntos").alias("puntos_totales"))
por_nivel.groupBy("nivel").agg(
    sround(avg("puntos_totales"), 1).alias("puntos_promedio"),
    count("*").alias("clientes")
).orderBy(col("puntos_promedio").desc()).show()

# ── Tendencia mensual de puntos otorgados ──────────────────────────────────────
print("Tendencia mensual de puntos otorgados:")
loy.filter(col("anio") > 0).groupBy("anio", "mes").agg(
    ssum("puntos").alias("puntos_del_mes"),
    count("*").alias("citas_que_generaron_puntos")
).orderBy("anio", "mes").show(24)

# ── Interpretación ──────────────────────────────────────────────────────────────
niveles_pd = por_nivel.groupBy("nivel").agg(sround(avg("puntos_totales"), 1).alias("prom")).toPandas()
print("INTERPRETACIÓN:")
if len(niveles_pd) >= 2:
    vip = niveles_pd[niveles_pd["nivel"] == "vip"]["prom"]
    reg = niveles_pd[niveles_pd["nivel"] == "regular"]["prom"]
    if len(vip) and len(reg):
        ratio = float(vip.iloc[0]) / float(reg.iloc[0]) if float(reg.iloc[0]) > 0 else 0
        print(f"  Los clientes VIP acumulan {ratio:.1f}x más puntos que los regulares "
              f"-> el sistema de niveles refleja correctamente el consumo real.")
print("  Todas las transacciones registradas son de tipo 'ganado' (aún no hay canjes) ->")
print("  oportunidad de negocio: activar la redención de puntos por servicios/productos")
print("  para aumentar la percepción de valor del programa de lealtad.")

spark.stop()
print("\nAnálisis de fidelización completado.")
