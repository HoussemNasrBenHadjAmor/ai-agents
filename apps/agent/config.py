import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


AI_PROVIDER = os.getenv("AI_PROVIDER")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("AI_MODEL")
AI_API_KEY = os.getenv("AI_API_KEY")

AGENT_MAX_ITERATIONS = int(
    os.getenv(
        "AGENT_MAX_ITERATIONS",
        "2",
    )
)

ORCHESTRATOR_MAX_ITERATIONS = int(os.getenv("ORCHESTRATOR_MAX_ITERATIONS", "2"))

required_variables = {
    "AI_PROVIDER": AI_PROVIDER,
    "AI_BASE_URL": AI_BASE_URL,
    "AI_MODEL": AI_MODEL,
    "AI_API_KEY": AI_API_KEY,
}


missing_variables = [name for name, value in required_variables.items() if not value]


if missing_variables:
    raise RuntimeError(
        "Missing required environment variables: " + ", ".join(missing_variables)
    )
