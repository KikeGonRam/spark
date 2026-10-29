# 02 — Causa raíz técnica: Spatie Permission sobre MongoDB

## El hallazgo contraintuitivo

`model_has_roles` (la colección donde Spatie Permission normalmente guarda "qué usuario
tiene qué rol") apareció vacía **incluso inmediatamente después de re-sembrar la base de
datos con seeders que sí llaman `assignRole()` explícitamente**. Esto obligó a investigar
más profundo: ¿por qué una llamada que no lanza ninguna excepción no persiste nada?

## Cómo funciona realmente en este proyecto

`spatie/laravel-permission` está diseñado para bases de datos relacionales: usa una
relación `MorphToMany` que, en SQL, se traduce en una tabla pivote real
(`model_has_roles`). El paquete `mongodb/laravel-mongodb` (el driver Eloquent para
Mongo que usa este proyecto) implementa `MorphToMany` de forma distinta: en vez de
escribir en una colección pivote separada, **embebe los IDs relacionados como un array
dentro del propio documento**.

Verificación directa en el documento crudo de un usuario:

```php
DB::connection('mongodb')->table('users')->where('email', '...')->first();
// ...
// [role_id] => Array ( [0] => 6a45f2cebf8203e6d80e7ccb )
```

Es decir: `assignRole('administrador')` sí funciona — pero escribe el ID del rol en un
campo `role_id` embebido en el documento del usuario, **no** en `model_has_roles`. Esa
colección existe (por la migración `create_permission_tables`) pero queda vacía porque
el driver de Mongo nunca la usa para este tipo de relación.

## Por qué esto no rompe la aplicación

El middleware real de autorización no consulta `model_has_roles` directamente:

```php
// app/Http/Middleware/Role/EnsureUserHasRole.php
if (! $user->hasAnyRole($roles)) {
    abort(403);
}
```

`hasAnyRole()` es un método del trait `HasRoles` que **carga la relación `roles()`** del
usuario (la cual sí resuelve correctamente contra el campo embebido `role_id`) y compara
nombres en PHP. Por eso, verificar con `hasAnyRole()`/`hasRole()`/`getRoleNames()` da el
resultado correcto, mientras que consultar `model_has_roles` como tabla independiente
da un falso negativo.

**Limitación adicional encontrada:** el scope de consulta `User::role('administrador')`
(que sí necesita una query "híbrida" contra la relación) falla con:

```
LogicException: MorphToMany is not supported for hybrid query constraints.
```

Esto confirma que la limitación es real y conocida del paquete: las relaciones
`morphToMany` de Spatie funcionan para operaciones de instancia (`$user->hasRole()`)
pero no para *scopes* de consulta masiva sobre el modelo. **Regla práctica para el
equipo:** para verificar o depurar roles en este proyecto, usar siempre
`$user->hasRole()` / `$user->getRoleNames()`, nunca `Model::role(...)` ni consultas
directas a `model_has_roles`.

## Por qué la pérdida de roles SÍ era real

Lo anterior explica por qué `model_has_roles` vacío no es necesariamente un bug — pero
no explica por qué los usuarios *sí* habían perdido acceso. La respuesta está en el
Paso 3 del diagnóstico: el dataset reducido (27 usuarios) provenía de un proceso que
**nunca llamó a `assignRole()`** para esos usuarios en absoluto (por eso su campo
`role_id` estaba ausente, no solo vacío). El síntoma reportado por el usuario era
correcto; el mecanismo interno que lo causaba era distinto del que se sospechó primero.
