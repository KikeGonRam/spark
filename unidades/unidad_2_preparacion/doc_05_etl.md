# Unidad II — Sesión 10: Proceso ETL Completo

**Script**: `unidades/unidad_2_preparacion/05_etl.py`  
**Fecha de ejecución**: 2026-06-10  
**Dataset**: 4 colecciones de `barber_db` (MongoDB Atlas)

---

## Conceptos clave del ETL

```
ETL = Extract → Transform → Load

  EXTRACT:   Leer datos desde las fuentes originales
  TRANSFORM: Limpiar, integrar, enriquecer y calcular
  LOAD:      Guardar el resultado en un destino analítico
```

**Tipos de extracción** (cuál usamos):
- **Completa (Full)** ← usado en este script — todos los registros cada vez
- Incremental — solo registros nuevos o modificados
- Streaming — en tiempo real (Spark Streaming)

**Tipo de carga** (cuál usamos):
- **Truncate & Load** ← usado aquí — reemplaza todo con `mode("overwrite")`
- Append — agrega sin borrar histórico
- Upsert — actualiza si existe, inserta si no

---

## FASE 1: EXTRACT (Extracción)

### Conexión y extracción de 4 colecciones

```
Conectando a MongoDB Atlas...
  Host:          <tu_cluster>.mongodb.net   (ver .env — nunca hardcodear ni compartir)
  Base de datos: barber_db

Extrayendo colecciones...
  appointments:   283 documentos  (1.95s)
  services:        12 documentos  (0.48s)
  barbers:          3 documentos  (0.41s)
  users:           32 documentos  (0.62s)

  Total extraído: 330 documentos en 3.46s
```

### Campos extraídos por colección

| Colección | Campos extraídos |
|---|---|
| appointments | _id, service_id, barber_id, client_id, precio_cobrado, estado, fecha, hora_inicio, hora_fin, metodo_pago, notas |
| services | _id, nombre, precio, duracion_min, categoria, activo |
| barbers | _id, user_id, nombre, especialidades, activo |
| users | _id, name, email |

---

## FASE 2: TRANSFORM (Transformación)

### 2.1 Integración — Join de 4 colecciones

```
Registros integrados: 283
```

Lógica del join (Python, antes de crear Spark DF):
- `appointments.service_id → services._id` → obtiene nombre, precio, duracion_min, categoria
- `appointments.barber_id → barbers._id` → obtiene nombre del barbero
- `barbers.user_id → users._id` → fallback para nombre si `barbero.nombre` es null
- `precio_cobrado || services.precio` → precio efectivo de la cita

### 2.2 Limpieza

```
Registros después de limpieza: 283
```

- `dropna` en campos críticos: precio, duracion_min, estado
- `lower(trim())` en estado y metodo_pago
- Cast explícito a `DoubleType` en precio y duracion_min
- `dropDuplicates(["cita_id"])` — sin duplicados reales por cita_id único

### 2.3 Enriquecimiento — Nuevas columnas calculadas

```
Columnas añadidas: ingreso, alto_valor, cancelada, pagado, anio, mes, dia
```

Schema del dataset transformado:
```
root
 |-- cita_id:      string  (nullable = true)
 |-- servicio:     string  (nullable = true)
 |-- categoria:    string  (nullable = true)
 |-- barbero:      string  (nullable = true)
 |-- duracion_min: double  (nullable = true)
 |-- precio:       double  (nullable = true)
 |-- estado:       string  (nullable = true)
 |-- metodo_pago:  string  (nullable = true)
 |-- fecha:        string  (nullable = true)
 |-- hora_inicio:  string  (nullable = true)
 |-- ingreso:      double  (nullable = true)
 |-- alto_valor:   integer (nullable = true)
 |-- cancelada:    integer (nullable = true)
 |-- pagado:       integer (nullable = true)
 |-- anio:         integer (nullable = true)
 |-- mes:          integer (nullable = true)
 |-- dia:          integer (nullable = true)
```

### Muestra del dataset transformado

```
+--------------------+--------------+------------+------+----------+-----------+----------+----+
|servicio            |barbero       |duracion_min|precio|estado    |alto_valor |cancelada |mes |
+--------------------+--------------+------------+------+----------+-----------+----------+----+
|Combo corte y barba |Barbero Test 2|        45.0|619.86|confirmada|          1|         0|   6|
|Corte fade 86       |Barbero Test 1|        30.0|439.81|completada|          0|         0|   6|
|Corte clásico 45    |Barbero Test 2|        30.0|632.15|pendiente |          1|         0|   6|
|Corte fade 16       |Barbero Test  |        75.0|540.26|confirmada|          1|         0|   6|
|Corte fade 16       |Barbero Test  |        30.0|160.26|confirmada|          0|         0|   6|
+--------------------+--------------+------------+------+----------+-----------+----------+----+
```

**Reglas de enriquecimiento**:
- `ingreso = precio` (precio efectivo de la cita)
- `alto_valor = 1` si precio > $500 (percentil ~75)
- `cancelada = 1` si estado == "cancelada"
- `pagado = 1` si estado == "completada"
- `anio`, `mes`, `dia` extraídos de `fecha` (substr)

```
Tiempo de transformación: 16.27s
```

---

## FASE 3: LOAD (Carga)

### 3.1 Parquet — Formato columnar comprimido

```
Ruta: data/etl_output/citas_etl.parquet
Tiempo: 3.63s
```

**Ventajas del Parquet sobre CSV**:
- Almacenamiento columnar: solo lee las columnas necesarias en cada query
- Compresión automática: 3–10x menos espacio que CSV equivalente
- Preserva tipos de datos (no requiere re-parsear)
- Lectura 10–100x más rápida en queries analíticas con filtros

### 3.2 CSV — Legible por humanos

```
Ruta: data/etl_output/citas_etl.csv
Tiempo: 3.01s
```

Compatible con Excel, Google Sheets, y herramientas BI.

### 3.3 Verificación — Lectura desde Parquet

```
Registros cargados desde Parquet: 283
```

Muestra de verificación:
```
+--------------------+--------------+------+----------+----+
|servicio            |barbero       |precio|estado    |mes |
+--------------------+--------------+------+----------+----+
|Combo corte y barba |Barbero Test 2|619.86|confirmada|   6|
|Corte fade 86       |Barbero Test 1|439.81|completada|   6|
|Corte clásico 45    |Barbero Test 2|632.15|pendiente |   6|
+--------------------+--------------+------+----------+----+
```

---

## Tabla Resumen por Mes

```
+----+---------+----------------+-------------+----------------+
|mes |num_citas|ingreso_total   |cancelaciones|precio_promedio |
+----+---------+----------------+-------------+----------------+
|  5 |     200 | $77,929.12     |          36 | $389.65        |
|  6 |      81 | $32,715.48     |          18 | $403.89        |
|  7 |       2 |    $778.52     |           0 | $389.26        |
+----+---------+----------------+-------------+----------------+
```

**Análisis por mes**:
- **Mayo** concentra **70.7% de las citas** (200/283) y **70.6% del ingreso** ($77,929)
- **Junio** tiene precio promedio más alto ($403.89 vs $389.65 en mayo)
- **Julio** solo tiene 2 citas — mes en curso, datos incompletos
- Tasa de cancelación: 19.1% (54/283) uniforme entre mayo y junio

---

## Resumen del proceso ETL

```
  ┌─────────────┬────────────────────────────────────────────┐
  │ Fase        │ Resultado                                  │
  ├─────────────┼────────────────────────────────────────────┤
  │ EXTRACT     │ 283 citas + 12 servicios + 3 barberos      │
  │             │ + 32 usuarios = 330 docs en 3.46s          │
  ├─────────────┼────────────────────────────────────────────┤
  │ TRANSFORM   │ 283 registros limpios y enriquecidos       │
  │             │ Joins: 4 colecciones unidas                │
  │             │ Nuevas columnas: ingreso, alto_valor,      │
  │             │   cancelada, pagado, anio, mes, dia        │
  │             │ Tiempo: 16.27s                             │
  ├─────────────┼────────────────────────────────────────────┤
  │ LOAD        │ ✓ Parquet: data/etl_output/citas_etl.parquet│
  │             │ ✓ CSV:     data/etl_output/citas_etl.csv  │
  │             │ Tiempo: 6.64s                              │
  ├─────────────┼────────────────────────────────────────────┤
  │ TOTAL ETL   │ 30.16 segundos                             │
  └─────────────┴────────────────────────────────────────────┘
```

---

## Observaciones técnicas

- **Cuello de botella**: la fase TRANSFORM (16.27s) toma el 54% del tiempo total — el join en Python antes de Spark es la operación más costosa. Con millones de registros se haría en Spark SQL directamente
- **Extracción completa** es correcta para un DW educativo; en producción se filtraría por `fecha > ultima_carga` para extracción incremental
- **Parquet vs CSV**: para los dashboards Streamlit se usa PyMongo directamente (más rápido que leer Parquet en esta escala); el Parquet es útil para análisis batch futuros
- El tiempo total de 30.16s incluye la inicialización de Spark (~10s) — en pipelines recurrentes Spark permanecería activo y las ejecuciones posteriores serían más rápidas
- Los archivos de salida se generan en `data/etl_output/` — este directorio está en `.gitignore` para no subir datos al repositorio
