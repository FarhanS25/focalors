import logging
import os
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from database import DatabaseError, check_connection, init_db, load_run, recent_runs, save_result
from engine import investigate, network_data

# Investigation responses omit these keys at every level. Evaluation keeps them.
# The ranker does not read them back; they are labels stored for evaluation.
_GROUND_TRUTH_KEYS = frozenset({
    "leak_pipe",
    "actual_pipe_rank",
    "true_pipe_in_candidate_set",
    "is_ground_truth",
})

logger = logging.getLogger("focalors.api")


def cors_origins():
    """Browser origins allowed to call the API.

    ``CORS_ORIGINS`` is a comma-separated list. When it is unset, only the
    local Vite dev server is allowed. The deployed site is same-origin, so it
    does not need a wildcard.
    """
    configured = os.environ.get("CORS_ORIGINS", "").strip()
    if not configured:
        return ["http://127.0.0.1:5173", "http://localhost:5173"]
    return [origin.strip().rstrip("/") for origin in configured.split(",") if origin.strip()]


app = FastAPI(title="FOCALORS API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request, exc):
    messages = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []) if part != "body")
        text = error.get("msg", "Invalid value")
        messages.append(f"{location}: {text}" if location else text)
    return JSONResponse(status_code=422, content={"detail": "; ".join(messages) or "Invalid request"})


def requested_view(value):
    text = str(value or "investigation").strip().lower()
    if text not in {"investigation", "evaluation"}:
        raise HTTPException(status_code=422, detail="view must be investigation or evaluation")
    return text


def project_view(value, view):
    """Copy a response, dropping ground-truth keys unless this is evaluation."""
    if isinstance(value, list):
        return [project_view(item, view) for item in value]
    if isinstance(value, dict):
        projected = {}
        for key, item in value.items():
            if view != "evaluation" and key in _GROUND_TRUTH_KEYS:
                continue
            projected[key] = project_view(item, view)
        return projected
    return value


def present_saved_run(document, view):
    """Rebuild the fields the UI reads from a stored run, then apply the view."""
    evaluation = document.get("evaluation") or {}
    configuration = document.get("configuration") or {}
    leak_pipe = evaluation.get("leak_pipe")
    candidates = []
    for row in document.get("predictions") or []:
        pipe_id = row.get("pipe_id")
        candidates.append({
            "pipe_id": pipe_id,
            "matching_error": row.get("matching_error"),
            "rank": row.get("rank"),
            "is_ground_truth": pipe_id is not None and str(pipe_id) == str(leak_pipe),
        })
    payload = {
        "run_id": str(document.get("_id")),
        "elapsed_seconds": document.get("elapsed_seconds"),
        "leak_pipe": leak_pipe,
        "actual_pipe_rank": evaluation.get("actual_pipe_rank"),
        "true_pipe_in_candidate_set": evaluation.get("true_pipe_in_candidate_set"),
        "candidate_count": document.get("candidate_count"),
        "candidate_selection": configuration.get("candidate_selection"),
        "candidates": candidates,
        "sensors": document.get("sensors") or [],
        "observed_signal_max_abs_m": document.get("observed_signal_max_abs_m"),
        "failures": document.get("failures") or [],
        "notes": document.get("notes") or [],
        "demonstration": document.get("demonstration"),
        "status": document.get("status"),
    }
    projected = project_view(payload, view)
    projected["view"] = view
    return projected


class SimulationRequest(BaseModel):
    view: Literal["investigation", "evaluation"] = "investigation"
    leak_pipe: Optional[str] = Field(
        default=None,
        description="Pipe used to generate the simulated observations. The ranker does not receive this id.",
    )
    leak_area_m2: float = Field(default=1e-4, gt=0, le=0.01)
    sensor_count: int = Field(default=5, ge=2, le=12)
    candidate_limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=117,
        description="Size of an independent spatial pipe sample. Null evaluates every Net3 pipe.",
    )
    sample_time_s: int = Field(default=7200, ge=3600, le=21600)

    @field_validator("leak_pipe", mode="before")
    @classmethod
    def clean_leak_pipe(cls, value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None


@app.get("/api/health")
def health():
    database_status = check_connection()
    return {
        "status": "ok" if database_status["status"] == "ok" else "degraded",
        "service": "FOCALORS API",
        "mode": "simulation",
        "database": database_status,
    }


@app.get("/api/network")
def get_network():
    try:
        return network_data()
    except Exception as exc:
        logger.exception("Could not load Net3")
        raise HTTPException(status_code=500, detail="Could not load Net3.") from exc


@app.post("/api/simulate")
def simulate(request: SimulationRequest):
    try:
        result = investigate(
            request.leak_pipe,
            request.leak_area_m2,
            request.sensor_count,
            request.candidate_limit,
            request.sample_time_s,
        )
        result["run_id"] = save_result(result)
        projected = project_view(result, request.view)
        projected["view"] = request.view
        return projected
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Simulation failed")
        raise HTTPException(status_code=500, detail="Simulation failed.") from exc


@app.get("/api/runs")
def get_runs(
    limit: int = Query(default=20, ge=1, le=100),
    view: str = Query(default="investigation"),
):
    selected = requested_view(view)
    try:
        runs = [project_view(run, selected) for run in recent_runs(limit)]
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"view": selected, "runs": runs}


@app.get("/api/runs/{run_id}")
def get_saved_run(run_id: str, view: str = Query(default="investigation")):
    selected = requested_view(view)
    try:
        document = load_run(run_id)
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not document:
        raise HTTPException(status_code=404, detail="Unknown run.")
    return present_saved_run(document, selected)


init_db()
