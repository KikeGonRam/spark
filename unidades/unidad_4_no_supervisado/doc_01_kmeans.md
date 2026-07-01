# 02 — KMeans Clustering

## Descripción

Agrupa las 283 citas en K clusters según sus características numéricas:
- `duracion_min`: duración del servicio en minutos
- `precio`: precio cobrado en MXN
- `ingreso`: igual a precio (una cita = un servicio)

Usa `VectorAssembler` para vectorizar las 3 features y `KMeans(k=3, seed=42)`.

---

## Resultados

**Silhouette Score: 0.7051 → Buena segmentación**

### Centroides (duracion_min | precio | ingreso)

| Cluster | duracion_min | precio ($) | ingreso ($) | # Citas |
|---------|-------------|------------|-------------|---------|
| 0 | 35.67 min | $395.29 | $395.29 | 127 |
| 1 | 38.24 min | $174.40 | $174.40 | 71 |
| 2 | 46.06 min | $574.57 | $574.57 | 85 |

### Distribución de clusters

```
+-------+-----+
|cluster|count|
+-------+-----+
|      0|  127|  → Segmento Medio
|      1|   71|  → Segmento Económico
|      2|   85|  → Segmento Premium
+-------+-----+
```

---

## Interpretación de segmentos

| Cluster | Perfil | Precio promedio | Citas |
|---------|--------|----------------|-------|
| **0** | Segmento Operativo / Medio | $395 | 127 (44.9%) |
| **1** | Segmento Económico | $174 | 71 (25.1%) |
| **2** | Segmento Premium | $575 | 85 (30.0%) |

**El segmento más grande (Cluster 0) es el operativo**, con precios medios (~$395 MXN) y duraciones intermedias (~36 min).

**El segmento Premium (Cluster 2)** tiene los precios más altos ($575 promedio) y las duraciones más largas (46 min), indicando servicios especializados.

---

## Observaciones técnicas

- **Silhouette 0.7051**: excelente separación. Significa que las citas están mucho más cerca de su propio cluster que del siguiente más cercano.
- `precio` e `ingreso` son idénticos (ingreso = precio), por lo que la tercera dimensión del vector no añade información nueva. El clustering efectivo ocurre sobre 2 dimensiones reales.
- El método del codo (Elbow) está implementado en `dashboard_kmeans.py` para seleccionar K óptimo visualmente.
