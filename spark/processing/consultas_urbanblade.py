"""
Consultas y utilidades de procesamiento – UrbanBlade
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.sql.functions import sum, avg, count, col


def resumen_por_barbero():
    """Ingresos y citas por barbero."""
    spark, df, _ = get_spark_session()
    df.groupBy("barbero").agg(
        sum("ingreso").alias("ingreso_total"),
        count("*").alias("total_citas"),
        avg("precio").alias("precio_promedio")
    ).orderBy("ingreso_total", ascending=False).show()
    spark.stop()


def resumen_por_servicio():
    """Ingresos totales por tipo de servicio."""
    spark, df, _ = get_spark_session()
    df.groupBy("servicio").agg(
        sum("ingreso").alias("ingreso_total"),
        count("*").alias("total_citas")
    ).orderBy("ingreso_total", ascending=False).show()
    spark.stop()


def citas_por_estado():
    """Distribución de citas por estado."""
    spark, df, _ = get_spark_session()
    df.groupBy("estado").count().show()
    spark.stop()


if __name__ == "__main__":
    print("\n=== RESUMEN POR BARBERO ===")
    resumen_por_barbero()
    print("\n=== RESUMEN POR SERVICIO ===")
    resumen_por_servicio()
    print("\n=== CITAS POR ESTADO ===")
    citas_por_estado()
