# UrbanBlade Analytics — Índice por Unidad

**Asignatura:** Extracción del conocimiento en bases de datos
**Programa:** Ingeniería en Desarrollo y Gestión de Software · Noveno cuatrimestre
**Periodo:** Mayo–Agosto 2026 · **Grupo:** IDGS-93
**Equipo:** Equipo UrbanBlade · **Docente:** MGTI. Héctor Velázquez Estrada

Proyecto de extracción del conocimiento sobre **UrbanBlade** (sistema de barbería,
MongoDB `barber_db`: 12,505 citas · 1,000 clientes · 25 barberos · 20 servicios).

---

## Mapa de unidades

| Unidad | Tema | Sesiones | Evaluación | Carpeta |
|---|---|---|---|---|
| **I** | Introducción al análisis de datos | 1–5 | 29-may-2026 | [`unidad_1_introduccion/`](unidad_1_introduccion/) |
| **II** | Preparación de los datos | 6–10 | 12-jun-2026 | [`unidad_2_preparacion/`](unidad_2_preparacion/) |
| **III** | Análisis supervisado | 11–12 | 03-jul-2026 | [`unidad_3_supervisado/`](unidad_3_supervisado/) |
| **IV** | Análisis no supervisado | 13–14 | 31-jul-2026 | [`unidad_4_no_supervisado/`](unidad_4_no_supervisado/) |
| **V** | Presentación y visualización | 15–17 | 17-ago-2026 | [`unidad_5_visualizacion/`](unidad_5_visualizacion/) |
| **VI** | Caso aplicado: diagnóstico y gobernanza de datos (extra, fuera del programa) | — | — | [`unidad_6_caso_aplicado_laravel/`](unidad_6_caso_aplicado_laravel/) |

Cada carpeta tiene su propio `README.md` con el checklist de entregables del documento.
La Unidad VI no forma parte de la secuencia didáctica oficial (que define I–V); documenta
un incidente real de pérdida de datos/roles en el backend Laravel que comparte la misma
base de datos, y cómo se diagnosticó y resolvió con las mismas técnicas de consulta y
verificación usadas en las Unidades II–IV.

---

## Checklist global de entregables (según la secuencia didáctica)

### Unidad I
- [x] Comparativa IA / ML / Data Mining / Big Data
- [x] Caso de estudio + justificación de metodología

### Unidad II
- [x] Esquema de Data Warehouse + tipos/fuentes + limpieza + config
- [x] Repositorio de datos preprocesados (ETL → Parquet/CSV)
- [x] Explotación de 5 colecciones reales adicionales: `payments`, `loyalty_transactions`,
  `barber_schedules`, `products`, `barbershop_settings` (control de calidad, fidelización,
  utilización de personal, inventario)

### Unidad III (supervisado)
- [x] Documento: justificación + diseño + evaluación (MSE, MAE)
- [x] Modelos de regresión y clasificación

### Unidad IV (no supervisado)
- [x] Documento: justificación + resultados + evaluación (Silhouette, WCSS)
- [x] Modelos de agrupación (K-means) y reducción (PCA)

### Unidad V (visualización)
- [x] Dashboard con gráficas personalizadas + interpretación (15 análisis en 1 app)
- [x] Código fuente de gráficas (Matplotlib)

### Unidad VI (caso aplicado, extra)
- [x] Diagnóstico completo de un incidente real (roles + pérdida de datos)
- [x] Análisis de causa raíz técnica (Spatie Permission + MongoDB)
- [x] Recuperación de datos documentada y verificada end-to-end
- [x] Limpieza de deuda técnica (seeders legado, documentación obsoleta)
- [x] Script de onboarding para prevenir recurrencia

---

## Motor compartido (fuera de `unidades/`)

| Carpeta | Contenido |
|---|---|
| `config/` | Capa de datos única: `mongo_spark_conexion_sinnulos.py` (conexión + JOIN + features) |
| `data_ingestion/` | Generador de datos sintéticos |
| `data/etl_output/` | Salida del ETL (Parquet/CSV) — regenerable, en `.gitignore` |

Todos los scripts localizan la raíz del proyecto automáticamente, así que funcionan desde cualquier ruta.
