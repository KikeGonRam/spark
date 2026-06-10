# Script 09: Predicción de Abandono de Clientes (Churn)

**Script**: `ml_algorithms/09_prediccion_abandono.py`  
**Dashboard**: `analytics/dashboard_abandono.py`  
**Dataset**: 283 citas reales — `barber_db` (MongoDB Atlas)  
**Datos reales**: Sí — join de `appointments + services + users`

---

## Objetivo

Identificar qué clientes tienen mayor probabilidad de dejar de asistir a la barbería, antes de que ocurra, para activar campañas de retención a tiempo.

---

## Feature Engineering por cliente

Cada cliente se describe con 5 variables derivadas de su historial real:

| Feature | Cálculo | Interpretación |
|---|---|---|
| `dias_sin_cita` | `max(dias_desde_cita)` | Inactividad reciente |
| `gasto_promedio` | `mean(precio)` | Valor por visita |
| `tasa_cancelacion_pct` | `canceladas / total * 100` | Confiabilidad del cliente |
| `frecuencia_mensual` | `total_citas / meses_activo` | Ritmo de visitas |
| `total_citas` | `count(*)` | Antigüedad en el sistema |

---

## Definición de riesgo (label)

El label `en_riesgo = 1` se asigna si el cliente cumple **cualquiera** de:

```
dias_sin_cita > percentil_60(dias_sin_cita)   [umbral dinámico]
tasa_cancelacion > 30%
```

El umbral del percentil 60 se calcula automáticamente sobre los datos actuales para adaptarse a la distribución real del momento de ejecución.

Con el dataset actual de 283 citas:
- Umbral de días típico: ~15–25 días
- Distribución esperada: ~35-45% en riesgo / ~55-65% estables

---

## Modelo: Random Forest Classifier

| Parámetro | Valor |
|---|---|
| `numTrees` | 10 |
| `maxDepth` | 3 |
| `seed` | 42 |
| Train set | 100% (dataset pequeño — sin split) |

**Métricas esperadas** (varían con datos):

| Métrica | Valor típico |
|---|---|
| AUC-ROC | 0.75–0.95 |
| Accuracy | 0.75–0.90 |

> **Nota**: Con ~25 clientes el modelo aprende directamente de los datos de entrenamiento. En producción con cientos de clientes se haría split 80/20 y se mediría generalización real.

---

## Importancia de features

Orden esperado de importancia (de mayor a menor):

1. `dias_sin_cita` — el predictor más fuerte: inactividad reciente es la señal de abandono más clara
2. `tasa_cancelacion_pct` — clientes que cancelan frecuentemente tienen mayor riesgo
3. `frecuencia_mensual` — baja frecuencia → mayor riesgo
4. `gasto_promedio` — clientes con bajo ticket son más volátiles
5. `total_citas` — clientes nuevos tienen mayor riesgo que los leales

---

## Score de riesgo (dashboard)

El dashboard calcula un **score 0–100** para cada cliente:

```
score_riesgo = (dias_sin_cita / max_dias) * 60 + (tasa_cancelacion / 100) * 40
```

| Score | Nivel | Acción |
|---|---|---|
| >= 70 | URGENTE | Llamada personal + oferta especial inmediata |
| 40–69 | ATENCION | WhatsApp + descuento 15% |
| < 40 | PREVENTIVO | Newsletter mensual + recordatorio |

---

## Dashboard

El dashboard `dashboard_abandono.py` incluye:

1. **KPIs**: Total, En riesgo, Estables, Ingresos en riesgo ($)
2. **Sliders interactivos**: ajustar umbrales de días y % cancelación en tiempo real
3. **Bar chart horizontal**: Score de riesgo por cliente (rojo = riesgo, verde = estable)
4. **Scatter plot**: Días inactivo vs Tasa cancelación con líneas de umbral
5. **Tabla de acción**: clientes en riesgo ordenados por score, con colores por urgencia
6. **Expander**: clientes estables para contexto

---

## Comandos de ejecución

```bash
# Script PySpark
python3 ml_algorithms/09_prediccion_abandono.py

# Dashboard interactivo
streamlit run analytics/dashboard_abandono.py
```

---

## Valor de negocio

El costo de retener a un cliente existente es ~5x menor que adquirir uno nuevo. Con esta herramienta, el sistema UrbanBlade puede:

- Detectar los 3–5 clientes con mayor riesgo de fuga cada semana
- Enviar oferta personalizada antes de que se vayan
- Medir el éxito de la retención comparando scores antes y después de la campaña
