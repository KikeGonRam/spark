# Unidad II — Sesión 7: Modelado de Datawarehouse

**Script**: `unidad2/02_datawarehouse.py`  
**Fecha de ejecución**: 2026-06-10  
**Dataset**: 283 citas reales — `barber_db` (MongoDB Atlas)

---

## Dimensiones construidas

### DIM_BARBERO (3 registros)

```
+--------------+---------------------------+
|barbero       |email                      |
+--------------+---------------------------+
|Barbero Test  |test@barbero.com           |
|Barbero Test 1|barbero.test1@example.com  |
|Barbero Test 2|barbero.test2@example.com  |
+--------------+---------------------------+
```

### DIM_SERVICIO (12 registros, muestra)

```
+--------------------+----------+---------+-------+
|nombre_servicio     |categoria |precio   |duracion|
+--------------------+----------+---------+-------+
|Corte fade 16       |corte     |540.26   |30     |
|Combo corte y barba |combo     |619.86   |45     |
|Arreglo de barba 53 |barba     |493.39   |30     |
|Tratamiento capilar |tratamiento|350.00  |60     |
|Corte clásico 45    |corte     |632.15   |30     |
+--------------------+----------+---------+-------+
```

Categorías disponibles: **corte**, **barba**, **combo**, **tratamiento**

### DIM_USUARIO (32 registros)

Roles presentes en el sistema:
- `admin` — 1 usuario
- `recepcionista` — varios
- `barbero` — 3 (Barbero Test, Barbero Test 1, Barbero Test 2)
- `cliente` — mayoría de los 32 usuarios

### DIM_FECHA (generada a partir de appointments)

Columnas calculadas: `anio`, `mes`, `dia`, `dia_semana`, `nombre_mes`

---

## Modelo Estrella (Star Schema)

```
                    FACT_CITAS
                  ┌─────────────────────────┐
                  │ cita_id (PK)            │
                  │ duracion_min            │
                  │ precio                  │
                  │ estado                  │
                  │                         │
    DIM_FECHA ◄───┤ fecha_id (FK)           │───► DIM_SERVICIO
    anio           │ servicio_id (FK)        │     nombre, categoria
    mes            │ barbero_id (FK)         │     precio, duracion_min
    dia            └─────────────────────────┘
    dia_semana              │
                            ▼
                       DIM_BARBERO
                       nombre, email
```

### Query Estrella — Ingreso por mes y servicio (top resultados)

**Mayo (mes 5) — Top 3 servicios:**

```
+--------------------+------+-----------+-------+
|servicio            |mes   |ingreso    |citas  |
+--------------------+------+-----------+-------+
|Corte fade 16       |5     |14,889.46  |35     |
|Combo corte y barba |5     |9,541.22   |19     |
|Arreglo de barba 53 |5     |8,103.11   |16     |
+--------------------+------+-----------+-------+
```

**Junio (mes 6) — Top 3 servicios:**

```
+--------------------+------+-----------+-------+
|servicio            |mes   |ingreso    |citas  |
+--------------------+------+-----------+-------+
|Arreglo de barba 53 |6     |5,427.29   |11     |
|Corte fade 16       |6     |5,273.80   |14     |
|Combo corte y barba |6     |4,612.45   |9      |
+--------------------+------+-----------+-------+
```

---

## Modelo Copo de Nieve (Snowflake Schema)

Extiende el Star Schema normalizando `DIM_SERVICIO` en dos niveles:

```
FACT_CITAS ──► DIM_SERVICIO ──► DIM_CATEGORIA
               nombre            id_categoria
               precio            nombre_cat
               duracion_min      descripcion
               categoria_id (FK)
```

### DIM_CATEGORIA (4 registros)

```
+------------+---------------+
|nombre_cat  |id_categoria   |
+------------+---------------+
|corte       |0              |
|tratamiento |1              |
|barba       |2              |
|combo       |3              |
+------------+---------------+
```

También se añadió `DIM_USUARIO` con roles normalizados:

```
FACT_CITAS ──► DIM_BARBERO ──► DIM_USUARIO
               nombre           name, email, rol
               user_id (FK)
```

---

## Comparativa Star vs Snowflake

```
+-------------------------+------------------+---------------------+
| Característica          | Estrella (Star)  | Copo de Nieve       |
+-------------------------+------------------+---------------------+
| Joins en query          | 3 joins simples  | 5+ joins anidados   |
| Redundancia             | Alta (desnorm.)  | Baja (normalizado)  |
| Velocidad de lectura    | Más rápida       | Más lenta           |
| Espacio en disco        | Mayor            | Menor               |
| Integridad referencial  | Manual           | Garantizada por FK  |
| Uso recomendado         | OLAP / dashboards| DW empresariales    |
+-------------------------+------------------+---------------------+
```

**Decisión en UrbanBlade**: se usa **Estrella** para los dashboards Streamlit (velocidad de lectura prioritaria) y **Snowflake** como modelo conceptual del Data Warehouse completo.

---

## Observaciones técnicas

- Los datos de `DIM_FECHA` se generan desde el campo `fecha` (string `YYYY-MM-DD`) de `appointments` usando `substr()`
- La query de estrella tarda **~2 segundos** sobre 283 registros — con millones de registros Spark escalaría horizontalmente
- `Corte fade 16` es el servicio estrella tanto en mayo como en junio por volumen de citas
- El modelo snowflake en MongoDB tiene sentido porque los documentos ya están parcialmente normalizados (service_id, barber_id como ObjectId)
