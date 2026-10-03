"""El acceso al dashboard pregunta a la API de barber y nunca lee contraseñas.

Fija el arreglo del 2026-10-02: antes `autenticar_usuario` comparaba el hash bcrypt
de `barber_db.users` en Python, saltándose el límite de intentos de barber. La API
se simula con unittest.mock; no hace falta barber, Mongo ni PySpark.
"""
import ast
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from config import barber_auth
from config.barber_auth import ApiNoDisponible, LoginBloqueado, autenticar_usuario, verificar_google_token

BASE = "http://barber.prueba"


def respuesta(status, cuerpo=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = cuerpo if cuerpo is not None else {}
    return r


def login_ok(roles):
    return respuesta(200, {
        "token": "token-emitido",
        "user": {"name": "Ana", "email": "ana@ejemplo.com", "roles": roles},
    })


@patch.dict("os.environ", {"BARBER_API_URL": BASE})
@patch.object(barber_auth, "_cargar_env", lambda: None)
class AutenticarUsuarioTest(unittest.TestCase):

    @patch("config.barber_auth.requests.post")
    def test_credenciales_validas_con_rol_autorizado(self, post):
        post.side_effect = [login_ok(["ingeniero"]), respuesta(200)]

        usuario = autenticar_usuario("  Ana@Ejemplo.com ", "secreta")

        self.assertEqual(usuario, {"name": "Ana", "email": "ana@ejemplo.com", "rol": "ingeniero"})
        login = post.call_args_list[0]
        self.assertEqual(login.args[0], f"{BASE}/api/v1/auth/login")
        self.assertEqual(login.kwargs["json"]["email"], "ana@ejemplo.com")
        self.assertEqual(login.kwargs["json"]["device_name"], "Spark Dashboard")

    @patch("config.barber_auth.requests.post")
    def test_revoca_el_token_que_emite_barber(self, post):
        post.side_effect = [login_ok(["administrador"]), respuesta(200)]

        autenticar_usuario("ana@ejemplo.com", "secreta")

        logout = post.call_args_list[1]
        self.assertEqual(logout.args[0], f"{BASE}/api/v1/auth/logout")
        self.assertEqual(logout.kwargs["headers"]["Authorization"], "Bearer token-emitido")

    @patch("config.barber_auth.requests.post")
    def test_rol_no_autorizado_no_entra(self, post):
        post.side_effect = [login_ok(["cliente"]), respuesta(200)]

        self.assertIsNone(autenticar_usuario("cliente@ejemplo.com", "secreta"))
        # Aunque no entre, el token emitido se revoca igual.
        self.assertEqual(post.call_count, 2)

    @patch("config.barber_auth.requests.post")
    def test_credenciales_invalidas(self, post):
        post.return_value = respuesta(422, {"message": "Las credenciales no son válidas."})

        self.assertIsNone(autenticar_usuario("ana@ejemplo.com", "mala"))
        self.assertEqual(post.call_count, 1)

    @patch("config.barber_auth.requests.post")
    def test_demasiados_intentos(self, post):
        post.return_value = respuesta(429)

        with self.assertRaises(LoginBloqueado):
            autenticar_usuario("ana@ejemplo.com", "mala")

    @patch("config.barber_auth.requests.post")
    def test_api_caida(self, post):
        post.side_effect = requests.ConnectionError("sin red")

        with self.assertRaises(ApiNoDisponible):
            autenticar_usuario("ana@ejemplo.com", "secreta")

    @patch("config.barber_auth.requests.post")
    def test_error_del_servidor(self, post):
        post.return_value = respuesta(503)

        with self.assertRaises(ApiNoDisponible):
            autenticar_usuario("ana@ejemplo.com", "secreta")


@patch.dict("os.environ", {"BARBER_API_URL": BASE})
@patch.object(barber_auth, "_cargar_env", lambda: None)
class VerificarGoogleTokenTest(unittest.TestCase):

    @patch("config.barber_auth.requests.post")
    @patch("config.barber_auth.requests.get")
    def test_lee_el_rol_y_revoca_el_token(self, get, post):
        get.return_value = respuesta(200, {"user": {"name": "Ana", "email": "a@e.com", "roles": ["administrador"]}})
        post.return_value = respuesta(200)

        usuario = verificar_google_token("token-de-google")

        self.assertEqual(usuario["rol"], "administrador")
        self.assertEqual(post.call_args.args[0], f"{BASE}/api/v1/auth/logout")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer token-de-google")

    @patch("config.barber_auth.requests.post")
    @patch("config.barber_auth.requests.get")
    def test_token_invalido(self, get, post):
        get.return_value = respuesta(401)

        self.assertIsNone(verificar_google_token("vencido"))
        post.assert_not_called()


class SinAccesoALaBaseTest(unittest.TestCase):
    """El módulo de acceso no debe volver a tocar Mongo ni bcrypt."""

    def test_no_importa_pymongo_ni_bcrypt(self):
        fuente = Path(barber_auth.__file__).read_text(encoding="utf-8")
        modulos = set()
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.Import):
                modulos.update(a.name.split(".")[0] for a in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                modulos.add(nodo.module.split(".")[0])
        self.assertFalse({"pymongo", "bcrypt"} & modulos, modulos)


if __name__ == "__main__":
    unittest.main()
