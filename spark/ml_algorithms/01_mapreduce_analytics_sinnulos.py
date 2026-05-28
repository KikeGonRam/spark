import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum, avg, count
import matplotlib.pyplot as plt


def interpretar_mapreduce(resumen_df):
    resumen_pd = resumen_df.toPandas()
    print("\nINTERPRETACIÓN AUTOMÁTICA MAPREDUCE – UrbanBlade\n")
    max_ingreso  = resumen_pd["ingreso_total"].max()
    max_cantidad = resumen_pd["cantidad_total"].max()

    for _, row in resumen_pd.iterrows():
        servicio = row["servicio"]
        ingreso  = round(row["ingreso_total"], 2)
        cantidad = row["cantidad_total"]
        print(f"Servicio: {servicio}")
        print(f"  Ingreso Total: ${ingreso:,.2f}")
        print(f"  Citas Totales: {cantidad}")
        if ingreso == max_ingreso:
            print("  → Servicio Estrella (Mayor ingreso)")
        elif cantidad == max_cantidad:
            print("  → Servicio de Alta Rotación")
        else:
            print("  → Servicio Secundario")
        print()


def graficar_ingresos(resumen_df):
    pdf = resumen_df.toPandas()
    plt.figure(figsize=(10, 6))
    plt.bar(pdf["servicio"], pdf["ingreso_total"], color="#d4af37")
    plt.xlabel("Servicio")
    plt.ylabel("Ingreso Total ($)")
    plt.title("Ingreso Total por Servicio – UrbanBlade")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main():
    spark, df, _ = get_spark_session()
    print("\nEJECUTANDO MAPREDUCE AVANZADO – UrbanBlade\n")

    df = df.fillna({"servicio": "SIN_CLASIFICAR"})

    resumen = df.groupBy("servicio").agg(
        sum("ingreso").alias("ingreso_total"),
        sum("cantidad").alias("cantidad_total"),
        avg("precio").alias("precio_promedio"),
        count("*").alias("numero_citas")
    )
    resumen.show()

    interpretar_mapreduce(resumen)
    graficar_ingresos(resumen)

    spark.stop()


if __name__ == "__main__":
    main()
