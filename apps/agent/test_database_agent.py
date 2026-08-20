import asyncio

from agents.database_agent import DatabaseAgent
from config import (
    AI_MODEL,
    AI_PROVIDER,
    AGENT_MAX_ITERATIONS,
)


async def main():

    print()
    print("================================")
    print("       DATABASE AGENT")
    print("================================")
    print()
    print(f"Provider       : {AI_PROVIDER}")
    print(f"Model          : {AI_MODEL}")
    print(
        f"Max iterations : "
        f"{AGENT_MAX_ITERATIONS}"
    )

    agent = DatabaseAgent()

    try:

        print()
        print("[Main] Connecting Database Agent...")

        await agent.connect()

        user_message = """
Investigate this PostgreSQL database.

Check the application service state stored in the database.

Also inspect:
- the schema
- recent incidents
- active PostgreSQL connections
- database size
- long-running queries
- locks or blocked sessions

Identify anything that appears unhealthy or suspicious.

Do not modify anything.
"""

        print()
        print("User:")
        print(user_message)

        result = await agent.run(
            user_message
        )

        print()
        print("================================")
        print("            RESULT")
        print("================================")
        print()
        print(result)

    finally:

        print()
        print("[Main] Closing Database Agent...")

        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
