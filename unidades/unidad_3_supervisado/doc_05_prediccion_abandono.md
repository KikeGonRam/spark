# Script 09: Predicción de Abandono de Clientes (Churn)

**Script**: `ml_algorithms/09_prediccion_abandono.py`
**Datos**: `barber_db` (MongoDB Atlas) — **12,535 citas, 1000 clientes reales**
**Capa de datos**: `get_clientes_df()` (RFM por cliente) desde el conector único

---

## Objetivo

Identificar qué clientes tienen mayor probabilidad de dejar de asistir, **antes** de
que ocurra, para activar campañas de retención a tiempo.

---

## Corrección importante respecto a la versión anterior

1. **Nombres de cliente reales.** `client_id` referencia la colección `clients`,
   NO `users`. La versión anterior resolvía el nombre contra `users` y mostraba a
   **todos** como "Cliente". Ahora la ruta correcta es
   `client_id → clients → user_id → users.name`.
2. **Sin fuga de datos.** Antes la etiqueta se definía con `dias_sin_cita` y esa
   misma variable se usaba como feature (circular) → AUC artificialmente perfecto.
   Ahora la recencia define la etiqueta pero **no** entra como feature.
3. **Evaluación real.** Se añadió split **train/test 70/30**; el AUC se mide sobre
   clientes no vistos.

---

## Feature Engineering por cliente (RFM)

| Feature | Cálculo | Rol |
|---|---|---|
| `total_citas` | `count(*)` | Frecuencia / antigüedad |
| `gasto_promedio` | `mean(ingreso)` | Valor por visita |
| `gasto_total` | `sum(ingreso)` | Valor monetario total |
| `tasa_cancelacion_pct` | `canceladas / total * 100` | Confiabilidad |
| `frecuencia_mensual` | `total_citas / meses_activo` | Ritmo de visitas |
| `meses_activo` | rango de fechas / 30 | Tenure |

La **recencia** (`dias_sin_cita`) se usa solo para definir la etiqueta, no como feature.

---

## Definición de riesgo (label)

```
en_riesgo = 1  si  dias_sin_cita > percentil_70(dias_sin_cita)
```

El umbral (percentil 70) se calcula sobre los datos reales en tiempo de ejecución.

---

## Modelo: Random Forest Classifier

| Parámetro | Valor |
|---|---|
| `numTrees` | 100 |
| `maxDepth` | 5 |
| Split | 70% train / 30% test |
| Métrica principal | AUC-ROC (sobre test) + F1 |

El modelo aprende a anticipar el abandono a partir del **patrón de consumo**
(frecuencia, gasto, cancelaciones, tenure), no de la variable que define la etiqueta.

---

## Salida

- Métricas AUC / Accuracy / F1 sobre el conjunto de prueba.
- Importancia de variables (qué patrón anticipa mejor el abandono).
- Lista de clientes en riesgo con **probabilidad de abandono** del modelo, con nombres reales.

---

## Acciones de retención

| Probabilidad | Acción |
|---|---|
| > 70% | Llamada personal + oferta urgente |
| 40–70% | WhatsApp + descuento 15% |
| < 40% | Newsletter mensual |

---

## Comandos de ejecución

```bash
# Script PySpark
spark-submit ml_algorithms/09_prediccion_abandono.py

# En el dashboard unificado: pestaña "Churn / Abandono"
streamlit run analytics/main_dashboard.py
```
