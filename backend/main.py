from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from database import init_db, recent_runs, save_result
from engine import network_data, investigate

app = FastAPI(title="FOCALORS API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"]
)
init_db()

class SimulationRequest(BaseModel):
    leak_pipe: Optional[str] = None
    leak_area_m2: float = Field(default=1e-4, gt=0, le=0.01)
    sensor_count: int = Field(default=5, ge=2, le=12)
    candidate_limit: Optional[int] = Field(default=15, ge=1, le=117)
    sample_time_s: int = Field(default=7200, ge=0, le=21600)

@app.get("/api/health")
def health():
    return {"status":"ok","service":"FOCALORS API"}

@app.get("/api/network")
def get_network():
    try:
        return network_data()
    except Exception as e:
        raise HTTPException(500, detail=f"Could not load Net3: {type(e).__name__}: {e}")

@app.post("/api/simulate")
def simulate(req: SimulationRequest):
    try:
        result = investigate(req.leak_pipe, req.leak_area_m2, req.sensor_count, req.candidate_limit, req.sample_time_s)
        result["run_id"] = save_result(result)
        return result
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Simulation failed: {type(e).__name__}: {e}")

@app.get("/api/runs")
def get_runs(limit: int = 20):
    return {"runs":recent_runs(max(1,min(limit,100)))}
