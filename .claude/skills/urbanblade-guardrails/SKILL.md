---
name: urbanblade-guardrails
description: Límites de acceso a datos y ejecución segura de UrbanBlade Analytics.
---

# Seguridad de datos

Leer CLAUDE.md, docs/arquitectura.md, docs/operacion.md y SECURITY.md.
El core de Barber es compartido y estrictamente de solo lectura. No ejecutar
migraciones, seeders, resets, limpiezas o reparaciones desde una tarea de Spark.
El incidente documentado en docs/postmortems explica este límite.

Las escrituras derivadas requieren otra base y credenciales propias. El publicador
pipelines/publicar_insights.py solo permite analytics_insights y requiere --publish
más ALLOW_ANALYTICS_PUBLICATION=true. La generación sintética solo permite
appointments_synthetic, --apply y ALLOW_SYNTHETIC_WRITES=true. No ejecutar ninguno
contra datos reales sin una orden explícita para esa operación.

Usar config/settings.py y config/mongo_spark_conexion_sinnulos.py. No reutilizar
MONGODB_URI heredada como fallback privilegiado. No imprimir archivos .env,
credenciales, URI, documentos de usuarios ni excepciones de conexión completas.
La configuración privada puede referenciarse con URBANBLADE_ENV_FILE sin copiarla.

Las pruebas que escriben usan Mongo local y bases únicas terminadas en _e2e;
validate_local_test_target debe ejecutarse antes de conectar. Nunca Atlas.
El diagnóstico --connect solo permite ping y privilegios; no consulta registros.

Conservar el contrato de insights de Barber, incluido unidad, hasta una migración
coordinada. No asumir que no hay programadores externos. No desplegar ni publicar
por consecuencia de una actualización de documentación. Ver el flujo de Git de
.agents/skills/git-commit-conventions/SKILL.md.
