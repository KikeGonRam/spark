---
name: spark-advanced-analytics-plan
description: Plan por fases para llevar el dashboard de negocio de spark (main_dashboard.py) a nivel de analitica avanzada real, inspirado en patrones de Stripe/Shopify/Amplitude/Mixpanel (cohortes de retencion, CLV, comparacion de periodos, forecasting, deteccion de anomalias, diseño). Consultar ANTES de tocar main_dashboard.py o mongo_spark_conexion_sinnulos.py para cualquiera de estas features, y seguir el orden de fases sin saltarse pasos.
---

# Analitica avanzada del dashboard de UrbanBlade (spark)

Origen: pedido explicito del usuario tras revisar que tecnicas usan dashboards de
negocio reales (Stripe, Shopify, Amplitude, Mixpanel, GA4, BI empresarial) y decidir
cuales aplicar aqui. No es trabajo escolar — el dashboard ya se trata como producto de
negocio real (ver identidad UrbanBlade, control de acceso, despliegue en Docker ya
implementados).

## Flujo de trabajo (repetir por cada fase, sin excepciones)

1. Implementar la fase completa (conector + UI + lo que haga falta).
2. Probar con datos reales: iniciar sesion (cuenta de prueba temporal si hace falta,
   borrarla despues — nunca dejar cuentas de prueba vivas), verificar en el navegador
   que la fase funciona con `barber_db` real, revisar que no rompio nada existente.
3. Si todo sale bien: marcar la fase como `✅ Completada` en este archivo (con fecha) y
   entregar al usuario resumen + archivos afectados + pruebas + mensaje de commit
   sugerido (ver `git-commit-conventions` — ninguna IA hace commit/push).
4. Si algo sale mal: NO marcarla como completada, arreglar primero, repetir el paso 2.
5. Solo entonces continuar con la fase siguiente. No adelantar trabajo de una fase
   futura mientras la actual no este marcada como completada.

## Antes de empezar cualquier fase

- Leer `urbanblade-data-architecture` (`.claude/skills/urbanblade-data-architecture/SKILL.md`):
  spark es de solo lectura contra las colecciones operativas de `barber_db`
  (appointments, clients, payments, etc.) — todo lo de este plan se calcula en memoria
  (pandas/pyspark) a partir de datos ya leidos, nunca escribe nada de vuelta a Mongo.
- Revisar `git status` en `spark` y `barber` antes de tocar nada (puede haber cambios
  de otras personas en curso — ya paso varias veces en este proyecto).

## Fases

### Fase 1 — Cohortes de retencion + CLV — ✅ Completada (2026-09-16)

**Cohortes de retencion**: agrupar clientes por mes de su primera cita (cohorte), y
para cada mes siguiente calcular que % de esa cohorte tuvo al menos otra cita. Es la
metrica que Mixpanel/Amplitude ponen primero — responde "¿los clientes que llegan se
quedan?", no solo "¿cuantos clientes tenemos?". Se calcula 100% en pandas a partir de
`pdf` (ya cargado), sin nuevas consultas a Mongo.

**CLV (Customer Lifetime Value) proyectado**: formula simplificada estandar de
e-commerce (la misma que usa el CLV basico de Shopify): `gasto_promedio ×
frecuencia_mensual × horizonte_meses` (horizonte default 12 meses). Se construye sobre
`get_clientes_df()` que ya existe (RFM) — no requiere datos nuevos.

Nueva pestaña: "Retención y CLV" (en los 4 grupos de secciones).

Funciones nuevas en `config/mongo_spark_conexion_sinnulos.py`:
- `get_cohortes_df(pdf)` — tabla de cohortes (pandas), a partir del `pdf` principal.
- `get_clv_df(spark, df)` — extiende `get_clientes_df()` con `clv_proyectado_12m`.

Probado con datos reales: heatmap de cohortes (mayo-agosto 2026, 20 clientes) y CLV
(promedio $6,705, cartera total $134,093) renderizando correctamente en el dashboard
desplegado en Docker. Bug encontrado y corregido en el camino: el eje Y del heatmap
mostraba las fechas garabateadas ("Aug 92026") porque plotly detectaba las etiquetas
"2026-06" como fechas y las reformateaba — se fuerza `type="category"` en el eje Y.

### Fase 2 — Comparacion de periodos + sparklines en todos los KPIs — ✅ Completada (2026-09-16)

Los 6 KPIs globales (Total Citas, Clientes Únicos, Ingreso Real, Ticket Promedio, Tasa
Cancelación, Barberos) ahora tienen delta vs mes anterior (antes solo 2 lo tenian), y
cada uno tiene una mini-grafica de tendencia (sparkline, ultimas 10 semanas con datos)
debajo — patron de Stripe. Tasa Cancelación usa `delta_color="inverse"` (subir es
malo) — verificado con JS que renderiza en rojo mientras los demas (mejoras reales)
renderizan en verde.

Funciones nuevas en `main_dashboard.py` (no en el conector — son puramente de
presentacion sobre `pdf` ya cargado, no consultan Mongo):
- `_serie_semanal(pdf)` — resample semanal de citas/ingreso/clientes/ticket/cancelacion/barberos.
- `_sparkline(serie, color)` — mini-grafica sin ejes, estilo Stripe.

No se agrego el selector "comparar contra mismo mes año anterior" (se descarto por
ahora: con ~3 meses de historial real no hay suficiente dato para una comparacion
interanual util todavia — revisar cuando haya mas historia).

### Fase 3 — Forecasting (proyeccion a futuro) — PENDIENTE

Hoy Regresion es descriptiva (explica el pasado). Agregar una proyeccion real hacia
adelante: ingreso/citas esperadas para las proximas 2-4 semanas, con banda de
incertidumbre. Requiere series de tiempo con suficiente historial — validar con datos
reales antes de prometer precision (con pocos meses de historia el intervalo de
confianza sera ancho, comunicarlo honestamente en vez de ocultarlo, mismo estandar de
"sin fuga de datos, metricas honestas" que ya sigue el resto del dashboard).

### Fase 4 — Deteccion de anomalias — PENDIENTE

Alertas automaticas tipo "esta semana el ingreso esta 30% por debajo de lo esperado"
en vez de que el dueño tenga que notar el patron el mismo. Empezar simple (desviacion
vs promedio movil + N desviaciones estandar) antes de algo mas sofisticado.

### Fase 5 — Diseño: menos donuts, "numero norte", anotaciones — PENDIENTE

- Reemplazar donuts con mas de 3-4 categorias por barras horizontales (mas facil de
  comparar) en las pestañas que aplique.
- Elegir una metrica "norte" (ingreso real, probablemente) y destacarla visualmente
  sobre las demas en el Resumen Ejecutivo, en vez de 6 KPIs del mismo tamaño.
- Anotaciones en graficas de tendencia cuando haya un evento conocido que explique un
  pico/caida (por ahora manual; automatizar si hace falta mas adelante).

### Fase 6 — Funnel de conversion — BLOQUEADA

Requiere datos que hoy no se capturan (visitas al catalogo antes de reservar). No
iniciar sin autorizacion explicita del usuario y sin definir primero de donde saldrian
esos datos (frontend-urban tendria que empezar a registrarlos).
