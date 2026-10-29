---
name: git-commit-conventions
description: "Flujo de Git de UrbanBlade desde el 2026-10-04: una rama por cambio, PR a main con CI en verde y la rama se conserva. Commits en español sin coautoría de IA. Cuando el propietario pide subir un cambio, la IA hace commit, push y PR y, si todo sale bien, fusiona y despliega barber y frontend-urban a staging sin volver a preguntar."
---

# Flujo de Git y commits — UrbanBlade

Aplica igual en `barber`, `frontend-urban`, `UrbanBladeMobile` y `spark`. Desde el
2026-10-04 `main` está **protegida** en GitHub en `barber` y `frontend-urban` (en
`UrbanBladeMobile` la activa su dueño, `al140605`): no admite push directo ni push forzado,
no se puede borrar, y solo recibe cambios por PR con los checks del CI en verde. La regla
vale también para administradores.

## Ramas y PR

1. **Partir de `main` al día:** `git fetch origin` y revisar `git log origin/main` antes
   de empezar; puede que el cambio ya esté subido (pasó con TT22) o que otro agente haya
   empujado algo.
2. **Una rama por cambio**, creada desde `origin/main`, con tipo, ID de la tarea y una
   descripción corta en minúsculas con guiones:
   `feat/t114-terraform-variables`, `fix/tt04-forgot-password-generico`,
   `chore/tt22-dependabot`, `docs/flujo-ramas-pr`.
3. **Validar en local** con los comandos del repositorio antes de cada push (en `barber`
   siempre `.\test.ps1`, nunca `php artisan test` directo; ver `urbanblade-guardrails`).
4. **Commits y push de la rama:** `git push -u origin <rama>`.
5. **PR a `main`** con `gh pr create`: título igual al commit principal y cuerpo con
   resumen, archivos, pruebas ejecutadas y la tarea (HU/T o HT/TT).
6. **Fusionar solo con el CI en verde**, con *merge commit*
   (`gh pr merge <n> --merge`), **sin `--delete-branch`**. Las ramas no se borran, ni en
   GitHub ni en local: quedan como historial del trabajo.
7. Después de fusionar, `git checkout main && git merge --ff-only origin/main`.
8. **Desplegar** `barber` y/o `frontend-urban` a staging si el cambio lo requiere (ver
   "Fusión y despliegue automáticos").

Los PR de Dependabot siguen el mismo criterio: se fusionan los que pasan todos los checks;
las versiones mayores se revisan con su guía de migración.

## Quién ejecuta Git

- La IA puede inspeccionar estado y diff, crear ramas locales, editar dentro del alcance
  autorizado y correr validaciones seguras sin pedir permiso.
- **El primer `git commit` / `git push` / `gh pr create` de cada cambio requiere la orden
  del propietario en el chat** ("súbelo", "haz el PR", "sube y despliega"). Esa orden no se
  extiende a otros cambios. Una vez dada, la fusión y el despliegue siguen la sección
  siguiente sin volver a preguntar.
- Nunca: `push --force`, `reset --hard` sobre trabajo ajeno, reescribir historial
  publicado, ni borrar ramas publicadas. Una rama local vacía creada por error sí se puede
  quitar avisando al propietario.
- Sin esa orden, la IA entrega en español: resumen, archivos, pruebas y resultado,
  pendientes y los comandos exactos (rama, `git add` con rutas, commit, push y
  `gh pr create`) para que el propietario los ejecute.

## Fusión y despliegue automáticos (autorizado por el propietario el 2026-10-04)

Cuando el propietario ordena subir un cambio, la IA hace commit, push y PR y, **si todo
sale bien, fusiona el PR y despliega a staging sin volver a pedir permiso**.

**"Todo sale bien" significa las cuatro cosas:** (1) validación local limpia, (2) todos los
checks obligatorios del PR en verde y sin conflictos, (3) fusión con *merge commit* sin
borrar la rama y (4) CI de `main` del commit de fusión en verde. Si falla cualquiera, la
IA se detiene, no fuerza nada y reporta la causa.

**Despliegue:** solo `barber` y `frontend-urban`, a staging, con el agente
`urbanblade-deploy`, y se despliega el servicio cuya imagen cambió (los dos si cambiaron
ambos). No se despliega un cambio que solo toca documentación, skills, `CLAUDE.md`,
`AGENTS.md`, `.github/`, pruebas o la app Android. El despliegue verifica el digest de la
tarea y las URL; si la verificación falla, **revierte solo** a la imagen de respaldo
`rollback-...` y reporta.

**Escrituras en AWS permitidas** (excepción a la regla de solo lectura del 2026-10-03,
acotada a esto): `docker push` y etiqueta de respaldo en los repos ECR
`urbanblade/barber` y `urbanblade/frontend-urban`, y `ecs update-service
--force-new-deployment` en `uba-stg-barber` y `uba-stg-frontend`. Nada más: ni S3, ni IAM,
ni secretos, ni task definitions, ni los respaldos de la Fase 5, ni otros servicios.

**Sigue pidiendo el "sí" del propietario:** un cambio que incluya migraciones o seeders
(el contenedor de staging migra contra Atlas al arrancar), cualquier escritura en Atlas,
producción, cambios de secretos o variables, y cualquier despliegue fuera de los dos
servicios anteriores.

## Idioma

Todos los mensajes de commit y de PR van en **español**. Términos técnicos sin
traducción natural (nombres de archivos, comandos, clases, mensajes de error citados) se
dejan en su idioma original.

## Autoría

Los commits quedan a nombre del autor humano configurado localmente (`KikeGonRam`).
**Prohibido** agregar `Co-Authored-By: ...`, `Generated with ...` o cualquier atribución a
herramientas de IA en commits y PR. No reescribir commits históricos para quitarla.

## Formato

- Primera línea: `tipo(alcance): ID descripción`, en minúsculas y sin punto final.
  Tipos: `feat`, `fix`, `docs`, `test`, `chore`, `ci`, `refactor`, `perf`.
  Ejemplo: `feat(pagos): T144 mensajes claros al cancelar el pago con tarjeta`.
- Cuerpo (si hace falta contexto): explica el *por qué*, no solo el *qué*; útil para
  decisiones no obvias, bugs encontrados o pendientes que quedan a propósito.
- Nunca credenciales, tokens, contraseñas ni datos sensibles en mensajes de commit o PR.
- No incluir en los commits los archivos que el propietario excluye: `README.md` de
  `frontend-urban`, `public/video/UrbanBlade.gif` de `barber` y salidas locales como
  `diagnostico.txt`.

## Ejemplo

```
fix(auth): TT04 forgot-password responde igual exista o no el correo

Antes devolvía "Enlace de recuperación enviado" o "No se pudo enviar" según el correo
existiera, lo que permitía enumerar cuentas. Ahora siempre responde 200 con el mismo
mensaje y el envío real sigue igual.
```
