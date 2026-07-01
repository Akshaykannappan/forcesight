"""App configuration and environment variable loading."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from the .env file sitting in backend/
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  # points to backend/

class Settings:
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # resolve DB_PATH relative to backend/ so it works no matter where uvicorn is invoked from
    DB_PATH: str = str((BASE_DIR / os.getenv("DB_PATH", "../DB/forcesight.db")).resolve())

    MAX_SQL_RETRIES: int = 2
    DEFAULT_ROW_LIMIT: int = 100

settings = Settings()

if not settings.OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is missing. Check that backend/.env exists and contains it."
    )