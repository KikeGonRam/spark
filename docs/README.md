# Documentación de Resultados — UrbanBlade BigData

Resultados de la ejecución del 10 de junio de 2026 con **283 citas reales** de MongoDB Atlas (`barber_db.appointments`).

---

## Resumen ejecutivo

| Script | Algoritmo | Métrica principal | Resultado |
|--------|-----------|-------------------|-----------|
| 01_mapreduce | MapReduce | Ingreso por servicio | Corte fade 16 = Servicio Estrella ($20,163) |
| 02_kmeans | KMeans | Silhouette Score | **0.7051** — Buena segmentación |
| 03_regresion | 6 modelos regresión | R² | Múltiple/Polinomial = 1.0 |
| 04_arboldedecision | Decision Tree | Accuracy | **1.0** (umbral precio > $505.75) |
| 05_bosque_aleatorio | Random Forest | AUC ROC | **0.6523** (predicción de cancelaciones) |
| 06_pca | PCA + KMeans | Varianza explicada | PC1=68.2%, PC2=31.8% |
| 07_red_neural | PyTorch MLP | Accuracy | **100%** (sobreajuste — dataset pequeño) |

---

## Dataset

- **Colección**: `barber_db.appointments` (datos reales del sistema UrbanBlade)
- **Total citas**: 283
- **Período**: últimos 30 días
- **Join realizado**: `appointments` + `services` + `barbers` + `users`

### Servicios en el dataset

| Servicio | Citas | Ingreso Total |
|----------|-------|---------------|
| Corte fade 16 | 49 | $20,163 |
| Corte clásico 45 | 31 | $12,359 |
| Corte clásico 3 | 32 | $11,404 |
| Corte fade 86 | 26 | $11,504 |
| Arreglo de barba 53 | 24 | $11,445 |
| Combo corte y barba 79 | 24 | $9,553 |
| Combo corte y barba 60 | 25 | $8,777 |
| Corte clásico 60 | 19 | $8,925 |
| Combo corte y barba 89 | 15 | $6,792 |
| Corte fade 66 | 18 | $6,172 |
| Arreglo de barba 3 | 20 | $4,328 |

### Estados de citas

| Estado | Descripción |
|--------|-------------|
| completada | Cita terminada y pagada |
| cancelada | Cliente canceló |
| pendiente | Sin confirmar aún |
| confirmada | Confirmada, no ejecutada |
| no_asistio | Cliente no se presentó |
| en_proceso | En curso |

---

## Campos del dataset Spark

| Campo | Tipo | Fuente | Descripción |
|-------|------|--------|-------------|
| `servicio` | string | `services.nombre` | Nombre del servicio |
| `barbero` | string | `users.name` (vía `barbers.user_id`) | Nombre del barbero |
| `duracion_min` | double | `services.duracion_min` | Duración en minutos |
| `precio` | double | `appointments.precio_cobrado` o `services.precio` | Precio cobrado |
| `estado` | string | `appointments.estado` | Estado de la cita |
| `ingreso` | double | = `precio` | Ingreso generado |
| `fecha` | string | `appointments.fecha` | Fecha de la cita |

### Nota sobre `barbero` (bug corregido)

El `BarberFactory` de Laravel no llena el campo `nombre` en la colección `barbers`. La solución implementada es hacer un join adicional con `users` usando `barbers.user_id → users.name`. Cadena completa:

```
appointments.barber_id → barbers._id → barbers.user_id → users._id → users.name
```

---

## Documentación — Unidad II: Preparación de datos

Resultados de la ejecución del 10 de junio de 2026 — scripts `unidad2/`.

| Archivo | Sesión | Contenido |
|---------|--------|-----------|
| [unidad2_01_tipos_fuentes_datos.md](unidad2_01_tipos_fuentes_datos.md) | Sesión 6 | Datos estructurados / semi-estructurados / no estructurados |
| [unidad2_02_datawarehouse.md](unidad2_02_datawarehouse.md) | Sesión 7 | Star Schema + Snowflake Schema con datos reales |
| [unidad2_03_limpieza_datos.md](unidad2_03_limpieza_datos.md) | Sesión 8 | 10 técnicas de limpieza — básicas y avanzadas |
| [unidad2_04_mineria_datos.md](unidad2_04_mineria_datos.md) | Sesión 9 | KDD, tipos de minería, splits 60/20/20, k-fold |
| [unidad2_05_etl.md](unidad2_05_etl.md) | Sesión 10 | ETL completo: Extract 330 docs → Transform → Load Parquet+CSV |

---

## Documentación — Unidad III: Algoritmos ML

| Archivo | Contenido |
|---------|-----------|
| [01_mapreduce.md](01_mapreduce.md) | Resultados MapReduce — ingresos por servicio |
| [02_kmeans.md](02_kmeans.md) | Clustering KMeans — segmentación de citas |
| [03_regresion.md](03_regresion.md) | 6 modelos de regresión — predicción de ingreso |
| [04_arbol_decision.md](04_arbol_decision.md) | Árbol de decisión — clasificación alto/bajo valor |
| [05_bosque_aleatorio.md](05_bosque_aleatorio.md) | Random Forest — predicción de cancelaciones |
| [06_pca.md](06_pca.md) | PCA + KMeans — reducción de dimensionalidad |
| [07_red_neural.md](07_red_neural.md) | Red neuronal PyTorch — clasificación de ingresos |

---

## Ejecución

```bash
conda activate spark_env
cd ~/spark   # WSL

python3 ml_algorithms/01_mapreduce.py
python3 ml_algorithms/02_kmeans.py
python3 ml_algorithms/03_regresion_analytics.py
python3 ml_algorithms/04_arboldedecision.py
python3 ml_algorithms/05_bosque_aleatorio.py
python3 ml_algorithms/06_pca.py
python3 ml_algorithms/07_red_neural.py

# Dashboards interactivos (abrir http://localhost:8501 en Windows)
streamlit run analytics/dashboard_kmeans.py
streamlit run analytics/dashboard_regresion_models.py
streamlit run analytics/dashboard_pca.py
```
