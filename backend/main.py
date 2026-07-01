"""ForceSight Text-to-SQL Assistant. Run with: uvicorn main:app --reload --port 8000"""

import logging
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(
    title="ForceSight Text-to-SQL Assistant",
    description=(
        "LLM-powered chatbot that converts natural language questions into "
        "SQL queries and returns human-readable answers."
    ),
    version="1.0.0",
)

# fine for local dev, but in production lock this down to the actual frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def health_check() -> dict:
    return {"status": "ok", "service": "ForceSight Text-to-SQL Assistant"}


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Starting ForceSight API server...")
    logger.info("Local URL: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
