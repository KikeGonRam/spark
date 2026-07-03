# Unidad VI — Caso aplicado: diagnóstico y gobernanza de datos en producción

**No forma parte de la secuencia didáctica oficial** (que define Unidades I–V). Se agrega
como extensión práctica porque el equipo tuvo que resolver un incidente real sobre la
**misma base de datos** (`barber_db`, MongoDB Atlas) que alimenta las Unidades I–V — un
ejercicio genuino de extracción del conocimiento aplicado a un problema de producción,
no a un dataset de práctica.

**Sistema:** UrbanBlade backend (Laravel 12 + MongoDB, Docker) — repositorio separado del
proyecto Spark, pero comparte la base de datos `barber_db`.

---

## Por qué importa esta unidad

Las Unidades I–V tratan la extracción de conocimiento como análisis **sobre datos ya
limpios y disponibles**. Esta unidad documenta lo que pasa **antes** de eso en un sistema
real: cómo se detecta que los datos están mal, cómo se investiga la causa con las mismas
técnicas de consulta/agregación que las Unidades II–IV, y cómo se decide y ejecuta una
remediación sin perder más información de la necesaria.

## Entregables de esta unidad

| Documento | Contenido |
|---|---|
| [`01_diagnostico_incidente.md`](01_diagnostico_incidente.md) | Cronología: del síntoma reportado (barberos sin ver sus citas) al hallazgo de pérdida de datos |
| [`02_causa_raiz_tecnica.md`](02_causa_raiz_tecnica.md) | Análisis técnico: incompatibilidad Spatie Permission + MongoDB, mecanismo real de roles |
| [`03_recuperacion_de_datos.md`](03_recuperacion_de_datos.md) | Remediación ejecutada (`migrate:fresh --seed`) y verificación end-to-end |
| [`04_gobernanza_y_limpieza.md`](04_gobernanza_y_limpieza.md) | Limpieza de seeders legado y documentación obsoleta — deuda técnica |
| [`05_automatizacion_onboarding.md`](05_automatizacion_onboarding.md) | Script de onboarding para nuevos integrantes del equipo |

## Resumen ejecutivo

1. Un barbero reportó que su agenda no mostraba citas en todos los estados posibles.
2. La causa inmediata era un **bug de código** (estados faltantes en una vista) — se corrigió.
3. Al verificar el fix contra datos reales, se detectó que **ningún usuario tenía rol
   asignado** tras un reinicio de Docker.
4. La investigación reveló que el problema no era solo de roles: la base de datos había
   perdido su dataset realista (1000 clientes, 25 barberos, 12,505 citas) y tenía en su
   lugar un dataset reducido (27 usuarios, 3 barberos, 21 clientes) más 100,000 citas
   sintéticas de una herramienta de pruebas de carga.
5. Se restauró el volumen de datos con la cadena oficial de seeders, y se verificó que
   los tres mecanismos involucrados (Spatie Permission, el driver MongoDB-Eloquent, y el
   middleware de la aplicación) funcionan correctamente juntos.
6. Como consecuencia, se limpiaron seeders legado y documentación desactualizada, y se
   construyó un script de onboarding para que el equipo no repita el mismo problema al
   clonar el proyecto.
