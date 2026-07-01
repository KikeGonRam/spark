# 04 — Árbol de Decisión: Predicción de Cancelación

## Descripción

Clasifica cada cita según si será **cancelada** (1) o no (0), a partir de su
contexto (horario, día, servicio). Objetivo de negocio: anticipar cancelaciones
para reducir huecos en la agenda.

```
label = es_cancelada   (1 = cancelada, 0 = resto)
```

Parámetros: `DecisionTreeClassifier(maxDepth=5)`. Split: 80/20.

---

## Features (sin fuga de datos)

| Feature | Origen |
|---------|--------|
| `duracion_min` | del servicio |
| `precio` | precio del servicio |
| `hora` | `hora_inicio` de la cita |
| `dia_semana` | derivada de `fecha` (1=Lun … 7=Dom) |
| `mes` | derivada de `fecha` |

El estado de la cita **NO** se usa como feature — se predice desde el contexto.
Esto evita la fuga de datos del enfoque anterior (que clasificaba "alto valor"
usando `ingreso`, una copia de `precio`, y daba accuracy=100% artificial).

---

## Métrica clave: AUC, no accuracy

Las clases están **desbalanceadas**: solo ~8.4% de las citas se cancelan.
Con ese desbalance, un modelo que prediga "nunca cancela" ya obtiene ~92% de
accuracy sin aprender nada. Por eso la métrica relevante es el **AUC-ROC** y el
**Recall** sobre la clase minoritaria (cancelaciones).

Se reportan: Accuracy, Precision, Recall, F1 y AUC-ROC (calculados en ejecución).

---

## Interpretabilidad

El árbol imprime `toDebugString` (sus reglas) y la **importancia de variables**,
que revela qué factores (hora, día, tipo de servicio) predicen mejor una cancelación.

---

## Relación con el script 05

El script 05 resuelve **el mismo problema** con un **Bosque Aleatorio** (100 árboles).
Comparar el AUC de ambos ilustra por qué un ensemble suele superar a un árbol único:
menos sobreajuste y mayor robustez al ruido.

---

## Aplicación

Reforzar recordatorios (WhatsApp/llamada) y confirmación activa en los horarios y
servicios que el modelo marca como de mayor riesgo de cancelación.
