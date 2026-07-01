"""Handles all LLM calls: question to SQL, and result to plain English summary."""

import json
import re

from openai import OpenAI

from app.config import settings

client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


def check_intent(question: str, schema: str) -> dict:
    system_prompt = (
        "You are a query intent classifier for a database chatbot. "
        "Given a user question and a database schema, classify the question into one of three cases and respond with raw JSON only, no markdown, no explanation.\n\n"
        "Case 1 — clear question: the question makes sense and is answerable from the schema. "
        'Return exactly: {"clear": true}\n\n'
        "Case 2 — garbage or unstructured input: the question is random characters, gibberish, or makes no sense. "
        "Generate 2-3 example questions the user could ask about this specific database. "
        "Each time, pick different questions — vary which tables and columns you focus on, vary the type of question (count, average, list, top N, filter by value). "
        "Never return the same set of questions twice. Draw from all available tables: users, products, orders, support_tickets. "
        'Return: {"clear": false, "questions": [<2-3 varied, specific, example questions drawn from the schema>]}\n\n'
        "Case 3 — structured but unrelated to the database: the question is a real sentence but about something outside the schema (e.g. weather, sports, news). "
        "Extract the key entity or location from the question (e.g. if they ask about weather in Mumbai, extract Mumbai). "
        "Then return 2-3 questions that are directly about that extracted entity using the actual tables and columns in the schema. "
        "For example if the entity is Mumbai: 'How many orders were placed by users from Mumbai?', 'Which users from Mumbai have raised support tickets?'. "
        'Return: {"clear": false, "questions": [<2-3 entity-specific questions grounded in the schema>]}\n\n'
        "The questions array must always have 2 to 3 items. Each item must be a complete, specific, answerable question about real data in the schema. Never return generic questions."
    )

    user_message = f"Schema:\n{schema}\n\nUser question: {question}"

    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    raw = response.choices[0].message.content or ""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # if the model returns something unparseable, let the pipeline continue normally
        return {"clear": True}


def generate_sql(
    question: str,
    schema: str,
    previous_error: str | None = None,
) -> str:
    system_prompt = (
        "You are an expert SQLite query generator. "
        f"Here is the database schema:\n\n{schema}\n\n"
        "Rules:\n"
        "- Output ONLY the raw SQL query and nothing else — no markdown code "
        "fences, no explanation, no comments.\n"
        "- Only generate SELECT statements, never write/modify statements.\n"
        "- Use exact table and column names from the schema exactly as given.\n"
        "- Always prefer explicit column names over SELECT * when it makes "
        "the result clearer.\n"
        "- If joining tables, use proper JOIN syntax with the foreign key "
        "relationships shown in the schema.\n\n"
        "Examples:\n\n"
        'Question: "Which city has the most orders?"\n'
        "SQL: SELECT u.city, COUNT(*) as order_count FROM orders o "
        "JOIN users u ON o.user_id = u.user_id "
        "GROUP BY u.city ORDER BY order_count DESC LIMIT 1\n\n"
        'Question: "List all users from Bangalore who have placed orders"\n'
        "SQL: SELECT DISTINCT u.name, u.email FROM users u "
        "JOIN orders o ON u.user_id = o.user_id WHERE u.city = 'Bangalore'"
    )

    user_message = question
    if previous_error is not None:
        user_message += (
            f"\n\nThe previous query failed with this error: {previous_error}. "
            "Please fix the query and try again."
        )

    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    raw = response.choices[0].message.content or ""

    # models sometimes wrap the SQL in ```sql fences even when told not to, so strip those
    cleaned = re.sub(r"^```(?:sql)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    return cleaned.strip()


def summarize_result(question: str, sql: str, rows: list[dict]) -> str:
    system_prompt = (
        "You are a helpful assistant that converts SQL query results into a "
        "short, natural-language answer for a non-technical user. "
        "Be concise — 1 to 3 sentences. "
        "Do not mention SQL, tables, or columns. "
        'Do not start with phrases like "Based on the data" or '
        '"According to the results" — just answer directly and naturally, '
        "like a knowledgeable colleague would."
    )

    if not rows:
        user_message = (
            f"Question: {question}\n\n"
            "No results were found for this query. "
            "Please answer naturally to indicate there were no matching records."
        )
    else:
        display_rows = rows
        truncated = False
        if len(rows) > 20:
            display_rows = rows[:20]
            truncated = True

        # cap at 20 rows to avoid blowing up the token budget on large result sets
        sample_note = (
            f" (Note: this is a partial sample of the first 20 rows out of "
            f"{len(rows)} total results.)"
            if truncated
            else ""
        )

        user_message = (
            f"Question: {question}\n\n"
            f"Query result (as JSON): {display_rows}{sample_note}\n\n"
            "Give a concise natural language answer."
        )

    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return (response.choices[0].message.content or "").strip()


def suggest_alternatives(question: str, schema: str) -> list[str]:
    system_prompt = (
        "You are a helpful database assistant. "
        "The user asked a question but no data was found in the database. "
        "Given the original question and the schema, suggest 2 to 3 related questions they could ask instead, "
        "based on what data actually exists in the schema. "
        "Return only a JSON array of question strings, no markdown, no explanation."
    )

    user_message = f"Schema:\n{schema}\n\nOriginal question: {question}\n\nSuggest 2-3 related questions the user could ask instead."

    response = client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    raw = response.choices[0].message.content or ""
    # strip markdown fences in case the model wraps the array
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw.strip())
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []
