# 05 — Random Forest (Bosque Aleatorio)

## Descripción

Predice si una cita será **cancelada** (1) o no (0) usando un Pipeline de PySpark:

```
VectorAssembler → RandomForestClassifier(50 árboles, maxDepth=5)
```

Label:
```
categoria = 1  si  estado == "cancelada"
categoria = 0  cualquier otro estado (completada, pendiente, confirmada, en_proceso, no_asistio)
```

Split: 70/30.

---

## Resultados

| Métrica | Valor |
|---------|-------|
| **AUC (área bajo curva ROC)** | **0.6523** |
| Citas test totales | 84 |
| Predicciones correctas (no cancelada) | 66 / 66 |
| Canceladas detectadas | 2 / 18 |
| Canceladas no detectadas (falsos negativos) | 16 |

### Matriz de confusión

```
+---------+----------+-----+
|categoria|prediction|count|
+---------+----------+-----+
|        0|       0.0|   66|  ← Verdadero Negativo (predijo no cancelada, era no cancelada)
|        1|       0.0|   16|  ← Falso Negativo (predijo no cancelada, era cancelada)
|        1|       1.0|    2|  ← Verdadero Positivo (detectó cancelada correctamente)
+---------+----------+-----+
```

### Importancia de variables

| Variable | Importancia |
|----------|-------------|
| `duracion_min` | 0.1911 (19%) |
| `precio` | 0.2344 (23%) |
| `ingreso` | 0.5745 (57%) |

---

## Interpretación

**AUC = 0.6523**: el modelo tiene poder discriminatorio moderado — mejor que azar (0.5) pero no ideal. Esto es esperado porque las cancelaciones en este dataset parecen ocurrir independientemente del precio o duración.

El modelo predice casi siempre clase 0 (no cancelada) porque el dataset es **muy desbalanceado**: ~80% de las citas no son cancelaciones. Con sólo 18 canceladas en test, el modelo aprende que la respuesta segura es siempre predecir "no cancelada".

**Importancia**: `ingreso` domina (0.57) porque `ingreso ≡ precio` y el modelo usa la variable más redundante con mayor peso de las 3 features.

---

## Observaciones técnicas

- **50 árboles** con **maxDepth=5**: suficiente para este tamaño de dataset (283 filas)
- El modelo fue guardado en disco: `modelo_pipeline_rf_urbanblade/`
- Para mejorar la detección de cancelaciones se recomienda:
  - `class_weight` balanceado (oversampling de cancelaciones)
  - Agregar features de fecha/hora (las cancelaciones pueden ser más frecuentes en ciertos días)
  - Incluir historial del cliente
- El Pipeline encapsula preprocesamiento + modelo para que cualquier dataset nuevo pueda ser predicho directamente
