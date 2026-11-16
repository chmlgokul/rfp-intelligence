"""Small SQLite persistence layer for saved RFP opportunities."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "rfp_intelligence.db"


def initialise_database(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    """Create the local opportunity table when the app starts."""
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                stage TEXT NOT NULL,
                human_decision TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )


def save_opportunity(payload: dict[str, Any], opportunity_id: int | None = None, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    """Insert or update an opportunity and return its stable identifier."""
    initialise_database(db_path)
    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    values = (
        str(payload.get("file_name") or "Untitled opportunity"),
        str(payload.get("opportunity_stage") or "New"),
        str(payload.get("human_decision") or "Pending human review"),
        updated_at,
        json.dumps(payload, ensure_ascii=False),
    )
    with sqlite3.connect(db_path) as connection:
        if opportunity_id is None:
            cursor = connection.execute(
                "INSERT INTO opportunities (file_name, stage, human_decision, updated_at, payload) VALUES (?, ?, ?, ?, ?)",
                values,
            )
            return int(cursor.lastrowid)
        connection.execute(
            "UPDATE opportunities SET file_name = ?, stage = ?, human_decision = ?, updated_at = ?, payload = ? WHERE id = ?",
            (*values, opportunity_id),
        )
        return opportunity_id


def list_opportunities(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    """Return lightweight summaries for the opportunity picker."""
    initialise_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, file_name, stage, human_decision, updated_at FROM opportunities ORDER BY updated_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def load_opportunity(opportunity_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any] | None:
    """Load a complete saved opportunity payload."""
    initialise_database(db_path)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("SELECT payload FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
    if not row:
        return None
    payload = json.loads(row[0])
    payload["opportunity_id"] = opportunity_id
    return payload
