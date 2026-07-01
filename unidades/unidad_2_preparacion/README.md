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

## Documentos de apoyo

`doc_01`…`doc_06`: material teórico de cada tema (tipos/fuentes, DW, limpieza, minería, ETL, MapReduce).

---

## Cómo ejecutar

```bash
spark-submit unidades/unidad_2_preparacion/05_etl.py          # genera el DW en data/etl_output/
spark-submit unidades/unidad_2_preparacion/06_mapreduce_etl.py
```
