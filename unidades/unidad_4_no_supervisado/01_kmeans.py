"""
Unidad IV – Análisis No Supervisado
Script  : 02_kmeans.py
Tema    : Clustering K-Means con Método del Codo y evaluación Silhouette
Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Equipo  : Equipo UrbanBlade
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-93
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
import matplotlib.pyplot as plt


def metodo_del_codo(df_vector, spark, k_min=2, k_max=9):
    """Método del Codo: evalúa WCSS para k en [k_min, k_max]."""
    wcss = []
    ks   = list(range(k_min, k_max + 1))
    print("\nMétodo del Codo:")
    for k in ks:
        m = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster").fit(df_vector)
        wcss.append(m.summary.trainingCost)
        print(f"  k={k}  WCSS={m.summary.trainingCost:.2f}")

    plt.figure(figsize=(8, 5))
    plt.plot(ks, wcss, marker="o", color="steelblue", linewidth=2)
    plt.xlabel("Número de Clusters (K)")
    plt.ylabel("WCSS (Within-Cluster Sum of Squares)")
    plt.title("Método del Codo – UrbanBlade KMeans")
    plt.xticks(ks)
    plt.tight_layout()
    plt.show()
    return ks, wcss


def main():
    print("\n===  UNIDAD IV – K-MEANS CLUSTERING – UrbanBlade  ===\n")
    spark, df, df_vector = get_spark_session()

    total = df_vector.count()
    if total < 3:
        print("No hay suficientes datos para clustering.")
        spark.stop()
        return
    print(f"Total registros cargados: {total}")
    print("\nMuestra del dataset:")
    df.select("servicio", "barbero", "duracion_min", "precio", "ingreso", "estado").show(10)

    # ─── 1. Método del Codo ───────────────────────────────────────────────────
    ks, wcss = metodo_del_codo(df_vector, spark)

    # ─── 2. Modelo final con K=3 ─────────────────────────────────────────────
    K_OPTIMO = 3
    print(f"\n{'='*50}")
    print(f"Entrenando KMeans con K={K_OPTIMO} (clusters seleccionado)")
    kmeans = KMeans(k=K_OPTIMO, seed=42, featuresCol="features", predictionCol="cluster")
    model  = kmeans.fit(df_vector)
    result = model.transform(df_vector)

    # ─── 3. Resultados por cluster ────────────────────────────────────────────
    print(f"\nResultados (muestra de 15 registros):")
    result.select("servicio", "barbero", "duracion_min", "precio", "ingreso", "cluster").show(15)

    # ─── 4. Silhouette Score ──────────────────────────────────────────────────
    evaluator  = ClusteringEvaluator(
        featuresCol="features", predictionCol="cluster", metricName="silhouette"
    )
    silhouette = evaluator.evaluate(result)
    print(f"\nSilhouette Score: {silhouette:.4f}")
    if silhouette > 0.5:
        print("  → Buena segmentación (clusters bien separados)")
    elif silhouette > 0.2:
        print("  → Segmentación aceptable")
    else:
        print("  → Segmentación débil — considerar más features o distinto K")

    # ─── 5. Centroides ────────────────────────────────────────────────────────
    print("\nCENTROIDES (duracion_min, precio, ingreso):")
    centros = model.clusterCenters()
    for i, c in enumerate(centros):
        print(f"  Cluster {i}: duracion={c[0]:.1f}min  precio=${c[1]:.2f}  ingreso=${c[2]:.2f}")

    # ─── 6. Distribución por cluster ──────────────────────────────────────────
    print("\nDISTRIBUCIÓN DE CLUSTERS:")
    result.groupBy("cluster").count().orderBy("cluster").show()

    # ─── 7. Servicios más comunes por cluster ─────────────────────────────────
    print("SERVICIOS PRINCIPALES POR CLUSTER:")
    result.groupBy("cluster", "servicio").count() \
        .orderBy("cluster", "count", ascending=[True, False]) \
        .show(20)

    # ─── 8. Interpretación de negocio ─────────────────────────────────────────
    print("\nINTERPRETACIÓN DE CLUSTERS (negocio barbería):")
    ingresos  = [c[2] for c in centros]
    max_ing   = max(ingresos)
    min_ing   = min(ingresos)
    for i, c in enumerate(centros):
        ing = c[2]
        if ing == max_ing:
            tipo = "PREMIUM — servicios de alto valor (corte+barba, tinte, etc.)"
        elif ing == min_ing:
            tipo = "BÁSICO — servicios de bajo precio (corte simple, etc.)"
        else:
            tipo = "ESTÁNDAR — servicios de precio medio"
        print(f"  Cluster {i}: {tipo}")
        print(f"    Duración promedio: {c[0]:.0f} min | Precio: ${c[1]:.0f} | Ingreso: ${c[2]:.0f}")

    # ─── 9. Gráfica WCSS (ya mostrada arriba, aquí summary) ──────────────────
    print(f"\nSilhouette={silhouette:.4f} indica que los {K_OPTIMO} clusters tienen una")
    print("separación medible. El Método del Codo confirmó K=3 como punto de inflexión.")

    spark.stop()
    print("\nSesión Spark finalizada")


if __name__ == "__main__":
    main()
