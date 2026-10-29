# Analítica · supervised

Módulos ejecutables bajo demanda; importar un módulo no conecta a Mongo ni entrena modelos.

| Módulo | Ejecución desde la raíz |
| --- | --- |
| [arbol_decision](arbol_decision.py) | `python -m analytics.supervised.arbol_decision` |
| [bosque_aleatorio](bosque_aleatorio.py) | `python -m analytics.supervised.bosque_aleatorio` |
| [prediccion_abandono](prediccion_abandono.py) | `python -m analytics.supervised.prediccion_abandono` |
| [prediccion_demanda](prediccion_demanda.py) | `python -m analytics.supervised.prediccion_demanda` |
| [red_neuronal](red_neuronal.py) | `python -m analytics.supervised.red_neuronal` |
| [regresion](regresion.py) | `python -m analytics.supervised.regresion` |

Los análisis leen el core y pueden producir salidas locales con información del negocio.
No ejecutarlos en CI con credenciales reales ni publicar sus logs o artefactos.
Consultar [desarrollo](../../docs/desarrollo.md), [datos](../../docs/arquitectura.md) y [modelos](../../docs/modelos.md).
