"""
Unidad II — Script 13: Engagement del muro de inspiración (publicaciones sociales)

Colecciones `works` / `work_images` / `comments` / `reactions` — antes
documentadas como vacías ("NO usar"); ya tienen contenido real y se agregan
al análisis por primera vez vía `get_publicaciones_df()`.

Correlaciona el engagement del portafolio de cada barbero (publicaciones,
fotos, comentarios, reacciones) contra su volumen de citas — para ver si
publicar más en el muro se asocia con más citas agendadas.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from pyspark.sql.functions import col, count as scount, round as sround
from config.mongo_spark_conexion_sinnulos import get_spark_session, get_publicaciones_df

print("\n" + "=" * 60)
print("ENGAGEMENT DEL MURO DE INSPIRACIÓN — UrbanBlade")
print("=" * 60)

spark, df, _ = get_spark_session()
publicaciones = get_publicaciones_df(spark)

if publicaciones is None:
    print("\nSin publicaciones registradas todavía — nada que analizar.")
    spark.stop()
    sys.exit(0)

total_barberos_con_posts = publicaciones.count()
print(f"\nBarberos con al menos una publicación: {total_barberos_con_posts}")

totales = publicaciones.agg(
    scount("*").alias("barberos"),
).first()
suma = publicaciones.groupBy().sum("publicaciones", "fotos", "comentarios", "reacciones").first()
print(f"Publicaciones totales: {suma['sum(publicaciones)']}")
print(f"Fotos totales: {suma['sum(fotos)']}")
print(f"Comentarios totales: {suma['sum(comentarios)']}")
print(f"Reacciones totales: {suma['sum(reacciones)']}")

# ── Ranking de engagement ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TOP 10 BARBEROS POR ENGAGEMENT (comentarios + reacciones por publicación)")
print("=" * 60)
publicaciones.orderBy(col("engagement_por_post").desc()).show(10, truncate=False)

# ── Correlación engagement vs volumen de citas ──────────────────────────────────
print("\n" + "=" * 60)
print("ENGAGEMENT vs VOLUMEN DE CITAS")
print("=" * 60)
citas_por_barbero = (df.filter(col("estado") == "completada")
                     .groupBy("barbero").agg(scount("*").alias("citas_completadas")))

cruce = (publicaciones.join(citas_por_barbero, on="barbero", how="left")
         .fillna(0, subset=["citas_completadas"]))
cruce_pdf = cruce.select("barbero", "publicaciones", "reacciones", "engagement_por_post",
                          "citas_completadas").toPandas()

if len(cruce_pdf) >= 3:
    correlacion = cruce_pdf[["engagement_por_post", "citas_completadas"]].corr().iloc[0, 1]
    print(f"Correlación (engagement_por_post vs citas_completadas): {correlacion:.3f}")
else:
    correlacion = None
    print("Muestra insuficiente para calcular correlación de forma confiable.")

# ── Interpretación ──────────────────────────────────────────────────────────────
print("\nINTERPRETACIÓN:")
if correlacion is not None:
    if correlacion > 0.3:
        print(f"  Correlación positiva ({correlacion:.2f}): los barberos con más engagement en")
        print("  el muro tienden a tener más citas completadas — el portafolio social funciona")
        print("  como canal de adquisición, vale la pena incentivar publicar seguido.")
    elif correlacion < -0.1:
        print(f"  Correlación negativa ({correlacion:.2f}): revisar si publicar mucho le resta")
        print("  tiempo a la agenda, o si el engagement viene de clientes que ya son recurrentes")
        print("  (no capta clientes nuevos).")
    else:
        print(f"  Correlación débil ({correlacion:.2f}): el engagement social y el volumen de")
        print("  citas no están claramente relacionados con los datos actuales — falta madurez")
        print("  del canal o el muro sirve más para fidelización que para captación.")

top_row = cruce_pdf.sort_values("engagement_por_post", ascending=False).iloc[0] if len(cruce_pdf) else None
if top_row is not None:
    print(f"  Barbero con mejor engagement: '{top_row['barbero']}' "
          f"({top_row['engagement_por_post']:.1f} interacciones/post, "
          f"{int(top_row['citas_completadas'])} citas completadas).")

n_sin_posts = df.select("barbero").distinct().count() - total_barberos_con_posts
if n_sin_posts > 0:
    print(f"  {n_sin_posts} barbero(s) sin ninguna publicación — oportunidad de onboarding")
    print("  para que suban su primer trabajo al muro.")

spark.stop()
print("\nAnálisis de engagement social completado.")
