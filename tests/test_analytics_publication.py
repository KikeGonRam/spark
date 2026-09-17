import unittest
from unittest.mock import MagicMock

from config.analytics_publication import publish_insights_atomically


class AnalyticsPublicationTest(unittest.TestCase):
    def test_publishes_through_a_temporary_collection(self):
        db = MagicMock()
        temporary = MagicMock()
        db.__getitem__.return_value = temporary

        count = publish_insights_atomically(db, [{"tipo": "demo"}])

        self.assertEqual(1, count)
        db.create_collection.assert_called_once()
        temporary.insert_many.assert_called_once_with([{"tipo": "demo"}], ordered=True)
        temporary.rename.assert_called_once_with("analytics_insights", dropTarget=True)
        db.drop_collection.assert_not_called()

    def test_removes_only_the_temporary_collection_when_publish_fails(self):
        db = MagicMock()
        temporary = MagicMock()
        temporary.insert_many.side_effect = RuntimeError("fallo controlado")
        db.__getitem__.return_value = temporary

        with self.assertRaisesRegex(RuntimeError, "fallo controlado"):
            publish_insights_atomically(db, [{"tipo": "demo"}])

        db.drop_collection.assert_called_once()
        temporary.rename.assert_not_called()


if __name__ == "__main__":
    unittest.main()
