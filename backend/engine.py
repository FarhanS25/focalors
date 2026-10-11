"""Net3 leak localization with WNTR.

The scenario generator is the only step that knows which pipe was leaked.
Sensor placement, candidate selection, and signature ranking do not receive
that pipe id. After the ranking exists, the id is used only to score this
controlled demonstration. A low score means a candidate reproduces the same
hydraulic model. It is not field-validated detection performance.
"""

import copy
import logging
import threading
import time
import warnings
from functools import lru_cache

import numpy as np
import wntr

logger = logging.getLogger("focalors")

# Net3's pump curves trip a SciPy covariance warning on every solve. The
# hydraulic result is still returned; hiding the warning keeps demo logs usable.
warnings.filterwarnings("ignore", message="Covariance of the parameters could not be estimated")

HYDRAULIC_TIMESTEP_S = 3600
LEAK_START_S = 3600
MAX_DURATION_S = 6 * 3600
REQUIRED_PRESSURE_M = 20.0
MINIMUM_PRESSURE_M = 0.0
DISCHARGE_COEFF = 0.75
MIN_SENSOR_PRESSURE_M = 5.0
PRESSURE_UNIT = "m"

_MODEL_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def base_network():
    """Return the cached, unmodified Net3 model. Callers must copy before editing."""
    try:
        return wntr.network.WaterNetworkModel("Net3")
    except Exception as exc:
        raise RuntimeError(
            "Could not load Net3 from WNTR's model library. "
            f"{type(exc).__name__}: {exc}"
        ) from exc


def fresh_network():
    with _MODEL_LOCK:
        return copy.deepcopy(base_network())


def pipe_sort_key(pipe_id):
    text = str(pipe_id)
    if text.isdigit():
        return (0, int(text), text)
    return (1, text, text)


def matching_rmse(observed, candidate):
    """RMSE of two pressure-change vectors, in meters of head."""
    observed = np.asarray(observed, dtype=float)
    candidate = np.asarray(candidate, dtype=float)
    if observed.shape != candidate.shape or observed.size == 0:
        raise ValueError("Pressure signatures must be non-empty and the same length.")
    if not np.all(np.isfinite(observed)) or not np.all(np.isfinite(candidate)):
        raise ValueError("Pressure signatures must be finite.")
    return float(np.sqrt(np.mean((observed - candidate) ** 2)))


def rank_signatures(observed_delta, candidate_deltas):
    """Rank candidate signatures by RMSE. This function has no leak-pipe argument."""
    rows = []
    for pipe_id, delta in candidate_deltas.items():
        rows.append({
            "pipe_id": str(pipe_id),
            "matching_error": matching_rmse(observed_delta, delta),
        })
    rows.sort(key=lambda row: (row["matching_error"], pipe_sort_key(row["pipe_id"])))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def annotate_scenario(rows, leak_pipe):
    """Label the scenario pipe after sorting. Must not change rank order."""
    order = [row["pipe_id"] for row in rows]
    leak_pipe = str(leak_pipe)
    true_rank = None
    for row in rows:
        is_leak = row["pipe_id"] == leak_pipe
        row["is_ground_truth"] = is_leak
        if is_leak:
            true_rank = row["rank"]
    if [row["pipe_id"] for row in rows] != order:
        raise RuntimeError("Scenario annotation must not reorder rankings.")
    return true_rank


def nearest_time(index, requested_time, step):
    times = np.asarray(index, dtype=float)
    if times.size == 0 or not np.all(np.isfinite(times)):
        raise RuntimeError("Hydraulic results have no usable timestamps.")
    position = int(np.argmin(np.abs(times - float(requested_time))))
    actual = float(times[position])
    half_step = float(step) / 2 + 1e-6
    if abs(actual - float(requested_time)) > half_step:
        raise RuntimeError(
            f"No hydraulic snapshot within half a timestep of {int(requested_time)} s. "
            f"Nearest snapshot is {actual:.0f} s."
        )
    return position, actual


def farthest_point_ids(points, count):
    """Greedy farthest-point sample. Tie breaks are by id, so the result is stable."""
    if count < 1 or count > len(points):
        raise ValueError(f"Cannot choose {count} points from {len(points)}.")

    def distance_squared(left, right):
        return (left[0] - right[0]) ** 2 + (left[1] - right[1]) ** 2

    centroid = (
        sum(point[0] for point in points.values()) / len(points),
        sum(point[1] for point in points.values()) / len(points),
    )
    selected = [min(points, key=lambda name: (distance_squared(points[name], centroid), str(name)))]
    while len(selected) < count:
        chosen = set(selected)

        def spread(name):
            nearest = min(distance_squared(points[name], points[other]) for other in selected)
            return (nearest, str(name))

        selected.append(max((name for name in points if name not in chosen), key=spread))
    return selected


def coordinates_of(wn, name):
    try:
        coords = wn.get_node(str(name)).coordinates
        x, y = float(coords[0]), float(coords[1])
    except Exception:
        return None
    if not np.isfinite(x) or not np.isfinite(y):
        return None
    return (x, y)


def pipe_midpoint(wn, pipe_id):
    link = wn.get_link(str(pipe_id))
    start = coordinates_of(wn, link.start_node_name)
    end = coordinates_of(wn, link.end_node_name)
    if start is None or end is None:
        return None
    return ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)


def select_candidate_pipes(wn, limit):
    """Choose pipes without reference to a leak location.

    A missing or oversized limit evaluates every pipe. A smaller limit is a
    spatially spread sample of pipe midpoints, not the first names in the file
    and not a sample that has been edited to include a known leak.
    """
    pipes = sorted((str(pipe) for pipe in wn.pipe_name_list), key=pipe_sort_key)
    if not pipes:
        raise RuntimeError("The network does not contain any pipes.")
    if limit is None or int(limit) >= len(pipes):
        return pipes

    points = {}
    for pipe in pipes:
        midpoint = pipe_midpoint(wn, pipe)
        if midpoint is not None:
            points[pipe] = midpoint
    if len(points) < int(limit):
        raise RuntimeError("Not enough pipes with endpoint coordinates to build a candidate sample.")
    chosen = farthest_point_ids(points, int(limit))
    return sorted(chosen, key=pipe_sort_key)


def select_sensors(wn, pressure_by_node, count):
    """Place virtual pressure sensors by spatial coverage, using the baseline only."""
    count = int(count)
    junctions = [str(name) for name in wn.junction_name_list]

    def eligible(threshold):
        points = {}
        for name in junctions:
            if name not in pressure_by_node:
                continue
            pressure = float(pressure_by_node[name])
            if not np.isfinite(pressure) or pressure < threshold:
                continue
            coords = coordinates_of(wn, name)
            if coords is None:
                continue
            points[name] = coords
        return points

    points = eligible(MIN_SENSOR_PRESSURE_M)
    if len(points) < count:
        points = eligible(0.0)
    if len(points) < count:
        points = eligible(float("-inf"))
    if len(points) < count:
        raise ValueError(
            f"sensor_count needs {count} junctions with finite baseline pressure; found {len(points)}."
        )
    return farthest_point_ids(points, count)


def longest_pipe(wn):
    pipes = [str(pipe) for pipe in wn.pipe_name_list]

    def sort_key(pipe):
        try:
            length = float(wn.get_link(pipe).length)
        except Exception:
            length = -1.0
        return (length, pipe_sort_key(pipe))

    if not pipes:
        raise RuntimeError("The network does not contain any pipes.")
    return max(pipes, key=sort_key)


def configure(wn, sample_time_s):
    """Pressure-dependent demand, stopped at the sample so later hours are not solved.

    Net3 is stored as a demand-driven model. Leaks are solved with WNTR's
    pressure-dependent demand so a large loss cannot keep extracting the full
    customer demand at a negative pressure. The 20 m required pressure is a
    service head used for that model, not a calibrated field value. The leak
    end time is past the final snapshot; ending exactly on the snapshot was
    observed to partially close the leak before that report.
    """
    step = HYDRAULIC_TIMESTEP_S
    duration = int(np.ceil(float(sample_time_s) / step) * step)
    duration = min(max(duration, step), MAX_DURATION_S)
    wn.options.time.duration = duration
    wn.options.time.hydraulic_timestep = step
    wn.options.time.report_timestep = step
    wn.options.hydraulic.demand_model = "PDD"
    wn.options.hydraulic.required_pressure = REQUIRED_PRESSURE_M
    wn.options.hydraulic.minimum_pressure = MINIMUM_PRESSURE_M
    return wn


def run_sim(wn):
    # Re-applied here because later imports can reset the process warning filters.
    warnings.filterwarnings("ignore", message="Covariance of the parameters could not be estimated")
    results = wntr.sim.WNTRSimulator(wn).run_sim()
    try:
        table = results.node["pressure"]
    except Exception as exc:
        raise RuntimeError(f"Hydraulic simulation did not return node pressures: {exc}") from exc
    if table is None or table.empty:
        raise RuntimeError("Hydraulic simulation returned no pressure readings.")
    return results


def pressure_vector(results, sensors, requested_time):
    table = results.node["pressure"]
    missing = [sensor for sensor in sensors if sensor not in table.columns]
    if missing:
        raise RuntimeError("Missing pressure readings for sensors: " + ", ".join(missing))
    position, actual = nearest_time(table.index, requested_time, HYDRAULIC_TIMESTEP_S)
    if actual + 1e-6 < LEAK_START_S:
        raise RuntimeError(
            f"Nearest snapshot is {actual:.0f} s, before the leak opens at {int(LEAK_START_S)} s."
        )
    values = table.iloc[position].reindex(list(sensors)).to_numpy(dtype=float)
    if values.shape != (len(sensors),) or not np.all(np.isfinite(values)):
        raise RuntimeError("Pressure readings are missing or non-finite at the sample time.")
    return values, actual


def pressures_at(results, requested_time):
    table = results.node["pressure"]
    position, actual = nearest_time(table.index, requested_time, HYDRAULIC_TIMESTEP_S)
    row = table.iloc[position]
    values = {}
    for name in row.index:
        try:
            values[str(name)] = float(row[name])
        except (TypeError, ValueError):
            continue
    return values, actual


def unique_leak_names(wn, pipe_id):
    node_names = set(map(str, wn.node_name_list))
    link_names = set(map(str, wn.link_name_list))
    for suffix in range(1, 51):
        extra = "" if suffix == 1 else f"_{suffix}"
        node_name = f"FOCALORS_LEAK_{pipe_id}{extra}"
        link_name = f"{pipe_id}_FOCALORS_DOWNSTREAM{extra}"
        if node_name not in node_names and link_name not in link_names:
            return node_name, link_name
    raise RuntimeError(f"Could not allocate a unique leak node for pipe {pipe_id}.")


def add_pipe_leak(wn, pipe_id, area):
    pipe_id = str(pipe_id)
    if pipe_id not in set(map(str, wn.pipe_name_list)):
        raise ValueError(f"Cannot place a leak on unknown pipe {pipe_id}.")
    node_name, link_name = unique_leak_names(wn, pipe_id)
    wntr.morph.split_pipe(
        wn,
        pipe_id,
        link_name,
        node_name,
        add_pipe_at_end=True,
        split_at_point=0.5,
        return_copy=False,
    )
    wn.get_node(node_name).add_leak(
        wn,
        area=float(area),
        discharge_coeff=DISCHARGE_COEFF,
        start_time=LEAK_START_S,
        end_time=int(wn.options.time.duration) + HYDRAULIC_TIMESTEP_S,
    )
    return wn


def simulate_leak_pressures(template, pipe_id, area, sensors, requested_time):
    model = add_pipe_leak(copy.deepcopy(template), pipe_id, area)
    results = run_sim(model)
    return pressure_vector(results, sensors, requested_time)


def short_error(exc):
    text = " ".join(f"{type(exc).__name__}: {exc}".split())
    return text[:400]


def _validate_request(leak_area_m2, sensor_count, candidate_limit, sample_time_s):
    if not np.isfinite(leak_area_m2) or leak_area_m2 <= 0 or leak_area_m2 > 0.01:
        raise ValueError("leak_area_m2 must be greater than 0 and at most 0.01 square meters.")
    if int(sensor_count) < 2 or int(sensor_count) > 12:
        raise ValueError("sensor_count must be between 2 and 12.")
    if candidate_limit is not None and (int(candidate_limit) < 1 or int(candidate_limit) > 500):
        raise ValueError("candidate_limit must be at least 1, or null to evaluate every pipe.")
    if int(sample_time_s) < LEAK_START_S or int(sample_time_s) > MAX_DURATION_S:
        raise ValueError(
            f"sample_time_s must be between {int(LEAK_START_S)} and {int(MAX_DURATION_S)} "
            "seconds so the sample is taken while the leak is open."
        )


def investigate(leak_pipe=None, leak_area_m2=1e-4, sensor_count=5, candidate_limit=None, sample_time_s=7200):
    started = time.perf_counter()
    _validate_request(float(leak_area_m2), sensor_count, candidate_limit, sample_time_s)
    leak_area_m2 = float(leak_area_m2)
    sensor_count = int(sensor_count)
    sample_time_s = int(sample_time_s)

    template = fresh_network()
    pipes = [str(pipe) for pipe in template.pipe_name_list]
    junctions = [str(name) for name in template.junction_name_list]
    if sensor_count > len(junctions):
        raise ValueError(f"sensor_count cannot exceed the {len(junctions)} Net3 junctions.")

    requested_pipe = None if leak_pipe is None else str(leak_pipe).strip()
    if requested_pipe:
        leak_pipe = requested_pipe
        leak_rule = "requested"
        if leak_pipe not in pipes:
            examples = ", ".join(pipes[:5])
            raise ValueError(
                f"Unknown pipe ID {leak_pipe!r}. Net3 pipe IDs look like {examples}. "
                f"There are {len(pipes)} pipes."
            )
    else:
        leak_pipe = longest_pipe(template)
        leak_rule = "longest_pipe"

    configure(template, sample_time_s)
    try:
        baseline_results = run_sim(copy.deepcopy(template))
    except Exception as exc:
        raise RuntimeError(f"Baseline hydraulic simulation failed. {short_error(exc)}") from exc

    baseline_pressures, baseline_time = pressures_at(baseline_results, sample_time_s)
    if baseline_time + 1e-6 < LEAK_START_S:
        raise ValueError(
            f"The snapshot at {baseline_time:.0f} s is before the leak opens at {int(LEAK_START_S)} s. "
            "Choose a later sample_time_s."
        )
    sensors = select_sensors(template, baseline_pressures, sensor_count)
    baseline, baseline_time = pressure_vector(baseline_results, sensors, sample_time_s)

    try:
        observed, observed_time = simulate_leak_pressures(
            template, leak_pipe, leak_area_m2, sensors, sample_time_s
        )
    except Exception as exc:
        raise RuntimeError(
            f"Scenario leak simulation failed for pipe {leak_pipe}. {short_error(exc)}"
        ) from exc
    if abs(observed_time - baseline_time) > 1e-6:
        raise RuntimeError(
            f"Could not align the baseline snapshot ({baseline_time:.0f} s) with the "
            f"leak snapshot ({observed_time:.0f} s)."
        )

    observed_delta = observed - baseline
    # Candidate ids are fixed before any candidate leak is simulated, and the
    # helper above does not accept the scenario pipe.
    candidate_ids = select_candidate_pipes(template, candidate_limit)
    candidate_deltas = {}
    failures = []
    total = len(candidate_ids)
    for index, pipe in enumerate(candidate_ids, start=1):
        try:
            readings, actual_time = simulate_leak_pressures(
                template, pipe, leak_area_m2, sensors, sample_time_s
            )
            if abs(actual_time - observed_time) > 1e-6:
                raise RuntimeError(
                    f"Time mismatch: candidate snapshot {actual_time:.0f} s, "
                    f"observed snapshot {observed_time:.0f} s."
                )
            candidate_deltas[pipe] = readings - baseline
        except Exception as exc:
            failures.append({"pipe_id": str(pipe), "error": short_error(exc)})
        if index == total or index % 25 == 0:
            logger.info("Candidate simulations %s/%s", index, total)
            print(f"Candidate simulations: {index}/{total}", flush=True)

    rows = rank_signatures(observed_delta, candidate_deltas)
    true_rank = annotate_scenario(rows, leak_pipe)
    signal = float(np.max(np.abs(observed_delta))) if observed_delta.size else 0.0

    sensor_rows = []
    for index, name in enumerate(sensors):
        coords = coordinates_of(template, name) or (None, None)
        sensor_rows.append({
            "id": f"S{index + 1}",
            "junction": name,
            "baseline_pressure": float(baseline[index]),
            "leak_pressure": float(observed[index]),
            "delta_pressure": float(observed_delta[index]),
            "x": None if coords[0] is None else float(coords[0]),
            "y": None if coords[1] is None else float(coords[1]),
        })

    limited = candidate_limit is not None and int(candidate_limit) < len(pipes)
    notes = [
        "Matching error is the root-mean-square difference of sensor pressure changes, in meters of head. It is not a probability.",
        "Sensors and candidate pipes are chosen without the scenario leak ID. A limited search is a spatial sample and does not have the simulated leak inserted into it.",
        "The scenario leak is simulated only to create the observations. It is ranked when that pipe was already selected, and the rank is applied after sorting.",
        "Observations and candidates use the same WNTR model, leak area, and sensors. A low error means the candidate reproduces this simulation. It is not field-validated leak-detection performance.",
        "Sensor and pipe coordinates are Net3 model coordinates, not GPS positions.",
    ]
    if limited:
        notes.append(
            f"This run evaluated {len(candidate_ids)} of {len(pipes)} pipes. "
            "Absence from the list is not evidence that a pipe is leak-free."
        )
    if abs(baseline_time - float(sample_time_s)) > 1:
        notes.append(
            f"Requested sample time {sample_time_s} s was aligned to the nearest hydraulic snapshot at {baseline_time:.0f} s."
        )
    if signal < 1e-4:
        notes.append(
            "The largest sensor pressure change is under 0.1 mm of head. Treat the ranking as numerically weak."
        )
    if failures:
        notes.append(f"{len(failures)} candidate simulations failed and were excluded from the ranking.")

    return {
        "network": "Net3",
        "junction_count": len(junctions),
        "pipe_count": len(pipes),
        "leak_pipe": leak_pipe,
        "leak_pipe_selection": leak_rule,
        "leak_area_m2": leak_area_m2,
        "pressure_unit": PRESSURE_UNIT,
        "sample_time_requested_s": sample_time_s,
        "sample_time_baseline_s": baseline_time,
        "sample_time_observed_s": observed_time,
        "sensors": sensor_rows,
        "signature": [float(value) for value in observed_delta],
        "observed_signal_max_abs_m": signal,
        "candidate_pipe_ids": candidate_ids,
        "candidate_count": len(rows),
        "candidate_limit_requested": None if candidate_limit is None else int(candidate_limit),
        "candidate_selection": "all_pipes" if not limited else "spatial_farthest_point",
        "actual_pipe_rank": true_rank,
        "true_pipe_in_candidate_set": leak_pipe in set(candidate_ids),
        "ranking_uses_leak_identity": False,
        "candidates": rows,
        "failures": failures,
        "error_metric": {
            "name": "rmse",
            "unit": PRESSURE_UNIT,
            "lower_is_closer": True,
            "description": (
                "Root-mean-square difference between observed and candidate sensor "
                "pressure-change vectors, in meters of head. Lower is a closer match. "
                "This is not a probability."
            ),
        },
        "hydraulic_settings": {
            "simulator": "WNTRSimulator",
            "demand_model": str(template.options.hydraulic.demand_model),
            "required_pressure_m": REQUIRED_PRESSURE_M,
            "minimum_pressure_m": MINIMUM_PRESSURE_M,
            "hydraulic_timestep_s": HYDRAULIC_TIMESTEP_S,
            "leak_start_s": LEAK_START_S,
            "leak_end_s": int(template.options.time.duration) + HYDRAULIC_TIMESTEP_S,
            "orifice_discharge_coeff": DISCHARGE_COEFF,
            "leak_position": "pipe midpoint",
            "sensor_selection": (
                "Farthest-point sampling on junctions with baseline pressure of at least "
                f"{MIN_SENSOR_PRESSURE_M:.0f} m, seeded at the junction nearest the centroid."
            ),
        },
        "demonstration": {
            "kind": "controlled_simulation",
            "field_validated": False,
            "statement": (
                "These rankings reproduce a leak inside the same WNTR model that generated "
                "the observations. They are not a measurement of real-world detection accuracy."
            ),
        },
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "notes": notes,
    }


def _element_kind(name, groups):
    for kind, names in groups:
        if name in names:
            return kind
    return "other"


def network_data():
    with _MODEL_LOCK:
        wn = base_network()
        node_groups = (
            ("junction", set(map(str, wn.junction_name_list))),
            ("reservoir", set(map(str, wn.reservoir_name_list))),
            ("tank", set(map(str, wn.tank_name_list))),
        )
        link_groups = (
            ("pipe", set(map(str, getattr(wn, "pipe_name_list", [])))),
            ("pump", set(map(str, getattr(wn, "pump_name_list", [])))),
            ("valve", set(map(str, getattr(wn, "valve_name_list", [])))),
        )
        elements = []
        node_ids = set()
        for name in wn.node_name_list:
            name = str(name)
            element_id = f"node:{name}"
            if element_id in node_ids:
                raise RuntimeError(f"Duplicate node id {element_id}.")
            node_ids.add(element_id)
            coords = coordinates_of(wn, name) or (0.0, 0.0)
            elements.append({
                "data": {
                    "id": element_id,
                    "name": name,
                    "label": name,
                    "kind": _element_kind(name, node_groups),
                },
                "position": {"x": coords[0], "y": coords[1]},
            })
        seen = set(node_ids)
        for name in wn.link_name_list:
            name = str(name)
            link = wn.get_link(name)
            start = str(getattr(link, "start_node_name", "") or "")
            end = str(getattr(link, "end_node_name", "") or "")
            if not start or not end:
                raise RuntimeError(f"Link {name} is missing endpoints.")
            element_id = f"link:{name}"
            if element_id in seen:
                raise RuntimeError(f"Duplicate element id {element_id}.")
            seen.add(element_id)
            source = f"node:{start}"
            target = f"node:{end}"
            if source not in node_ids or target not in node_ids:
                raise RuntimeError(f"Link {name} references a missing node.")
            elements.append({
                "data": {
                    "id": element_id,
                    "name": name,
                    "source": source,
                    "target": target,
                    "kind": _element_kind(name, link_groups),
                }
            })
        return {
            "network": "Net3",
            "junction_count": len(wn.junction_name_list),
            "pipe_count": len(wn.pipe_name_list),
            "node_count": len(wn.node_name_list),
            "link_count": len(wn.link_name_list),
            "elements": elements,
        }
