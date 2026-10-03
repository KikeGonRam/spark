import random
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Credenciales de ANALYTICS, no las del core. El usuario de MONGO_USER es el de
# lectura de barber_db: usarlo para escribir convertiría un generador de datos
# sintéticos en una vía de escritura sobre la base real de la app, que es
# justamente el incidente que este repositorio ya sufrió (ver
# unidades/unidad_6_caso_aplicado_laravel/01_diagnostico_incidente.md).
user         = os.getenv("ANALYTICS_MONGO_USER")
password_raw = os.getenv("ANALYTICS_MONGO_PASSWORD")
cluster      = os.getenv("ANALYTICS_MONGO_CLUSTER")
database     = os.getenv("ANALYTICS_MONGO_DB")
# Always use the dedicated synthetic collection — never touch the production 'appointments'
coll         = os.getenv("MONGO_COLLECTION_SYNTHETIC", "appointments_synthetic")

faltantes = [
    nombre for nombre, valor in {
        "ANALYTICS_MONGO_USER": user,
        "ANALYTICS_MONGO_PASSWORD": password_raw,
        "ANALYTICS_MONGO_CLUSTER": cluster,
        "ANALYTICS_MONGO_DB": database,
    }.items() if not valor
]
if faltantes:
    raise ValueError(
        "Faltan variables en el archivo .env: " + ", ".join(faltantes) + ". "
        "El generador escribe con la conexion de ANALYTICS; no uses MONGO_USER."
    )

# Segunda barrera, independiente de las credenciales: aunque alguien apunte
# ANALYTICS_MONGO_DB a barber_db por error, el script se niega a escribir.
core_database = os.getenv("MONGO_DB")
if database == core_database:
    raise RuntimeError(
        "ANALYTICS_MONGO_DB no puede ser la base del core (MONGO_DB): este script "
        "solo escribe datos sinteticos en la base de derivados analiticos."
    )

mongo_uri = f"mongodb+srv://{user}:{quote_plus(password_raw)}@{cluster}"
client    = MongoClient(mongo_uri)

try:
    client.admin.command("ping")
    print("Conexión exitosa a MongoDB Atlas")
except Exception as e:
    raise ConnectionError(f"Error al conectar con MongoDB: {e}")

db        = client[database]
coleccion = db[coll]

servicios = ["Corte Clásico", "Corte Fade", "Barba", "Corte + Barba", "Tintura"]
barberos  = ["Carlos", "Miguel", "Andrés", "Javier"]
estados   = ["completada", "cancelada", "pendiente"]

precio_base = {
    "Corte Clásico": 150,
    "Corte Fade":    200,
    "Barba":         100,
    "Corte + Barba": 250,
    "Tintura":       400
}

citas = []
for _ in range(2000):
    servicio = random.choice(servicios)
    cita = {
        "servicio": servicio,
        "barbero":  random.choice(barberos),
        "cantidad": random.randint(1, 3),
        "precio":   precio_base[servicio] + random.randint(-20, 50),
        "estado":   random.choices(estados, weights=[70, 20, 10])[0]
    }
    citas.append(cita)

resultado = coleccion.insert_many(citas)

coleccion.create_index("servicio")
coleccion.create_index("barbero")
coleccion.create_index("precio")

print(f"{len(resultado.inserted_ids)} citas insertadas correctamente en '{coll}'")
client.close()
