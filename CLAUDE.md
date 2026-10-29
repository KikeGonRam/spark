# UrbanBlade Analytics · instrucciones de mantenimiento

Este repositorio es un producto de analítica de UrbanBlade. No está organizado por
unidades académicas y no necesita tareas del cuatrimestre para atender una petición
explícita del propietario. Leer README.md, docs/arquitectura.md y SECURITY.md.

## Estructura

- config/: datos, configuración, autenticación y publicación atómica.
- analytics/preparation/: preparación, calidad y ETL.
- analytics/supervised/ y analytics/unsupervised/: modelos y patrones.
- dashboard/app.py y dashboard/views/: interfaz Streamlit.
- pipelines/publicar_insights.py: derivados consumidos por Barber.
- data_ingestion/: datos sintéticos con escritura explícita y separada del core.
- tests/: contratos, guardas, integración local y runtime sintético.

## Límites de datos

El core se lee con credenciales de solo lectura; no es un destino de publicación.
Solo se escriben analytics_insights y appointments_synthetic en la base de derivados,
con credenciales distintas y habilitación explícita. No ejecutar esas operaciones
contra Atlas por el solo hecho de editar el repositorio.

La existencia de un .env no autoriza copiarlo, imprimirlo o versionarlo. Se puede usar
URBANBLADE_ENV_FILE para apuntar al archivo privado existente, sin duplicarlo.
No escribir PII en artefactos de CI. El diagnóstico muestra solo flags y tipos de error.

No ejecutar migraciones, seeders, resets, rotaciones de credenciales o cambios de IAM
para una tarea de Spark. Conservar los postmortems en docs/postmortems como antecedentes,
no como operaciones para repetir. Los roles remotos se verifican, no se deducen del código.

## Calidad y entrega

Python 3.12, Java 17 y Spark 3.5.x. El dashboard no instala torch/tensorflow.
Usar requirements-ci.txt para pruebas rápidas y requirements-dashboard.txt para runtime.
Validar sintaxis, pruebas, guardas, dependencias y runtime con datos sintéticos.
La publicación remota y el despliegue son evidencias distintas de la validación local.

Preservar trabajo ajeno. Rama por cambio desde main revisada; commit/push/PR solo
con orden del propietario para este cambio. Mensajes en español, sin atribuciones
de herramientas, force push ni eliminación de ramas. Spark no se despliega automáticamente.
Las skills de proveedores deben respetar estos límites y la petición vigente del usuario.
