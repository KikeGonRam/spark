# Unidad II — Sesión 9: Tipos y Conjuntos de Datos en Minería

**Script**: `unidad2/04_mineria_datos.py`  
**Fecha de ejecución**: 2026-06-10  
**Dataset**: 283 citas reales — `barber_db` (MongoDB Atlas)

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
  └─────────────┘     └─────────────┘     └──────┬──────┘
                                                  │
  ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
  │CONOCIMIENTO │◄────│   MINERÍA   │◄────│TRANSFORMACIÓN│
  │  (Resultado)│     │ (Algoritmos)│     │  DE DATOS   │
  │─────────────│     │─────────────│     │─────────────│
  │ Clusters    │     │ KMeans      │     │ VectorAssemb│
  │ Predicciones│     │ RandomForest│     │ Normaliz.   │
  │ Patrones    │     │ PCA         │     │ Encoding    │
  └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Tipos de Tareas de Minería

### 1. Clasificación (Supervisada)

**Pregunta**: ¿Esta cita será cancelada?  
**Variable objetivo**: `cancelada` (0 = no cancelada, 1 = cancelada)

```
+---------+-------+
|cancelada|  count|
+---------+-------+
|        0|    229|
|        1|     54|
+---------+-------+
```

```
Citas canceladas:     54  (19.1%)
Citas no canceladas: 229  (80.9%)
```

**Desbalance de clases**: 80.9% vs 19.1% — clase positiva minoritaria.  
Para corregir este desbalance en producción se usaría:
- Sobremuestreo SMOTE (clase positiva)
- Pesos de clase (`classWeight` en RandomForest)
- Umbral de decisión ajustado

Script que implementa clasificación: `ml_algorithms/05_bosque_aleatorio.py`

---

### 2. Regresión (Supervisada)

**Pregunta**: ¿Cuánto ingreso generará esta cita?  
**Variable objetivo**: `precio` (continua, double)

```
Precio promedio:    $393.72 MXN
Duración promedio:  39.4 minutos
```

**Features usados**: `duracion_min`, `precio` (para predecir `ingreso`)

Script que implementa regresión: `ml_algorithms/03_regresion_analytics.py`

---

### 3. Clustering (No supervisado)

**Pregunta**: ¿Qué grupos naturales existen entre las citas?  
**Sin variable objetivo** — el algoritmo descubre los grupos

Features para clustering:
```
+-------+-----------------+------------------+
|summary|           precio|      duracion_min|
+-------+-----------------+------------------+
|  count|              283|               283|
|   mean|393.7191872791519| 39.43462897526502|
| stddev|158.1588398961007|16.519872047574566|
|    min|           100.57|                30|
|    max|           646.31|                75|
+-------+-----------------+------------------+
```

Script que implementa clustering: `ml_algorithms/02_kmeans.py`  
Resultado: **Silhouette Score = 0.7051** (buena segmentación en 3 clusters)

---

### 4. Reglas de Asociación (No supervisado)

**Pregunta**: ¿Qué servicios tienden a coincidir con qué barberos?  
(Análogo a Market Basket Analysis)

Top 8 combinaciones servicio–barbero más frecuentes:

```
+--------------------+--------------+-----------+
|servicio            |barbero       |frecuencia |
+--------------------+--------------+-----------+
|Corte fade 16       |Barbero Test 1|         20|
|Corte fade 86       |Barbero Test 1|         18|
|Combo corte y barba |Barbero Test 2|         16|
|Corte clásico 45    |Barbero Test 2|         15|
|Arreglo de barba 53 |Barbero Test  |         14|
|Corte fade 16       |Barbero Test 2|         13|
|Combo corte y barba |Barbero Test  |         12|
|Corte fade 86       |Barbero Test 2|         11|
+--------------------+--------------+-----------+
```

**Patrón encontrado**: "Corte fade 16" con "Barbero Test 1" es la combinación más frecuente del sistema (20 citas).

---

## Tipos de Conjuntos de Datos

### Split Train / Validation / Test (60% / 20% / 20%)

```
Dataset Total: 283 citas

┌─────────────────────────┬──────────────────────────────┐
│    ENTRENAMIENTO 60%    │      EVALUACIÓN 40%          │
│    174 registros        ├──────────────┬───────────────┤
│                         │ VALIDACIÓN   │ TEST          │
│  Para AJUSTAR el modelo │  55 reg.     │  54 reg.      │
│                         │  20% total   │  20% total    │
│                         │ Para ELEGIR  │ Para MEDIR    │
│                         │ hiperparáms  │ rendimiento   │
│                         │ del modelo   │ final         │
└─────────────────────────┴──────────────┴───────────────┘
```

**Método de división**: `randomSplit([0.8, 0.2], seed=42)` → `[0.75, 0.25]` para extraer validación del 80%.

Seed `42` garantiza reproducibilidad — la misma split se obtiene en cualquier ejecución.

---

### Validación Cruzada K-Fold (k=5)

```
Dataset: 283 citas → 5 folds de ~56 registros cada uno

Fold 1: [TEST]  [TRAIN] [TRAIN] [TRAIN] [TRAIN]  → métrica_1
Fold 2: [TRAIN] [TEST]  [TRAIN] [TRAIN] [TRAIN]  → métrica_2
Fold 3: [TRAIN] [TRAIN] [TEST]  [TRAIN] [TRAIN]  → métrica_3
Fold 4: [TRAIN] [TRAIN] [TRAIN] [TEST]  [TRAIN]  → métrica_4
Fold 5: [TRAIN] [TRAIN] [TRAIN] [TRAIN] [TEST]   → métrica_5

Resultado final: promedio(métrica_1 ... métrica_5)
```

**Ventaja del K-Fold sobre un split simple**: usa el 100% de los datos tanto para entrenamiento como para validación, dando una estimación más robusta del rendimiento real. Se usa en `03_regresion_analytics.py` con `numFolds=3`.

---

## Resumen: Tipos de Minería aplicados

```
Tipo              | Supervisado | Variable objetivo | Script UrbanBlade
──────────────────────────────────────────────────────────────────────
Clasificación     | Sí          | cancelada (0/1)   | 05_bosque_aleatorio.py
Regresión         | Sí          | precio (float)    | 03_regresion_analytics.py
Clustering        | No          | ninguna           | 02_kmeans.py
Reglas asociación | No          | ninguna           | 01_mapreduce.py
Reducción dim.    | No          | ninguna           | 06_pca.py
Red neuronal      | Sí          | clase ingreso     | 07_red_neural.py
```

---

## Observaciones técnicas

- El 19.1% de cancelaciones indica un problema real en el negocio — predecir cancelaciones con RandomForest tiene valor operativo concreto
- El dataset de 283 registros es pequeño para ML — los splits resultan en solo 54 ejemplos de test, lo que da alta varianza en las métricas
- La combinación "Corte fade 16 + Barbero Test 1" (20 citas) sugiere que los clientes tienen barbero preferido para servicios específicos — útil para recomendaciones
- K-fold con `numFolds=3` (en vez de 5) se prefirió en este dataset pequeño para que cada fold tenga suficientes ejemplos de entrenamiento
