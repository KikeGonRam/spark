# 07 — Red Neuronal (PyTorch)

## Descripción

Combina PySpark (para preprocesamiento y escalado) con PyTorch (para entrenar la red neuronal). Clasifica citas en 3 categorías de ingreso.

Pipeline:
```
Spark: VectorAssembler → StandardScaler → toPandas()
PyTorch: tensor → Red Neuronal → CrossEntropyLoss → Adam
```

---

## Dataset

20 filas representativas de rangos reales de `barber_db`:

| duracion_min | precio ($) | clase |
|-------------|-----------|-------|
| 20 min | 100–160 | 0 = Ingreso bajo (<$200) |
| 30–45 min | 200–320 | 1 = Ingreso medio ($200–$450) |
| 60 min | 450–650 | 2 = Ingreso alto (>$450) |

Split: 80/20 (16 train, 4 test).

---

## Arquitectura de la red

```
Input(2) → Linear(2→16) → ReLU → Linear(16→8) → ReLU → Linear(8→3) → Softmax
```

- Entradas: `duracion_min`, `precio` (ya escalados por StandardScaler)
- Salida: 3 clases (bajo, medio, alto)
- Optimizador: Adam (lr=0.01)
- Pérdida: CrossEntropyLoss
- Epochs: 100

---

## Resultados de entrenamiento

| Epoch | Loss |
|-------|------|
| 0 | 1.1571 |
| 10 | 0.9626 |
| 20 | 0.7445 |
| 30 | 0.4691 |
| 40 | 0.2415 |
| 50 | 0.1078 |
| 60 | 0.0487 |
| 70 | 0.0237 |
| 80 | 0.0136 |
| 90 | 0.0090 |

**Precisión en test: 100%** (4/4 correctas)

---

## Predicción de ejemplo

```
Cita: 45 min / $300 MXN
Predicción: Ingreso alto (>$450)
Probabilidades: [[0. 0. 1.]]
```

### Análisis de la predicción

La predicción "Ingreso alto" para una cita de $300 parece incorrecta a primera vista (debería ser "medio"). Esto ocurre porque:

1. El dataset de 20 filas es muy pequeño — el modelo sobreajusta
2. `$300` después del escalado StandardScaler cae en zona de "alto" dentro de los 20 ejemplos de entrenamiento
3. Las probabilidades son `[0, 0, 1]` — certeza absoluta, señal clara de sobreajuste

En producción se necesitarían al menos 1,000+ ejemplos para generalizar bien.

---

## Observaciones técnicas

- **UserWarning: Creating a tensor from a list of numpy.ndarrays is extremely slow** — warning menor de PyTorch. Se puede suprimir convirtiendo a `np.array()` primero: `torch.tensor(np.array(X_train), ...)`. No afecta el resultado.
- El escalado con Spark → toPandas → PyTorch es el puente correcto entre ambos frameworks
- El modelo PyTorch NO se guarda en disco (solo el Random Forest de 05 se guarda)
