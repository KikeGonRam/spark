# Desarrollo y pruebas

## Entornos

Runtime verificado objetivo: Python 3.12, Java 17 y PySpark 3.5.9. Los manifiestos
separan dashboard, frameworks opcionales y herramientas de CI. Python 3.14 del host
no es el intérprete de este runtime; usar un entorno compatible o Docker.

| Archivo | Uso |
| --- | --- |
| requirements-ci.txt | pytest, cliente Mongo, autenticación y herramientas de calidad; sin Java/Spark. |
| requirements-dashboard.txt | Streamlit, Spark y dependencias de la aplicación. |
| requirements-ml.txt | Frameworks de modelado opcionales. |
| requirements.txt | Entorno completo de análisis y desarrollo. |

`setup-spark.ps1` valida el intérprete; solo crea .venv e instala con -Install.
No clona otra rama, instala WSL/Miniconda, aplica seeders o inicia servicios.
Se puede seleccionar -Profile ci, dashboard o full y -PythonExe explícito.

## Pruebas rápidas

Desde la raíz y un entorno virtual limpio, sin URI E2E heredadas:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-ci.txt
.venv/Scripts/python -B -m pytest tests/ -q
.venv/Scripts/python -m ruff check config analytics dashboard pipelines data_ingestion tests scripts
.venv/Scripts/python -m compileall -q config analytics dashboard pipelines data_ingestion tests
.venv/Scripts/python scripts/check_repository.py
```

La suite rápida usa mocks. La integración local y los casos de runtime se omiten
si no se configuró su entorno; informar omisiones, no presentarlas como pruebas ejecutadas.
Las guardas recorren las rutas nuevas y rechazan escritores fuera de la lista autorizada.

## Integración de Mongo

Usar exclusivamente un Mongo local desechable, sin volúmenes ni credenciales del
proyecto. Configurar ANALYTICS_E2E_URI con loopback y ANALYTICS_E2E_DB con un nombre
único terminado en _e2e. No usar Atlas aunque la base tenga ese sufijo.
La integración escribe solo en esa base local y la retira al finalizar.

El fixture opcional usa CORE_E2E_URI/DB y tiene los mismos límites. Sus operaciones
son destructivas dentro de la base de prueba; no ejecutar sobre un servidor con
datos ajenos ni reutilizar nombres de pruebas de otra sesión.

## Runtime y UI sintéticos

```powershell
docker build -t urbanblade-analytics-local .
docker run --rm --mount "type=bind,source=C:/ruta/al/checkout/tests,target=/app/tests,readonly" urbanblade-analytics-local python -B -m unittest discover -s tests/runtime -v
```

Los casos arrancan Spark local, normalizan esquemas vacíos/no vacíos y prueban la
pantalla inicial con AppTest sin datos reales. No equivalen a probar roles reales,
Google OAuth, datos completos ni rendimiento del servicio desplegado.

## Modelado y ejecución

```powershell
python -m analytics.preparation.etl
python -m analytics.supervised.regresion
python -m analytics.unsupervised.segmentacion_clientes
python -m pipelines.publicar_insights --help
python -m data_ingestion.generar_datos_urbanblade --count 10 --seed 42
```

Los análisis requieren variables autorizadas y pueden exportar datos locales. No
poner variables de la base real en CI. El generador es dry-run si falta --apply;
publicación está bloqueada sin --publish y la habilitación correspondiente.

## Dependencias y calidad

Las versiones directas se fijan; los manifiestos no son un lock completo con hashes
de todas las transitivas. Revisar pip check y auditoría de la resolución real. La
imagen de runtime no instala herramientas de entrenamiento o CI innecesarias.
Dependabot propone PR para pip, Actions e imágenes; no hay automerge. Los saltos
mayores de Spark, pandas y NumPy están reservados para una migración explícita.

CI escanea la historia de la rama con Gitleaks fijado por versión y checksum.
CI usa Actions fijadas por SHA, Mongo local e imagen oficial por digest. El job de
runtime construye y audita las dependencias instaladas, sin publicar una imagen.
La auditoría Python no cubre por sí sola JVM, sistema operativo, calidad de modelos
o la configuración efectiva de Atlas.

## Entrega

Preparar rama, diff, pruebas y evidencia. Commit/push/PR requieren la orden del
propietario para el cambio. No desplegar Spark por fusionar un PR. Ver
[contribución](../CONTRIBUTING.md) y [migración](migracion.md).
