import sys
import os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.sql.functions import sum, avg, count
import matplotlib.pyplot as plt


def interpretar_mapreduce(resumen_df):
    resumen_pd = resumen_df.toPandas()
    print("\nINTERPRETACIÓN AUTOMÁTICA MAPREDUCE – UrbanBlade\n")
    max_ingreso = resumen_pd["ingreso_total"].max()
    max_citas   = resumen_pd["numero_citas"].max()

    for _, row in resumen_pd.iterrows():
        servicio = row["servicio"]
        ingreso  = round(row["ingreso_total"], 2)
        citas    = row["numero_citas"]
        duracion = round(row["duracion_promedio"], 1)
        print(f"Servicio: {servicio}")
        print(f"  Ingreso Total: ${ingreso:,.2f}")
        print(f"  Citas Totales: {citas}")
        print(f"  Duración Promedio: {duracion} min")
        if ingreso == max_ingreso:
            print("  → Servicio Estrella (Mayor ingreso)")
        elif citas == max_citas:
            print("  → Servicio de Alta Rotación")
        else:
            print("  → Servicio Secundario")
        print()


def graficar_ingresos(resumen_df):
    pdf = resumen_df.toPandas()
    plt.figure(figsize=(10, 6))
    plt.bar(pdf["servicio"], pdf["ingreso_total"], color="gold")
    plt.xlabel("Servicio")
    plt.ylabel("Ingreso Total ($)")
    plt.title("Ingreso Total por Servicio – UrbanBlade")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def graficar_citas(resumen_df):
    pdf = resumen_df.toPandas()
    plt.figure(figsize=(10, 6))
    plt.bar(pdf["servicio"], pdf["numero_citas"], color="steelblue")
    plt.xlabel("Servicio")
    plt.ylabel("Número de Citas")
    plt.title("Citas por Servicio – UrbanBlade")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main():
    spark, df, _ = get_spark_session()
    print("\nEJECUTANDO MAPREDUCE AVANZADO – UrbanBlade\n")

    df = df.fillna({"servicio": "SIN_CLASIFICAR"})

    resumen = df.groupBy("servicio").agg(
        sum("ingreso").alias("ingreso_total"),
        avg("precio").alias("precio_promedio"),
        avg("duracion_min").alias("duracion_promedio"),
        count("*").alias("numero_citas")
    )
    resumen.show()

    interpretar_mapreduce(resumen)
    graficar_ingresos(resumen)
    graficar_citas(resumen)

    spark.stop()


if __name__ == "__main__":
    main()
