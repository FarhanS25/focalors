import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("focalors.db")

def conn():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with conn() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            leak_pipe TEXT NOT NULL,
            leak_area_m2 REAL NOT NULL,
            candidate_count INTEGER NOT NULL,
            actual_pipe_rank INTEGER,
            result_json TEXT NOT NULL
        )""")

def save_result(result):
    with conn() as db:
        cur = db.execute(
            "INSERT INTO runs (leak_pipe, leak_area_m2, candidate_count, actual_pipe_rank, result_json) VALUES (?, ?, ?, ?, ?)",
            (result["leak_pipe"], result["leak_area_m2"], result["candidate_count"],
             result.get("actual_pipe_rank"), json.dumps(result))
        )
        return cur.lastrowid

def recent_runs(limit=20):
    with conn() as db:
        rows = db.execute(
            "SELECT id, created_at, leak_pipe, leak_area_m2, candidate_count, actual_pipe_rank FROM runs ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
