# UrbanBlade Analytics

Analítica operativa, modelos de negocio y dashboard ejecutivo de UrbanBlade.
Lee el core de MongoDB con una identidad de solo lectura, calcula indicadores
y publica derivados reconstruibles mediante un proceso explícito y separado.

El repositorio evoluciona como producto independiente. La organización por unidades
y los entregables académicos se retiraron de la entrada del proyecto; se conservan
los antecedentes técnicos y postmortems que siguen siendo útiles.

## Capacidades

- Indicadores de citas, ingresos, pagos, inventario, pedidos y utilización del equipo.
- Retención, CLV simplificado, demanda, anomalías y segmentación.
- Modelos supervisados y no supervisados ejecutables bajo demanda.
- Dashboard Streamlit con identidad de UrbanBlade y autenticación delegada a Barber.
- Publicación atómica de insights en una base de derivados, nunca en el core.

La disponibilidad de un modelo no demuestra calidad predictiva actual. Las métricas
históricas y modelos guardados necesitan evaluación antes de usarse para decisiones.

## Estructura

| Ruta | Responsabilidad |
| --- | --- |
| [config](config) | Conexiones, configuración validada, autenticación y publicación. |
| [analytics/preparation](analytics/preparation/README.md) | Calidad, preparación y ETL. |
| [analytics/supervised](analytics/supervised/README.md) | Regresión, clasificación, abandono y demanda. |
| [analytics/unsupervised](analytics/unsupervised/README.md) | Segmentación, PCA, clustering y recomendaciones. |
| [dashboard](dashboard/README.md) | Aplicación y paneles de detalle. |
| [pipelines](pipelines) | Publicación de derivados para consumidores de UrbanBlade. |
| [data_ingestion](data_ingestion) | Generación reproducible de datos sintéticos, sin escritura por defecto. |
| [tests](tests) | Contratos, protección del core, integración local y runtime sintético. |
| [docs](docs/README.md) | Arquitectura, desarrollo, operación, modelos y migración. |

## Inicio seguro

Python **3.12**, Java **17** y Spark **3.5.9** son la combinación de runtime elegida.
Para pruebas rápidas no se necesitan Spark, Java ni variables reales:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-ci.txt
.venv/Scripts/python -B -m pytest tests/ -q
```

Los casos de runtime se omiten si no están instaladas las dependencias del dashboard;
la integración se omite si no hay un Mongo local aislado configurado. La guía de
[desarrollo](docs/desarrollo.md) distingue cada nivel y sus requisitos.

## Configuración privada

Copiar [.env.example](.env.example) solo para crear un archivo nuevo; no sobrescribir
credenciales existentes. También se puede apuntar a un archivo privado existente:

```powershell
$env:URBANBLADE_ENV_FILE = 'C:/ruta/privada/spark/.env'
python -m config.diagnostics
```

Este diagnóstico valida configuración y separación de bases sin conectarse. Añadir
`--connect` solo para un ping y revisión de privilegios, sin consultar registros.
Nunca pegar URI, contraseñas o contenido de `.env` en issues, logs o PR.

## Ejecutar el dashboard

```powershell
.venv/Scripts/python -m pip install -r requirements-dashboard.txt
.venv/Scripts/streamlit run dashboard/app.py
```

O usar el Compose local descrito en [operación](docs/operacion.md). El puerto se
publica en `127.0.0.1:8501`; el servicio se conecta a la red externa de Barber ya
existente. No inicia ni migra el backend y no es un procedimiento de despliegue AWS.

Los roles administrador e ingeniero (presentado como Analista) se validan en Barber.
Spark no lee ni compara hashes de contraseñas del core.

## Datos y publicación

El core es solo lectura. Los únicos destinos de escritura son `analytics_insights`
y `appointments_synthetic`, dentro de la base de derivados y con credenciales
separadas. Ambas rutas están bloqueadas por defecto y requieren confirmación CLI.
Consultar [arquitectura](docs/arquitectura.md) y [operación](docs/operacion.md).

Las salidas ETL y modelos son artefactos privados, ignorados por Git. No se incluyen
datos reales en imágenes Docker ni fixtures; CI usa Mongo local desechable y datos
sintéticos. El build del dashboard no instala torch o TensorFlow.

## Calidad y colaboración

CI valida sintaxis, errores estáticos, contratos y publicación local; otro job
construye el runtime y prueba Spark/Streamlit con datos sintéticos. Las Actions e
imágenes base están fijadas y Dependabot propone actualizaciones por PR, sin automerge.
La auditoría Python no equivale a una certificación del sistema o de sus modelos.

[Mantenimiento](docs/gobierno.md) · [Cambios](CHANGELOG.md) ·
[Contribuir](CONTRIBUTING.md) · [Seguridad](SECURITY.md) ·
[Migración de rutas](docs/migracion.md) · [Licencia](LICENSING.md).

## Licencia

GNU GPLv3, versión 3 únicamente (**GPL-3.0-only**). Texto íntegro en [LICENSE](LICENSE).
Los datos reales, credenciales y componentes de terceros no cambian de titularidad
por distribuir el código. Versión de desarrollo: 0.1.0; no implica una publicación
ni actualización del servicio actualmente desplegado.
