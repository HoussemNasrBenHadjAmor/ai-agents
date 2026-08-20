import asyncio

from agents.network_agent import NetworkAgent


async def main():

    agent = NetworkAgent()

    try:

        await agent.connect()

        result = await agent.run(
            """
Investigate this server's network environment.

Check:
- host network configuration
- listening ports
- whether localhost PostgreSQL on port 55433
  is reachable
- whether external DNS resolution works

Everything must remain read-only.
"""
        )

        print()
        print("============================")
        print("           RESULT")
        print("============================")
        print()
        print(result)

    finally:

        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
