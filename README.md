# UrbanBlade — Spark / PySpark Data Lab

Análisis de datos de barbería con **Apache Spark** / **PySpark** + **MongoDB Atlas**.  
Cubre la **Unidad II** (Preparación de datos) y **Unidad III** (Algoritmos ML) del curso BigData — UTVT.  
El entorno corre íntegramente dentro de **WSL Ubuntu 24.04**.

---

## Stack

| Componente | Versión |
|---|---|
| OS (WSL) | Ubuntu 24.04.4 LTS |
| Java | OpenJDK 11.0.31 |
| Python | 3.11.15 |
| PySpark | 3.4.3 |
| Conda | 26.3.2 (Miniconda3) |
| MongoDB | Atlas (barber_db) |
| Streamlit | Dashboard interactivo |

---

## Estructura del proyecto

```
spark/
├── .env                             ← Credenciales MongoDB (NO subir a git)
├── requirements.txt
│
├── config/
│   ├── mongo_spark_conexion.py           ← Conexión base (4 colecciones)
│   └── mongo_spark_conexion_sinnulos.py  ← Conexión con limpieza de nulos ← USAR ESTA
│
├── unidad2/                         ← UNIDAD II: Preparación de datos
│   ├── 01_tipos_fuentes_datos.py         ← Sesión 6:  Tipos y fuentes de datos
│   ├── 02_datawarehouse.py               ← Sesión 7:  Modelado DW (Estrella + Copo de Nieve)
│   ├── 03_limpieza_datos.py              ← Sesión 8:  Técnicas básicas y avanzadas de limpieza
│   ├── 04_mineria_datos.py               ← Sesión 9:  Tipos y conjuntos en minería (KDD)
│   └── 05_etl.py                         ← Sesión 10: Proceso ETL completo
│
├── ml_algorithms/                   ← UNIDAD III: Algoritmos ML
│   ├── 01_mapreduce.py                   ← MapReduce por servicio
│   ├── 01_mapreduce_analytics_sinnulos.py← MapReduce con gráficas matplotlib
│   ├── 02_kmeans.py                      ← Clustering KMeans
│   ├── 03_regresion_analytics.py         ← 6 modelos de regresión
│   ├── 04_arboldedecision.py             ← Árbol de Decisión
│   ├── 05_bosque_aleatorio.py            ← Random Forest Pipeline
│   ├── 06_pca.py                         ← PCA + KMeans + Plotly
│   └── 07_red_neural.py                  ← Spark → PyTorch Red Neuronal
│
├── analytics/                       ← Dashboards Streamlit interactivos
│   ├── dashboard_kmeans.py               ← Segmentación con KMeans
│   ├── dashboard_regresion_models.py     ← Predicción de ingresos
│   └── dashboard_pca.py                  ← PCA + Clustering + IA
│
├── data_ingestion/
│   └── generar_datos_urbanblade.py       ← Semilla de datos de prueba (opcional)
│
├── data/etl_output/                 ← Salida del ETL (generado al ejecutar 05_etl.py)
│   ├── citas_etl.parquet
│   └── citas_etl.csv
│
└── docs/                            ← Documentación de resultados por algoritmo
    ├── README.md
    ├── 01_mapreduce.md
    ├── 02_kmeans.md
    ├── 03_regresion.md
    ├── 04_arbol_decision.md
    ├── 05_bosque_aleatorio.md
    ├── 06_pca.md
    └── 07_red_neural.md
```

---

## Configuración MongoDB

Base de datos: `barber_db` | Colecciones: `appointments`, `services`, `barbers`, `users`

El `.env` en la raíz del proyecto:

```env
MONGO_USER=luis
MONGO_PASSWORD=<tu_password>
MONGO_CLUSTER=server.qiot9hi.mongodb.net
MONGO_DB=barber_db
MONGO_COLLECTION=appointments
MONGO_COLLECTION_SERVICES=services
MONGO_COLLECTION_BARBERS=barbers
```

Los scripts hacen un **join de 4 colecciones** en PyMongo antes de pasar los datos a Spark:
```
appointments + services + barbers + users → DataFrame Spark
```

---

## Cómo entrar al entorno

```bash
# 1. Abrir WSL desde PowerShell o Terminal de Windows
wsl -d Ubuntu

# 2. Ir al directorio del proyecto
cd ~/spark

# 3. Activar el entorno conda
conda activate spark_env
```

El prompt cambia a `(spark_env) luis1@...:~/spark$`

Verificar instalación:
```bash
python -c "import pyspark; print('PySpark OK:', pyspark.__version__)"
```

---

## Ejecución — Unidad II: Preparación de datos

> Todos los comandos se ejecutan desde `~/spark` con `conda activate spark_env` activo.

### Sesión 6 — Tipos y fuentes de datos

```bash
python3 unidad2/01_tipos_fuentes_datos.py
```

Demuestra:
- **Datos estructurados**: tabla appointments con esquema StructType fijo
- **Datos semi-estructurados**: documentos BSON crudos de MongoDB con campos opcionales y arrays
- **Datos no estructurados**: campo `notas` (texto libre) de las citas

---

### Sesión 7 — Modelado de Datawarehouse

```bash
python3 unidad2/02_datawarehouse.py
```

Demuestra:
- **Modelo Estrella**: `FACT_CITAS` + `dim_fecha` + `dim_servicio` + `dim_barbero`
- **Modelo Copo de Nieve**: normalización con `dim_categoria` y `dim_usuario`
- Query analítica: ingreso total por mes y servicio

---

### Sesión 8 — Técnicas de limpieza de datos

```bash
python3 unidad2/03_limpieza_datos.py
```

Técnicas básicas:
- Análisis de nulos (`isnull + count`)
- `fillna` — rellenar nulos con valores por defecto
- `dropna` — eliminar filas con nulos en campos críticos
- Corrección de tipos (`cast`)
- Estandarización de strings (`trim`, `lower`)
- Eliminación de duplicados (`dropDuplicates`)

Técnicas avanzadas:
- Detección de outliers por **IQR** (rango intercuartílico)
- **Winsorización** — limitar outliers sin eliminar filas
- Codificación categórica (`StringIndexer`)
- Normalización numérica (`MinMaxScaler` → rango [0, 1])

---

### Sesión 9 — Tipos y conjuntos de datos en minería de datos

```bash
python3 unidad2/04_mineria_datos.py
```

Demuestra:
- **Proceso KDD** completo (diagrama en consola)
- **4 tipos de minería** sobre datos reales:
  - Clasificación: ¿La cita será cancelada?
  - Regresión: ¿Cuánto ingreso generará?
  - Clustering: ¿Qué grupos existen?
  - Asociación: ¿Qué servicios coinciden con qué barberos?
- **Splits de dataset**: entrenamiento (60%) / validación (20%) / prueba (20%)
- Explicación de **validación cruzada k-fold**

---

### Sesión 10 — Proceso ETL

```bash
python3 unidad2/05_etl.py
```

Proceso completo con tiempos medidos:
- **EXTRACT**: 4 colecciones de MongoDB Atlas (`appointments`, `services`, `barbers`, `users`)
- **TRANSFORM**: join, limpieza, estandarización, enriquecimiento (nuevas columnas: `ingreso`, `alto_valor`, `cancelada`, `anio`, `mes`, `dia`)
- **LOAD**: guarda en `data/etl_output/citas_etl.parquet` y `data/etl_output/citas_etl.csv`

---

## Ejecución — Unidad III: Algoritmos ML

> Todos los scripts leen datos reales de `barber_db` automáticamente.

### Scripts de algoritmos

```bash
# MapReduce — ingresos totales por servicio
python3 ml_algorithms/01_mapreduce.py

# MapReduce avanzado — con gráficas matplotlib
python3 ml_algorithms/01_mapreduce_analytics_sinnulos.py

# KMeans — segmentación de citas en 3 clusters
python3 ml_algorithms/02_kmeans.py

# Regresión — 6 modelos para predecir ingreso
python3 ml_algorithms/03_regresion_analytics.py

# Árbol de Decisión — clasificar citas alto/bajo valor
python3 ml_algorithms/04_arboldedecision.py

# Random Forest — predecir cancelaciones (guarda modelo en disco)
python3 ml_algorithms/05_bosque_aleatorio.py

# PCA + KMeans — reducción de dimensiones + visualización Plotly
python3 ml_algorithms/06_pca.py

# Red Neuronal PyTorch — clasificación de nivel de ingreso
python3 ml_algorithms/07_red_neural.py
```

---

### Dashboards Streamlit interactivos

```bash
# Dashboard de segmentación KMeans
streamlit run analytics/dashboard_kmeans.py

# Dashboard de predicción de ingresos (Random Forest)
streamlit run analytics/dashboard_regresion_models.py

# Dashboard PCA + Clustering + interpretación automática
streamlit run analytics/dashboard_pca.py
```

Abrir en Windows: **http://localhost:8501**

> Los dashboards cargan datos reales de MongoDB Atlas automáticamente al iniciar.

---

## Resultados obtenidos (283 citas reales)

| Algoritmo | Métrica | Resultado |
|-----------|---------|-----------|
| MapReduce | Servicio estrella | Corte fade 16 — $20,163 MXN |
| KMeans | Silhouette Score | **0.7051** (buena segmentación) |
| Regresión Múltiple | R² | 1.0 |
| Árbol de Decisión | Accuracy | 1.0 (umbral precio > $505.75) |
| Random Forest | AUC ROC | **0.6523** (predicción cancelaciones) |
| PCA | Varianza PC1 + PC2 | 68.2% + 31.8% = 100% |
| Red Neuronal | Precisión test | 100% (dataset pequeño) |

Ver documentación detallada en [`docs/`](docs/README.md).

---

## Referencia rápida de comandos

| Acción | Comando |
|---|---|
| Activar entorno | `conda activate spark_env` |
| Desactivar entorno | `conda deactivate` |
| Ver entornos | `conda env list` |
| Ver paquetes instalados | `conda list` |
| Instalar paquete | `pip install <paquete>` |
| Jupyter Notebook | `jupyter notebook --no-browser --port=8888` |
| Jupyter Lab | `jupyter lab --no-browser --port=8888` |
| PySpark REPL | `pyspark` |

Variable de entorno Java (ya configurada):
```bash
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
```
