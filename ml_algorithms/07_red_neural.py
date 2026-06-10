from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.model_selection import train_test_split

spark = SparkSession.builder \
    .appName("UrbanBlade-RedNeuronal") \
    .getOrCreate()

# Dataset representativo: (duracion_min, precio, clase: 0=bajo, 1=medio, 2=alto)
# duracion_min: 20-60 min — precio: 100-650 MXN (rangos reales de barber_db)
data = [
    (20, 150, 0), (30, 300, 1), (20, 100, 0), (60, 450, 2),
    (30, 200, 1), (20, 400, 2), (60, 600, 2), (20, 120, 0),
    (45, 250, 1), (60, 650, 2), (20, 130, 0), (45, 280, 1),
    (60, 500, 2), (20, 160, 0), (30, 320, 1), (60, 480, 2),
    (20, 110, 0), (30, 220, 1), (60, 620, 2), (20, 140, 0)
]
columns = ["duracion_min", "precio", "label"]
df = spark.createDataFrame(data, columns)

assembler = VectorAssembler(inputCols=["duracion_min", "precio"], outputCol="features")
df_vector = assembler.transform(df)

scaler       = StandardScaler(inputCol="features", outputCol="scaledFeatures",
                              withMean=True, withStd=True)
scaler_model = scaler.fit(df_vector)
df_scaled    = scaler_model.transform(df_vector)

pdf = df_scaled.select("scaledFeatures", "label").toPandas()
X   = pdf["scaledFeatures"].apply(lambda x: x.toArray()).tolist()
y   = pdf["label"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.long)
X_test  = torch.tensor(X_test,  dtype=torch.float32)
y_test  = torch.tensor(y_test,  dtype=torch.long)


class RedNeuronal(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 16), nn.ReLU(),
            nn.Linear(16, 8), nn.ReLU(),
            nn.Linear(8, 3)
        )

    def forward(self, x):
        return self.net(x)


model     = RedNeuronal()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.01)

for epoch in range(100):
    outputs = model(X_train)
    loss    = criterion(outputs, y_train)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    if epoch % 10 == 0:
        print(f"Epoch {epoch} - Loss: {loss.item():.4f}")

with torch.no_grad():
    outputs  = model(X_test)
    _, pred  = torch.max(outputs, 1)
    accuracy = (pred == y_test).sum().item() / len(y_test)

print(f"Precisión: {accuracy * 100:.2f}%")

# Predicción de cita nueva: 45 min, $300 MXN
labels_map = {0: "Ingreso bajo (<$200)", 1: "Ingreso medio ($200-$450)", 2: "Ingreso alto (>$450)"}
nuevo = torch.tensor([[45.0, 300.0]])
with torch.no_grad():
    prob  = torch.softmax(model(nuevo), dim=1)
    clase = torch.argmax(prob).item()
print(f"Cita 45min/$300: {labels_map[clase]}")
print(f"Probabilidades: {prob.numpy()}")

spark.stop()
