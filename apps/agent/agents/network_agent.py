import json

from config import AGENT_MAX_ITERATIONS
from events import EventCallback, emit
from llm import chat

from tools.network_tools import (
    check_http,
    check_tcp_port,
    get_host_network_info,
    resolve_dns,
)

NETWORK_SYSTEM_PROMPT = """
You are a network diagnostic agent.

Your responsibility is to investigate network-related
problems using the read-only tools available to you.

You may investigate:

- DNS resolution
- HTTP connectivity
- HTTPS connectivity
- TCP port connectivity
- listening ports
- host IP configuration
- routing information
- service connectivity

Rules:

- Use tools whenever real network information is required.
- Never invent DNS results, HTTP responses, ports,
  connectivity, addresses, or routes.
- Never claim something was checked unless a tool checked it.
- Prefer evidence over assumptions.
- Investigate likely root causes when connectivity fails.

Safety:

- Everything is read-only.
- Never modify network configuration.
- Never change DNS configuration.
- Never modify routes.
- Never change firewall rules.
- Never open or close ports.
- Never execute arbitrary shell commands.
- Never attempt to bypass these restrictions.
"""


NETWORK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "resolve_dns",
            "description": ("Resolve a hostname and return " "its IP addresses."),
            "parameters": {
                "type": "object",
                "properties": {
                    "hostname": {
                        "type": "string",
                        "description": "Hostname to resolve.",
                    }
                },
                "required": [
                    "hostname",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_tcp_port",
            "description": (
                "Test whether a TCP connection "
                "can be established to a host and port."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                    },
                    "port": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 65535,
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": [
                    "host",
                    "port",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_http",
            "description": (
                "Perform a read-only HTTP or HTTPS "
                "request and return the response status."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                    },
                    "timeout": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 15,
                    },
                },
                "required": [
                    "url",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_host_network_info",
            "description": (
                "Inspect host IP addresses, routes, " "and listening TCP ports."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
]


NETWORK_FUNCTIONS = {
    "resolve_dns": resolve_dns,
    "check_tcp_port": check_tcp_port,
    "check_http": check_http,
    "get_host_network_info": get_host_network_info,
}


class NetworkAgent:

    async def connect(self):

        print(
            f"[Network Agent] Ready with " f"{len(NETWORK_TOOLS)} " "read-only tools."
        )

    async def close(self):
        pass

    async def run(
        self,
        user_message: str,
        event_callback: EventCallback = None,
    ) -> str:

        await emit(
            event_callback,
            "agent_started",
            agent="network",
            message="Network Agent started",
        )

        messages = [
            {
                "role": "system",
                "content": NETWORK_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        for iteration in range(AGENT_MAX_ITERATIONS):

            print()
            print(
                f"[Network Agent iteration "
                f"{iteration + 1}/"
                f"{AGENT_MAX_ITERATIONS}]"
            )

            response = chat(
                messages=messages,
                tools=NETWORK_TOOLS,
            )

            messages.append(response)

            if not response.tool_calls:

                await emit(
                    event_callback,
                    "agent_completed",
                    agent="network",
                    message="Network Agent completed",
                )

                return response.content

            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")

                except json.JSONDecodeError:
                    arguments = {}

                print(f"[Network Tool] {tool_name}")

                print(f"[Arguments] " f"{json.dumps(arguments)}")

                await emit(
                    event_callback,
                    "tool_started",
                    agent="network",
                    tool=tool_name,
                    arguments=arguments,
                )

                function = NETWORK_FUNCTIONS.get(tool_name)

                if function is None:

                    result = f"ERROR: Unknown network " f"tool: {tool_name}"

                else:

                    try:

                        result = function(**arguments)

                    except Exception as exc:

                        result = f"ERROR executing " f"{tool_name}: {exc}"

                await emit(
                    event_callback,
                    "tool_completed",
                    agent="network",
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
network diagnosis now.

Clearly separate:

1. Confirmed findings
2. Likely root cause
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
            agent="network",
            message="Network Agent completed",
        )

        return final_response.content
