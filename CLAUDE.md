# UrbanBlade Spark — Data mining coursework

School project for "Extracción del conocimiento en bases de datos" (UTVT, IDGS-93,
Prof. Héctor Velázquez Estrada, May–Aug 2026). Applies the course's 5 units of
data analysis to real UrbanBlade barbershop data (`barber_db`: 12,535 appointments,
1,000 clients, 25 barbers, 20 services). Not production software — academic
deliverables organized per unit, following the professor's exact patterns
(e.g. `get_spark_session()`).

This folder is one of several independent repos gathered under the `UrbanBlade/`
parent folder (see `../CLONAR_PROYECTOS.md`). It is a standalone Python module
that reads from the same MongoDB Atlas database (`barber_db`) used by the
Laravel app in `../barber/`, but does not depend on it.

Repo: `https://github.com/KikeGonRam/spark.git`, working branch `urbanblade-analytics`.

## Stack

- Python 3.11 (Miniconda env `spark_env`), run inside WSL Ubuntu 24.04
- PySpark 3.5.1, MongoDB via pymongo 4.7.2, python-dotenv
- pandas, numpy, scipy, scikit-learn, statsmodels
- ML: PyTorch 2.3.0, TensorFlow 2.16.1, XGBoost, LightGBM
- Visualization: matplotlib, seaborn, plotly; dashboards via Streamlit

## Structure

```
config/                 shared data-access layer
  mongo_spark_conexion_sinnulos.py   connection + JOIN + features (use this one)
  mongo_spark_conexion.py            legacy base connection
data_ingestion/          synthetic/seed data generation
data/etl_output/          ETL output (Parquet/CSV), gitignored
unidades/                 one folder per course unit, each with its own README
  unidad_1_introduccion    intro / comparative docs
  unidad_2_preparacion     ETL, data warehouse, cleaning (7 scripts)
  unidad_3_supervisado     regression, classification (6 scripts)
  unidad_4_no_supervisado  KMeans, PCA, FP-Growth (4 scripts)
  unidad_5_visualizacion   executive dashboard, Matplotlib
  unidad_6_caso_aplicado_laravel
```

Scripts locate the project root automatically (they search for `config/`), so
they can be run from any working directory.

## Run / setup

```powershell
.\setup-spark.ps1     # validates WSL2, Java, Miniconda, spark_env
cp .env.example .env   # fill MONGO_USER, MONGO_PASSWORD, MONGO_CLUSTER, MONGO_DB
```
Dependencies: `pip install -r requirements.txt` inside the `spark_env` conda env.
Dashboards: `streamlit run <script>` from the relevant `unidad_5_visualizacion` script.

See `unidades/README.md` for the per-unit deliverable checklist and
`unidades/COMANDOS.txt` for exact commands.

## Conventions

- Never commit `.env` (MongoDB Atlas credentials) — use `.env.example` as template.
- All new data-access code should go through `config/mongo_spark_conexion_sinnulos.py`,
  not the legacy connector.

## Guardrails (read before writing to MongoDB or touching Laravel-side flows)

- **`barber_db` on Atlas is shared with `../barber/` (production-style Laravel app).**
  This project should only ever write to the `analytics_insights` collection (via
  `unidades/unidad_5_visualizacion/exportar_insights_dashboard.py`). Every other script
  reads `appointments`, `payments`, `customers`, `barbers`, `services` — never writes to
  them. Confirm before adding any `.write()`/`insert_many()`/`update_many()`/
  `delete_many()` targeting anything else.
- **This has already gone wrong once.** See
  `unidades/unidad_6_caso_aplicado_laravel/01_diagnostico_incidente.md`: a Laravel/Docker
  "reset" wiped real users/barbers/clients in this same Atlas database with no
  recoverable backup. Never suggest or chain a `php artisan migrate:fresh`, `db:seed`, or
  "reset the database" step as part of a `spark/` task.
- Full detail: see `.claude/skills/urbanblade-guardrails/SKILL.md` in this repo.
