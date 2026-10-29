"""Runtime Spark y UI con datos sintéticos; no necesita .env ni Atlas."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

AVAILABLE = all(importlib.util.find_spec(name) for name in ("pyspark", "streamlit", "pandas"))
ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(AVAILABLE, "Runtime opcional: instalar requirements-dashboard.txt y Java 17.")
class SparkRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pyspark.sql import SparkSession
        from config import mongo_spark_conexion_sinnulos as data
        cls.data = data
        cls.spark = (SparkSession.builder.master("local[2]").appName("UrbanBladeRuntimeTests")
                     .config("spark.ui.enabled", "false")
                     .config("spark.sql.shuffle.partitions", "2").getOrCreate())
        cls.spark.sparkContext.setLogLevel("ERROR")

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()

    def test_empty_dataset_preserves_schema_and_features(self):
        client = MagicMock()
        with patch.object(self.data, "_connect_db", return_value=(client, "core_runtime_e2e")), \
             patch.object(self.data, "_extract_records", return_value=[]):
            spark, df, vector = self.data.get_spark_session()
        self.assertEqual(df.count(), 0)
        self.assertIn("client_id", df.columns)
        self.assertIn("features", vector.columns)
        client.close.assert_called_once()

    def test_nonempty_dataset_runs_vector_assembly(self):
        row = {f.name: ("synthetic" if f.dataType.simpleString() == "string" else
                       0.0 if f.dataType.simpleString() == "double" else 0)
               for f in self.data.RAW_SCHEMA.fields}
        row.update(duracion_min=30.0, precio=100.0, ingreso=100.0, estado="completada")
        with patch.object(self.data, "_connect_db", return_value=(MagicMock(), "core_runtime_e2e")), \
             patch.object(self.data, "_extract_records", return_value=[row]):
            _, df, vector = self.data.get_spark_session()
        self.assertEqual(df.count(), 1)
        self.assertEqual(list(vector.first()["features"]), [30.0, 100.0, 100.0])

    def test_numeric_normalization_handles_decimal_invalid_and_nonfinite_values(self):
        from bson import Decimal128
        self.assertEqual(self.data._num(Decimal128("10.50")), 10.5)
        for value in (None, "invalid", float("nan"), float("inf"), True):
            with self.subTest(value=str(value)):
                self.assertEqual(self.data._num(value), 0.0)

    def test_join_resolves_client_through_client_profile_not_user_id(self):
        from datetime import datetime
        class Collection:
            def __init__(self, records):
                self.records = records
            def find(self, *_args, **_kwargs):
                return self.records
        records = {
            "services": [{"_id": "s", "nombre": "Corte", "precio": 100, "duracion_min": 30}],
            "barbers": [{"_id": "b", "user_id": "ub"}],
            "clients": [{"_id": "c", "user_id": "uc", "puntos": 10}],
            "users": [{"_id": "ub", "name": "Barbero sintético"}, {"_id": "uc", "name": "Cliente sintético"}],
            "appointments": [{"_id": "a", "service_id": "s", "barber_id": "b", "client_id": "c",
                              "estado": "completada", "fecha": datetime(2026, 1, 1), "precio_cobrado": 100}],
        }
        result = self.data._extract_records({key: Collection(value) for key, value in records.items()})
        self.assertEqual(result[0]["cliente"], "Cliente sintético")
        self.assertEqual(result[0]["barbero"], "Barbero sintético")

    def test_login_screen_renders_without_reading_mongo(self):
        from streamlit.testing.v1 import AppTest
        with patch.object(self.data, "_connect_db") as connection:
            app = AppTest.from_file(str(ROOT / "dashboard/app.py")).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.text_input), 2)
        connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
