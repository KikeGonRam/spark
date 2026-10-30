# Operación de UrbanBlade Analytics

## Configuración existente

El archivo real permanece fuera de Git. Configurar URBANBLADE_ENV_FILE para usarlo
sin duplicarlo o usar un .env privado del checkout. Las variables de proceso tienen
prioridad; cargar el archivo no debe sobreescribir una habilitación de escritura
bloqueada por el entorno.

```powershell
python -m config.diagnostics --env-file C:/ruta/privada/.env
```

Sin --connect no hay conexión. Con --connect solo se ejecutan ping y consulta de
privilegios: no se listan registros ni contraseñas. Ante error se informa el tipo,
no el texto completo del driver. Un diagnóstico favorable no certifica toda la aplicación.

## Dashboard local

```powershell
$env:SPARK_ENV_FILE = "C:/ruta/privada/.env"
docker compose --env-file "$env:SPARK_ENV_FILE" config --quiet
docker compose --env-file "$env:SPARK_ENV_FILE" up -d --build dashboard
```

SPARK_ENV_FILE selecciona el archivo del servicio; --env-file también lo usa
para resolver las variables de Compose, sin imprimir sus valores. El archivo
se carga como entorno del proceso y no se copia a la imagen.

Revisar el contexto Docker antes de operar. Este Compose es local, publica en
loopback y usa la red externa existente indicada por BARBER_DOCKER_NETWORK. No
inicia ni reinicia Barber, no migra datos y no es un despliegue AWS. Los flags de
escritura se fijan en false para la interfaz. El proceso usa un usuario no root,
capacidades reducidas y Java 17.

Para acceso por proxy o en un servidor, revisar HTTPS, orígenes, autenticación,
puertos y configuración efectiva con autorización específica. No desactivar XSRF
ni exponer 8501 en todas las interfaces para solucionar una prueba local.

## Publicar derivados

Antes de publicar, registrar responsable, alcance, commit y consumidores; revisar
base, identidad y privilegios. Conservar una recuperación privada del último snapshot
si el procedimiento operativo la requiere. No modificar el core ni añadir roles
para hacer pasar una publicación.

```powershell
python -m pipelines.publicar_insights
```

Calcula sin publicar. Solo con autorización de escritura específica se habilitan
ALLOW_ANALYTICS_PUBLICATION=true y --publish. La base de derivados debe estar
separada y el contrato debe ser compatible. Un snapshot vacío se rechaza para no
borrar el último conocido; un fallo de publicación conserva o limpia según el punto
alcanzado, y no se resuelve con delete_many sobre el destino.

El generador exige ALLOW_SYNTHETIC_WRITES=true más --apply, y su colección está
limitada a appointments_synthetic. No usarlo para rellenar métricas de producción
ni inventar actividad de clientes. No se configura cron automáticamente.

## Verificación

Distinguir respuesta de healthcheck, login/roles, lectura de datos, ejecución de
modelos, publicación de derivados y consumidores. Registrar qué se verificó y qué
quedó pendiente. Las salidas de análisis pueden contener información del negocio;
no adjuntarlas a issues o artefactos públicos sin depuración y autorización.

Las referencias académicas previas y evaluaciones no prueban calidad actual. No
cargar modelos persistidos de origen desconocido ni reutilizar su validación tras
cambiar features o dependencias sin evaluar compatibilidad.

## Recuperación

Si falla una versión, detener nuevas publicaciones y conservar evidencia privada.
La aplicación de una imagen anterior no revierte por sí sola datos publicados.
Revisar consumidores y snapshot antes de cualquier restauración. Nunca ejecutar
migrate:fresh, db:seed, reset, drop_database o limpieza de colecciones core como
parte de una reparación de Spark.

Los postmortems están en [docs/postmortems](postmortems/README.md). El canal privado
de incidentes se define en [SECURITY.md](../SECURITY.md). Una rotación de credenciales
es una intervención separada, con permisos y aprobación del propietario.

## Verificar contra Mongo y API locales de Barber

Este perfil requiere los servicios de desarrollo ya existentes: mongo-dev en
barber_internal y la API aislada ub-demo-api:8000. No usa el .env operativo ni
reinicia Barber. Comprobar primero la conexión efectiva de esa API: APP_ENV=local
por sí solo no demuestra que haya dejado de usar Atlas.

```powershell
Copy-Item config/local.env.example .env.local
$env:SPARK_ENV_FILE = ".env.local"
docker compose --env-file .env.local -f docker-compose.yml -f docker-compose.local.yml -p urbanblade-spark-local up -d --build dashboard
```

Abrir http://localhost:8501. El puerto solo escucha en loopback. El perfil local
fija core y derivados en mongo-dev, bases con nombres distintos y flags de escritura
false. La etiqueta del dashboard se obtiene de la conexión configurada; no presenta
Mongo local como Atlas. La cuenta debe existir en la API local con rol administrador
o ingeniero; no crear usuarios ni cambiar claves de producción para esta prueba.

No asumir que urbanblade_dev es una réplica completa: comprobar origen, fecha y
alcance de la copia antes de usar sus resultados como evidencia de producción.
Los datos de demostración permiten probar navegación, permisos e integración;
no validan la precisión de los modelos sobre el negocio real.

La cuenta local y sus credenciales se administran fuera de Git. No copiar sus
valores en issues, documentación, comandos compartidos o ejemplos. No ejecutar
seeders o restores para preparar esta verificación.
