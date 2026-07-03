# UrbanBlade — Extracción del conocimiento en bases de datos

Proyecto de análisis de datos de una barbería con **Apache Spark / PySpark** + **MongoDB Atlas**,
organizado por las **5 unidades** de la asignatura (UTVT · IDGS-93 · Mayo–Agosto 2026).

**Equipo:** Equipo UrbanBlade · **Docente:** MGTI. Héctor Velázquez Estrada
**Datos reales:** `barber_db` — 12,535 citas · 1,000 clientes · 25 barberos · 20 servicios.

---

## Organización por unidad

Todo el proyecto está ordenado en [`unidades/`](unidades/README.md), una carpeta por unidad,
cada una con su `README.md` y el checklist de entregables que pide la secuencia didáctica.

| Unidad | Tema | Carpeta |
|---|---|---|
| **I** | Introducción al análisis de datos | [`unidades/unidad_1_introduccion/`](unidades/unidad_1_introduccion/) |
| **II** | Preparación de los datos (ETL, DW, limpieza) | [`unidades/unidad_2_preparacion/`](unidades/unidad_2_preparacion/) |
| **III** | Análisis supervisado (regresión, clasificación) | [`unidades/unidad_3_supervisado/`](unidades/unidad_3_supervisado/) |
| **IV** | Análisis no supervisado (KMeans, PCA, FP-Growth) | [`unidades/unidad_4_no_supervisado/`](unidades/unidad_4_no_supervisado/) |
| **V** | Presentación y visualización (dashboard, Matplotlib) | [`unidades/unidad_5_visualizacion/`](unidades/unidad_5_visualizacion/) |

Índice completo con checklist de entregables: [`unidades/README.md`](unidades/README.md).

---

## Estructura del proyecto

```
spark/
├── README.md                         ← este archivo
├── SKILL.md                          ← guía técnica del proyecto
├── .env                              ← credenciales MongoDB (NO se sube a git)
├── requirements.txt
│
├── config/                           ← MOTOR compartido (capa de datos única)
│   ├── mongo_spark_conexion_sinnulos.py   ← conexión + JOIN + features  ← USAR ESTA
│   └── mongo_spark_conexion.py            ← conexión base (legacy)
│
├── data_ingestion/
│   └── generar_datos_urbanblade.py
│
├── data/etl_output/                  ← salida del ETL (Parquet/CSV) — en .gitignore
│
└── unidades/
    ├── README.md                     ← índice por unidad + checklist
    ├── unidad_1_introduccion/        ← 2 documentos (comparativa + caso de estudio)
    ├── unidad_2_preparacion/         ← 7 scripts + esquema DW + docs
    ├── unidad_3_supervisado/         ← 6 scripts + reporte de evaluación + docs
    ├── unidad_4_no_supervisado/      ← 4 scripts + reporte de evaluación + docs
    └── unidad_5_visualizacion/       ← dashboard ejecutivo + Matplotlib
```

Los scripts **localizan la raíz del proyecto automáticamente**, así que se ejecutan
correctamente desde cualquier ruta (buscan la carpeta `config/`).

---

## Stack

| Componente | Detalle |
|---|---|
| OS | WSL Ubuntu 24.04 |
| Python | 3.11 (Miniconda `spark_env`) |
| PySpark | 3.5.x |
| ML | Spark MLlib + PyTorch |
| Base de datos | MongoDB Atlas (`barber_db`) |
| Visualización | Matplotlib · Plotly · Streamlit |

---

## Configuración MongoDB (`.env` en la raíz)

**Nunca subas tu `.env` real a git** (ya está en `.gitignore`). El repositorio incluye
[`.env.example`](.env.example) como plantilla — cópialo y llena los valores reales:

```bash
cp .env.example .env
```

```env
# .env.example — plantilla, sin credenciales reales
MONGO_USER=
MONGO_PASSWORD=
MONGO_CLUSTER=
MONGO_DB=barber_db
```

| Variable | De dónde se obtiene |
|---|---|
| `MONGO_USER` | Atlas → Database Access → Database Users |
| `MONGO_PASSWORD` | Atlas → Database Access → Edit → Edit Password |
| `MONGO_CLUSTER` | Atlas → Database → Connect → Drivers (solo el host, sin `mongodb+srv://` ni credenciales) |
| `MONGO_DB` | `barber_db` (nombre fijo del proyecto) |

Pide estos 4 valores al responsable del proyecto — **no se comparten por chat ni se
suben al repositorio**, solo se entregan directamente al archivo `.env` local de cada
integrante.

La capa de datos (`config/mongo_spark_conexion_sinnulos.py`) hace un **JOIN de 4 colecciones**
en PyMongo y entrega un DataFrame Spark enriquecido:
```
appointments + services + barbers(→users) + clients(→users) → DataFrame Spark
```

Además expone helpers para **5 colecciones adicionales** (`payments`, `loyalty_transactions`,
`barber_schedules`, `products`, `barbershop_settings`) usadas en Unidad II y visualizadas
en el dashboard ejecutivo (Unidad V): pagos/calidad, fidelización, utilización de barberos
e inventario. Ver [`unidades/unidad_2_preparacion/README.md`](unidades/unidad_2_preparacion/README.md).

---

## Clonar, configurar y ejecutar (guía completa)

Para integrantes nuevos del equipo, en Windows con PowerShell:

```powershell
# 1. Clona el repo y prepara el entorno (WSL + Java + Miniconda + spark_env)
git clone https://github.com/KikeGonRam/spark.git
cd spark
.\setup-spark.ps1
```

El script se detendrá en el paso de `.env` la primera vez — en ese momento:

```powershell
# 2. Copia la plantilla y pide los valores reales al responsable del proyecto
cp .env.example .env
notepad .env    # pega MONGO_USER / MONGO_PASSWORD / MONGO_CLUSTER / MONGO_DB

# 3. Vuelve a correr el script para validar la conexión a MongoDB Atlas
.\setup-spark.ps1
```

Cuando termine sin errores, ya puedes ejecutar cualquier script (ver
[`unidades/COMANDOS.txt`](unidades/COMANDOS.txt) para la lista completa):

```bash
# Desde WSL (Ubuntu), dentro de la carpeta del proyecto
conda activate spark_env
spark-submit unidades/unidad_3_supervisado/01_regresion.py
streamlit run unidades/unidad_5_visualizacion/main_dashboard.py
```

Instala/valida automáticamente: WSL2 + Ubuntu, Java (OpenJDK 11), Miniconda, el entorno
`spark_env` con Python 3.11, y todas las dependencias de `requirements.txt`. Si no existe
un archivo `.env`, el script se detiene y explica cómo obtenerlo (no genera uno falso).

## Cómo ejecutar

```bash
# 1. Entrar al entorno (WSL) — usa la ruta montada de Windows, NO ~/spark
#    (~/spark es una copia nativa de WSL desactualizada, sin la carpeta unidades/)
wsl -d Ubuntu && cd /mnt/c/Users/<tu_usuario>/Documents/UrbanBlade/spark && conda activate spark_env

# 2. Ejemplos por unidad
spark-submit unidades/unidad_2_preparacion/05_etl.py                 # ETL → data warehouse
spark-submit unidades/unidad_3_supervisado/01_regresion.py           # regresión (R², MSE, MAE)
spark-submit unidades/unidad_4_no_supervisado/03_segmentacion_clientes.py  # segmentación

# 3. Dashboard ejecutivo (Unidad V) — abre en http://localhost:8501
streamlit run unidades/unidad_5_visualizacion/main_dashboard.py
```

---

## Nota metodológica (importante)

Los modelos se diseñaron **sin fuga de datos (leakage)**: la variable objetivo nunca
aparece entre las features. Por eso las métricas son **realistas y defendibles**
(p. ej. R² ≈ 0.6–0.9, no 1.0). Detalle en los reportes de evaluación de las Unidades III y IV.
