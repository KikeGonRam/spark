#!/bin/bash
SPARK_DIR="/mnt/c/Users/luis1/Desktop/BarberPro-Python/spark"
SPARK_HOME="$SPARK_DIR/.venv/lib/python3.12/site-packages/pyspark"
PYSPARK_PYTHON="$SPARK_DIR/.venv/bin/python3"
export SPARK_HOME PYSPARK_PYTHON SPARK_SUBMIT_OPTS="-Dlog4j.rootCategory=ERROR,console"

cd "$SPARK_DIR"
echo "=== TEST MAPREDUCE – UrbanBlade ==="
"$SPARK_HOME/bin/spark-submit" \
    --conf spark.driver.extraJavaOptions="-Dlog4j.rootCategory=ERROR,console" \
    --packages org.mongodb.spark:mongo-spark-connector_2.12:10.4.0 \
    ml_algorithms/01_mapreduce.py 2>/tmp/spark_stderr.log
echo "--- stderr (errores) ---"
grep -v 'INFO\|WARN\|MongoClient\|MongoClientSettings\|clusterSettings\|connectionPool\|serverSettings\|sslSettings\|socketSettings' /tmp/spark_stderr.log | tail -10
