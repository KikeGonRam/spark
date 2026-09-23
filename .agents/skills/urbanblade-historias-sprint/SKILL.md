---
name: urbanblade-historias-sprint
description: Forma de trabajo de Urban Blade desde el 23-sep-2026 — todo trabajo sale de una historia de usuario (HU/T) del Product Backlog o de una historia técnica (HT/TT) asignada, dentro de su sprint. Usar al iniciar cualquier sesión de trabajo en este repositorio, antes de proponer o escribir código, al elegir qué hacer, al preparar un commit o al reportar avance.
---

# Trabajo guiado por historias (Urban Blade)

Desde el 23-sep-2026 el equipo trabaja **solo** con lo que se encargó en el
cuatrimestre: historias de usuario (HU-xx, tareas Txxx) e historias técnicas (HT-xx,
tareas TTxx). Nada de funciones nuevas, rediseños ni refactors "de paso" si no están
ligados a una tarea.

Esta skill existe con el mismo nombre en los cuatro repositorios (`barber`,
`frontend-urban`, `UrbanBladeMobile`, `spark`). El núcleo es idéntico; cambia solo la
sección **"Tareas de este repositorio"**. Si cambias el núcleo, cámbialo en los cuatro.

## Fuente de verdad

Carpeta `C:\Users\luis1\Documents\UrbanBlade\DOCUMENTACION\` (no es repositorio Git):

| Archivo | Para qué |
|---|---|
| `Product_Backlog_Urban_Blade_UBv3_Pendiente.xlsx` | **Tablero de trabajo**: 17 HU, 42 tareas, 74 pts pendientes. Hoja «Tablero de Tareas» = estado real (col. N). |
| `Historias_Tecnicas_Urban_Blade.xlsx` | HT-01 a HT-14, TT01 a TT37 (55 pts), ligadas al checklist y casos de prueba. |
| `Product_Backlog_Urban_Blade_UBv2.xlsx` | Registro completo con evidencia (incluye lo ya completado). |
| `UrbanBlade_Checklist_250_v2.xlsx`, `Casos_de_Prueba_Urban_Blade_v2.xlsx` | Pruebas que alimentan las HT. |

Si la tabla de esta skill contradice los Excel, **ganan los Excel** (esta skill es una
foto al 23-sep-2026). Para editar los Excel usar la skill `urbanblade-product-backlog`
(en `barber`).

## Calendario

| Sprint | Fechas | Notas |
|---|---|---|
| 1 | 14–25 sep | |
| 2 | 28 sep–9 oct | Terraform empieza el **5-oct** |
| 3 | 12–23 oct | |
| 4 | 26 oct–6 nov | CI/CD y Continuous Delivery desde el **26-oct** (≥ 25-oct) |
| 5 | 9–20 nov | |
| 6 | 23 nov–4 dic | Cierre, pruebas finales y documentación |

Puntos 1, 3 o 5; 1 punto = 8 horas. Estados: Pendiente, En progreso, Completado.

## Equipo

| Integrante | Rol |
|---|---|
| Alan Ruiz Vilchis | Product Owner / Backend |
| Elías García Nolasco | Scrum Master / Frontend |
| Miguel Ángel Mena Garduño | QA Tester / Frontend |
| Luis Enrique González Ramírez | Full Stack / Mobile |
| María Isabel Cruz Flores | Backend / Administradora de BD |

## Flujo obligatorio por tarea

1. **Identificar la tarea.** Pregunta o deduce quién es el usuario y busca su tarea en
   la tabla de abajo o en el Excel. Si lo pedido no corresponde a ninguna HU/HT, dilo y
   propón a qué tarea ligarlo o que el PO (Alan) la agregue; no lo hagas "por fuera".
2. **Revisar dependencias.** Si la tarea depende de otra que no está Completada
   (columna "Depende de"), no la adelantes en `main`; avisa a quién se espera.
3. **Leer los criterios de aceptación** de la HU/HT (hoja «Product Backlog» o
   «Historias Técnicas»). La tarea está hecha cuando se cumplen, no cuando compila.
4. **Revisar lo existente** en el código antes de escribir: muchas cosas ya existen a
   medias. No reinventar ni duplicar.
5. **Implementar lo mínimo** que cumple el criterio, con sus pruebas.
6. **Validar** con los comandos de este repositorio (sección de abajo). Sin validación
   no hay commit.
7. **Entregar al usuario**: resumen, archivos, resultado de pruebas y los comandos
   completos para PowerShell (`cd` al repo, `git add` con rutas, `git commit`,
   `git push origin main`). El mensaje de commit va en español, con el ID de la tarea:
   `feat(pagos): T144 mensajes claros al cancelar el pago con tarjeta`.
   **La IA no ejecuta `git commit` ni `git push`**: solo el usuario, y solo en `main`.
8. **Marcar el estado con evidencia**: una tarea pasa a *Completado* solo con evidencia
   verificable (commit en `main` + prueba que pasa, o registro de QA). Código subido sin
   probar = *En progreso*. "NO INVENTES AVANCE".

## Reglas de alcance

- Tecnología real: Laravel 13 + MongoDB (`laravel-mongodb`), token Bearer propio
  (`mobile_api_tokens`, no JWT ni Sanctum), Nuxt 4, Android nativo Kotlin + Jetpack
  Compose. Nunca Next.js, Expo, Mongoose ni JWT.
- `mobil` (Expo) está descontinuado; no es evidencia ni se toca.
- La API `/api/v1` es contrato para web y Android: cambios aditivos, con prueba.
- Terraform: aún no existe en ningún repositorio; su ubicación la define **T112**
  (Alan). No crear archivos `.tf` antes de que T112 esté en `main`.
- Secretos: nunca en código, `.tf`, docs ni en la app Android (solo claves públicas
  como `pk_test_...`). `docs/ACCESOS.md` de `barber` es la única fuente de credenciales.
- Diseños (Stitch, Figma) se revisan contra la HU que implementan antes de codificar.

## Tareas de este repositorio (spark)

**`spark` no tiene historias asignadas en el backlog de este cuatrimestre.** Es el
proyecto de la materia de Extracción del conocimiento y comparte `barber_db` con
`barber`. Reglas:

- No crear trabajo en `spark` por iniciativa propia; solo si una HU/HT de otro repo lo
  requiere (por ejemplo, datos de analítica que consume el dashboard de `barber`) o si
  el usuario lo pide explícitamente para la materia.
- Cualquier cambio de esquema o de colecciones compartidas se coordina con `barber`
  (skill `urbanblade-data-architecture`). Nunca escribir en Atlas desde pruebas.
- Se trabaja solo en `main` (el `CLAUDE.md` que menciona la rama `urbanblade-analytics`
  está desactualizado: hoy el repositorio solo tiene `main`).
## Validación antes de entregar el commit

```powershell
# dentro de WSL, entorno spark_env
python -m pytest tests
```
