"""Validates LLM-generated SQL before it touches the database."""

import re

from app.config import settings

FORBIDDEN_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "REPLACE", "GRANT", "REVOKE", "ATTACH", "DETACH",
    "PRAGMA", "VACUUM", "EXEC", "EXECUTE",
]


class SQLValidationError(Exception):
    """Raised when generated SQL fails safety checks."""
    pass


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def validate_and_clean(sql: str) -> str:
    if not sql or not sql.strip():
        raise SQLValidationError("Generated SQL was empty.")

    cleaned = _strip_comments(sql).strip()
    cleaned = cleaned.rstrip(";").strip()

    if ";" in cleaned:
        raise SQLValidationError(
            "Only a single SELECT statement is allowed; multiple "
            "statements separated by ';' were detected."
        )

    if not re.match(r"^\s*SELECT\b", cleaned, flags=re.IGNORECASE):
        raise SQLValidationError(
            "Only SELECT statements are allowed. The generated query "
            "did not start with SELECT."
        )

    upper_sql = cleaned.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper_sql):
            raise SQLValidationError(
                f"Forbidden keyword '{keyword}' detected. Only read-only "
                f"SELECT queries are permitted."
            )

    # add a LIMIT if the model forgot one, so we never accidentally dump an entire table
    if not re.search(r"\bLIMIT\b", upper_sql):
        cleaned = f"{cleaned} LIMIT {settings.DEFAULT_ROW_LIMIT}"

    return cleaned