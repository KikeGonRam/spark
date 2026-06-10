import random
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path
import os
from urllib.parse import quote_plus

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

user     = os.getenv("MONGO_USER")
password = quote_plus(os.getenv("MONGO_PASSWORD"))
cluster  = os.getenv("MONGO_CLUSTER")
database = os.getenv("MONGO_DB")
coll     = os.getenv("MONGO_COLLECTION")

if not all([user, password, cluster, database, coll]):
    raise ValueError("Faltan variables en el archivo .env")

mongo_uri = f"mongodb+srv://{user}:{password}@{cluster}"
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
