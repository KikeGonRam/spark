#!/bin/bash
# ============================================================
# UrbanBlade – Script de ejecución en WSL Ubuntu
# Uso: ./run.sh <script>
# Ejemplos:
#   ./run.sh generar        → Inserta 2000 citas de prueba en MongoDB
#   ./run.sh mapreduce      → Unidad II: MapReduce ETL
#   ./run.sh kmeans         → Unidad IV: Clustering KMeans
#   ./run.sh regresion      → Unidad III: 6 modelos de regresión
#   ./run.sh arbol          → Unidad III: Árbol de Decisión
#   ./run.sh bosque         → Unidad III: Bosque Aleatorio
#   ./run.sh pca            → Unidad IV: PCA + KMeans
#   ./run.sh redneuronal    → Unidad III/IV: Red Neuronal PyTorch
#   ./run.sh dash-kmeans    → Unidad V: Dashboard KMeans (Streamlit)
#   ./run.sh dash-regresion → Unidad V: Dashboard Regresión (Streamlit)
#   ./run.sh dash-pca       → Unidad V: Dashboard PCA (Streamlit)
# ============================================================

SPARK_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SPARK_DIR/.venv"
PYTHON="$VENV/bin/python3"
SPARK_HOME="$VENV/lib/python3.12/site-packages/pyspark"
SPARK_SUBMIT="$SPARK_HOME/bin/spark-submit"
STREAMLIT="$VENV/bin/streamlit"
MONGO_CONNECTOR="org.mongodb.spark:mongo-spark-connector_2.12:10.4.0"
SPARK_OPTS="--conf spark.driver.extraJavaOptions=-Dlog4j.rootCategory=ERROR,console"

export SPARK_HOME PYSPARK_PYTHON="$PYTHON"

cd "$SPARK_DIR"

if [ ! -f "$PYTHON" ]; then
    echo "ERROR: Venv no encontrado. Ejecuta:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/python3 -m ensurepip --upgrade"
    echo "  .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Inicia MongoDB local en WSL si no está corriendo
if ! nc -z localhost 27017 2>/dev/null; then
    echo "Iniciando MongoDB local..."
    mkdir -p /tmp/mongodb-data
    mongod --dbpath /tmp/mongodb-data --port 27017 --fork --logpath /tmp/mongod.log 2>/dev/null || \
        nohup mongod --dbpath /tmp/mongodb-data --port 27017 --logpath /tmp/mongod.log &
    sleep 3
fi

case "$1" in
    generar)
        echo "=== Generando 2000 citas UrbanBlade en MongoDB ==="
        $PYTHON data_ingestion/generar_datos_urbanblade.py
        ;;
    mapreduce)
        echo "=== Unidad II – MapReduce ETL ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/01_mapreduce.py
        ;;
    kmeans)
        echo "=== Unidad IV – Clustering KMeans ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/02_kmeans.py
        ;;
    regresion)
        echo "=== Unidad III – Regresión (6 modelos) ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/03_regresion_analytics.py
        ;;
    arbol)
        echo "=== Unidad III – Árbol de Decisión ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/04_arboldedecision.py
        ;;
    bosque)
        echo "=== Unidad III – Bosque Aleatorio ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/05_bosque_aleatorio.py
        ;;
    pca)
        echo "=== Unidad IV – PCA + KMeans ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/06_pca.py
        ;;
    redneuronal)
        echo "=== Unidad III/IV – Red Neuronal PyTorch ==="
        $PYTHON ml_algorithms/07_red_neural.py
        ;;
    dash-kmeans)
        echo "=== Unidad V – Dashboard KMeans → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_kmeans.py
        ;;
    dash-regresion)
        echo "=== Unidad V – Dashboard Regresión → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_regresion_models.py
        ;;
    dash-pca)
        echo "=== Unidad V – Dashboard PCA → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_pca.py
        ;;
    dash-ejecutivo)
        echo "=== Dashboard Ejecutivo (TODOS los modelos) → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_ejecutivo.py
        ;;
    generar-100k)
        echo "=== Generando 100,000 citas UrbanBlade en MongoDB ==="
        $PYTHON data_ingestion/generar_datos_100k.py
        ;;
    limpieza)
        echo "=== Unidad II – Validación y Limpieza ETL ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/08_limpieza_datos.py
        ;;
    dash-limpieza)
        echo "=== Dashboard Limpieza de Datos → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_limpieza.py
        ;;
    series)
        echo "=== Unidad III – Análisis de Series de Tiempo ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/09_series_tiempo.py
        ;;
    rfm)
        echo "=== Unidad III/IV – Análisis RFM de Clientes ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/10_rfm_clientes.py
        ;;
    asociacion)
        echo "=== Unidad IV – Reglas de Asociación FP-Growth ==="
        $SPARK_SUBMIT $SPARK_OPTS --packages $MONGO_CONNECTOR ml_algorithms/11_asociacion_fpgrowth.py
        ;;
    dash-series)
        echo "=== Dashboard Series de Tiempo → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_series_tiempo.py
        ;;
    dash-rfm)
        echo "=== Dashboard RFM Clientes → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_rfm.py
        ;;
    dash-asociacion)
        echo "=== Dashboard Reglas de Asociación → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_asociacion.py
        ;;
    dash-exportar)
        echo "=== Centro de Exportación → http://localhost:8501 ==="
        $STREAMLIT run analytics/dashboard_exportar.py
        ;;
    *)
        echo "Uso: ./run.sh <comando>"
        echo ""
        echo "Comandos disponibles:"
        echo "  generar         Insertar 2000 citas en MongoDB local"
        echo "  mapreduce       Unidad II  – ETL MapReduce"
        echo "  kmeans          Unidad IV  – Clustering KMeans"
        echo "  regresion       Unidad III – 6 modelos de regresión"
        echo "  arbol           Unidad III – Árbol de Decisión"
        echo "  bosque          Unidad III – Bosque Aleatorio"
        echo "  pca             Unidad IV  – PCA + KMeans"
        echo "  redneuronal     Unidad III/IV – Red Neuronal PyTorch"
        echo "  dash-kmeans     Unidad V   – Dashboard KMeans (puerto 8501)"
        echo "  dash-regresion  Unidad V   – Dashboard Regresión (puerto 8501)"
        echo "  dash-pca        Unidad V   – Dashboard PCA (puerto 8501)"
        echo "  dash-ejecutivo  Unidad V   – Dashboard Ejecutivo completo (puerto 8501)"
        echo "  generar-100k    Insertar 100,000 citas enriquecidas en MongoDB"
        echo "  limpieza        Unidad II  – Validación y Limpieza ETL (consola)"
        echo "  dash-limpieza   Unidad II  – Dashboard Limpieza de Datos (puerto 8501)"
        echo "  series          Unidad III – Series de Tiempo (consola)"
        echo "  rfm             Unidad III/IV – Análisis RFM de Clientes (consola)"
        echo "  asociacion      Unidad IV  – Reglas de Asociación FP-Growth (consola)"
        echo "  dash-series     Unidad III – Dashboard Series de Tiempo (puerto 8501)"
        echo "  dash-rfm        Unidad III/IV – Dashboard RFM Clientes (puerto 8501)"
        echo "  dash-asociacion Unidad IV  – Dashboard Reglas de Asociación (puerto 8501)"
        echo "  dash-exportar              – Centro de Exportación CSV/JSON/Excel/PDF/Parquet/SQL"
        ;;
esac
