# Spark preprocesa y escala → PyTorch entrena — patrón del profesor
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split

spark = SparkSession.builder \
    .appName("UrbanBlade-RedNeuronal") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Dataset de UrbanBlade: (cantidad, precio, label)
# label: 0=ingreso bajo, 1=ingreso medio, 2=ingreso alto
data = [
    (1, 150, 0), (2, 300, 1), (1, 100, 0), (3, 450, 2),
    (2, 200, 1), (1, 400, 2), (3, 600, 2), (1, 120, 0),
    (2, 250, 1), (3, 750, 2), (1, 130, 0), (2, 220, 1),
    (3, 500, 2), (1, 110, 0), (2, 280, 1), (3, 650, 2),
    (1, 160, 0), (2, 350, 1), (3, 700, 2), (1, 140, 0)
]
columns = ["cantidad", "precio", "label"]
df = spark.createDataFrame(data, columns)

assembler = VectorAssembler(inputCols=["cantidad", "precio"], outputCol="features")
df_vector = assembler.transform(df)

# Escalar con Spark antes de pasar a PyTorch
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

print("\nEntrenando Red Neuronal UrbanBlade...")
for epoch in range(100):
    outputs = model(X_train)
    loss    = criterion(outputs, y_train)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    if epoch % 10 == 0:
        print(f"  Epoch {epoch:3d} – Loss: {loss.item():.4f}")

with torch.no_grad():
    outputs  = model(X_test)
    _, pred  = torch.max(outputs, 1)
    accuracy = (pred == y_test).sum().item() / len(y_test)

print(f"\nPrecisión en test: {accuracy * 100:.2f}%")

labels_map = {0: "Ingreso bajo", 1: "Ingreso medio", 2: "Ingreso alto"}

# Predicción de ejemplo: barbero con 2 servicios a $300
nuevo = torch.tensor([[2.0, 300.0]])
with torch.no_grad():
    prob  = torch.softmax(model(nuevo), dim=1)
    clase = torch.argmax(prob).item()
print(f"\nPredicción para (cantidad=2, precio=300):")
print(f"  Clase: {labels_map[clase]}")
print(f"  Probabilidades: {prob.numpy()}")

spark.stop()
