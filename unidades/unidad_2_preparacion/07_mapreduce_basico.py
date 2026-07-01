import sys
import os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.sql.functions import sum

spark, df, _ = get_spark_session()

print("\n")
print("=== MAPREDUCE – INGRESOS POR SERVICIO UrbanBlade ===")
print("\n")

# MAP → agrupa por servicio
# REDUCE → suma ingresos reales (precio_cobrado)
df.groupBy("servicio") \
  .agg(sum("ingreso").alias("total_ingreso")) \
  .orderBy("total_ingreso", ascending=False) \
  .show()

spark.stop()
