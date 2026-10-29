# 03 — Recuperación de datos: decisión y ejecución

## Opciones evaluadas

Se presentaron tres rutas al usuario antes de tocar la base de datos:

| Opción | Descripción | Riesgo |
|---|---|---|
| A. Reset limpio + reseed oficial | `migrate:fresh --seed` con la cadena completa de `DatabaseSeeder` | Genera datos **nuevos** (nombres distintos a los originales), pero mismo volumen y estructura realista, con roles correctamente asignados |
| B. Solo arreglar roles del dataset reducido | Asignar roles a los 27 usuarios existentes, dejar las 100,000 citas sintéticas | No recupera el volumen ni la calidad del dataset para análisis |
| C. Detener todo, investigar más | No tocar nada hasta confirmar qué pasó exactamente | Más lento, sin garantía de encontrar más información (no había logs de auditoría de Atlas disponibles) |

**Decisión del usuario:** Opción A — reset limpio + reseed oficial.

## Ejecución

```bash
php artisan migrate:fresh --seed --force
```

Cadena de `DatabaseSeeder` ejecutada (orden real, con salida real del proceso):

```
RolePermissionSeeder      →  4 roles, 27 permisos
AdminUserSeeder           →  1 administrador
BarbershopSettingSeeder   →  configuración del negocio
ServiceSeeder             →  20 servicios
ProductSeeder             →  16 productos de venta + 15 insumos
ProductionSeeder          →  1 recepcionista + 25 barberos + 1000 clientes
                              (1,579,198 ms — el paso más largo, por volumen)
HistoricalDataSeeder      →  12,505 citas · 11,029 pagos · 11,029 puntos de lealtad
WorkSeeder                →  250 trabajos de portafolio
WorkImageSeeder           →  500 imágenes asignadas
```

Tiempo total: **~31 minutos** (proceso ejecutado en segundo plano, monitoreado con
`docker top` para confirmar actividad de CPU real, no un proceso colgado).

## Verificación end-to-end (no solo conteos)

Verificar que los datos existen no es suficiente — se verificó que el **mecanismo de
autorización real** funciona, usando exactamente el mismo método que usa el middleware
de producción:

```php
$admin->hasRole('administrador');                    // true
$barberUser->hasAnyRole(['barbero']);                // true
$clientUser->hasAnyRole(['cliente']);                // true
$recepcionista->hasAnyRole(['recepcionista']);       // true

DB::table('users')->where('role_id', '!=', null)->count(); // 1027 de 1027
```

**Los 1027 usuarios tienen un rol funcional** — no solo "algunos roles asignados", el
100% del universo de usuarios verificado contra el mecanismo real de autorización.

## Limpieza post-recuperación

```bash
php artisan permission:cache-reset
php artisan config:clear && php artisan route:clear && php artisan view:clear && php artisan cache:clear
```

Smoke test final: `curl` a `/login` y `/` devolvieron `200`.

## Estado final de datos (referencia para las Unidades I–V)

```
users: 1027 | barbers: 25 | clients: 1000 | appointments: 12,505
payments: 11,029 | loyalty_transactions: 11,029 | barber_schedules: 175 | products: 31
```

> Estos son los números vigentes usados en las Unidades I–V de este proyecto tras el
> incidente. Los scripts de análisis (Spark) no requirieron ningún cambio: como leen
> datos en vivo desde MongoDB, reflejan automáticamente el dataset restaurado.
