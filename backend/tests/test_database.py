import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

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
        with self.assertRaises(database.DatabaseError):
            database.to_bson({"value": float("inf")})

    def test_datetimes_and_nested_lists_stay_bson_safe(self):
        moment = datetime(2026, 10, 11, 8, 0, tzinfo=timezone.utc)
        clean = database.to_bson({"when": moment, "rows": [{"delta": np.float64(1.5)}]})
        self.assertEqual(clean["when"], moment)
        self.assertEqual(clean["rows"], [{"delta": 1.5}])
        json.dumps({key: value for key, value in clean.items() if key != "when"})

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

    def test_database_name_prefers_mongodb_database(self):
        previous_database = os.environ.get("MONGODB_DATABASE")
        previous_db = os.environ.get("MONGODB_DB")
        os.environ["MONGODB_DATABASE"] = "focalors_named"
        os.environ["MONGODB_DB"] = "other_name"
        try:
            self.assertEqual(database.db_name(), "focalors_named")
            os.environ.pop("MONGODB_DATABASE")
            self.assertEqual(database.db_name(), "other_name")
            os.environ.pop("MONGODB_DB")
            self.assertEqual(database.db_name(), "focalors")
        finally:
            if previous_database is None:
                os.environ.pop("MONGODB_DATABASE", None)
            else:
                os.environ["MONGODB_DATABASE"] = previous_database
            if previous_db is None:
                os.environ.pop("MONGODB_DB", None)
            else:
                os.environ["MONGODB_DB"] = previous_db

    def test_check_connection_matches_ping_and_hides_configuration_details(self):
        previous = os.environ.pop("MONGODB_URI", None)
        database.reset_client()
        try:
            report = database.check_connection()
            self.assertEqual(report, database.ping())
            self.assertEqual(report["status"], "unavailable")
            self.assertFalse(report["configured"])
            self.assertNotIn("mongodb+srv://", json.dumps(report))
        finally:
            if previous is not None:
                os.environ["MONGODB_URI"] = previous

    def test_check_connection_reports_failure_without_credentials(self):
        """DownClient is a test double. This does not contact Atlas."""
        database.install_client(DownClient())
        report = database.check_connection()
        self.assertEqual(report["status"], "unavailable")
        self.assertTrue(report["configured"])
        self.assertEqual(report["detail"], "Could not reach MongoDB.")
        self.assertNotIn("secret", json.dumps(report))
        self.assertNotIn("mongodb+srv", json.dumps(report))

    def test_recent_runs_are_sorted_newest_first_and_limit_is_validated(self):
        """Inserts plain documents into the in-memory double. This does not contact Atlas."""
        database.install_client(MemoryClient())
        collection = database.collection()
        collection.insert_one({
            "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "status": "completed",
            "candidate_count": 2,
            "evaluation": {"leak_pipe": "older", "actual_pipe_rank": 2},
            "configuration": {"leak_area_m2": 0.0001},
            "predictions": [{"pipe_id": "10", "matching_error": 0.2, "rank": 1}],
        })
        collection.insert_one({
            "created_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
            "status": "completed",
            "candidate_count": 3,
            "evaluation": {"leak_pipe": "newer", "actual_pipe_rank": 1},
            "configuration": {"leak_area_m2": 0.0001},
            "predictions": [{"pipe_id": "20", "matching_error": 0.1, "rank": 1}],
        })
        runs = database.recent_runs(1)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["leak_pipe"], "newer")
        self.assertEqual(runs[0]["created_at"], "2025-06-01 00:00:00")
        self.assertNotIn("is_ground_truth", collection.documents[-1]["predictions"][0])
        ordered = database.recent_runs(20)
        self.assertEqual([item["leak_pipe"] for item in ordered], ["newer", "older"])
        with self.assertRaises(ValueError):
            database.recent_runs(0)
        with self.assertRaises(ValueError):
            database.recent_runs(101)

    def test_naive_utc_timestamps_are_not_shifted_to_local_time(self):
        """PyMongo returns naive UTC datetimes unless the client is timezone-aware."""
        database.install_client(MemoryClient())
        database.collection().insert_one({
            "created_at": datetime(2025, 6, 1, 12, 0, 0),
            "status": "completed",
            "candidate_count": 1,
            "evaluation": {"leak_pipe": "329", "actual_pipe_rank": 1},
            "configuration": {"leak_area_m2": 0.0001},
            "predictions": [{"pipe_id": "329", "matching_error": 0.0, "rank": 1}],
        })
        runs = database.recent_runs(1)
        self.assertEqual(runs[0]["created_at"], "2025-06-01 12:00:00")

    def test_env_file_is_loaded_from_the_module_directory(self):
        recorded = []

        def capture(path, override=False):
            recorded.append((Path(path).resolve(), override))
            return False

        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            try:
                with patch("dotenv.load_dotenv", side_effect=capture):
                    database.load_env()
            finally:
                os.chdir(previous)
        backend_env = Path(database.__file__).resolve().parent / ".env"
        root_env = backend_env.parent.parent / ".env"
        self.assertEqual(recorded[0], (backend_env.resolve(), False))
        self.assertEqual(recorded[1], (root_env.resolve(), False))
        self.assertNotEqual(recorded[0][0].parent, Path(directory).resolve())

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
