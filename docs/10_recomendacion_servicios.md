# Script 10: Recomendación de Servicios

**Script**: `ml_algorithms/10_recomendacion_servicios.py`  
**Dashboard**: `analytics/dashboard_recomendacion.py`  
**Dataset**: 283 citas reales (solo completadas/confirmadas) — `barber_db`  
**Datos reales**: Sí — join de `appointments + services + users`

---

## Objetivo

Descubrir patrones de compra entre clientes para implementar recomendaciones del tipo "Clientes que solicitan X también solicitan Y", aumentando el ticket promedio por visita (upsell/cross-sell).

---

## Técnica: FP-Growth (Frequent Pattern Mining)

Adaptación de Market Basket Analysis a la barbería:

| Concepto original | Adaptación UrbanBlade |
|---|---|
| Ticket de supermercado | Historial de servicios de un cliente |
| Producto comprado | Servicio de barbería agendado |
| Clientes del supermercado | Clientes de la barbería |

Cada **transacción** = conjunto de servicios únicos que ha pedido un cliente a lo largo de su historial.

---

## Métricas de asociación

| Métrica | Fórmula | Interpretación |
|---|---|---|
| **Support** | count(A ∩ B) / n_clientes | % de clientes que piden A y B juntos |
| **Confidence** | count(A ∩ B) / count(A) | De los que piden A, ¿qué % también pide B? |
| **Lift** | confidence(A→B) / P(B) | ¿Cuánto más probable es B dado A vs azar? |

Umbrales utilizados:
- `minSupport = 0.10` (al menos 10% de los clientes)
- `minConfidence = 0.20` (20% de confianza mínima)

---

## Resultados esperados

Con el dataset actual (283 citas, ~25 clientes, 12 servicios):

**Itemsets frecuentes** — combinaciones de servicios que el mismo cliente ha pedido:

```
Servicio(s)                              | Frecuencia (clientes)
─────────────────────────────────────────┼──────────────────────
[Corte fade 16]                          | ~20 clientes
[Arreglo de barba 53]                    | ~15 clientes
[Corte fade 16, Combo corte y barba]     | ~8 clientes
[Corte clásico 45, Arreglo de barba 53] | ~6 clientes
```

**Reglas de asociación** (ejemplo):

```
Si pide               | Recomendar              | Confianza | Lift
──────────────────────┼─────────────────────────┼───────────┼──────
Corte fade 16         | Arreglo de barba 53     | ~45%      | ~1.8
Combo corte y barba   | Tratamiento capilar     | ~35%      | ~2.1
Corte clásico 45      | Corte fade 16           | ~30%      | ~1.5
```

> Lift > 1.0 = asociación positiva (el cliente tiene más probabilidad de pedir B si ya pidió A que si lo eligiera al azar)

---

## Análisis de co-ocurrencia por categoría

Clientes que usaron 2 o más categorías de servicio (corte + barba + combo + tratamiento):

- Estos clientes son los **mejores candidatos para upsell cruzado**
- En el dataset actual: ~40-60% de los clientes han usado al menos 2 categorías

---

## Populariedad de servicios (base de recomendaciones)

Top 5 servicios más pedidos (completadas/confirmadas):

```
Servicio                | Veces pedido | Clientes distintos
────────────────────────┼──────────────┼───────────────────
Corte fade 16           | ~35          | ~15
Combo corte y barba     | ~28          | ~12
Corte clásico 45        | ~25          | ~11
Arreglo de barba 53     | ~22          | ~10
Corte clásico 3         | ~20          | ~10
```

---

## Dashboard

El dashboard `dashboard_recomendacion.py` incluye:

1. **KPIs**: Clientes analizados, servicios distintos, reglas encontradas, mejor lift
2. **Sliders**: ajustar support y confianza mínima en tiempo real
3. **Tabla de reglas**: ordenada por lift (mayor lift = recomendación más fuerte)
4. **Ranking de servicios**: gráfica horizontal por popularidad
5. **Simulador interactivo**: seleccionas un servicio y muestra que recomendar con confianza y lift
6. **Heatmap de co-ocurrencia**: qué servicios comparten los mismos clientes (top 8)
7. **Clientes multi-categoría**: histograma de diversidad de consumo

---

## Comandos de ejecución

```bash
# Script PySpark
python3 ml_algorithms/10_recomendacion_servicios.py

# Dashboard interactivo
streamlit run analytics/dashboard_recomendacion.py
```

---

## Implementación recomendada en UrbanBlade

| Punto de contacto | Recomendación |
|---|---|
| Al crear la cita (web/app) | Pop-up: "También te puede interesar: Arreglo de barba — $230" |
| Email post-cita | "Clientes como tú que piden Corte fade también reservaron..." |
| Dashboard admin | Lista de oportunidades de upsell ordenadas por lift |
| WhatsApp automatizado | "Tu próxima visita podría incluir tratamiento capilar — reserva ahora" |

---

## Observaciones técnicas

- FP-Growth con `minSupport=0.10` y solo 25 clientes significa que una regla requiere aparecer en al menos 3 clientes — umbral muy bajo pero necesario para el dataset pequeño
- En producción con 500+ clientes: subir `minSupport` a 0.05 y `minConfidence` a 0.30 para reglas más robustas
- El fallback de co-ocurrencia por categoría siempre produce resultados aunque no haya reglas con los umbrales actuales
