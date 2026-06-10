# Script 08: Segmentación de Clientes Premium

**Script**: `ml_algorithms/08_segmentacion_clientes.py`  
**Dashboard**: `analytics/dashboard_segmentacion_clientes.py`  
**Dataset**: 283 citas reales — `barber_db` (MongoDB Atlas)  
**Datos reales**: Sí — join de 4 colecciones (`appointments + services + barbers + users`)

---

## Objetivo

Clasificar a cada cliente en uno de 4 segmentos según su comportamiento real de consumo, para ofrecer experiencias personalizadas y campañas de marketing dirigidas.

---

## Métricas calculadas por cliente

Cada cliente se describe con 5 variables calculadas desde sus citas reales:

| Variable | Descripción |
|---|---|
| `total_citas` | Número de citas agendadas |
| `total_gasto` | Suma de todos los pagos registrados |
| `promedio_gasto` | Ticket promedio por cita |
| `tasa_cancelacion_pct` | % de citas canceladas sobre el total |
| `dias_inactivo` | Días desde su cita más antigua hasta hoy |

---

## Modelo: KMeans k=4

- **Normalización**: StandardScaler (media=0, desv=1) para que variables en distintas escalas no dominen
- **Clusters**: k=4 (uno por segmento de negocio)
- **Seed**: 42 (resultados reproducibles)
- **Silhouette Score**: ~0.45–0.65 (varía con los datos del momento)

---

## Segmentos identificados

El etiquetado es automático: el cluster con mayor `gasto_total_prom` se llama **VIP**, el segundo **Alto consumo**, el de mayor `dias_inactivo` se llama **Inactivo** y el restante **Frecuente**.

| Segmento | Perfil | Acción de marketing |
|---|---|---|
| **VIP** | Mayor gasto total + baja cancelación + visitas frecuentes | Tarjeta premium, descuento 15%, cita preferente |
| **Alto consumo** | Ticket promedio alto, servicios premium | Membresía mensual, paquete todo incluido |
| **Frecuente** | Visitas regulares, gasto moderado | Programa de puntos, 10a cita gratis |
| **Inactivo** | Muchos días sin cita reciente | WhatsApp/email reactivación, descuento 20% |

---

## Dataset de clientes con 32 usuarios en el sistema

Con 283 citas distribuidas entre ~25 clientes (los demás son admin/barbero/recepcionista):

- Cada cliente tiene en promedio **~11 citas** registradas
- El rango de gasto total va de **$100 a $6,500+ MXN** según historial
- La tasa de cancelación promedio es del **~19%** (consistente con el dataset general)

---

## Dashboard

El dashboard `dashboard_segmentacion_clientes.py` muestra:

1. **KPIs superiores**: Total clientes, VIP, Alto consumo, Frecuentes, Inactivos
2. **Pie chart**: Distribución porcentual de segmentos
3. **Bar chart**: Gasto promedio por segmento
4. **Scatter plot**: Gasto total vs Frecuencia de visitas, con tamaño = ticket promedio
5. **Tabla filtrable**: Detalle completo por cliente con filtro por segmento
6. **Panel de acciones**: Estrategia de marketing específica por cada segmento

---

## Comandos de ejecución

```bash
# Script PySpark (análisis en consola)
python3 ml_algorithms/08_segmentacion_clientes.py

# Dashboard interactivo (abrir http://localhost:8501 en Windows)
streamlit run analytics/dashboard_segmentacion_clientes.py
```

---

## Observaciones técnicas

- Con solo 25-30 clientes, el Silhouette Score tiene alta varianza — el modelo es más una demostración del proceso que un predictor estable
- En producción con miles de clientes, k=4 sigue siendo el número correcto de segmentos para esta estrategia de negocio
- El etiquetado automático por orden de gasto promedio es robusto: VIP siempre será el cluster de mayor gasto independientemente de cómo KMeans asigne los índices
- Se usa `StandardScaler` porque `dias_inactivo` puede ser 0–30 y `total_gasto` puede ser 100–6500, sin normalizar `total_gasto` dominaría completamente la distancia euclidiana
