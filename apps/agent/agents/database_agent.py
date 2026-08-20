import json

from config import AGENT_MAX_ITERATIONS
from database_mcp_client import DatabaseMCPClient
from events import EventCallback, emit
from llm import chat

DATABASE_SYSTEM_PROMPT = """
You are a PostgreSQL database diagnostic agent.

Your responsibility is to investigate database-related problems
using the read-only database tools available to you.

You may investigate:

- database schema
- tables and columns
- application data
- database size
- active connections
- long-running queries
- locks
- blocked sessions
- transaction activity
- PostgreSQL statistics
- recent incidents stored in application tables
- potentially unhealthy database behavior

Rules:

- Use tools whenever real database information is required.
- Never invent database contents, schemas, connections,
  queries, statistics, or errors.
- Never claim to have checked something unless a tool checked it.
- Prefer database evidence over assumptions.
- Use search_objects when you need to discover tables,
  columns, views, or schema objects.
- Use execute_sql only for read-only investigation.
- Keep SQL targeted.
- Avoid retrieving unnecessary data.
- Prefer PostgreSQL system views for diagnostics.

Safety:

- This is strictly read-only.
- Never INSERT.
- Never UPDATE.
- Never DELETE.
- Never CREATE.
- Never ALTER.
- Never DROP.
- Never TRUNCATE.
- Never execute destructive or administrative SQL.
- Never attempt to bypass read-only restrictions.
"""


class DatabaseAgent:

    def __init__(self):
        self.mcp = DatabaseMCPClient()

    async def connect(self):
        await self.mcp.connect()

        print(
            f"[Database Agent] Connected with "
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
            agent="database",
            message="Database Agent started",
        )

        messages = [
            {
                "role": "system",
                "content": DATABASE_SYSTEM_PROMPT,
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
                f"[Database Agent iteration "
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
                    agent="database",
                    message="Database Agent completed",
                )

                return response.content

            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name

                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")

                except json.JSONDecodeError:
                    arguments = {}

                print(f"[Database MCP] {tool_name}")

                print(f"[Arguments] " f"{json.dumps(arguments)}")

                await emit(
                    event_callback,
                    "tool_started",
                    agent="database",
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
                    agent="database",
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
database diagnosis now.

Clearly separate:

1. Confirmed findings
2. Likely issues or root causes
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
            agent="database",
            message="Database Agent completed",
        )

        return final_response.content
