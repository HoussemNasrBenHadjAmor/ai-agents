import os

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# AI PROVIDER
# ============================================================

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


# ============================================================
# AGENT LIMITS
# ============================================================

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


# ============================================================
# AI PRICING
#
# These values represent USD per 1 million tokens.
#
# They are configurable because model/provider prices can change.
# ============================================================

AI_CACHE_HIT_COST_PER_1M_OFF_PEAK = float(
    os.getenv(
        "AI_CACHE_HIT_COST_PER_1M_OFF_PEAK",
        "0",
    )
)


AI_CACHE_MISS_COST_PER_1M_OFF_PEAK = float(
    os.getenv(
        "AI_CACHE_MISS_COST_PER_1M_OFF_PEAK",
        "0",
    )
)


AI_OUTPUT_COST_PER_1M_OFF_PEAK = float(
    os.getenv(
        "AI_OUTPUT_COST_PER_1M_OFF_PEAK",
        "0",
    )
)


AI_CACHE_HIT_COST_PER_1M_PEAK = float(
    os.getenv(
        "AI_CACHE_HIT_COST_PER_1M_PEAK",
        "0",
    )
)


AI_CACHE_MISS_COST_PER_1M_PEAK = float(
    os.getenv(
        "AI_CACHE_MISS_COST_PER_1M_PEAK",
        "0",
    )
)


AI_OUTPUT_COST_PER_1M_PEAK = float(
    os.getenv(
        "AI_OUTPUT_COST_PER_1M_PEAK",
        "0",
    )
)


AI_PEAK_WINDOWS_UTC = os.getenv(
    "AI_PEAK_WINDOWS_UTC",
    "01:00-04:00,06:00-10:00",
)


AI_PRICING_CURRENCY = os.getenv(
    "AI_PRICING_CURRENCY",
    "USD",
)


# ============================================================
# VALIDATION
# ============================================================

if not AI_API_KEY:
    raise RuntimeError("AI_API_KEY is not configured.")
