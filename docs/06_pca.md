# 06 — PCA (Análisis de Componentes Principales)

## Descripción

Reduce las 3 features (`duracion_min`, `precio`, `ingreso`) a 2 componentes principales (PC1, PC2) para visualización y clustering en 2D.

Pipeline:
```
VectorAssembler → StandardScaler → PCA(k=2) → KMeans(k=3)
```

El escalado (`StandardScaler`) es obligatorio antes de PCA para que ninguna variable domine por su escala numérica (precio en cientos vs duracion en decenas).

---

## Varianza explicada

| Componente | Varianza |
|-----------|---------|
| **PC1** | **68.23%** |
| **PC2** | **31.77%** |
| **Total** | **100%** |

Las 2 componentes capturan el **100% de la varianza** — resultado esperado cuando `ingreso = precio` (las 3 features son efectivamente 2 dimensiones independientes: `duracion_min` y `precio`).

---

## Pesos de los componentes (PCA loadings)

```
DenseMatrix([[-0.2068,  0.9784],   ← duracion_min
             [-0.6918, -0.1462],   ← precio
             [-0.6918, -0.1462]])  ← ingreso
```

- **PC1** (~68%): captura principalmente `precio` e `ingreso` (pesos -0.69) — es el eje de "nivel económico"
- **PC2** (~32%): captura principalmente `duracion_min` (peso +0.98) — es el eje de "duración del servicio"

---

## Clusters sobre PCA

### Centroides en espacio PCA (PC1, PC2)

| Cluster | PC1 | PC2 | Interpretación |
|---------|-----|-----|----------------|
| 0 | +1.30 | -0.09 | Precio ALTO, duración MEDIA |
| 1 | -1.02 | -0.66 | Precio BAJO, duración CORTA |
| 2 | -1.07 | +1.97 | Precio BAJO, duración LARGA |

### Interpretación

- **Cluster 0** (PC1 alto positivo): citas de alto precio — servicios premium
- **Cluster 1** (PC1 negativo, PC2 negativo): citas económicas y rápidas
- **Cluster 2** (PC1 negativo, PC2 muy positivo): citas económicas pero de larga duración — servicios especializados de bajo costo (ej. tratamientos)

---

## Observaciones técnicas

- La gráfica Plotly (scatter 2D PC1 vs PC2) no abrió en WSL porque el entorno WSL no tiene acceso al browser de Windows directamente. Para verla, ejecutar el dashboard Streamlit que sí funciona vía `localhost:8501`.
- `gio: http://127.0.0.1:...: Operation not supported` es un error de WSL al intentar abrir un browser — no afecta el cálculo PCA.
- En el dashboard `dashboard_pca.py` el scatter es interactivo con Plotly dentro de Streamlit.
