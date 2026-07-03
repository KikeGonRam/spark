# 05 — Automatización: script de onboarding del equipo

## Problema que resuelve

El incidente documentado en esta unidad ocurrió, en parte, porque no existía un
procedimiento estandarizado para levantar el proyecto desde cero: cada integrante del
equipo corría comandos distintos (`docker compose up`, seeders sueltos, `migrate:fresh`)
sin un flujo verificado, lo que aumenta la probabilidad de ejecutar el comando
equivocado contra la base de datos compartida en producción (MongoDB Atlas).

## Solución: `setup.ps1`

Script de PowerShell (repositorio `barber`, raíz del proyecto) que automatiza el
onboarding en Windows:

1. Verifica prerequisitos (Git, Docker Desktop corriendo, Node.js).
2. Clona o actualiza el repositorio.
3. **Verifica que exista un archivo `.env`** — si no existe, se detiene con
   instrucciones claras de pedirlo al responsable del proyecto. **No genera uno falso
   ni sobreescribe uno real** — evita que alguien trabaje contra una base de datos
   equivocada o con credenciales de prueba.
4. Levanta los contenedores (`docker compose up -d --build`) y espera a que el
   contenedor de la aplicación reporte estado `healthy`.
5. Corre **únicamente** `php artisan migrate --force` (nunca `migrate:fresh` ni
   `--seed`) — decisión deliberada para que el script de onboarding nunca pueda borrar
   los datos reales de otro integrante del equipo.
6. Compila el frontend en el host (`npm install && npm run build`), ya que este
   proyecto no tiene un servicio de Node dentro de Docker.

## Decisión de diseño clave

> El script de onboarding es intencionalmente menos "completo" que un reset total: NO
> ofrece la opción de sembrar datos de ejemplo automáticamente. Cualquier operación
> destructiva (`migrate:fresh --seed`) queda como paso manual, documentado pero fuera
> del flujo automático — precisamente el tipo de salvaguarda que habría prevenido este
> incidente si hubiera existido antes.

## Relación con Unidad II (calidad de datos)

Este script aplica el mismo principio que los scripts de calidad de datos de la
Unidad II (`08_calidad_pagos.py`): antes de operar, **verificar el estado real en vez
de asumirlo**. Aquí se verifica que el `.env` exista y que Docker esté corriendo antes
de continuar; allá se verifica que las citas completadas tengan pago reconciliado antes
de reportar el análisis como confiable.
