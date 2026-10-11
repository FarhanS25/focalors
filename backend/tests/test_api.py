import json
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
    def assert_hides_ground_truth(self, payload, leak_pipe):
        hidden = {"leak_pipe", "actual_pipe_rank", "true_pipe_in_candidate_set", "is_ground_truth"}

        def walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertNotIn(key, hidden)
                    walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(payload)
        serialized = json.dumps(payload)
        self.assertNotIn('"leak_pipe"', serialized)
        self.assertNotIn('"is_ground_truth"', serialized)
        self.assertNotIn('"actual_pipe_rank"', serialized)
        self.assertNotIn('"true_pipe_in_candidate_set"', serialized)
        if leak_pipe is not None:
            self.assertNotIn(f'"leak_pipe": "{leak_pipe}"', serialized)
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
        self.assertEqual(self.client.get("/api/runs?view=audit").status_code, 422)
        rejected = self.client.post("/api/simulate", json={"view": "audit", "candidate_limit": 2})
        self.assertEqual(rejected.status_code, 422)

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
        self.assertEqual(payload["view"], "investigation")
        self.assert_hides_ground_truth(payload, outsider)
        self.assertNotIn(f'"{outsider}"', response.text)
        self.assertEqual(payload["candidate_pipe_ids"], selected)
        self.assertNotIn(outsider, payload["candidate_pipe_ids"])
        self.assertFalse(payload["ranking_uses_leak_identity"])
        self.assertEqual(len(payload["sensors"]), 5)
        self.assertIn("not a probability", " ".join(payload["notes"]).lower())
        self.assertFalse(payload["demonstration"]["field_validated"])
        self.assertIsInstance(payload["run_id"], str)
        self.assertTrue(payload["run_id"])
        for candidate in payload["candidates"]:
            self.assertNotIn("is_ground_truth", candidate)

        stored = database.load_run(payload["run_id"])
        self.assertEqual(stored["evaluation"]["leak_pipe"], outsider)
        self.assertNotIn("is_ground_truth", stored["predictions"][0])

        hidden = self.client.get("/api/runs?limit=5")
        self.assertEqual(hidden.status_code, 200)
        hidden_body = hidden.json()
        self.assertEqual(hidden_body["view"], "investigation")
        self.assertGreaterEqual(len(hidden_body["runs"]), 1)
        self.assertEqual(hidden_body["runs"][0]["id"], payload["run_id"])
        self.assert_hides_ground_truth(hidden_body, outsider)
        self.assertNotIn(f'"{outsider}"', hidden.text)
        self.assertEqual(hidden_body["runs"][0]["status"], "completed")

        revealed = self.client.get("/api/runs?limit=5&view=evaluation")
        self.assertEqual(revealed.status_code, 200)
        self.assertEqual(revealed.json()["runs"][0]["leak_pipe"], outsider)
        self.assertIsNone(revealed.json()["runs"][0]["actual_pipe_rank"])

        evaluation = self.client.get(f"/api/runs/{payload['run_id']}?view=evaluation")
        self.assertEqual(evaluation.status_code, 200)
        evaluated = evaluation.json()
        self.assertEqual(evaluated["view"], "evaluation")
        self.assertEqual(evaluated["leak_pipe"], outsider)
        self.assertIsNone(evaluated["actual_pipe_rank"])
        self.assertFalse(evaluated["true_pipe_in_candidate_set"])
        self.assertTrue(all("is_ground_truth" in row for row in evaluated["candidates"]))
        self.assertTrue(all(row["is_ground_truth"] is False for row in evaluated["candidates"]))
        investigation_rank = [(row["pipe_id"], row["matching_error"], row["rank"]) for row in payload["candidates"]]
        evaluation_rank = [(row["pipe_id"], row["matching_error"], row["rank"]) for row in evaluated["candidates"]]
        self.assertEqual(investigation_rank, evaluation_rank)

        again = self.client.get(f"/api/runs/{payload['run_id']}")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["view"], "investigation")
        self.assert_hides_ground_truth(again.json(), outsider)
        self.assertNotIn(f'"{outsider}"', again.text)
        self.assertEqual(self.client.get("/api/runs/not-a-run").status_code, 404)

    def test_evaluation_view_returns_labels_without_changing_rank(self):
        original = main.investigate

        def finished(*_args, **_kwargs):
            return {
                "leak_pipe": "329",
                "actual_pipe_rank": 2,
                "true_pipe_in_candidate_set": True,
                "ranking_uses_leak_identity": False,
                "candidate_count": 2,
                "candidates": [
                    {"pipe_id": "20", "matching_error": 0.1, "rank": 1, "is_ground_truth": False},
                    {"pipe_id": "329", "matching_error": 0.4, "rank": 2, "is_ground_truth": True},
                ],
                "sensors": [],
                "signature": [],
            }

        main.investigate = finished
        try:
            response = self.client.post(
                "/api/simulate",
                json={"view": "evaluation", "leak_pipe": "329", "candidate_limit": 2},
            )
        finally:
            main.investigate = original
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assertEqual(body["view"], "evaluation")
        self.assertEqual(body["leak_pipe"], "329")
        self.assertEqual(body["actual_pipe_rank"], 2)
        self.assertTrue(body["true_pipe_in_candidate_set"])
        self.assertEqual(
            [(row["pipe_id"], row["rank"]) for row in body["candidates"]],
            [("20", 1), ("329", 2)],
        )
        self.assertFalse(body["candidates"][0]["is_ground_truth"])
        self.assertTrue(body["candidates"][1]["is_ground_truth"])
        stored = database.load_run(body["run_id"])
        self.assertEqual(stored["evaluation"]["leak_pipe"], "329")
        self.assertNotIn("is_ground_truth", stored["predictions"][0])
        hidden = self.client.get(f"/api/runs/{body['run_id']}")
        self.assertEqual(hidden.status_code, 200)
        self.assert_hides_ground_truth(hidden.json(), "329")
        self.assertEqual(
            [(row["pipe_id"], row["rank"]) for row in hidden.json()["candidates"]],
            [("20", 1), ("329", 2)],
        )

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

    def test_health_stays_available_when_mongodb_is_not(self):
        original = main.check_connection

        def unavailable():
            return {
                "status": "unavailable",
                "engine": "mongodb",
                "configured": False,
                "detail": "MONGODB_URI is not set.",
            }

        main.check_connection = unavailable
        try:
            response = self.client.get("/api/health")
        finally:
            main.check_connection = original
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["service"], "FOCALORS API")
        self.assertEqual(body["database"]["status"], "unavailable")
        self.assertNotIn("mongodb+srv", response.text)

    def test_history_failure_is_not_reported_as_an_empty_list(self):
        def fail(limit=20):
            raise DatabaseUnavailableError("Could not read saved runs.")

        original = main.recent_runs
        main.recent_runs = fail
        try:
            response = self.client.get("/api/runs")
        finally:
            main.recent_runs = original
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("runs", response.json())
        self.assertNotIn("secret", response.text)
        self.assertNotIn("traceback", response.text.lower())

        def fail_load(_run_id):
            raise DatabaseUnavailableError("Could not read saved runs.")

        original_load = main.load_run
        main.load_run = fail_load
        try:
            missing = self.client.get("/api/runs/000000000000000000000000?view=evaluation")
        finally:
            main.load_run = original_load
        self.assertEqual(missing.status_code, 503)
        self.assertNotIn("leak_pipe", missing.json())
        self.assertNotIn("secret", missing.text)


if __name__ == "__main__":
    unittest.main()
