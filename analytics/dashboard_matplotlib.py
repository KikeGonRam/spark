"""
Unidad V – Presentación y Visualización
Script  : analytics/dashboard_matplotlib.py
Tema    : Visualización de datos con MATPLOTLIB (sesión 17 del programa)
          6 gráficas personalizadas con interpretación de resultados
Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Alumno  : KikeGonRam (Luis Enrique González Ramírez)
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-84
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.sql.functions import sum as spark_sum, avg, count, col, when
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# ─── 1. Cargar datos reales desde MongoDB Atlas ───────────────────────────────
print("\n===  UNIDAD V – VISUALIZACIÓN CON MATPLOTLIB – UrbanBlade  ===\n")
spark, df, _ = get_spark_session()
print(f"Datos cargados: {df.count()} citas reales\n")

# ─── 2. Agregaciones para gráficas ───────────────────────────────────────────
# Ingreso y citas por servicio
resumen_servicio = df.groupBy("servicio").agg(
    spark_sum("ingreso").alias("ingreso_total"),
    avg("precio").alias("precio_promedio"),
    avg("duracion_min").alias("duracion_promedio"),
    count("*").alias("numero_citas")
).orderBy("ingreso_total", ascending=False).toPandas()

# Distribución de estados
estados = df.groupBy("estado").agg(
    count("*").alias("total")
).orderBy("total", ascending=False).toPandas()

# Ingresos por barbero (top 10)
por_barbero = df.groupBy("barbero").agg(
    spark_sum("ingreso").alias("ingreso_total"),
    count("*").alias("citas")
).orderBy("ingreso_total", ascending=False).limit(10).toPandas()

# Distribución de precios (histograma)
precios = df.select("precio").toPandas()

# Duración vs Ingreso (scatter)
scatter_data = df.select("duracion_min", "ingreso", "servicio").limit(500).toPandas()

# Ingresos diarios (distribución en cajas por servicio)
box_data = df.select("servicio", "ingreso").toPandas()

spark.stop()
print("Datos preparados — generando visualizaciones Matplotlib\n")

# ─── 3. Dashboard Matplotlib (2 filas × 3 columnas) ──────────────────────────
fig = plt.figure(figsize=(18, 12))
fig.suptitle("Dashboard UrbanBlade – Análisis de Citas y Servicios",
             fontsize=16, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

GOLD   = "#d4af37"
BLUE   = "steelblue"
GREEN  = "#2ecc71"
RED    = "#e74c3c"
PURPLE = "#9b59b6"

# ─── Gráfica 1: Ingreso total por servicio (barras horizontales) ──────────────
ax1 = fig.add_subplot(gs[0, 0])
colores = [GOLD if x == resumen_servicio["ingreso_total"].max() else BLUE
           for x in resumen_servicio["ingreso_total"]]
ax1.barh(resumen_servicio["servicio"], resumen_servicio["ingreso_total"],
         color=colores, edgecolor="white")
ax1.set_title("Ingreso Total por Servicio", fontweight="bold")
ax1.set_xlabel("Ingreso ($MXN)")
for i, v in enumerate(resumen_servicio["ingreso_total"]):
    ax1.text(v * 1.01, i, f"${v:,.0f}", va="center", fontsize=7)
ax1.tick_params(axis="y", labelsize=8)

# ─── Gráfica 2: Distribución de estados de citas (pie) ───────────────────────
ax2 = fig.add_subplot(gs[0, 1])
estado_colors = [GREEN, BLUE, GOLD, RED, PURPLE, "#e67e22"]
wedges, texts, autotexts = ax2.pie(
    estados["total"],
    labels=estados["estado"],
    colors=estado_colors[:len(estados)],
    autopct="%1.1f%%",
    startangle=90,
    textprops={"fontsize": 8}
)
ax2.set_title("Distribución de Estados de Citas", fontweight="bold")

# ─── Gráfica 3: Top 10 barberos por ingreso ───────────────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
bars = ax3.bar(range(len(por_barbero)), por_barbero["ingreso_total"],
               color=PURPLE, edgecolor="white")
ax3.set_xticks(range(len(por_barbero)))
ax3.set_xticklabels(por_barbero["barbero"], rotation=45, ha="right", fontsize=7)
ax3.set_title("Top 10 Barberos por Ingreso", fontweight="bold")
ax3.set_ylabel("Ingreso Total ($MXN)")
ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

# ─── Gráfica 4: Histograma de distribución de precios ────────────────────────
ax4 = fig.add_subplot(gs[1, 0])
ax4.hist(precios["precio"].dropna(), bins=25, color=GREEN, edgecolor="white", alpha=0.8)
mean_precio = precios["precio"].mean()
ax4.axvline(mean_precio, color=RED, linestyle="--", linewidth=2, label=f"Media: ${mean_precio:.0f}")
ax4.set_title("Distribución de Precios de Citas", fontweight="bold")
ax4.set_xlabel("Precio ($MXN)")
ax4.set_ylabel("Frecuencia")
ax4.legend(fontsize=8)

# ─── Gráfica 5: Duración del servicio vs Ingreso (scatter) ───────────────────
ax5 = fig.add_subplot(gs[1, 1])
servicios_uniq = scatter_data["servicio"].unique()
colores_svc    = plt.cm.tab10(np.linspace(0, 1, len(servicios_uniq)))
for svc, color in zip(servicios_uniq, colores_svc):
    subset = scatter_data[scatter_data["servicio"] == svc]
    ax5.scatter(subset["duracion_min"], subset["ingreso"],
                label=svc, alpha=0.6, s=20, color=color)
ax5.set_title("Duración vs Ingreso por Servicio", fontweight="bold")
ax5.set_xlabel("Duración (min)")
ax5.set_ylabel("Ingreso ($MXN)")
ax5.legend(fontsize=6, loc="upper left", ncol=2)

# ─── Gráfica 6: Precio promedio por servicio (barras con error) ───────────────
ax6 = fig.add_subplot(gs[1, 2])
servicios_ord = resumen_servicio["servicio"].tolist()
precios_prom  = resumen_servicio["precio_promedio"].tolist()
duraciones    = resumen_servicio["duracion_promedio"].tolist()
x_pos = np.arange(len(servicios_ord))
bars1 = ax6.bar(x_pos - 0.2, precios_prom, width=0.35, label="Precio Promedio ($)",
                color=GOLD, edgecolor="white")
ax6_2 = ax6.twinx()
bars2 = ax6_2.bar(x_pos + 0.2, duraciones, width=0.35, label="Duración (min)",
                  color=BLUE, alpha=0.7, edgecolor="white")
ax6.set_xticks(x_pos)
ax6.set_xticklabels(servicios_ord, rotation=45, ha="right", fontsize=7)
ax6.set_title("Precio Promedio y Duración por Servicio", fontweight="bold")
ax6.set_ylabel("Precio ($MXN)", color=GOLD)
ax6_2.set_ylabel("Duración (min)", color=BLUE)
lines1, labels1 = ax6.get_legend_handles_labels()
lines2, labels2 = ax6_2.get_legend_handles_labels()
ax6.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper right")

plt.savefig("dashboard_urbanblade_matplotlib.png", dpi=150, bbox_inches="tight")
print("Dashboard guardado como: dashboard_urbanblade_matplotlib.png")
plt.show()

# ─── 4. Interpretación de resultados ──────────────────────────────────────────
print("\n" + "=" * 60)
print("INTERPRETACIÓN DE RESULTADOS – UNIDAD V")
print("=" * 60)

servicio_estrella = resumen_servicio.iloc[0]["servicio"]
ingreso_max       = resumen_servicio.iloc[0]["ingreso_total"]
estado_mas_comun  = estados.iloc[0]["estado"]
pct_estado_comun  = estados.iloc[0]["total"] / estados["total"].sum() * 100
barbero_top       = por_barbero.iloc[0]["barbero"]

print(f"\n  Gráfica 1 — Servicio Estrella: '{servicio_estrella}' (${ingreso_max:,.0f} ingreso total)")
print(f"  Gráfica 2 — Estado más frecuente: '{estado_mas_comun}' ({pct_estado_comun:.1f}% de citas)")
print(f"  Gráfica 3 — Barbero líder: '{barbero_top}'")
print(f"  Gráfica 4 — Precio promedio general: ${precios['precio'].mean():.0f} MXN")
print(f"  Gráfica 5 — Mayor dispersión en servicios de larga duración → mayor variabilidad de ingreso")
print(f"  Gráfica 6 — Correlación positiva entre duración del servicio y precio cobrado")
print("\nConclusión: Las visualizaciones con Matplotlib permiten identificar los servicios")
print("de mayor rentabilidad, el comportamiento de precios y el desempeño por barbero,")
print("facilitando la toma de decisiones estratégicas en UrbanBlade.")
