import os

from dotenv import load_dotenv

load_dotenv()


AI_PROVIDER = os.getenv(
    "AI_PROVIDER",
    "deepseek",
)


AI_API_KEY = os.getenv(
    "AI_API_KEY",
    "",
)


AI_BASE_URL = os.getenv(
    "AI_BASE_URL",
    "https://api.deepseek.com",
)


AI_MODEL = os.getenv(
    "AI_MODEL",
    "deepseek-v4-flash",
)


AGENT_MAX_ITERATIONS = int(
    os.getenv(
        "AGENT_MAX_ITERATIONS",
        "2",
    )
)


ORCHESTRATOR_MAX_ITERATIONS = int(
    os.getenv(
        "ORCHESTRATOR_MAX_ITERATIONS",
        "2",
    )
)


AI_INPUT_COST_PER_1M = float(
    os.getenv(
        "AI_INPUT_COST_PER_1M",
        "0",
    )
)


AI_OUTPUT_COST_PER_1M = float(
    os.getenv(
        "AI_OUTPUT_COST_PER_1M",
        "0",
    )
)


if not AI_API_KEY:
    raise RuntimeError("AI_API_KEY is not configured.")
