import json

from config import ORCHESTRATOR_MAX_ITERATIONS
from events import EventCallback, emit
from llm import chat

ORCHESTRATOR_SYSTEM_PROMPT = """
You are an infrastructure investigation orchestrator.

You do not directly inspect infrastructure.

You have three specialist agents:

1. docker_agent

Use for:

- Docker containers
- container logs
- crash loops
- unhealthy containers
- Docker networks
- Docker volumes
- Docker Compose
- Docker resource usage
- Docker configuration

2. database_agent

Use for:

- PostgreSQL
- database tables
- application data
- database connections
- locks
- blocked queries
- long-running queries
- database size
- database statistics
- incidents stored in databases

3. network_agent

Use for:

- DNS resolution
- HTTP connectivity
- HTTPS connectivity
- TCP ports
- listening ports
- host network configuration
- routes
- connectivity problems

Your job is to decide which specialist agent or agents should
investigate the user's request.

Use specialists instead of guessing.

If a problem could involve multiple systems, you may use
multiple specialists.

After receiving specialist results, analyze the evidence
together and produce one final answer.

Never claim a system was inspected unless a specialist
actually inspected it.

Everything must remain read-only.

Never ask a specialist to modify infrastructure.
"""


ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "docker_agent",
            "description": (
                "Ask the Docker specialist to investigate "
                "containers, logs, networks, volumes, "
                "Compose, resource usage, crashes, "
                "or other Docker-related problems."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": (
                            "Detailed investigation task " "for the Docker specialist."
                        ),
                    }
                },
                "required": [
                    "task",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "database_agent",
            "description": (
                "Ask the PostgreSQL specialist to investigate "
                "database state, connections, locks, tables, "
                "application data, statistics, incidents, "
                "or database problems."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": (
                            "Detailed investigation task "
                            "for the database specialist."
                        ),
                    }
                },
                "required": [
                    "task",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "network_agent",
            "description": (
                "Ask the network specialist to investigate "
                "DNS, HTTP/HTTPS connectivity, TCP ports, "
                "listening ports, routes, or host networking."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": ("Detailed network investigation task."),
                    }
                },
                "required": [
                    "task",
                ],
                "additionalProperties": False,
            },
        },
    },
]


class Orchestrator:

    def __init__(
        self,
        docker_agent,
        database_agent,
        network_agent,
    ):
        self.docker_agent = docker_agent
        self.database_agent = database_agent
        self.network_agent = network_agent

    async def execute_specialist(
        self,
        tool_name: str,
        arguments: dict,
        event_callback: EventCallback = None,
    ) -> str:

        task = arguments.get(
            "task",
            "",
        )

        if tool_name == "docker_agent":

            print()
            print("[Orchestrator → Docker Agent]")
            print(task)

            await emit(
                event_callback,
                "specialist_selected",
                agent="docker",
                message="Docker Agent selected",
            )

            return await self.docker_agent.run(
                task,
                event_callback=event_callback,
            )

        if tool_name == "database_agent":

            print()
            print("[Orchestrator → Database Agent]")
            print(task)

            await emit(
                event_callback,
                "specialist_selected",
                agent="database",
                message="Database Agent selected",
            )

            return await self.database_agent.run(
                task,
                event_callback=event_callback,
            )

        if tool_name == "network_agent":

            print()
            print("[Orchestrator → Network Agent]")
            print(task)

            await emit(
                event_callback,
                "specialist_selected",
                agent="network",
                message="Network Agent selected",
            )

            return await self.network_agent.run(
                task,
                event_callback=event_callback,
            )

        return f"ERROR: Unknown specialist: " f"{tool_name}"

    async def run(
        self,
        user_message: str,
        event_callback: EventCallback = None,
    ) -> str:

        await emit(
            event_callback,
            "investigation_started",
            message="Investigation started",
        )

        messages = [
            {
                "role": "system",
                "content": ORCHESTRATOR_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        for iteration in range(ORCHESTRATOR_MAX_ITERATIONS):

            print()
            print(
                f"[Orchestrator iteration "
                f"{iteration + 1}/"
                f"{ORCHESTRATOR_MAX_ITERATIONS}]"
            )

            response = chat(
                messages=messages,
                tools=ORCHESTRATOR_TOOLS,
            )

            messages.append(response)

            if not response.tool_calls:

                await emit(
                    event_callback,
                    "investigation_completed",
                    message="Investigation completed",
                )

                return response.content

            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name

                try:

                    arguments = json.loads(tool_call.function.arguments or "{}")

                except json.JSONDecodeError:

                    arguments = {}

                print(f"[Specialist requested] " f"{tool_name}")

                result = await self.execute_specialist(
                    tool_name,
                    arguments,
                    event_callback=event_callback,
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        await emit(
            event_callback,
            "synthesizing",
            message="Combining specialist findings",
        )

        messages.append(
            {
                "role": "user",
                "content": """
You have reached the maximum orchestration rounds.

Do not request additional specialists.

Using all specialist evidence already collected,
provide the final combined diagnosis now.

Clearly explain:

1. Confirmed problems
2. Which system is affected
3. Likely root causes
4. Remaining uncertainty
5. Recommended next read-only investigation

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
            "investigation_completed",
            message="Investigation completed",
        )

        return final_response.content
