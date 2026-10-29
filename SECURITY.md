# Seguridad de UrbanBlade Analytics

## Reportar en privado

Usar el [canal privado del equipo UrbanBlade](https://github.com/KikeGonRam/barber/security/advisories/new)
e indicar componente spark y commit. No publicar secretos, PII, tokens, URI ni
exploits en issues. El canal compartido no presupone un formulario propio habilitado
en este repositorio. No se promete plazo de respuesta, recompensa o soporte no acordado.

## Datos y credenciales

El core pertenece a la operación de UrbanBlade y solo se lee desde este componente.
La conexión analítica usa base y credenciales separadas. Las guardas de configuración,
AST y CLI complementan los permisos remotos; no los sustituyen ni autorizan escrituras.

.env, respaldos de variables, logs con datos, salidas ETL y modelos son privados.
No copiarlos a imágenes o fixtures ni usarlos como evidencia pública. La existencia
de variables reales no autoriza rotarlas, cambiarlas o probar cuentas ajenas.

No usar MONGODB_URI del backend como fallback. No imprimir excepciones del driver que
puedan contener valores de conexión. El diagnóstico muestra solo flags y tipos de error;
los comandos analíticos pueden producir datos de negocio y necesitan operación privada.

## Pruebas y operación

CI no recibe secretos de Atlas. Las integraciones que escriben exigen Mongo loopback
sin credenciales y bases únicas *_e2e. No ejecutar generadores o publicación de insights
contra datos reales por el solo hecho de probar el repositorio.

No ejecutar resets, seeders, migraciones o borrados del core desde Spark. Conservar los
[postmortems](docs/postmortems/README.md) como antecedente y seguir
[operación](docs/operacion.md) para revisar alcance y recuperación.

Si se detecta una credencial expuesta, comunicar tipo y ubicación en privado sin
copiarla ni probarla contra un proveedor. Revocación, rotación y limpieza histórica
requieren coordinación específica; borrar el archivo actual no elimina su historial.

Los escáneres Python, pruebas y healthcheck no certifican el sistema completo, JVM,
modelos o infraestructura. La publicación del código no implica autorización para
pruebas intrusivas sobre el servicio. Ver [licencia](LICENSING.md).
