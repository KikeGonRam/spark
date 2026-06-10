# Unidad II — Sesión 6: Tipos y Fuentes de Datos

**Script**: `unidad2/01_tipos_fuentes_datos.py`  
**Fecha de ejecución**: 2026-06-10  
**Dataset**: 283 citas reales — `barber_db` (MongoDB Atlas)

---

## Resultado: Tipo 1 — Datos Estructurados

Fuente: `appointments` + `services` + `barbers` + `users` (join de 4 colecciones)

### Esquema definido (StructType)

```
root
 |-- servicio:     string  (nullable = true)
 |-- barbero:      string  (nullable = true)
 |-- duracion_min: integer (nullable = true)
 |-- precio:       double  (nullable = true)
 |-- estado:       string  (nullable = true)
 |-- fecha:        string  (nullable = true)
```

### Muestra de datos

```
+--------------------+--------------+------------+------+----------+----------+
|            servicio|       barbero|duracion_min|precio|    estado|     fecha|
+--------------------+--------------+------------+------+----------+----------+
|Combo corte y bar...|Barbero Test 2|          45|619.86|confirmada|2026-06-09|
|       Corte fade 86|Barbero Test 1|          30|439.81|completada|2026-06-09|
|    Corte clásico 45|Barbero Test 2|          30|632.15| pendiente|2026-06-09|
|       Corte fade 16|  Barbero Test|          75|540.26|confirmada|2026-06-09|
|       Corte fade 16|  Barbero Test|          30|160.26|confirmada|2026-06-09|
+--------------------+--------------+------------+------+----------+----------+
```

### Estadísticas descriptivas

```
+-------+-----------------+------------------+
|summary|           precio|      duracion_min|
+-------+-----------------+------------------+
|  count|              283|               283|
|   mean|393.7191872791519| 39.43462897526502|
| stddev|158.1588398961007|16.519872047574566|
|    min|           100.57|                30|
|    max|           646.31|                75|
+-------+-----------------+------------------+
```

**Interpretación**: El precio promedio es **$393.72 MXN** con desviación estándar de $158.16, lo que indica alta variabilidad. La duración promedio es **39.4 minutos** (rango: 30–75 min).

---

## Resultado: Tipo 2 — Datos Semi-estructurados

Fuente: documentos BSON crudos de `appointments` (sin join, campo a campo variable)

### 5 documentos raw de MongoDB

```
Documento 1:
  barber_id:      '6a283b9c166b79fce506975d'
  service_id:     '6a283bb7166b79fce50697a3'
  estado:         'confirmada'
  notas:          'Voluptatem ea odio dolorem enim tempora tempora odio voluptas.'
  precio_cobrado: None                          ← campo NULO

Documento 2:
  barber_id:      '6a283b95166b79fce5069751'
  service_id:     '6a283bb6166b79fce50697a0'
  estado:         'completada'
  notas:          None                          ← campo NULO
  precio_cobrado: 439.81

Documento 3:
  barber_id:      '6a283b9c166b79fce506975d'
  service_id:     '6a283bb6166b79fce506979f'
  estado:         'pendiente'
  notas:          None
  precio_cobrado: 632.15

Documento 4:
  barber_id:      '6a283b8f166b79fce5069745'
  service_id:     '6a283bb6166b79fce50697a1'
  estado:         'confirmada'
  notas:          None
  precio_cobrado: None                          ← dos campos NULOS

Documento 5:
  barber_id:      '6a283b8f166b79fce5069745'
  service_id:     '6a283bb7166b79fce50697a7'
  estado:         'confirmada'
  notas:          'Magni et numquam quisquam qui nesciunt mollitia.'
  precio_cobrado: 160.26
```

### Representación JSON (documento 1)

```json
{
  "barber_id":      "6a283b9c166b79fce506975d",
  "service_id":     "6a283bb7166b79fce50697a3",
  "estado":         "confirmada",
  "notas":          "Voluptatem ea odio dolorem enim tempora tempora odio voluptas.",
  "precio_cobrado": "None"
}
```

**Características semi-estructuradas observadas**:
- `precio_cobrado` puede ser `null` o `float` según el estado de la cita
- `notas` puede estar ausente (documentos 2, 3, 4) o contener texto libre (documentos 1, 5)
- `productos` puede ser `null`, `[]` o `[{...}]` (array anidado)
- Los IDs (`barber_id`, `service_id`) son ObjectIds de 24 caracteres en formato hex

---

## Resultado: Tipo 3 — Datos No Estructurados

Fuente: campo `notas` (texto libre) de `appointments`  
Citas con notas registradas: **10 de 283**

```
+----------+--------------------------------------------------------------+
|estado    |nota                                                          |
+----------+--------------------------------------------------------------+
|confirmada|Voluptatem ea odio dolorem enim tempora tempora odio voluptas.|
|confirmada|Magni et numquam quisquam qui nesciunt mollitia.              |
|pendiente |Nostrum sunt ex iure neque quam.                              |
|completada|Distinctio dolores voluptates voluptatem est vitae a quo nisi.|
|completada|Quia consequatur id nihil quasi provident aliquam excepturi.  |
|completada|Repellat sint nemo eligendi qui voluptatem in.                |
|completada|Omnis cumque aut pariatur hic eos a.                          |
|completada|Consectetur et et et rerum sit aut.                           |
|completada|Debitis qui neque et iure pariatur et soluta similique.       |
|completada|Similique et rem quis.                                        |
+----------+--------------------------------------------------------------+
```

**Características observadas**:
- Longitud variable: de 4 a 10 palabras por nota
- Sin esquema ni tipos fijos — Spark lo trata como `string` plano
- Contenido generado por faker en el seeder (texto en latín)
- En producción real: comentarios de clientes, instrucciones especiales

---

## Tabla Comparativa Final

```
+------------------+-------------------+------------------------+------------------+
| Tipo             | Fuente UrbanBlade | Formato                | Procesamiento    |
+------------------+-------------------+------------------------+------------------+
| Estructurado     | appointments      | Tabla con schema fijo  | SQL / Spark DF   |
|                  | + services        | (StructType)           | directo          |
+------------------+-------------------+------------------------+------------------+
| Semi-estructurado| MongoDB BSON docs | JSON / BSON con campos | Parsing + mapeo  |
|                  | (raw documents)   | opcionales y anidados  | manual           |
+------------------+-------------------+------------------------+------------------+
| No estructurado  | appointments.notas| Texto libre            | NLP / expresiones|
|                  |                   | sin esquema            | regulares        |
+------------------+-------------------+------------------------+------------------+
```

---

## Observaciones técnicas

- El **esquema StructType** es lo que hace que los datos sean "estructurados" en Spark — Spark rechazará tipos incorrectos en tiempo de carga
- Los datos semi-estructurados de MongoDB requieren un paso de normalización (el join que hace `config/mongo_spark_conexion.py`) para convertirse en estructurados
- Solo **10/283 citas (3.5%)** tienen notas — muy baja densidad de datos no estructurados en este dataset
- El campo `precio_cobrado = None` en citas no completadas es el motivo del fallback a `services.precio` en el config
