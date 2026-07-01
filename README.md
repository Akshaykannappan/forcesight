# ForceSight Text-to-SQL Query Assistant

An LLM-powered chatbot that converts natural language questions into SQL, executes them against a local database, and returns plain-English answers — built for the ForceSight technical assignment.

## Architecture Overview

The app implements a three-stage pipeline, with a safety and self-correction layer wrapped around it:

```
User question (frontend)
│
▼
POST /chat (FastAPI)
│
▼
Stage 1 — NL → SQL
(OpenRouter LLM call, schema injected into prompt)
│
▼
Validation layer
(blocks non-SELECT statements, query stacking, forces LIMIT)
│
▼
Stage 2 — SQL → Result
(executed against SQLite, opened in read-only mode)
│
├── on error: error fed back to Stage 1 for retry (max 2 retries)
▼
Stage 3 — Result → Summary
(second OpenRouter LLM call, converts rows to plain English)
│
▼
JSON response → rendered in chat UI
```

**Backend (`/backend`)** — FastAPI, modular by responsibility:
- `app/config.py` — environment/config loading
- `app/database.py` — SQLite connection (opened read-only) and query execution
- `app/schema_context.py` — builds schema description dynamically from SQLite metadata (not hardcoded), so it stays correct if the schema changes
- `app/sql_validator.py` — safety gate: rejects any non-SELECT statement, blocks statement stacking, auto-adds a row LIMIT
- `app/llm.py` — OpenAI SDK configured against OpenRouter's base URL; two functions: `generate_sql()` (Stage 1) and `summarize_result()` (Stage 3)
- `app/models.py` — Pydantic request/response schemas matching the API contract
- `app/routes.py` — orchestrates the full pipeline with a retry-on-error loop
- `main.py` — FastAPI app entrypoint, CORS, health check

**Frontend (`/frontend`)** — React + Vite chat interface with a loading/cancel state and a collapsible "View SQL" section per response.

**Database** — SQLite (`DB/forcesight.db`), 4 tables (`users`, `products`, `orders`, `support_tickets`) with foreign key relationships, seeded from the provided schema/data dump.

## Key Design Decisions & Trade-offs

- **SQLite over MySQL**: simpler local setup with no server/auth overhead, and explicitly allowed by the assignment. Trade-off: SQLite has no native read-only DB user, so the read-only guarantee is enforced at two layers instead — the SQL validator (rejects non-SELECT) and the connection itself, which is opened in SQLite's read-only URI mode (`mode=ro`), so even a validator bypass would still fail at the DB layer.
- **Two separate LLM calls instead of one**: keeps the SQL-generation prompt uncontaminated by summarization instructions, and maps cleanly onto the three explicit pipeline stages in the spec.
- **No LangChain/LangGraph/RAG**: the schema is 4 tables and fits entirely in the prompt context; retrieval-based schema selection or multi-step agent orchestration would add dependency weight and failure surface without solving a problem this scope actually has. Direct OpenAI SDK calls keep the prompt logic fully visible and debuggable.
- **Retry-on-error loop**: if generated SQL fails validation or execution, the error is fed back to the model for self-correction (max 2 retries), since first-pass LLM SQL generation is not 100% reliable.
- **Dynamic schema introspection**: schema context is built from SQLite's own metadata at runtime rather than hardcoded as a string, so it survives schema changes without a code edit.

## Setup & Execution

### Prerequisites
- Python 3.11–3.13 (3.14 currently has wheel-compatibility issues with `pydantic-core`)
- Node.js (for the frontend)
- An OpenRouter API key (https://openrouter.ai)

### Database
```bash
cd DB
python3 -c "
import sqlite3
conn = sqlite3.connect('forcesight.db')
conn.executescript(open('schema_and_data.sql').read())
conn.commit()
conn.close()
print('DB created')
"
```

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
DB_PATH=../DB/forcesight.db
```

Run the server:
```bash
uvicorn main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`).

## Sample Questions & Outputs

**Q: Which city has the most orders?**
> SQL: `SELECT u.city, COUNT(*) as order_count FROM orders o JOIN users u ON o.user_id = u.user_id GROUP BY u.city ORDER BY order_count DESC LIMIT 1`
> A: "Mumbai has the most orders, with a total of three."

**Q: Which city has the highest sales?**
> SQL: `SELECT u.city, SUM(o.total_amount) as total_sales FROM orders o JOIN users u ON o.user_id = u.user_id GROUP BY u.city ORDER BY total_sales DESC LIMIT 1`
> A: [insert actual output from your run]

**Q: Which product generated the highest total revenue?**
> [insert actual output from your run]

**Q: How many high-priority support tickets are still open?**
> [insert actual output from your run]

**Q: Show all cancelled orders along with the customer name.**
> [insert actual output from your run]

*(Replace the bracketed placeholders with real outputs from your own test runs before submitting — screenshot or paste exact text.)*

## Tech Stack
| Layer | Choice |
|---|---|
| Database | SQLite |
| Backend | FastAPI |
| LLM Integration | OpenAI Python SDK → OpenRouter (`openai/gpt-4o-mini`) |
| Frontend | React + Vite |
| Config | `.env` (excluded from version control) |
# ForceSight
