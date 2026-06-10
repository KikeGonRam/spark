# UrbanBlade — Spark / PySpark Data Lab

Directorio de análisis de datos, exportaciones y predicciones con **Apache Spark** vía **PySpark**.  
El entorno corre íntegramente dentro de **WSL Ubuntu 24.04**.

---

## Stack

| Componente | Versión |
|---|---|
| OS (WSL) | Ubuntu 24.04.4 LTS |
| Java | OpenJDK 11.0.31 |
| Python | 3.11.15 |
| PySpark | 3.5.1 |
| Conda | 26.3.2 (Miniconda3) |
| Jupyter | notebook + JupyterLab |

---

## Cómo entrar al entorno

### 1 — Abrir WSL

Desde **PowerShell** o **Terminal de Windows**:

```powershell
wsl -d Ubuntu
```

O simplemente abre la app **Ubuntu** desde el menú de inicio.

### 2 — Ir al directorio spark

```bash
cd ~/spark
```

> En Windows el mismo directorio es accesible como:  
> `\\wsl.localhost\Ubuntu\home\luis1\spark`

### 3 — Activar el entorno conda

```bash
conda activate spark_env
```

Verás el prompt cambiar a:

```
(spark_env) luis1@...:~/spark$
```

### 4 — Verificar que todo funciona

```bash
python -c "import pyspark; print('PySpark OK:', pyspark.__version__)"
```

Salida esperada:
```
PySpark OK: 3.5.1
```

---

## Iniciar Jupyter Notebook

```bash
conda activate spark_env
cd ~/spark
jupyter notebook --no-browser --port=8888
```

Luego abre en Windows:  
**http://localhost:8888**  
(el token se imprime en la terminal)

Para JupyterLab:

```bash
jupyter lab --no-browser --port=8888
```

---

## Sesión rápida de PySpark (REPL)

```bash
conda activate spark_env
pyspark
```

---

## Estructura del proyecto

```
spark/
├── .env                        ← Credenciales MongoDB (5 variables separadas)
├── requirements.txt
├── config/
│   ├── mongo_spark_conexion.py           ← Conexión base (con nulos)
│   └── mongo_spark_conexion_sinnulos.py  ← Conexión limpia ← USAR ESTA
├── data_ingestion/
│   └── generar_datos_urbanblade.py       ← Inserta 2000 citas de prueba
├── ml_algorithms/
│   ├── 01_mapreduce.py                   ← MapReduce por servicio
│   ├── 01_mapreduce_analytics_sinnulos.py← MapReduce con gráficas
│   ├── 02_kmeans.py                      ← Clustering KMeans
│   ├── 03_regresion_analytics.py         ← 6 modelos de regresión
│   ├── 04_arboldedecision.py             ← Árbol de Decisión
│   ├── 05_bosque_aleatorio.py            ← Random Forest Pipeline
│   ├── 06_pca.py                         ← PCA + KMeans + Plotly
│   └── 07_red_neural.py                  ← Spark → PyTorch
├── analytics/
│   ├── dashboard_kmeans.py               ← Dashboard Streamlit KMeans
│   ├── dashboard_regresion_models.py     ← Dashboard Streamlit Regresión
│   └── dashboard_pca.py                  ← Dashboard Streamlit PCA
└── data/ exports/ notebooks/ jobs/
```

---

## Configuración MongoDB

Base de datos: `barber_db` | Colección analítica: `appointments_analytics`

El `.env` tiene las **5 variables separadas** que requiere PySpark:

```env
MONGO_USER=luis
MONGO_PASSWORD=kike12369
MONGO_CLUSTER=server.qiot9hi.mongodb.net
MONGO_DB=barber_db
MONGO_COLLECTION=appointments_analytics
```

---

## Ejecución

### 1. Generar datos de prueba (una sola vez)

```bash
conda activate spark_env
cd ~/spark
python3 data_ingestion/generar_datos_urbanblade.py
```

### 2. Scripts ML

Los scripts usan PyMongo → Pandas → Spark internamente (compatible con cualquier PySpark).
Ejecutar con `python3` desde `~/spark`:

```bash
python3 ml_algorithms/01_mapreduce.py
python3 ml_algorithms/01_mapreduce_analytics_sinnulos.py
python3 ml_algorithms/02_kmeans.py
python3 ml_algorithms/03_regresion_analytics.py
python3 ml_algorithms/04_arboldedecision.py
python3 ml_algorithms/05_bosque_aleatorio.py
python3 ml_algorithms/06_pca.py
python3 ml_algorithms/07_red_neural.py
```

### 4. Dashboards Streamlit

```bash
streamlit run analytics/dashboard_kmeans.py
streamlit run analytics/dashboard_regresion_models.py
streamlit run analytics/dashboard_pca.py
```

Luego abre en Windows: **http://localhost:8501**

---

## Desactivar el entorno

```bash
conda deactivate
```

---

## Referencia rápida de comandos conda

| Acción | Comando |
|---|---|
| Activar entorno | `conda activate spark_env` |
| Desactivar | `conda deactivate` |
| Ver entornos | `conda env list` |
| Ver paquetes | `conda list` |
| Instalar paquete | `pip install <paquete>` |

---

## Variables de entorno relevantes (ya configuradas por Java 11)

```bash
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```

PySpark las detecta automáticamente — no se necesita configuración adicional.
