# Analítica · unsupervised

Módulos ejecutables bajo demanda; importar un módulo no conecta a Mongo ni entrena modelos.

| Módulo | Ejecución desde la raíz |
| --- | --- |
| [kmeans](kmeans.py) | `python -m analytics.unsupervised.kmeans` |
| [pca](pca.py) | `python -m analytics.unsupervised.pca` |
| [recomendacion_servicios](recomendacion_servicios.py) | `python -m analytics.unsupervised.recomendacion_servicios` |
| [segmentacion_clientes](segmentacion_clientes.py) | `python -m analytics.unsupervised.segmentacion_clientes` |

Los análisis leen el core y pueden producir salidas locales con información del negocio.
No ejecutarlos en CI con credenciales reales ni publicar sus logs o artefactos.
Consultar [desarrollo](../../docs/desarrollo.md), [datos](../../docs/arquitectura.md) y [modelos](../../docs/modelos.md).
