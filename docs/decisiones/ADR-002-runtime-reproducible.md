# ADR-002: runtime acotado y dependencias verificables

Estado: aceptada. Registro: 2026-10-29. Documenta el runtime integrado en el PR #1.

## Contexto

El dashboard debe arrancar sin instalar todos los frameworks opcionales de
entrenamiento. Actualizar versiones sin ejecutar Spark y Streamlit puede dejar
un conjunto de dependencias resoluble pero inutilizable.

## Decisión

El runtime verificado usa Python 3.12, Java 17 y PySpark 3.5.9, con pandas 2.x y
NumPy 1.26.4. setuptools proporciona la compatibilidad distutils que necesita
PySpark bajo Python 3.12. Los frameworks de entrenamiento siguen en otro perfil.

CI y Docker instalan resoluciones completas con hashes. Se exigen wheels salvo
para PySpark, publicado como fuente; su artefacto también tiene hash fijado.
pylock.toml registra los mismos paquetes de runtime según PEP 751. Las Actions
se fijan por SHA y las imágenes base por digest.

## Consecuencias y revisión

Un hash verifica integridad del artefacto revisado, no la ausencia de vulnerabilidades.
La auditoría Python no cubre por sí sola Java o el sistema operativo. Actualizar
perfiles exige regenerar locks, instalar con hashes, ejecutar pruebas y auditar.

Spark 4, nuevas versiones mayores de pandas/NumPy o cambios del modelo requieren
una entrega propia con compatibilidad y evaluación explícitas. No se presentan
métricas históricas como resultados de esta validación de runtime.

El runner de Mongo está temporalmente en Ubuntu 22.04 por compatibilidad de kernel;
revisarlo antes de su retirada. Ver [desarrollo](../desarrollo.md).
