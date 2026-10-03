"""
Acceso al dashboard de spark a través de la API de barber
=========================================================
barber es la fuente de verdad de la identidad y los roles. spark nunca lee
contraseñas ni hashes: tanto el login con correo como el de Google preguntan a la
API (`POST /api/v1/auth/login`, `GET /api/v1/auth/me`) y después revocan el token
que barber emitió (`POST /api/v1/auth/logout`), porque el dashboard solo necesita
saber quién entró y con qué rol, no conservar una sesión de la API.

Antes (hasta el 2026-10-02) el login con correo leía `barber_db.users`, comparaba
el hash bcrypt en Python y resolvía el rol en `roles`: se saltaba el límite de 5
intentos por minuto de barber y obligaba a spark a leer datos de autenticación.

Solo depende de `requests` y `python-dotenv`, para poder probarse sin PySpark.
"""
from __future__ import annotations

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Roles reales de `barber` (RolePermissionSeeder) autorizados a ver el dashboard.
# 'ingeniero' es el nombre real del rol; spark lo presenta como "Analista".
ROLES_AUTORIZADOS = ["administrador", "ingeniero"]

_TIMEOUT = 8


class LoginBloqueado(Exception):
    """barber respondió 429: demasiados intentos con ese correo en el último minuto."""


class ApiNoDisponible(Exception):
    """No se pudo hablar con la API de barber (red caída, 5xx o respuesta inválida)."""


def _cargar_env() -> None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


def _api_base() -> str:
    """URL de servidor a servidor (dentro de Docker suele ser http://web)."""
    _cargar_env()
    return os.getenv("BARBER_API_URL", "http://localhost:8000").rstrip("/")


def _usuario_autorizado(user: dict) -> dict | None:
    roles = user.get("roles") or []
    rol = next((r for r in roles if r in ROLES_AUTORIZADOS), None)
    if rol is None:
        return None
    return {"name": user.get("name", "Usuario"), "email": user.get("email", ""), "rol": rol}


def _revocar(base: str, token: str) -> None:
    """Revoca el token de barber; un fallo aquí no debe impedir la entrada."""
    try:
        requests.post(
            f"{base}/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=_TIMEOUT,
        )
    except requests.RequestException:
        pass


def autenticar_usuario(email: str, password: str) -> dict | None:
    """Login con correo y contraseña contra barber.

    Devuelve {"name", "email", "rol"} si las credenciales son válidas y el rol está
    autorizado; None si no lo son. Lanza LoginBloqueado (429) o ApiNoDisponible
    (sin conexión o error del servidor) para que la pantalla muestre el motivo real.
    """
    base = _api_base()
    try:
        resp = requests.post(
            f"{base}/api/v1/auth/login",
            json={
                "email": str(email).strip().lower(),
                "password": password,
                "device_name": "Spark Dashboard",
            },
            headers={"Accept": "application/json"},
            timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise ApiNoDisponible(str(exc)) from exc

    if resp.status_code == 429:
        raise LoginBloqueado()
    if resp.status_code >= 500:
        raise ApiNoDisponible(f"HTTP {resp.status_code}")
    if resp.status_code != 200:
        # 401/403/422: credenciales inválidas o correo sin verificar. No se distingue
        # a propósito, igual que barber, para no revelar qué correos existen.
        return None

    try:
        datos = resp.json()
    except ValueError as exc:
        raise ApiNoDisponible("respuesta no JSON") from exc

    token = datos.get("token")
    if token:
        _revocar(base, token)
    return _usuario_autorizado(datos.get("user") or {})


def google_login_url() -> str:
    """URL para iniciar el login con Google — reutiliza el OAuth de barber
    (SocialAuthController::redirect) con ?target=spark, que hace que barber
    regrese aquí en vez de a frontend-urban.

    Usa BARBER_PUBLIC_URL, NO BARBER_API_URL: este link lo abre el NAVEGADOR del
    usuario, que no puede resolver nombres internos de Docker como "http://web"."""
    _cargar_env()
    base = os.getenv("BARBER_PUBLIC_URL") or os.getenv("BARBER_API_URL", "http://localhost:8000")
    return f"{base.rstrip('/')}/api/v1/auth/google/redirect?target=spark"


def verificar_google_token(token: str) -> dict | None:
    """Verifica el token que barber emitió tras el login con Google (GET /auth/me)
    y lo revoca después de leer el rol: viajó en la URL (?google_token=) y no debe
    quedar vigente en el historial del navegador."""
    base = _api_base()
    try:
        resp = requests.get(
            f"{base}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=_TIMEOUT,
        )
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None

    try:
        user = resp.json().get("user") or {}
    except ValueError:
        return None

    _revocar(base, token)
    return _usuario_autorizado(user)
