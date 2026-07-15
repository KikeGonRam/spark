# Unidad II — Esquema de Data Warehouse UrbanBlade

**Asignatura:** Extracción del conocimiento en bases de datos · UTVT · IDGS-93
**Equipo:** Equipo UrbanBlade · **Docente:** MGTI. Héctor Velázquez Estrada

> Entregable de la Unidad II. Incluye: esquema de data warehouse, tipos y fuentes de
> datos, técnicas de limpieza aplicadas y parámetros de configuración del DW.

---

## 1. Tipos y fuentes de datos

| Fuente | Tipo | Descripción |
|---|---|---|
| MongoDB `barber_db` | **Semi-estructurado** (documentos BSON) | Fuente operacional (OLTP) del sistema Laravel |
| Colección `appointments` | Semi-estructurado | 12,505 citas (hechos) |
| Colecciones `services/barbers/users/clients` | Semi-estructurado | Catálogos (dimensiones) |
| Salida ETL `data/etl_output/` | **Estructurado** (Parquet/CSV) | Data warehouse analítico (OLAP) |

---

## 2. Modelo dimensional (Esquema Estrella)

Se elige **esquema estrella** (no copo de nieve) por su simplicidad de consulta y porque
las dimensiones de una barbería son pequeñas y no requieren normalización adicional.

```
                    ┌────────────────────┐
                    │   DIM_TIEMPO        │
                    │  fecha, anio, mes,  │
                    │  dia, dia_semana,   │
                    │  hora               │
                    └─────────┬──────────┘
                              │
 ┌──────────────┐   ┌─────────┴──────────┐   ┌──────────────┐
 │ DIM_SERVICIO │   │   HECHOS_CITAS     │   │ DIM_BARBERO  │
 │ servicio,    ├───┤  (grano = 1 cita)  ├───┤ barbero      │
 │ categoria,   │   │  precio, ingreso,  │   │              │
 │ duracion_min │   │  es_cancelada,     │   └──────────────┘
 └──────────────┘   │  estado            │
                    └─────────┬──────────┘
                    ┌─────────┴──────────┐
                    │   DIM_CLIENTE      │
                    │ cliente, nivel,    │
                    │ puntos, edad       │
                    └────────────────────┘
```

### Tabla de HECHOS (`HECHOS_CITAS`)
Grano: **una fila por cita**. Medidas: `precio`, `ingreso`, `duracion_min`, `es_cancelada`.

### Dimensiones
| Dimensión | Atributos | Origen |
|---|---|---|
| DIM_TIEMPO | anio, mes, dia, dia_semana, hora | derivado de `fecha` / `hora_inicio` |
| DIM_SERVICIO | servicio, categoria, duracion_min | `services` |
| DIM_BARBERO | barbero | `barbers → users.name` |
| DIM_CLIENTE | cliente, nivel, puntos, edad | `clients → users.name` |

---

## 2.1 Extensión del modelo — hechos y dimensiones de las 5 colecciones adicionales

La Unidad II original solo modelaba `appointments` (+ sus 3 dimensiones). Los scripts
08–11 incorporan 5 colecciones más de `barber_db`, que se modelan como **dos tablas de
hechos adicionales** y **una dimensión nueva**, conectadas a las dimensiones ya
existentes (mismo `DIM_TIEMPO`, `DIM_BARBERO`, `DIM_CLIENTE`):

```
                    ┌────────────────────┐
                    │   DIM_TIEMPO       │  (compartida con HECHOS_CITAS)
                    └─────────┬──────────┘
                              │
 ┌──────────────┐   ┌─────────┴──────────┐   ┌──────────────────┐
 │ DIM_CLIENTE  │   │   HECHOS_PAGOS     │   │ DIM_PROCESADOR   │
 │ (compartida) ├───┤  (grano = 1 pago)  ├───┤ (users, quién     │
 │              │   │  monto, propina    │   │  procesó el pago) │
 └──────────────┘   └────────────────────┘   └──────────────────┘

 ┌──────────────┐   ┌────────────────────┐
 │ DIM_CLIENTE  │   │ HECHOS_FIDELIZACION│
 │ (compartida) ├───┤ (grano = 1 trans.) │
 │              │   │  puntos, tipo      │
 └──────────────┘   └────────────────────┘

 ┌──────────────┐   ┌────────────────────┐
 │ DIM_BARBERO  │   │  DIM_HORARIO       │
 │ (compartida) ├───┤  dia_semana,       │
 │              │   │  horas_disponibles │
 └──────────────┘   └────────────────────┘

 ┌──────────────────────────────────────┐
 │        DIM_PRODUCTO (independiente)  │
 │  producto, categoria, tipo, stock,   │
 │  precio_compra, precio_venta         │
 └──────────────────────────────────────┘
```

### Tabla de HECHOS (`HECHOS_PAGOS`)
Grano: **una fila por pago**. Medidas: `monto`, `propina`.
Colección origen: `payments` (11,029 documentos). Se une a `appointments` por
`appointment_id` para heredar `DIM_TIEMPO`/`DIM_CLIENTE`/`DIM_BARBERO`, y a `users` por
`created_by` para resolver quién procesó el cobro (`get_pagos_df()` en el conector).

### Tabla de HECHOS (`HECHOS_FIDELIZACION`)
Grano: **una fila por transacción de puntos**. Medida: `puntos`. Atributo: `tipo`
(`ganado`/`canjeado`). Colección origen: `loyalty_transactions` (11,029 documentos),
unida a `DIM_CLIENTE` por `client_id`.

### Dimensión nueva: `DIM_HORARIO`
Atributos: `dia_semana` (convertido de convención Laravel 0=Domingo a ISO 1=Lunes),
`horas_disponibles`, `is_working`. Colección origen: `barber_schedules` (350 = 50
barberos × 7 días). Se cruza contra `HECHOS_CITAS` (agregadas por barbero/día) para
calcular la tasa de utilización real — ver `10_utilizacion_barberos.py`.

### Dimensión independiente: `DIM_PRODUCTO`
Atributos: `producto`, `categoria`, `tipo` (`uso_interno`/`venta`),
`precio_compra`, `precio_venta`, `stock_actual`, `stock_minimo`. Colección origen:
`products` (31 documentos). No tiene tabla de hechos propia en el modelo actual porque
`inventory_movements` (el registro de consumo que la conectaría con `HECHOS_CITAS`)
está vacía en la base real — limitación documentada en `11_inventario_productos.py`.

> **Nota de tipos:** `products.precio_compra` y `precio_venta` llegan como BSON
> `Decimal128`, no como `float` nativo — requieren el helper `_num()` del conector para
> convertirse correctamente (`float()` directo falla). Ver `SKILL.md` para el detalle.

---

## 3. Técnicas de limpieza aplicadas

| Técnica | Aplicación en UrbanBlade | Script |
|---|---|---|
| Manejo de nulos | `dropna` en features clave; defaults en duración/precio | `config/…_sinnulos.py`, `03_limpieza_datos.py` |
| Tipado explícito | `cast` a double/int/string por columna | conector |
| Resolución de referencias | `client_id → clients → users.name` (evita "Cliente" genérico) | conector |
| Estandarización de fechas | `fecha` → `dia_semana`, `mes`, `anio` | conector |
| Deduplicación / soft-delete | filtro `deleted_at == None` | conector |
| Detección de anomalías | edades fuera de 0–120 se anulan | conector |

---

## 4. Proceso ETL (script `05_etl.py`)

```
EXTRACT   → 4 colecciones de MongoDB Atlas (PyMongo)
TRANSFORM → JOIN + limpieza + enriquecimiento (cliente, tiempo, categoría)
LOAD      → data/etl_output/citas_etl.parquet  (+ .csv)
```

---

## 5. Parámetros de configuración del Data Warehouse

| Parámetro | Valor | Justificación |
|---|---|---|
| Motor de procesamiento | Apache Spark 3.5 | Escala a millones de filas |
| Formato de almacenamiento | **Parquet** (columnar) + CSV | Parquet: compresión y lectura analítica rápida |
| Modo de escritura | `overwrite` | Recarga completa (full refresh) |
| Compresión | Snappy (default Parquet) | Balance velocidad/tamaño |
| Particionamiento | `coalesce(1)` para CSV | Un archivo único legible |
| Frecuencia de carga | Bajo demanda (batch) | El histórico se reprocesa completo |
| Log level | ERROR | Reduce ruido en consola |

---

## 6. Repositorio de datos preprocesados

El conjunto de datos preprocesado se genera en `data/etl_output/` (Parquet + CSV) al
ejecutar `05_etl.py`. Este directorio está en `.gitignore` (son artefactos regenerables);
el **código** que lo produce sí está versionado.
