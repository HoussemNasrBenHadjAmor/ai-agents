from contextvars import ContextVar
from dataclasses import dataclass

from openai import OpenAI

from config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
)

client = OpenAI(
    api_key=AI_API_KEY,
    base_url=AI_BASE_URL,
)


@dataclass
class UsageStats:
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


usage_context: ContextVar[UsageStats | None] = ContextVar(
    "usage_context",
    default=None,
)


def start_usage_tracking():
    """
    Start usage tracking for the current investigation context.

    Returns a ContextVar token that must later be passed to
    stop_usage_tracking().
    """

    stats = UsageStats()

    token = usage_context.set(stats)

    return token


def stop_usage_tracking(
    token,
):
    """
    Stop usage tracking and return the collected statistics.
    """

    stats = usage_context.get()

    usage_context.reset(token)

    return stats


def get_current_usage():
    """
    Return current usage statistics if tracking is active.
    """

    return usage_context.get()


def chat(
    messages,
    tools=None,
):
    """
    Send one chat completion request.

    Any token usage reported by the provider is automatically
    accumulated in the active UsageStats context.
    """

    request = {
        "model": AI_MODEL,
        "messages": messages,
    }

    if tools:
        request["tools"] = tools

    response = client.chat.completions.create(**request)

    stats = usage_context.get()

    if stats is not None:

        stats.llm_calls += 1

        usage = response.usage

        if usage is not None:

            input_tokens = (
                getattr(
                    usage,
                    "prompt_tokens",
                    0,
                )
                or 0
            )

            output_tokens = (
                getattr(
                    usage,
                    "completion_tokens",
                    0,
                )
                or 0
            )

            total_tokens = getattr(
                usage,
                "total_tokens",
                0,
            ) or (input_tokens + output_tokens)

            stats.input_tokens += input_tokens

            stats.output_tokens += output_tokens

            stats.total_tokens += total_tokens

    return response.choices[0].message
