---
name: urbanblade-data-architecture
description: Aplica la arquitectura y gobernanza de datos al cambiar conectores, lecturas, escrituras, exportaciones o contenedores del proyecto Spark de UrbanBlade.
---

# Arquitectura de datos de UrbanBlade

Lee `../barber/docs/ADR-001-ARQUITECTURA-DE-DATOS.md`. El ADR está **Propuesto** y no
autoriza migraciones ni cambios de infraestructura.

- Spark no es fuente de verdad operativa: lee la base core con credenciales de solo
  lectura.
- Su única escritura remota permitida son derivados reconstruibles en
  `urbanblade_analytics`, comenzando por `analytics_insights`, con credenciales distintas.
- No escribas ni borres `users`, `clients`, `barbers`, `services`, `appointments`,
  `payments`, inventario, pedidos o cualquier otra colección operativa.
- Prueba conectores y exportaciones primero con bases locales/sintéticas. No copies PII
  a artefactos o logs.
- Una migración requiere backup, conteos, verificación, corte reversible y conservación
  temporal del origen.
- Ninguna IA ejecuta `git commit`, `git push`, merge, rebase ni publica PR. Entrega al
  usuario el resumen, validaciones y mensaje de commit sugerido en español.
