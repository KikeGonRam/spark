"""Diagnóstico explícito de conexión; no consulta registros ni modifica datos."""

import argparse
import json

from config.settings import connect_mongo, load_environment, mongo_settings


READ_ONLY_ACTIONS = {
    'find', 'changeStream', 'collStats', 'dbHash', 'dbStats', 'indexStats',
    'killCursors', 'listCollections', 'listIndexes', 'planCacheRead',
    'listSearchIndexes', 'getMore',
}


def core_is_read_only(status, database):
    privileges = status.get('authInfo', {}).get('authenticatedUserPrivileges', [])
    relevant = [p for p in privileges if p.get('resource', {}).get('db') in {'', database}
                or p.get('resource', {}).get('anyResource')]
    actions = {a for privilege in relevant for a in privilege.get('actions', [])}
    return 'find' in actions and actions.issubset(READ_ONLY_ACTIONS)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', help='Archivo privado de configuración.')
    parser.add_argument('--connect', action='store_true', help='Ping y privilegios efectivos; sin leer registros.')
    args = parser.parse_args(argv)
    client = None
    try:
        load_environment(args.env_file)
        core = mongo_settings()
        derived = mongo_settings(analytics=True)
        result = {'configuration_valid': True, 'databases_separate': core.database != derived.database}
        if args.connect:
            client, database = connect_mongo()
            client[database].command('ping')
            status = client[database].command({'connectionStatus': 1, 'showPrivileges': True})
            result.update(connected=True, core_read_only=core_is_read_only(status, database))
        print(json.dumps(result))
        return 0 if result.get('core_read_only', True) else 1
    except Exception as error:
        # Driver exceptions can contain hosts and credentials: expose only the type.
        print(json.dumps({'configuration_valid': False, 'error_type': type(error).__name__}))
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == '__main__':
    raise SystemExit(main())
