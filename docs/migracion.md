# Migración a UrbanBlade Analytics

Esta rama sustituye la organización por unidades académicas por módulos de producto.
No ejecuta migraciones de MongoDB ni modifica la aplicación Barber.

| Ruta anterior | Ruta actual |
| --- | --- |
| unidades/unidad_2_preparacion | analytics/preparation |
| unidades/unidad_3_supervisado | analytics/supervised |
| unidades/unidad_4_no_supervisado | analytics/unsupervised |
| unidades/unidad_5_visualizacion/main_dashboard.py | dashboard/app.py |
| unidades/unidad_5_visualizacion/dashboards_individuales | dashboard/views |
| unidades/unidad_5_visualizacion/exportar_insights_dashboard.py | pipelines/publicar_insights.py |
| unidades/unidad_6_caso_aplicado_laravel | docs/postmortems |

Los scripts de análisis se ejecutan mediante sus módulos, por ejemplo
`python -m analytics.preparation.etl`. Importarlos ya no inicia conexiones o entrenamientos.
Los conectores obsoletos se retiran; el acceso compartido usa
`config/mongo_spark_conexion_sinnulos.py` y `config/settings.py`.

## Configuración y operación

Conservar el archivo privado original. Referenciarlo con URBANBLADE_ENV_FILE o
--env-file; nunca incorporarlo a Git o a una imagen. Ver [operación](operacion.md).
La conexión core requiere CORE_MONGODB_URI o MONGO_USER/MONGO_PASSWORD/MONGO_CLUSTER/MONGO_DB.
MONGODB_URI heredada no se usa como sustituto implícito, porque podría pertenecer
a una cuenta con permisos de escritura.

La base derivada debe tener nombre distinto y credenciales propias. Publicar exige
--publish y ALLOW_ANALYTICS_PUBLICATION=true. La generación sintética es dry-run por
defecto; --apply exige ALLOW_SYNTHETIC_WRITES=true y solo permite appointments_synthetic.
Los consumidores conservan el campo unidad del contrato histórico de insights.

Antes de cambiar tareas programadas externas, inventariarlas y adaptar sus rutas;
el repositorio no demuestra que no existan cron u otros planificadores externos.
No ejecutar el publicador sobre Atlas como prueba de esta migración.

Se retiran entregables escolares y documentación duplicada. Las referencias técnicas
y el postmortem se conservan con su contexto histórico; las métricas antiguas no
constituyen evidencia de validación actual. Ver [modelos](modelos.md).

Validar con las pruebas de [desarrollo](desarrollo.md), revisar el diff y actualizar
manualmente los comandos de operación antes de aprobar una futura publicación.
