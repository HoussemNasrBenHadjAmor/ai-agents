import asyncio

from agents.database_agent import DatabaseAgent
from agents.docker_agent import DockerAgent
from agents.orchestrator import Orchestrator
from agents.network_agent import NetworkAgent

from config import (
    AI_MODEL,
    AI_PROVIDER,
    AGENT_MAX_ITERATIONS,
)


async def main():

    print()
    print("================================")
    print("      AI DEVOPS PLATFORM")
    print("================================")
    print()

    print(f"Provider                : {AI_PROVIDER}")
    print(f"Model                   : {AI_MODEL}")
    print(f"Specialist max iterations: " f"{AGENT_MAX_ITERATIONS}")

    docker_agent = DockerAgent()
    database_agent = DatabaseAgent()
    network_agent = NetworkAgent()

    try:

        print()
        print("[Main] Connecting specialists...")

        await docker_agent.connect()
        await database_agent.connect()
        await network_agent.connect()

        orchestrator = Orchestrator(
            docker_agent=docker_agent,
            database_agent=database_agent,
            network_agent=network_agent,
        )

        print()
        print("[Main] All specialists ready.")

        user_message = """
Investigate the current infrastructure.

Find any active problems affecting the application.

Check Docker and the database where appropriate.

Try to identify likely root causes.

Everything must remain read-only.
"""

        print()
        print("User:")
        print(user_message)

        result = await orchestrator.run(user_message)

        print()
        print("================================")
        print("          FINAL RESULT")
        print("================================")
        print()

        print(result)

    finally:

        print()
        print("[Main] Closing specialists...")

        await database_agent.close()
        await docker_agent.close()
        await network_agent.close()


if __name__ == "__main__":
    asyncio.run(main())
