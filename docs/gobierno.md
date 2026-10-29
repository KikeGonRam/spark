# Mantenimiento y entrega

## Responsabilidad y revisión

El responsable actual es [KikeGonRam](https://github.com/KikeGonRam), propietario
del repositorio y destinatario de CODEOWNERS. No se atribuyen obligaciones a otros
integrantes sin acordarlas. CODEOWNERS orienta la revisión; no implica que el autor
pueda aprobar su propio PR.

main recibe cambios mediante PR. Sus cuatro checks obligatorios son:

- Pruebas y guarda de solo lectura.
- Runtime Spark y dashboard.
- SonarCloud Code Analysis.
- GitGuardian Security Checks.

La protección exige rama actualizada y conversaciones resueltas, se aplica a
administradores e impide push forzado y borrado. No exige aprobaciones independientes
mientras solo haya un mantenedor acordado; revisar esa decisión cuando el equipo
formalice responsables. No usar --admin para omitir checks.

Conservar las ramas y fusionar con merge commit. Ver [CONTRIBUTING](../CONTRIBUTING.md).
La configuración descrita debe contrastarse con GitHub al cambiar las protecciones;
este documento no las configura automáticamente.

## Versiones

0.1.0 identifica el paquete de desarrollo. No existe una release por el mero hecho
de que ese número aparezca en pyproject.toml. Registrar cambios en
[CHANGELOG](../CHANGELOG.md) y preparar release y tag como una acción explícita,
con commit exacto, compatibilidad, notas y comprobaciones verificables.

Antes de publicar una versión estable, comprobar documentación de instalación,
pruebas y análisis del commit, compatibilidad con Barber, permisos de datos,
procedimiento de recuperación y limitaciones de modelos. No incluir datos reales,
logs privados o modelos persistidos en artefactos públicos sin revisión específica.
Un tag o release no autoriza un despliegue ni publicar insights en Atlas.

## Próximas entregas

1. Evaluación temporal de modelos: baseline por objetivo, partición por fecha,
   métricas apropiadas y prevención de fugas; criterios en [modelos](modelos.md).
   Las pruebas sintéticas actuales no sustituyen esta evaluación.
2. Revisión de compatibilidad Mongo/kernel y migración del runner antes de retirar
   Ubuntu 22.04; mantener las pruebas locales con escritura separadas de Atlas.
3. Aceptación funcional del dashboard con una sesión y entorno autorizados,
   comprobando roles y estados vacíos además del healthcheck. Sin crear cuentas
   de producción o cambiar credenciales como parte automática de la prueba.

El funnel sigue fuera de alcance hasta definir eventos, privacidad, contrato de
frontend y autorización. Las decisiones vigentes están en [ADR](decisiones/README.md).
