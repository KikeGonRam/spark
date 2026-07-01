# Unidad II — Preparación de los datos

**Sesiones:** 6–10 · **Duración:** 10 h · **Evaluación:** 12-jun-2026 · **Grupo:** IDGS-93

Temas: tipos y fuentes de datos · modelado de Data Warehouse (estrella / copo de nieve) ·
técnicas de limpieza · minería de datos · proceso ETL.

---

## Entregables que pide el documento

- [x] **Documento** con esquema de Data Warehouse, tipos y fuentes de datos, técnicas de
  limpieza y parámetros de configuración del DW
  → [`esquema_datawarehouse.md`](esquema_datawarehouse.md)
- [x] **Repositorio con el conjunto de datos preprocesados**
  → generado por [`05_etl.py`](05_etl.py) en `data/etl_output/` (Parquet + CSV)

---

## Scripts (prácticas con Python + Spark)

| Archivo | Sesión | Tema |
|---|---|---|
| `01_tipos_fuentes_datos.py` | 6 | Clasificación de tipos y fuentes de datos |
| `02_datawarehouse.py` | 7 | Modelado de Data Warehouse |
| `03_limpieza_datos.py` | 8 | Técnicas de limpieza |
| `04_mineria_datos.py` | 9 | Conjuntos de datos en minería |
| `05_etl.py` | 10 | Proceso ETL (Extract-Transform-Load) → Parquet/CSV |
| `06_mapreduce_etl.py` | 10 | MapReduce avanzado + interpretación + gráficas |
| `07_mapreduce_basico.py` | 10 | MapReduce básico (ingresos por servicio) |

## Fuentes de datos adicionales (colecciones reales antes sin usar)

El caso de estudio original solo explotaba 4 colecciones (`appointments`, `services`,
`barbers`, `users`). Estos scripts incorporan **5 colecciones más de `barber_db`** para
un análisis integral del negocio:

| Archivo | Colección(es) usadas | Tema |
|---|---|---|
| `08_calidad_pagos.py` | `payments` (11,016) + `barbershop_settings` | Reconciliación de cobros y validación de horario oficial |
| `09_fidelizacion_clientes.py` | `loyalty_transactions` (11,016) | Puntos de lealtad, tendencia y nivel VIP vs regular |
| `10_utilizacion_barberos.py` | `barber_schedules` (175) | Horas disponibles vs horas trabajadas por barbero |
| `11_inventario_productos.py` | `products` (31) | Salud de stock, márgenes y categorías |

> Colecciones descartadas por estar vacías en la BD actual: `service_combos`,
> `combo_service`, `inventories`, `inventory_movements`, `works`, `saved_works`,
> `work_images`, `raffle_results`, `comments`, `reactions`.

## Documentos de apoyo

`doc_01`…`doc_06`: material teórico de cada tema (tipos/fuentes, DW, limpieza, minería, ETL, MapReduce).

---

## Cómo ejecutar

```bash
spark-submit unidades/unidad_2_preparacion/05_etl.py            # genera el DW en data/etl_output/
spark-submit unidades/unidad_2_preparacion/06_mapreduce_etl.py
spark-submit unidades/unidad_2_preparacion/08_calidad_pagos.py
spark-submit unidades/unidad_2_preparacion/09_fidelizacion_clientes.py
spark-submit unidades/unidad_2_preparacion/10_utilizacion_barberos.py
python3      unidades/unidad_2_preparacion/11_inventario_productos.py   # no requiere Spark
```
