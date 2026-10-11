import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import database
from tests.memory_mongo import MemoryClient

database.install_client(MemoryClient())

import main
from database import DatabaseUnavailableError
from engine import base_network, select_candidate_pipes
from fastapi.testclient import TestClient


class ApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["database"]["status"], "ok")
        self.assertEqual(body["database"]["engine"], "mongodb")
        self.assertNotIn("mongodb+srv", response.text)

    def test_network_has_unique_cytoscape_ids(self):
        response = self.client.get("/api/network")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["network"], "Net3")
        self.assertEqual(payload["junction_count"], 92)
        self.assertEqual(payload["pipe_count"], 117)
        elements = payload["elements"]
        ids = [element["data"]["id"] for element in elements]
        self.assertEqual(len(ids), len(set(ids)))
        node_ids = {element["data"]["id"] for element in elements if "position" in element}
        self.assertTrue(node_ids)
        for element in elements:
            data = element["data"]
            if "source" not in data:
                continue
            self.assertIn(data["source"], node_ids)
            self.assertIn(data["target"], node_ids)
            self.assertNotIn(data["id"], node_ids)
            self.assertTrue(data["id"].startswith("link:"))
            self.assertNotEqual(data["id"], data["name"])

    def test_validation_errors_are_readable(self):
        area = self.client.post("/api/simulate", json={"leak_area_m2": 0})
        self.assertEqual(area.status_code, 422)
        self.assertIsInstance(area.json()["detail"], str)
        early = self.client.post("/api/simulate", json={"sample_time_s": 10})
        self.assertEqual(early.status_code, 422)
        self.assertIsInstance(early.json()["detail"], str)
        self.assertEqual(self.client.get("/api/runs?limit=0").status_code, 422)

    def test_unknown_pipe_is_a_client_error(self):
        response = self.client.post("/api/simulate", json={"leak_pipe": "not-a-pipe", "candidate_limit": 2})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Unknown pipe", response.json()["detail"])

    def test_simulate_persists_a_run_without_inserting_the_leak(self):
        selected = select_candidate_pipes(base_network(), 3)
        outsider = next(str(pipe) for pipe in base_network().pipe_name_list if str(pipe) not in selected)
        response = self.client.post(
            "/api/simulate",
            json={
                "leak_pipe": outsider,
                "leak_area_m2": 0.0001,
                "sensor_count": 5,
                "candidate_limit": 3,
                "sample_time_s": 7200,
            },
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        payload = response.json()
        self.assertEqual(payload["leak_pipe"], outsider)
        self.assertEqual(payload["candidate_pipe_ids"], selected)
        self.assertNotIn(outsider, payload["candidate_pipe_ids"])
        self.assertIsNone(payload["actual_pipe_rank"])
        self.assertFalse(payload["ranking_uses_leak_identity"])
        self.assertEqual(len(payload["sensors"]), 5)
        self.assertIn("not a probability", " ".join(payload["notes"]).lower())
        self.assertFalse(payload["demonstration"]["field_validated"])
        self.assertIsInstance(payload["run_id"], str)
        self.assertTrue(payload["run_id"])

        runs = self.client.get("/api/runs?limit=5")
        self.assertEqual(runs.status_code, 200)
        saved = runs.json()["runs"]
        self.assertGreaterEqual(len(saved), 1)
        self.assertEqual(saved[0]["id"], payload["run_id"])
        self.assertEqual(saved[0]["leak_pipe"], outsider)
        self.assertIsNone(saved[0]["actual_pipe_rank"])
        self.assertEqual(saved[0]["status"], "completed")

    def test_storage_failure_is_not_reported_as_success(self):
        original = main.investigate

        def finished(*args, **kwargs):
            return {
                "leak_pipe": "329",
                "leak_area_m2": 0.0001,
                "candidate_count": 1,
                "candidates": [{"pipe_id": "20", "matching_error": 0.1, "rank": 1, "is_ground_truth": False}],
                "sensors": [],
                "signature": [],
            }

        def fail(result):
            raise DatabaseUnavailableError("Could not save the simulation run.")

        main.investigate = finished
        main.save_result = fail
        try:
            response = self.client.post("/api/simulate", json={"leak_pipe": "329", "candidate_limit": 2})
        finally:
            main.investigate = original
            main.save_result = database.save_result
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("run_id", response.json())
        self.assertNotIn("secret", response.text)
        self.assertNotIn("traceback", response.text.lower())


if __name__ == "__main__":
    unittest.main()
