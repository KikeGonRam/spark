# 04 — Gobernanza y limpieza: deuda técnica identificada

Como consecuencia directa del incidente, se auditó el repositorio `barber` buscando
**causas estructurales** que hicieran más probable un problema similar en el futuro:
seeders redundantes/legado que pueden confundirse entre sí, y documentación que ya no
describe el sistema real.

## Seeders — hallazgos

| Seeder | Veredicto | Motivo |
|---|---|---|
| `DemoDataSeeder.php` | **Eliminado** | Superado por `ProductionSeeder` + `HistoricalDataSeeder`, ya integrados en `DatabaseSeeder`. La documentación lo seguía recomendando como flujo principal — riesgo de que alguien lo ejecutara por error creyendo que era el camino correcto |
| `InventorySeeder.php` | **Eliminado** | Usaba categorías de producto (`cuidado`, `estilismo`, `herramienta`) que no coinciden con las reales en producción (`afeitar`, `coloración`, `pomadas y ceras`, etc.) |
| `TestUsersSeeder.php` | Conservado | Documentado a propósito, crea cuentas QA con credenciales fijas, sí llama `assignRole()` correctamente |
| `MassiveDataSeeder.php` | Conservado, pero **causa raíz de este incidente** | Es una herramienta legítima de pruebas de carga, pero no asigna roles y no valida que el dataset base sea el "real" antes de ejecutarse — puede aplicarse sobre un dataset ya corrupto sin advertirlo |
| `CommentSeeder.php` / `ReactionSeeder.php` | Sin decisión (pendiente) | No están en `DatabaseSeeder` ni documentados; funcionalidad de portafolio sin terminar de integrar |

**Lección aplicada a `PROJECT_DOCUMENTATION.md`:** se corrigió para que documente
explícitamente que `MassiveDataSeeder` **requiere haber corrido `migrate:fresh --seed`
primero** y **no asigna roles** — la ambigüedad anterior de la documentación fue un
factor que contribuyó al incidente.

## Documentación — hallazgos

Se identificaron **~70 archivos Markdown**, la mayoría (≈50) fechados en abril de 2026 —
2.5 meses antes de los cambios más recientes del proyecto (ampliación de Unidad II,
seeders de producción, dashboard de 15 pestañas). Se eliminaron **15 documentos**
sin valor de referencia continuo:

- 5 reportes de sprint con fecha explícita (`release-notes-2026-04-01.md`, etc.):
  snapshots de un punto en el tiempo, sin utilidad una vez superada la fecha.
- 10 reportes de "fase completada" / fixes puntuales (`PHASE3_*`, `PHASE4_*`,
  `CACHE_PATH_FIX.md`, `SETTINGS_PAGE_FIX.md`, etc.): describen cambios que ya están
  incorporados al código; mantenerlos como documentación activa genera confusión sobre
  qué es vigente.

**Lo que se decidió NO tocar:** la suite de tests (`tests/`, 55 archivos). Se verificó
su antigüedad real (el más viejo tiene 8 semanas, varios modificados el mismo día del
incidente) antes de aceptar la premisa de que eran "legado" — **no lo eran**. Esto
ilustra un principio de esta unidad: verificar con datos antes de actuar sobre una
suposición, incluso cuando la suposición viene del propio equipo del proyecto.

## Principio general aplicado

> Un sistema de datos no solo necesita estar "correcto" en un momento dado — necesita
> mecanismos que hagan **difícil volver a corromperlo por accidente**. La documentación
> desactualizada y los seeders ambiguos no causaron el incidente original, pero sí
> hicieron más probable que se repitiera y más lento diagnosticarlo.
