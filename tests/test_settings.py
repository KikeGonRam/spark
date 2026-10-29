import contextlib
import io
import os
import unittest
from unittest.mock import patch

from config import diagnostics
from config.settings import ConfigurationError, connect_mongo, mongo_settings, require_write_opt_in


BASE = {
    'CORE_MONGODB_URI': 'mongodb://reader:private-password@localhost:27017/core_e2e',
    'MONGO_DB': 'core_e2e',
    'ANALYTICS_MONGODB_URI': 'mongodb://writer:private-password@localhost:27017/analytics_e2e',
    'ANALYTICS_MONGO_DB': 'analytics_e2e',
}


class SettingsTest(unittest.TestCase):
    def test_validates_separate_connections_without_connecting(self):
        with patch.dict(os.environ, BASE, clear=True):
            self.assertEqual(mongo_settings().database, 'core_e2e')
            self.assertEqual(mongo_settings(analytics=True).database, 'analytics_e2e')

    def test_database_can_be_inferred_from_explicit_uri(self):
        with patch.dict(os.environ, {'CORE_MONGODB_URI': BASE['CORE_MONGODB_URI']}, clear=True):
            self.assertEqual(mongo_settings().database, 'core_e2e')

    def test_uri_cannot_disagree_with_database_name(self):
        with patch.dict(os.environ, {**BASE, 'MONGO_DB': 'different_e2e'}, clear=True):
            with self.assertRaises(ConfigurationError):
                mongo_settings()

    def test_derived_connection_cannot_target_core(self):
        with patch.dict(os.environ, {**BASE, 'ANALYTICS_MONGODB_URI': BASE['CORE_MONGODB_URI'],
                                    'ANALYTICS_MONGO_DB': 'core_e2e'}, clear=True):
            with self.assertRaises(ConfigurationError):
                mongo_settings(analytics=True)

    def test_missing_configuration_never_falls_back_to_privileged_legacy_uri(self):
        with patch.dict(os.environ, {'MONGODB_URI': BASE['CORE_MONGODB_URI']}, clear=True):
            with self.assertRaises(ConfigurationError):
                mongo_settings()

    def test_credentials_are_hidden_in_repr_and_errors(self):
        with patch.dict(os.environ, BASE, clear=True):
            self.assertNotIn('private-password', repr(mongo_settings()))
        with patch.dict(os.environ, {'CORE_MONGODB_URI': 'bad:private-password'}, clear=True):
            with self.assertRaises(ConfigurationError) as caught:
                mongo_settings()
            self.assertNotIn('private-password', str(caught.exception))

    def test_reserved_databases_are_rejected(self):
        for name in ('admin', 'config', 'local'):
            with self.subTest(name=name), patch.dict(os.environ, {'CORE_MONGODB_URI': f'mongodb://localhost/{name}'}, clear=True):
                with self.assertRaises(ConfigurationError):
                    mongo_settings()

    @patch('config.settings.load_environment')
    @patch('config.settings.MongoClient')
    def test_client_is_lazy_bounded_and_core_does_not_retry_writes(self, client, _load):
        with patch.dict(os.environ, BASE, clear=True):
            connect_mongo()
        self.assertFalse(client.call_args.kwargs['connect'])
        self.assertFalse(client.call_args.kwargs['retryWrites'])
        self.assertEqual(client.call_args.kwargs['serverSelectionTimeoutMS'], 8000)

    def test_writes_require_a_recognized_explicit_opt_in(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigurationError):
                require_write_opt_in('ALLOW_ANALYTICS_PUBLICATION')
        with patch.dict(os.environ, {'ALLOW_ANALYTICS_PUBLICATION': 'true'}, clear=True):
            require_write_opt_in('ALLOW_ANALYTICS_PUBLICATION')
            with self.assertRaises(ConfigurationError):
                require_write_opt_in('UNRECOGNIZED_FLAG')

    def test_read_only_privilege_check_rejects_writers_and_unknown_privileges(self):
        def status(actions):
            return {'authInfo': {'authenticatedUserPrivileges': [{'resource': {'db': 'core_e2e'}, 'actions': actions}]}}
        self.assertTrue(diagnostics.core_is_read_only(status(['find', 'listCollections']), 'core_e2e'))
        self.assertFalse(diagnostics.core_is_read_only(status(['find', 'insert']), 'core_e2e'))
        self.assertFalse(diagnostics.core_is_read_only({}, 'core_e2e'))

    @patch('config.diagnostics.load_environment')
    def test_configuration_diagnostic_never_connects_by_default(self, _load):
        with patch.dict(os.environ, BASE, clear=True), patch('config.diagnostics.connect_mongo') as client:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(diagnostics.main([]), 0)
            client.assert_not_called()
            self.assertNotIn('private-password', output.getvalue())


if __name__ == '__main__':
    unittest.main()
