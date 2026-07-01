# Unidad III — Reporte de evaluación de modelos supervisados

**Asignatura:** Extracción del conocimiento en bases de datos · UTVT · IDGS-93
**Equipo:** Equipo UrbanBlade · **Docente:** MGTI. Héctor Velázquez Estrada

> Entregable de la Unidad III. Incluye: justificación del algoritmo, descripción del
> diseño del modelo, y reporte de evaluación y optimización (MSE, MAE, AUC).
> Las métricas exactas se generan al ejecutar cada script sobre los datos reales.

---

## 1. Modelos entregados

| # | Script | Tipo | Problema de negocio |
|---|---|---|---|
| 1 | `01_regresion.py` | Regresión | Predecir la facturación diaria |
| 2 | `02_arbol_decision.py` | Clasificación | ¿Se cancelará la cita? (árbol) |
| 3 | `03_bosque_aleatorio.py` | Clasificación | ¿Se cancelará la cita? (bosque) |
| 4 | `04_red_neuronal.py` | Clasificación (PyTorch) | Nivel de ingreso de la cita |
| 5 | `05_prediccion_abandono.py` | Clasificación | Churn de clientes |
| 6 | `06_prediccion_demanda.py` | Regresión (GBT) | Nº de citas por franja horaria |

---

## 2. Justificación de los algoritmos

- **Regresión Lineal (y variantes Ridge/Lasso/Polinomial):** relación interpretable entre
  volumen de citas y facturación; Ridge/Lasso controlan el sobreajuste.
- **Árbol de Decisión:** interpretable (muestra reglas), base para comparar con el ensemble.
- **Random Forest:** ensemble que reduce el sobreajuste del árbol único → mejor AUC.
- **Red Neuronal (PyTorch):** captura relaciones no lineales entre features escaladas.
- **GBT Regressor:** boosting robusto para predecir demanda por franja temporal.

---

## 3. Diseño de los modelos (sin fuga de datos)

| Modelo | Target | Features | Nota metodológica |
|---|---|---|---|
| Regresión | `ingreso_dia` | num_citas, duración, día, mes | Agregado por día (el precio por cita es determinista) |
| Árbol / Bosque | `es_cancelada` | duración, precio, hora, día, mes | El estado NO es feature |
| Red Neuronal | nivel ingreso (3 clases) | features escaladas | StandardScaler antes de la red |
| Churn | recencia > P70 | RFM sin la recencia | Split 70/30 real |
| Demanda | nº citas por slot | mes, día, hora | GBT, split 80/20 |

**Regla clave:** en ningún modelo la variable objetivo aparece (ni una copia suya) entre
las features. Por eso las métricas son realistas y defendibles.

---

## 4. Métricas de evaluación (Unidad III)

### Regresión — se reportan las tres exigidas por el documento
- **R²** (coeficiente de determinación): proporción de varianza explicada.
- **MSE** (Error Cuadrático Medio): penaliza errores grandes.
- **MAE** (Error Absoluto Medio): error promedio en las unidades del target ($MXN).

### Clasificación — con clases desbalanceadas (~8.4% cancelaciones)
- **AUC-ROC**: métrica principal (robusta al desbalance).
- **Accuracy / Precision / Recall / F1**: complementarias.
- **Matriz de confusión** para ver falsos negativos (cancelaciones no detectadas).

---

## 5. Optimización aplicada

- **Cross Validation (3-fold)** con grid `regParam × elasticNetParam` en la regresión.
- **maxDepth / numTrees** ajustados en árbol y bosque.
- **StandardScaler + Dropout + scheduler** en la red neuronal.
- **Comparación árbol vs bosque**: el ensemble mejora el AUC del árbol único.

---

## 6. Cómo reproducir

```bash
spark-submit unidades/unidad_3_supervisado/01_regresion.py
spark-submit unidades/unidad_3_supervisado/02_arbol_decision.py
spark-submit unidades/unidad_3_supervisado/03_bosque_aleatorio.py
python       unidades/unidad_3_supervisado/04_red_neuronal.py
spark-submit unidades/unidad_3_supervisado/05_prediccion_abandono.py
spark-submit unidades/unidad_3_supervisado/06_prediccion_demanda.py
```
