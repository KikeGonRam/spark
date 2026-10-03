"""Guarda automática de solo lectura sobre las colecciones reales de `barber_db`.

Convierte en prueba ejecutable la regla documentada en `CLAUDE.md`: el proyecto
`spark` solo puede escribir en

  * `analytics_insights` — y siempre a través de
    `config.analytics_publication.publish_insights_atomically`;
  * `appointments_synthetic` — colección sintética del generador de datos;
  * bases terminadas en `_e2e` — exclusivamente desde pruebas y fixtures.

Todo lo demás (`appointments`, `users`, `barbers`, `clients`, `services`, `payments`,
`products`, `loyalty_transactions`, `barber_schedules`, `barbershop_settings`, …) es
de solo lectura.

Esta prueba existe porque `barber_db` se comparte con la app Laravel y ya se perdió
información real una vez (ver
`unidades/unidad_6_caso_aplicado_laravel/01_diagnostico_incidente.md`).

La detección usa el AST de Python, no expresiones regulares: así `rename(columns=…)`
de pandas o `.drop("columna")` de Spark no se confunden con una escritura en Mongo.
"""

import ast
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Métodos que modifican datos, crean o destruyen colecciones/bases en pymongo.
METODOS_ESCRITURA = {
    "insert_one",
    "insert_many",
    "update_one",
    "update_many",
    "replace_one",
    "delete_one",
    "delete_many",
    "bulk_write",
    "find_one_and_replace",
    "find_one_and_update",
    "find_one_and_delete",
    "create_collection",
    "drop_collection",
    "drop_database",
    "drop",
}

# `rename` es ambiguo: pandas lo usa para renombrar columnas y series. Solo cuenta
# como escritura si el receptor parece un handle de Mongo (ver _es_receptor_mongo).
METODOS_ESCRITURA_AMBIGUOS = {"rename"}

# Identificadores que en este proyecto designan un handle de MongoDB.
RECEPTORES_MONGO = {
    "db",
    "_db",
    "database",
    "_database",
    "client",
    "_client",
    "mongo",
    "_mongo",
    "coleccion",
    "_coleccion",
    "collection",
    "_collection",
    "coll",
    "_coll",
}

# Únicos archivos autorizados a contener llamadas de escritura directas.
ESCRITORES_AUTORIZADOS = {
    "config/analytics_publication.py",
    "data_ingestion/generar_datos_urbanblade.py",
    "tests/fixtures/analytics_core_fixture.py",
    "tests/test_analytics_publication_integration.py",
}

# Directorios que no forman parte del código entregable.
DIRECTORIOS_IGNORADOS = {"data", "__pycache__", ".pytest_cache", ".git", ".venv"}


def _es_nombre_mongo(nombre):
    minuscula = nombre.lower()
    if minuscula in RECEPTORES_MONGO:
        return True
    return any(fragmento in minuscula for fragmento in ("coleccion", "collection", "coll"))


def _es_receptor_mongo(nodo):
    """¿El receptor de la llamada parece un handle de MongoDB?"""
    return any(
        isinstance(hijo, ast.Name) and _es_nombre_mongo(hijo.id)
        for hijo in ast.walk(nodo)
    )


def escanear_fuente(codigo, ruta="<memoria>"):
    """Devuelve las escrituras a Mongo encontradas en un fragmento de código."""
    try:
        arbol = ast.parse(codigo)
    except SyntaxError:
        return []

    hallazgos = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        funcion = nodo.func
        if not isinstance(funcion, ast.Attribute):
            continue
        metodo = funcion.attr
        if metodo not in METODOS_ESCRITURA and metodo not in METODOS_ESCRITURA_AMBIGUOS:
            continue
        if not _es_receptor_mongo(funcion.value):
            continue
        hallazgos.append({"ruta": ruta, "metodo": metodo, "linea": nodo.lineno})
    return hallazgos


def archivos_python():
    for ruta in sorted(RAIZ.rglob("*.py")):
        if any(parte in DIRECTORIOS_IGNORADOS for parte in ruta.parts):
            continue
        yield ruta


def escanear_proyecto():
    hallazgos = {}
    for ruta in archivos_python():
        relativa = ruta.relative_to(RAIZ).as_posix()
        encontrados = escanear_fuente(ruta.read_text(encoding="utf-8"), relativa)
        if encontrados:
            hallazgos[relativa] = encontrados
    return hallazgos


class GuardaSoloLecturaTest(unittest.TestCase):
    """Invariantes sobre el árbol real del repositorio."""

    def test_solo_los_archivos_autorizados_escriben_en_mongo(self):
        hallazgos = escanear_proyecto()
        encontrados = set(hallazgos)

        no_autorizados = encontrados - ESCRITORES_AUTORIZADOS
        self.assertEqual(
            set(),
            no_autorizados,
            "Estos archivos escriben en MongoDB pero no están autorizados: "
            f"{sorted(no_autorizados)}. Detalle: "
            f"{ {clave: hallazgos[clave] for clave in sorted(no_autorizados)} }. "
            "La regla del proyecto es que spark solo escribe en analytics_insights, "
            "appointments_synthetic y bases *_e2e. Si la escritura es legítima, "
            "justifícala y agrega el archivo a ESCRITORES_AUTORIZADOS.",
        )

        # El sentido inverso: una entrada de la lista blanca que ya no escribe deja
        # de proteger nada y esconde el motivo por el que se autorizó.
        obsoletos = ESCRITORES_AUTORIZADOS - encontrados
        self.assertEqual(
            set(),
            obsoletos,
            f"Entradas obsoletas en ESCRITORES_AUTORIZADOS: {sorted(obsoletos)}. "
            "Quítalas para que la lista blanca siga significando algo.",
        )

    def test_ningun_script_de_analisis_escribe(self):
        infracciones = []
        for ruta in sorted((RAIZ / "unidades").rglob("*.py")):
            hallazgos = escanear_fuente(
                ruta.read_text(encoding="utf-8"),
                ruta.relative_to(RAIZ).as_posix(),
            )
            if hallazgos:
                infracciones.append(ruta.relative_to(RAIZ).as_posix())
        self.assertEqual(
            [],
            infracciones,
            f"Los scripts de las unidades son de solo lectura: {infracciones}",
        )

    def test_el_exportador_delega_en_el_publicador_atomico(self):
        ruta = RAIZ / "unidades/unidad_5_visualizacion/exportar_insights_dashboard.py"
        codigo = ruta.read_text(encoding="utf-8")
        arbol = ast.parse(codigo)

        self.assertEqual(
            [],
            escanear_fuente(codigo, "exportar_insights_dashboard.py"),
            "El exportador no debe escribir directamente: debe usar "
            "publish_insights_atomically para no dejar el destino vacío a medias.",
        )

        nombres_llamados = {
            nodo.func.id
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
        }
        self.assertIn("publish_insights_atomically", nombres_llamados)

    def test_el_publicador_apunta_a_analytics_insights(self):
        ruta = RAIZ / "config/analytics_publication.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        funcion = next(
            nodo
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.FunctionDef)
            and nodo.name == "publish_insights_atomically"
        )
        # `defaults` se alinea con la COLA de `args`, no con su inicio.
        nombres = [argumento.arg for argumento in funcion.args.args]
        self.assertIn("target_collection", nombres)
        valores_por_defecto = dict(
            zip(nombres[-len(funcion.args.defaults) :], funcion.args.defaults)
        )
        self.assertEqual(
            "analytics_insights",
            ast.literal_eval(valores_por_defecto["target_collection"]),
        )

    def test_los_archivos_de_prueba_exigen_base_e2e(self):
        rutas = [
            RAIZ / "tests/fixtures/analytics_core_fixture.py",
            RAIZ / "tests/test_analytics_publication_integration.py",
        ]
        for ruta in rutas:
            arbol = ast.parse(ruta.read_text(encoding="utf-8"))
            exige_sufijo = any(
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "endswith"
                and any(
                    isinstance(argumento, ast.Constant) and argumento.value == "_e2e"
                    for argumento in nodo.args
                )
                for nodo in ast.walk(arbol)
            )
            self.assertTrue(
                exige_sufijo,
                f"{ruta.name} debe exigir que la base termine en _e2e antes de "
                "escribir: es lo que impide que apunte a barber_db por accidente.",
            )

    def test_el_generador_solo_usa_la_coleccion_sintetica(self):
        ruta = RAIZ / "data_ingestion/generar_datos_urbanblade.py"
        codigo = ruta.read_text(encoding="utf-8")
        self.assertIn("MONGO_COLLECTION_SYNTHETIC", codigo)

        # Se inspeccionan solo las constantes de cadena del código, no los
        # comentarios: el archivo menciona la colección real justamente para
        # explicar que nunca la toca.
        arbol = ast.parse(codigo)
        cadenas = {
            nodo.value
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
        }
        self.assertIn("appointments_synthetic", cadenas)
        self.assertNotIn(
            "appointments",
            cadenas,
            "El generador no debe poder apuntar a la colección real de la app.",
        )


class DetectorTest(unittest.TestCase):
    """El guard solo sirve si de verdad detecta violaciones y no da falsos positivos."""

    def test_detecta_escrituras_reales(self):
        violaciones = [
            'db.appointments.insert_many([{"x": 1}])',
            'db["appointments"].insert_one({"x": 1})',
            'coleccion.update_many({}, {"$set": {"x": 1}})',
            'db["users"].delete_many({})',
            'client.drop_database(database)',
            'db.create_collection("temporal")',
            'coleccion.bulk_write([])',
            'db[destino].rename("appointments", dropTarget=True)',
            'db.payments.find_one_and_update({}, {})',
        ]
        for codigo in violaciones:
            with self.subTest(codigo=codigo):
                self.assertTrue(
                    escanear_fuente(codigo),
                    f"No se detectó la escritura: {codigo}",
                )

    def test_no_marca_operaciones_de_pandas_ni_de_spark(self):
        # Casos reales del repositorio que antes producían falsos positivos.
        lecturas = [
            'primera_cita = d.groupby("client_id")["mes_cita"].min().rename("cohorte")',
            'df = df.rename(columns={"duracion_min": "horas_ocupadas"})',
            'resultado = agregado.drop("fecha_dt")',
            'st.dataframe(combo_pdf.rename(columns={"a": "b"}))',
            'filas = db["appointments"].find({}, {"_id": 1})',
            'barbers_map = {str(b["_id"]): b for b in db["barbers"].find({})}',
            'insights = list(db["pagos"].aggregate([]))',
        ]
        for codigo in lecturas:
            with self.subTest(codigo=codigo):
                self.assertEqual(
                    [],
                    escanear_fuente(codigo),
                    f"Falso positivo, no es una escritura: {codigo}",
                )


if __name__ == "__main__":
    unittest.main()
