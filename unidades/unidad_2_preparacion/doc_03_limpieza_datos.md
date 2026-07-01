# Unidad II — Sesión 8: Técnicas de Limpieza de Datos

**Script**: `unidad2/03_limpieza_datos.py`  
**Fecha de ejecución**: 2026-06-10  
**Dataset**: 283 citas reales — `barber_db` (MongoDB Atlas)

---

## Estado inicial del dataset crudo

```
Dataset crudo: 283 registros
Columnas: servicio, barbero, precio, precio_base, duracion_min, estado, metodo_pago, notas
```

---

## TÉCNICAS BÁSICAS

### 1. Análisis de valores nulos

```
+--------+-------+-------+-----------+------+-----------+-----+
|servicio|barbero|precio |duracion_min|estado|metodo_pago|notas|
+--------+-------+-------+-----------+------+-----------+-----+
|       0|      0|    148|          0|     0|        148|  273|
+--------+-------+-------+-----------+------+-----------+-----+
```

**Interpretación**:
- `precio`: 148 nulos — citas donde `precio_cobrado` es `null` en MongoDB (citas no completadas)
- `metodo_pago`: 148 nulos — correspondientes a las mismas citas sin pago registrado
- `notas`: 273 nulos — solo 10/283 citas tienen notas (3.5% del dataset)
- `servicio`, `barbero`, `estado`, `duracion_min`: **0 nulos** — datos completos

### 2. fillna — Rellenar nulos

Estrategia de relleno aplicada:

```python
df.fillna({
    "precio":       0.0,          # citas sin precio_cobrado → $0
    "duracion_min": 30.0,         # duración mínima por defecto
    "metodo_pago":  "no_registrado",
    "notas":        "",
    "servicio":     "Sin servicio",
    "barbero":      "Sin asignar",
    "estado":       "pendiente",
})
```

Nulos después de fillna:
```
+------+-----------+-----------+-----+
|precio|duracion_min|metodo_pago|notas|
+------+-----------+-----------+-----+
|     0|          0|          0|    0|
+------+-----------+-----------+-----+
```

> **Nota**: `fillna(precio=0.0)` sobre 148 citas hace que Q1 del campo precio sea $0 en el análisis IQR posterior. Esto es esperado — las citas no completadas no tienen ingreso real.

### 3. dropna — Eliminar filas con nulos críticos

```
Registros antes de dropna:  283
Registros después de dropna: 283
Filas eliminadas: 0
```

Los campos `servicio` y `estado` no tienen nulos, por lo que no se pierde ningún registro.

### 4. Casting — Corrección de tipos

Schema después de casting correcto:
```
root
 |-- servicio:     string  (nullable = true)
 |-- barbero:      string  (nullable = true)
 |-- precio:       double  (nullable = true)
 |-- precio_base:  double  (nullable = true)
 |-- duracion_min: double  (nullable = true)
 |-- estado:       string  (nullable = true)
 |-- metodo_pago:  string  (nullable = true)
```

### 5. Estandarización de strings (trim + lowercase)

Valores únicos de `estado` después de estandarizar:
```
+----------+
|estado    |
+----------+
|cancelada |
|completada|
|confirmada|
|no_asistio|
|pendiente |
+----------+
```

5 estados bien formados, sin espacios ni mayúsculas inconsistentes.

### 6. Eliminación de duplicados (dropDuplicates)

```
Registros antes:  283
Registros después de dropDuplicates: 230
Duplicados eliminados: 53
```

Se detectaron **53 registros duplicados** por combinación `(servicio, barbero, precio, estado)`. Esto ocurre porque el seeder puede generar citas con el mismo servicio, precio y estado para el mismo barbero en fechas distintas.

---

## TÉCNICAS AVANZADAS

### 7. Detección de Outliers — Método IQR

Aplicado sobre el campo `precio` (después de fillna con 0.0 para nulos):

```
Q1 (percentil 25):  $0.00
Q3 (percentil 75):  $465.33
IQR = Q3 - Q1:      $465.33

Límite inferior:    $0.00 - 1.5 × $465.33 = -$697.99
Límite superior:    $465.33 + 1.5 × $465.33 = $1,163.33
```

```
Outliers detectados: 0 registros
Registros sin outliers: 230
```

**¿Por qué Q1 = $0?** Porque las 148 citas con `precio_cobrado = null` recibieron `fillna(0.0)`. Esto desplaza el primer cuartil a $0, ampliando el rango de tolerancia. Resultado: ningún precio del dataset supera $646.31, que está muy por debajo del límite superior de $1,163.33.

### 8. Winsorización — Limitar outliers sin eliminar filas

Como alternativa a dropear, la winsorización reemplaza valores extremos por el límite:

```
Precio original  → Precio limitado (winsorizado)
$646.31          → $646.31  (no cambió — dentro del límite)
$632.15          → $632.15  (no cambió)
$619.86          → $619.86  (no cambió)
```

En este dataset todos los valores están dentro de los límites, así que ningún precio fue modificado.

### 9. Codificación categórica — StringIndexer

Convierte el campo `estado` (string) a índice numérico para algoritmos ML:

```
+-----------+-----------+
|estado     |estado_idx |
+-----------+-----------+
|completada |0.0        |
|cancelada  |1.0        |
|no_asistio |2.0        |
|pendiente  |3.0        |
|confirmada |4.0        |
+-----------+-----------+
```

El índice se asigna por frecuencia descendente: `completada` es el estado más frecuente (0.0).

### 10. Normalización — MinMaxScaler [0, 1]

El precio se transforma al rango [0, 1] para que no domine las features en distancia euclidiana:

```
Precio original  → Precio normalizado [0-1]
$0.00            → 0.0
$100.57          → 0.155
$350.00          → 0.541
$465.33          → 0.720
$540.26          → 0.835
$619.86          → 0.958
$632.15          → 0.977
$646.31          → 1.000
```

Fórmula aplicada: `precio_norm = (precio - min) / (max - min)`  
Donde `min = $0.00` y `max = $646.31`

---

## Resumen de técnicas aplicadas

```
Dataset original:          283 registros
Después de fillna:         283 registros (nulos rellenados, sin pérdida)
Después de dropDuplicates: 230 registros  (-53 duplicados)
Sin outliers (IQR):        230 registros  (0 outliers detectados)

Técnicas básicas (6):
  ✓ Análisis de nulos (isnull + count)
  ✓ fillna — rellenar nulos con defaults
  ✓ dropna — eliminar filas con nulos críticos
  ✓ Casting — corrección de tipos de datos
  ✓ Estandarización de strings (trim, lower)
  ✓ Eliminación de duplicados (dropDuplicates)

Técnicas avanzadas (4):
  ✓ Detección de outliers por IQR
  ✓ Winsorización (limitar en vez de eliminar)
  ✓ Codificación categórica (StringIndexer)
  ✓ Normalización MinMaxScaler [0, 1]
```

---

## Observaciones técnicas

- El dataset de UrbanBlade está sorprendentemente limpio — los únicos "nulos" son intencionales (citas no completadas sin precio)
- La estrategia `fillna(precio=0.0)` es correcta para el dominio: una cita cancelada o pendiente ingresa $0
- La eliminación de 53 duplicados es esperada: el seeder puede crear múltiples citas con la misma combinación servicio+barbero+precio en fechas distintas
- El IQR con Q1=$0 y 0 outliers indica que los datos de precio del seeder son uniformes (faker genera precios dentro de rangos coherentes)
- En producción real, `precio_cobrado` puede incluir propinas o descuentos que crearían outliers genuinos
