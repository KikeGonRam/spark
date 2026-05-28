# UrbanBlade – Guía de Comandos
**Proyecto:** Extracción del Conocimiento en BD | UTVT IDGS-84  
**Prof.:** MGTI. Héctor Velázquez Estrada  
**Stack:** PySpark 3.5.1 · MongoDB 7.0 · Streamlit · PyTorch

---

## Requisitos previos

Todos los comandos se ejecutan en **WSL Ubuntu**. Desde Windows abre una terminal y entra a WSL:

```bash
wsl -d Ubuntu
```

Luego navega al directorio del proyecto:

```bash
cd /mnt/c/Users/luis1/Desktop/BarberPro-Python/spark
```

> A partir de aquí todos los comandos usan `./run.sh <comando>`.

---

## Primera vez (instalación del entorno)

```bash
# 1. Crear entorno virtual
python3 -m venv .venv

# 2. Instalar pip
.venv/bin/python3 -m ensurepip --upgrade

# 3. Instalar dependencias
.venv/bin/pip install -r requirements.txt
```

---

## 1. Inserción de Datos

| Archivo | Descripción | Comando |
|---|---|---|
| `data_ingestion/generar_datos_urbanblade.py` | Inserta **2,000** citas básicas en MongoDB | `./run.sh generar` |
| `data_ingestion/generar_datos_100k.py` | Inserta **100,000** citas enriquecidas en MongoDB | `./run.sh generar-100k` |

```bash
# Insertar 2,000 citas (demo rápida)
./run.sh generar

# Insertar 100,000 citas (recomendado para todos los análisis)
./run.sh generar-100k
```

> **Nota:** Ejecutar `generar-100k` antes de correr cualquier algoritmo de ML para tener datos completos.

---

## 2. Unidad II – ETL y Limpieza de Datos

| Archivo | Descripción | Comando |
|---|---|---|
| `ml_algorithms/01_mapreduce.py` | ETL MapReduce con PySpark | `./run.sh mapreduce` |
| `ml_algorithms/08_limpieza_datos.py` | 10 técnicas de limpieza + KDD | `./run.sh limpieza` |

```bash
# ETL MapReduce (consola)
./run.sh mapreduce

# Validación y limpieza de datos (consola)
./run.sh limpieza
```

---

## 3. Unidad III – Modelos de Machine Learning

| Archivo | Descripción | Comando |
|---|---|---|
| `ml_algorithms/03_regresion_analytics.py` | 6 modelos de regresión | `./run.sh regresion` |
| `ml_algorithms/04_arboldedecision.py` | Árbol de Decisión | `./run.sh arbol` |
| `ml_algorithms/05_bosque_aleatorio.py` | Bosque Aleatorio (Random Forest) | `./run.sh bosque` |
| `ml_algorithms/07_red_neural.py` | Red Neuronal con PyTorch | `./run.sh redneuronal` |
| `ml_algorithms/09_series_tiempo.py` | Series de Tiempo + Regresión Lineal | `./run.sh series` |
| `ml_algorithms/10_rfm_clientes.py` | Segmentación RFM de clientes | `./run.sh rfm` |

```bash
# 6 modelos de regresión (Linear, Ridge, Lasso, DTR, RFR, GBT)
./run.sh regresion

# Árbol de Decisión
./run.sh arbol

# Bosque Aleatorio
./run.sh bosque

# Red Neuronal PyTorch (no requiere spark-submit)
./run.sh redneuronal

# Series de Tiempo + predicción de ingresos
./run.sh series

# Análisis RFM: VIP / Leal / En Riesgo / Inactivo
./run.sh rfm
```

---

## 4. Unidad IV – Aprendizaje No Supervisado

| Archivo | Descripción | Comando |
|---|---|---|
| `ml_algorithms/02_kmeans.py` | Clustering KMeans (Silhouette) | `./run.sh kmeans` |
| `ml_algorithms/06_pca.py` | PCA + KMeans en espacio reducido | `./run.sh pca` |
| `ml_algorithms/10_rfm_clientes.py` | RFM + KMeans k=4 | `./run.sh rfm` |
| `ml_algorithms/11_asociacion_fpgrowth.py` | Reglas de Asociación FP-Growth | `./run.sh asociacion` |

```bash
# Clustering KMeans
./run.sh kmeans

# PCA + KMeans
./run.sh pca

# Reglas de Asociación FP-Growth (canastas de servicios)
./run.sh asociacion
```

---

## 5. Unidad V – Dashboards Interactivos (Streamlit)

Todos los dashboards se abren en el navegador automáticamente.

| Archivo | Descripción | Comando | Puerto |
|---|---|---|---|
| `analytics/dashboard_kmeans.py` | Dashboard KMeans | `./run.sh dash-kmeans` | 8501 |
| `analytics/dashboard_regresion_models.py` | Dashboard Regresión | `./run.sh dash-regresion` | 8501 |
| `analytics/dashboard_pca.py` | Dashboard PCA | `./run.sh dash-pca` | 8501 |
| `analytics/dashboard_limpieza.py` | Dashboard Limpieza ETL + KDD | `./run.sh dash-limpieza` | 8501 |
| `analytics/dashboard_series_tiempo.py` | Dashboard Series de Tiempo | `./run.sh dash-series` | 8501 |
| `analytics/dashboard_rfm.py` | Dashboard RFM Clientes | `./run.sh dash-rfm` | 8501 |
| `analytics/dashboard_asociacion.py` | Dashboard Reglas de Asociación | `./run.sh dash-asociacion` | 8501 |
| `analytics/dashboard_ejecutivo.py` | **Dashboard Ejecutivo (TODOS)** | `./run.sh dash-ejecutivo` | 8501 |
| `analytics/dashboard_exportar.py` | Centro de Exportación | `./run.sh dash-exportar` | 8501 |

```bash
# Dashboard KMeans
./run.sh dash-kmeans

# Dashboard Regresión (6 modelos comparados)
./run.sh dash-regresion

# Dashboard PCA
./run.sh dash-pca

# Dashboard Limpieza de Datos + Diagrama KDD
./run.sh dash-limpieza

# Dashboard Series de Tiempo + Predicciones
./run.sh dash-series

# Dashboard RFM – Segmentación de Clientes
./run.sh dash-rfm

# Dashboard Reglas de Asociación FP-Growth
./run.sh dash-asociacion

# ⭐ Dashboard Ejecutivo – TODOS los modelos en una sola app
./run.sh dash-ejecutivo

# Centro de Exportación (CSV / JSON / Excel / Parquet / SQL / PDF)
./run.sh dash-exportar
```

> Abre **http://localhost:8501** en tu navegador después de ejecutar cualquier dashboard.

---

## 6. Exportación de Archivos

Desde el **Centro de Exportación** (`dash-exportar`) puedes descargar:

| Formato | Uso |
|---|---|
| `.csv` | Excel, Google Sheets |
| `.json` | APIs, JavaScript |
| `.xlsx` | Excel multi-hoja con KPIs |
| `.parquet` | Big Data, Apache Spark |
| `.sql` | MySQL / PostgreSQL |
| `.pdf` | Reportes ejecutivos |

```bash
./run.sh dash-exportar
# → http://localhost:8501
```

---

## 7. Flujo Completo Recomendado

Ejecuta en este orden para una demo completa:

```bash
# PASO 1 – Generar 100K registros limpios
./run.sh generar-100k

# PASO 2 – Verificar limpieza de datos
./run.sh limpieza

# PASO 3 – Correr todos los algoritmos (opcional, para ver resultados en consola)
./run.sh mapreduce
./run.sh kmeans
./run.sh regresion
./run.sh arbol
./run.sh bosque
./run.sh pca
./run.sh redneuronal
./run.sh series
./run.sh rfm
./run.sh asociacion

# PASO 4 – Abrir el Dashboard Ejecutivo (muestra TODO)
./run.sh dash-ejecutivo

# PASO 5 – Exportar reportes
./run.sh dash-exportar
```

---

## 8. Estructura de Archivos del Proyecto

```
spark/
├── run.sh                          ← Script principal de comandos
├── requirements.txt                ← Dependencias Python
├── COMANDOS.md                     ← Este archivo
│
├── config/
│   └── mongo_spark_conexion_sinnulos.py   ← Conexión MongoDB + Spark Session
│
├── data_ingestion/
│   ├── generar_datos_urbanblade.py        ← Genera 2,000 citas
│   └── generar_datos_100k.py             ← Genera 100,000 citas
│
├── ml_algorithms/
│   ├── 01_mapreduce.py            ← Unidad II: ETL MapReduce
│   ├── 02_kmeans.py               ← Unidad IV: KMeans Clustering
│   ├── 03_regresion_analytics.py  ← Unidad III: 6 modelos regresión
│   ├── 04_arboldedecision.py      ← Unidad III: Árbol de Decisión
│   ├── 05_bosque_aleatorio.py     ← Unidad III: Random Forest
│   ├── 06_pca.py                  ← Unidad IV: PCA + KMeans
│   ├── 07_red_neural.py           ← Unidad III/IV: Red Neuronal PyTorch
│   ├── 08_limpieza_datos.py       ← Unidad II: Validación y Limpieza ETL
│   ├── 09_series_tiempo.py        ← Unidad III: Series de Tiempo
│   ├── 10_rfm_clientes.py         ← Unidad III/IV: Análisis RFM
│   └── 11_asociacion_fpgrowth.py  ← Unidad IV: Reglas de Asociación
│
├── analytics/
│   ├── dashboard_kmeans.py        ← Unidad V: Dashboard KMeans
│   ├── dashboard_regresion_models.py  ← Unidad V: Dashboard Regresión
│   ├── dashboard_pca.py           ← Unidad V: Dashboard PCA
│   ├── dashboard_limpieza.py      ← Unidad II: Dashboard Limpieza + KDD
│   ├── dashboard_series_tiempo.py ← Unidad III: Dashboard Series de Tiempo
│   ├── dashboard_rfm.py           ← Unidad III/IV: Dashboard RFM
│   ├── dashboard_asociacion.py    ← Unidad IV: Dashboard Asociación
│   ├── dashboard_ejecutivo.py     ← Unidad V: Dashboard Ejecutivo completo
│   └── dashboard_exportar.py      ← Centro de Exportación
│
└── utils/
    └── exportar.py                ← Módulo: CSV/JSON/Excel/PDF/Parquet/SQL
```

---

## 9. Referencia Rápida de Comandos

```bash
./run.sh generar          # 2,000 citas básicas
./run.sh generar-100k     # 100,000 citas completas
./run.sh mapreduce        # ETL MapReduce
./run.sh kmeans           # KMeans Clustering
./run.sh regresion        # 6 modelos de regresión
./run.sh arbol            # Árbol de Decisión
./run.sh bosque           # Random Forest
./run.sh pca              # PCA + KMeans
./run.sh redneuronal      # Red Neuronal PyTorch
./run.sh limpieza         # Limpieza y validación ETL
./run.sh series           # Series de Tiempo
./run.sh rfm              # Segmentación RFM
./run.sh asociacion       # Reglas de Asociación FP-Growth
./run.sh dash-kmeans      # Dashboard KMeans
./run.sh dash-regresion   # Dashboard Regresión
./run.sh dash-pca         # Dashboard PCA
./run.sh dash-limpieza    # Dashboard Limpieza + KDD
./run.sh dash-series      # Dashboard Series de Tiempo
./run.sh dash-rfm         # Dashboard RFM Clientes
./run.sh dash-asociacion  # Dashboard Reglas de Asociación
./run.sh dash-ejecutivo   # Dashboard Ejecutivo (TODOS los modelos)
./run.sh dash-exportar    # Centro de Exportación de archivos
```
