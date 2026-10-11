# FOCALORS MVP

Minimal full-stack prototype: WNTR/Net3 hydraulic simulation, FastAPI backend, MongoDB persistence, React + Cytoscape network map.

The leak ranker compares pressure-change signatures. It does not receive the scenario leak ID, and a limited candidate list does not have that pipe inserted. Matching error is an RMSE in meters of head, not a probability. A close match means the candidate reproduces this same WNTR model. It is not field-validated detection performance.

## MongoDB Atlas

Completed runs are stored in one collection, `simulation_runs`. Sensor readings and ranked pipes are nested in that document. The scenario leak id is stored under `evaluation`, separate from the ranked predictions. The ranker does not read the database.

The API reads `MONGODB_URI` from the environment. On startup it loads `backend/.env` using the path of `backend/database.py`, so the terminal's current directory does not matter. A repository-root `.env` fills only names that are still unset. A variable already exported in the shell wins over both files. Restart the API after changing either file.

Do these steps in the Atlas website. The repository does not contain a cluster or a password.

1. Sign in at [cloud.mongodb.com](https://cloud.mongodb.com) and create a project.
2. Create a free M0 cluster in a region near you. Wait until the cluster status is ready.
3. Under Database Access, add a database user. Give that user the built-in `readWrite` role on the database `focalors`. Use a password that is not reused elsewhere. Do not use the Atlas account password, and do not grant `atlasAdmin` for this demo.
4. Under Network Access, choose Add IP Address, then Add Current IP Address. Wait until that entry is Active. Leave `0.0.0.0/0` unset; that rule would allow any address to attempt a login.
5. Open the cluster, choose Connect, then Drivers, then Python. Copy the `mongodb+srv://` connection string. Replace the `<password>` placeholder with the database user's password. If the password contains `@`, `:`, `/`, `?`, `#`, `[`, `]`, or `%`, percent-encode that character first. The string should look like the placeholder in `.env.example`, with your own user, password, and host.
6. From the repository root, create the local env file and edit it. Keep `.env.example` as the placeholder template.

```powershell
copy .env.example backend\.env
```

Edit `backend/.env`. Set `MONGODB_URI` to the string from step 5. `MONGODB_DATABASE` selects the database name (`focalors` if omitted). Runs are stored in `simulation_runs` unless `MONGODB_COLLECTION` is set. The database name comes from `MONGODB_DATABASE`, so the URI path can stay empty. An older `MONGODB_DB` value is used only when `MONGODB_DATABASE` is absent.

| Variable | Required | Purpose |
| --- | --- | --- |
| `MONGODB_URI` | Yes | Atlas connection string |
| `MONGODB_DATABASE` | No | Database name. Defaults to `focalors` |
| `MONGODB_COLLECTION` | No | Collection name. Defaults to `simulation_runs` |

Do not commit `backend/.env` or paste a real password into `.env.example`, the README, or source code.

## Backend

Python 3.13 is the verified interpreter for this repository. On Windows, `python` may point at 3.14, which was not used for the WNTR install. Prefer the 3.13 launcher.

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Check `http://127.0.0.1:8000/api/health`. The response is HTTP 200 in all three database states so the network map can still load. `status` is `ok` only when MongoDB answers a ping. The body never includes the connection string.

| Situation | `status` | `database.configured` | `database.detail` |
| --- | --- | --- | --- |
| MongoDB answered the ping | `ok` | `true` | omitted |
| `MONGODB_URI` is missing | `degraded` | `false` | `MONGODB_URI is not set.` |
| URI is set, but the server cannot be reached | `degraded` | `true` | `Could not reach MongoDB.` |

`GET /api/network` still works when the database is degraded. `POST /api/simulate` and `GET /api/runs` return HTTP 503 in that case. A 503 means the run was not saved.

Use `127.0.0.1` rather than `localhost` so the frontend does not hit an IPv6 address the server is not bound to.

From `backend`, with the virtual environment active, this check prints the connection report and does not print the URI or password:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -c "import database; print(database.check_connection())"
```

`database.ping()` prints the same report. A connected database prints `status` `ok` plus the database and collection names. `configured` false means `MONGODB_URI` is missing. `configured` true with `status` `unavailable` means the URI is set and the server could not be reached. Restart `uvicorn` after a successful check so the API process reloads `backend/.env`.

After that check prints `status` `ok`, save one spatial sample and read it back. A full 117-pipe search is optional. This request returns HTTP 503, and does not save a run, when MongoDB is unavailable.

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/simulate -H "Content-Type: application/json" -d "{\"leak_pipe\":\"329\",\"leak_area_m2\":0.0001,\"sensor_count\":5,\"candidate_limit\":15,\"sample_time_s\":7200}"
curl.exe -s http://127.0.0.1:8000/api/runs
```

## Frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL (usually `http://127.0.0.1:5173`).

Results open in Investigation view. That map and ranking show virtual sensors and the lowest-RMSE pipes, and they do not mark the scenario leak. Switch to Evaluation to inspect the configured leak and its rank after sorting. RMSE stays a matching error in meters, not a probability.

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
- Citizen priors, active investigation, sensor noise, and model mismatch are not implemented.

## AWS deployment

Use one EC2 instance. Nginx serves the built frontend and proxies `/api` to FastAPI on the same machine. MongoDB stays on the existing Atlas cluster. The API does not fall back to SQLite.

This creates a billable instance. Do not launch it until the instance type and region are confirmed. A `t3.medium` (4 GB RAM) in the same region as the Atlas cluster is the practical minimum; WNTR's Net3 search is a CPU-bound Python process, not a Lambda function.

### What you must provide

- An AWS account with permission to create an EC2 instance, a security group, and a key pair (`ec2:RunInstances`, `ec2:CreateSecurityGroup`, `ec2:AuthorizeSecurityGroupIngress`, `ec2:CreateKeyPair`, and the related `Describe*` calls). No RDS, IAM role, or load balancer is required.
- The existing `MONGODB_URI` for database `focalors`. Put it only in `backend/.env` on the instance.
- In Atlas Network Access, allow the instance's public IP. Do not open `0.0.0.0/0`.

### Instance setup

Launch Ubuntu 24.04, `t3.medium`, 20 GB gp3. Security group inbound: TCP 22 from your IP, and TCP 80 from the viewers. Leave 8000 closed; only Nginx is public.

On the instance:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo usermod -aG docker "$USER"
```

Log out and back in, clone this repository, then:

```bash
cp .env.example backend/.env
```

Edit `backend/.env` and set `MONGODB_URI`. `MONGODB_DATABASE` remains `focalors`.

```bash
docker compose up -d --build
```

Open `http://THE_PUBLIC_DNS/`. The site calls `/api` on that same host. `GET /api/health` stays on port 80 and reports MongoDB separately from the API process.

FastAPI binds `HOST` and `PORT` inside the container (`0.0.0.0` and `8000` unless those variables are set). A full 117-pipe search can take longer on this instance than on a workstation; Nginx allows 300 seconds for `/api`.

To point the built site at an API on a different origin, rebuild the web image with `VITE_API_BASE` set to that origin and set `CORS_ORIGINS` to the website origin. Do not use `*`.
