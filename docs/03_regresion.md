# 03 — Regresión: Predicción de Ingresos

## Descripción

Entrena 6 modelos de regresión para predecir `ingreso` a partir de las features `duracion_min` y `precio`.

Split: 80% entrenamiento / 20% prueba. Métrica: R² (coeficiente de determinación).

---

## Modelos y resultados

| # | Modelo | Features | R² |
|---|--------|----------|-----|
| 1 | Regresión Lineal Simple | `[duracion_min]` | -0.0369 |
| 2 | Regresión Lineal Múltiple | `[duracion_min, precio]` | **1.0** |
| 3 | Ridge (regParam=0.5) | `[duracion_min, precio]` | 0.9999 |
| 4 | Lasso (regParam=0.5) | `[duracion_min, precio]` | 0.9999 |
| 5 | Regresión Polinómica (degree=2) | `[duracion_min, precio]` | **1.0** |
| 6 | Cross Validation | `[duracion_min, precio]` | ≈1.0 |

**Mejor modelo: Regresión Lineal Múltiple**

---

## Por qué R² = 1.0

Los modelos 2–6 alcanzan R²=1.0 porque `ingreso = precio` exactamente (una cita = un servicio, sin multiplicador). El modelo aprende la identidad `ingreso ≈ 1.0 × precio + 0 × duracion_min + 0`.

Esto NO es sobreajuste — es un artefacto de la definición del campo. En un escenario real con múltiples servicios por cita o propinas, `ingreso` sería distinto de `precio` y los R² bajarían a valores más realistas.

### Modelo 1 (R² = -0.037)

R² negativo significa que `duracion_min` sola **no predice ingreso**. La duración del servicio (30, 45, 75 min) no está correlacionada con el precio cobrado — un servicio de 30 min puede costar desde $108 hasta $632.

---

## Visualizaciones generadas

Cada modelo genera una gráfica matplotlib con:
- Eje X: `duracion_min`
- Eje Y: `ingreso` (real vs predicho)
- Dos scatter: puntos reales (azul) y predicciones (naranja)

---

## Observaciones técnicas

- Ridge y Lasso penalizan los coeficientes: R² baja mínimamente de 1.0 a 0.9999 por el término de regularización, lo cual es esperado
- Cross Validation hace grid search sobre `regParam ∈ {0.01, 0.1, 1.0}` × `elasticNetParam ∈ {0, 0.5, 1.0}` con 3 folds
- Polinomial degree=2 no mejora sobre la versión lineal porque la relación ya es perfectamente lineal
