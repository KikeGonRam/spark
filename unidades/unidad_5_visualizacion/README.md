# Unidad V — Presentación y visualización

**Sesiones:** 15–17 · **Duración:** 10 h · **Evaluación:** 17-ago-2026 · **Grupo:** IDGS-93

Temas: técnicas de visualización y representación del conocimiento · herramientas
(Excel, Power BI) · bibliotecas / APIs: **Matplotlib** de Python (sesión 17).

---

## Entregables que pide el documento

- [x] **Dashboard** con gráficas personalizadas e interpretación de resultados
  → [`main_dashboard.py`](main_dashboard.py) (dashboard ejecutivo con 11 análisis)
- [x] **Repositorio con el código fuente para creación de gráficas** (Matplotlib)
  → [`dashboard_matplotlib.py`](dashboard_matplotlib.py)

---

## Contenido

| Archivo | Herramienta | Descripción |
|---|---|---|
| `main_dashboard.py` | Streamlit + Plotly | **Dashboard ejecutivo unificado** — 11 tabs (Resumen, MapReduce, Regresión, Árbol, Random Forest, KMeans, PCA, Segmentación, Churn, Recomendación, Demanda) + KPIs |
| `dashboard_matplotlib.py` | **Matplotlib** | 6 gráficas personalizadas (sesión 17 del programa) + interpretación |
| `dashboards_individuales/` | Streamlit | Dashboards por algoritmo (versiones previas, integradas ya en `main_dashboard.py`) |

---

## Cómo ejecutar

```bash
# Dashboard ejecutivo (abre en el navegador)
streamlit run unidades/unidad_5_visualizacion/main_dashboard.py

# Gráficas Matplotlib (sesión 17) → genera PNG
python unidades/unidad_5_visualizacion/dashboard_matplotlib.py
```

> El `main_dashboard.py` presenta de forma visual el resultado de TODAS las unidades
> (II–IV) en una sola aplicación, con interpretación de negocio en cada pestaña.
