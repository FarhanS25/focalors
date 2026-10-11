# FOCALORS MVP

Minimal full-stack prototype: WNTR/Net3 hydraulic simulation, FastAPI backend, MongoDB persistence, React + Cytoscape network map.

The leak ranker compares pressure-change signatures. It does not receive the scenario leak ID, and a limited candidate list does not have that pipe inserted. Matching error is an RMSE in meters of head, not a probability. A close match means the candidate reproduces this same WNTR model. It is not field-validated detection performance.

## MongoDB Atlas

Completed runs are stored in one collection, `simulation_runs`. Sensor readings and ranked pipes are nested in that document. The scenario leak id is stored under `evaluation`, separate from the ranked predictions. The ranker does not read the database.

1. Create a free Atlas cluster and a database user.
2. In Atlas, allow your IP under Network Access, or use `0.0.0.0/0` only for a short-lived demo.
3. Copy the SRV connection string. It looks like `mongodb+srv://USER:PASSWORD@CLUSTER.mongodb.net/`.
4. From the repository root, copy the example environment file and edit it:

```powershell
copy .env.example .env
```

Set these variables in `.env`. Do not commit `.env` or put a real password in `.env.example`.

| Variable | Required | Purpose |
| --- | --- | --- |
| `MONGODB_URI` | Yes | Atlas connection string |
| `MONGODB_DB` | No | Database name. Defaults to `focalors` |
| `MONGODB_COLLECTION` | No | Collection name. Defaults to `simulation_runs` |

The API reads environment variables. A `.env` file in the repository root or in `backend/` is loaded if `python-dotenv` is installed, and it does not override variables already set in the shell.

## Backend

Python 3.13 is the verified interpreter for this repository. On Windows, `python` may point at 3.14, which was not used for the WNTR install. Prefer the 3.13 launcher.

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/api/health`. `status` is `ok` only when MongoDB answers a ping. If the database is down or `MONGODB_URI` is missing, `status` is `degraded` and `database.detail` explains it without including the connection string. `GET /api/network` still works in that case. `POST /api/simulate` returns HTTP 503 instead of pretending the run was saved.

Use `127.0.0.1` rather than `localhost` so the frontend does not hit an IPv6 address the server is not bound to.

Check the database without printing the URI:

```powershell
cd backend
.\.venv\Scripts\python.exe -c "import database; print(database.ping())"
```

## Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL (usually `http://127.0.0.1:5173`).

If the API is not on port 8000, create `frontend/.env` with `VITE_API_BASE=http://127.0.0.1:8000`.

## API

- `GET /api/health`
- `GET /api/network`
- `POST /api/simulate`
- `GET /api/runs`

Example POST body for a full Net3 search:

```json
{"leak_pipe":"329","leak_area_m2":0.0001,"sensor_count":5,"candidate_limit":null,"sample_time_s":7200}
```

`candidate_limit: null` evaluates every pipe. A number such as `15` evaluates an independent spatial sample of that size. The simulated leak is not added to the sample. `sample_time_s` must be from 3600 through 21600 because the orifice opens at one hour. The default sample is 7200 seconds.

A full search runs one WNTR hydraulic simulation per pipe plus the baseline and the scenario. In local testing, all 117 pipes finished in about 12–15 seconds. Use a spatial sample when you want a faster partial result. A partial result can miss the scenario pipe; that pipe is then reported as not ranked.

On one same-model check (pipe 329, area 0.0001 m², five virtual sensors, sample at 7200 s), the generating pipe had the lowest RMSE, about 1e-14 m, and the next pipe was about 6e-4 m. That shows this search can recover a leak it simulated itself. It is not a field-accuracy measurement.

## Tests

From `backend`, with the virtual environment active:

```powershell
python -m unittest discover -s tests -v
```

The hydraulic tests run real Net3 simulations, including one full-network search. Database unit tests use an in-memory MongoDB double, not Atlas. `test_atlas_ping_when_credentials_are_configured` runs only when `MONGODB_URI` is set; otherwise it is skipped and Atlas has not been tested.

## Important limitations

- All sensors and leaks are simulated inside WNTR's Net3 model.
- Candidate scores are RMSE values in meters of head, not probabilities and not confidence.
- The same hydraulic model generates the observations and the candidate signatures. Agreement is a controlled demonstration, not evidence of field performance.
- A spatial sample is not a full-network evaluation, and the scenario pipe is not forced into it.
- Five virtual sensors are placed by farthest-point sampling on baseline pressures. They are not an optimized or field-installed sensor design.
- Net3 coordinates and distances are model units, not GPS.
- Demand is solved as pressure-dependent demand with a 20 m service head so large leaks cannot keep extracting full customer demand at negative pressure. That setting is a modeling choice, not a calibration.
- Citizen priors, active investigation, sensor noise, model mismatch, and deployment are not implemented.
