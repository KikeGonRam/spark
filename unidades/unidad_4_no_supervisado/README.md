# Unidad IV — Análisis no supervisado

**Sesiones:** 13–14 · **Duración:** 20 h · **Evaluación:** 31-jul-2026 · **Grupo:** IDGS-93

Temas: algoritmos de aprendizaje no supervisado (PCA, K-means) ·
métricas de evaluación (entrenamiento, prueba y error).

---

## Entregables que pide el documento

- [x] **Documento** con justificación del algoritmo, descripción de los resultados y
  reporte de evaluación y optimización → [`reporte_evaluacion.md`](reporte_evaluacion.md)
- [x] **Modelo de agrupación (K-means) y reducción de dimensionalidad (PCA) en el repositorio**
  → scripts 01–04 (abajo)

---

## Scripts

| Archivo | Técnica | Objetivo | Métricas |
|---|---|---|---|
| `01_kmeans.py` | KMeans + Método del Codo | agrupar citas | Silhouette, WCSS |
| `02_pca.py` | PCA + KMeans | reducir a 2 componentes y agrupar | Varianza explicada, Silhouette |
| `03_segmentacion_clientes.py` | KMeans sobre RFM | segmentar 1000 clientes | Silhouette |
| `04_recomendacion_servicios.py` | FP-Growth | reglas de asociación | Support, Confidence, Lift |

Documentos de apoyo: `doc_01`…`doc_04` (uno por script).

---

## Métricas clave (Unidad IV)

- **Silhouette Score** — calidad de separación de los clusters.
- **WCSS / Método del Codo** — para elegir el k óptimo.

Ver detalle en [`reporte_evaluacion.md`](reporte_evaluacion.md).

---

## Cómo ejecutar

```bash
spark-submit unidades/unidad_4_no_supervisado/01_kmeans.py
spark-submit unidades/unidad_4_no_supervisado/02_pca.py
```
