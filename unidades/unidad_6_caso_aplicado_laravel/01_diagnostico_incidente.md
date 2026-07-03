# 01 — Diagnóstico del incidente: cronología completa

## Síntoma reportado

> "Me estoy dando cuenta que a los barberos no se les está mostrando sus citas de todos
> los estados."

## Paso 1 — Bug de código (agenda del barbero)

**Investigación:** se localizó `BarberDashboardController::agenda()` y su vista
`resources/views/barber/agenda.blade.php`.

**Hallazgo:** la migración `2026_03_02_000130_create_appointments_table.php` define
**6 estados válidos**:

```php
$table->enum('estado', ['pendiente', 'confirmada', 'en_proceso', 'completada', 'cancelada', 'no_asistio'])
```

Pero el controlador y la vista de la agenda del barbero solo conocían **4**: `pendiente`,
`en_proceso`, `completada`, `cancelada`. Las citas en estado `confirmada` (una porción
real y significativa del total) no se contaban en ningún widget, no tenían chip de
filtro, y cayían al estilo gris genérico en la lista.

**Confirmación con datos reales** (antes de corregir):

```
Total citas del barbero: 451
completada: 401 | cancelada: 32 | pendiente: 10 | confirmada: 8   ← invisibles
```

**Fix aplicado:** se agregó `confirmada` (y `no_asistio`) a los contadores del
controlador, los chips de filtro, los estilos de la vista, y la validación del
formulario de cambio de estado. Ver commit correspondiente en el repo `barber`.

---

## Paso 2 — Reinicio de Docker y pérdida de acceso

Tras el fix, el usuario reinició completamente el entorno Docker y reportó:

> "Ya no tengo acceso a ningún rol."

**Primera hipótesis (descartada):** que el reinicio de contenedores hubiera vaciado la
base de datos. Se descartó de inmediato porque `barber_db` vive en **MongoDB Atlas**
(nube), no en un volumen local — un `docker compose down`/`up` no puede vaciar una base
de datos remota por sí solo.

**Verificación con `tinker`:**

```php
App\Models\Role::all();       // 4 roles: administrador, barbero, recepcionista, cliente
App\Models\Permission::count(); // 27 permisos
DB::connection('mongodb')->table('model_has_roles')->count(); // 0  ← sospechoso
```

Los roles y permisos existían, pero la colección pivote `model_has_roles` (donde Spatie
Permission normalmente registra qué usuario tiene qué rol) estaba vacía. Ver el detalle
técnico de por qué esto **no era en realidad el problema real** en
[`02_causa_raiz_tecnica.md`](02_causa_raiz_tecnica.md).

---

## Paso 3 — El hallazgo más grave: pérdida de datos

Al intentar reparar los roles, una verificación de conteos reales destapó algo mayor:

| Colección | Antes (conocido) | Encontrado tras el reinicio |
|---|---|---|
| `users` | 1027 | **27** |
| `barbers` | 25 | **3** |
| `clients` | 1000 | **21** |
| `appointments` | 12,505 | **100,000** |

El número **100,000** coincidía exactamente con lo documentado para
`MassiveDataSeeder` — una herramienta de pruebas de carga que **no borra nada**, solo
agrega citas sintéticas masivas usando los barberos/clientes que ya existan.

**Conclusión de la cronología:** en algún punto del "reinicio completo" se ejecutó un
reset de base de datos (p. ej. `migrate:fresh`, o un borrado manual vía el Data Explorer
de Atlas) que redujo drásticamente `users`/`barbers`/`clients`, y sobre ese remanente se
corrió `MassiveDataSeeder`, que solo añadió volumen sintético sin restaurar la
estructura real.

**Verificación de backups:** se revisó `backups/` — contenía únicamente volcados `.sql`
(formato MySQL, incompatible con MongoDB) del 17 de abril, anteriores incluso a la
creación del dataset realista (30 de junio). **No había backup recuperable.**

Con esta información se decidió, junto con el usuario, la ruta de remediación —
documentada en [`03_recuperacion_de_datos.md`](03_recuperacion_de_datos.md).
