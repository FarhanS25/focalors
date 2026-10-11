import inspect
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import (
    annotate_scenario,
    base_network,
    farthest_point_ids,
    investigate,
    matching_rmse,
    nearest_time,
    pipe_sort_key,
    rank_signatures,
    select_candidate_pipes,
    select_sensors,
)


class RankingTests(unittest.TestCase):
    def test_rmse_is_root_mean_square_not_a_probability(self):
        error = matching_rmse(np.array([0.0, 0.0]), np.array([3.0, 4.0]))
        self.assertAlmostEqual(error, (12.5) ** 0.5)

    def test_nonfinite_signatures_are_rejected(self):
        with self.assertRaises(ValueError):
            matching_rmse(np.array([1.0, np.nan]), np.array([1.0, 0.0]))

    def test_rank_orders_by_error_and_ignores_scenario_labels(self):
        rows = rank_signatures(
            np.array([1.0, -2.0, 0.5]),
            {
                "bad": np.array([0.0, 0.0, 0.0]),
                "exact": np.array([1.0, -2.0, 0.5]),
                "mid": np.array([1.0, -2.0, 0.0]),
            },
        )
        self.assertEqual([row["pipe_id"] for row in rows], ["exact", "mid", "bad"])
        self.assertEqual(rows[0]["matching_error"], 0.0)
        self.assertEqual([row["rank"] for row in rows], [1, 2, 3])
        self.assertNotIn("is_ground_truth", rows[0])

        rank = annotate_scenario(rows, "bad")
        self.assertEqual([row["pipe_id"] for row in rows], ["exact", "mid", "bad"])
        self.assertEqual(rank, 3)
        self.assertTrue(rows[2]["is_ground_truth"])
        self.assertFalse(rows[0]["is_ground_truth"])

    def test_equal_errors_tie_break_by_pipe_id_not_by_a_favored_label(self):
        rows = rank_signatures(
            np.zeros(2),
            {"20": np.array([1.0, 0.0]), "10": np.array([0.0, 1.0])},
        )
        self.assertEqual([row["pipe_id"] for row in rows], ["10", "20"])
        self.assertAlmostEqual(rows[0]["matching_error"], rows[1]["matching_error"])
        annotate_scenario(rows, "20")
        self.assertEqual(rows[1]["rank"], 2)
        self.assertTrue(rows[1]["is_ground_truth"])

    def test_ranking_functions_do_not_accept_a_leak_argument(self):
        for function in (rank_signatures, select_candidate_pipes, select_sensors):
            names = " ".join(inspect.signature(function).parameters)
            self.assertNotIn("leak", names)

    def test_nearest_snapshot_stays_inside_half_a_timestep(self):
        index = np.array([0, 3600, 7200])
        self.assertEqual(nearest_time(index, 7200, 3600), (2, 7200.0))
        self.assertEqual(nearest_time(index, 5000, 3600)[0], 1)
        with self.assertRaises(RuntimeError):
            nearest_time(index, 10000, 3600)


class SelectionTests(unittest.TestCase):
    def test_farthest_point_reaches_the_remote_site(self):
        points = {
            "sw": (0.0, 0.0),
            "nw": (0.0, 1.0),
            "se": (1.0, 0.0),
            "ne": (1.0, 1.0),
            "remote": (10.0, 10.0),
        }
        chosen = farthest_point_ids(points, 2)
        self.assertEqual(chosen[0], "ne")
        self.assertIn("remote", chosen)
        self.assertEqual(farthest_point_ids(points, 4), farthest_point_ids(points, 4))

    def test_candidate_sample_is_stable_and_does_not_grow_to_fit_a_caller(self):
        wn = base_network()
        sample = select_candidate_pipes(wn, 10)
        self.assertEqual(sample, select_candidate_pipes(wn, 10))
        self.assertEqual(len(sample), 10)
        self.assertEqual(len(set(sample)), 10)
        self.assertEqual(sample, sorted(sample, key=pipe_sort_key))
        everything = select_candidate_pipes(wn, None)
        self.assertEqual(len(everything), 117)
        self.assertTrue(set(sample).issubset(everything))
        self.assertEqual(select_candidate_pipes(wn, 500), everything)

    def test_sensors_prefer_pressurized_junctions_and_are_unique(self):
        wn = base_network()
        pressures = {str(name): 40.0 for name in wn.junction_name_list}
        sensors = select_sensors(wn, pressures, 5)
        self.assertEqual(len(set(sensors)), 5)
        self.assertEqual(sensors, select_sensors(wn, pressures, 5))
        pressures[sensors[0]] = 0.0
        self.assertNotIn(sensors[0], select_sensors(wn, pressures, 5))


class HydraulicTests(unittest.TestCase):
    def test_pipe_329_leak_is_measurable_and_every_pipe_stays_eligible(self):
        """One leak and five sensors. The ranker is not given the scenario pipe."""
        result = investigate(
            leak_pipe="329",
            leak_area_m2=1e-4,
            sensor_count=5,
            candidate_limit=1,
            sample_time_s=7200,
        )
        signature = np.array(result["signature"], dtype=float)
        self.assertEqual(len(result["sensors"]), 5)
        self.assertEqual(result["signature"], [sensor["delta_pressure"] for sensor in result["sensors"]])
        self.assertGreater(result["observed_signal_max_abs_m"], 1e-3)
        self.assertGreater(float(np.std(signature)), 1e-4)
        self.assertFalse(result["ranking_uses_leak_identity"])
        self.assertEqual(result["leak_pipe"], "329")
        names = " ".join(inspect.signature(select_candidate_pipes).parameters)
        self.assertNotIn("leak", names)
        pipes = [str(pipe) for pipe in base_network().pipe_name_list]
        chosen = select_candidate_pipes(base_network(), None)
        self.assertIn("329", chosen)
        self.assertEqual(chosen, sorted(pipes, key=pipe_sort_key))
        self.assertEqual(len(result["candidate_pipe_ids"]), 1)
        if result["true_pipe_in_candidate_set"]:
            self.assertEqual(result["actual_pipe_rank"], 1)
        else:
            self.assertIsNone(result["actual_pipe_rank"])
            self.assertNotIn("329", result["candidate_pipe_ids"])

    def test_unknown_pipe_and_early_sample_fail_before_a_misleading_rank(self):
        with self.assertRaises(ValueError):
            investigate(leak_pipe="not-a-pipe", candidate_limit=2)
        with self.assertRaises(ValueError):
            investigate(leak_pipe="329", sample_time_s=10, candidate_limit=2)

    def test_candidate_set_does_not_depend_on_or_insert_the_leak(self):
        wn = base_network()
        selected = select_candidate_pipes(wn, 3)
        pipes = [str(pipe) for pipe in wn.pipe_name_list]
        outsiders = [pipe for pipe in pipes if pipe not in selected]
        self.assertGreaterEqual(len(outsiders), 2)
        first = investigate(leak_pipe=outsiders[0], candidate_limit=3, sensor_count=5, sample_time_s=7200)
        second = investigate(leak_pipe=outsiders[1], candidate_limit=3, sensor_count=5, sample_time_s=7200)

        self.assertEqual(first["candidate_pipe_ids"], selected)
        self.assertEqual(second["candidate_pipe_ids"], selected)
        self.assertNotIn(outsiders[0], first["candidate_pipe_ids"])
        self.assertNotIn(outsiders[1], second["candidate_pipe_ids"])
        self.assertIsNone(first["actual_pipe_rank"])
        self.assertFalse(first["true_pipe_in_candidate_set"])
        self.assertFalse(first["ranking_uses_leak_identity"])
        self.assertEqual(
            [sensor["junction"] for sensor in first["sensors"]],
            [sensor["junction"] for sensor in second["sensors"]],
        )
        self.assertGreater(
            np.max(np.abs(np.array(first["signature"]) - np.array(second["signature"]))),
            1e-6,
        )
        self.assertEqual(
            first["signature"],
            [sensor["delta_pressure"] for sensor in first["sensors"]],
        )

    def test_resimulated_candidate_matches_the_observation(self):
        selected = select_candidate_pipes(base_network(), 4)
        leak_pipe = selected[0]
        result = investigate(leak_pipe=leak_pipe, candidate_limit=4, sensor_count=5, sample_time_s=7200)
        self.assertEqual(result["candidate_pipe_ids"], selected)
        matches = [row for row in result["candidates"] if row["pipe_id"] == leak_pipe]
        self.assertEqual(len(matches), 1, msg=result["failures"])
        self.assertLess(matches[0]["matching_error"], 1e-5)
        near_zero = [row for row in result["candidates"] if row["matching_error"] <= 1e-5]
        self.assertIn(leak_pipe, [row["pipe_id"] for row in near_zero])
        self.assertLessEqual(result["candidates"][0]["matching_error"], 1e-5)

    def test_full_network_search_recovers_the_generating_signature(self):
        result = investigate(leak_pipe="329", candidate_limit=None, sensor_count=5, sample_time_s=7200)
        self.assertEqual(len(result["candidate_pipe_ids"]), 117)
        self.assertEqual(result["candidate_count"] + len(result["failures"]), 117)
        self.assertTrue(result["true_pipe_in_candidate_set"])
        matches = [row for row in result["candidates"] if row["pipe_id"] == "329"]
        self.assertEqual(len(matches), 1, msg=result["failures"])
        self.assertLess(
            matches[0]["matching_error"],
            1e-5,
            msg=f"top={result['candidates'][:5]} failures={result['failures'][:3]}",
        )
        # Same-model resimulation is numerically identical, so this scenario is rank 1.
        # The engine does not special-case pipe 329; the gap to the next pipe is the check.
        self.assertEqual(matches[0]["rank"], 1)
        self.assertGreater(result["candidates"][1]["matching_error"], 1e-4)
        self.assertLessEqual(result["candidates"][0]["matching_error"], 1e-5)
        self.assertGreater(result["observed_signal_max_abs_m"], 1e-4)
        self.assertFalse(result["demonstration"]["field_validated"])


if __name__ == "__main__":
    unittest.main()
