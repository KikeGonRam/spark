"""
Unidad II — Script 10: Utilización de barberos (oferta vs demanda)

Usa la colección real `barber_schedules` (175 documentos = 25 barberos × 7 días,
antes sin usar) para calcular cuántas HORAS DISPONIBLES tiene cada barbero según
su agenda oficial, y las compara contra las horas REALMENTE ocupadas (duración de
sus citas no canceladas) → tasa de utilización real.

`day_of_week` en Mongo usa convención Laravel (0=Domingo…6=Sábado); se convierte
a ISO (1=Lunes…7=Domingo) para cruzar con el resto del proyecto.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import (
    get_spark_session, get_horarios_df, get_utilizacion_barberos_df, DIAS_SEMANA
)

print("\n" + "=" * 60)
print("UTILIZACIÓN DE BARBEROS — Oferta (agenda) vs Demanda (citas)")
print("=" * 60)

spark, df, _ = get_spark_session()
pdf = df.toPandas()

horarios = get_horarios_df()
print(f"\nBarberos con horario configurado: {horarios['barbero'].nunique()}")
print(f"Horas disponibles promedio por semana por barbero: "
      f"{horarios.groupby('barbero')['horas_disponibles'].sum().mean():.1f} h")

util = get_utilizacion_barberos_df(pdf)
if util.empty:
    print("Sin datos de horarios para calcular utilización.")
    spark.stop()
    raise SystemExit

util["dia_nombre"] = util["dia_semana"].map(DIAS_SEMANA)

print("\nUtilización por barbero y día (muestra):")
print(util.sort_values("utilizacion_pct", ascending=False)
          [["barbero", "dia_nombre", "horas_disponibles_total", "horas_ocupadas", "utilizacion_pct"]]
          .head(15).to_string(index=False))

# ── Ranking global de barberos por utilización promedio ────────────────────────
print("\n" + "=" * 60)
print("RANKING DE UTILIZACIÓN POR BARBERO (promedio semanal)")
print("=" * 60)
ranking = (util.groupby("barbero")
               .agg(utilizacion_prom=("utilizacion_pct", "mean"),
                    horas_disp_sem=("horas_disponibles_total", "sum"),
                    horas_ocup_sem=("horas_ocupadas", "sum"))
               .round(1).sort_values("utilizacion_prom", ascending=False))
print(ranking.to_string())

sobrecargados = ranking[ranking["utilizacion_prom"] > 80]
subutilizados = ranking[ranking["utilizacion_prom"] < 30]

print("\nINTERPRETACIÓN:")
print(f"  Utilización promedio del equipo: {ranking['utilizacion_prom'].mean():.1f}%")
if len(sobrecargados):
    print(f"  {len(sobrecargados)} barbero(s) con utilización > 80% (riesgo de saturación):")
    for b in sobrecargados.index:
        print(f"    - {b}: {sobrecargados.loc[b,'utilizacion_prom']:.1f}%")
if len(subutilizados):
    print(f"  {len(subutilizados)} barbero(s) con utilización < 30% (capacidad ociosa):")
    for b in subutilizados.index:
        print(f"    - {b}: {subutilizados.loc[b,'utilizacion_prom']:.1f}%")
print("  Acción: redistribuir citas de los días/barberos saturados hacia los de baja")
print("  utilización, o ajustar el horario de agenda según la demanda real (ver Unidad III,")
print("  script de predicción de demanda).")

spark.stop()
print("\nAnálisis de utilización de barberos completado.")
