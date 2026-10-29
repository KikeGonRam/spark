# Analítica · preparation

Módulos ejecutables bajo demanda; importar un módulo no conecta a Mongo ni entrena modelos.

| Módulo | Ejecución desde la raíz |
| --- | --- |
| [calidad_pagos](calidad_pagos.py) | `python -m analytics.preparation.calidad_pagos` |
| [datawarehouse](datawarehouse.py) | `python -m analytics.preparation.datawarehouse` |
| [etl](etl.py) | `python -m analytics.preparation.etl` |
| [fidelizacion_clientes](fidelizacion_clientes.py) | `python -m analytics.preparation.fidelizacion_clientes` |
| [inventario_productos](inventario_productos.py) | `python -m analytics.preparation.inventario_productos` |
| [limpieza_datos](limpieza_datos.py) | `python -m analytics.preparation.limpieza_datos` |
| [mapreduce_basico](mapreduce_basico.py) | `python -m analytics.preparation.mapreduce_basico` |
| [mapreduce_etl](mapreduce_etl.py) | `python -m analytics.preparation.mapreduce_etl` |
| [mineria_datos](mineria_datos.py) | `python -m analytics.preparation.mineria_datos` |
| [pedidos_tienda](pedidos_tienda.py) | `python -m analytics.preparation.pedidos_tienda` |
| [publicaciones_sociales](publicaciones_sociales.py) | `python -m analytics.preparation.publicaciones_sociales` |
| [tipos_fuentes_datos](tipos_fuentes_datos.py) | `python -m analytics.preparation.tipos_fuentes_datos` |
| [utilizacion_barberos](utilizacion_barberos.py) | `python -m analytics.preparation.utilizacion_barberos` |

Los análisis leen el core y pueden producir salidas locales con información del negocio.
No ejecutarlos en CI con credenciales reales ni publicar sus logs o artefactos.
Consultar [desarrollo](../../docs/desarrollo.md), [datos](../../docs/arquitectura.md) y [modelos](../../docs/modelos.md).
