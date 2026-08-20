import json

from config import AGENT_MAX_ITERATIONS
from events import EventCallback, emit
from llm import chat
from mcp_client import DockerMCPClient

DOCKER_SYSTEM_PROMPT = """
You are a Docker infrastructure diagnostic agent.

Your responsibility is to investigate Docker-related problems
using the read-only Docker tools available to you.

You may investigate:

- containers
- crash loops
- unhealthy containers
- logs
- Docker configuration
- Docker networks
- Docker volumes
- Docker Compose
- resource usage
- image information
- likely Docker-related root causes

Rules:

- Use tools whenever real Docker information is required.
- Never invent container status, logs, metrics, configuration,
  networks, volumes, or errors.
- Never claim to have inspected something unless a tool checked it.
- Prefer evidence from tools over assumptions.
- Investigate problems instead of stopping at the first symptom.
- Distinguish expected exited one-shot containers from actual failures.

Safety:

- You have read-only access.
- Never modify Docker infrastructure.
- Never start containers.
- Never stop containers.
- Never restart containers.
- Never remove containers.
- Never execute commands inside containers.
- Never create or modify Docker networks.
- Never create or modify Docker volumes.
- Never modify Docker configuration.
- Never attempt to bypass the read-only restrictions.
"""


class DockerAgent:

    def __init__(self):
        self.mcp = DockerMCPClient()

    async def connect(self):
        await self.mcp.connect()

        print(
            f"[Docker Agent] Connected with "
            f"{len(self.mcp.tools)} approved MCP tools."
        )

    async def close(self):
        await self.mcp.close()

    async def run(
        self,
        user_message: str,
        event_callback: EventCallback = None,
    ) -> str:

        await emit(
            event_callback,
            "agent_started",
            agent="docker",
            message="Docker Agent started",
        )

        messages = [
            {
                "role": "system",
                "content": DOCKER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        tools = self.mcp.get_deepseek_tools()

        for iteration in range(AGENT_MAX_ITERATIONS):

            print()
            print(
                f"[Docker Agent iteration "
                f"{iteration + 1}/"
                f"{AGENT_MAX_ITERATIONS}]"
            )

            response = chat(
                messages=messages,
                tools=tools,
            )

            messages.append(response)

            if not response.tool_calls:

                await emit(
                    event_callback,
                    "agent_completed",
                    agent="docker",
                    message="Docker Agent completed",
                )

                return response.content

            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")

                except json.JSONDecodeError:
                    arguments = {}

                print(f"[Docker MCP] {tool_name}")

                print(f"[Arguments] " f"{json.dumps(arguments)}")

                await emit(
                    event_callback,
                    "tool_started",
                    agent="docker",
                    tool=tool_name,
                    arguments=arguments,
                )

                try:

                    result = await self.mcp.call_tool(
                        tool_name,
                        arguments,
                    )

                except Exception as exc:

                    result = f"ERROR executing " f"{tool_name}: {exc}"

                await emit(
                    event_callback,
                    "tool_completed",
                    agent="docker",
                    tool=tool_name,
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": """
You have reached the maximum number of investigation rounds.

Do not request any more tools.

Using only the evidence already collected, provide your best
Docker diagnosis now.

Clearly separate:

1. Confirmed problems
2. Likely root causes
3. Things that could not yet be confirmed
4. Recommended next read-only investigation steps

Do not modify anything.
""",
            }
        )

        final_response = chat(
            messages=messages,
            tools=None,
        )

        await emit(
            event_callback,
            "agent_completed",
            agent="docker",
            message="Docker Agent completed",
        )

        return final_response.content
