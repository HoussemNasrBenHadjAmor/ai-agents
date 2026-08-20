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

After receiving specialist results, analyze the evidence together.

Never claim a system was inspected unless a specialist
actually inspected it.

Everything must remain read-only.

Never ask a specialist to modify infrastructure.
"""


STRUCTURED_FINAL_PROMPT = """
Using ONLY the specialist evidence already collected, produce the final
diagnosis as VALID JSON.

Do not use Markdown fences.

Do not include any text before or after the JSON.

Return exactly this general structure:

{
  "summary": {
    "status": "healthy | degraded | critical",
    "total_issues": 0,
    "critical": 0,
    "warnings": 0,
    "healthy": 0,
    "headline": "Short overall summary"
  },

  "issues": [
    {
      "resource": "resource name",
      "resource_type": "docker | database | network | other",
      "status": "current technical status",
      "severity": "critical | warning | info | healthy",
      "problem": "short problem title",
      "evidence": "important concrete evidence",
      "likely_cause": "likely root cause",
      "recommendation": "next READ-ONLY investigation or recommendation"
    }
  ],

  "narrative": "Short readable explanation of the overall diagnosis."
}

Rules:

- Never invent evidence.
- Only report findings supported by specialist results.
- If something is uncertain, clearly say so.
- Keep fields concise.
- Do not recommend automatic infrastructure modifications.
- Recommendations must remain read-only or require human action.
- Do not expose private chain-of-thought.
- Do not return Markdown.
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
                "required": ["task"],
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
                "required": ["task"],
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
                "required": ["task"],
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

        return f"ERROR: Unknown specialist: {tool_name}"

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
            diagnosis = json.loads(raw_content)

        except json.JSONDecodeError:

            diagnosis = {
                "summary": {
                    "status": "degraded",
                    "total_issues": 0,
                    "critical": 0,
                    "warnings": 0,
                    "healthy": 0,
                    "headline": ("Structured diagnosis " "could not be parsed"),
                },
                "issues": [],
                "narrative": raw_content,
            }

        diagnosis.setdefault(
            "summary",
            {},
        )

        diagnosis.setdefault(
            "issues",
            [],
        )

        diagnosis.setdefault(
            "narrative",
            "",
        )

        summary = diagnosis["summary"]

        summary.setdefault(
            "status",
            "degraded",
        )

        summary.setdefault(
            "total_issues",
            len(diagnosis["issues"]),
        )

        summary.setdefault(
            "critical",
            0,
        )

        summary.setdefault(
            "warnings",
            0,
        )

        summary.setdefault(
            "healthy",
            0,
        )

        summary.setdefault(
            "headline",
            "Infrastructure diagnosis",
        )

        return diagnosis

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
