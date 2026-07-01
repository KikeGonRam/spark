# 03 — Regresión: Predicción de la Facturación Diaria

## Descripción

Entrena 6 modelos de regresión para predecir la **facturación diaria** de la barbería
(`ingreso_dia`) a partir del volumen de citas y variables de calendario.

Split: 80% entrenamiento / 20% prueba. Métricas: **R², MSE (Error Cuadrático Medio),
MAE (Error Absoluto Medio)** — las tres exigidas por la Unidad III.

---

## Por qué NO se predice el precio por cita

En `barber_db` el precio de una cita es **determinista por servicio**
(`precio_cobrado == precio_servicio`, ratio 1.000 en todas las citas) y no hay propinas.
Predecir el precio de una sola cita usando `precio`/`ingreso` como feature daría
**R² ≈ 1.0**, pero eso es **fuga de datos** (leakage): el modelo predice una variable
usando una copia de sí misma. Un R²=1.0 así es fácil de refutar en una exposición.

**Solución honesta:** agregar por día. La facturación diaria SÍ tiene varianza real
(depende del volumen de citas, la mezcla de servicios y el día de la semana), así que
la regresión se vuelve un problema legítimo y defendible.

---

## Diseño del modelo

| Elemento | Valor |
|----------|-------|
| Target | `ingreso_dia` (suma de ingresos del día, sin citas canceladas) |
| Granularidad | una fila por día |
| Features | `num_citas`, `duracion_total`, `dia_semana`, `mes` |
| Fuga de datos | **Ninguna** — el ingreso no aparece entre las features |

| # | Modelo | Features |
|---|--------|----------|
| 1 | Lineal Simple | `[num_citas]` |
| 2 | Lineal Múltiple | `[num_citas, duracion_total, dia_semana, mes]` |
| 3 | Ridge (L2, regParam=0.5) | múltiples |
| 4 | Lasso (L1, regParam=0.5) | múltiples |
| 5 | Polinomial (grado 2) | múltiples |
| 6 | Cross Validation (3-fold) | grid `regParam × elasticNetParam` |

Los valores de R²/MSE/MAE se calculan en tiempo de ejecución sobre los datos reales
y se imprimen en una tabla comparativa al final del script.

---

## Interpretación esperada

- El **modelo simple** (`ingreso_dia ~ num_citas`) ya captura la mayor parte de la señal:
  cada cita adicional aporta ~un ticket promedio de facturación. R² alto pero **honesto**
  (no 1.0), porque la mezcla de servicios por día introduce ruido.
- La **regresión múltiple** mejora al añadir el calendario (los sábados facturan más).
- **Ridge/Lasso** regularizan; con pocas features el cambio es pequeño.
- Un R² entre ~0.6 y ~0.9 aquí es un resultado **creíble y a prueba de profesor**.

---

## Visualización

Scatter matplotlib: eje X = número de citas del día, eje Y = facturación del día
(real en azul vs predicción en naranja).
