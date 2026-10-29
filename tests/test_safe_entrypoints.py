import contextlib
import importlib
import io
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from config.analytics_publication import publish_insights_atomically
from config.settings import ConfigurationError
from data_ingestion import generar_datos_urbanblade as synthetic


ROOT = Path(__file__).resolve().parents[1]


class SafeEntrypointTest(unittest.TestCase):
    def test_importing_analysis_and_publication_does_not_connect(self):
        modules = ['pipelines.publicar_insights', 'dashboard.dashboard_matplotlib'] + [
            '.'.join(path.relative_to(ROOT).with_suffix('').parts)
            for path in (ROOT / 'analytics').rglob('*.py') if path.name != '__init__.py'
        ]
        self.assertGreater(len(modules), 20)
        with patch('config.settings.MongoClient') as client:
            for module in modules:
                importlib.import_module(module)
            client.assert_not_called()

    def test_synthetic_generation_is_reproducible_and_dry_by_default(self):
        expected = synthetic.generate_records(5, 7)
        self.assertEqual(expected, synthetic.generate_records(5, 7))
        self.assertNotEqual(expected, synthetic.generate_records(5, 8))
        with patch.object(synthetic, 'connect_mongo') as client:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(synthetic.main(['--count', '5']), 0)
            self.assertIn('"written": false', output.getvalue())
            client.assert_not_called()

    def test_synthetic_write_is_blocked_before_connecting(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(synthetic, 'load_environment'), \
             patch.object(synthetic, 'connect_mongo') as client:
            with self.assertRaises(ConfigurationError):
                synthetic.main(['--apply', '--count', '2'])
            client.assert_not_called()

    def test_empty_snapshot_does_not_erase_last_known_insights(self):
        db = MagicMock()
        db.name = 'analytics_e2e'
        with self.assertRaises(ValueError):
            publish_insights_atomically(db, [])
        db.create_collection.assert_not_called()

    def test_publication_cannot_target_operational_database_or_arbitrary_collection(self):
        db = MagicMock()
        db.name = 'barber_db'
        with self.assertRaises(ValueError):
            publish_insights_atomically(db, [{'tipo': 'synthetic'}])
        db.name = 'analytics_e2e'
        with self.assertRaises(ValueError):
            publish_insights_atomically(db, [{'tipo': 'synthetic'}], target_collection='users')
        db.create_collection.assert_not_called()


if __name__ == '__main__':
    unittest.main()
