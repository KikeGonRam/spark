# Script 08: Segmentación de Clientes (RFM + KMeans)

**Script**: `ml_algorithms/08_segmentacion_clientes.py`
**Datos**: `barber_db` (MongoDB Atlas) — **12,535 citas, 1000 clientes reales**
**Capa de datos**: `get_clientes_df()` (RFM por cliente) desde el conector único

---

## Objetivo

Clasificar a cada cliente en uno de 4 segmentos según su comportamiento real de
consumo, para campañas de marketing dirigidas.

---

## Corrección importante respecto a la versión anterior

`client_id` referencia la colección `clients`, **no** `users`. La versión anterior
resolvía el nombre contra `users` y mostraba a todos como "Cliente". Ahora se usa la
ruta correcta `client_id → clients → user_id → users.name`, con **1000 clientes reales**
(no ~25). Además `clients` aporta `nivel` (regular/vip) y `puntos`.

---

## Métricas por cliente (RFM)

| Variable | Descripción |
|---|---|
| `total_citas` | Número de citas |
| `gasto_total` | Suma de ingresos del cliente |
| `gasto_promedio` | Ticket promedio |
| `tasa_cancelacion_pct` | % de citas canceladas |
| `dias_sin_cita` | Recencia (días desde la última cita) |

---

## Modelo: KMeans k=4

- **StandardScaler** (media=0, desv=1) antes de agrupar.
- **k=4** (uno por segmento de negocio), seed=42.
- **Silhouette Score** calculado en ejecución.

---

## Segmentos (etiquetado automático)

El cluster con mayor `gasto_total_prom` = **VIP**, el segundo = **Alto consumo**,
el de mayor recencia = **Inactivo**, el restante = **Frecuente**.

| Segmento | Perfil | Acción de marketing |
|---|---|---|
| **VIP** | Mayor gasto + baja cancelación + frecuentes | Tarjeta premium, descuento 15% |
| **Alto consumo** | Ticket alto | Membresía mensual todo incluido |
| **Frecuente** | Visitas regulares, gasto moderado | Programa de puntos, 10ª cita gratis |
| **Inactivo** | Muchos días sin cita | Reactivación: 20% en su próxima cita |

---

## Comandos de ejecución

```bash
# Script PySpark
spark-submit ml_algorithms/08_segmentacion_clientes.py

# En el dashboard unificado: pestaña "Segmentacion Clientes"
streamlit run analytics/main_dashboard.py
```

---

## Nota técnica

Con 1000 clientes reales el Silhouette Score es estable. El etiquetado por orden de
gasto es robusto: VIP siempre será el cluster de mayor gasto, sin importar cómo KMeans
asigne los índices internos.
