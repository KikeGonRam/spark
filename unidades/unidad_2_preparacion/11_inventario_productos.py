"""
Unidad II — Script 11: Salud del inventario de productos

Usa la colección real `products` (31 documentos, antes sin usar) para analizar
stock, márgenes y categorías. Distingue insumos de trabajo (se consumen dando
el servicio) de productos de venta al cliente (retail).

Equipo  : Equipo UrbanBlade — UTVT IDGS-93
Materia : Extracción del conocimiento en bases de datos — MGTI. Héctor Velázquez Estrada
"""
import sys, os
_ROOT = os.path.abspath(__file__)
while _ROOT != os.path.dirname(_ROOT) and not os.path.isdir(os.path.join(_ROOT, "config")):
    _ROOT = os.path.dirname(_ROOT)
sys.path.insert(0, _ROOT)

from config.mongo_spark_conexion_sinnulos import get_productos_df

print("\n" + "=" * 60)
print("SALUD DEL INVENTARIO — UrbanBlade")
print("=" * 60)

productos = get_productos_df()
print(f"\nProductos registrados: {len(productos)}")

print("\nDistribución por tipo:")
print(productos["tipo"].value_counts().to_string())

print("\nDistribución por categoría:")
print(productos["categoria"].value_counts().to_string())

# ── Salud de stock ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ALERTAS DE REORDEN (stock_actual <= stock_minimo)")
print("=" * 60)
alertas = productos[productos["necesita_reorden"]]
if len(alertas):
    print(alertas[["producto", "categoria", "stock_actual", "stock_minimo"]].to_string(index=False))
else:
    print("Sin alertas: todo el inventario está por encima del stock mínimo.")

# ── Márgenes ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ANÁLISIS DE MÁRGENES (solo productos de venta al cliente)")
print("=" * 60)
venta = productos[productos["tipo"] == "venta"].sort_values("margen_pct", ascending=False)
print(venta[["producto", "precio_compra", "precio_venta", "margen", "margen_pct"]].to_string(index=False))

print(f"\nMargen promedio (venta al cliente): {venta['margen_pct'].mean():.1f}%")
print(f"Valor total del inventario (a precio de compra): "
      f"${(productos['precio_compra'] * productos['stock_actual']).sum():,.2f} MXN")
print(f"Valor total del inventario (a precio de venta):  "
      f"${(productos['precio_venta'] * productos['stock_actual']).sum():,.2f} MXN")

# ── Interpretación ──────────────────────────────────────────────────────────────
print("\nINTERPRETACIÓN:")
n_reorden = len(alertas)
if n_reorden == 0:
    print("  El inventario está saludable actualmente — sin urgencias de reabastecimiento.")
else:
    print(f"  {n_reorden} producto(s) requieren reorden inmediato.")
top_margen = venta.iloc[0] if len(venta) else None
if top_margen is not None:
    print(f"  Producto de mayor margen: '{top_margen['producto']}' ({top_margen['margen_pct']:.1f}%) "
          f"-> priorizar su promoción en mostrador/upsell post-cita.")
print("  Nota: no existe registro de consumo de insumos por cita (`inventory_movements` está vacía) ->")
print("  no se puede correlacionar directamente inventario con volumen de citas todavía;")
print("  se recomienda habilitar ese registro para planificación de compras basada en demanda.")

print("\nAnálisis de inventario completado.")
