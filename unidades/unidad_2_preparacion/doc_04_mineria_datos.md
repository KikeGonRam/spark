# Unidad II — Sesión 9: Tipos y Conjuntos de Datos en Minería

**Script**: `unidades/unidad_2_preparacion/04_mineria_datos.py`
**Dataset**: 12,505 citas reales — `barber_db` (MongoDB Atlas), 1,000 clientes, 25 barberos

---

## Proceso KDD — Diagrama aplicado a UrbanBlade

```
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   FUENTES   │────►│  SELECCIÓN  │────►│  LIMPIEZA   │
  │  DE DATOS   │     │  DE DATOS   │     │  DE DATOS   │
  │─────────────│     │─────────────│     │─────────────│
  │ MongoDB     │     │appointments │     │ dropna      │
  │ barber_db   │     │ + services  │     │ fillna      │
  │ (raw BSON)  │     │ + barbers   │     │ casting     │
  │             │     │ + clients   │     │             │
  └─────────────┘     └─────────────┘     └──────┬──────┘
                                                  │
  ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
  │CONOCIMIENTO │◄────│   MINERÍA   │◄────│TRANSFORMACIÓN│
  │  (Resultado)│     │ (Algoritmos)│     │  DE DATOS   │
  │─────────────│     │─────────────│     │─────────────│
  │ Clusters    │     │ KMeans      │     │ VectorAssemb│
  │ Predicciones│     │ RandomForest│     │ Normaliz.   │
  │ Patrones    │     │ PCA/FPGrowth│     │ Encoding    │
  └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Tipos de Tareas de Minería

### 1. Clasificación (Supervisada)

**Pregunta**: ¿Esta cita será cancelada?
**Variable objetivo**: `es_cancelada` (0 = no cancelada, 1 = cancelada)

```
+-------------+-------+
|es_cancelada |  count|
+-------------+-------+
|            0|  11541|
|            1|    964|
+-------------+-------+
```

```
Citas canceladas:      964  (7.7%)
Citas no canceladas: 11541  (92.3%)
```

**Desbalance de clases**: 92.3% vs 7.7% — clase positiva minoritaria, más marcado que un
desbalance moderado. Con clases tan desbalanceadas, el **accuracy no es confiable** (un
modelo que siempre prediga "no cancela" ya acierta 92.3% sin aprender nada); se usa
**AUC-ROC** como métrica principal.

Script que implementa clasificación: `unidades/unidad_3_supervisado/02_arbol_decision.py`
(árbol) y `03_bosque_aleatorio.py` (bosque, ensemble).

---

### 2. Regresión (Supervisada)

**Pregunta**: ¿Cuánto facturará la barbería en un día dado?
**Variable objetivo**: `ingreso_dia` (agregado diario, no por cita — ver nota abajo)

```
Precio promedio por cita:  $355.84 MXN
Facturación diaria promedio (464 días con datos): variable según volumen del día
```

**Nota metodológica**: predecir el precio de una sola cita sería trivial
(`precio_cobrado == precio_servicio` siempre en este dataset), así que la Unidad III
agrega por día para obtener un problema de regresión real. Ver
`unidades/unidad_3_supervisado/reporte_evaluacion.md` para los resultados.

Script: `unidades/unidad_3_supervisado/01_regresion.py`

---

### 3. Clustering (No supervisado)

**Pregunta**: ¿Qué grupos naturales existen entre las citas?
**Sin variable objetivo** — el algoritmo descubre los grupos

Features para clustering: `duracion_min`, `precio`, `ingreso` (12,505 registros).

Script que implementa clustering: `unidades/unidad_4_no_supervisado/01_kmeans.py`
**Resultado (ejecución sobre datos actuales): Silhouette Score = 0.7430** (buena
segmentación en K=3, confirmado por el Método del Codo). Detalle completo en
[`../unidad_4_no_supervisado/doc_01_kmeans.md`](../unidad_4_no_supervisado/doc_01_kmeans.md).

---

### 4. Reglas de Asociación / Co-ocurrencia (No supervisado)

**Pregunta**: ¿Qué servicios tienden a coincidir con qué barberos?

Top 8 combinaciones servicio–barbero más frecuentes (dataset actual, nombres reales):

```
+--------------------------------------+---------------------+-----------+
|servicio                              |barbero               |frecuencia |
+--------------------------------------+---------------------+-----------+
|Pompadour                             |Roy Jakubowski MD     |         41|
|Combo Clásico                         |Sid Wolff             |         40|
|Corte Texturizado                     |Sid Wolff             |         39|
|Combo Express                         |Lincoln Torphy        |         38|
|Corte Clásico                         |Junior Bosco          |         38|
|Corte Clásico                         |Sid Wolff             |         38|
|Corte Texturizado                     |Prof. Thad Nikolaus V |         37|
|Afeitado Clásico con Toalla Caliente  |Darrick Collins       |         36|
+--------------------------------------+---------------------+-----------+
```

**Patrón encontrado**: con 1,000 clientes y 25 barberos, la frecuencia máxima por
combinación individual servicio-barbero (~41) es baja en proporción al total —
consistente con una asignación de citas mayormente aleatoria/por disponibilidad más que
por preferencia fuerte de barbero. Esto es información valiosa en sí misma: sugiere que
**no existe un sistema de "barbero preferido"** operando actualmente, a diferencia de lo
que se podría asumir. El análisis de reglas de asociación real entre **servicios**
(no servicio-barbero) se hace con FP-Growth en
`unidades/unidad_4_no_supervisado/04_recomendacion_servicios.py`.

---

## Tipos de Conjuntos de Datos

### Split Train / Validation / Test

Con 12,505 registros (mucho mayor al dataset inicial de prueba de 283), los splits usados
en los scripts de la Unidad III son:

```
Regresión (por día, 464 registros):     80% train / 20% test → 397 / 67
Clasificación (por cita, 12,505 reg.):  80% train / 20% test  (árbol)
                                         70% train / 30% test  (bosque)
```

**Método de división**: `randomSplit([0.8, 0.2], seed=42)`. La semilla `42` garantiza
reproducibilidad — la misma partición se obtiene en cualquier ejecución.

---

### Validación Cruzada K-Fold (k=3)

Usada en `01_regresion.py` (Cross Validation) sobre las 397 filas de entrenamiento:

```
Dataset de entrenamiento: 397 días → 3 folds de ~132 registros cada uno

Fold 1: [TEST]  [TRAIN] [TRAIN]  → métrica_1
Fold 2: [TRAIN] [TEST]  [TRAIN]  → métrica_2
Fold 3: [TRAIN] [TRAIN] [TEST]   → métrica_3

Resultado final: promedio(métrica_1, métrica_2, métrica_3)
```

**Ventaja del K-Fold sobre un split simple**: usa más del conjunto de entrenamiento tanto
para ajustar como para validar, dando una estimación más robusta que un solo split. Se
usa `numFolds=3` (no 5 o 10) porque el dataset agregado por día (464 filas) es
relativamente pequeño; con más folds cada uno tendría muy pocos ejemplos.

---

## Resumen: Tipos de Minería aplicados (mapeo actual a scripts)

```
Tipo              | Supervisado | Variable objetivo      | Script UrbanBlade
──────────────────────────────────────────────────────────────────────────────────
Clasificación     | Sí          | es_cancelada (0/1)     | 02_arbol_decision.py / 03_bosque_aleatorio.py
Regresión         | Sí          | ingreso_dia (float)    | 01_regresion.py
Clustering        | No          | ninguna                | 01_kmeans.py (Unidad IV)
Reglas asociación | No          | ninguna                | 04_recomendacion_servicios.py (FP-Growth)
Reducción dim.    | No          | ninguna                | 02_pca.py (Unidad IV)
Red neuronal      | Sí          | clase de ingreso (3)   | 04_red_neuronal.py (Unidad III)
```

---

## Observaciones técnicas

- El 7.7% de cancelaciones es un desbalance real y significativo — predecir cancelaciones
  con Random Forest tiene valor operativo concreto (anticipar huecos en la agenda).
- Con 12,505 registros el dataset ya tiene volumen suficiente para que los splits de
  prueba (por ejemplo, ~30% de 12,505 ≈ 3,750 citas para el bosque) den estimaciones de
  métricas con baja varianza, a diferencia del dataset inicial de 283 registros.
- El bajo repunte de combinaciones servicio-barbero (máximo ~41 sobre 12,505 citas)
  sugiere que la asignación de citas no sigue un patrón fuerte de "barbero preferido" —
  hallazgo relevante para decidir si vale la pena construir un sistema de recomendación
  de barbero (a diferencia de recomendación de servicio, que sí muestra patrones útiles).
- K-fold con `numFolds=3` se prefiere sobre 5 o 10 en el dataset agregado por día (464
  filas) para que cada fold tenga suficientes ejemplos de entrenamiento.
