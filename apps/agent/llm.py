from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone

from openai import OpenAI

from config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_CACHE_HIT_COST_PER_1M_OFF_PEAK,
    AI_CACHE_MISS_COST_PER_1M_OFF_PEAK,
    AI_OUTPUT_COST_PER_1M_OFF_PEAK,
    AI_CACHE_HIT_COST_PER_1M_PEAK,
    AI_CACHE_MISS_COST_PER_1M_PEAK,
    AI_OUTPUT_COST_PER_1M_PEAK,
    AI_PEAK_WINDOWS_UTC,
)

# ============================================================
# OPENAI-COMPATIBLE CLIENT
# ============================================================

client = OpenAI(
    api_key=AI_API_KEY,
    base_url=AI_BASE_URL,
)


# ============================================================
# USAGE STATISTICS
# ============================================================


@dataclass
class UsageStats:

    # Number of actual calls made to the LLM provider.
    llm_calls: int = 0

    # Input token totals.
    input_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0

    # Generated output.
    output_tokens: int = 0

    # Thinking/reasoning tokens when reported.
    reasoning_tokens: int = 0

    # Provider-reported total.
    total_tokens: int = 0

    # Number of requests billed during each pricing period.
    peak_llm_calls: int = 0
    off_peak_llm_calls: int = 0

    # Token breakdown by pricing period.
    peak_cache_hit_tokens: int = 0
    peak_cache_miss_tokens: int = 0
    peak_output_tokens: int = 0

    off_peak_cache_hit_tokens: int = 0
    off_peak_cache_miss_tokens: int = 0
    off_peak_output_tokens: int = 0

    # Dollar estimate accumulated per API request.
    estimated_cost_usd: float = 0.0

    # Useful for debugging.
    pricing_periods_seen: set[str] = field(default_factory=set)


usage_context: ContextVar[UsageStats | None] = ContextVar(
    "usage_context",
    default=None,
)


# ============================================================
# USAGE CONTEXT
# ============================================================


def start_usage_tracking():
    """
    Start token/cost tracking for the current investigation.

    ContextVar makes this investigation-local so concurrent
    investigations do not intentionally share usage counters.
    """

    stats = UsageStats()

    token = usage_context.set(stats)

    return token


def stop_usage_tracking(
    token,
):
    """
    Stop tracking and return the accumulated statistics.
    """

    stats = usage_context.get()

    usage_context.reset(token)

    return stats


def get_current_usage():
    """
    Return current usage statistics if tracking is active.
    """

    return usage_context.get()


# ============================================================
# DEEPSEEK USAGE FIELD HELPERS
# ============================================================


def _usage_value(
    obj,
    field_name: str,
) -> int:
    """
    Read a numeric usage field safely.

    DeepSeek exposes some OpenAI-compatible extension fields,
    including:

      prompt_cache_hit_tokens
      prompt_cache_miss_tokens

    Depending on the installed OpenAI SDK version, those fields
    may be normal model attributes or appear in model_extra.
    """

    if obj is None:
        return 0

    value = getattr(
        obj,
        field_name,
        None,
    )

    if value is not None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    model_extra = getattr(
        obj,
        "model_extra",
        None,
    )

    if isinstance(
        model_extra,
        dict,
    ):
        value = model_extra.get(field_name)

        if value is not None:
            try:
                return int(value)
            except (
                TypeError,
                ValueError,
            ):
                return 0

    try:
        dumped = obj.model_dump()

        value = dumped.get(field_name)

        if value is not None:
            return int(value)

    except Exception:
        pass

    return 0


def _reasoning_tokens(
    usage,
) -> int:

    if usage is None:
        return 0

    details = getattr(
        usage,
        "completion_tokens_details",
        None,
    )

    if details is None:

        model_extra = getattr(
            usage,
            "model_extra",
            None,
        )

        if isinstance(
            model_extra,
            dict,
        ):
            details = model_extra.get("completion_tokens_details")

    if details is None:
        return 0

    if isinstance(
        details,
        dict,
    ):
        try:
            return int(
                details.get(
                    "reasoning_tokens",
                    0,
                )
                or 0
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

    return _usage_value(
        details,
        "reasoning_tokens",
    )


# ============================================================
# PRICING WINDOW
# ============================================================


def _clock_to_minutes(
    value: str,
) -> int:

    hours, minutes = value.strip().split(":")

    return int(hours) * 60 + int(minutes)


def _is_peak_time(
    moment: datetime,
) -> bool:
    """
    Determine whether the request started inside one of the
    configured DeepSeek peak windows.

    Example:
      01:00-04:00,06:00-10:00
    """

    utc_moment = moment.astimezone(timezone.utc)

    current_minutes = utc_moment.hour * 60 + utc_moment.minute

    for window in AI_PEAK_WINDOWS_UTC.split(","):

        window = window.strip()

        if not window:
            continue

        try:

            start_text, end_text = window.split(
                "-",
                1,
            )

            start = _clock_to_minutes(start_text)

            end = _clock_to_minutes(end_text)

        except Exception:
            continue

        # Normal same-day window.
        if start < end:

            if start <= current_minutes < end:
                return True

        # Handles a window that crosses midnight.
        elif start > end:

            if current_minutes >= start or current_minutes < end:
                return True

        # start == end means the entire day.
        else:
            return True

    return False


# ============================================================
# COST CALCULATION
# ============================================================


def _calculate_request_cost(
    *,
    cache_hit_tokens: int,
    cache_miss_tokens: int,
    output_tokens: int,
    peak: bool,
) -> float:

    if peak:

        hit_rate = AI_CACHE_HIT_COST_PER_1M_PEAK

        miss_rate = AI_CACHE_MISS_COST_PER_1M_PEAK

        output_rate = AI_OUTPUT_COST_PER_1M_PEAK

    else:

        hit_rate = AI_CACHE_HIT_COST_PER_1M_OFF_PEAK

        miss_rate = AI_CACHE_MISS_COST_PER_1M_OFF_PEAK

        output_rate = AI_OUTPUT_COST_PER_1M_OFF_PEAK

    cache_hit_cost = cache_hit_tokens / 1_000_000 * hit_rate

    cache_miss_cost = cache_miss_tokens / 1_000_000 * miss_rate

    output_cost = output_tokens / 1_000_000 * output_rate

    return cache_hit_cost + cache_miss_cost + output_cost


# ============================================================
# CHAT
# ============================================================


def chat(
    messages,
    tools=None,
):
    """
    Execute one OpenAI-compatible chat completion.

    When usage tracking is active, this function automatically
    records:

      - LLM calls
      - input tokens
      - cache-hit tokens
      - cache-miss tokens
      - output tokens
      - reasoning tokens
      - total tokens
      - peak/off-peak usage
      - estimated USD cost
    """

    request = {
        "model": AI_MODEL,
        "messages": messages,
    }

    if tools:
        request["tools"] = tools

    # Pricing period is determined per API request.
    request_started_at = datetime.now(timezone.utc)

    peak = _is_peak_time(request_started_at)

    response = client.chat.completions.create(**request)

    stats = usage_context.get()

    if stats is not None:

        stats.llm_calls += 1

        usage = response.usage

        if usage is not None:

            input_tokens = _usage_value(
                usage,
                "prompt_tokens",
            )

            cache_hit_tokens = _usage_value(
                usage,
                "prompt_cache_hit_tokens",
            )

            cache_miss_tokens = _usage_value(
                usage,
                "prompt_cache_miss_tokens",
            )

            output_tokens = _usage_value(
                usage,
                "completion_tokens",
            )

            total_tokens = _usage_value(
                usage,
                "total_tokens",
            )

            reasoning_tokens = _reasoning_tokens(usage)

            # DeepSeek documents:
            #
            # prompt_tokens =
            #   prompt_cache_hit_tokens
            #   + prompt_cache_miss_tokens
            #
            # If the provider/SDK fails to expose that
            # breakdown, conservatively treat all input
            # tokens as cache misses for cost estimation.
            if cache_hit_tokens == 0 and cache_miss_tokens == 0 and input_tokens > 0:

                cache_miss_tokens = input_tokens

            if total_tokens == 0:

                total_tokens = input_tokens + output_tokens

            request_cost = _calculate_request_cost(
                cache_hit_tokens=cache_hit_tokens,
                cache_miss_tokens=cache_miss_tokens,
                output_tokens=output_tokens,
                peak=peak,
            )

            stats.input_tokens += input_tokens

            stats.cache_hit_tokens += cache_hit_tokens

            stats.cache_miss_tokens += cache_miss_tokens

            stats.output_tokens += output_tokens

            stats.reasoning_tokens += reasoning_tokens

            stats.total_tokens += total_tokens

            stats.estimated_cost_usd += request_cost

            if peak:

                stats.peak_llm_calls += 1

                stats.pricing_periods_seen.add("peak")

                stats.peak_cache_hit_tokens += cache_hit_tokens

                stats.peak_cache_miss_tokens += cache_miss_tokens

                stats.peak_output_tokens += output_tokens

            else:

                stats.off_peak_llm_calls += 1

                stats.pricing_periods_seen.add("off_peak")

                stats.off_peak_cache_hit_tokens += cache_hit_tokens

                stats.off_peak_cache_miss_tokens += cache_miss_tokens

                stats.off_peak_output_tokens += output_tokens

    return response.choices[0].message
