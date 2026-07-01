"""Chat endpoint that runs the full question to answer pipeline."""

import logging
import sqlite3

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.database import run_query
from app.llm import generate_sql, summarize_result, check_intent, suggest_alternatives
from app.models import ChatRequest, ChatResponse
from app.schema_context import build_schema_context
from app.sql_validator import SQLValidationError, validate_and_clean

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    logger.info("Received question: %r", request.query)

    schema = build_schema_context()

    intent = check_intent(request.query, schema)
    if intent.get("clear") is False:
        logger.warning("Question flagged as ambiguous, returning clarifying questions")
        return ChatResponse(
            question=request.query,
            sql="",
            raw_result=[],
            summary="",
            clarification_needed=True,
            clarifying_questions=intent.get("questions", []),
        )

    previous_error: str | None = None
    clean_sql: str | None = None
    rows: list[dict] | None = None

    total_attempts = settings.MAX_SQL_RETRIES + 1

    for attempt in range(1, total_attempts + 1):
        logger.info(
            "SQL generation attempt %d/%d (previous_error=%r)",
            attempt,
            total_attempts,
            previous_error,
        )

        sql = generate_sql(request.query, schema, previous_error)
        logger.info("Generated SQL (attempt %d): %s", attempt, sql)

        try:
            clean_sql = validate_and_clean(sql)
        except SQLValidationError as exc:
            logger.warning("SQL validation failed (attempt %d): %s", attempt, exc)
            previous_error = str(exc)
            continue

        try:
            rows = run_query(clean_sql)
        except sqlite3.Error as exc:
            logger.warning("SQL execution failed (attempt %d): %s", attempt, exc)
            previous_error = str(exc)
            continue

        logger.info(
            "Pipeline succeeded on attempt %d — %d row(s) returned.",
            attempt,
            len(rows),
        )
        break

    else:
        # the for/else fires only if we never hit break, meaning all retries failed
        raise HTTPException(
            status_code=422,
            detail=(
                "Could not generate a valid SQL query after multiple attempts. "
                f"Last error: {previous_error}"
            ),
        )

    if not rows:
        logger.info("Query returned zero rows, fetching alternative suggestions")
        alternatives = suggest_alternatives(request.query, schema)
        return ChatResponse(
            question=request.query,
            sql=clean_sql,
            raw_result=[],
            summary="",
            clarification_needed=True,
            clarifying_questions=alternatives,
        )

    try:
        summary = summarize_result(request.query, clean_sql, rows)
    except Exception as exc:
        logger.error("summarize_result failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Failed to generate a natural language summary.",
        )

    return ChatResponse(
        question=request.query,
        sql=clean_sql,
        raw_result=rows,
        summary=summary,
    )
