import json

from config import AI_MODEL, AI_PROVIDER
from llm import chat
from tools.tool_registry import TOOLS, TOOL_FUNCTIONS


SYSTEM_PROMPT = """
You are an AI DevOps diagnostic agent.

Your job is to investigate infrastructure problems using the tools
available to you.

Rules:

- Use tools whenever actual server information is required.
- Never invent container statuses, logs, metrics, or errors.
- Never claim to have checked something unless a tool actually checked it.
- Prefer evidence from tools over assumptions.
- The currently available tools are read-only.
"""


def execute_tool(tool_call):
    tool_name = tool_call.function.name

    arguments = json.loads(
        tool_call.function.arguments or "{}"
    )

    if tool_name not in TOOL_FUNCTIONS:
        return f"ERROR: Unknown tool: {tool_name}"

    function = TOOL_FUNCTIONS[tool_name]

    try:
        result = function(**arguments)
        return result
    except Exception as exc:
        return f"ERROR executing {tool_name}: {exc}"


def run_agent(user_message):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    max_iterations = 10

    for iteration in range(max_iterations):

        print(f"\n[Agent iteration {iteration + 1}]")

        response = chat(
            messages=messages,
            tools=TOOLS,
        )

        # Add DeepSeek's response to conversation history.
        messages.append(response)

        # If DeepSeek doesn't request any tools,
        # it has produced its final answer.
        if not response.tool_calls:
            return response.content

        # DeepSeek requested one or more tools.
        for tool_call in response.tool_calls:

            tool_name = tool_call.function.name

            print(f"[Tool requested] {tool_name}")
            print(
                f"[Arguments] "
                f"{tool_call.function.arguments}"
            )

            tool_result = execute_tool(tool_call)

            print(f"[Tool completed] {tool_name}")

            # Return the real tool result to DeepSeek.
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

    return (
        "Agent stopped because it reached the "
        "maximum number of iterations."
    )


def main():

    print()
    print("================================")
    print("      AI DEVOPS AGENT")
    print("================================")
    print()
    print(f"Provider : {AI_PROVIDER}")
    print(f"Model    : {AI_MODEL}")
    print()

    user_message = """
    Investigate my Docker server.

    Identify containers that appear to have real problems.

    If a container is restarting, unhealthy, or appears to have
    crashed unexpectedly, investigate further using available tools.

    Try to determine the likely cause of the problem.

    Do not modify, restart, stop, delete, or otherwise change anything.
    """

    print("User:")
    print(user_message)

    answer = run_agent(user_message)

    print()
    print("Agent:")
    print(answer)
    print()


if __name__ == "__main__":
    main()
