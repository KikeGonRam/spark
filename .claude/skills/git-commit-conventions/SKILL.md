---
name: git-commit-conventions
description: Prepara mensajes de commit en español para que el usuario humano los ejecute. Ningún proveedor de IA puede crear commits ni hacer push en UrbanBlade.
---

# Entrega Git con propiedad humana

Ningún agente o proveedor de IA ejecuta `git commit`, `git push`, merge, rebase,
publicación de PR ni reescritura de historial en `barber`, `frontend-urban` o `spark`.
No se pide permiso para hacerlo: la ejecución queda reservada al usuario humano.

La IA puede inspeccionar estado/diff, editar y validar dentro del alcance autorizado. Al
finalizar entrega en español:

1. resumen de lo realizado;
2. archivos afectados;
3. pruebas y resultado;
4. pendientes o riesgos;
5. mensaje de commit sugerido y comandos opcionales para revisión humana.

El mensaje sugerido usa imperativo, máximo 72 caracteres en la primera línea, cuerpo
solo cuando aporte contexto, sin secretos ni líneas de coautoría de IA.
