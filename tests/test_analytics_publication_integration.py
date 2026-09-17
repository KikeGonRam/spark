import os
import unittest
from datetime import datetime, timezone

from pymongo import MongoClient

from config.analytics_publication import publish_insights_atomically


class AnalyticsPublicationIntegrationTest(unittest.TestCase):
    def test_replaces_snapshot_and_preserves_indexes(self):
        uri = os.getenv("ANALYTICS_E2E_URI")
        database = os.getenv("ANALYTICS_E2E_DB")
        if not uri or not database:
            self.skipTest("ANALYTICS_E2E_URI y ANALYTICS_E2E_DB no configuradas")
        if not database.endswith("_e2e"):
            self.fail("La base temporal debe terminar en _e2e")

        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        database_created = False
        try:
            db = client[database]
            db["analytics_insights"].insert_one({"tipo": "anterior"})
            database_created = True
            snapshot = [
                {"tipo": "nuevo_a", "roles": ["administrador"], "generado_en": datetime.now(timezone.utc)},
                {"tipo": "nuevo_b", "roles": ["barbero"], "generado_en": datetime.now(timezone.utc)},
            ]

            self.assertEqual(2, publish_insights_atomically(db, snapshot))
            self.assertEqual({"nuevo_a", "nuevo_b"}, {
                item["tipo"] for item in db["analytics_insights"].find({}, {"tipo": 1})
            })
            self.assertEqual([], [
                name for name in db.list_collection_names()
                if name.startswith("analytics_insights__")
            ])
            self.assertGreaterEqual(len(db["analytics_insights"].index_information()), 4)
        finally:
            if database_created:
                client.drop_database(database)
            client.close()


if __name__ == "__main__":
    unittest.main()
