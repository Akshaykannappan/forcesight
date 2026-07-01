"""SQLite connection and query execution layer."""

import sqlite3
from contextlib import contextmanager
from typing import Any

from app.config import settings


@contextmanager
def get_connection():
    # open the DB as read-only so writes are blocked at the connection level,
    # even if somehow a write statement slipped past the validator
    uri = f"file:{settings.DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def run_query(sql: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]