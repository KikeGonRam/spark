# 04 — Árbol de Decisión

## Descripción

Clasifica citas en **alto valor** (1) o **bajo valor** (0) según si el ingreso supera los $500 MXN.

```
label = 1  si  ingreso > 500  (cita de alto valor)
label = 0  si  ingreso ≤ 500  (cita de bajo valor)
```

Parámetros: `DecisionTreeClassifier(maxDepth=3)`. Split: 80/20.

---

## Estructura del árbol aprendido

```
DecisionTreeClassificationModel
  depth=1, numNodes=3, numClasses=2, numFeatures=3

  If (feature 1 <= 505.745)    ← feature 1 = precio
     Predict: 0.0              ← bajo valor
  Else (feature 1 > 505.745)
     Predict: 1.0              ← alto valor
```

El árbol colapsó a **profundidad 1** con una sola regla:
> **Si precio > $505.75 → cita de alto valor**

---

## Resultados

| Métrica | Valor |
|---------|-------|
| Datos entrenamiento | 229 |
| Datos prueba | 54 |
| **Accuracy** | **1.0 (100%)** |

### Muestra de predicciones

```
[30.0, 152.4, 152.4]  → label=0, pred=0.0  ✓
[30.0, 525.94, 525.94]→ label=1, pred=1.0  ✓
[75.0, 572.86, 572.86]→ label=1, pred=1.0  ✓
[30.0, 432.54, 432.54]→ label=0, pred=0.0  ✓
```

---

## Por qué accuracy = 1.0

Misma razón que en regresión: `ingreso = precio`. El árbol usa `feature 1` (precio) para predecir si `ingreso > 500`, pero `ingreso ≡ precio`, así que la regla `precio > 505.75 → label=1` es perfecta por definición.

El umbral 505.745 que el árbol aprendió corresponde a un punto medio entre el precio más alto ≤ 500 y el precio más bajo > 500 en el dataset de entrenamiento.

---

## Observaciones técnicas

- `maxDepth=3` se configuró pero el árbol convergió en depth=1 (sólo necesita 1 split para clasificar perfectamente)
- `numFeatures=3` pero efectivamente sólo usa la feature 1 (precio)
- `feature 0 = duracion_min`, `feature 1 = precio`, `feature 2 = ingreso`
- En datos reales con `ingreso ≠ precio` el árbol usaría las 3 features y alcanzaría una profundidad mayor con accuracy realista
