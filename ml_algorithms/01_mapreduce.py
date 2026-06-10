import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion import get_spark_session
from pyspark.sql.functions import sum

spark, df, _ = get_spark_session()

print("\n")
print("=== MAPREDUCE – INGRESOS POR SERVICIO UrbanBlade ===")
print("\n")

# MAP → agrupa por servicio
# REDUCE → suma ingresos
df.groupBy("servicio") \
  .agg(sum("ingreso").alias("total_ingreso")) \
  .orderBy("total_ingreso", ascending=False) \
  .show()

spark.stop()
