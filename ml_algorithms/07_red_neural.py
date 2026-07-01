"""
Unidad III / IV – Análisis Supervisado + No Supervisado
Script  : 07_red_neural.py
Tema    : Red Neuronal PyTorch para clasificación de nivel de ingreso de citas
          Patrón: Spark preprocesa y escala → PyTorch entrena
Datos   : MongoDB Atlas → barber_db (appointments + services + barbers + users)
Alumno  : KikeGonRam (Luis Enrique González Ramírez)
Materia : Extracción del conocimiento en bases de datos – UTVT IDGS-84
Docente : MGTI. Héctor Velázquez Estrada
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mongo_spark_conexion_sinnulos import get_spark_session
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.sql.functions import when, col
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.model_selection import train_test_split

print("\n===  UNIDAD III/IV – RED NEURONAL PYTORCH – UrbanBlade  ===\n")

# ─── 1. Spark: cargar y preprocesar datos reales ──────────────────────────────
spark, df, _ = get_spark_session()

# Etiqueta de 3 clases según nivel de ingreso:
#   0 = Bajo   (ingreso <= $200 — cortes básicos)
#   1 = Medio  ($200 < ingreso <= $500 — servicios estándar)
#   2 = Alto   (ingreso > $500 — servicios premium)
df = df.withColumn(
    "label",
    when(col("ingreso") <= 200, 0)
    .when(col("ingreso") <= 500, 1)
    .otherwise(2)
)

print("Distribución de etiquetas (niveles de ingreso):")
df.groupBy("label").count().orderBy("label").show()
print("  label 0 = Bajo (<=200) | 1 = Medio (200-500) | 2 = Alto (>500)")

# ─── 2. Vectorización y escalado con Spark ────────────────────────────────────
assembler = VectorAssembler(
    inputCols=["duracion_min", "precio", "ingreso"],
    outputCol="features",
    handleInvalid="skip"
)
df_vector = assembler.transform(df)

scaler       = StandardScaler(inputCol="features", outputCol="scaledFeatures",
                              withMean=True, withStd=True)
scaler_model = scaler.fit(df_vector)
df_scaled    = scaler_model.transform(df_vector)
print("Datos escalados con StandardScaler (withMean=True, withStd=True)")

# ─── 3. Convertir a Pandas / NumPy para PyTorch ───────────────────────────────
print("Convirtiendo Spark DataFrame a tensores PyTorch...")
pdf = df_scaled.select("scaledFeatures", "label").toPandas()
X   = np.array(pdf["scaledFeatures"].apply(lambda v: v.toArray()).tolist(), dtype=np.float32)
y   = pdf["label"].values.astype(np.int64)
spark.stop()
print(f"Total registros reales: {len(X)}\n")

# ─── 4. Train / Test split ────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.long)
X_test  = torch.tensor(X_test,  dtype=torch.float32)
y_test  = torch.tensor(y_test,  dtype=torch.long)
print(f"Entrenamiento: {len(X_train)} | Prueba: {len(X_test)}")

# ─── 5. Arquitectura de la Red Neuronal ───────────────────────────────────────
class RedNeuronalUrbanBlade(nn.Module):
    """
    Red neuronal para clasificar citas en 3 niveles de ingreso.
    Entrada: 3 features escalados (duracion_min, precio, ingreso)
    Salida : 3 clases (Bajo, Medio, Alto)
    """
    def __init__(self):
        super().__init__()
        self.red = nn.Sequential(
            nn.Linear(3, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 16), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(16, 8),  nn.ReLU(),
            nn.Linear(8, 3)
        )

    def forward(self, x):
        return self.red(x)


model     = RedNeuronalUrbanBlade()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.5)

print("\nArquitectura de la Red Neuronal:")
print(model)
total_params = sum(p.numel() for p in model.parameters())
print(f"Parametros totales: {total_params}\n")

# ─── 6. Entrenamiento ─────────────────────────────────────────────────────────
EPOCHS = 150
print(f"Entrenando por {EPOCHS} epocas...\n")

for epoch in range(EPOCHS):
    model.train()
    optimizer.zero_grad()
    outputs = model(X_train)
    loss    = criterion(outputs, y_train)
    loss.backward()
    optimizer.step()
    scheduler.step()

    if epoch % 15 == 0 or epoch == EPOCHS - 1:
        model.eval()
        with torch.no_grad():
            val_out        = model(X_test)
            val_loss       = criterion(val_out, y_test).item()
            _, val_pred    = torch.max(val_out, 1)
            val_acc        = (val_pred == y_test).float().mean().item()
        print(f"  Epoch {epoch:>3} | Train Loss: {loss.item():.4f} | "
              f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc*100:.1f}%")

# ─── 7. Evaluación final ──────────────────────────────────────────────────────
model.eval()
with torch.no_grad():
    outputs  = model(X_test)
    _, pred  = torch.max(outputs, 1)
    accuracy = (pred == y_test).float().mean().item()

labels_map = {0: "Bajo  (<=200)", 1: "Medio (200-500)", 2: "Alto  (>500)"}
print(f"\n{'='*52}")
print("EVALUACION FINAL – RED NEURONAL PYTORCH")
print(f"{'='*52}")
print(f"  Accuracy total: {accuracy*100:.2f}%")
for clase_id, clase_nombre in labels_map.items():
    mask = (y_test == clase_id)
    if mask.sum() > 0:
        acc_clase = (pred[mask] == y_test[mask]).float().mean().item()
        n         = mask.sum().item()
        print(f"  Clase {clase_id} - {clase_nombre}: {acc_clase*100:.1f}%  (n={n})")

# ─── 8. Predicción de nuevas citas ───────────────────────────────────────────
print("\nPREDICCION DE NUEVAS CITAS (valores estandarizados aprox.):")
nuevas_citas = [
    ("Corte Clasico  (30min, ~$200)", torch.tensor([[-0.8, -1.0, -1.0]])),
    ("Corte + Barba  (60min, ~$400)", torch.tensor([[ 0.2,  0.2,  0.2]])),
    ("Tinte Full     (90min, ~$800)", torch.tensor([[ 1.5,  1.8,  1.8]])),
]
with torch.no_grad():
    for desc, x_nuevo in nuevas_citas:
        prob  = torch.softmax(model(x_nuevo.float()), dim=1)
        clase = torch.argmax(prob).item()
        print(f"  {desc}")
        print(f"    -> Clase predicha: {labels_map[clase]}  "
              f"(prob={prob[0][clase].item()*100:.1f}%)")

print(f"\nCONCLUSION:")
print(f"  La red neuronal alcanzo {accuracy*100:.1f}% de precision clasificando")
print("  citas en 3 niveles de ingreso usando datos reales de UrbanBlade.")
print("  Spark normalizo los datos y PyTorch entrenó el modelo.")
