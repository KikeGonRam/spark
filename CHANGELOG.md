# Registro de cambios

Se registran cambios de producto y compatibilidad. Fusionar código no implica
publicar una versión ni desplegar un servicio.

## Sin publicar

### 2026-10-29

- Validación local autenticada: perfil aislado de Barber, tema oscuro y etiqueta de origen efectiva.
- PyArrow 24 fijado para serializar tablas con NumPy 1.26.4; prueba de ida y vuelta incluida.

- Organización por módulos de preparación, modelos, dashboard y publicación.
- Arquitectura, operación, evaluación, contribución y seguridad actualizadas.
- Licencia GPL-3.0-only y plantillas de colaboración.
- Core de solo lectura, derivados separados y escrituras con habilitación explícita.
- Python 3.12, Java 17 y Spark 3.5; locks completos con hashes y manifiesto PEP 751.
- Actualización del perfil opcional a SciPy 1.17.1 y Matplotlib 3.11.2, conservando NumPy 1.26.4.
- Pruebas de runtime y contratos de cohortes, ingresos y proyecciones no negativas.
- Protección de main con PR y cuatro checks obligatorios; reporte privado de seguridad.

Entrega: [PR #1](https://github.com/KikeGonRam/spark/pull/1),
[commit de integración](https://github.com/KikeGonRam/spark/commit/c3ef9901d160fc0839a5e01143a49f78a81e466a).
La versión 0.1.0 del paquete sigue siendo de desarrollo: no se ha creado una release.
