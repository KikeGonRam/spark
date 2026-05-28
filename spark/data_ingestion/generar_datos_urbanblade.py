import random
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

database        = os.getenv("MONGO_DB",         "barberpro")
collection_name = os.getenv("MONGO_COLLECTION", "appointments")

# Soportar URI directa O variables separadas Atlas
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    user     = os.getenv("MONGO_USER")
    password = quote_plus(os.getenv("MONGO_PASSWORD", ""))
    cluster  = os.getenv("MONGO_CLUSTER")
    if not all([user, cluster]):
        raise ValueError("Configura MONGO_URI o MONGO_USER/MONGO_PASSWORD/MONGO_CLUSTER en .env")
    mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"

client = MongoClient(mongo_uri)

try:
    client.admin.command("ping")
    print("Conexión exitosa a MongoDB")
except Exception as e:
    raise ConnectionError(f"Error al conectar con MongoDB: {e}")

db        = client[database]
coleccion = db[collection_name]

servicios = ["Corte Clásico", "Corte Fade", "Barba", "Corte + Barba", "Tintura"]
barberos  = ["Carlos", "Miguel", "Andrés", "Javier"]
estados   = ["completada", "cancelada", "pendiente"]

precios_base = {
    "Corte Clásico": 150,
    "Corte Fade":    200,
    "Barba":         100,
    "Corte + Barba": 250,
    "Tintura":       400
}

citas = []
for _ in range(2000):
    servicio = random.choice(servicios)
    precio   = precios_base[servicio] + random.randint(-20, 50)
    cantidad = random.randint(1, 3)
    cita = {
        "servicio": servicio,
        "barbero":  random.choice(barberos),
        "cantidad": cantidad,
        "precio":   precio,
        "estado":   random.choices(estados, weights=[70, 20, 10])[0]
    }
    citas.append(cita)

resultado = coleccion.insert_many(citas)

coleccion.create_index("servicio")
coleccion.create_index("barbero")
coleccion.create_index("precio")

print(f"{len(resultado.inserted_ids)} citas de UrbanBlade insertadas en '{database}.{collection_name}'")
