# Modelos y evaluación

El repositorio conserva algoritmos supervisados y no supervisados como componentes
analíticos ejecutables. La modernización de estructura no convierte sus resultados
históricos en modelos aprobados para producción ni garantiza precisión nueva.

| Área | Implementación | Objetivo |
| --- | --- | --- |
| Supervisados | [Módulos](../analytics/supervised/README.md) | Facturación diaria, cancelación, abandono y demanda. |
| Patrones | [Módulos](../analytics/unsupervised/README.md) | Agrupación, PCA, segmentos y asociación de servicios. |
| Negocio | [Dashboard](../dashboard/README.md) | Indicadores, cohortes, CLV simplificado, proyección y anomalías. |

## Contratos y honestidad de métricas

Las features de cancelación excluyen ingreso/estado para evitar fuga directa de
la etiqueta. La regresión de negocio agrega por día; predecir un precio usando el
mismo precio como entrada no sería una evaluación útil.

FEATURES_BASE y el vector original se conservan por compatibilidad; precio e ingreso
pueden ser redundantes en ese vector. No interpretar su resultado como un modelo
revalidado ni compararlo sin controlar selección y escala de features. La migración
metodológica requiere evaluación propia y revisión del consumidor.

Antes de promover un modelo, registrar como mínimo:

- Fuente, ventana temporal, exclusiones, consentimiento y calidad del conjunto.
- Target, features, tratamiento de nulos y posibles fugas de datos.
- Separación de entrenamiento/validación adecuada al uso, incluida validación temporal
  cuando se pronostica; tamaño de muestra y clases disponibles.
- Baseline, métricas apropiadas, incertidumbre y límites de interpretación.
- Versión de código/dependencias, artefacto privado y procedimiento de recuperación.

Las métricas de los documentos heredados no se usan como criterio de aceptación del
runtime nuevo. Las pruebas sintéticas comprueban contratos técnicos, no valor
predictivo sobre datos reales. Un indicador de ajuste bajo no se oculta o infla.

## Alcance vigente

No se añade captación de eventos de navegación ni un funnel nuevo: faltan contrato,
privacidad y datos definidos. No se generan datos sintéticos para aparentar precisión.
Los modelos opcionales de PyTorch/TensorFlow requieren su entorno de entrenamiento;
el dashboard no los necesita para arrancar.

Referencias históricas: [supervisados](reference/supervised) y
[no supervisados](reference/unsupervised). Revisar [operación](operacion.md) antes
de exportar resultados o usar un artefacto persistido.

## Contratos de indicadores

Las pruebas sintéticas verifican clientes únicos por cohorte, exclusión de ingresos
de citas canceladas y ausencia de proyección cuando falta historial. Una tendencia
decreciente no puede producir ingresos o citas negativos: estimación y límites se
recortan a cero, manteniendo mínimo <= estimación <= máximo.

La banda de la tendencia lineal es una heurística basada en residuos históricos;
no representa una cobertura predictiva del 95 % demostrada ni incorpora todas las
fuentes de incertidumbre. No usarla como compromiso de ingresos o demanda futura.
