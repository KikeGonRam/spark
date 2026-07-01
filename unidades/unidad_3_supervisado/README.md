# Unidad III — Análisis supervisado

**Sesiones:** 11–12 · **Duración:** 20 h · **Evaluación:** 03-jul-2026 · **Grupo:** IDGS-93

Temas: algoritmos de aprendizaje supervisado (Regresión Lineal, Clasificación) ·
evaluación de modelos (Error Cuadrático Medio, Error Absoluto Medio).

---

## Entregables que pide el documento

- [x] **Documento** con justificación del algoritmo, descripción del diseño del modelo y
  reporte de evaluación y optimización → [`reporte_evaluacion.md`](reporte_evaluacion.md)
- [x] **Modelo de regresión y clasificación en el repositorio** → scripts 01–06 (abajo)

---

## Scripts

| Archivo | Técnica | Target | Métricas |
|---|---|---|---|
| `01_regresion.py` | Regresión lineal (6 modelos) | facturación diaria | R², MSE, MAE |
| `02_arbol_decision.py` | Árbol de Decisión | cancelación | AUC, Accuracy, F1 |
| `03_bosque_aleatorio.py` | Random Forest | cancelación | AUC, Accuracy, F1 |
| `04_red_neuronal.py` | Red Neuronal (PyTorch) | nivel de ingreso | Accuracy por clase |
| `05_prediccion_abandono.py` | Random Forest (churn) | abandono de cliente | AUC, F1 |
| `06_prediccion_demanda.py` | GBT Regressor | nº de citas por slot | R², RMSE |

Documentos de apoyo: `doc_01`…`doc_06` (uno por script).

---

## Clave metodológica: sin fuga de datos

Todos los modelos se diseñaron **sin leakage**: la variable objetivo (ni una copia suya)
aparece entre las features. Por eso las métricas son realistas (p. ej. R² ≈ 0.6–0.9,
no 1.0). Ver detalle en [`reporte_evaluacion.md`](reporte_evaluacion.md).

---

## Cómo ejecutar

```bash
spark-submit unidades/unidad_3_supervisado/01_regresion.py
python       unidades/unidad_3_supervisado/04_red_neuronal.py
```
