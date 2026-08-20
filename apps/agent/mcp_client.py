import json
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


DOCKER_MCP_SERVER = StdioServerParameters(
    command="docker",
    args=[
        "run",
        "--rm",
        "-i",
        "-e",
        "DOCKER_MCP_SERVER_READONLY=1",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        "ghcr.io/l337-org/docker-mcp-server:latest",
    ],
)


# These are the tools DeepSeek can initially use.
# They are all diagnostic/read-only.
ALLOWED_DOCKER_TOOLS = {
    "container_list",
    "container_inspect",
    "container_logs",
    "container_stats",
    "container_top",
    "container_diff",

    "network_list",
    "network_inspect",

    "volume_list",
    "volume_inspect",

    "image_list",
    "image_inspect",

    "compose_list",
    "compose_ps",
    "compose_logs",
    "compose_config",

    "system_info",
    "system_df",
    "system_events",
    "system_version",
}


class DockerMCPClient:

    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session = None
        self.tools = []

    async def connect(self):

        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(DOCKER_MCP_SERVER)
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
            tool
            for tool in response.tools
            if tool.name in ALLOWED_DOCKER_TOOLS
        ]

        return self

    async def close(self):
        await self.exit_stack.aclose()

    def get_deepseek_tools(self):
        """
        Convert MCP tool definitions into the
        OpenAI-compatible tool format DeepSeek understands.
        """

        converted = []

        for tool in self.tools:

            schema = getattr(
                tool,
                "inputSchema",
                None,
            )

            if schema is None:
                schema = {
                    "type": "object",
                    "properties": {},
                }

            converted.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": (
                            tool.description
                            or f"Docker MCP tool: {tool.name}"
                        ),
                        "parameters": schema,
                    },
                }
            )

        return converted

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
    ) -> str:

        if tool_name not in ALLOWED_DOCKER_TOOLS:
            return (
                f"ERROR: Tool '{tool_name}' "
                "is not permitted."
            )

        result = await self.session.call_tool(
            tool_name,
            arguments=arguments,
        )

        output_parts = []

        for item in result.content:

            if hasattr(item, "text"):
                output_parts.append(item.text)

            else:
                try:
                    output_parts.append(
                        json.dumps(
                            item.model_dump(),
                            default=str,
                        )
                    )

                except Exception:
                    output_parts.append(str(item))

        return "\n".join(output_parts)
