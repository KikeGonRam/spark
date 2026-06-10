import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator


def main():
    print("\n=== INICIANDO KMEANS – UrbanBlade ===\n")
    spark, df, df_vector = get_spark_session()

    total = df_vector.count()
    if total < 3:
        print("No hay suficientes datos para clustering.")
        spark.stop()
        return

    print(f"Total registros: {total}")

    kmeans = KMeans(
        k=3,
        seed=42,
        featuresCol="features",
        predictionCol="cluster"
    )
    model  = kmeans.fit(df_vector)
    result = model.transform(df_vector)

    print("\n=== RESULTADOS ===")
    result.select("servicio", "cantidad", "precio", "ingreso", "cluster").show(10)

    evaluator  = ClusteringEvaluator(
        featuresCol="features",
        predictionCol="cluster",
        metricName="silhouette"
    )
    silhouette = evaluator.evaluate(result)

    print(f"\nSilhouette Score: {round(silhouette, 4)}")

    if silhouette > 0.5:
        print("Buena segmentación")
    elif silhouette > 0.2:
        print("Segmentación aceptable")
    else:
        print("Segmentación débil")

    print("\n=== CENTROIDES ===")
    for i, center in enumerate(model.clusterCenters()):
        print(f"Cluster {i}: {center}")

    print("\n=== DISTRIBUCIÓN DE CLUSTERS ===")
    result.groupBy("cluster").count().show()

    spark.stop()


if __name__ == "__main__":
    main()
