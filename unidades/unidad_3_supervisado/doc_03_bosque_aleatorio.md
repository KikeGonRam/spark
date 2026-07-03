# 05 — Random Forest (Bosque Aleatorio): Cancelación

## Descripción

Predice si una cita será **cancelada** (1) o no (0) con un Pipeline de PySpark.
Resuelve **el mismo problema que el script 04** (árbol único) pero con un ensemble,
para comparar "un árbol vs 100 árboles".

```
VectorAssembler → RandomForestClassifier(numTrees=100, maxDepth=5)
```

Label:
```
categoria = es_cancelada   (1 = cancelada, 0 = resto)
```

Split: 70/30. Datos: **12,505 citas reales**.

---

## Estados reales

En `barber_db` los estados son exactamente cuatro:
`cancelada, completada, confirmada, pendiente`.
**No existe `no_asistio`** — se eliminó ese código muerto de la versión anterior.
Solo `cancelada` representa ingreso perdido.

---

## Features (sin fuga de datos)

`duracion_min`, `precio`, `hora`, `dia_semana`, `mes` — el contexto de la cita.
El estado no se usa como feature. (La versión anterior incluía `ingreso`, que es una
copia de `precio`, inflando la importancia de esa variable de forma artificial.)

---

## Métrica clave: AUC

Las clases están desbalanceadas (~8.4% cancelaciones), así que el **AUC-ROC** es la
métrica relevante, no el accuracy. Se comparan Accuracy, Precision, Recall, F1 y AUC.

**Comparación esperada:** el bosque (05) debería obtener un AUC igual o mayor que el
árbol único (04), demostrando la ventaja del ensemble (promedia 100 árboles → menos
sobreajuste).

---

## Persistencia

El pipeline entrenado se guarda en `modelo_pipeline_rf_urbanblade/` y puede reutilizarse
para puntuar citas nuevas sin reentrenar.

---

## Mejoras aplicables

- Balanceo de clases (oversampling de cancelaciones) para subir el recall de la clase 1.
- Añadir features de cliente (historial, nivel VIP) desde la capa de datos única.
- Umbral de decisión ajustado para priorizar recall sobre precisión.
