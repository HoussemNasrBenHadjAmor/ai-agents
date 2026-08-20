import json
import os
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

AGENT_DIR = Path(__file__).resolve().parent
DBHUB_CONFIG = AGENT_DIR / "dbhub.toml"

DATABASE_MCP_SERVER = StdioServerParameters(
    command="dbhub",
    args=[
        "--config",
        str(DBHUB_CONFIG),
        "--transport",
        "stdio",
    ],
    env=dict(os.environ),
)


ALLOWED_DATABASE_TOOLS = {
    "execute_sql",
    "search_objects",
}


class DatabaseMCPClient:

    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session = None
        self.tools = []

    async def connect(self):

        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(DATABASE_MCP_SERVER)
        )

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(
                read_stream,
                write_stream,
            )
        )

        await self.session.initialize()

        response = await self.session.list_tools()

        self.tools = [
            tool for tool in response.tools if tool.name in ALLOWED_DATABASE_TOOLS
        ]

        return self

    async def close(self):
        await self.exit_stack.aclose()

    def get_deepseek_tools(self):

        tools = []

        for tool in self.tools:

            schema = getattr(
                tool,
                "inputSchema",
                None,
            ) or {
                "type": "object",
                "properties": {},
            }

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": (tool.description or tool.name),
                        "parameters": schema,
                    },
                }
            )

        return tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> str:

        if tool_name not in ALLOWED_DATABASE_TOOLS:
            return f"ERROR: Database tool " f"'{tool_name}' is not permitted."

        result = await self.session.call_tool(
            tool_name,
            arguments=arguments,
        )

        parts = []

        for item in result.content:

            if hasattr(item, "text"):
                parts.append(item.text)

            else:
                try:
                    parts.append(
                        json.dumps(
                            item.model_dump(),
                            default=str,
                        )
                    )

                except Exception:
                    parts.append(str(item))

        return "\n".join(parts)
