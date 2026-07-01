# ForceSight Text-to-SQL Query Assistant

An LLM-powered chatbot that converts natural language questions into SQL, executes them against a local database, and returns plain-English answers — built for the ForceSight technical assignment.

## Architecture Overview

The app implements a four-stage pipeline, with a safety and self-correction layer wrapped around it:

```
User question (frontend)
│
▼
POST /chat (FastAPI)
│
▼
Stage 0 — Intent check
(LLM classifies: clear question / gibberish / unrelated to DB)
│ if unclear → return clarifying questions to the user
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
├── on zero rows: suggest_alternatives() returns related questions
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
- `app/llm.py` — OpenAI SDK configured against OpenRouter's base URL; four functions: `check_intent()` (Stage 0), `generate_sql()` (Stage 1), `summarize_result()` (Stage 3), `suggest_alternatives()` (zero-results fallback)
- `app/models.py` — Pydantic request/response schemas matching the API contract
- `app/routes.py` — orchestrates the full pipeline with a retry-on-error loop
- `main.py` — FastAPI app entrypoint, CORS, health check

**Frontend (`/frontend`)** — React 19 + Vite 8 chat interface with a typing indicator, loading/cancel state, clickable suggestion chips for clarification responses, and a collapsible "View SQL" section per response.

**Database** — SQLite (`DB/forcesight.db`), 4 tables (`users`, `products`, `orders`, `support_tickets`) with foreign key relationships, seeded from `DB/schema_and_data.sql`.

## Key Design Decisions & Trade-offs

- **SQLite over MySQL**: simpler local setup with no server/auth overhead, and explicitly allowed by the assignment. Trade-off: SQLite has no native read-only DB user, so the read-only guarantee is enforced at two layers instead — the SQL validator (rejects non-SELECT) and the connection itself, which is opened in SQLite's read-only URI mode (`mode=ro`), so even a validator bypass would still fail at the DB layer.
- **Two separate LLM calls instead of one**: keeps the SQL-generation prompt uncontaminated by summarization instructions, and maps cleanly onto the pipeline stages in the spec.
- **Stage 0 intent check**: before any SQL is generated, the LLM classifies the question as clear / gibberish / unrelated-to-DB. Gibberish and off-topic inputs get schema-grounded clarifying questions back immediately without wasting a SQL generation call.
- **Zero-results handling**: when valid SQL runs but returns no rows, `suggest_alternatives()` asks the LLM for 2–3 related questions the user could ask instead, returned as clickable chips in the UI.
- **No LangChain/LangGraph/RAG**: the schema is 4 tables and fits entirely in the prompt context; direct OpenAI SDK calls keep the prompt logic fully visible and debuggable.
- **Retry-on-error loop**: if generated SQL fails validation or execution, the error is fed back to the model for self-correction (max 2 retries).
- **Dynamic schema introspection**: schema context is built from SQLite's own metadata at runtime rather than hardcoded as a string, so it survives schema changes without a code edit.

## Setup & Execution

### Prerequisites
- Python 3.11–3.13 (3.14 currently has wheel-compatibility issues with `pydantic-core`)
- Node.js 18+ (for the frontend)
- An OpenRouter API key (https://openrouter.ai)

### Database

The `DB/forcesight.db` file is already present in the repo. If you need to recreate it from scratch:

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
python main.py
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
> A: "Hyderabad has the highest sales, totaling 9,498."

**Q: Which product generated the highest total revenue?**
> SQL: `SELECT p.name, SUM(o.total_amount) as total_revenue FROM orders o JOIN products p ON o.product_id = p.product_id GROUP BY p.product_id ORDER BY total_revenue DESC LIMIT 1`
> A: "The Mechanical Keyboard generated the highest total revenue, totaling $9,998."

**Q: How many high-priority support tickets are still open?**
> SQL: `SELECT COUNT(*) as open_high_priority_tickets FROM support_tickets WHERE priority = 'high' AND status = 'open' LIMIT 100`
> A: "There are currently 2 open high-priority support tickets."

**Q: Show all cancelled orders along with the customer name.**
> SQL: `SELECT o.order_id, u.name FROM orders o JOIN users u ON o.user_id = u.user_id WHERE o.status = 'cancelled' LIMIT 100`
> A: "There is one cancelled order, which belongs to Eva Pillai."

**Q: Which user has spent the most money overall?**
> SQL: `SELECT u.name, u.email, SUM(o.total_amount) as total_spent FROM orders o JOIN users u ON o.user_id = u.user_id GROUP BY u.user_id ORDER BY total_spent DESC LIMIT 1`
> A: "Eva Pillai has spent the most money overall, totaling $9,498."

## Tech Stack
| Layer | Choice |
|---|---|
| Database | SQLite |
| Backend | FastAPI + Uvicorn |
| LLM Integration | OpenAI Python SDK → OpenRouter (`openai/gpt-4o-mini`) |
| Frontend | React 19 + Vite 8 |
| Config | `.env` (excluded from version control) |
