# Análisis de datos en UrbanBlade

Este documento resume qué datos usa el sistema para análisis, cómo funcionan los algoritmos aplicados y cómo se presentan los resultados en el proyecto.

## 1. Fuentes de datos
- Base de datos principal (MongoDB `barberpro`): colección `appointments` (citas), `users` (clientes/barberos), `services`, `payments`, `inventory`, `logs`.
- Eventos de aplicación: acciones del usuario (reserva, cancelación, check-in), registros de cambios (audit logs).
- Datos de negocio auxiliares: precios, duración de servicios, stock de productos.
- Datos sintéticos o ingestados para pruebas: generados en `spark/data_ingestion` cuando se requiere volumen para análisis y demos.

## 2. Campos principales utilizados
- appointments: _id, user_id, service_id, barber_id, scheduled_at, status, price, quantity, created_at
- users: _id, role, name, email, phone, metadata
- services: _id, name, duration, price, category
- payments: _id, user_id, amount, method, status, created_at
- inventory: _id, sku, name, stock, threshold

## 3. Procesamiento y limpieza (preprocessing)
- Normalización de fechas y zonas horarias (UTC canonical).
- Relleno / filtrado de registros nulos: se eliminan filas sin user_id o scheduled_at para análisis operativos; registros con campos faltantes pueden pasarse a pipeline de imputación cuando se requiere (scripts en `spark/processing`).
- Escalado y transformación numérica: estandarización para algoritmos sensibles (PCA, clustering).
- Enriquecimiento: derivación de campos (ingreso = cantidad * precio, slot_hour, day_of_week, is_weekend).

## 4. Algoritmos y su propósito
### 4.1 MapReduce / agregaciones
- Uso para agregaciones masivas (conteo por servicio, facturación por día, consumos por SKU). Implementado mediante Spark jobs `01_mapreduce.py` y consultas agregadas en MongoDB para reportes rápidos.
- Resultados: tablas agregadas que alimentan dashboards y CSVs.

### 4.2 Clustering (k-means)
- Archivo: `analytics/dashboard_kmeans.py`.
- Objetivo: segmentar citas o clientes por patrones (frecuencia, gasto, comportamiento de reserva) para identificar segmentos VIP, frecuentes o inactivos.
- Variables típicas: loyalty_points, total_spent, appointment_count, avg_ticket.
- Preprocesamiento: imputación de nulos, estandarización, selección de k mediante silhouette / elbow.
- Salida: cluster label por cliente; métricas por cluster (size, avg_spend).

### 4.3 Reducción de dimensionalidad (PCA)
- Archivo: `analytics/dashboard_pca.py`.
- Objetivo: visualizar datos multivariantes en 2D/3D, detectar grupos y outliers.
- Uso en dashboards: scatter plots con color por cluster / categoría.

### 4.4 Modelos predictivos / regresión
- Archivo: `analytics/dashboard_regresion_models.py`.
- Objetivo: predecir métricas como demanda por franjas horarias (peak hours), predicción de cancelaciones o demanda semanal.
- Algoritmos: regresión lineal, árboles, modelos de ensemble (dependiendo del experimento).
- Validación: cross-validation simple; métricas reportadas (MAE, RMSE).

### 4.5 Redes neuronales (investigación)
- Prototipos en `ml_algorithms/07_red_neural.py` para problemas de clasificación/regresión con mayor complejidad (opcional).

## 5. Visualización y presentación de la información
- Dashboards internos (áreas administrativas): series temporales de ocupación, heatmap de horas pico, tabla de servicios más vendidos, panel de inventario con alertas.
- Visualizaciones generadas por Spark/Python: gráficos PNG/JSON que se consumen en el frontend o se exportan como imágenes en informes.
- Entregables:
  - CSV/JSON con resultados agregados (`/reports` o endpoint API para dashboards).
  - Imágenes y gráficos estáticos para presentaciones y reportes.
  - Endpoints API que exponen resúmenes: e.g. `/api/dashboard/summary`, `/api/predictions/peak-hours`, `/api/predictions/services`.

## 6. Integración con el sistema
- Pipelines: scripts Spark en `spark/` que leen desde Mongo, procesan y vuelcan resultados en colecciones o archivos para consumo por el frontend.
- Cron / orquestación: los jobs pueden ejecutarse manualmente o por scheduler (cron, Airflow, etc.).
- Consistencia: los datos del dashboard pueden estar pre-aggregados para mejorar performance; la API sirve resúmenes rápidos.

## 7. Consideraciones y limitaciones
- Calidad de datos: datos incompletos o mal formateados impactan modelos — priorizar logging y validación en el punto de ingestión.
- Escalado: Spark está preparado para volúmenes mayores; para producción considerar pipelines en cluster y almacenamiento de resultados en data warehouse.
- Privacidad: anonimizar PII para usos de investigación y cumplir regulaciones locales.

## 8. Reproducibilidad
- Scripts y notebooks: `spark/` contiene scripts de ingestión y análisis; versionados en el repo.
- Entradas esperadas: especificar sample CSV o colección Mongo con esquema mínimo para reproducir experimentos.
- Tests: incluir pruebas unitarias simples para funciones de transformación y notebooks de ejemplo.

## 9. Próximos pasos sugeridos
- Definir dataset canónico para análisis (schema, limpieza, frecuencia de actualización).
- Automatizar ejecución de pipelines y almacenamiento de resultados en colección `analytics_results`.
- Crear notebooks reproductibles con ejemplos de análisis y visualización listos para presentación académica.

---
*Archivo generado automáticamente. Reemplazar ejemplos de métricas y rutas si se personaliza la arquitectura.*