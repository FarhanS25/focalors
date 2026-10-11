import json
import os
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from engine import investigate
from tests.memory_mongo import DownClient, MemoryClient


class DatabaseTests(unittest.TestCase):
    def tearDown(self):
        database.reset_client()

    def test_numpy_values_are_bson_safe(self):
        payload = {
            "signature": np.array([1.25, np.float64(-0.5)]),
            "rank": np.int64(3),
            "flag": np.bool_(True),
            "nested": {"area": np.float64(0.0001)},
        }
        clean = database.to_bson(payload)
        json.dumps(clean)
        self.assertEqual(clean["signature"], [1.25, -0.5])
        self.assertEqual(clean["rank"], 3)
        self.assertIs(clean["flag"], True)
        self.assertEqual(clean["nested"]["area"], 0.0001)

    def test_non_finite_numbers_are_rejected(self):
        with self.assertRaises(database.DatabaseError):
            database.to_bson({"value": float("nan")})

    def test_unconfigured_database_is_reported_without_pretending_success(self):
        previous = os.environ.pop("MONGODB_URI", None)
        database.reset_client()
        try:
            report = database.ping()
            self.assertEqual(report["status"], "unavailable")
            self.assertFalse(report["configured"])
            self.assertNotIn("mongodb+srv://", json.dumps(report))
            with self.assertRaises(database.DatabaseConfigurationError):
                database.save_result({"leak_pipe": "329", "candidates": []})
        finally:
            if previous is not None:
                os.environ["MONGODB_URI"] = previous

    def test_connection_failure_does_not_leak_credentials_or_fake_an_id(self):
        database.install_client(DownClient())
        report = database.ping()
        self.assertEqual(report["status"], "unavailable")
        self.assertNotIn("secret", json.dumps(report))
        with self.assertRaises(database.DatabaseUnavailableError) as caught:
            database.save_result({
                "leak_pipe": "329",
                "leak_area_m2": 0.0001,
                "candidate_count": 0,
                "candidates": [],
                "sensors": [],
                "signature": [],
            })
        self.assertNotIn("secret", str(caught.exception))
        self.assertNotIn("mongodb+srv", str(caught.exception))

    def test_real_simulation_round_trip_keeps_ground_truth_out_of_predictions(self):
        """Uses an in-memory Mongo double. This does not contact Atlas."""
        database.install_client(MemoryClient())
        result = investigate(leak_pipe="329", candidate_limit=2, sensor_count=5, sample_time_s=7200)
        stored = database.build_document(result)
        json.dumps(database.to_bson(result))
        self.assertEqual(stored["evaluation"]["leak_pipe"], "329")
        self.assertEqual(stored["status"], "completed")
        self.assertTrue(stored["sensors"])
        self.assertEqual(stored["signature"], [row["delta_pressure"] for row in stored["sensors"]])
        for prediction in stored["predictions"]:
            self.assertNotIn("is_ground_truth", prediction)
            self.assertNotIn("leak_pipe", prediction)
            self.assertIn("matching_error", prediction)

        run_id = database.save_result(result)
        self.assertIsInstance(run_id, str)
        self.assertTrue(run_id)
        runs = database.recent_runs(5)
        self.assertEqual(runs[0]["id"], run_id)
        self.assertEqual(runs[0]["leak_pipe"], "329")
        self.assertEqual(runs[0]["status"], "completed")
        self.assertIn("created_at", runs[0])
        saved = database.collection().documents[-1]
        self.assertEqual(saved["evaluation"]["leak_pipe"], "329")
        self.assertNotIn("is_ground_truth", saved["predictions"][0])
        self.assertIn("created_at_desc", database.collection().indexes)

    def test_atlas_ping_when_credentials_are_configured(self):
        uri = os.environ.get("MONGODB_URI", "").strip()
        if not uri:
            self.skipTest("MONGODB_URI is not set. Atlas was not contacted.")
        database.reset_client()
        report = database.ping()
        self.assertEqual(report["status"], "ok", msg=report.get("detail"))
        self.assertNotIn(uri, json.dumps(report))


if __name__ == "__main__":
    unittest.main()
