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


def chat(messages, tools=None):
    request = {
        "model": AI_MODEL,
        "messages": messages,
    }

    if tools:
        request["tools"] = tools

    response = client.chat.completions.create(**request)

    return response.choices[0].message
