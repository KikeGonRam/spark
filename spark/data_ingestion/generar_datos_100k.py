"""
Generador de 100,000 citas UrbanBlade con datos enriquecidos.
Schema extendido: fechas reales, propinas, ratings, clientes, duración.
"""
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

database        = os.getenv("MONGO_DB",         "urbanblade")
collection_name = os.getenv("MONGO_COLLECTION", "appointments")

mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD", ""))
    cluster  = os.getenv("MONGO_CLUSTER")
    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

client = MongoClient(mongo_uri)
client.admin.command("ping")
print("Conexión exitosa a MongoDB")

db        = client[database]
coleccion = db[collection_name]

# ─── Catálogos ──────────────────────────────────────────────
SERVICIOS = {
    "Corte Clásico":  {"precio_base": 150, "duracion": 30, "popularidad": 25},
    "Corte Fade":     {"precio_base": 200, "duracion": 45, "popularidad": 30},
    "Barba":          {"precio_base": 100, "duracion": 20, "popularidad": 20},
    "Corte + Barba":  {"precio_base": 250, "duracion": 60, "popularidad": 15},
    "Tintura":        {"precio_base": 400, "duracion": 90, "popularidad":  7},
    "Diseño":         {"precio_base": 180, "duracion": 35, "popularidad": 10},
    "Keratina":       {"precio_base": 500, "duracion":120, "popularidad":  5},
    "Afeitado":       {"precio_base":  80, "duracion": 15, "popularidad": 10},
}

BARBEROS = {
    "Carlos":  {"especialidad": "Fade",     "factor_precio": 1.10},
    "Miguel":  {"especialidad": "Barba",    "factor_precio": 1.00},
    "Andrés":  {"especialidad": "Clásico",  "factor_precio": 0.95},
    "Javier":  {"especialidad": "Tintura",  "factor_precio": 1.15},
    "Diego":   {"especialidad": "Diseño",   "factor_precio": 1.05},
    "Roberto": {"especialidad": "General",  "factor_precio": 0.90},
}

ESTADOS = ["completada", "cancelada", "pendiente", "no_asistio"]
PESOS   = [72, 12, 10, 6]

CLIENTES = [f"C{str(i).zfill(4)}" for i in range(1, 501)]  # 500 clientes

# ─── Generador de fechas (últimos 18 meses) ─────────────────
FECHA_FIN   = datetime(2026, 5, 27)
FECHA_INICIO = FECHA_FIN - timedelta(days=548)  # ~18 meses

def fecha_aleatoria():
    # Más citas en fines de semana y viernes
    delta = FECHA_FIN - FECHA_INICIO
    while True:
        d = FECHA_INICIO + timedelta(days=random.randint(0, delta.days))
        hora = random.randint(9, 19)
        # Viernes (4) y sábados (5) tienen el doble de probabilidad
        if d.weekday() in (4, 5) and random.random() < 0.6:
            break
        if d.weekday() not in (4, 5) and random.random() < 0.4:
            break
    minuto = random.choice([0, 15, 30, 45])
    return d.replace(hour=hora, minute=minuto, second=0, microsecond=0)

# ─── Construcción de registros ──────────────────────────────
nombres_servicios = list(SERVICIOS.keys())
pesos_popularidad = [SERVICIOS[s]["popularidad"] for s in nombres_servicios]

citas = []
TOTAL = 100_000

print(f"Generando {TOTAL:,} citas...")

for i in range(TOTAL):
    servicio_nombre = random.choices(nombres_servicios, weights=pesos_popularidad, k=1)[0]
    servicio        = SERVICIOS[servicio_nombre]
    barbero_nombre  = random.choice(list(BARBEROS.keys()))
    barbero         = BARBEROS[barbero_nombre]

    precio_base = servicio["precio_base"]
    # Variación de precio ±15% + factor del barbero
    precio = round(precio_base * barbero["factor_precio"] * random.uniform(0.85, 1.15))

    cantidad = random.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0]
    estado   = random.choices(ESTADOS, weights=PESOS, k=1)[0]

    # Propina: entre 5% y 20% del precio, solo en citas completadas
    propina = round(precio * random.uniform(0.05, 0.20)) if estado == "completada" else 0

    # Rating: solo en completadas (mayoría 4-5)
    if estado == "completada":
        rating = random.choices([1, 2, 3, 4, 5], weights=[1, 2, 10, 35, 52], k=1)[0]
    else:
        rating = None

    fecha = fecha_aleatoria()

    cita = {
        "servicio":       servicio_nombre,
        "barbero":        barbero_nombre,
        "cliente_id":     random.choice(CLIENTES),
        "cantidad":       cantidad,
        "precio":         precio,
        "propina":        propina,
        "duracion_min":   servicio["duracion"] + random.randint(-5, 10),
        "rating":         rating,
        "estado":         estado,
        "fecha":          fecha,
        "mes":            fecha.month,
        "anio":           fecha.year,
        "dia_semana":     fecha.weekday(),   # 0=lunes, 6=domingo
        "hora":           fecha.hour,
    }
    citas.append(cita)

    if (i + 1) % 10_000 == 0:
        print(f"  {i + 1:,} / {TOTAL:,} generadas...")

# ─── Inserción en lotes de 5000 ─────────────────────────────
print("Insertando en MongoDB...")
lote = 5_000
insertados = 0
for inicio in range(0, TOTAL, lote):
    coleccion.insert_many(citas[inicio:inicio + lote])
    insertados += lote
    print(f"  Insertados: {min(insertados, TOTAL):,}")

# ─── Índices para búsquedas rápidas ─────────────────────────
coleccion.create_index("servicio")
coleccion.create_index("barbero")
coleccion.create_index("fecha")
coleccion.create_index("estado")
coleccion.create_index("cliente_id")
coleccion.create_index([("fecha", -1)])

print(f"\n{TOTAL:,} citas insertadas en '{database}.{collection_name}'")
print("Índices creados correctamente")
