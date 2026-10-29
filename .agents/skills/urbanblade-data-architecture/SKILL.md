---
name: urbanblade-data-architecture
description: Separación de datos operativos y derivados al mantener UrbanBlade Analytics.
---

# Arquitectura de datos

El ADR aceptado de referencia está en barber/docs/referencia/ADR-001-ARQUITECTURA-DE-DATOS.md
(repo hermano), no en la ruta antigua docs/ADR-001-ARQUITECTURA-DE-DATOS.md.
La guía propia del componente es docs/arquitectura.md.

- Core solo lectura; nunca publicar o generar datos en colecciones operativas.
- Derivados reconstruibles con base y credenciales separadas.
- Pruebas con mocks o Mongo local aislado terminado en _e2e; nunca fixtures sobre Atlas.
- No imprimir .env, URI, credenciales ni PII. Verificar privilegios sin consultar registros.
- Una migración o escritura real necesita autorización específica y recuperación revisada.
- Conservar trabajo ajeno y usar el flujo Git vigente; ninguna edición despliega servicios.
