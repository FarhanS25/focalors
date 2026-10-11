# FOCALORS MVP

Minimal full-stack prototype: WNTR/Net3 hydraulic simulation, FastAPI backend, SQLite persistence, React + Cytoscape network map.

## Backend
Use Python 3.11 or 3.12 if available.

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Check `http://localhost:8000/api/health`.

## Frontend
In another terminal:
```bash
cd frontend
npm install
npm run dev
```
Open the Vite URL (usually `http://localhost:5173`).

If needed, create `frontend/.env` with `VITE_API_BASE=http://localhost:8000`.

## API
- `GET /api/health`
- `GET /api/network`
- `POST /api/simulate`
- `GET /api/runs`

Example POST body:
```json
{"leak_pipe":"329","leak_area_m2":0.0001,"sensor_count":5,"candidate_limit":15,"sample_time_s":7200}
```
Use `candidate_limit: null` to try all pipes; it can take several minutes. The default is 15 plus the selected ground-truth pipe so the first demo is quicker.

## Important limitations
- All sensors and leaks are simulated.
- Candidate scores are matching errors, not probabilities.
- A 15-pipe subset is not full-network evaluation.
- The observed and candidate cases use the same hydraulic model; this is not field validation.
- Net3 coordinates/distances are model units, not GPS.
- Citizen priors, active investigation, noise/model-mismatch tests, and AWS deployment are not implemented in this MVP yet.

## Push to GitHub
From this folder:
```bash
git init
git add .
git commit -m "Add FOCALORS MVP"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```
