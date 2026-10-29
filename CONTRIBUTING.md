# Contribuir a UrbanBlade Analytics

Leer [arquitectura](docs/arquitectura.md), [seguridad](SECURITY.md) y
[desarrollo](docs/desarrollo.md). El alcance proviene de una petición o issue del
producto; no se inventan historias académicas ni se cambia el backlog de otros componentes.

1. Revisar estado y conservar trabajo ajeno. Crear una rama desde main revisada.
2. Separar cambios de datos, dependencias, UI y operación cuando requieran revisiones distintas.
3. Validar con mocks y datos sintéticos antes de una comprobación real autorizada.
4. Revisar diff, sintaxis, pruebas, secretos y artefactos. Añadir solo rutas revisadas.
5. Publicar por PR cuando el propietario lo ordene para ese cambio, con título y
   descripción en español y evidencia del SHA exacto.
6. Fusionar solo con checks aprobados, sin forzar protecciones ni borrar ramas.
   La fusión no autoriza despliegue, publicación de derivados o escrituras de datos.

No añadir atribuciones de herramientas a commits o PR. No usar force push,
reset destructivo o reescritura de historia para limpiar una edición ordinaria.
Las correcciones que cambien contratos con Barber deben coordinarse antes de ejecutarse.

## Validación por nivel

Pruebas rápidas, integración local, runtime sintético y flujo real son evidencias
distintas. Informar omisiones y fallos; no presentar mocks como una verificación de
Atlas o de roles del usuario. Conservar postmortems y avisos de terceros al retirar
contenido obsoleto.

Las contribuciones originales deben poder distribuirse bajo [GPL-3.0-only](LICENSE).
La licencia no incluye datos, cuentas o credenciales ni implica cesión de autoría.
