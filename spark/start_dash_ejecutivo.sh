#!/bin/bash
SPARK_DIR="/mnt/c/Users/luis1/Desktop/BarberPro-Python/spark"
cd "$SPARK_DIR"
"$SPARK_DIR/.venv/bin/streamlit" run analytics/dashboard_ejecutivo.py \
    --server.port 8502 --server.headless true \
    > "$SPARK_DIR/dash_ejecutivo.log" 2>&1 &
echo "PID: $!"
sleep 12
cat "$SPARK_DIR/dash_ejecutivo.log"
