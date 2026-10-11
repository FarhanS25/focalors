import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from database import DatabaseError, check_connection, init_db, recent_runs, save_result
from engine import investigate, network_data

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


class SimulationRequest(BaseModel):
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
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Simulation failed")
        raise HTTPException(status_code=500, detail="Simulation failed.") from exc


@app.get("/api/runs")
def get_runs(limit: int = Query(default=20, ge=1, le=100)):
    try:
        return {"runs": recent_runs(limit)}
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


init_db()
