import asyncio
import json
import sys
import time

from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
)

from fastapi.responses import (
    StreamingResponse,
)

from pydantic import BaseModel

# ============================================================
# AGENT IMPORT PATH
# ============================================================

AGENT_PATH = Path(__file__).resolve().parents[1] / "agent"

sys.path.insert(
    0,
    str(AGENT_PATH),
)


# ============================================================
# AGENT IMPORTS
# ============================================================

from agents.database_agent import DatabaseAgent
from agents.docker_agent import DockerAgent
from agents.network_agent import NetworkAgent
from agents.orchestrator import Orchestrator

from config import (
    AI_MODEL,
    AI_PRICING_CURRENCY,
    AI_CACHE_HIT_COST_PER_1M_OFF_PEAK,
    AI_CACHE_MISS_COST_PER_1M_OFF_PEAK,
    AI_OUTPUT_COST_PER_1M_OFF_PEAK,
    AI_CACHE_HIT_COST_PER_1M_PEAK,
    AI_CACHE_MISS_COST_PER_1M_PEAK,
    AI_OUTPUT_COST_PER_1M_PEAK,
)

from llm import (
    start_usage_tracking,
    stop_usage_tracking,
)

from history import (
    complete_investigation,
    create_investigation,
    fail_investigation,
    get_investigation,
    init_history_database,
    list_investigations,
    save_event,
)

# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="AI DevOps Agent API",
    version="0.4.0",
)


docker_agent = None
database_agent = None
network_agent = None
orchestrator = None


class InvestigationRequest(BaseModel):
    message: str


# ============================================================
# METRIC BUILDER
# ============================================================


def build_metrics(
    *,
    usage,
    duration_seconds: float,
    agents_used,
    tool_calls: int,
) -> dict:

    if usage is None:

        return {
            "duration_seconds": round(
                duration_seconds,
                2,
            ),
            "agents_used": sorted(agents_used),
            "tool_calls": tool_calls,
            "llm_calls": 0,
            "input_tokens": 0,
            "input_cache_hit_tokens": 0,
            "input_cache_miss_tokens": 0,
            "cache_hit_ratio_percent": 0.0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "total_tokens": 0,
            "peak_llm_calls": 0,
            "off_peak_llm_calls": 0,
            "pricing_period": "unknown",
            "estimated_cost_usd": 0.0,
            "pricing_currency": AI_PRICING_CURRENCY,
            "pricing_model": AI_MODEL,
        }

    input_tokens = usage.input_tokens

    cache_hit_tokens = usage.cache_hit_tokens

    cache_miss_tokens = usage.cache_miss_tokens

    if input_tokens > 0:

        cache_hit_ratio = cache_hit_tokens / input_tokens * 100

    else:

        cache_hit_ratio = 0.0

    periods = usage.pricing_periods_seen

    if periods == {"peak"}:

        pricing_period = "peak"

    elif periods == {"off_peak"}:

        pricing_period = "off_peak"

    elif len(periods) > 1:

        pricing_period = "mixed"

    else:

        pricing_period = "unknown"

    return {
        # Execution
        "duration_seconds": round(
            duration_seconds,
            2,
        ),
        "agents_used": sorted(agents_used),
        "tool_calls": tool_calls,
        "llm_calls": usage.llm_calls,
        # Input tokens
        "input_tokens": input_tokens,
        "input_cache_hit_tokens": cache_hit_tokens,
        "input_cache_miss_tokens": cache_miss_tokens,
        "cache_hit_ratio_percent": round(
            cache_hit_ratio,
            2,
        ),
        # Output
        "output_tokens": usage.output_tokens,
        "reasoning_tokens": usage.reasoning_tokens,
        "total_tokens": usage.total_tokens,
        # Pricing periods
        "peak_llm_calls": usage.peak_llm_calls,
        "off_peak_llm_calls": usage.off_peak_llm_calls,
        "pricing_period": pricing_period,
        # Detailed pricing-period tokens
        "peak_cache_hit_tokens": usage.peak_cache_hit_tokens,
        "peak_cache_miss_tokens": usage.peak_cache_miss_tokens,
        "peak_output_tokens": usage.peak_output_tokens,
        "off_peak_cache_hit_tokens": usage.off_peak_cache_hit_tokens,
        "off_peak_cache_miss_tokens": usage.off_peak_cache_miss_tokens,
        "off_peak_output_tokens": usage.off_peak_output_tokens,
        # Cost
        "estimated_cost_usd": round(
            usage.estimated_cost_usd,
            8,
        ),
        "pricing_currency": AI_PRICING_CURRENCY,
        "pricing_model": AI_MODEL,
        # Rates used
        "pricing_rates_per_1m": {
            "off_peak": {
                "cache_hit": AI_CACHE_HIT_COST_PER_1M_OFF_PEAK,
                "cache_miss": AI_CACHE_MISS_COST_PER_1M_OFF_PEAK,
                "output": AI_OUTPUT_COST_PER_1M_OFF_PEAK,
            },
            "peak": {
                "cache_hit": AI_CACHE_HIT_COST_PER_1M_PEAK,
                "cache_miss": AI_CACHE_MISS_COST_PER_1M_PEAK,
                "output": AI_OUTPUT_COST_PER_1M_PEAK,
            },
        },
    }


# ============================================================
# STARTUP
# ============================================================


@app.on_event("startup")
async def startup():

    global docker_agent
    global database_agent
    global network_agent
    global orchestrator

    print("[API] Initializing history database...")

    await init_history_database()

    print("[API] History database ready.")

    print("[API] Starting agents...")

    docker_agent = DockerAgent()

    database_agent = DatabaseAgent()

    network_agent = NetworkAgent()

    await docker_agent.connect()

    await database_agent.connect()

    await network_agent.connect()

    orchestrator = Orchestrator(
        docker_agent=docker_agent,
        database_agent=database_agent,
        network_agent=network_agent,
    )

    print("[API] Agents ready.")


# ============================================================
# SHUTDOWN
# ============================================================


@app.on_event("shutdown")
async def shutdown():

    print("[API] Closing agents...")

    if network_agent:
        await network_agent.close()

    if database_agent:
        await database_agent.close()

    if docker_agent:
        await docker_agent.close()


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
async def health():

    return {
        "status": "ok",
        "service": "ai-devops-api",
    }


# ============================================================
# NON-STREAM INVESTIGATION
# ============================================================


@app.post("/investigate")
async def investigate(
    request: InvestigationRequest,
):

    started_at = time.perf_counter()

    tool_calls = 0
    agents_used = set()

    async def metrics_callback(
        event: dict,
    ):

        nonlocal tool_calls

        if event.get("type") == "tool_started":
            tool_calls += 1

        if event.get("type") == "specialist_selected":

            agent = event.get("agent")

            if agent:
                agents_used.add(agent)

    usage_token = start_usage_tracking()

    usage_stopped = False

    try:

        diagnosis = await orchestrator.run(
            request.message,
            event_callback=metrics_callback,
        )

        usage = stop_usage_tracking(usage_token)

        usage_stopped = True

        duration_seconds = time.perf_counter() - started_at

        metrics = build_metrics(
            usage=usage,
            duration_seconds=duration_seconds,
            agents_used=agents_used,
            tool_calls=tool_calls,
        )

        return {
            "message": request.message,
            "diagnosis": diagnosis,
            "metrics": metrics,
            "result": diagnosis.get(
                "narrative",
                "",
            ),
        }

    finally:

        if not usage_stopped:

            try:

                stop_usage_tracking(usage_token)

            except Exception:
                pass


# ============================================================
# STREAM INVESTIGATION
# ============================================================


@app.post("/investigate/stream")
async def investigate_stream(
    request: InvestigationRequest,
):

    investigation = await create_investigation(request.message)

    investigation_id = investigation.id

    queue = asyncio.Queue()

    sequence = 0

    started_at = time.perf_counter()

    tool_calls = 0

    agents_used = set()

    async def event_callback(
        event: dict,
    ):

        nonlocal sequence
        nonlocal tool_calls

        sequence += 1

        if event.get("type") == "tool_started":

            tool_calls += 1

        if event.get("type") == "specialist_selected":

            agent = event.get("agent")

            if agent:

                agents_used.add(agent)

        await save_event(
            investigation_id,
            sequence,
            event,
        )

        await queue.put(event)

    async def run_investigation():

        usage_token = start_usage_tracking()

        usage_stopped = False

        try:

            diagnosis = await orchestrator.run(
                request.message,
                event_callback=event_callback,
            )

            usage = stop_usage_tracking(usage_token)

            usage_stopped = True

            duration_seconds = time.perf_counter() - started_at

            metrics = build_metrics(
                usage=usage,
                duration_seconds=duration_seconds,
                agents_used=agents_used,
                tool_calls=tool_calls,
            )

            await complete_investigation(
                investigation_id,
                diagnosis,
                metrics,
            )

            await queue.put(
                {
                    "type": "result",
                    "investigation_id": investigation_id,
                    "diagnosis": diagnosis,
                    "metrics": metrics,
                    "result": diagnosis.get(
                        "narrative",
                        "",
                    ),
                }
            )

        except Exception as exc:

            if not usage_stopped:

                try:

                    stop_usage_tracking(usage_token)

                except Exception:
                    pass

            error_message = str(exc)

            await fail_investigation(
                investigation_id,
                error_message,
            )

            await queue.put(
                {
                    "type": "error",
                    "investigation_id": investigation_id,
                    "message": error_message,
                }
            )

        finally:

            await queue.put(
                {
                    "type": "done",
                    "investigation_id": investigation_id,
                }
            )

    async def event_generator():

        yield (
            "data: "
            + json.dumps(
                {
                    "type": "investigation_created",
                    "investigation_id": investigation_id,
                }
            )
            + "\n\n"
        )

        task = asyncio.create_task(run_investigation())

        try:

            while True:

                event = await queue.get()

                yield ("data: " + json.dumps(event) + "\n\n")

                if event.get("type") == "done":

                    break

        finally:

            await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# HISTORY
# ============================================================


@app.get("/investigations")
async def investigations():

    return await list_investigations()


@app.get("/investigations/{investigation_id}")
async def investigation_detail(
    investigation_id: str,
):

    investigation = await get_investigation(investigation_id)

    if investigation is None:

        raise HTTPException(
            status_code=404,
            detail="Investigation not found",
        )

    return investigation
