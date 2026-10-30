"""Configuración validada sin conexiones ni efectos laterales al importar."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from urllib.parse import quote_plus, unquote, urlsplit

from dotenv import load_dotenv
from pymongo import MongoClient


class ConfigurationError(ValueError):
    """Configuración incompleta o incompatible; el mensaje nunca incluye secretos."""


@dataclass(frozen=True)
class MongoSettings:
    uri: str = field(repr=False)
    database: str
    analytics: bool = False


def load_environment(env_file=None):
    selected = env_file or os.getenv('URBANBLADE_ENV_FILE')
    path = Path(selected) if selected else Path(__file__).resolve().parents[1] / '.env'
    if selected and not path.is_file():
        raise ConfigurationError('No existe el archivo de configuración indicado.')
    load_dotenv(dotenv_path=path, override=False)


def _database_from_uri(uri):
    if not uri:
        return ''
    try:
        parsed = urlsplit(uri)
        if parsed.scheme not in {'mongodb', 'mongodb+srv'} or not parsed.hostname:
            raise ValueError
        return unquote(parsed.path.lstrip('/'))
    except ValueError:
        raise ConfigurationError('URI MongoDB inválida; revisar el archivo privado.') from None


def _connection(analytics):
    prefix = 'ANALYTICS_MONGO_' if analytics else 'MONGO_'
    uri_name = 'ANALYTICS_MONGODB_URI' if analytics else 'CORE_MONGODB_URI'
    uri = os.getenv(uri_name, '').strip()
    uri_database = _database_from_uri(uri)
    database = os.getenv(prefix + 'DB', '').strip() or uri_database
    if not database or not re.fullmatch(r'[A-Za-z0-9_-]+', database):
        raise ConfigurationError('Configura un nombre de base válido en ' + prefix + 'DB.')
    if database in {'admin', 'local', 'config'}:
        raise ConfigurationError('No se permite usar una base de sistema MongoDB.')
    if uri_database and uri_database != database:
        raise ConfigurationError('La base de la URI no coincide con ' + prefix + 'DB.')
    if not uri:
        names = [prefix + key for key in ('USER', 'PASSWORD', 'CLUSTER')]
        values = [os.getenv(name, '') for name in names]
        missing = [name for name, value in zip(names, values) if not value]
        if missing:
            raise ConfigurationError('Faltan variables: ' + ', '.join(missing))
        user, password, cluster = values
        if any(token in cluster for token in ('/', '@', '?', '#', ':')):
            raise ConfigurationError('El host de Atlas no es válido en ' + prefix + 'CLUSTER.')
        uri = f'mongodb+srv://{quote_plus(user)}:{quote_plus(password)}@{cluster}'
    return MongoSettings(uri=uri, database=database, analytics=analytics)


def mongo_settings(*, analytics=False):
    settings = _connection(analytics)
    if analytics:
        core = _connection(False)
        if settings.database == core.database:
            raise ConfigurationError('La base analítica debe ser distinta de la base operativa.')
    return settings


def connect_mongo(*, analytics=False):
    load_environment()
    settings = mongo_settings(analytics=analytics)
    client = MongoClient(
        settings.uri,
        appname='UrbanBladeAnalyticsDerived' if analytics else 'UrbanBladeAnalyticsCore',
        connect=False,
        serverSelectionTimeoutMS=8000,
        connectTimeoutMS=8000,
        socketTimeoutMS=20000,
        maxPoolSize=10,
        retryWrites=analytics,
    )
    return client, settings.database


def require_write_opt_in(variable):
    if variable not in {'ALLOW_ANALYTICS_PUBLICATION', 'ALLOW_SYNTHETIC_WRITES'}:
        raise ConfigurationError('Habilitación de escritura no reconocida.')
    if os.getenv(variable, '').lower() != 'true':
        raise ConfigurationError('Operación de escritura bloqueada; falta habilitación ' + variable + '. ')


def validate_local_test_target(uri, database):
    """Los fixtures con escritura nunca aceptan Atlas, aunque la base termine en _e2e."""
    try:
        parsed = urlsplit(uri)
        valid = (parsed.scheme == 'mongodb' and parsed.hostname in {'localhost', '127.0.0.1', '::1'}
                 and database.endswith('_e2e') and len(database) > 4
                 and not parsed.username and not parsed.password)
    except (ValueError, AttributeError):
        valid = False
    if not valid:
        raise ConfigurationError('Los fixtures requieren Mongo local sin credenciales y una base propia *_e2e.')


def data_source_label():
    """Descripción visible de la conexión; nunca incluye URI, usuario o contraseña."""
    load_environment()
    settings = mongo_settings()
    host = urlsplit(settings.uri).hostname
    if host in {'localhost', '127.0.0.1', '::1', 'mongo-dev', 'barber-mongo-dev', 'host.docker.internal'}:
        kind = 'MongoDB local'
    elif host and host.endswith('.mongodb.net'):
        kind = 'MongoDB Atlas'
    else:
        kind = 'MongoDB remoto'
    return kind + ' · ' + settings.database
