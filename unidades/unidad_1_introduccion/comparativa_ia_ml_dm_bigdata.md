# Unidad I — Documento comparativo: IA · Machine Learning · Data Mining · Big Data

**Asignatura:** Extracción del conocimiento en bases de datos · UTVT · IDGS-93
**Equipo:** Equipo UrbanBlade · **Docente:** MGTI. Héctor Velázquez Estrada
**Caso de aplicación transversal:** UrbanBlade (sistema de barbería, MongoDB `barber_db`)

> Entregable de la sesión 1–4. Cubre: características, beneficios/restricciones/retos,
> casos de aplicación, y lenguajes/herramientas de cada disciplina.

---

## 1. Definiciones

| Disciplina | Definición | Alcance |
|---|---|---|
| **Inteligencia Artificial (IA)** | Campo que busca que las máquinas realicen tareas que requieren "inteligencia" humana (razonar, percibir, decidir). | El más amplio; contiene a ML como subcampo. |
| **Machine Learning (ML)** | Subcampo de la IA: algoritmos que **aprenden patrones de los datos** sin ser programados explícitamente. | Regresión, clasificación, clustering, redes neuronales. |
| **Data Mining (Minería de datos)** | Proceso de **descubrir patrones y relaciones** útiles en grandes volúmenes de datos. | Reglas de asociación, segmentación, detección de anomalías. |
| **Big Data** | Conjunto de tecnologías para **almacenar y procesar** datos de gran Volumen, Velocidad y Variedad (las 3 V). | Infraestructura distribuida (Spark, Hadoop). |

**Relación:** Big Data aporta la **infraestructura**, Data Mining el **proceso de descubrimiento**,
ML los **algoritmos que aprenden**, e IA el **paraguas conceptual**.

---

## 2. Características

| Criterio | IA | Machine Learning | Data Mining | Big Data |
|---|---|---|---|---|
| Objetivo | Simular inteligencia | Aprender de datos | Descubrir patrones | Procesar grandes volúmenes |
| Entrada | Reglas + datos | Datos etiquetados/no | Datos históricos | Datos masivos (3V) |
| Salida | Decisiones/acciones | Modelo predictivo | Patrones/reglas | Datos procesados |
| Requiere aprendizaje | No siempre | **Sí (central)** | A veces | No |
| Ejemplo en UrbanBlade | Recomendador de servicios | Predecir cancelaciones | Reglas "corte → barba" | 12,535 citas en Spark |

---

## 3. Beneficios, restricciones y retos

### Beneficios
- **IA/ML:** automatiza decisiones, personaliza la experiencia, anticipa el futuro (churn, demanda).
- **Data Mining:** revela relaciones ocultas (qué servicios se piden juntos).
- **Big Data:** permite analizar el histórico completo, no una muestra.

### Restricciones
- **IA/ML:** dependen de la **calidad de los datos**; un modelo con fuga de datos da métricas falsas.
- **Data Mining:** riesgo de encontrar correlaciones espurias sin causalidad.
- **Big Data:** costo de infraestructura y complejidad de procesamiento distribuido.

### Retos
- Evitar **fuga de datos (leakage)** — p. ej. predecir el ingreso usando el propio ingreso.
- Manejar **clases desbalanceadas** (solo 8.4% de citas se cancelan en UrbanBlade).
- Privacidad de los datos de clientes (nombres, historial, nivel de lealtad).

---

## 4. Casos de aplicación (UrbanBlade)

| Disciplina | Caso real implementado | Unidad |
|---|---|---|
| ML supervisado | Predicción de cancelación de citas (árbol + bosque) | III |
| ML supervisado | Regresión de facturación diaria | III |
| ML no supervisado | Segmentación de clientes (KMeans RFM) | IV |
| Data Mining | Recomendación de servicios (FP-Growth) | IV |
| Big Data | Procesamiento de 12,535 citas con Spark | II |

---

## 5. Lenguajes y herramientas

| Categoría | Herramientas usadas en UrbanBlade |
|---|---|
| Lenguaje | **Python 3.12** |
| Big Data / procesamiento | **Apache Spark (PySpark 3.5)** |
| Machine Learning | **Spark MLlib** (regresión, árboles, KMeans, PCA, FP-Growth) + **PyTorch** (red neuronal) |
| Base de datos | **MongoDB Atlas** (`barber_db`) |
| Visualización | **Matplotlib**, **Plotly**, **Streamlit** |
| Otras (mercado) | R, TensorFlow, scikit-learn, Power BI, Tableau, Hadoop |

---

## 6. Conclusión

Las cuatro disciplinas son **complementarias, no excluyentes**: en UrbanBlade, Big Data
(Spark) procesa el histórico completo, Data Mining descubre patrones de consumo, y el
Machine Learning construye modelos predictivos — todo bajo el paraguas de la IA aplicada
a un problema de negocio real: optimizar la operación de una barbería.
