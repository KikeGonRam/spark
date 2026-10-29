# Dashboard de UrbanBlade Analytics

Entrada: [app.py](app.py). Integra operación, modelos predictivos, retención, demanda
y segmentación. Los paneles de detalle están en [views](views); los cálculos leen
el core con el conector compartido. No se escriben datos operativos desde la interfaz.

El acceso se valida con Barber; únicamente los roles administrador e ingeniero
(presentado como Analista) están autorizados. Spark no compara hashes de contraseñas.
Google usa el flujo existente de Barber y no recibe secretos OAuth del proveedor.

Ejecutar localmente con `streamlit run dashboard/app.py` o con el Compose documentado.
No considerar una respuesta del healthcheck como prueba de login, permisos o calidad
de modelos. Las pruebas AppTest verifican la pantalla inicial sin Mongo; el resto de
la aceptación funcional necesita una sesión autorizada y el entorno correspondiente.

[Desarrollo](../docs/desarrollo.md) · [Operación](../docs/operacion.md).
