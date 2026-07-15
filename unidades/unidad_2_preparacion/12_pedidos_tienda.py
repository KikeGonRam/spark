"""
Unidad II — Script 12: Pedidos de tienda (colección `orders`)

Función nueva de la app: carrito/checkout de productos, con dos modalidades
    - 'cita'   → add-on comprado dentro de la reserva de una cita
    - 'tienda' → compra suelta hecha por el cliente en la tienda

Usa `get_pedidos_df()` (agregado por pedido) y `get_top_productos_df()`
(explode de `items`, agregado por producto) — ambos nuevos en la capa de
datos. Antes de esta actualización Spark no tenía ninguna visibilidad sobre
esta colección.

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from pyspark.sql.functions import col, sum as ssum, count, avg, round as sround
from config.mongo_spark_conexion_sinnulos import _build_spark, get_pedidos_df, get_top_productos_df

print("\n" + "=" * 60)
print("PEDIDOS DE TIENDA — UrbanBlade")
print("=" * 60)

spark = _build_spark()
pedidos = get_pedidos_df(spark)

if pedidos is None:
    print("\nSin pedidos registrados todavía — nada que analizar.")
    spark.stop()
    sys.exit(0)

total_pedidos = pedidos.count()
print(f"\nPedidos totales: {total_pedidos}")

# ── Distribución por tipo y estado ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("DISTRIBUCIÓN POR TIPO Y ESTADO")
print("=" * 60)
pedidos.groupBy("tipo", "estado").count().orderBy("tipo", "estado").show(truncate=False)

# ── Ingresos reales (solo entregados, evita contar pedidos cancelados/pendientes) ──
print("\n" + "=" * 60)
print("INGRESOS POR TIPO (solo entregados)")
print("=" * 60)
entregados = pedidos.filter(col("estado") == "entregado")
ingresos = entregados.groupBy("tipo").agg(
    count("*").alias("pedidos"),
    sround(ssum("total"), 2).alias("ingreso_total"),
    sround(avg("total"), 2).alias("ticket_promedio"),
)
ingresos.show(truncate=False)

total_entregado = entregados.agg(ssum("total")).first()[0] or 0.0
print(f"Ingreso total de tienda (servicio + producto entregado): ${total_entregado:,.2f} MXN")

# ── Attach-rate: qué tan seguido una cita se lleva un add-on de producto ─────────
print("\n" + "=" * 60)
print("ATTACH-RATE (add-ons de producto por cita completada)")
print("=" * 60)
citas_addon = pedidos.filter(col("tipo") == "cita").count()
print(f"Citas con add-on de producto: {citas_addon}")
print("(compara este numero contra el total de citas completadas de 06_estados.py")
print(" para calcular el % de attach-rate real — se deja como referencia cruzada)")

# ── Top productos vendidos ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TOP 10 PRODUCTOS MÁS VENDIDOS (por unidades, solo pedidos entregados)")
print("=" * 60)
top = get_top_productos_df()
if len(top):
    resumen = (top.groupby("producto")
               .agg(unidades=("cantidad", "sum"), ingreso=("subtotal", "sum"))
               .sort_values("unidades", ascending=False)
               .head(10))
    resumen["ingreso"] = resumen["ingreso"].round(2)
    print(resumen.to_string())
else:
    print("Sin líneas de producto en pedidos entregados.")

# ── Cancelaciones de pedidos de tienda ───────────────────────────────────────────
print("\n" + "=" * 60)
print("PEDIDOS CANCELADOS (solo tipo 'tienda' — los 'cita' no se cancelan aparte)")
print("=" * 60)
cancelados = pedidos.filter((col("tipo") == "tienda") & (col("estado") == "cancelado")).count()
tienda_total = pedidos.filter(col("tipo") == "tienda").count()
tasa_cancel = round(cancelados / tienda_total * 100, 1) if tienda_total else 0.0
print(f"Cancelados: {cancelados} de {tienda_total} pedidos de tienda ({tasa_cancel}%)")

# ── Interpretación ──────────────────────────────────────────────────────────────
print("\nINTERPRETACIÓN:")
fila_cita = ingresos.filter(col("tipo") == "cita").first()
fila_tienda = ingresos.filter(col("tipo") == "tienda").first()
if fila_cita and fila_tienda:
    pct_addon = round(fila_cita["ingreso_total"] / (fila_cita["ingreso_total"] + fila_tienda["ingreso_total"]) * 100, 1)
    print(f"  Los add-ons dentro de citas representan el {pct_addon}% del ingreso de tienda —")
    print("  el checkout durante la reserva convierte mejor que la tienda suelta del cliente.")
if len(top):
    producto_top = resumen.index[0]
    print(f"  Producto estrella: '{producto_top}' — candidato a destacarlo en el mostrador")
    print("  y en el paso de 'productos' del wizard de reserva de citas.")
if tasa_cancel > 15:
    print(f"  Tasa de cancelación de tienda ({tasa_cancel}%) es alta — revisar tiempos de entrega")
    print("  o disponibilidad de stock en el momento del pedido.")

spark.stop()
print("\nAnálisis de pedidos de tienda completado.")
