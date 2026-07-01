# 01 — MapReduce: Ingresos por Servicio

## Descripción

Implementa el patrón MapReduce con PySpark para calcular el ingreso total por tipo de servicio.

- **MAP**: agrupa cada cita por `servicio`
- **REDUCE**: suma el campo `ingreso` (= `precio_cobrado`) de cada grupo

## Fuente de datos

| Colección | Campo usado |
|---|---|
| `appointments` | `precio_cobrado`, `estado`, `barber_id`, `service_id` |
| `services` | `nombre`, `precio`, `duracion_min` |
| `barbers` + `users` | `user_id` → `users.name` |

Total citas procesadas: **283**

---

## Resultados (01_mapreduce.py)

```
+--------------------+------------------+
|            servicio|     total_ingreso|
+--------------------+------------------+
|       Corte fade 16|          20163.05|  ← Servicio Estrella
|    Corte clásico 45|          12359.32|
|       Corte fade 86|          11504.15|
| Arreglo de barba 53|          11444.93|
|     Corte clásico 3|          11403.93|
|Combo corte y bar...|           9553.49|
|    Corte clásico 60|           8924.58|
|Combo corte y bar...|           8776.98|
|Combo corte y bar...|           6791.91|
|       Corte fade 66|           6172.01|
|  Arreglo de barba 3|           4328.18|
+--------------------+------------------+
```

---

## Resultados avanzados (01_mapreduce_analytics_sinnulos.py)

```
+--------------------+------------------+------------------+------------------+------------+
|            servicio|     ingreso_total|   precio_promedio| duracion_promedio|numero_citas|
+--------------------+------------------+------------------+------------------+------------+
|       Corte fade 16|          20163.05|            411.49|             50.20|          49|
|    Corte clásico 45|          12359.32|            398.69|             30.00|          31|
|       Corte fade 86|          11504.15|            442.47|             30.00|          26|
| Arreglo de barba 53|          11444.93|            476.87|             75.00|          24|
|     Corte clásico 3|          11403.93|            356.37|             30.00|          32|
|Combo corte y bar...|           9553.49|            398.06|             30.00|          24|
|    Corte clásico 60|           8924.58|            469.71|             30.00|          19|
|Combo corte y bar...|           8776.98|            351.08|             45.00|          25|
|Combo corte y bar...|           6791.91|            452.79|             45.00|          15|
|       Corte fade 66|           6172.01|            342.89|             30.00|          18|
|  Arreglo de barba 3|           4328.18|            216.41|             30.00|          20|
+--------------------+------------------+------------------+------------------+------------+
```

---

## Interpretación

| Servicio | Categoría |
|---|---|
| Corte fade 16 | **Servicio Estrella** — mayor ingreso ($20,163) con 49 citas |
| Arreglo de barba 53 | Servicio de alta duración (75 min) y precio promedio más alto ($476.87) |
| Arreglo de barba 3 | Menor ingreso total ($4,328) — menor precio promedio ($216) |

**Ingreso total del sistema: ~$111,422 MXN en 283 citas**

---

## Observaciones técnicas

- El patrón MapReduce corre completamente distribuido en Spark — cada executor procesa un subset de particiones
- `ingreso = precio_cobrado` (un servicio por cita)
- Los servicios aparecen con número al final (ej. "Corte fade 16") porque el ServiceFactory genera nombres con faker + sufijo numérico
