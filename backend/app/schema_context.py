"""Builds schema description from SQLite metadata for LLM prompt injection."""

from app.database import get_connection

# cached after first build since the schema doesn't change while the server is running
_schema_cache: str | None = None


def _get_tables(conn) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [row["name"] for row in rows]


def _describe_table(conn, table: str) -> str:
    columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
    col_lines = []
    for col in columns:
        pk_marker = " PRIMARY KEY" if col["pk"] else ""
        col_lines.append(f"  - {col['name']} ({col['type']}){pk_marker}")

    fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    fk_lines = [
        f"  - {table}.{fk['from']} -> {fk['table']}.{fk['to']}"
        for fk in fks
    ]

    section = f"TABLE: {table}\n" + "\n".join(col_lines)
    if fk_lines:
        section += "\nFOREIGN KEYS:\n" + "\n".join(fk_lines)
    return section


def build_schema_context(force_refresh: bool = False) -> str:
    global _schema_cache
    if _schema_cache is not None and not force_refresh:
        return _schema_cache

    with get_connection() as conn:
        tables = _get_tables(conn)
        sections = [_describe_table(conn, t) for t in tables]

    _schema_cache = "\n\n".join(sections)
    return _schema_cache