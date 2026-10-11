import copy
from functools import lru_cache
import numpy as np
import wntr

@lru_cache(maxsize=1)
def base_network():
    # Treat this cached model as read-only; every run uses a deep copy.
    return wntr.network.WaterNetworkModel("Net3")

def configure(wn):
    wn.options.time.duration = 6 * 3600
    wn.options.time.hydraulic_timestep = 3600
    wn.options.time.report_timestep = 3600
    try:
        wn.options.hydraulic.demand_model = "PDD"
    except Exception:
        pass
    return wn

def pressure_at(results, sensors, requested_time):
    table = results.node["pressure"]
    if table.empty:
        raise RuntimeError("No pressure readings returned by hydraulic simulation.")
    times = np.asarray(table.index, dtype=float)
    index = int(np.argmin(np.abs(times - float(requested_time))))
    actual_time = table.index[index]
    return table.loc[actual_time, sensors].astype(float), float(actual_time)

def leak_signature(wn_source, pipe_id, area, sensors, sample_time):
    wn = copy.deepcopy(wn_source)
    node = f"FOCALORS_LEAK_{pipe_id}"
    downstream = f"{pipe_id}_FOCALORS_DOWNSTREAM"
    suffix = 1
    while node in wn.node_name_list or downstream in wn.link_name_list:
        suffix += 1
        node = f"FOCALORS_LEAK_{pipe_id}_{suffix}"
        downstream = f"{pipe_id}_FOCALORS_DOWNSTREAM_{suffix}"
    wn = wntr.morph.split_pipe(wn, pipe_id, downstream, node)
    wn.get_node(node).add_leak(
        wn, area=float(area), discharge_coeff=0.75,
        start_time=3600, end_time=6*3600
    )
    results = wntr.sim.WNTRSimulator(configure(wn)).run_sim()
    return pressure_at(results, sensors, sample_time)

def network_data():
    wn = base_network()
    elements = []
    for name in wn.node_name_list:
        node = wn.get_node(name)
        coords = getattr(node, "coordinates", (0, 0))
        try:
            x, y = float(coords[0]), float(coords[1])
        except Exception:
            x, y = 0.0, 0.0
        kind = "junction" if name in wn.junction_name_list else ("reservoir" if name in wn.reservoir_name_list else "tank")
        elements.append({"data":{"id":str(name),"label":str(name),"kind":kind},"position":{"x":x,"y":y}})
    for name in wn.link_name_list:
        link = wn.get_link(name)
        elements.append({"data":{"id":str(name),"source":str(link.start_node_name),"target":str(link.end_node_name),"kind":"pipe" if name in wn.pipe_name_list else "other"}})
    return {"network":"Net3","junction_count":len(wn.junction_name_list),"pipe_count":len(wn.pipe_name_list),"elements":elements}

def investigate(leak_pipe=None, leak_area_m2=1e-4, sensor_count=5, candidate_limit=15, sample_time_s=7200):
    if leak_area_m2 <= 0:
        raise ValueError("leak_area_m2 must be positive")
    wn = copy.deepcopy(base_network())
    junctions = sorted(wn.junction_name_list)
    pipes = list(wn.pipe_name_list)
    if sensor_count < 2 or sensor_count > len(junctions):
        raise ValueError("sensor_count must be between 2 and the number of junctions")
    indexes = [round(i*(len(junctions)-1)/(sensor_count-1)) for i in range(sensor_count)]
    sensors = [junctions[i] for i in indexes]
    lengths = {p: float(wn.get_link(p).length) for p in pipes}
    leak_pipe = str(leak_pipe) if leak_pipe is not None else max(lengths, key=lengths.get)
    if leak_pipe not in pipes:
        raise ValueError(f"Unknown pipe ID {leak_pipe}. Net3 has {len(pipes)} pipes.")

    baseline_results = wntr.sim.WNTRSimulator(configure(copy.deepcopy(wn))).run_sim()
    baseline, baseline_t = pressure_at(baseline_results, sensors, sample_time_s)
    observed, observed_t = leak_signature(wn, leak_pipe, leak_area_m2, sensors, sample_time_s)
    observed_delta = observed.to_numpy() - baseline.to_numpy()

    if candidate_limit is None:
        candidates = list(pipes)
    else:
        candidates = list(pipes[:int(candidate_limit)])
        if leak_pipe not in candidates:
            candidates.append(leak_pipe)

    rows, failures = [], []
    for i, pipe in enumerate(candidates, 1):
        try:
            readings, _ = leak_signature(wn, pipe, leak_area_m2, sensors, sample_time_s)
            delta = readings.to_numpy() - baseline.to_numpy()
            rows.append({
                "pipe_id": str(pipe),
                "matching_error": float(np.linalg.norm(observed_delta-delta)),
                "is_ground_truth": pipe == leak_pipe,
            })
        except Exception as exc:
            failures.append({"pipe_id":str(pipe),"error":f"{type(exc).__name__}: {exc}"})
        if i % 10 == 0:
            print(f"Candidate simulations: {i}/{len(candidates)}")

    rows.sort(key=lambda r:r["matching_error"])
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    true_rank = next((r["rank"] for r in rows if r["is_ground_truth"]), None)
    sensor_rows = []
    for i, (name, b, o, d) in enumerate(zip(sensors, baseline.to_numpy(), observed.to_numpy(), observed_delta), 1):
        sensor_rows.append({"id":f"S{i}","junction":str(name),"baseline_pressure":float(b),"leak_pressure":float(o),"delta_pressure":float(d)})

    return {
        "network":"Net3","junction_count":len(junctions),"pipe_count":len(pipes),
        "leak_pipe":leak_pipe,"leak_area_m2":float(leak_area_m2),
        "sample_time_requested_s":int(sample_time_s),
        "sample_time_baseline_s":baseline_t,"sample_time_observed_s":observed_t,
        "sensors":sensor_rows,"signature":[float(x) for x in observed_delta],
        "candidate_count":len(rows),"candidate_limit_requested":candidate_limit,
        "actual_pipe_rank":true_rank,"candidates":rows[:20],"failures":failures,
        "notes":[
            "Matching errors are not probabilities.",
            "A limited candidate set is not full-network evaluation.",
            "Candidate and observed cases use the same hydraulic model; this is a controlled simulation, not field validation.",
            "Net3 coordinates are model coordinates, not GPS."
        ]
    }
