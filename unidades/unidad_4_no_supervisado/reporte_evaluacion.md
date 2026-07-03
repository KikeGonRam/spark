# Unidad IV — Reporte de evaluación de modelos no supervisados

**Asignatura:** Extracción del conocimiento en bases de datos · UTVT · IDGS-93
**Equipo:** Equipo UrbanBlade · **Docente:** MGTI. Héctor Velázquez Estrada

> Entregable de la Unidad IV. Incluye: justificación del algoritmo, descripción de los
> resultados, y reporte de evaluación y optimización (Silhouette, WCSS / Método del Codo).
> Las métricas exactas se generan al ejecutar cada script sobre los datos reales.

---

## 1. Modelos entregados

| # | Script | Técnica | Problema de negocio |
|---|---|---|---|
| 1 | `01_kmeans.py` | Clustering (KMeans) | Agrupar citas por perfil |
| 2 | `02_pca.py` | Reducción de dimensionalidad (PCA) + KMeans | Visualizar y agrupar en 2 componentes |
| 3 | `03_segmentacion_clientes.py` | KMeans sobre RFM | Segmentar 1000 clientes (VIP/Frecuente/…) |
| 4 | `04_recomendacion_servicios.py` | Reglas de asociación (FP-Growth) | "Quien pide A también pide B" |

---

## 2. Justificación de los algoritmos

- **KMeans:** agrupa por similitud sin etiquetas; ideal para segmentar clientes/citas.
- **PCA:** reduce 3+ variables a 2 componentes para **visualizar** y quitar redundancia
  (necesario porque `precio ≈ ingreso` son colineales).
- **FP-Growth:** descubre patrones de co-ocurrencia (market basket) sin supervisión.

---

## 3. Diseño y preprocesamiento

| Modelo | Features | Preprocesamiento |
|---|---|---|
| KMeans | duración, precio, ingreso | VectorAssembler |
| PCA + KMeans | duración, precio, ingreso | **StandardScaler** (obligatorio antes de PCA) |
| Segmentación | total_citas, gasto, ticket, cancelación, recencia | StandardScaler + KMeans k=4 |
| Recomendación | conjunto de servicios por cliente | transacciones (collect_set) |

---

## 4. Métricas de evaluación (Unidad IV)

### Silhouette Score
Mide qué tan bien separados están los clusters (rango −1 a 1).
- `> 0.5` buena estructura · `0.2–0.5` aceptable · `< 0.2` débil.

### WCSS / Método del Codo (Elbow)
Se calcula el **Within-Cluster Sum of Squares** para k = 2…8 y se busca el "codo"
donde añadir más clusters ya no reduce significativamente el WCSS → elige el **k óptimo**.

### FP-Growth
- **Support:** % de clientes que piden un conjunto de servicios.
- **Confidence:** de los que piden A, % que también pide B.
- **Lift:** cuánto más probable es B dado A (>1 = asociación positiva).

---

## 5. Resultados reales (KMeans, ejecución sobre 12,505 citas)

**Silhouette Score: 0.7430** → buena segmentación, confirmada por el Método del Codo
(codo claro en K=3: WCSS cae de 152M en k=2 a 51.5M en k=3, y luego de forma mucho más
gradual). Detalle completo en
[`doc_01_kmeans.md`](doc_01_kmeans.md).

| Cluster | Perfil | Duración | Precio | Citas | % |
|---|---|---|---|---|---|
| 0 | Estándar | 42.9 min | $382 | 7,545 | 60.3% |
| 1 | Premium | 75.0 min | $820 | 602 | 4.8% |
| 2 | Básico | 24.3 min | $248 | 4,358 | 34.9% |

**Segmentación de clientes, Recomendación (FP-Growth) y PCA:** se ejecutan sobre las
mismas 12,505 citas y 1,000 clientes; sus resultados exactos (segmentos VIP/Frecuente/
Inactivo, reglas de asociación, varianza explicada) se generan en tiempo de ejecución —
correr `03_segmentacion_clientes.py`, `04_recomendacion_servicios.py` y `02_pca.py` para
obtener las cifras vigentes antes de una presentación, ya que dependen de asignaciones
aleatorias de KMeans (semilla fija, pero sensibles a cambios en el volumen de datos).

---

## 6. Cómo reproducir

```bash
spark-submit unidades/unidad_4_no_supervisado/01_kmeans.py
spark-submit unidades/unidad_4_no_supervisado/02_pca.py
spark-submit unidades/unidad_4_no_supervisado/03_segmentacion_clientes.py
spark-submit unidades/unidad_4_no_supervisado/04_recomendacion_servicios.py
```
