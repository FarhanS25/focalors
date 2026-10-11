"""MongoDB persistence for completed simulation runs.

The hydraulic ranker never reads this module. A run is stored only after
ranking finishes. The scenario leak id is kept under ``evaluation``, separate
from the ranked predictions.
"""

import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import DESCENDING, MongoClient
from pymongo.errors import PyMongoError

logger = logging.getLogger("focalors.database")

_client = None
_injected = False
_indexes_ready = False


class DatabaseError(Exception):
    """Client-safe persistence error. The message must not contain credentials."""


class DatabaseConfigurationError(DatabaseError):
    pass


class DatabaseUnavailableError(DatabaseError):
    pass


def _apply_env_file(path):
    """Fill blank environment names from one env file.

    A non-empty process variable wins. A blank one does not hide the file.
    Values are not shell-expanded, so a ``$`` in a password stays literal.
    The path is resolved from the given file, not from the process cwd.
    """
    from dotenv import dotenv_values

    file_path = Path(path)
    if not file_path.is_file():
        return False
    parsed = dotenv_values(file_path, interpolate=False, encoding="utf-8-sig")
    applied = False
    for key, value in parsed.items():
        if not key or value is None or not str(value).strip():
            continue
        if os.environ.get(key, "").strip():
            continue
        os.environ[key] = str(value).strip()
        applied = True
    return applied


def load_env():
    """Load env files from this module's directory, not from the process cwd.

    An environment variable already set to a non-empty value wins.
    ``backend/.env`` then fills anything still blank, and a repository-root
    ``.env`` fills only names that neither of those provided.
    """
    try:
        import dotenv  # noqa: F401
    except ImportError:
        logger.warning("python-dotenv is not installed, so .env files were not loaded.")
        return
    backend_dir = Path(__file__).resolve().parent
    _apply_env_file(backend_dir / ".env")
    _apply_env_file(backend_dir.parent / ".env")


def mongodb_uri():
    return os.environ.get("MONGODB_URI", "").strip()


def db_name():
    for key in ("MONGODB_DATABASE", "MONGODB_DB"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return "focalors"


def collection_name():
    return os.environ.get("MONGODB_COLLECTION", "simulation_runs").strip() or "simulation_runs"


def _close_client(client):
    """Close a discarded client. Missing clients and close errors stay local.

    The exception message is not logged: a driver error can contain the URI.
    """
    close = getattr(client, "close", None)
    if not callable(close):
        return
    try:
        close()
    except Exception as exc:
        logger.error("MongoDB client close failed: %s", type(exc).__name__)


def install_client(client):
    """Use a test double instead of opening a URI. Not for production.

    The shared reference is swapped before the previous client is closed, so
    ``close`` is not invoked on the client still published for reuse. The same
    instance can be installed again without closing it. There is no module
    lock; this matches the existing global client and avoids holding a lock
    across ``close``.
    """
    global _client, _injected, _indexes_ready
    previous = _client
    _client = client
    _injected = True
    _indexes_ready = False
    if previous is not client:
        _close_client(previous)


def reset_client():
    """Discard the shared client. A real client is closed first.

    Safe when no client is installed, when ``close`` is missing, and when
    ``close`` raises. The reference is cleared before closing so a later
    ``get_client`` cannot reuse a client that is shutting down. Closing
    failures are logged by exception type and do not propagate.
    """
    global _client, _injected, _indexes_ready
    client = _client
    _client = None
    _injected = False
    _indexes_ready = False
    _close_client(client)


def get_client():
    global _client
    if _injected and _client is not None:
        return _client
    uri = mongodb_uri()
    if not uri:
        raise DatabaseConfigurationError("MONGODB_URI is not set.")
    if _client is None:
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            retryWrites=True,
            tz_aware=True,
            tzinfo=timezone.utc,
        )
    return _client


def collection():
    return get_client()[db_name()][collection_name()]


def to_bson(value):
    """Convert engine results, including NumPy values, into BSON-safe objects."""
    if isinstance(value, dict):
        return {str(key): to_bson(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        return [to_bson(item) for item in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [to_bson(item) for item in value]
    if isinstance(value, np.generic):
        return to_bson(value.item())
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise DatabaseError("Simulation result contains a non-finite number and was not saved.")
        return float(value)
    if isinstance(value, str) or value is None:
        return value
    if isinstance(value, datetime):
        return value
    raise DatabaseError(f"Simulation result contains an unsupported value of type {type(value).__name__}.")


def build_document(result):
    data = to_bson(result)
    if not data.get("leak_pipe"):
        raise DatabaseError("Simulation result is missing the scenario leak id.")
    predictions = []
    for row in data.get("candidates") or []:
        predictions.append({
            "pipe_id": row.get("pipe_id"),
            "matching_error": row.get("matching_error"),
            "rank": row.get("rank"),
        })
    return {
        "created_at": datetime.now(timezone.utc),
        "status": "completed",
        "configuration": {
            "network": data.get("network"),
            "leak_area_m2": data.get("leak_area_m2"),
            "sensor_count": len(data.get("sensors") or []),
            "candidate_limit": data.get("candidate_limit_requested"),
            "sample_time_s": data.get("sample_time_requested_s"),
            "pressure_unit": data.get("pressure_unit"),
            "candidate_selection": data.get("candidate_selection"),
            "hydraulic_settings": data.get("hydraulic_settings"),
        },
        "evaluation": {
            "leak_pipe": data.get("leak_pipe"),
            "leak_pipe_selection": data.get("leak_pipe_selection"),
            "actual_pipe_rank": data.get("actual_pipe_rank"),
            "true_pipe_in_candidate_set": data.get("true_pipe_in_candidate_set"),
        },
        "sensors": data.get("sensors") or [],
        "signature": data.get("signature") or [],
        "observed_signal_max_abs_m": data.get("observed_signal_max_abs_m"),
        "candidate_pipe_ids": data.get("candidate_pipe_ids") or [],
        "candidate_count": data.get("candidate_count"),
        "predictions": predictions,
        "failures": data.get("failures") or [],
        "error_metric": data.get("error_metric"),
        "elapsed_seconds": data.get("elapsed_seconds"),
        "demonstration": data.get("demonstration"),
    }


def _ensure_indexes():
    runs = collection()
    runs.create_index([("created_at", DESCENDING)], name="created_at_desc")
    runs.create_index("status", name="status")
    runs.create_index("evaluation.leak_pipe", name="evaluation_leak_pipe")


def _ensure_ready():
    global _indexes_ready
    try:
        get_client()
    except DatabaseConfigurationError:
        raise
    except Exception as exc:
        logger.error("MongoDB client setup failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Could not reach MongoDB.") from exc
    if _indexes_ready:
        return
    try:
        _ensure_indexes()
    except DatabaseError:
        raise
    except Exception as exc:
        logger.error("MongoDB index setup failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Could not reach MongoDB.") from exc
    _indexes_ready = True


def check_connection():
    """Ping MongoDB with the shared client. The result never includes the URI."""
    if not _injected and not mongodb_uri():
        return {
            "status": "unavailable",
            "engine": "mongodb",
            "configured": False,
            "detail": "MONGODB_URI is not set.",
        }
    try:
        get_client().admin.command("ping")
    except DatabaseConfigurationError:
        return {
            "status": "unavailable",
            "engine": "mongodb",
            "configured": False,
            "detail": "MONGODB_URI is not set.",
        }
    except Exception as exc:
        logger.error("MongoDB ping failed: %s", type(exc).__name__)
        return {
            "status": "unavailable",
            "engine": "mongodb",
            "configured": True,
            "detail": "Could not reach MongoDB.",
        }
    return {
        "status": "ok",
        "engine": "mongodb",
        "configured": True,
        "database": db_name(),
        "collection": collection_name(),
    }


def ping():
    """Same report as ``check_connection``. Kept for the existing diagnostic command."""
    return check_connection()


def init_db():
    report = ping()
    if report["status"] != "ok":
        return report
    try:
        _ensure_ready()
    except DatabaseError as exc:
        return {
            "status": "unavailable",
            "engine": "mongodb",
            "configured": True,
            "detail": str(exc),
        }
    return report


def save_result(result):
    _ensure_ready()
    try:
        document = build_document(result)
        inserted = collection().insert_one(document)
    except DatabaseError:
        raise
    except PyMongoError as exc:
        logger.error("MongoDB insert failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Could not save the simulation run.") from exc
    except Exception as exc:
        logger.error("MongoDB insert failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Could not save the simulation run.") from exc
    if getattr(inserted, "inserted_id", None) is None:
        raise DatabaseUnavailableError("Could not save the simulation run.")
    return str(inserted.inserted_id)


def _created_at_text(value):
    if isinstance(value, datetime):
        # PyMongo stores UTC. A naive value is that UTC time, not the machine's local time.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    return value


def _run_limit(limit):
    if isinstance(limit, bool) or isinstance(limit, float):
        raise ValueError("limit must be an integer from 1 to 100.")
    if isinstance(limit, str):
        text = limit.strip()
        if not text.isdigit():
            raise ValueError("limit must be an integer from 1 to 100.")
        limit = int(text)
    if not isinstance(limit, int):
        raise ValueError("limit must be an integer from 1 to 100.")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be an integer from 1 to 100.")
    return limit


def load_run(run_id):
    """Return one stored run, including its evaluation block, or None.

    The HTTP layer decides whether evaluation fields leave the process.
    """
    try:
        identifier = ObjectId(str(run_id))
    except (InvalidId, TypeError):
        return None
    _ensure_ready()
    try:
        return collection().find_one({"_id": identifier})
    except DatabaseError:
        raise
    except Exception as exc:
        logger.error("MongoDB read failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Could not read saved runs.") from exc


def recent_runs(limit=20):
    limit = _run_limit(limit)
    _ensure_ready()
    try:
        cursor = collection().find().sort("created_at", DESCENDING).limit(limit)
        documents = list(cursor)
    except DatabaseError:
        raise
    except Exception as exc:
        logger.error("MongoDB read failed: %s", type(exc).__name__)
        raise DatabaseUnavailableError("Could not read saved runs.") from exc
    runs = []
    for document in documents:
        evaluation = document.get("evaluation") or {}
        configuration = document.get("configuration") or {}
        runs.append({
            "id": str(document.get("_id")),
            "created_at": _created_at_text(document.get("created_at")),
            "leak_pipe": evaluation.get("leak_pipe"),
            "leak_area_m2": configuration.get("leak_area_m2"),
            "candidate_count": document.get("candidate_count"),
            "actual_pipe_rank": evaluation.get("actual_pipe_rank"),
            "status": document.get("status"),
        })
    return runs


load_env()
