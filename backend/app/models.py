"""Request and response schemas for the chat endpoint."""

from typing import Any, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    question: str
    sql: str
    raw_result: list[dict[str, Any]]
    summary: str
    clarification_needed: bool = False
    clarifying_questions: list[str] = []
