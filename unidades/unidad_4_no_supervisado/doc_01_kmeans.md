# 01 — KMeans Clustering

## Descripción

Agrupa las 12,505 citas reales en K clusters según sus características numéricas:
- `duracion_min`: duración del servicio en minutos
- `precio`: precio cobrado en MXN
- `ingreso`: igual a precio (una cita = un servicio)

Usa `VectorAssembler` para vectorizar las 3 features y `KMeans(k=3, seed=42)`, con el
**Método del Codo** ejecutado primero (k=2 a k=9) para justificar la elección de K=3.

---

## Método del Codo (WCSS)

```
k=2  WCSS=152,124,957.18
k=3  WCSS= 51,515,440.99   ← codo: la caída se vuelve mucho más gradual después de aquí
k=4  WCSS= 32,748,256.50
k=5  WCSS= 13,916,908.32
k=6  WCSS=  8,967,975.62
k=7  WCSS=  2,454,482.75
k=8  WCSS=  1,948,125.55
k=9  WCSS=  1,322,554.98
```

Se elige **K=3** porque es el punto donde añadir más clusters deja de reducir el WCSS de
forma proporcional (criterio del "codo"), y porque 3 segmentos (básico/estándar/premium)
tiene interpretación de negocio clara y accionable.

---

## Resultados (ejecución sobre el dataset actual, 12,505 citas)

**Silhouette Score: 0.7430 → Buena segmentación**

### Centroides (duracion_min | precio | ingreso)

| Cluster | duracion_min | precio ($) | ingreso ($) | # Citas | % |
|---------|-------------|------------|-------------|---------|---|
| 0 | 42.9 min | $382.06 | $382.06 | 7,545 | 60.3% |
| 1 | 75.0 min | $820.00 | $820.00 | 602 | 4.8% |
| 2 | 24.3 min | $247.76 | $247.76 | 4,358 | 34.9% |

### Distribución de clusters

```
+-------+-----+
|cluster|count|
+-------+-----+
|      0| 7545|  → ESTÁNDAR
|      1|  602|  → PREMIUM
|      2| 4358|  → BÁSICO
+-------+-----+
```

---

## Interpretación de segmentos

| Cluster | Perfil | Duración | Precio promedio | Citas |
|---------|--------|----------|-----------------|-------|
| **0** | ESTÁNDAR | 42.9 min | $382 | 7,545 (60.3%) |
| **1** | PREMIUM | 75.0 min | $820 | 602 (4.8%) |
| **2** | BÁSICO | 24.3 min | $248 | 4,358 (34.9%) |

Servicios representativos de cada cluster (top por conteo):

- **Cluster 0 (Estándar)**: Combo Clásico, Keratina Express, Pompadour, Undercut, Fade
  Clásico, Coloración Capilar, Skin Fade.
- **Cluster 1 (Premium)**: Combo Premium (único servicio que cae aquí — el más caro y
  de mayor duración del catálogo).
- **Cluster 2 (Básico)**: Corte Texturizado, Perfilado de Barba, Buzz Cut, Corte
  Clásico, Masaje de Cuero Cabelludo, Hidratación de Barba.

**El segmento más grande es el Estándar (60.3%)** — la mayoría del volumen de negocio
ocurre en servicios de precio y duración media. **El segmento Premium es pequeño en
volumen (4.8%) pero de alto valor por cita** ($820 vs. $382/$248) — candidato natural
para estrategias de upsell dado que aporta ingreso desproporcionado a su frecuencia.

---

## Observaciones técnicas

- **Silhouette 0.7430**: buena separación — las citas están mucho más cerca de su propio
  cluster que del siguiente más cercano. Es consistente con el resultado del Método del
  Codo, que también señala K=3 como punto de inflexión claro.
- `precio` e `ingreso` son idénticos (`ingreso = precio_cobrado` siempre en este dataset),
  por lo que la tercera dimensión del vector no añade información nueva — el clustering
  efectivo ocurre sobre 2 dimensiones reales (`duracion_min`, `precio`). Esta es la misma
  observación metodológica que motivó el rediseño de los modelos supervisados en la
  Unidad III (evitar variables redundantes/colineales).
- El Método del Codo y el Silhouette están ambos calculados dentro del mismo script
  (`unidades/unidad_4_no_supervisado/01_kmeans.py`), no en un dashboard separado.
