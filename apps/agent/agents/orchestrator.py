import json

from pydantic import ValidationError

from config import ORCHESTRATOR_MAX_ITERATIONS
from diagnosis_schema import Diagnosis
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

Your job is to decide which specialist agent or agents
should investigate the user's request.

Use specialists instead of guessing.

If a problem could involve multiple systems,
you may use multiple specialists.

After receiving specialist results,
analyze the evidence together.

Never claim a system was inspected unless a specialist
actually inspected it.

Everything must remain read-only.

Never ask a specialist to modify infrastructure.

Do not expose private chain-of-thought.
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


DIAGNOSIS_JSON_SCHEMA = Diagnosis.model_json_schema()


STRUCTURED_FINAL_PROMPT = f"""
Using ONLY the specialist evidence already collected,
produce the final diagnosis as VALID JSON.

Do not use Markdown fences.

Do not return any text before or after the JSON.

Your response MUST conform to this JSON Schema:

{json.dumps(
    DIAGNOSIS_JSON_SCHEMA,
    indent=2,
)}

Rules:

- Never invent evidence.
- Only report findings supported by specialist results.
- Clearly state uncertainty where evidence is incomplete.
- Keep fields concise.
- Recommendations must remain read-only or require human action.
- Do not recommend automatic infrastructure modification.
- Do not expose private chain-of-thought.
- Return JSON only.
"""


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

    async def build_structured_diagnosis(
        self,
        messages: list,
        event_callback: EventCallback = None,
    ) -> dict:

        await emit(
            event_callback,
            "synthesizing",
            message="Building structured diagnosis",
        )

        messages.append(
            {
                "role": "user",
                "content": STRUCTURED_FINAL_PROMPT,
            }
        )

        final_response = chat(
            messages=messages,
            tools=None,
        )

        raw_content = final_response.content or "{}"

        try:

            raw_json = json.loads(raw_content)

            validated = Diagnosis.model_validate(raw_json)

            diagnosis = validated.model_dump()

            print("[Orchestrator] " "Structured diagnosis validated successfully.")

        except json.JSONDecodeError as exc:

            print("[Orchestrator] " "Diagnosis JSON parsing failed:")

            print(exc)

            diagnosis = self.build_fallback_diagnosis(
                raw_content=raw_content,
                reason=("The model returned invalid JSON."),
            )

        except ValidationError as exc:

            print("[Orchestrator] " "Diagnosis schema validation failed:")

            print(exc)

            diagnosis = self.build_fallback_diagnosis(
                raw_content=raw_content,
                reason=(
                    "The model output did not match " "the required diagnosis schema."
                ),
            )

        return diagnosis

    def build_fallback_diagnosis(
        self,
        raw_content: str,
        reason: str,
    ) -> dict:

        fallback = Diagnosis(
            summary={
                "status": "degraded",
                "total_issues": 0,
                "critical": 0,
                "warnings": 0,
                "healthy": 0,
                "headline": ("Structured diagnosis " "validation failed"),
            },
            issues=[],
            narrative=(
                f"{reason}\n\n"
                "The investigation completed, "
                "but the structured response could "
                "not be validated.\n\n"
                "Raw model output:\n\n"
                f"{raw_content}"
            ),
        )

        return fallback.model_dump()

    async def run(
        self,
        user_message: str,
        event_callback: EventCallback = None,
    ) -> dict:

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

                print("[Orchestrator] " "No additional specialists requested.")

                diagnosis = await self.build_structured_diagnosis(
                    messages,
                    event_callback,
                )

                await emit(
                    event_callback,
                    "investigation_completed",
                    message="Investigation completed",
                )

                return diagnosis

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

        print("[Orchestrator] " "Maximum orchestration rounds reached.")

        diagnosis = await self.build_structured_diagnosis(
            messages,
            event_callback,
        )

        await emit(
            event_callback,
            "investigation_completed",
            message="Investigation completed",
        )

        return diagnosis
