# ADR-001: aislar lectura operativa y escritura de derivados

Estado: aceptada. Registro: 2026-10-29. Responsable de mantenimiento: propietario
del repositorio. Documenta el comportamiento integrado en el PR #1.

## Contexto

Spark consulta datos compartidos con Barber. Una tarea analítica o fixture no debe
alterar las colecciones operativas. El postmortem conservado documenta las
consecuencias de confundir una preparación de entorno con una limpieza de datos.

## Decisión

El core se consulta mediante una identidad de solo lectura. Los derivados usan
credenciales propias y una base con otro nombre. La configuración rechaza usar
el mismo nombre para ambas y no reutiliza MONGODB_URI como fallback privilegiado.

La publicación de analytics_insights requiere --publish y su flag de habilitación.
La generación sintética requiere --apply y otro flag; solo usa appointments_synthetic.
La interfaz fija ambas habilitaciones en false. Las pruebas con escritura aceptan
únicamente Mongo local y bases propias terminadas en _e2e.

## Consecuencias y verificación

Las guardas del código complementan los permisos del servidor. Un cambio de
credenciales requiere revisar privilegios efectivos; las pruebas sintéticas no
certifican Atlas. El diagnóstico de conexión solo ejecuta ping y connectionStatus.

Se conserva el contrato de insights de Barber, incluido unidad. Una futura
migración exige revisar al consumidor, compatibilidad y recuperación antes de
publicar. No se ejecutan migraciones o seeders del core desde Spark.

Ver [arquitectura](../arquitectura.md), [operación](../operacion.md) y
[seguridad](../../SECURITY.md).
