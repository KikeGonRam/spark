---
name: urbanblade-guardrails
description: >
  Safety rules for the UrbanBlade "spark" PySpark/analytics repo — consult BEFORE writing
  any `.write()`, `.save()`, `insert_many()`, `update_many()`, or `delete_many()` call
  that targets MongoDB in this repo, before scheduling or running
  `exportar_insights_dashboard.py`, and before suggesting any Laravel-side seeder,
  migration, or database reset (even though those live in the sibling `barber/` repo).
  This project reads from the SAME MongoDB Atlas database (`barber_db`) used by the
  production-style `barber/` Laravel app, and there is a real, documented incident in
  this repo's own files of that shared database being wiped by a careless reset. Treat
  every collection except `analytics_insights` as strictly read-only from here.
---

# UrbanBlade `spark` — guardrails

`CLAUDE.md`/`README.md`/`SKILL.md` (the course-reference one) already cover stack and
structure. This skill covers the cross-repo risk that isn't obvious from this repo alone.

## 1. `barber_db` on Atlas is shared — almost everything here is read-only

This repo connects to the exact same Atlas database (`barber_db`) as the `barber/`
Laravel app (see `.env.example`, `config/mongo_spark_conexion_sinnulos.py`). By design,
**the only collection this project should ever write to is `analytics_insights`**
(cleared and repopulated by `unidades/unidad_5_visualizacion/exportar_insights_dashboard.py`,
which Laravel then reads to render insights). Every other script in `unidades/` reads
`appointments`, `payments`, `customers`/`clients`, `barbers`, `services`, etc. — never
writes to them.

Before adding or approving any `.write()`, `.save()`, `insert_many()`, `update_many()`,
or `delete_many()` call: confirm the target collection is `analytics_insights` (or a
local file / synthetic-data collection like `appointments_synthetic`, configured via
`MONGO_COLLECTION_SYNTHETIC`). If it targets `appointments`, `payments`, `customers`,
`clients`, or `barbers` directly, stop and confirm with the user — that would be a
first for this codebase and is very likely a mistake.

## 2. This has already gone wrong once — read the postmortem before touching cross-repo flows

`unidades/unidad_6_caso_aplicado_laravel/01_diagnostico_incidente.md` documents a real
incident: a "full reset" of the Laravel/Docker environment (likely `migrate:fresh` or a
manual Atlas Data Explorer wipe) reduced `users` from 1027→27, `barbers` 25→3, `clients`
1000→21 in the shared Atlas database, with **no recoverable backup** (only incompatible
MySQL `.sql` dumps existed). A subsequent seeder then inflated `appointments` to 100,000
synthetic records on top of that corrupted remainder. `04_gobernanza_y_limpieza.md` in
the same folder covers the follow-up governance gaps.

Implication for this repo specifically: even though `spark/` itself doesn't run
migrations or seeders, an AI session working here may also have access to `../barber/`.
Never suggest or chain a `php artisan migrate:fresh`, `db:seed`, or "reset the database"
step as part of a `spark/` analytics task — that's exactly the failure mode that already
happened.

## 3. `exportar_insights_dashboard.py` may run outside this session

Its own docstring says it's meant to run as a scheduled task (e.g. daily via WSL cron),
not on every page load. There's no cron actually configured in the repo today, but don't
assume it only runs when you invoke it — if editing it, keep it safe to run unattended
(it already scopes its writes to `analytics_insights` only; keep that invariant).

## 4. Use the current connector, not the legacy one

New data-access code should go through `config/mongo_spark_conexion_sinnulos.py`. Avoid
`config/mongo_spark_conexion.py` (legacy) for anything new — it's kept only for
reference/back-compat within the course material.

## 5. Secrets

`spark/.env` (gitignored) holds real Atlas credentials in plain text, as expected for a
local `.env`. Never read, print, or log its contents in a shared/AI session. Note
`.env.example` doesn't currently list every variable actually used in `.env`
(`MONGO_COLLECTION`, `MONGO_COLLECTION_SERVICES`, `MONGO_COLLECTION_BARBERS` are used but
undocumented there) — worth syncing at some point, but that's a documentation gap, not a
security issue.
