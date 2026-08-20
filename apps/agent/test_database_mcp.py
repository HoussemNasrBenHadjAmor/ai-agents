import asyncio

from database_mcp_client import DatabaseMCPClient


async def main():

    client = DatabaseMCPClient()

    try:
        await client.connect()

        print()
        print("============================")
        print("      DATABASE MCP TOOLS")
        print("============================")
        print()

        for tool in client.tools:
            print(f"- {tool.name}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
