# Unidad I — Caso de estudio y metodología de análisis

**Asignatura:** Extracción del conocimiento en bases de datos · UTVT · IDGS-93
**Equipo:** Equipo UrbanBlade · **Docente:** MGTI. Héctor Velázquez Estrada

> Entregable de la sesión 5. Incluye: objetivo y alcance del caso, justificación de la
> metodología a utilizar, y planeación de las etapas para el análisis de datos.

---

## 1. Objetivo y alcance del caso

**Caso:** UrbanBlade, un sistema de gestión para barbería con backend Laravel y base de
datos MongoDB (`barber_db`), que registra citas, servicios, barberos y clientes.

**Objetivo general:** Aplicar técnicas de extracción del conocimiento sobre los datos
reales de operación de UrbanBlade para **optimizar el negocio**: anticipar cancelaciones,
segmentar clientes, recomendar servicios, predecir demanda y proyectar ingresos.

**Alcance:**
- **Incluye:** 12,505 citas, 1,000 clientes, 25 barberos, 20 servicios (periodo dic-2024 a jun-2026).
- **No incluye:** datos personales sensibles más allá de nombre/nivel; información de pagos con tarjeta.
- **Entregables:** modelos supervisados y no supervisados + dashboard de visualización.

---

## 2. Justificación de la metodología

Se adopta un enfoque basado en **CRISP-DM** (Cross-Industry Standard Process for Data Mining),
por ser el estándar de facto para proyectos de minería de datos y adaptarse al caso:

| Fase CRISP-DM | Aplicación en UrbanBlade |
|---|---|
| 1. Comprensión del negocio | Reducir cancelaciones, fidelizar clientes, optimizar agenda |
| 2. Comprensión de los datos | Auditoría de `barber_db`: esquema, calidad, relaciones |
| 3. Preparación de los datos | JOIN de 4 colecciones, limpieza, features (Unidad II) |
| 4. Modelado | Supervisado (Unidad III) + no supervisado (Unidad IV) |
| 5. Evaluación | R²/MSE/MAE, AUC, Silhouette — **sin fuga de datos** |
| 6. Despliegue | Dashboard Streamlit + reportes (Unidad V) |

**Por qué CRISP-DM y no otra:** es iterativo, agnóstico a la herramienta y pone el
**objetivo de negocio** en el centro — ideal para un caso aplicado como UrbanBlade.

---

## 3. Planeación de las etapas del análisis

```
Entrada de datos      → MongoDB Atlas (barber_db), 4 colecciones
       ↓
Preparación           → JOIN + limpieza + features (Unidad II)
       ↓
Exploración           → MapReduce, agregaciones, distribuciones
       ↓
Enriquecimiento       → dimensión cliente (RFM), tiempo (día/hora/mes), categoría
       ↓
Data Science          → modelos supervisados (III) y no supervisados (IV)
       ↓
Business Intelligence → interpretación de negocio de cada modelo
       ↓
Informes / Dashboard  → Matplotlib + Streamlit (Unidad V)
       ↓
Optimización          → recomendaciones accionables (retención, upsell, agenda)
```

### Cronograma (alineado a la secuencia didáctica)

| Etapa | Unidad | Sesiones | Fecha de evaluación |
|---|---|---|---|
| Introducción y metodología | I | 1–5 | 29-may-2026 |
| Preparación de datos (ETL, DW) | II | 6–10 | 12-jun-2026 |
| Análisis supervisado | III | 11–12 | 03-jul-2026 |
| Análisis no supervisado | IV | 13–14 | 31-jul-2026 |
| Presentación y visualización | V | 15–17 | 17-ago-2026 |

---

## 4. Riesgos identificados y mitigación

| Riesgo | Mitigación aplicada |
|---|---|
| Fuga de datos (métricas infladas) | Targets sin la variable objetivo entre las features |
| `precio_cobrado == precio_servicio` (sin varianza) | Regresión sobre facturación **diaria**, no por cita |
| Nombres de cliente mal resueltos | Ruta correcta `client_id → clients → users.name` |
| Clases desbalanceadas | Usar AUC/Recall, no solo accuracy |
